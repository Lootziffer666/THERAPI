from __future__ import annotations

from typing import Any

from .registry import EndpointRecord, SchemaRegistry


class OpenApiGenerator:
    def __init__(self, registry: SchemaRegistry):
        self.registry = registry

    def _schema_from_snapshot(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        types = snapshot.get("types", {})
        ordered = sorted(types.items(), key=lambda item: item[1], reverse=True)
        if not ordered:
            return {"type": "object"}
        primary = ordered[0][0]

        if primary == "object":
            properties = snapshot.get("properties", {})
            presence = snapshot.get("property_presence", {})
            samples = max(snapshot.get("samples", 1), 1)
            required = [k for k, count in presence.items() if count / samples >= 0.95]
            schema: dict[str, Any] = {
                "type": "object",
                "properties": {
                    k: self._schema_from_snapshot(v)
                    for k, v in sorted(properties.items())
                },
            }
            if required:
                schema["required"] = sorted(required)
            return schema

        if primary == "array":
            return {
                "type": "array",
                "items": self._schema_from_snapshot(snapshot.get("items", {})),
            }

        return {"type": primary}

    def _request_schema(self, record: EndpointRecord) -> dict[str, Any]:
        if record.versions:
            return self._schema_from_snapshot(record.versions[-1].schema.get("request", {}))
        return record.request_schema.to_openapi_schema()

    def _response_schema(self, record: EndpointRecord) -> dict[str, Any]:
        if record.versions:
            return self._schema_from_snapshot(record.versions[-1].schema.get("response", {}))
        return record.response_schema.to_openapi_schema()

    def generate(self) -> dict[str, Any]:
        paths: dict[str, Any] = {}
        for record in self.registry.records():
            endpoint = paths.setdefault(record.path, {})
            endpoint[record.method.lower()] = {
                "summary": f"Observed endpoint ({record.samples} samples)",
                "requestBody": {
                    "required": False,
                    "content": {
                        "application/json": {
                            "schema": self._request_schema(record),
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "Observed response",
                        "content": {
                            "application/json": {
                                "schema": self._response_schema(record),
                            }
                        },
                    }
                },
            }

        return {
            "openapi": "3.0.3",
            "info": {
                "title": "therAPI Discovered Contract",
                "version": "0.1.0",
            },
            "paths": paths,
        }
