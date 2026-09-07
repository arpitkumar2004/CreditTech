import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ReferenceLine,
  CartesianGrid,
} from "recharts";
import { CheckCircle2 } from "lucide-react";

interface KSCurvePoint {
  score: number;
  cum_bads_pct: number;
  cum_goods_pct: number;
  ks_gap: number;
}

interface KSPlotProps {
  data?: {
    max_ks: number;
    max_ks_score?: number;
    optimal_cutoff?: number;
    curve: KSCurvePoint[];
  };
  className?: string;
}

export const KSPlot: React.FC<KSPlotProps> = ({ data, className = "" }) => {
  if (!data || !data.curve || data.curve.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50/50 p-6 text-slate-400">
        No Kolmogorov-Smirnov data available
      </div>
    );
  }

  const maxCutoff = data.max_ks_score || data.optimal_cutoff || 650;
  const maxKSVal = typeof data.max_ks === "number" ? (data.max_ks * (data.max_ks <= 1.0 ? 100 : 1)).toFixed(1) : "0.0";

  const chartData = data.curve.map((pt) => ({
    score: pt.score,
    cum_bads_pct: typeof pt.cum_bads_pct === "number" ? pt.cum_bads_pct : 0,
    cum_goods_pct: typeof pt.cum_goods_pct === "number" ? pt.cum_goods_pct : 0,
    ks_gap: typeof pt.ks_gap === "number" ? Number((pt.ks_gap * (pt.ks_gap <= 1.0 ? 100 : 1)).toFixed(1)) : 0,
  }));

  return (
    <div className={`rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm hover:shadow-md transition-shadow ${className}`}>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-semibold text-slate-900">
              Kolmogorov-Smirnov (K-S) Separation Curve
            </h3>
            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 ring-1 ring-emerald-200">
              <CheckCircle2 className="h-3.5 w-3.5" />
              Max KS: {maxKSVal}%
            </span>
          </div>
          <p className="mt-0.5 text-xs text-slate-500">
            Cumulative distribution separation between defaults and solvent borrowers across score bands
          </p>
        </div>

        <div className="flex items-center gap-3 text-xs">
          <div className="rounded-lg border border-slate-200/80 bg-slate-50 px-3 py-1.5 text-slate-700">
            <span className="text-slate-500">Peak Cutoff: </span>
            <span className="font-mono font-bold text-amber-700">{maxCutoff}</span>
          </div>
          <div className="rounded-lg border border-slate-200/80 bg-slate-50 px-3 py-1.5 text-slate-700">
            <span className="text-slate-500">Regulatory Floor: </span>
            <span className="font-mono font-medium text-emerald-700">KS ≥ 15.0%</span>
          </div>
        </div>
      </div>

      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis
              dataKey="score"
              domain={[300, 900]}
              tick={{ fill: "#64748b", fontSize: 11 }}
              label={{ value: "Alternative Credit Score (300 - 900 Scale)", position: "insideBottom", offset: -12, fill: "#475569", fontSize: 12 }}
            />
            <YAxis
              type="number"
              domain={[0, 100]}
              tick={{ fill: "#64748b", fontSize: 11 }}
              tickFormatter={(v) => `${v}%`}
              label={{ value: "Cumulative % of Population", angle: -90, position: "insideLeft", offset: 10, fill: "#475569", fontSize: 12 }}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const d = payload[0].payload;
                  return (
                    <div className="rounded-xl border border-slate-200 bg-white/95 p-3 text-xs shadow-xl backdrop-blur">
                      <p className="font-bold text-slate-900">Score: {d.score}</p>
                      <p className="text-rose-600 font-medium">Cumulative Defaults: {d.cum_bads_pct}%</p>
                      <p className="text-emerald-700 font-medium">Cumulative Solvents: {d.cum_goods_pct}%</p>
                      <p className="font-semibold text-amber-700">K-S Gap: {d.ks_gap}%</p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: "11px", color: "#475569" }} />
            <ReferenceLine
              x={maxCutoff}
              stroke="#d97706"
              strokeDasharray="4 4"
              label={{
                value: `Max KS (${maxCutoff})`,
                position: "top",
                fill: "#b45309",
                fontSize: 11,
              }}
            />
            <Line
              type="monotone"
              dataKey="cum_bads_pct"
              name="Cumulative Defaults (Bads CDF)"
              stroke="#e11d48"
              strokeWidth={2}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="cum_goods_pct"
              name="Cumulative Solvents (Goods CDF)"
              stroke="#16a34a"
              strokeWidth={2}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="ks_gap"
              name="K-S Separation Gap"
              stroke="#d97706"
              strokeWidth={2.5}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-3 rounded-xl bg-amber-50/70 px-3.5 py-2.5 text-xs text-amber-950 border border-amber-200/80">
        <span className="font-semibold text-amber-900">Decision Story:</span> Peak K-S gap occurs at score {maxCutoff}, providing mathematical justification for the Underwriting STP boundary at score 650. Below this threshold, default density rises sharply.
      </div>
    </div>
  );
};
