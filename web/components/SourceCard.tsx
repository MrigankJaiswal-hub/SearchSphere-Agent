import { SearchHit } from "@/lib/types";

export default function SourceCard({ hit }: { hit: SearchHit }) {
  const s = hit._source ?? {};
  const snippet = hit.highlight?.text?.[0] ?? (s.text ? s.text.slice(0, 220) + "…" : "");
  return (
    <article className="card">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h4 className="font-semibold">{s.title ?? s.page_num != null ? `Page ${s.page_num}` : "Untitled"}</h4>
          <div className="mt-1 text-sm text-gray-600">{snippet}</div>
          <div className="mt-2 flex gap-2 text-xs">
            {s.url ? (
              <a className="badge underline" href={s.url} target="_blank" rel="noreferrer">Open source</a>
            ) : (
              <span className="badge">local</span>
            )}
            {s.team && <span className="badge">team: {s.team}</span>}
            {s.doc_type && <span className="badge">type: {s.doc_type}</span>}
          </div>
        </div>
        <div className="text-xs text-gray-400">{typeof hit._score === "number" ? hit._score.toFixed(2) : ""}</div>
      </div>
    </article>
  );
}
