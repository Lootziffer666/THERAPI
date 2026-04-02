# therAPI

Runtime API Discovery Tool auf Basis des PRD-Plans (**Capture → Infer → Expose**).

## Was ist enthalten?

- **Capture Layer**: `POST /api/capture` nimmt Request/Response-Beobachtungen auf.
- **Schema Inference**: Typen, verschachtelte Felder und `requiredRatio` werden aus Samples abgeleitet.
- **Registry**: In-Memory Endpunkt-Snapshots.
- **Contract Generation**: `GET /api/openapi` generiert OpenAPI 3.1 dynamisch.
- **Mock Output**: `GET /api/mock?method=...&path=...` erstellt Schema-basierte Mock-Responses.

## Start

```bash
npm run start
```

Server läuft standardmäßig auf `http://localhost:3000`.

## Beispiel-Flow

### 1) Capture

```bash
curl -X POST http://localhost:3000/api/capture \
  -H 'content-type: application/json' \
  -d '{
    "method":"GET",
    "path":"/users",
    "status":200,
    "responseBody":{"id":1,"name":"Mira","active":true}
  }'
```

### 2) Endpunkte ansehen

```bash
curl http://localhost:3000/api/endpoints
```

### 3) OpenAPI exportieren

```bash
curl http://localhost:3000/api/openapi
```

### 4) Mock erzeugen

```bash
curl 'http://localhost:3000/api/mock?method=GET&path=/users'
```

## Hinweis

Die bisherigen Ordner `therapi_old/` und `apisniffer_old/` wurden entfernt. Sie dienten nur als Referenzquelle.
