from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .schema import SchemaNode


@dataclass
class SchemaVersion:
    version: int
    fingerprint: str
    schema: dict[str, Any]


@dataclass
class EndpointRecord:
    method: str
    path: str
    request_schema: SchemaNode = field(default_factory=SchemaNode)
    response_schema: SchemaNode = field(default_factory=SchemaNode)
    samples: int = 0
    versions: list[SchemaVersion] = field(default_factory=list)

    def observe(self, request_payload: Any, response_payload: Any) -> bool:
        self.samples += 1
        if request_payload is not None:
            self.request_schema.observe(request_payload)
        if response_payload is not None:
            self.response_schema.observe(response_payload)

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
            self.versions.append(
                SchemaVersion(
                    version=len(self.versions) + 1,
                    fingerprint=fingerprint,
                    schema=snapshot,
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

    def observe(self, method: str, path: str, request_payload: Any, response_payload: Any) -> bool:
        key = self._key(method, path)
        record = self._records.setdefault(
            key,
            EndpointRecord(method=method.upper(), path=path),
        )
        changed = record.observe(request_payload, response_payload)
        if changed:
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
                "versions": [
                    {
                        "version": version.version,
                        "fingerprint": version.fingerprint,
                    }
                    for version in record.versions
                ],
            }
            for key, record in sorted(self._records.items())
        }

    def save(self) -> None:
        if not self.persistence_file:
            return
        data = {}
        for key, record in self._records.items():
            data[key] = {
                "method": record.method,
                "path": record.path,
                "samples": record.samples,
                "versions": [
                    {
                        "version": version.version,
                        "fingerprint": version.fingerprint,
                        "schema": version.schema,
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
        # keep load minimal and rely on snapshots for display/openapi
        for key, rec in raw.items():
            endpoint = EndpointRecord(method=rec["method"], path=rec["path"], samples=rec.get("samples", 0))
            endpoint.versions = [
                SchemaVersion(
                    version=ver["version"],
                    fingerprint=ver["fingerprint"],
                    schema=ver["schema"],
                )
                for ver in rec.get("versions", [])
            ]
            self._records[key] = endpoint
