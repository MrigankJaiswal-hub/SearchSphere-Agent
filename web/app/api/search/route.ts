// web/app/api/search/route.ts
import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

function backendBase() {
  // Prefer explicit public var for the browser, but also accept common alternates.
  return (
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    process.env.BACKEND_URL ||
    process.env.NEXT_PUBLIC_BACKEND_URL ||
    process.env.BACKEND_API_BASE ||
    "http://127.0.0.1:8080"
  );
}

export async function POST(req: NextRequest) {
  const t0 = Date.now();
  try {
    const bodyText = await req.text();

    const r = await fetch(`${backendBase()}/api/search`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: bodyText,
    });

    const upstreamText = await r.text();

    // Try to merge upstream JSON with a local latency measurement so the UI can show it.
    try {
      const json = JSON.parse(upstreamText || "{}");
      const elapsed = Date.now() - t0;
      if (typeof json === "object" && json) {
        json.__latency_ms = json.__latency_ms ?? elapsed;
      }
      return NextResponse.json(json, {
        status: r.status,
        headers: { "x-proxy-latency": String(elapsed) },
      });
    } catch {
      // Not JSON? Just forward through.
      return new NextResponse(upstreamText, {
        status: r.status,
        headers: { "content-type": r.headers.get("content-type") || "application/json" },
      });
    }
  } catch (err: any) {
    return NextResponse.json(
      { error: err?.message ?? "proxy_failed" },
      { status: 500 }
    );
  }
}
