import React from "react";
import {
  ResponsiveContainer,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  Line,
  ComposedChart,
} from "recharts";
import { ShieldCheck } from "lucide-react";

interface CashflowMonth {
  month: string;
  shg_savings: number;
  inflow: number;
  outflow: number;
  net_savings?: number;
  on_time: boolean;
}

interface CashflowPulseProps {
  data?: CashflowMonth[];
  className?: string;
}

export const CashflowPulsePlot: React.FC<CashflowPulseProps> = ({ data, className = "" }) => {
  const points = data && data.length > 0 ? data : [
    { month: "M-11", shg_savings: 500, inflow: 8200, outflow: 6100, on_time: true },
    { month: "M-10", shg_savings: 500, inflow: 7900, outflow: 5800, on_time: true },
    { month: "M-9",  shg_savings: 500, inflow: 8400, outflow: 6000, on_time: true },
    { month: "M-8",  shg_savings: 500, inflow: 12500, outflow: 7200, on_time: true }, // Harvest surge
    { month: "M-7",  shg_savings: 500, inflow: 9100, outflow: 6400, on_time: true },
    { month: "M-6",  shg_savings: 500, inflow: 8300, outflow: 6100, on_time: true },
    { month: "M-5",  shg_savings: 500, inflow: 7800, outflow: 5900, on_time: true },
    { month: "M-4",  shg_savings: 500, inflow: 8100, outflow: 6000, on_time: true },
    { month: "M-3",  shg_savings: 500, inflow: 14200, outflow: 8100, on_time: true }, // Harvest surge
    { month: "M-2",  shg_savings: 500, inflow: 8800, outflow: 6300, on_time: true },
    { month: "M-1",  shg_savings: 500, inflow: 8500, outflow: 6200, on_time: true },
    { month: "Current", shg_savings: 500, inflow: 8600, outflow: 6100, on_time: true },
  ];

  return (
    <div className={`rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm hover:shadow-md transition-shadow ${className}`}>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-semibold text-slate-900">
              12-Month Cashflow Pulse & Mutual SHG Savings
            </h3>
            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 ring-1 ring-emerald-200">
              <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
              100% On-Time Peer Discipline
            </span>
          </div>
          <p className="mt-0.5 text-xs text-slate-500">
            Monthly cash inflows, essential outflows, and continuous peer-validated SHG savings
          </p>
        </div>

        <div className="flex items-center gap-3 text-xs">
          <div className="rounded-lg bg-slate-50 px-3 py-1.5 text-slate-600 border border-slate-200/80">
            <span className="text-slate-500">Cumulative Savings: </span>
            <span className="font-mono font-bold text-emerald-700">₹6,000</span>
          </div>
          <div className="rounded-lg bg-slate-50 px-3 py-1.5 text-slate-600 border border-slate-200/80">
            <span className="text-slate-500">Streak: </span>
            <span className="font-mono font-bold text-blue-700">36 Months</span>
          </div>
        </div>
      </div>

      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={points} margin={{ top: 10, right: 20, left: 10, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis
              dataKey="month"
              tick={{ fill: "#64748b", fontSize: 11 }}
              label={{ value: "Timeline (Past 12 Months)", position: "insideBottom", offset: -12, fill: "#64748b", fontSize: 12 }}
            />
            <YAxis
              tick={{ fill: "#64748b", fontSize: 11 }}
              tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`}
              label={{ value: "Amount in INR (₹)", angle: -90, position: "insideLeft", offset: 0, fill: "#64748b", fontSize: 12 }}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const d = payload[0].payload;
                  return (
                    <div className="rounded-xl border border-slate-200 bg-white/95 p-2.5 text-xs shadow-xl backdrop-blur">
                      <p className="font-bold text-slate-900">{d.month}</p>
                      <p className="text-emerald-700 mt-1">Inflow: ₹{d.inflow.toLocaleString()}</p>
                      <p className="text-rose-600">Outflow: ₹{d.outflow.toLocaleString()}</p>
                      <p className="text-blue-700">Net Surplus: ₹{(d.inflow - d.outflow).toLocaleString()}</p>
                      <p className="text-amber-700">SHG Savings: ₹{d.shg_savings.toLocaleString()} (Paid)</p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: "11px", color: "#475569" }} />
            <Bar dataKey="inflow" name="Total Monthly Inflow" fill="#059669" radius={[4, 4, 0, 0]} opacity={0.9} />
            <Bar dataKey="outflow" name="Total Outflow / Expenses" fill="#f43f5e" radius={[4, 4, 0, 0]} opacity={0.8} />
            <Line
              type="monotone"
              dataKey="shg_savings"
              name="Monthly SHG Deposit"
              stroke="#d97706"
              strokeWidth={3}
              dot={{ r: 4, fill: "#d97706" }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-3 rounded-xl bg-slate-50 px-3.5 py-2.5 text-xs text-slate-700 border border-slate-200/80">
        <span className="font-semibold text-emerald-800">Alternative Cashflow Insight:</span> Rural agricultural incomes naturally surge in harvest months (M-8 Kharif and M-3 Rabi). Even during lean sowing months, savings deposits remain 100% steady, evidencing true creditworthiness without formal salary slips.
      </div>
    </div>
  );
};
