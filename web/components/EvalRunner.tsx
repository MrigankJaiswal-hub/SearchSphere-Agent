"use client";

import { useRef, useState } from "react";
import { apiRunEval } from "@/lib/api";

export default function EvalRunner() {
  const [k, setK] = useState<number>(10);
  const [jsonText, setJsonText] = useState<string>('{"filters": null, "items": []}');
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement | null>(null);

  async function run() {
    try {
      setBusy(true); setMsg(null);
      const payload = JSON.parse(jsonText);
      payload.k = k;
      const out = await apiRunEval(payload);
      setMsg(`Precision@${out.k}: ${(out.p_at_k * 100).toFixed(1)}% over ${out.queries} queries`);
    } catch (e: any) {
      setMsg(e?.message ?? "Failed");
    } finally {
      setBusy(false);
    }
  }

  async function onFile(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (!f) return;
    const text = await f.text();
    setJsonText(text);
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold">Run Evaluation</h3>
        <div className="text-xs text-gray-500">Paste or upload your groundtruth.json</div>
      </div>

      <div className="mb-2">
        <label className="text-sm font-medium">K</label>
        <input
          type="number"
          min={1}
          max={100}
          value={k}
          onChange={(e) => setK(parseInt(e.target.value || "10"))}
          className="input mt-1"
        />
      </div>

      <textarea
        className="input !h-40"
        value={jsonText}
        onChange={(e) => setJsonText(e.target.value)}
        placeholder='{"filters": null, "items": [{"query":"...", "relevant_ids":["file::chunk::0"]}]}'
      />
      <div className="mt-2 flex items-center gap-2">
        <input ref={fileRef} type="file" accept="application/json" className="hidden" onChange={onFile} />
        <button className="btn" onClick={() => fileRef.current?.click()}>Upload JSON</button>
        <button className="btn bg-brand-500 text-white" onClick={run} disabled={busy}>
          {busy ? "Running…" : "Run Evaluation"}
        </button>
      </div>

      {msg && <div className="mt-2 text-sm text-gray-700">{msg}</div>}
      <div className="mt-2 text-xs text-gray-500">
        After running, the Metrics panel auto-refresh (every 5s) will show the latest Precision@K.
      </div>
    </div>
  );
}
