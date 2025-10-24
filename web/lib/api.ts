// web/lib/api.ts
import { ChatRequest, ChatResponse, SearchRequest, SearchResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || ""; // e.g. https://searchsphere-backend-...run.app

function api(path: string) {
  // If a backend base is set, call it directly; else rely on Netlify proxy (/api/*)
  return API_BASE ? `${API_BASE}${path}` : `/api${path}`;
}

export async function apiSearch(
  payload: SearchRequest,
  abortSignal?: AbortSignal
): Promise<SearchResponse> {
  const url = api("/api/search");
  const t0 = performance.now?.() ?? Date.now();
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal: abortSignal
  });
  if (!res.ok) throw new Error(`Search failed: ${res.status}`);
  const data = (await res.json()) as SearchResponse;
  (data as any).__latency_ms = (performance.now?.() ?? Date.now()) - t0;
  return data;
}

export async function apiChat(
  payload: ChatRequest,
  abortSignal?: AbortSignal
): Promise<ChatResponse & { __latency_ms: number }> {
  const url = api("/api/chat");
  const t0 = performance.now?.() ?? Date.now();
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal: abortSignal
  });
  if (!res.ok) throw new Error(`Chat failed: ${res.status}`);
  const data = (await res.json()) as ChatResponse;
  return Object.assign(data, { __latency_ms: (performance.now?.() ?? Date.now()) - t0 });
}

export async function apiMetrics(): Promise<{ search: any; chat: any; eval?: any }> {
  const url = api("/api/metrics");
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error(`Metrics failed: ${res.status}`);
  return res.json();
}

export async function apiRunEval(
  payload: unknown
): Promise<{ k: number; p_at_k: number; queries: number }> {
  // Backend route is /api/eval/precision (not /api/run-eval)
  const url = api("/api/eval/precision");
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error(`Run eval failed: ${res.status}`);
  return res.json();
}
