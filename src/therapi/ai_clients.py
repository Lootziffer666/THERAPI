from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


class RemoteInsightEngine:
    def __init__(
        self,
        provider: str,
        api_key: str,
        model: str,
        endpoint: str | None = None,
        timeout_seconds: int = 20,
        default_headers: dict[str, str] | None = None,
    ):
        self.provider = provider.lower()
        self.api_key = api_key
        self.model = model
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds
        self.default_headers = default_headers or {}

    def generate(self, prompt: str) -> str:
        if self.provider == "openai":
            return self._generate_openai(prompt)
        if self.provider == "google":
            return self._generate_google(prompt)
        if self.provider == "custom":
            return self._generate_custom(prompt)
        raise ValueError(f"unsupported ai provider: {self.provider}")

    def _request(self, url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(url=url, data=data, method="POST")
        request.add_header("Content-Type", "application/json")
        for key, value in self.default_headers.items():
            request.add_header(key, value)
        for key, value in headers.items():
            request.add_header(key, value)

        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"AI provider HTTP {error.code}: {body[:300]}") from error
        except urllib.error.URLError as error:
            raise RuntimeError(f"AI provider connection failed: {error.reason}") from error

        try:
            return json.loads(raw)
        except json.JSONDecodeError as error:
            raise RuntimeError("AI provider returned invalid JSON") from error

    def _generate_openai(self, prompt: str) -> str:
        url = self.endpoint or "https://api.openai.com/v1/responses"
        payload = {
            "model": self.model,
            "input": [
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": prompt}],
                }
            ],
        }
        response = self._request(url, payload, {"Authorization": f"Bearer {self.api_key}"})
        output_text = response.get("output_text")
        if isinstance(output_text, str) and output_text.strip():
            return output_text.strip()
        return json.dumps(response, ensure_ascii=False)

    def _generate_google(self, prompt: str) -> str:
        model = urllib.parse.quote(self.model, safe="")
        base = self.endpoint or f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        joiner = "&" if "?" in base else "?"
        url = f"{base}{joiner}key={urllib.parse.quote(self.api_key, safe='')}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        response = self._request(url, payload, {})
        candidates = response.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            text = "\n".join(part.get("text", "") for part in parts if part.get("text"))
            if text.strip():
                return text.strip()
        return json.dumps(response, ensure_ascii=False)

    def _generate_custom(self, prompt: str) -> str:
        if not self.endpoint:
            raise ValueError("custom provider requires an endpoint URL")
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = {"model": self.model, "prompt": prompt}
        response = self._request(self.endpoint, payload, headers)
        for key in ("text", "output", "response", "result"):
            value = response.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return json.dumps(response, ensure_ascii=False)


def build_insight_engine(
    provider: str | None,
    api_key: str | None,
    model: str | None,
    endpoint: str | None = None,
    headers: dict[str, str] | None = None,
) -> RemoteInsightEngine | None:
    if not provider:
        return None
    provider_name = provider.lower()
    if provider_name in {"openai", "google"} and not api_key:
        raise ValueError(f"{provider_name} provider requires an API key")
    if provider_name != "custom" and not model:
        raise ValueError(f"{provider_name} provider requires a model")
    resolved_model = model or "default"
    return RemoteInsightEngine(
        provider_name,
        api_key or "",
        resolved_model,
        endpoint=endpoint,
        default_headers=headers,
    )
