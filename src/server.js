import { createServer } from "node:http";
import { URL } from "node:url";
import { buildMockFromSchema } from "./mock-generator.js";
import { captureExchange, clearRegistry, listEndpointSnapshots } from "./discovery-registry.js";
import { generateOpenApiDocument } from "./openapi-generator.js";

const PORT = Number(process.env.PORT ?? 3000);

function sendJson(res, statusCode, payload) {
  res.writeHead(statusCode, { "content-type": "application/json; charset=utf-8" });
  res.end(JSON.stringify(payload, null, 2));
}

async function readJsonBody(req) {
  const chunks = [];
  for await (const chunk of req) {
    chunks.push(chunk);
  }

  if (chunks.length === 0) return {};

  const raw = Buffer.concat(chunks).toString("utf8");
  return JSON.parse(raw);
}

const server = createServer(async (req, res) => {
  const method = req.method?.toUpperCase() ?? "GET";
  const url = new URL(req.url ?? "/", `http://${req.headers.host ?? `localhost:${PORT}`}`);

  if (method === "GET" && url.pathname === "/") {
    return sendJson(res, 200, {
      name: "therAPI discovery server",
      endpoints: {
        capture: "POST /api/capture",
        endpoints: "GET /api/endpoints",
        openapi: "GET /api/openapi",
        mock: "GET /api/mock?method=GET&path=/users",
        reset: "POST /api/reset",
      },
    });
  }

  if (method === "POST" && url.pathname === "/api/capture") {
    try {
      const payload = await readJsonBody(req);

      if (!payload?.method || !payload?.path || typeof payload?.status !== "number") {
        return sendJson(res, 400, { error: "Payload requires method, path, and status" });
      }

      const snapshot = captureExchange(payload);
      return sendJson(res, 200, { message: "Capture stored", endpoint: snapshot });
    } catch {
      return sendJson(res, 400, { error: "Invalid JSON payload" });
    }
  }

  if (method === "GET" && url.pathname === "/api/endpoints") {
    return sendJson(res, 200, { endpoints: listEndpointSnapshots() });
  }

  if (method === "GET" && url.pathname === "/api/openapi") {
    return sendJson(res, 200, generateOpenApiDocument());
  }

  if (method === "GET" && url.pathname === "/api/mock") {
    const queryMethod = url.searchParams.get("method")?.toUpperCase();
    const queryPath = url.searchParams.get("path");

    if (!queryMethod || !queryPath) {
      return sendJson(res, 400, { error: "Query parameters method and path are required" });
    }

    const endpoint = listEndpointSnapshots().find(
      (candidate) => candidate.method === queryMethod && candidate.path === queryPath,
    );

    if (!endpoint) {
      return sendJson(res, 404, { error: "No endpoint discovered yet" });
    }

    return sendJson(res, 200, {
      method: queryMethod,
      path: queryPath,
      mock: buildMockFromSchema(endpoint.inferredResponseSchema),
    });
  }

  if (method === "POST" && url.pathname === "/api/reset") {
    clearRegistry();
    return sendJson(res, 200, { message: "Registry cleared" });
  }

  return sendJson(res, 404, { error: "Not found" });
});

server.listen(PORT, () => {
  console.log(`therAPI discovery server listening on http://localhost:${PORT}`);
});
