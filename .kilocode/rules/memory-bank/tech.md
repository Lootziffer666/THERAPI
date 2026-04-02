# Technical Context: therAPI Discovery MVP

## Stack in Active App (`therapi_old`)

- Next.js App Router (TypeScript)
- Route Handlers for API endpoints
- Tailwind CSS for simple landing page docs

## New Technical Components

- `src/lib/discovery-types.ts`: shared domain types for captures and inferred schemas
- `src/lib/schema-inference.ts`: recursive aggregation + schema inference
- `src/lib/discovery-registry.ts`: in-memory capture storage and endpoint snapshots
- `src/lib/openapi-generator.ts`: OpenAPI 3.1 document generation from snapshots
- `src/lib/mock-generator.ts`: schema-to-mock payload conversion

## API Endpoints

- `POST /api/capture`
- `GET /api/endpoints`
- `GET /api/openapi`
- `GET /api/mock?method=...&path=...`

## Validation Commands

```bash
npm run lint
npm run typecheck
```
