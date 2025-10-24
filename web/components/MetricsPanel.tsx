"use client";

import { useEffect, useState } from "react";
import { apiMetrics } from "@/lib/api";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts";

type Row = { label: string; count: number; p50_ms: number; p95_ms: number; samples: number };
type EvalRow = { k: number; p_at_k: number; runs: number };
type Point = { t: string; p50: number; p95: number };

// Minimal shape we expect from /api/metrics; eval is optional
type MetricsResponse = {
  search: { count: number; p50_ms: number; p95_ms: number; samples: number };
  chat: { count: number; p50_ms: number; p95_ms: number; samples: number };
  eval?: EvalRow;
};

export default function MetricsPanel() {
  const [rows, setRows] = useState<Row[]>([
    { label: "Search", count: 0, p50_ms: 0, p95_ms: 0, samples: 0 },
    { label: "Chat", count: 0, p50_ms: 0, p95_ms: 0, samples: 0 },
  ]);
  const [evalRow, setEvalRow] = useState<EvalRow>({ k: 10, p_at_k: 0, runs: 0 });
  const [error, setError] = useState<string | null>(null);
  const [chartData, setChartData] = useState<Point[]>([]);

  async function refresh() {
    try {
      const m = (await apiMetrics()) as MetricsResponse;

      setRows([
        { label: "Search", ...m.search },
        { label: "Chat", ...m.chat },
      ]);

      if ("eval" in m && m.eval) setEvalRow(m.eval);

      const now = new Date();
      const label = now.toLocaleTimeString(undefined, { hour12: false });
      setChartData((prev) => [
        ...prev.slice(-30),
        { t: label, p50: m.search.p50_ms, p95: m.search.p95_ms },
      ]);

      setError(null);
    } catch (e: any) {
      setError(e?.message ?? "Failed");
    }
  }

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 10000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="p-2 border rounded-md bg-white/5">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold">Metrics</h3>
        <button className="text-xs underline" onClick={refresh}>
          Refresh
        </button>
      </div>
      {error && <div className="text-xs text-red-500 mb-2">{error}</div>}

      {/* Table */}
      <div className="text-sm">
        <div className="grid grid-cols-5 gap-2 mb-1 text-gray-500">
          <div>Type</div>
          <div>Count</div>
          <div>p50</div>
          <div>p95</div>
          <div>Samples</div>
        </div>
        {rows.map((r) => (
          <div key={r.label} className="grid grid-cols-5 gap-2 py-1 border-t">
            <div>{r.label}</div>
            <div>{r.count}</div>
            <div>{r.p50_ms.toFixed(0)} ms</div>
            <div>{r.p95_ms.toFixed(0)} ms</div>
            <div>{r.samples}</div>
          </div>
        ))}
      </div>

      {/* Chart (fixed-size wrapper prevents Recharts width/height -1 warning) */}
      <div className="mt-3 w-full h-[260px] min-h-[260px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="t" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="p50" name="p50 (ms)" dot={false} />
            <Line type="monotone" dataKey="p95" name="p95 (ms)" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Evaluation */}
      <div className="mt-3 border-t pt-2 text-sm">
        <div className="flex items-center justify-between">
          <div className="font-medium">Evaluation</div>
          <div className="text-xs text-gray-500">runs: {evalRow.runs}</div>
        </div>
        <div className="mt-1">
          Precision@{evalRow.k}:{" "}
          <span className="font-semibold">{(evalRow.p_at_k * 100).toFixed(1)}%</span>
        </div>
      </div>
    </div>
  );
}
