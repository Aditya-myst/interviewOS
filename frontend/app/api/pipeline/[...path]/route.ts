import { NextResponse } from "next/server";

/**
 * Browser -> FastAPI for the pipeline, including the multipart resume upload.
 *
 * This one does not reuse `lib/proxy.ts` on purpose: that helper reads the body as text,
 * which is correct for JSON and fatal for `multipart/form-data` — it would rewrite the
 * boundary and FastAPI would answer 422 "missing file". Here the raw bytes and the
 * original content-type (boundary included) are forwarded untouched.
 */
const BASE = (process.env.INTERVIEWOS_API_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "");

const FORWARDED = ["x-data-source", "x-fallback-reason"] as const;

async function proxy(request: Request, path: string[]): Promise<NextResponse> {
  const target = `${BASE}/v1/${path.map(encodeURIComponent).join("/")}`;
  const contentType = request.headers.get("content-type") ?? "application/json";

  const init: RequestInit = { method: request.method, cache: "no-store", headers: { "content-type": contentType } };
  if (request.method !== "GET" && request.method !== "HEAD") {
    init.body = await request.arrayBuffer();
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
    return NextResponse.json(
      { detail: "the API is unreachable — is uvicorn running on :8000?" },
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
