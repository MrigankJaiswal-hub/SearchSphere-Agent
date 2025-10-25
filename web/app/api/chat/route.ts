import { NextRequest, NextResponse } from "next/server";
import { getBackendBase } from "../_backend";

export const dynamic = "force-dynamic";

export async function POST(req: NextRequest) {
  const base = getBackendBase();
  try {
    const body = await req.text();
    const r = await fetch(`${base}/api/chat`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body,
    });
    const text = await r.text();
    return new NextResponse(text, {
      status: r.status,
      headers: { "content-type": r.headers.get("content-type") || "application/json" },
    });
  } catch (err: any) {
    return NextResponse.json({ error: err?.message ?? "proxy_failed" }, { status: 500 });
  }
}
