import { useState } from "react";
import { ShieldCheck, Download, Info, ChevronDown } from "lucide-react";
import { BarChart, Bar, ResponsiveContainer, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts";
import { Badge, Dot } from "@/components/ui/badge";
import { fairnessSlices } from "@/lib/mockData";

export default function Fairness() {
  const [showCharts, setShowCharts] = useState(false);

  const flatRows = fairnessSlices.flatMap((s) =>
    s.groups.map((g) => ({ dim: s.dim, ...g }))
  );

  return (
    <div className="space-y-6">
      <header className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-semibold display">Fairness monitor</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Approval-rate parity across protected & operational dimensions · pilot period 2026-09.
          </p>
        </div>
        <button className="pill-ghost"><Download className="h-4 w-4 mr-2" /> Auditor CSV</button>
      </header>

      {/* Overall status */}
      <div className="glass rounded-3xl p-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="flex items-center gap-4">
          <span className="grid place-items-center h-12 w-12 rounded-2xl bg-emerald-500/10 text-emerald-700">
            <ShieldCheck className="h-6 w-6" />
          </span>
          <div>
            <p className="text-lg font-semibold display">FairnessGate · PASS</p>
            <p className="text-sm text-muted-foreground">
              0 breaches · ratified manifest v2026.09.01 · last evaluated just now
            </p>
          </div>
        </div>
      </div>

      {/* Key metrics */}
      <section>
        <p className="section-heading mb-3">Key metrics</p>
        <div className="grid grid-cols-3 gap-4 glass rounded-3xl p-5">
          <Metric label="Max ΔApproval" value="4.5 pts" />
          <Metric label="Min approval" value="56.7%" />
          <Metric label="Dims checked" value="3" />
        </div>
      </section>

      {/* Group comparison table */}
      <section>
        <p className="section-heading mb-3">Group comparison</p>
        <div className="glass rounded-3xl overflow-hidden">
          <table className="data-table">
            <thead>
              <tr>
                <th className="first">Dimension</th>
                <th>Group</th>
                <th>Sample (n)</th>
                <th>Approval</th>
                <th>Δ vs baseline</th>
                <th className="last">Verdict</th>
              </tr>
            </thead>
            <tbody>
              {flatRows.map((r, i) => (
                <tr key={`${r.dim}-${r.g}-${i}`}>
                  <td className="first text-xs text-muted-foreground uppercase tracking-wide">{r.dim}</td>
                  <td className="font-medium">{r.g}</td>
                  <td className="tabular">{r.n}</td>
                  <td className="tabular font-medium">{(r.approval * 100).toFixed(1)}%</td>
                  <td className={"tabular " + (r.delta >= 0 ? "text-emerald-600" : "text-rose-600")}>
                    {r.delta >= 0 ? "+" : ""}{(r.delta * 100).toFixed(1)}pt
                  </td>
                  <td className="last">
                    {Math.abs(r.delta) <= 0.1
                      ? <Badge tone="success"><Dot tone="success" /> pass</Badge>
                      : <Badge tone="danger"><Dot tone="danger" /> breach</Badge>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Detailed per-dim charts (collapsed) */}
      <section>
        <button
          onClick={() => setShowCharts((v) => !v)}
          className="flex items-center gap-2 text-sm font-medium text-primary hover:underline"
        >
          <ChevronDown className={"h-4 w-4 transition " + (showCharts ? "rotate-180" : "")} />
          {showCharts ? "Hide" : "Show"} per-dimension breakdown
        </button>
        {showCharts && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mt-4">
            {fairnessSlices.map((s) => (
              <div key={s.dim} className="glass rounded-3xl p-5">
                <p className="text-sm font-semibold display mb-3">{s.dim}</p>
                <div className="h-40">
                  <ResponsiveContainer>
                    <BarChart data={s.groups.map((g) => ({ name: g.g, approval: Math.round(g.approval * 1000) / 10 }))}>
                      <CartesianGrid stroke="hsl(220 30% 92%)" strokeDasharray="3 4" vertical={false} />
                      <XAxis dataKey="name" tick={{ fontSize: 10, fill: "hsl(220 15% 45%)" }} axisLine={false} tickLine={false} />
                      <YAxis tick={{ fontSize: 10, fill: "hsl(220 15% 45%)" }} axisLine={false} tickLine={false} width={30} />
                      <Tooltip
                        contentStyle={{ borderRadius: 14, border: "1px solid hsl(220 30% 90%)", background: "rgba(255,255,255,0.95)", fontSize: 12 }}
                        formatter={(v: any) => [`${v}%`, "Approval"]}
                      />
                      <Bar dataKey="approval" fill="hsl(220 45% 22%)" radius={[8, 8, 4, 4]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Ratified manifest */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <p className="section-heading">Ratified thresholds</p>
          <Badge tone="primary">v2026.09.01</Badge>
        </div>
        <div className="glass rounded-3xl p-5 grid sm:grid-cols-3 gap-3">
          <Manifest label="Min approval / group" value="≥ 45.0%" />
          <Manifest label="Max gap within dim" value="≤ 10.0pt" />
          <Manifest label="Max officer override" value="≤ 30.0%" />
          <Manifest label="Min sample size" value="≥ 30" />
          <Manifest label="Perf. floor · AUC" value="≥ 0.60" />
          <Manifest label="Perf. floor · Brier" value="≤ 0.30" />
        </div>
      </section>

      <p className="text-xs text-muted-foreground flex items-start gap-1.5">
        <Info className="h-3.5 w-3.5 mt-0.5" />
        Demo data · production numbers come from the FairnessAuditor batch (weekly) and
        <span className="font-mono mx-1">config/fairness_thresholds.json</span>.
      </p>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric-inline">
      <span className="label">{label}</span>
      <span className="value">{value}</span>
    </div>
  );
}

function Manifest({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/70 bg-white/60 p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-0.5 font-semibold display tabular">{value}</p>
    </div>
  );
}
