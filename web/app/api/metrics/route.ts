import { NextResponse } from "next/server";
import { getBackendBase } from "../_backend";

export const dynamic = "force-dynamic";

export async function GET() {
  const base = getBackendBase();
  try {
    const r = await fetch(`${base}/api/metrics`, { cache: "no-store" });
    const data = await r.json().catch(() => ({}));
    return NextResponse.json(data, { status: r.status });
  } catch (err: any) {
    return NextResponse.json({ error: err?.message ?? "proxy_failed" }, { status: 500 });
  }
}
