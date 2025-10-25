// web/lib/api.ts
import { ChatRequest, ChatResponse, SearchRequest, SearchResponse } from "./types";

/** Normalize a base URL (strip trailing `/` and `/api`) */
function normalizeBase(v?: string) {
  if (!v) return "";
  let s = v.trim();
  if (s.endsWith("/")) s = s.slice(0, -1);
  if (s.toLowerCase().endsWith("/api")) s = s.slice(0, -4);
  return s;
}

/**
 * If NEXT_PUBLIC_API_BASE is set (Netlify prod), call backend directly.
 * Otherwise use Next.js API routes (which proxy to backend).
 */
const PUBLIC_BASE = normalizeBase(process.env.NEXT_PUBLIC_API_BASE);

function apiUrl(path: string) {
  // path should be like "/search", "/chat", "/metrics", "/run-eval"
  if (PUBLIC_BASE) return `${PUBLIC_BASE}/api${path}`;
  return `/api${path}`; // Next.js app route proxy in dev/local
}

export async function apiSearch(payload: SearchRequest, abortSignal?: AbortSignal): Promise<SearchResponse> {
  const url = apiUrl("/search");
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

export async function apiChat(payload: ChatRequest, abortSignal?: AbortSignal): Promise<ChatResponse & { __latency_ms: number }> {
  const url = apiUrl("/chat");
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
  const url = apiUrl("/metrics");
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error(`Metrics failed: ${res.status}`);
  return res.json();
}

export async function apiRunEval(payload: unknown): Promise<{ k: number; p_at_k: number; queries: number }> {
  const url = apiUrl("/run-eval");
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error(`Run eval failed: ${res.status}`);
  return res.json();
}
