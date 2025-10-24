// app/api/run-eval/route.ts
import { NextRequest, NextResponse } from "next/server";

const PUBLIC_BASE = process.env.NEXT_PUBLIC_API_BASE || ""; // e.g. https://searchsphere-backend-...run.app

export async function POST(req: NextRequest) {
  try {
    // Accept either text or JSON body gracefully
    let payload: any = {};
    const text = await req.text();
    if (text) {
      try {
        payload = JSON.parse(text);
      } catch {
        payload = text; // forward raw text if not JSON
      }
    }

    // If PUBLIC_BASE is set, hit backend directly; else rely on Netlify proxy at /api/*
    const url = PUBLIC_BASE
      ? `${PUBLIC_BASE}/api/eval/precision`
      : `/api/eval/precision`;

    const resp = await fetch(url, {
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
