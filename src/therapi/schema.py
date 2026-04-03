from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


JsonType = str


def detect_json_type(value: Any) -> JsonType:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int) and not isinstance(value, bool):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return "unknown"


@dataclass
class SchemaNode:
    samples: int = 0
    type_counts: dict[JsonType, int] = field(default_factory=dict)
    properties: dict[str, "SchemaNode"] = field(default_factory=dict)
    property_presence: dict[str, int] = field(default_factory=dict)
    items: "SchemaNode | None" = None

    def observe(self, value: Any) -> None:
        self.samples += 1
        value_type = detect_json_type(value)
        self.type_counts[value_type] = self.type_counts.get(value_type, 0) + 1

        if value_type == "object":
            assert isinstance(value, dict)
            for key, child_value in value.items():
                self.property_presence[key] = self.property_presence.get(key, 0) + 1
                self.properties.setdefault(key, SchemaNode()).observe(child_value)
        elif value_type == "array":
            assert isinstance(value, list)
            if self.items is None:
                self.items = SchemaNode()
            for entry in value:
                self.items.observe(entry)

    def most_likely_types(self) -> list[JsonType]:
        return sorted(self.type_counts, key=self.type_counts.get, reverse=True)


    def structural_signature(self) -> dict[str, Any]:
        signature: dict[str, Any] = {
            "types": sorted(self.type_counts),
        }
        if self.properties:
            signature["properties"] = {
                key: value.structural_signature()
                for key, value in sorted(self.properties.items())
            }
        if self.items is not None:
            signature["items"] = self.items.structural_signature()
        return signature

    def to_probabilistic_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "samples": self.samples,
            "types": dict(sorted(self.type_counts.items())),
        }
        if self.properties:
            result["properties"] = {
                key: value.to_probabilistic_dict() for key, value in sorted(self.properties.items())
            }
            result["property_presence"] = dict(sorted(self.property_presence.items()))
        if self.items is not None:
            result["items"] = self.items.to_probabilistic_dict()
        return result

    def to_openapi_schema(self, required_threshold: float = 0.95) -> dict[str, Any]:
        types = self.most_likely_types()
        if not types:
            return {"type": "object"}

        primary_type = types[0]
        if primary_type == "object":
            schema: dict[str, Any] = {"type": "object", "properties": {}}
            required: list[str] = []
            for name, child in sorted(self.properties.items()):
                schema["properties"][name] = child.to_openapi_schema(required_threshold)
                presence = self.property_presence.get(name, 0) / max(self.samples, 1)
                if presence >= required_threshold:
                    required.append(name)
            if required:
                schema["required"] = required
            return schema

        if primary_type == "array":
            items = self.items.to_openapi_schema(required_threshold) if self.items else {"type": "string"}
            return {"type": "array", "items": items}

        if primary_type == "null" and len(types) > 1:
            primary_type = types[1]

        if len(types) > 1 and "null" in types:
            return {"type": [primary_type, "null"]}

        return {"type": primary_type}
