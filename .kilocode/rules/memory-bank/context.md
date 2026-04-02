# Active Context: therAPI Discovery MVP

## Current State

**Project Status**: ✅ MVP discovery pipeline implemented in `therapi_old`

The project now includes a first end-to-end API discovery flow based on the plan in `docs/`:

1. Capture runtime API traffic
2. Infer probabilistic schemas from observed payloads
3. Keep endpoint snapshots in a registry
4. Generate OpenAPI dynamically
5. Generate mock responses from inferred schemas

## Recently Completed

- [x] Added capture endpoint: `POST /api/capture`
- [x] Added endpoint registry view: `GET /api/endpoints`
- [x] Added dynamic contract endpoint: `GET /api/openapi`
- [x] Added schema-based mock endpoint: `GET /api/mock?method=...&path=...`
- [x] Added initial inference/registry/openapi/mock library modules
- [x] Updated landing page to explain the Capture → Infer → Expose workflow

## Current Focus

- Validate with real sniffed traffic input
- Add persistence and schema versioning (next roadmap phase)
- Add semantic enrichment (therapi integration)

## Session History

| Date | Changes |
|------|---------|
| 2026-04-02 | Implemented discovery MVP API routes, schema inference, dynamic OpenAPI, and mock generation |
