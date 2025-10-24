import { NextRequest, NextResponse } from "next/server";

const BASE = process.env.BACKEND_API_BASE || "http://127.0.0.1:8080";

export async function POST(req: NextRequest) {
  try {
    // Accept either text or JSON body gracefully
    let payload: any = {};
    const text = await req.text();
    if (text) {
      try {
        payload = JSON.parse(text);
      } catch {
        // If body wasn't JSON, forward raw text as-is
        payload = text;
      }
    }

    const resp = await fetch(new URL("/api/eval/precision", BASE), {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: typeof payload === "string" ? payload : JSON.stringify(payload),
    });

    // Try JSON, fall back to text
    const data =
      (await resp
        .clone()
        .json()
        .catch(async () => await resp.text())) ?? {};

    // Mirror backend status but avoid throwing on errors
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
