// web/lib/types.ts
// Accept normalized hits from the backend while staying compatible
// with legacy ES-style hits.

export type SearchFilters = {
  team?: string[];
  doc_type?: string[];
  since?: string; // ISO date
};

export type SearchRequest = {
  query: string;
  k?: number;
  filters?: SearchFilters;
};

export type LegacySource = {
  title?: string;
  url?: string | null;
  text?: string;
  team?: string;
  doc_type?: string;
  page_num?: number;
};

// Normalized hit shape (what backend returns)
export type NormalizedHit = {
  id?: string;
  score?: number;
  index?: string;
  title?: string;
  url?: string | null;
  snippet?: string;
  team?: string | null;
  doc_type?: string | null;
};

// Keep legacy fields optional
export type SearchHit = NormalizedHit & {
  _id?: string;
  _score?: number;
  _source?: LegacySource;
  highlight?: { text?: string[] };
};

export type SearchResponse = {
  query?: string;
  k?: number;
  results: SearchHit[];
  mode?: "bm25" | "knn" | "hybrid" | "demo";
  __latency_ms?: number;
};

export type ChatRequest = {
  query: string;
  k?: number;
  filters?: SearchFilters;
};

export type ChatCitation = {
  id: number;
  title: string;
  url?: string | null;
  snippet?: string;
};

export type ChatResponse = {
  answer: string;
  citations: ChatCitation[];
  top_k_used: number;
  __latency_ms?: number;
};
