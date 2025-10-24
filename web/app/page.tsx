// app/page.tsx
"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Chat from "@/components/Chat";
import Filters from "@/components/Filters";
import { apiSearch } from "@/lib/api";
import { SearchHit, SearchResponse } from "@/lib/types";
import clsx from "clsx";
import MetricsPanel from "@/components/MetricsPanel";
import EvalRunner from "@/components/EvalRunner";
import { ResultList } from "@/components/ResultCard"; // NOTE: file must be ResultCard.tsx (capital C)
import { motion, AnimatePresence } from "framer-motion";

export default function HomePage() {
  const [query, setQuery] = useState("How does hybrid search work?");
  const [team, setTeam] = useState<string[]>([]);
  const [docType, setDocType] = useState<string[]>([]);
  const [since, setSince] = useState<string | undefined>();
  const [results, setResults] = useState<SearchHit[]>([]);
  const [loading, setLoading] = useState(false);
  const [latency, setLatency] = useState<number | null>(null);
  const ctrlRef = useRef<AbortController | null>(null);

  const filters = useMemo(
    () => ({ team, doc_type: docType, since }),
    [team, docType, since]
  );

  async function runSearch() {
    if (ctrlRef.current) ctrlRef.current.abort();
    ctrlRef.current = new AbortController();
    setLoading(true);
    const t0 = performance.now();

    try {
      const q = (query ?? "").trim();
      const effectiveQuery = q.length ? q : "*"; // <-- avoid 422s / show something
      const res: SearchResponse & { __latency_ms?: number } = await apiSearch(
        { query: effectiveQuery, k: 10, filters },
        ctrlRef.current.signal
      );
      setResults(res.results || []);
      setLatency(
        typeof res.__latency_ms === "number"
          ? res.__latency_ms
          : performance.now() - t0
      );
    } catch (e: any) {
      if (e?.name === "AbortError" || e?.code === 20) return;
      console.error(e);
      setResults([]);
      setLatency(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    runSearch();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const containerVariants = {
    hidden: { opacity: 0, y: 8 },
    show: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.35, staggerChildren: 0.06 },
    },
  } as const;

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 grid grid-cols-1 lg:grid-cols-3 gap-6 min-h-[calc(100vh-112px)]">
      {/* Main: search + results */}
      <section className="lg:col-span-2 space-y-4">
        <motion.div
          className="card mb-2 overflow-hidden relative"
          variants={containerVariants}
          initial="hidden"
          animate="show"
        >
          <div className="flex flex-col gap-2">
            <label className="text-sm font-medium">Ask your data</label>

            <div className="flex gap-2 relative">
              <input
                className="input"
                placeholder="e.g., Summarize FinOps optimization insights"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && runSearch()}
                aria-label="Search query"
              />
              <motion.button
                whileTap={{ scale: 0.96 }}
                whileHover={{ scale: 1.04 }}
                transition={{ type: "spring", stiffness: 260, damping: 16 }}
                onClick={runSearch}
                className="btn bg-brand-500 text-white"
              >
                Search
              </motion.button>

              {/* Glow loading bar */}
              <AnimatePresence>
                {loading && (
                  <motion.div
                    key="loading-bar"
                    initial={{ width: "0%" }}
                    animate={{ width: "100%" }}
                    exit={{ opacity: 0 }}
                    transition={{
                      duration: 1.0,
                      ease: "easeInOut",
                      repeat: Infinity,
                    }}
                    className="absolute bottom-0 left-0 h-[3px] bg-gradient-to-r from-brand-500 via-pink-500 to-yellow-400 rounded-full shadow-[0_0_8px_rgba(0,0,0,0.2)]"
                  />
                )}
              </AnimatePresence>
            </div>

            <div className="flex items-center gap-2 text-xs text-gray-500">
              <span className="badge">Hybrid (KNN + BM25)</span>
              <span className="badge">Citations</span>
              <span
                className={clsx(
                  "badge",
                  latency ? "border-brand-500 text-brand-700" : ""
                )}
                title={latency ? `${latency.toFixed(0)} ms` : undefined}
              >
                {latency ? `Search ${latency.toFixed(0)} ms` : "—"}
              </span>
            </div>

            {/* --- search tips --- */}
            <div className="text-xs text-gray-400 mt-1">
              💡 Try:
              <span className="ml-1 italic">"hybrid search OR vector"</span>,
              <span className="ml-1 italic">"team:finops doc:pdf"</span>,
              <span className="ml-1 italic">"since:2025-10-01"</span>
            </div>
          </div>
        </motion.div>

        {/* Animated results */}
        <ResultList
          items={results}
          loading={loading}
          onClearFilters={() => {
            setTeam([]);
            setDocType([]);
            setSince(undefined);
            setQuery("");
          }}
        />
      </section>

      {/* Sidebar: sticky so the right column doesn’t leave a black hole */}
      <aside className="lg:col-span-1 space-y-6 lg:sticky lg:top-6 self-start">
        <motion.div
          className="card"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, ease: "easeOut" }}
        >
          <Filters
            team={team}
            setTeam={setTeam}
            docType={docType}
            setDocType={setDocType}
            since={since}
            setSince={setSince}
          />
        </motion.div>

        <motion.div
          className="card"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, ease: "easeOut", delay: 0.05 }}
        >
          <MetricsPanel />
        </motion.div>

        <motion.div
          className="card"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, ease: "easeOut", delay: 0.1 }}
        >
          <EvalRunner />
        </motion.div>

        <motion.div
          className="card"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, ease: "easeOut", delay: 0.15 }}
        >
          <Chat />
        </motion.div>
      </aside>
    </div>
  );
}
