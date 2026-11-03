import { NextResponse } from "next/server";

/**
 * One proxy for every browser -> FastAPI call.
 *
 * The browser cannot reach FastAPI directly without baking an API URL into the bundle,
 * opening CORS, and losing the `X-Data-Source` header on the way. A route handler keeps
 * the address server-side and forwards the provenance headers verbatim, so a screen can
 * always say whether what it is holding lives in Postgres or in memory.
 *
 * `scope` is the first path segment of the upstream route ("interview", "assessment"),
 * because FastAPI mounts them under /v1/<scope>/....
 */
const BASE = (process.env.INTERVIEWOS_API_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "");

const FORWARDED = ["x-data-source", "x-fallback-reason"] as const;

export async function proxyToApi(
  request: Request,
  path: string[],
  scope: string,
): Promise<NextResponse> {
  const target = `${BASE}/v1/${scope}/${path.map(encodeURIComponent).join("/")}`;

  const init: RequestInit = {
    method: request.method,
    cache: "no-store",
    headers: { "content-type": request.headers.get("content-type") ?? "application/json" },
  };
  if (request.method !== "GET" && request.method !== "HEAD") {
    init.body = await request.text();
  }

  try {
    const upstream = await fetch(target, init);
    const body = await upstream.text();
    const headers = new Headers({ "content-type": "application/json; charset=utf-8" });
    for (const name of FORWARDED) {
      const value = upstream.headers.get(name);
      if (value) headers.set(name, value);
    }
    return new NextResponse(body, { status: upstream.status, headers });
  } catch {
    // The screen must be able to say "the API is not running" rather than render a button
    // that does nothing.
    return NextResponse.json(
      { detail: `the API is unreachable — is uvicorn running on :8000? (${scope})` },
      { status: 503 },
    );
  }
}
