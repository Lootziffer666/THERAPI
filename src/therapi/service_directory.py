from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_AVV_SERVICES = [
    {"name": "Arrival board", "wadl_url": "https://auskunft.avv.de/restproxy/arrivalBoard?wadl"},
    {"name": "Departure board", "wadl_url": "https://auskunft.avv.de/restproxy/departureBoard?wadl"},
    {"name": "GIS Route by Context", "wadl_url": "https://auskunft.avv.de/restproxy/gisroute?wadl"},
    {"name": "Interval search", "wadl_url": "https://auskunft.avv.de/restproxy/intervalsearch?wadl"},
    {"name": "Journey Detail", "wadl_url": "https://auskunft.avv.de/restproxy/journeyDetail?wadl"},
    {"name": "Location search by coordinate", "wadl_url": "https://auskunft.avv.de/restproxy/location.nearbystops?wadl"},
    {"name": "Location search by name", "wadl_url": "https://auskunft.avv.de/restproxy/location.name?wadl"},
    {"name": "Reconstruction", "wadl_url": "https://auskunft.avv.de/restproxy/db_recon?wadl"},
    {"name": "Trias", "wadl_url": "https://auskunft.avv.de/restproxy/trias?wadl"},
    {"name": "Trip search", "wadl_url": "https://auskunft.avv.de/restproxy/trip?wadl"},
    {"name": "XSD", "wadl_url": "https://auskunft.avv.de/restproxy/xsd"},
]

DEFAULT_APIS = [
    {
        "name": "AVV",
        "base_url": "https://auskunft.avv.de/restproxy",
        "category": "transit",
        "notes": "Aachener Verkehrsverbund",
        "services": DEFAULT_AVV_SERVICES,
    },
    {
        "name": "DB",
        "base_url": "https://apis.deutschebahn.com",
        "category": "transit",
        "notes": "Deutsche Bahn APIs",
    },
    {
        "name": "Transitous",
        "base_url": "https://api.transitous.org",
        "category": "transit",
        "notes": "Open transit routing platform",
    },
]


class ServiceDirectory:
    def __init__(self, persistence_file: str = ".therapi/phonebook.json"):
        self.persistence_file = Path(persistence_file)
        self._providers: list[dict[str, Any]] = []
        self._apis: list[dict[str, Any]] = []
        self._load()
        self._seed_defaults()

    def _seed_defaults(self) -> None:
        known_names = {entry["name"].lower() for entry in self._apis}
        changed = False
        for api in DEFAULT_APIS:
            if api["name"].lower() not in known_names:
                self._apis.append(api)
                changed = True
        if changed:
            self.save()

    def _load(self) -> None:
        if not self.persistence_file.exists():
            return
        raw = json.loads(self.persistence_file.read_text(encoding="utf-8"))
        self._providers = list(raw.get("providers", []))
        self._apis = list(raw.get("apis", []))

    def save(self) -> None:
        self.persistence_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {"providers": self._providers, "apis": self._apis}
        self.persistence_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def list_providers(self) -> list[dict[str, Any]]:
        return list(self._providers)

    def list_apis(self) -> list[dict[str, Any]]:
        return list(self._apis)

    def add_provider(
        self,
        name: str,
        endpoint: str,
        model: str | None = None,
        api_key_env: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        if any(entry["name"].lower() == name.lower() for entry in self._providers):
            raise ValueError(f"provider '{name}' already exists")
        record = {
            "name": name,
            "endpoint": endpoint,
            "model": model or "default",
            "api_key_env": api_key_env,
            "headers": headers or {},
        }
        self._providers.append(record)
        self.save()
        return record

    def add_api(
        self,
        name: str,
        base_url: str,
        category: str = "general",
        notes: str = "",
        services: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        if any(entry["name"].lower() == name.lower() for entry in self._apis):
            raise ValueError(f"api '{name}' already exists")
        record = {
            "name": name,
            "base_url": base_url,
            "category": category,
            "notes": notes,
            "services": services or [],
        }
        self._apis.append(record)
        self.save()
        return record

    def get_provider(self, name: str) -> dict[str, Any] | None:
        for provider in self._providers:
            if provider["name"].lower() == name.lower():
                return provider
        return None
