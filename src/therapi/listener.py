from __future__ import annotations

import hashlib
import json
import threading
from datetime import UTC, datetime
from typing import Any, Protocol

from .registry import SchemaRegistry


class InsightEngine(Protocol):
    def generate(self, prompt: str) -> str: ...


class AutoListener:
    def __init__(
        self,
        registry: SchemaRegistry,
        interval_seconds: int = 300,
        insight_engine: InsightEngine | None = None,
    ):
        self.registry = registry
        self.interval_seconds = max(15, interval_seconds)
        self.insight_engine = insight_engine
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._last_run_at: str | None = None
        self._last_error: str | None = None
        self._last_fingerprint: str | None = None
        self._last_report: dict[str, Any] | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="therapi-auto-listener", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def _run(self) -> None:
        while not self._stop_event.is_set():
            self.tick()
            self._stop_event.wait(self.interval_seconds)

    def tick(self) -> None:
        summary = self.registry.summary()
        drift = self.registry.drift_report()
        fingerprint = hashlib.sha256(
            json.dumps(drift, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        with self._lock:
            now = datetime.now(UTC).isoformat()
            self._last_run_at = now
            if self._last_fingerprint == fingerprint and self._last_report is not None:
                return

        report = self._build_report(summary, drift)
        with self._lock:
            self._last_fingerprint = fingerprint
            self._last_report = report

    def _build_report(self, summary: dict[str, Any], drift: dict[str, Any]) -> dict[str, Any]:
        endpoint_count = len(summary)
        version_changes = sum(len(changes) for changes in drift.values())
        fallback_text = (
            f"Observed {endpoint_count} endpoint(s) and {version_changes} schema version snapshots. "
            "Prioritize reviewing endpoints with removed response fields first."
        )
        report: dict[str, Any] = {
            "generated_at": datetime.now(UTC).isoformat(),
            "endpoints": endpoint_count,
            "version_snapshots": version_changes,
            "recommendation": fallback_text,
            "source": "local-fallback",
        }

        if self.insight_engine is None:
            return report

        prompt = self._compose_prompt(summary, drift)
        try:
            llm_text = self.insight_engine.generate(prompt)
            report["recommendation"] = llm_text
            report["source"] = "ai"
            with self._lock:
                self._last_error = None
        except Exception as exc:  # noqa: BLE001
            with self._lock:
                self._last_error = str(exc)
            report["source"] = "local-fallback"
            report["warning"] = "AI request failed; fallback recommendation returned"

        return report

    def _compose_prompt(self, summary: dict[str, Any], drift: dict[str, Any]) -> str:
        return (
            "You are assisting with runtime API drift analysis. "
            "Give concise action items for a developer who wants to leave the service running and return later.\n\n"
            f"Summary:\n{json.dumps(summary, indent=2)}\n\n"
            f"Drift report:\n{json.dumps(drift, indent=2)}"
        )

    def status(self) -> dict[str, Any]:
        with self._lock:
            running = bool(self._thread and self._thread.is_alive())
            return {
                "running": running,
                "interval_seconds": self.interval_seconds,
                "last_run_at": self._last_run_at,
                "last_error": self._last_error,
                "ai_enabled": self.insight_engine is not None,
            }

    def latest_insights(self) -> dict[str, Any]:
        with self._lock:
            report = self._last_report
        if report is not None:
            return report
        self.tick()
        with self._lock:
            return self._last_report or {
                "generated_at": datetime.now(UTC).isoformat(),
                "recommendation": "No data observed yet.",
                "source": "local-fallback",
            }
