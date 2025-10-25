// web/app/api/label-assist/route.ts
import { NextRequest, NextResponse } from "next/server";
import { getBackendBase } from "../_backend";

export const dynamic = "force-dynamic";

export async function POST(req: NextRequest) {
  const base = getBackendBase();
  try {
    const bodyText = await req.text();

    const resp = await fetch(`${base}/api/eval/label-assist`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: bodyText || "{}",
    });

    const data =
      (await resp.clone().json().catch(async () => await resp.text())) ?? {};

    if (typeof data === "string") {
      return new NextResponse(data, {
        status: resp.status,
        headers: { "content-type": "application/json" },
      });
    }
    return NextResponse.json(data, { status: resp.status });
  } catch (err: any) {
    return NextResponse.json(
      { error: err?.message ?? "proxy_failed" },
      { status: 500 }
    );
  }
}
