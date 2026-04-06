from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .ai_clients import build_insight_engine
from .listener import AutoListener
from .openapi import OpenApiGenerator
from .redaction import redact_headers, redact_json
from .registry import SchemaRegistry
from .service_directory import ServiceDirectory


def parse_json_if_possible(raw: bytes) -> Any | None:
    if not raw:
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


UI_ROOT = Path(__file__).resolve().parents[2] / "docs" / "HTML"
_ALLOWED_UI_FILES = {
    "control-panel.html",
    "endpoint-explorer.html",
    "schema-drift.html",
    "capture-inspector.html",
    "openapi-export.html",
    "collections-export.html",
    "settings.html",
    "index.html",
}


def _ui_html_filename(path: str) -> str | None:
    if path in {"/_therapi/ui", "/_therapi/ui/"}:
        return "control-panel.html"
    prefix = "/_therapi/ui/"
    if not path.startswith(prefix):
        return None
    candidate = path[len(prefix) :]
    if not candidate or "/" in candidate or ".." in candidate:
        return None
    return candidate


def _rewrite_ui_links(html: str) -> str:
    def repl(match: re.Match[str]) -> str:
        filename = match.group(1)
        return f'href="/_therapi/ui/{filename}"'

    return re.sub(r'href="([a-z0-9\-]+\.html)"', repl, html, flags=re.IGNORECASE)


def _load_ui_page(filename: str) -> str | None:
    if filename not in _ALLOWED_UI_FILES:
        return None
    page = UI_ROOT / filename
    if not page.is_file():
        return None
    return _rewrite_ui_links(page.read_text(encoding="utf-8"))


class DiscoveryProxyHandler(BaseHTTPRequestHandler):
    registry: SchemaRegistry
    openapi: OpenApiGenerator
    target_base_url: str | None = None
    listener: AutoListener | None = None
    directory: ServiceDirectory | None = None

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
        if self.path == "/_therapi/listener":
            status = self.listener.status() if self.listener else {"running": False, "configured": False}
            self._respond_json(200, status)
            return
        if self.path == "/_therapi/providers":
            self._respond_json(200, {"providers": self.directory.list_providers() if self.directory else []})
            return
        if self.path == "/_therapi/phonebook":
            self._respond_json(200, {"apis": self.directory.list_apis() if self.directory else []})
            return
        if self.path == "/_therapi/insights":
            if not self.listener:
                self._respond_json(200, {"recommendation": "Listener is disabled", "source": "local-fallback"})
                return
            self._respond_json(200, self.listener.latest_insights())
            return
        ui_filename = _ui_html_filename(urllib.parse.urlsplit(self.path).path)
        if ui_filename is not None:
            page = _load_ui_page(ui_filename)
            if page is None:
                self._respond_json(404, {"error": "ui page not found"})
                return
            self._respond_html(200, page)
            return
        self._forward()

    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/_therapi/providers":
            payload = self._read_json_body()
            if payload is None:
                return
            if not self.directory:
                self._respond_json(500, {"error": "directory is not configured"})
                return
            try:
                created = self.directory.add_provider(
                    name=str(payload["name"]),
                    endpoint=str(payload["endpoint"]),
                    model=payload.get("model"),
                    api_key_env=payload.get("api_key_env"),
                    headers=payload.get("headers"),
                )
            except (KeyError, ValueError, TypeError) as err:
                self._respond_json(400, {"error": str(err)})
                return
            self._respond_json(201, created)
            return

        if self.path == "/_therapi/phonebook":
            payload = self._read_json_body()
            if payload is None:
                return
            if not self.directory:
                self._respond_json(500, {"error": "directory is not configured"})
                return
            try:
                created = self.directory.add_api(
                    name=str(payload["name"]),
                    base_url=str(payload["base_url"]),
                    category=str(payload.get("category", "general")),
                    notes=str(payload.get("notes", "")),
                    services=payload.get("services"),
                )
            except (KeyError, ValueError, TypeError) as err:
                self._respond_json(400, {"error": str(err)})
                return
            self._respond_json(201, created)
            return

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

    def _read_json_body(self) -> dict[str, Any] | None:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length) if content_length > 0 else b""
        try:
            decoded = json.loads(raw.decode("utf-8") if raw else "{}")
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._respond_json(400, {"error": "invalid JSON payload"})
            return None
        if not isinstance(decoded, dict):
            self._respond_json(400, {"error": "payload must be a JSON object"})
            return None
        return decoded

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
    parser.add_argument("--listener-interval", default=int(os.environ.get("THERAPI_LISTENER_INTERVAL", "300")), type=int)
    parser.add_argument("--ai-provider", default=os.environ.get("THERAPI_AI_PROVIDER"))
    parser.add_argument("--ai-api-key", default=os.environ.get("THERAPI_AI_API_KEY"))
    parser.add_argument("--ai-model", default=os.environ.get("THERAPI_AI_MODEL"))
    parser.add_argument("--ai-endpoint", default=os.environ.get("THERAPI_AI_ENDPOINT"))
    parser.add_argument("--ai-provider-profile", default=os.environ.get("THERAPI_AI_PROVIDER_PROFILE"))
    parser.add_argument("--directory-file", default=os.environ.get("THERAPI_DIRECTORY_FILE", ".therapi/phonebook.json"))
    args = parser.parse_args()

    registry = SchemaRegistry(args.store)
    directory = ServiceDirectory(args.directory_file)
    DiscoveryProxyHandler.registry = registry
    DiscoveryProxyHandler.openapi = OpenApiGenerator(registry)
    DiscoveryProxyHandler.target_base_url = args.target_base_url
    DiscoveryProxyHandler.directory = directory

    provider = args.ai_provider
    api_key = args.ai_api_key
    model = args.ai_model
    endpoint = args.ai_endpoint
    headers = None

    if args.ai_provider_profile:
        profile = directory.get_provider(args.ai_provider_profile)
        if profile is None:
            raise ValueError(f"unknown provider profile: {args.ai_provider_profile}")
        provider = "custom"
        endpoint = profile.get("endpoint")
        model = model or profile.get("model")
        key_env = profile.get("api_key_env")
        if not api_key and key_env:
            api_key = os.environ.get(key_env)
        headers = profile.get("headers")

    insight_engine = build_insight_engine(
        provider=provider,
        api_key=api_key,
        model=model,
        endpoint=endpoint,
        headers=headers,
    )
    listener = AutoListener(registry, interval_seconds=args.listener_interval, insight_engine=insight_engine)
    listener.start()
    DiscoveryProxyHandler.listener = listener

    server = ThreadingHTTPServer((args.host, args.port), DiscoveryProxyHandler)
    print(f"therAPI discovery proxy listening on http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
