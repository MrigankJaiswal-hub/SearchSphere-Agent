import { NextRequest, NextResponse } from "next/server";
import { getBackendBase } from "../_backend";

export const dynamic = "force-dynamic";

export async function POST(req: NextRequest) {
  const base = getBackendBase();
  const t0 = Date.now();
  try {
    const bodyText = await req.text();
    const r = await fetch(`${base}/api/search`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: bodyText,
    });

    const upstreamText = await r.text();
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
      return new NextResponse(upstreamText, {
        status: r.status,
        headers: { "content-type": r.headers.get("content-type") || "application/json" },
      });
    }
  } catch (err: any) {
    return NextResponse.json({ error: err?.message ?? "proxy_failed" }, { status: 500 });
  }
}
