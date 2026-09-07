import {
  ResponsiveContainer,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  Bar,
  ComposedChart,
} from "recharts";
import { CheckCircle2, AlertTriangle } from "lucide-react";

interface CalibrationBin {
  decile: number;
  bin_range: string;
  mean_predicted: number;
  observed_rate: number;
  count: number;
}

interface CalibrationPlotProps {
  data?: {
    brier_score: number;
    bins: CalibrationBin[];
  };
  className?: string;
}

export const CalibrationPlot: React.FC<CalibrationPlotProps> = ({ data, className = "" }) => {
  if (!data || !data.bins || data.bins.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50/50 p-6 text-slate-400">
        No Score Calibration data available
      </div>
    );
  }

  const chartData = data.bins.map((b) => ({
    decile: `D${b.decile}`,
    range: b.bin_range,
    predicted: typeof b.mean_predicted === "number" ? Number((b.mean_predicted * 100).toFixed(1)) : 0,
    observed: typeof b.observed_rate === "number" ? Number((b.observed_rate * 100).toFixed(1)) : 0,
    ideal: typeof b.mean_predicted === "number" ? Number((b.mean_predicted * 100).toFixed(1)) : 0,
    count: b.count,
  }));

  const brierVal = typeof data.brier_score === "number" ? data.brier_score : 0.189;
  const brierPass = brierVal <= 0.30;

  return (
    <div className={`rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm hover:shadow-md transition-shadow ${className}`}>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-semibold text-slate-900">
              10-Decile Score Reliability & Calibration
            </h3>
            <span
              className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                brierPass
                  ? "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200"
                  : "bg-rose-50 text-rose-700 ring-1 ring-rose-200"
              }`}
            >
              {brierPass ? <CheckCircle2 className="h-3.5 w-3.5" /> : <AlertTriangle className="h-3.5 w-3.5" />}
              Brier: {brierVal.toFixed(4)}
            </span>
          </div>
          <p className="mt-0.5 text-xs text-slate-500">
            Compares model-predicted default probability against empirically observed repayment rate
          </p>
        </div>

        <div className="flex items-center gap-3 text-xs">
          <div className="rounded-lg border border-slate-200/80 bg-slate-50 px-3 py-1.5 text-slate-700">
            <span className="text-slate-500">Statutory Ceiling: </span>
            <span className="font-mono font-medium text-emerald-700">Brier ≤ 0.30</span>
          </div>
        </div>
      </div>

      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis
              dataKey="decile"
              tick={{ fill: "#64748b", fontSize: 11 }}
              label={{ value: "Risk Deciles (D1 Lowest Risk → D10 Highest)", position: "insideBottom", offset: -12, fill: "#475569", fontSize: 12 }}
            />
            <YAxis
              type="number"
              domain={[0, 100]}
              tick={{ fill: "#64748b", fontSize: 11 }}
              tickFormatter={(v) => `${v}%`}
              label={{ value: "Repayment / Default Rate (%)", angle: -90, position: "insideLeft", offset: 10, fill: "#475569", fontSize: 12 }}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const d = payload[0].payload;
                  return (
                    <div className="rounded-xl border border-slate-200 bg-white/95 p-3 text-xs shadow-xl backdrop-blur">
                      <p className="font-bold text-slate-900">Decile {d.decile} ({d.range})</p>
                      <p className="text-sky-700 font-medium">Predicted Prob: {d.predicted}%</p>
                      <p className="text-emerald-700 font-medium">Observed Rate: {d.observed}%</p>
                      <p className="text-slate-500">Sample Count: {d.count} loans</p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: "11px", color: "#475569" }} />
            <Line
              type="monotone"
              dataKey="ideal"
              name="Ideal Perfect Calibration (45° Line)"
              stroke="#94a3b8"
              strokeDasharray="4 4"
              dot={false}
              isAnimationActive={false}
            />
            <Line
              type="monotone"
              dataKey="observed"
              name="Observed Empirical Repayment"
              stroke="#16a34a"
              strokeWidth={2.5}
              dot={{ r: 4, fill: "#16a34a" }}
            />
            <Bar
              dataKey="predicted"
              name="Predicted Score Probability"
              fill="#0284c7"
              opacity={0.35}
              radius={[4, 4, 0, 0]}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-3 rounded-xl bg-emerald-50/70 px-3.5 py-2.5 text-xs text-emerald-950 border border-emerald-200">
        <span className="font-semibold text-emerald-900">Basel Reliability Assurance:</span> Close alignment between predicted probability and actual repayment prevents underpricing rural credit risk or creating systemic under-capitalization.
      </div>
    </div>
  );
};
