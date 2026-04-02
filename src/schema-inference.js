/** @typedef {import('./discovery-types.js').ObservedValueType} ObservedValueType */

function createAggregateNode() {
  return {
    total: 0,
    kindCounts: {
      null: 0,
      boolean: 0,
      number: 0,
      string: 0,
      object: 0,
      array: 0,
    },
    present: 0,
    examples: [],
    objectChildren: {},
    arrayItems: undefined,
  };
}

function detectKind(value) {
  if (value === null) return "null";
  if (Array.isArray(value)) return "array";
  const t = typeof value;
  if (t === "boolean") return "boolean";
  if (t === "number") return "number";
  if (t === "string") return "string";
  return "object";
}

function updateAggregate(node, value) {
  node.total += 1;
  if (value === undefined) return;

  node.present += 1;
  const kind = detectKind(value);
  node.kindCounts[kind] += 1;

  if (node.examples.length < 3) {
    node.examples.push(value);
  }

  if (kind === "object") {
    for (const [key, nestedValue] of Object.entries(value)) {
      if (!node.objectChildren[key]) {
        node.objectChildren[key] = createAggregateNode();
      }
      updateAggregate(node.objectChildren[key], nestedValue);
    }
  }

  if (kind === "array") {
    if (!node.arrayItems) {
      node.arrayItems = createAggregateNode();
    }
    for (const item of value) {
      updateAggregate(node.arrayItems, item);
    }
  }
}

function mostLikelyKind(kindCounts) {
  const entries = Object.entries(kindCounts);
  entries.sort((a, b) => b[1] - a[1]);
  return /** @type {ObservedValueType} */ (entries[0]?.[0] ?? "null");
}

function buildSchema(node) {
  const kind = mostLikelyKind(node.kindCounts);
  const result = {
    kind,
    occurrences: node.present,
    requiredRatio: node.total === 0 ? 0 : Number((node.present / node.total).toFixed(2)),
    examples: node.examples,
  };

  if (kind === "object") {
    result.children = Object.fromEntries(
      Object.entries(node.objectChildren).map(([key, child]) => [key, buildSchema(child)]),
    );
  }

  if (kind === "array" && node.arrayItems) {
    result.items = buildSchema(node.arrayItems);
  }

  return result;
}

export function inferSchema(observedValues) {
  if (!Array.isArray(observedValues) || observedValues.length === 0) {
    return undefined;
  }

  const root = createAggregateNode();
  for (const value of observedValues) {
    updateAggregate(root, value);
  }

  return buildSchema(root);
}
