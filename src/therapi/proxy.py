from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .openapi import OpenApiGenerator
from .redaction import redact_headers, redact_json
from .registry import SchemaRegistry


def parse_json_if_possible(raw: bytes) -> Any | None:
    if not raw:
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def _render_control_panel(host: str, port: int, target_base_url: str | None, summary: dict[str, Any]) -> str:
    rows = []
    for key, record in summary.items():
        rows.append(
            "<tr>"
            f"<td><code>{key}</code></td>"
            f"<td>{record['samples']}</td>"
            f"<td>{len(record['versions'])}</td>"
            f"<td>{record['captures']}</td>"
            "</tr>"
        )

    table_html = "".join(rows) or "<tr><td colspan='4'><em>No captures yet</em></td></tr>"
    target_hint = target_base_url or "(none)"
    return f"""<!doctype html>
<html lang='en'>
<head><meta charset='utf-8'><title>therAPI Control Panel</title></head>
<body style='font-family: sans-serif; margin: 2rem;'>
<h1>therAPI Control Panel</h1>
<p><strong>Proxy:</strong> http://{host}:{port}</p>
<p><strong>Configured target base URL:</strong> <code>{target_hint}</code></p>
<p>
  <a href='/_therapi/summary'>Summary JSON</a> |
  <a href='/_therapi/drift'>Drift JSON</a> |
  <a href='/_therapi/openapi.json'>OpenAPI Export</a> |
  <a href='/_therapi/collections.json'>Collections Export</a>
</p>
<table border='1' cellspacing='0' cellpadding='6'>
<thead><tr><th>Endpoint</th><th>Samples</th><th>Versions</th><th>Captures</th></tr></thead>
<tbody>{table_html}</tbody>
</table>
</body></html>"""


class DiscoveryProxyHandler(BaseHTTPRequestHandler):
    registry: SchemaRegistry
    openapi: OpenApiGenerator
    target_base_url: str | None = None

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/_therapi/health":
            self._respond_json(200, {"status": "ok"})
            return
        if self.path == "/_therapi/summary":
            self._respond_json(200, self.registry.summary())
            return
        if self.path == "/_therapi/drift":
            self._respond_json(200, self.registry.drift_report())
            return
        if self.path == "/_therapi/openapi.json":
            self._respond_json(200, self.openapi.generate())
            return
        if self.path == "/_therapi/collections.json":
            self._respond_json(200, self.registry.export_collections())
            return
        if self.path == "/_therapi/ui":
            panel = _render_control_panel(
                self.server.server_address[0],
                self.server.server_address[1],
                self.target_base_url,
                self.registry.summary(),
            )
            self._respond_html(200, panel)
            return
        self._forward()

    def do_POST(self) -> None:  # noqa: N802
        self._forward()

    def do_PUT(self) -> None:  # noqa: N802
        self._forward()

    def do_PATCH(self) -> None:  # noqa: N802
        self._forward()

    def do_DELETE(self) -> None:  # noqa: N802
        self._forward()

    def _target_url(self) -> str:
        parsed = urllib.parse.urlsplit(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        target = query.get("url", [None])[0]
        if target:
            return target

        if not self.target_base_url:
            raise ValueError("missing query parameter 'url' and no default target configured")

        path_without_query = parsed.path or "/"
        query_suffix = f"?{parsed.query}" if parsed.query else ""
        return f"{self.target_base_url.rstrip('/')}{path_without_query}{query_suffix}"

    def _forward(self) -> None:
        try:
            target = self._target_url()
        except ValueError as err:
            self._respond_json(400, {"error": str(err)})
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        request_body = self.rfile.read(content_length) if content_length > 0 else b""
        request = urllib.request.Request(url=target, method=self.command, data=request_body or None)

        for header, value in self.headers.items():
            if header.lower() in {"host", "content-length"}:
                continue
            request.add_header(header, value)

        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                response_body = response.read()
                status = response.status
                headers = dict(response.getheaders())
        except urllib.error.HTTPError as error:
            response_body = error.read()
            status = error.code
            headers = dict(error.headers.items())
        except urllib.error.URLError as error:
            self._respond_json(502, {"error": f"upstream request failed: {error.reason}"})
            return

        upstream_path = urllib.parse.urlsplit(target).path or "/"
        request_json = parse_json_if_possible(request_body)
        response_json = parse_json_if_possible(response_body)

        self.registry.observe(
            self.command,
            upstream_path,
            request_json,
            response_json,
            capture={
                "target": target,
                "status": status,
                "request_headers": redact_headers(dict(self.headers.items())),
                "response_headers": redact_headers(headers),
                "request_json": redact_json(request_json),
                "response_json": redact_json(response_json),
            },
        )

        self.send_response(status)
        for name, value in headers.items():
            if name.lower() in {"content-length", "connection", "transfer-encoding"}:
                continue
            self.send_header(name, value)
        self.send_header("Content-Length", str(len(response_body)))
        self.end_headers()
        self.wfile.write(response_body)

    def _respond_json(self, status: int, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _respond_html(self, status: int, body: str) -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def main() -> None:
    parser = argparse.ArgumentParser(description="therAPI discovery proxy")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8080, type=int)
    parser.add_argument("--store", default=".therapi/registry.json")
    parser.add_argument("--target-base-url", default=os.environ.get("THERAPI_TARGET_BASE_URL"))
    args = parser.parse_args()

    registry = SchemaRegistry(args.store)
    DiscoveryProxyHandler.registry = registry
    DiscoveryProxyHandler.openapi = OpenApiGenerator(registry)
    DiscoveryProxyHandler.target_base_url = args.target_base_url

    server = ThreadingHTTPServer((args.host, args.port), DiscoveryProxyHandler)
    print(f"therAPI discovery proxy listening on http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
