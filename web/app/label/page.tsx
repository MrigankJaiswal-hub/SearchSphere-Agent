"use client";

import { useMemo, useState } from "react";

/** Candidate shape from /api/label-assist */
type Candidate = {
  chunk_id: string;
  title: string;
  page_num?: number;
  team?: string;
  doc_type?: string;
  score?: number;
  snippet?: string; // may contain <em> from ES highlights
};

async function fetchCandidates(query: string, k: number) {
  const base = process.env.NEXT_PUBLIC_API_BASE || "";
  const url = base
    ? `${base}/api/eval/label-assist`
    : `/api/eval/label-assist`; // Netlify proxy fallback

  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, k }),
  });

  if (!res.ok) throw new Error(`Label assist failed: ${res.status}`);
  return (await res.json()) as {
    query: string;
    k: number;
    candidates: Candidate[];
  };
}


function download(filename: string, text: string) {
  const blob = new Blob([text], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

/** Safe helper to shorten long ids visually */
function shortenId(id: string, left = 18, right = 8) {
  if (!id || id.length <= left + right + 3) return id;
  return `${id.slice(0, left)}…${id.slice(-right)}`;
}

export default function LabelPage() {
  const [query, setQuery] = useState("What is hybrid search?");
  const [k, setK] = useState(20);
  const [loading, setLoading] = useState(false);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [selected, setSelected] = useState<Record<string, boolean>>({});
  const [items, setItems] = useState<{ query: string; relevant_ids: string[] }[]>(
    []
  );

  const selectedCount = useMemo(
    () => Object.values(selected).filter(Boolean).length,
    [selected]
  );

  async function run() {
    setLoading(true);
    try {
      const data = await fetchCandidates(query, k);
      setCandidates(data.candidates);
      setSelected({});
    } catch (e) {
      console.error(e);
      setCandidates([]);
    } finally {
      setLoading(false);
    }
  }

  function addToGroundTruth() {
    const rel = Object.entries(selected)
      .filter(([, v]) => v)
      .map(([id]) => id);
    if (rel.length === 0) return;
    setItems((arr) => [...arr, { query, relevant_ids: rel }]);
    setSelected({});
  }

  function exportJson() {
    const payload = { filters: null, items };
    download("groundtruth.json", JSON.stringify(payload, null, 2));
  }

  function selectAll() {
    const next: Record<string, boolean> = {};
    for (const c of candidates) next[c.chunk_id] = true;
    setSelected(next);
  }

  function clearSelected() {
    setSelected({});
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-6">
      <h1 className="text-2xl font-semibold mb-4">Label Assist</h1>

      <div className="card mb-4">
        <div className="grid gap-3 sm:grid-cols-[1fr_auto_auto]">
          <input
            className="input"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter a query to label…"
            aria-label="Label Assist Query"
          />
          <input
            className="input sm:ml-2"
            type="number"
            min={5}
            max={100}
            value={k}
            onChange={(e) => setK(parseInt(e.target.value || "20"))}
            aria-label="K candidates"
            title="K (top candidates)"
          />
          <button
            className="btn bg-brand-500 text-white sm:ml-2"
            onClick={run}
            disabled={loading}
          >
            {loading ? "Loading…" : "Fetch candidates"}
          </button>
        </div>
        <div className="mt-2 text-xs text-gray-500">
          1) Fetch candidates • 2) Tick relevant chunks • 3) “Add to ground
          truth” • 4) Export JSON
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* ----------------- Candidates ----------------- */}
        <section className="card">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold">Candidates</h3>
            <div className="flex items-center gap-2">
              <button className="badge" onClick={selectAll} disabled={!candidates.length}>
                Select All
              </button>
              <button className="badge" onClick={clearSelected} disabled={!selectedCount}>
                Clear
              </button>
              <span className="badge">selected: {selectedCount}</span>
            </div>
          </div>

          <div className="space-y-2 max-h-[480px] overflow-auto pr-1">
            {candidates.map((c) => (
              <label
                key={c.chunk_id}
                className="flex gap-3 items-start border rounded-xl p-2"
              >
                <input
                  type="checkbox"
                  checked={!!selected[c.chunk_id]}
                  onChange={(e) =>
                    setSelected((s) => ({ ...s, [c.chunk_id]: e.target.checked }))
                  }
                  className="mt-1"
                />
                <div>
                  {/* Title + page number */}
                  <div className="text-sm font-medium">
                    {c.title}{" "}
                    {typeof c.page_num === "number" && (
                      <span className="text-gray-500">• p{c.page_num}</span>
                    )}
                  </div>

                  {/* Snippet (shows ES <em> highlights if present) */}
                  {c.snippet && (
                    <div
                      className="text-xs text-gray-700"
                      dangerouslySetInnerHTML={{ __html: c.snippet }}
                    />
                  )}

                  {/* Chips — render only when values exist (no "None:None") */}
                  <div className="mt-1 flex gap-2 flex-wrap text-[11px] text-gray-600">
                    {c.team && <span className="badge">team: {c.team}</span>}
                    {c.doc_type && <span className="badge">type: {c.doc_type}</span>}
                    {typeof c.page_num === "number" && (
                      <span className="badge">p.{c.page_num}</span>
                    )}
                    {typeof c.score === "number" && (
                      <span className="badge">score {c.score.toFixed(2)}</span>
                    )}
                    {/* always show id but shorten visual length; full value in title */}
                    <span className="badge" title={c.chunk_id}>
                      {shortenId(c.chunk_id)}
                    </span>
                  </div>
                </div>
              </label>
            ))}
            {candidates.length === 0 && (
              <div className="text-sm text-gray-500">No candidates yet.</div>
            )}
          </div>

          <div className="mt-3">
            <button
              className="btn"
              onClick={addToGroundTruth}
              disabled={selectedCount === 0}
            >
              Add to ground truth
            </button>
          </div>
        </section>

        {/* ----------------- Ground Truth ----------------- */}
        <section className="card">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold">Ground Truth</h3>
            <button className="text-xs underline" onClick={() => setItems([])}>
              Clear
            </button>
          </div>
          <div className="space-y-2 max-h-[480px] overflow-auto pr-1">
            {items.map((it, i) => (
              <div key={i} className="border rounded-xl p-2">
                <div className="text-sm font-medium">
                  Q{i + 1}: {it.query}
                </div>
                <div className="text-xs text-gray-600 break-words">
                  Relevant IDs: {it.relevant_ids.join(", ")}
                </div>
              </div>
            ))}
            {items.length === 0 && (
              <div className="text-sm text-gray-500">Nothing added yet.</div>
            )}
          </div>
          <div className="mt-3">
            <button
              className="btn bg-brand-500 text-white"
              onClick={exportJson}
              disabled={items.length === 0}
            >
              Export groundtruth.json
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}
