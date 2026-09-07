import React from "react";
import {
  ResponsiveContainer,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  ReferenceLine,
  Area,
  ComposedChart,
} from "recharts";
import { Satellite } from "lucide-react";

interface NDVIPoint {
  month: string;
  baseline_ndvi: number;
  observed_ndvi: number;
  stress_threshold: number;
  season?: string;
}

interface NDVITrajectoryProps {
  data?: NDVIPoint[];
  className?: string;
}

export const NDVITrajectoryPlot: React.FC<NDVITrajectoryProps> = ({ data, className = "" }) => {
  const points = data && data.length > 0 ? data : [
    { month: "Jun", baseline_ndvi: 0.32, observed_ndvi: 0.35, stress_threshold: 0.25, season: "Kharif Sowing" },
    { month: "Jul", baseline_ndvi: 0.48, observed_ndvi: 0.52, stress_threshold: 0.30, season: "Kharif Growth" },
    { month: "Aug", baseline_ndvi: 0.65, observed_ndvi: 0.68, stress_threshold: 0.40, season: "Kharif Peak" },
    { month: "Sep", baseline_ndvi: 0.72, observed_ndvi: 0.74, stress_threshold: 0.45, season: "Kharif Harvest" },
    { month: "Oct", baseline_ndvi: 0.42, observed_ndvi: 0.40, stress_threshold: 0.28, season: "Post-Harvest" },
    { month: "Nov", baseline_ndvi: 0.38, observed_ndvi: 0.42, stress_threshold: 0.26, season: "Rabi Sowing" },
    { month: "Dec", baseline_ndvi: 0.55, observed_ndvi: 0.58, stress_threshold: 0.35, season: "Rabi Growth" },
    { month: "Jan", baseline_ndvi: 0.68, observed_ndvi: 0.71, stress_threshold: 0.42, season: "Rabi Peak" },
    { month: "Feb", baseline_ndvi: 0.70, observed_ndvi: 0.69, stress_threshold: 0.44, season: "Rabi Harvest" },
    { month: "Mar", baseline_ndvi: 0.35, observed_ndvi: 0.33, stress_threshold: 0.25, season: "Zaid Prep" },
    { month: "Apr", baseline_ndvi: 0.30, observed_ndvi: 0.32, stress_threshold: 0.22, season: "Zaid Fallow" },
    { month: "May", baseline_ndvi: 0.28, observed_ndvi: 0.29, stress_threshold: 0.20, season: "Pre-Monsoon" },
  ];

  return (
    <div className={`rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm hover:shadow-md transition-shadow ${className}`}>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-semibold text-slate-900">
              Sentinel-2 10m Multi-Spectral Crop Vigor (NDVI)
            </h3>
            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 ring-1 ring-emerald-200">
              <Satellite className="h-3.5 w-3.5 text-emerald-600" />
              10m Resolution
            </span>
          </div>
          <p className="mt-0.5 text-xs text-slate-500">
            12-Month vegetative index trajectory across Kharif, Rabi, and Zaid agricultural crop cycles
          </p>
        </div>

        <div className="flex items-center gap-3 text-xs">
          <div className="rounded-lg bg-slate-50 px-3 py-1.5 text-slate-600 border border-slate-200/80">
            <span className="text-slate-500">Peak Vigor: </span>
            <span className="font-mono font-bold text-emerald-700">0.74 (Kharif)</span>
          </div>
          <div className="rounded-lg bg-slate-50 px-3 py-1.5 text-slate-600 border border-slate-200/80">
            <span className="text-slate-500">Status: </span>
            <span className="font-semibold text-emerald-700">Normal / Healthy Canopy</span>
          </div>
        </div>
      </div>

      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={points} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis
              dataKey="month"
              tick={{ fill: "#64748b", fontSize: 11 }}
              label={{ value: "Month & Agri Season", position: "insideBottom", offset: -12, fill: "#64748b", fontSize: 12 }}
            />
            <YAxis
              domain={[0.1, 0.9]}
              tick={{ fill: "#64748b", fontSize: 11 }}
              tickFormatter={(v) => v.toFixed(2)}
              label={{ value: "NDVI Index (-1.0 to +1.0)", angle: -90, position: "insideLeft", offset: 10, fill: "#64748b", fontSize: 12 }}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const d = payload[0].payload;
                  return (
                    <div className="rounded-xl border border-slate-200 bg-white/95 p-2.5 text-xs shadow-xl backdrop-blur">
                      <p className="font-bold text-slate-900">{d.month} — {d.season}</p>
                      <p className="text-emerald-700 mt-1">Observed NDVI: <strong>{d.observed_ndvi}</strong></p>
                      <p className="text-blue-700">5-Yr Baseline: {d.baseline_ndvi}</p>
                      <p className="text-rose-600">Crop Stress Line: {d.stress_threshold}</p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: "11px", color: "#475569" }} />
            <ReferenceLine
              y={0.25}
              stroke="#dc2626"
              strokeDasharray="4 4"
              label={{ value: "Crop Failure / Drought Warning (0.25)", fill: "#dc2626", fontSize: 10, position: "insideBottomRight" }}
            />
            <Area
              type="monotone"
              dataKey="baseline_ndvi"
              name="5-Yr Regional Norm (Normal Band)"
              fill="#0284c7"
              stroke="#0284c7"
              fillOpacity={0.08}
            />
            <Line
              type="monotone"
              dataKey="observed_ndvi"
              name="Farm Parcel Observed NDVI"
              stroke="#059669"
              strokeWidth={2.5}
              dot={{ r: 4, fill: "#059669" }}
              activeDot={{ r: 6, fill: "#10b981" }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-3 rounded-xl bg-emerald-50/70 px-3.5 py-2.5 text-xs text-emerald-950 border border-emerald-200">
        <span className="font-semibold text-emerald-800">Agricultural Underwriting Story:</span> Farm parcel maintained healthy vegetative vigor through both Kharif harvest (0.74) and Rabi harvest (0.69). Consistently above the 0.25 drought stress threshold, confirming verifiable farm productivity without requiring manual crop cutting experiments.
      </div>
    </div>
  );
};
