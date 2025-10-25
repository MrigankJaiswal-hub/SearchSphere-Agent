// web/app/api/run-eval/route.ts
import { NextRequest, NextResponse } from "next/server";
import { getBackendBase } from "../_backend";

// Ensure this runs as a Node function (needed on Netlify so fetch works as expected)
export const dynamic = "force-dynamic";
export const runtime = "nodejs";

type GroundTruth = {
  k?: number;
  filters?: any | null;
  items: Array<{ query: string; relevant_ids: string[] }>;
};

function safeParseJSON(text: string): any {
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

function normalizeGroundTruth(input: any): GroundTruth {
  // Accepts:
  // 1) { filters, items }           -> add k
  // 2) { k, filters, items }        -> pass-through (with defaults)
  // 3) any other shape -> throw
  if (!input || typeof input !== "object") {
    throw new Error("invalid_groundtruth: body must be JSON with { items }");
  }
  const items = input.items;
  if (!Array.isArray(items) || items.length === 0) {
    throw new Error("invalid_groundtruth: items[] required");
  }
  // validate items quickly
  for (const it of items) {
    if (!it || typeof it.query !== "string" || !Array.isArray(it.relevant_ids)) {
      throw new Error("invalid_groundtruth: each item must have query:string and relevant_ids:string[]");
    }
  }
  const k = typeof input.k === "number" && input.k > 0 ? input.k : 10;
  const filters = input.filters ?? null;
  return { k, filters, items };
}

export async function POST(req: NextRequest) {
  try {
    const base = getBackendBase();
    const raw = await req.text();

    // Accept either raw JSON text of the file OR a JSON object posted by the UI
    const parsed = raw ? safeParseJSON(raw) : {};
    if (!parsed) {
      // If somebody posted plain text that isn't JSON, bail clearly
      return NextResponse.json(
        { error: "invalid_json: expected JSON body (use groundtruth.json export)" },
        { status: 400 }
      );
    }

    // Some UIs may wrap the payload as { groundtruth: {...} }
    const candidate = parsed?.groundtruth ? parsed.groundtruth : parsed;
    const normalized: GroundTruth = normalizeGroundTruth(candidate);

    // Forward to backend /api/eval/precision
    const resp = await fetch(`${base}/api/eval/precision`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(normalized),
    });

    // Return backend result (JSON or text)
    const data = await resp.clone().json().catch(async () => await resp.text());
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
