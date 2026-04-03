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

## Nutzung

Proxy-Request über Query-Parameter `url`:

```bash
curl "http://127.0.0.1:8080/get?url=https://httpbin.org/get"
```

Request/Response werden aufgezeichnet und pro Endpoint (`METHOD + path`) aggregiert.

## TherAPI interne Endpunkte

- `GET /_therapi/health` – Healthcheck
- `GET /_therapi/summary` – Endpoints, Samples, Versionsstände
- `GET /_therapi/openapi.json` – dynamisch erzeugte OpenAPI 3.0.3 Spezifikation

## Tests

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```
