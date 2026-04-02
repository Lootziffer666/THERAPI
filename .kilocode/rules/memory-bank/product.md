# Product Context: therAPI Discovery MVP

## Product Direction

The current implementation shifts the project from a generic template to an API discovery MVP aligned with the PRD:

- Runtime API observation
- Automatic schema inference
- Dynamic contract generation
- Mock API support

## User Value Delivered

Developers can now capture unknown API payloads and immediately get:

1. A discovered endpoint inventory
2. Inferred request/response structure
3. A generated OpenAPI representation
4. Mock payloads for downstream consumers

## MVP Boundaries

Included now:
- HTTP JSON capture and analysis
- In-memory registry
- OpenAPI export endpoint
- Basic schema-derived mock output

Not yet included:
- Persistent storage
- Version diff engine
- therapi-based semantic enrichment
- Multi-transport capture (Kafka/gRPC)
