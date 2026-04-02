export function buildMockFromSchema(schema) {
  if (!schema) return {};

  switch (schema.kind) {
    case "null":
      return null;
    case "boolean":
      return true;
    case "number":
      return 42;
    case "string":
      return typeof schema.examples?.[0] === "string" ? schema.examples[0] : "example";
    case "array":
      return [buildMockFromSchema(schema.items)];
    case "object": {
      const result = {};
      for (const [key, child] of Object.entries(schema.children ?? {})) {
        result[key] = buildMockFromSchema(child);
      }
      return result;
    }
  }
}
