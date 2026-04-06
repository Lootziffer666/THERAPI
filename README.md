# THERAPI (MVP)

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

Optional mit automatischem Listener + AI-Empfehlungen (OpenAI/Google/Custom):

```bash
PYTHONPATH=src python -m therapi.proxy \
  --target-base-url https://httpbin.org \
  --ai-provider openai \
  --ai-model gpt-4.1-mini \
  --ai-api-key "$THERAPI_AI_API_KEY"
```

Custom-Provider-Profil aus dem Telefonbuch verwenden:

```bash
PYTHONPATH=src python -m therapi.proxy --ai-provider-profile mein-llm
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
- `GET /_therapi/ui` – UI-Startseite (Control Panel)
- `GET /_therapi/ui/<screen>.html` – weitere UI-Screens (z. B. `schema-drift.html`)
- `GET /_therapi/listener` – Status des Auto-Listeners
- `GET /_therapi/insights` – automatische Drift-Empfehlungen (AI oder Fallback)
- `GET /_therapi/providers` – gespeicherte Custom-AI-Provider
- `POST /_therapi/providers` – neuen Custom-AI-Provider speichern
- `GET /_therapi/phonebook` – API-Telefonbuch (u. a. AVV, DB, Transitous; AVV inkl. WADL-Servicekatalog)
- `POST /_therapi/phonebook` – API-Eintrag hinzufügen
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


## Beispiele: Telefonbuch erweitern

Custom-Provider anlegen:

```bash
curl -X POST http://127.0.0.1:8080/_therapi/providers \
  -H "Content-Type: application/json" \
  -d '{"name":"mein-llm","endpoint":"https://llm.example.com/v1/generate","model":"custom-model","api_key_env":"MEIN_LLM_KEY"}'
```

Neue Ziel-API für CatchIt anlegen:

```bash
curl -X POST http://127.0.0.1:8080/_therapi/phonebook \
  -H "Content-Type: application/json" \
  -d '{"name":"Meine API","base_url":"https://api.example.com","category":"catchit","notes":"später produktiv"}'
```


AVV ist bereits mit folgenden Services im Telefonbuch vorbelegt: arrivalBoard, departureBoard, gisroute, intervalsearch, journeyDetail, location.nearbystops, location.name, db_recon, trias, trip, xsd.
