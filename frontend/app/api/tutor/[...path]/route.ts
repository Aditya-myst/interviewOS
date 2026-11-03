import { proxyToApi } from "@/lib/proxy";

export async function GET(request: Request, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  return proxyToApi(request, path, "tutor");
}

export async function POST(request: Request, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  return proxyToApi(request, path, "tutor");
}
