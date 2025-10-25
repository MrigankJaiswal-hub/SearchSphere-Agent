// web/app/api/eval/[...rest]/route.ts
import { NextRequest, NextResponse } from "next/server";
import { getBackendBase } from "../../_backend";

export const dynamic = "force-dynamic";

/**
 * Proxies any /api/eval/* to backend /api/eval/*
 * e.g. /api/eval/precision, /api/eval/label-assist, etc.
 */
export async function POST(
  req: NextRequest,
  { params }: { params: { rest: string[] } }
) {
  const base = getBackendBase();
  const path = (params?.rest || []).join("/");
  try {
    const bodyText = await req.text();
    const resp = await fetch(`${base}/api/eval/${path}`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: bodyText,
    });
    const text = await resp.text();
    return new NextResponse(text, {
      status: resp.status,
      headers: {
        "content-type":
          resp.headers.get("content-type") || "application/json",
      },
    });
  } catch (err: any) {
    return NextResponse.json(
      { error: err?.message ?? "proxy_failed" },
      { status: 500 }
    );
  }
}
