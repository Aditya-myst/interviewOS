import { NextResponse } from "next/server";

/**
 * A thin proxy from the browser to the interview service.
 *
 * The interview is the first genuinely interactive screen, so it is the first time the
 * browser — not the server — has to reach FastAPI. Two ways to do that, and only one of
 * them is honest about configuration:
 *
 *   expose the API URL to the client   -> NEXT_PUBLIC_ var baked into the bundle, plus
 *                                         CORS, plus a port nobody can change at runtime
 *   proxy through a route handler      -> the API address stays server-side, no CORS, and
 *                                         the data-source headers survive the hop
 *
 * This is the second. It also keeps the rule that a screen never invents its own state:
 * `X-Data-Source` from the API is forwarded verbatim, so the UI can say whether the
 * session it is holding lives in Postgres or in memory.
 */
const BASE = (process.env.INTERVIEWOS_API_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "");

const FORWARDED = ["x-data-source", "x-fallback-reason"] as const;

async function proxy(request: Request, path: string[]): Promise<NextResponse> {
  const target = `${BASE}/v1/interview/${path.map(encodeURIComponent).join("/")}`;

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
    // The screen must be able to say "the interview service is not running" rather than
    // render a dead button.
    return NextResponse.json(
      { detail: "the interview service is unreachable — is uvicorn running on :8000?" },
      { status: 503 },
    );
  }
}

export async function GET(request: Request, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  return proxy(request, path);
}

export async function POST(request: Request, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  return proxy(request, path);
}
