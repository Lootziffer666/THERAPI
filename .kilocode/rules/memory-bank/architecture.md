# System Patterns: therAPI Discovery MVP

## Architecture Overview

Implemented pipeline in `therapi_old/src`:

```
Capture -> Infer -> Registry -> Expose
```

### Modules

- `lib/discovery-registry.ts`
  - In-memory endpoint registry
  - Stores captured exchanges grouped by `METHOD path`
  - Returns inferred endpoint snapshots
- `lib/schema-inference.ts`
  - Probabilistic schema inference over observed values
  - Tracks dominant type, required ratio, nested object/array structure
- `lib/openapi-generator.ts`
  - Converts inferred schemas to OpenAPI 3.1-compatible path schemas
  - Marks fields as required when observed ratio is >= 0.95
- `lib/mock-generator.ts`
  - Generates deterministic mock payloads from inferred schema trees

### API Surface

- `POST /api/capture` — add runtime sample
- `GET /api/endpoints` — inspect inferred endpoint snapshots
- `GET /api/openapi` — export reconstructed OpenAPI document
- `GET /api/mock` — generate mock response for discovered endpoint

## Key Design Choices

1. **In-memory first**: keeps MVP simple and fast to iterate.
2. **Probabilistic schema**: supports partially observed and evolving payloads.
3. **Contract from usage**: OpenAPI is generated dynamically from runtime evidence.
4. **Composable modules**: inference/registry/expose are separated for future persistence/versioning.
