from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .schema import SchemaNode


@dataclass
class SchemaVersion:
    version: int
    fingerprint: str
    schema: dict[str, Any]
    changed_at: str
    diff: dict[str, Any] = field(default_factory=dict)


@dataclass
class EndpointRecord:
    method: str
    path: str
    request_schema: SchemaNode = field(default_factory=SchemaNode)
    response_schema: SchemaNode = field(default_factory=SchemaNode)
    samples: int = 0
    versions: list[SchemaVersion] = field(default_factory=list)
    captures: list[dict[str, Any]] = field(default_factory=list)

    def _extract_paths(self, signature: dict[str, Any], prefix: str = "") -> set[str]:
        found = set()
        for data_type in signature.get("types", []):
            found.add(f"{prefix}:{data_type}")

        for key, child in signature.get("properties", {}).items():
            child_prefix = f"{prefix}.{key}" if prefix else key
            found.update(self._extract_paths(child, child_prefix))

        items = signature.get("items")
        if items:
            items_prefix = f"{prefix}[]" if prefix else "[]"
            found.update(self._extract_paths(items, items_prefix))
        return found

    def _build_diff(self, previous: dict[str, Any] | None, current: dict[str, Any]) -> dict[str, Any]:
        if previous is None:
            return {"added": sorted(self._extract_paths(current)), "removed": []}

        previous_paths = self._extract_paths(previous)
        current_paths = self._extract_paths(current)
        return {
            "added": sorted(current_paths - previous_paths),
            "removed": sorted(previous_paths - current_paths),
        }

    def observe(
        self,
        request_payload: Any,
        response_payload: Any,
        capture: dict[str, Any] | None = None,
    ) -> bool:
        self.samples += 1
        if request_payload is not None:
            self.request_schema.observe(request_payload)
        if response_payload is not None:
            self.response_schema.observe(response_payload)

        if capture is not None:
            self.captures.append(capture)
            self.captures = self.captures[-20:]

        snapshot = {
            "request": self.request_schema.to_probabilistic_dict(),
            "response": self.response_schema.to_probabilistic_dict(),
        }
        structure = {
            "request": self.request_schema.structural_signature(),
            "response": self.response_schema.structural_signature(),
        }
        fingerprint = hashlib.sha256(
            json.dumps(structure, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        if not self.versions or self.versions[-1].fingerprint != fingerprint:
            previous = self.versions[-1].schema if self.versions else None
            change_diff = {
                "request": self._build_diff(
                    previous.get("request") if previous else None,
                    snapshot["request"],
                ),
                "response": self._build_diff(
                    previous.get("response") if previous else None,
                    snapshot["response"],
                ),
            }
            self.versions.append(
                SchemaVersion(
                    version=len(self.versions) + 1,
                    fingerprint=fingerprint,
                    schema=snapshot,
                    changed_at=datetime.now(UTC).isoformat(),
                    diff=change_diff,
                )
            )
            return True
        return False


class SchemaRegistry:
    def __init__(self, persistence_file: str | None = None):
        self._records: dict[str, EndpointRecord] = {}
        self.persistence_file = Path(persistence_file) if persistence_file else None
        if self.persistence_file and self.persistence_file.exists():
            self._load()

    def _key(self, method: str, path: str) -> str:
        return f"{method.upper()} {path}"

    def observe(
        self,
        method: str,
        path: str,
        request_payload: Any,
        response_payload: Any,
        capture: dict[str, Any] | None = None,
    ) -> bool:
        key = self._key(method, path)
        record = self._records.setdefault(
            key,
            EndpointRecord(method=method.upper(), path=path),
        )
        changed = record.observe(request_payload, response_payload, capture=capture)
        self.save()
        return changed

    def records(self) -> list[EndpointRecord]:
        return list(self._records.values())

    def summary(self) -> dict[str, Any]:
        return {
            key: {
                "method": record.method,
                "path": record.path,
                "samples": record.samples,
                "captures": len(record.captures),
                "versions": [
                    {
                        "version": version.version,
                        "fingerprint": version.fingerprint,
                        "changed_at": version.changed_at,
                    }
                    for version in record.versions
                ],
            }
            for key, record in sorted(self._records.items())
        }

    def drift_report(self) -> dict[str, Any]:
        return {
            key: [
                {
                    "version": version.version,
                    "changed_at": version.changed_at,
                    "request": version.diff.get("request", {}),
                    "response": version.diff.get("response", {}),
                }
                for version in record.versions
            ]
            for key, record in sorted(self._records.items())
        }

    def export_collections(self) -> dict[str, Any]:
        entries: list[dict[str, Any]] = []
        for key, record in sorted(self._records.items()):
            entries.append(
                {
                    "endpoint": key,
                    "method": record.method,
                    "path": record.path,
                    "samples": record.samples,
                    "captures": record.captures,
                }
            )
        return {"collections": entries}

    def save(self) -> None:
        if not self.persistence_file:
            return
        data = {}
        for key, record in self._records.items():
            data[key] = {
                "method": record.method,
                "path": record.path,
                "samples": record.samples,
                "captures": record.captures,
                "versions": [
                    {
                        "version": version.version,
                        "fingerprint": version.fingerprint,
                        "schema": version.schema,
                        "changed_at": version.changed_at,
                        "diff": version.diff,
                    }
                    for version in record.versions
                ],
            }
        self.persistence_file.parent.mkdir(parents=True, exist_ok=True)
        self.persistence_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _load(self) -> None:
        if not self.persistence_file:
            return
        raw = json.loads(self.persistence_file.read_text(encoding="utf-8"))
        for key, rec in raw.items():
            endpoint = EndpointRecord(
                method=rec["method"],
                path=rec["path"],
                samples=rec.get("samples", 0),
                captures=rec.get("captures", []),
            )
            endpoint.versions = [
                SchemaVersion(
                    version=ver["version"],
                    fingerprint=ver["fingerprint"],
                    schema=ver["schema"],
                    changed_at=ver.get("changed_at", ""),
                    diff=ver.get("diff", {}),
                )
                for ver in rec.get("versions", [])
            ]
            self._records[key] = endpoint
