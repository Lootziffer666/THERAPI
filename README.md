# therAPI (MVP)

Dieses Repository enthält einen MVP für das im PRD definierte API-Discovery-Tool mit den vier geplanten Kernschritten:

1. HTTP Capture (Proxy)
2. JSON Schema Inference (probabilistisch)
3. Versionierte Schema Registry
4. OpenAPI Export

## Starten

```bash
PYTHONPATH=src python -m therapi.proxy --host 127.0.0.1 --port 8080
```

Optional mit fixer Upstream-Base-URL (statt `?url=` pro Request):

```bash
PYTHONPATH=src python -m therapi.proxy --target-base-url https://httpbin.org
```

## Nutzung

### Variante A: Ziel-URL direkt im Request

```bash
curl "http://127.0.0.1:8080/get?url=https://httpbin.org/get"
```

### Variante B: Mit gesetzter Base URL

```bash
curl "http://127.0.0.1:8080/get"
```

Request/Response werden aufgezeichnet und pro Endpoint (`METHOD + path`) aggregiert.

## TherAPI interne Endpunkte

- `GET /_therapi/health` – Healthcheck
- `GET /_therapi/ui` – lokales Control Panel (HTML)
- `GET /_therapi/summary` – Endpoints, Samples, Versionsstände
- `GET /_therapi/drift` – Schema-Änderungen zwischen Versionen
- `GET /_therapi/openapi.json` – dynamisch erzeugte OpenAPI 3.0.3 Spezifikation
- `GET /_therapi/collections.json` – redaktierte Capture-Collections

## Security / Redaction

Beim Speichern von Captures werden sensible Header/Felder redigiert (`[REDACTED]`), z. B. `Authorization`, `Cookie`, `api_key`, `token`, `password`.

## Tests

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```
