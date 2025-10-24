// web/components/ResultCard.tsx
"use client";

import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { SearchHit } from "@/lib/types";

/** Prefer normalized fields; fallback to legacy _source/highlight */
function titleOf(h: SearchHit) {
  return (
    h.title ||
    h._source?.title ||
    h._source?.doc_type ||
    h._source?.team ||
    "Untitled"
  );
}

function snippetOf(h: SearchHit) {
  if (h.snippet && h.snippet.trim()) return h.snippet;
  const hi = h.highlight?.text;
  if (Array.isArray(hi) && hi[0]) return hi[0];
  const raw = h._source?.text || "";
  const s = raw.trim();
  return s ? s.slice(0, 240) : "No snippet available.";
}

function urlOf(h: SearchHit) {
  return h.url ?? h._source?.url ?? null;
}

function metaOf(h: SearchHit) {
  const team = h.team ?? h._source?.team;
  const dt = h.doc_type ?? h._source?.doc_type;
  const page = h._source?.page_num ? `p.${h._source?.page_num}` : null;
  const parts = [team, dt, page].filter(Boolean);
  return parts.length ? parts.join(" • ") : null;
}

function scoreOf(h: SearchHit) {
  return typeof h.score === "number" ? h.score : h._score;
}

export function ResultCard({ hit }: { hit: SearchHit }) {
  const title = titleOf(hit);
  const snippet = snippetOf(hit);
  const url = urlOf(hit);
  const meta = metaOf(hit);
  const score = scoreOf(hit);

  const badgeDocType = hit.doc_type ?? hit._source?.doc_type;
  const badgeTeam = hit.team ?? hit._source?.team;

  return (
    <motion.article
      layout
      initial={{ opacity: 0, scale: 0.98, y: 10 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.97, y: -10 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className="rounded-xl border p-4 hover:shadow-sm transition bg-white"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="font-medium text-gray-900 truncate">
            {url ? (
              <a href={url} target="_blank" rel="noreferrer" className="hover:underline">
                {title}
              </a>
            ) : (
              title
            )}
          </h3>

          {/* tiny badges for meta */}
          <div className="flex items-center gap-1 mt-1">
            {badgeDocType && <span className="badge text-[10px]">{badgeDocType}</span>}
            {badgeTeam && <span className="badge text-[10px]">{badgeTeam}</span>}
            {typeof score === "number" && (
              <span className="badge text-[10px] bg-brand-50 text-brand-700">
                score {score.toFixed(2)}
              </span>
            )}
          </div>

          {meta && <div className="text-[11px] text-gray-500 mt-1">{meta}</div>}
        </div>
      </div>

      {snippet && (
        <p className="mt-2 text-sm text-gray-700 line-clamp-3">
          <span dangerouslySetInnerHTML={{ __html: snippet }} />
        </p>
      )}
    </motion.article>
  );
}

export function ResultCardSkeleton() {
  return (
    <div className="rounded-xl border p-4 bg-white animate-pulse">
      <div className="h-4 w-40 bg-gray-200 rounded" />
      <div className="mt-2 h-3 w-24 bg-gray-200 rounded" />
      <div className="mt-3 space-y-2">
        <div className="h-3 w-full bg-gray-200 rounded" />
        <div className="h-3 w-11/12 bg-gray-200 rounded" />
        <div className="h-3 w-9/12 bg-gray-200 rounded" />
      </div>
    </div>
  );
}

export function EmptyState({ onClear }: { onClear?: () => void }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl border p-6 bg-white text-center"
    >
      <div className="text-gray-900 font-medium">No results</div>
      <p className="text-sm text-gray-500 mt-1">Try another query or clear filters.</p>
      {onClear && (
        <button onClick={onClear} className="btn mt-3 border-gray-300 hover:bg-gray-50">
          Clear filters
        </button>
      )}
    </motion.div>
  );
}

export function ResultList({
  items,
  loading,
  onClearFilters,
  skeletonCount = 4,
}: {
  items: SearchHit[];
  loading: boolean;
  onClearFilters?: () => void;
  skeletonCount?: number;
}) {
  if (loading) {
    return (
      <div className="grid gap-4">
        {Array.from({ length: skeletonCount }).map((_, i) => (
          <ResultCardSkeleton key={i} />
        ))}
      </div>
    );
  }
  if (!items || items.length === 0) {
    return <EmptyState onClear={onClearFilters} />;
  }
  return (
    <AnimatePresence mode="popLayout">
      <motion.div layout className="grid gap-4" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.3 }}>
        {items.map((hit, i) => (
          <ResultCard key={(hit.id ?? hit._id ?? i).toString()} hit={hit} />
        ))}
      </motion.div>
    </AnimatePresence>
  );
}
