import { inferSchema } from "./schema-inference.js";

const endpoints = new Map();

function endpointKey(method, path) {
  return `${method.toUpperCase()} ${path}`;
}

export function captureExchange(payload) {
  const key = endpointKey(payload.method, payload.path);
  const existing = endpoints.get(key);

  const exchange = {
    ...payload,
    method: payload.method.toUpperCase(),
    capturedAt: payload.capturedAt ?? new Date().toISOString(),
  };

  if (existing) {
    existing.exchanges.push(exchange);
  } else {
    endpoints.set(key, {
      method: exchange.method,
      path: exchange.path,
      exchanges: [exchange],
    });
  }

  return getEndpointSnapshot(key);
}

export function listEndpointSnapshots() {
  return Array.from(endpoints.keys())
    .map((key) => getEndpointSnapshot(key))
    .filter(Boolean)
    .sort((a, b) => a.key.localeCompare(b.key));
}

export function getEndpointSnapshot(key) {
  const record = endpoints.get(key);
  if (!record) return undefined;

  const statuses = new Set(record.exchanges.map((x) => x.status));
  const requestBodies = record.exchanges.map((x) => x.requestBody).filter((v) => v !== undefined);
  const responseBodies = record.exchanges.map((x) => x.responseBody).filter((v) => v !== undefined);
  const lastSeen = record.exchanges[record.exchanges.length - 1];

  return {
    key,
    method: record.method,
    path: record.path,
    samples: record.exchanges.length,
    statuses: Array.from(statuses).sort((a, b) => a - b),
    inferredRequestSchema: inferSchema(requestBodies),
    inferredResponseSchema: inferSchema(responseBodies),
    lastSeenAt: lastSeen.capturedAt,
  };
}

export function clearRegistry() {
  endpoints.clear();
}
