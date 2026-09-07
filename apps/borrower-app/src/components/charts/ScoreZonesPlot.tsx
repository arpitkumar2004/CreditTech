import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell,
} from "recharts";
import { Layers, CheckCircle, HelpCircle, XCircle } from "lucide-react";

interface HistogramBin {
  range: string;
  zone: string;
  count: number;
  percentage?: number;
  pct?: number;
}

interface ScoreZonesPlotProps {
  data?: {
    total_evaluated?: number;
    stp_approve_count?: number;
    stp_approve_pct?: number;
    manual_review_count?: number;
    manual_review_pct?: number;
    actionable_reject_count?: number;
    actionable_reject_pct?: number;
    zones_summary?: {
      approve_stp_pct: number;
      review_manual_pct: number;
      reject_actionable_pct: number;
    };
    histogram: HistogramBin[];
  };
  className?: string;
}

export const ScoreZonesPlot: React.FC<ScoreZonesPlotProps> = ({ data, className = "" }) => {
  if (!data || !data.histogram || data.histogram.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50/50 p-6 text-slate-400">
        No Score Distribution data available
      </div>
    );
  }

  const stpPct = data.stp_approve_pct ?? data.zones_summary?.approve_stp_pct ?? 0.0;
  const reviewPct = data.manual_review_pct ?? data.zones_summary?.review_manual_pct ?? 42.8;
  const rejectPct = data.actionable_reject_pct ?? data.zones_summary?.reject_actionable_pct ?? 57.2;

  const chartData = data.histogram.map((item) => ({
    range: item.range,
    count: item.count,
    pct: item.percentage ?? item.pct ?? 0,
    zone: item.zone,
  }));

  const getZoneColor = (zone: string) => {
    switch (zone) {
      case "APPROVE":
        return "#16a34a"; // Green
      case "REVIEW":
        return "#f59e0b"; // Amber
      case "REJECT":
      default:
        return "#e11d48"; // Rose
    }
  };

  return (
    <div className={`rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm hover:shadow-md transition-shadow ${className}`}>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-3">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-semibold text-slate-900">
              3-Zone Score Decision Spectrum
            </h3>
            <span className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-semibold text-blue-700 ring-1 ring-blue-200">
              <Layers className="h-3.5 w-3.5" />
              Scale 300 - 900
            </span>
          </div>
          <p className="mt-0.5 text-xs text-slate-500">
            Automated STP Approval (≥650) · Officer Review (550-649) · Actionable Recourse (&lt;550)
          </p>
        </div>

        {/* 3 Zone metric badges */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <div className="flex items-center gap-1.5 rounded-lg border border-emerald-200 bg-emerald-50/80 px-2.5 py-1 text-emerald-800">
            <CheckCircle className="h-3.5 w-3.5 text-emerald-600" />
            <span>STP Approve: <strong>{stpPct}%</strong></span>
          </div>
          <div className="flex items-center gap-1.5 rounded-lg border border-amber-200 bg-amber-50/80 px-2.5 py-1 text-amber-800">
            <HelpCircle className="h-3.5 w-3.5 text-amber-600" />
            <span>Review: <strong>{reviewPct}%</strong></span>
          </div>
          <div className="flex items-center gap-1.5 rounded-lg border border-rose-200 bg-rose-50/80 px-2.5 py-1 text-rose-800">
            <XCircle className="h-3.5 w-3.5 text-rose-600" />
            <span>Reject: <strong>{rejectPct}%</strong></span>
          </div>
        </div>
      </div>

      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis
              dataKey="range"
              tick={{ fill: "#64748b", fontSize: 11 }}
              label={{ value: "Score Range & Decision Zone", position: "insideBottom", offset: -12, fill: "#475569", fontSize: 12 }}
            />
            <YAxis
              tick={{ fill: "#64748b", fontSize: 11 }}
              label={{ value: "Borrower Count", angle: -90, position: "insideLeft", offset: 10, fill: "#475569", fontSize: 12 }}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const d = payload[0].payload;
                  return (
                    <div className="rounded-xl border border-slate-200 bg-white/95 p-3 text-xs shadow-xl backdrop-blur">
                      <p className="font-bold text-slate-900">Range: {d.range}</p>
                      <p className="text-slate-600">Zone: <strong style={{ color: getZoneColor(d.zone) }}>{d.zone}</strong></p>
                      <p className="text-blue-700 font-medium">Applications: {d.count.toLocaleString()} ({d.pct}%)</p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Bar dataKey="count" radius={[4, 4, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getZoneColor(entry.zone)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-3 grid grid-cols-1 gap-2 text-xs md:grid-cols-3">
        <div className="rounded-xl border border-rose-100 bg-rose-50/60 p-3 text-rose-950">
          <p className="font-semibold text-rose-900">Score &lt; 550: Actionable Recourse</p>
          <p className="mt-1 text-slate-600 leading-relaxed">Never dead-end rejections. Automatically produces clear milestones (SHG meetings, utility rail) to upgrade.</p>
        </div>
        <div className="rounded-xl border border-amber-100 bg-amber-50/60 p-3 text-amber-950">
          <p className="font-semibold text-amber-900">550 - 649: Branch Loan Officer Review</p>
          <p className="mt-1 text-slate-600 leading-relaxed">Underwriter evaluates localized ground reality (panchayat endorsement, crop insurance) to approve or override.</p>
        </div>
        <div className="rounded-xl border border-emerald-100 bg-emerald-50/60 p-3 text-emerald-950">
          <p className="font-semibold text-emerald-900">≥ 650: Straight-Through Lending (STP)</p>
          <p className="mt-1 text-slate-600 leading-relaxed">Zero officer intervention required. Immediate digital loan pass through to participating Regional Rural Banks.</p>
        </div>
      </div>
    </div>
  );
};
