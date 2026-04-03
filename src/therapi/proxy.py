from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .openapi import OpenApiGenerator
from .registry import SchemaRegistry


def parse_json_if_possible(raw: bytes) -> Any | None:
    if not raw:
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


class DiscoveryProxyHandler(BaseHTTPRequestHandler):
    registry: SchemaRegistry
    openapi: OpenApiGenerator

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/_therapi/health":
            self._respond_json(200, {"status": "ok"})
            return
        if self.path == "/_therapi/summary":
            self._respond_json(200, self.registry.summary())
            return
        if self.path == "/_therapi/openapi.json":
            self._respond_json(200, self.openapi.generate())
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
        if not target:
            raise ValueError("missing query parameter 'url'")
        return target

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
        self.registry.observe(
            self.command,
            upstream_path,
            parse_json_if_possible(request_body),
            parse_json_if_possible(response_body),
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


def main() -> None:
    parser = argparse.ArgumentParser(description="therAPI discovery proxy")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8080, type=int)
    parser.add_argument("--store", default=".therapi/registry.json")
    args = parser.parse_args()

    registry = SchemaRegistry(args.store)
    DiscoveryProxyHandler.registry = registry
    DiscoveryProxyHandler.openapi = OpenApiGenerator(registry)

    server = ThreadingHTTPServer((args.host, args.port), DiscoveryProxyHandler)
    print(f"therAPI discovery proxy listening on http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
