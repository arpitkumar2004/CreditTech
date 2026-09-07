import React from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
  Cell,
} from "recharts";
import { ShieldCheck, AlertTriangle, AlertOctagon } from "lucide-react";

interface DriftRadarProps {
  data?: {
    status?: string;
    stability?: string;
    action_recommendation?: string;
    score_psi?: {
      psi: number;
      stability?: string;
      decile_breakdown?: Array<{ decile: number; expected_pct: number; actual_pct: number; psi_component: number }>;
    };
    feature_csi?: Record<string, number>;
  };
  className?: string;
}

export const DriftRadarPlot: React.FC<DriftRadarProps> = ({ data, className = "" }) => {
  const psiVal = typeof data?.score_psi?.psi === "number" ? data.score_psi.psi : 0.042;
  const stability = data?.stability || (psiVal < 0.10 ? "STABLE" : psiVal < 0.25 ? "MODERATE_DRIFT" : "SEVERE_DRIFT");
  const actionRec = data?.action_recommendation || "NORMAL_OPERATION";

  const featureCsi = data?.feature_csi || {
    shg_savings_consistency: 0.038,
    electricity_timeliness: 0.045,
    crop_ndvi_mean: 0.052,
    upi_regularity: 0.029,
    pm_kisan_regularity: 0.015,
  };

  const chartData = Object.entries(featureCsi).map(([feat, csi]) => ({
    feature: feat.replace(/_/g, " "),
    csi: typeof csi === "number" ? Number(csi.toFixed(3)) : 0,
  }));

  // Add overall score PSI
  chartData.unshift({
    feature: "★ Overall Score (PSI)",
    csi: typeof psiVal === "number" ? Number(psiVal.toFixed(3)) : 0.042,
  });

  const getBarColor = (val: number) => {
    if (val < 0.10) return "#059669"; // Stable (Emerald)
    if (val < 0.25) return "#d97706"; // Moderate (Amber)
    return "#dc2626"; // Severe (Red)
  };

  const getStatusBadge = () => {
    if (stability === "STABLE") {
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 ring-1 ring-emerald-200">
          <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
          STABLE (PSI &lt; 0.10)
        </span>
      );
    }
    if (stability === "MODERATE_DRIFT") {
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-semibold text-amber-700 ring-1 ring-amber-200">
          <AlertTriangle className="h-3.5 w-3.5 text-amber-600" />
          MODERATE DRIFT (0.10 - 0.25)
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-rose-50 px-2.5 py-0.5 text-xs font-semibold text-rose-700 ring-1 ring-rose-200">
        <AlertOctagon className="h-3.5 w-3.5 text-rose-600" />
        SEVERE DRIFT (PSI &gt; 0.25)
      </span>
    );
  };

  return (
    <div className={`rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm hover:shadow-md transition-shadow ${className}`}>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-semibold text-slate-900">
              Drift Radar: Population Stability (PSI) & Characteristic Shift (CSI)
            </h3>
            {getStatusBadge()}
          </div>
          <p className="mt-0.5 text-xs text-slate-500">
            Automated drift telemetry monitoring live applicant distribution against training calibration baseline
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <div className="rounded-lg bg-slate-50 px-3 py-1.5 text-slate-600 border border-slate-200/80">
            <span className="text-slate-500">Action: </span>
            <span className="font-mono font-semibold text-blue-700">{actionRec}</span>
          </div>
        </div>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 10, right: 30, left: 140, bottom: 10 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis
              type="number"
              domain={[0, 0.30]}
              tick={{ fill: "#64748b", fontSize: 11 }}
              tickFormatter={(v) => v.toFixed(2)}
            />
            <YAxis
              type="category"
              dataKey="feature"
              tick={{ fill: "#334155", fontSize: 11, fontWeight: 500 }}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const d = payload[0].payload;
                  return (
                    <div className="rounded-xl border border-slate-200 bg-white/95 p-2.5 text-xs shadow-xl backdrop-blur">
                      <p className="font-bold text-slate-900">{d.feature}</p>
                      <p className="text-blue-700 font-semibold mt-0.5">Index Value: {d.csi}</p>
                      <p className="text-slate-600">
                        {d.csi < 0.10 ? "Stable (<0.10)" : d.csi < 0.25 ? "Moderate Shift" : "Severe Drift (>0.25)"}
                      </p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <ReferenceLine
              x={0.10}
              stroke="#d97706"
              strokeDasharray="3 3"
              label={{ value: "Warning (0.10)", fill: "#d97706", fontSize: 10, position: "insideTopRight" }}
            />
            <ReferenceLine
              x={0.25}
              stroke="#dc2626"
              strokeDasharray="3 3"
              label={{ value: "Action Threshold (0.25)", fill: "#dc2626", fontSize: 10, position: "insideTopRight" }}
            />
            <Bar dataKey="csi" radius={[0, 4, 4, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getBarColor(entry.csi)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-3 flex items-center justify-between rounded-xl bg-slate-50 px-3.5 py-2.5 text-xs text-slate-700 border border-slate-200/80">
        <div>
          <span className="font-semibold text-blue-700">Closed-Loop Trigger Policy:</span> PSI &gt; 0.25 triggers automatic lockdown of straight-through lending, switching all automated decisions to manual branch underwriter review and initiating scheduled DPDP retraining.
        </div>
      </div>
    </div>
  );
};
