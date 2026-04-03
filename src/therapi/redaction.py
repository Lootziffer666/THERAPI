from __future__ import annotations

from typing import Any

SENSITIVE_HEADERS = {
    "authorization",
    "proxy-authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "api-key",
}

SENSITIVE_FIELD_MARKERS = {
    "password",
    "passwd",
    "secret",
    "token",
    "apikey",
    "api_key",
    "access_token",
    "refresh_token",
    "client_secret",
    "session",
    "cookie",
    "authorization",
}

REDACTED = "[REDACTED]"


def is_sensitive_field(field_name: str) -> bool:
    lowered = field_name.lower().replace("-", "_")
    return any(marker in lowered for marker in SENSITIVE_FIELD_MARKERS)


def redact_headers(headers: dict[str, str]) -> dict[str, str]:
    redacted: dict[str, str] = {}
    for name, value in headers.items():
        if name.lower() in SENSITIVE_HEADERS:
            redacted[name] = REDACTED
        else:
            redacted[name] = value
    return redacted


def redact_json(value: Any) -> Any:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, child in value.items():
            if is_sensitive_field(key):
                result[key] = REDACTED
            else:
                result[key] = redact_json(child)
        return result
    if isinstance(value, list):
        return [redact_json(entry) for entry in value]
    return value
