import { proxyToApi } from "@/lib/proxy";

/**
 * Progress writes: PATCH /api/preparation/topics/<id>  ->  FastAPI /v1/preparation/topics/<id>
 *
 * The first path segment after /api/ is the API's mount point (`proxyToApi` builds
 * `/v1/<scope>/<rest>`), so this directory has to be named for the mount, not for the screen.
 * Naming it `prep` produced a clean 404 on every click: `/v1/prep/preparation/topics/...`.
 */
export async function GET(request: Request, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  return proxyToApi(request, path, "preparation");
}

export async function POST(request: Request, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  return proxyToApi(request, path, "preparation");
}

export async function PATCH(request: Request, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  return proxyToApi(request, path, "preparation");
}
