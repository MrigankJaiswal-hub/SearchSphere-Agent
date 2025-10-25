// web/lib/api.ts
import { ChatRequest, ChatResponse, SearchRequest, SearchResponse } from "./types";

function normalizeBase(v?: string) {
  if (!v) return "";
  let s = v.trim();
  if (s.endsWith("/")) s = s.slice(0, -1);
  if (s.toLowerCase().endsWith("/api")) s = s.slice(0, -4);
  return s;
}

const PUBLIC_BASE = normalizeBase(process.env.NEXT_PUBLIC_API_BASE);

// If PUBLIC_BASE is set, call backend directly; otherwise use Next.js proxy routes.
function apiUrl(path: string) {
  // `path` like "/search", "/chat", "/metrics", "/run-eval"
  if (PUBLIC_BASE) return `${PUBLIC_BASE}/api${path}`;
  return `/api${path}`; // Next app route proxies locally
}

export async function apiSearch(
  payload: SearchRequest,
  abortSignal?: AbortSignal
): Promise<SearchResponse> {
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

export async function apiChat(
  payload: ChatRequest,
  abortSignal?: AbortSignal
): Promise<ChatResponse & { __latency_ms: number }> {
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

export async function apiRunEval(
  payload: unknown
): Promise<{ k: number; p_at_k: number; queries: number }> {
  // IMPORTANT:
  // - In production (PUBLIC_BASE present), call backend's real endpoint: /api/eval/precision
  // - Locally (no PUBLIC_BASE), call the Next.js proxy route: /api/run-eval
  const url = PUBLIC_BASE
    ? `${PUBLIC_BASE}/api/eval/precision`
    : `/api/run-eval`;

  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error(`Run eval failed: ${res.status}`);
  return res.json();
}
