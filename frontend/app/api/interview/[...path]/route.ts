import { proxyToApi } from "@/lib/proxy";

/**
 * Browser -> FastAPI for the interview. The reasoning lives in `lib/proxy.ts`; this file
 * only names the scope, so the interview and the assessment cannot drift apart.
 */
export async function GET(request: Request, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  return proxyToApi(request, path, "interview");
}

export async function POST(request: Request, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  return proxyToApi(request, path, "interview");
}
