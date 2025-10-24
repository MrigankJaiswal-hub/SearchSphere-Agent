// axios/fetch wrapper
import { ChatRequest, ChatResponse, SearchRequest, SearchResponse } from "./types";

const isBrowser = typeof window !== "undefined";
const PUBLIC_BASE = process.env.NEXT_PUBLIC_API_BASE;
const PROXY_BASE = ""; // Next API routes live under /api

const base = isBrowser && PUBLIC_BASE ? PUBLIC_BASE : PROXY_BASE;

export async function apiSearch(payload: SearchRequest, abortSignal?: AbortSignal): Promise<SearchResponse> {
  const url = base ? `${base}/api/search` : `/api/search`;
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
  const url = base ? `${base}/api/chat` : `/api/chat`;
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

export async function apiMetrics(): Promise<{ search: any; chat: any }> {
  const url = (typeof window !== "undefined" && process.env.NEXT_PUBLIC_API_BASE)
    ? `${process.env.NEXT_PUBLIC_API_BASE}/api/metrics`
    : `/api/metrics`;
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error(`Metrics failed: ${res.status}`);
  return res.json();
}

export async function apiRunEval(payload: unknown): Promise<{ k: number; p_at_k: number; queries: number }> {
  const url = (typeof window !== "undefined" && process.env.NEXT_PUBLIC_API_BASE)
    ? `${process.env.NEXT_PUBLIC_API_BASE}/api/run-eval`
    : `/api/run-eval`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error(`Run eval failed: ${res.status}`);
  return res.json();
}
