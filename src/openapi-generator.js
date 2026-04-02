import { listEndpointSnapshots } from "./discovery-registry.js";

function toOpenApiSchema(schema) {
  if (!schema) return { type: "object", description: "No samples captured yet" };

  if (schema.kind === "null") return { nullable: true };

  if (schema.kind === "array") {
    return {
      type: "array",
      items: toOpenApiSchema(schema.items),
      description: `Observed ${schema.occurrences} array values`,
    };
  }

  if (schema.kind === "object") {
    const properties = {};
    const required = [];

    for (const [key, child] of Object.entries(schema.children ?? {})) {
      properties[key] = toOpenApiSchema(child);
      if (child.requiredRatio >= 0.95) {
        required.push(key);
      }
    }

    return {
      type: "object",
      properties,
      ...(required.length ? { required } : {}),
      description: `Observed ${schema.occurrences} object values`,
    };
  }

  return {
    type: schema.kind,
    description: `Observed ${schema.occurrences} values`,
  };
}

export function generateOpenApiDocument() {
  const snapshots = listEndpointSnapshots();
  const paths = {};

  for (const snapshot of snapshots) {
    const pathEntry = (paths[snapshot.path] ??= {});

    pathEntry[snapshot.method.toLowerCase()] = {
      summary: `Discovered from ${snapshot.samples} runtime sample(s)`,
      requestBody: {
        required: false,
        content: {
          "application/json": {
            schema: toOpenApiSchema(snapshot.inferredRequestSchema),
          },
        },
      },
      responses: {
        [snapshot.statuses[0] ?? 200]: {
          description: "Observed response",
          content: {
            "application/json": {
              schema: toOpenApiSchema(snapshot.inferredResponseSchema),
            },
          },
        },
      },
    };
  }

  return {
    openapi: "3.1.0",
    info: {
      title: "therAPI Runtime Discovery Contract",
      version: "0.1.0",
      description: "Auto-generated from captured runtime traffic",
    },
    paths,
  };
}
