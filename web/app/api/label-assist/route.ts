import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  const base = process.env.BACKEND_API_BASE!;
  const body = await req.text();
  const r = await fetch(`${base}/api/eval/label-assist`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body
  });
  const data = await r.text();
  return new NextResponse(data, { status: r.status, headers: { "Content-Type": "application/json" } });
}
