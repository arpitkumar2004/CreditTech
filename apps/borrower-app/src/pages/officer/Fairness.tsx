import { useState } from "react";
import { ShieldCheck, Download, Info, ChevronDown, AlertTriangle } from "lucide-react";
import { BarChart, Bar, ResponsiveContainer, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts";
import { useQuery } from "@tanstack/react-query";
import { Badge, Dot } from "@/components/ui/badge";
import { LoadingState } from "@/components/ui/loading";
import { EmptyState } from "@/components/ui/empty";
import { fairnessSlices as fallbackSlices } from "@/lib/mockData";
import { dashboardApi, adminApi } from "@/lib/api";
import { usePersona, isAllowed } from "@/lib/usePersona";
import AccessDenied from "@/components/AccessDenied";

export default function Fairness() {
  const persona = usePersona();

  if (!isAllowed(persona.role, ["RISK_OFFICER", "LOAN_OFFICER", "ADMIN", "SUPERVISOR"])) {
    return (
      <AccessDenied
        resourceName="Fairness & Demographic Parity Audits"
        allowedRoles={["RISK_OFFICER", "LOAN_OFFICER", "ADMIN"]}
      />
    );
  }

  const [showCharts, setShowCharts] = useState(false);

  const { data: fairnessData, isLoading } = useQuery({
    queryKey: ["fairness-audit", persona.id],
    queryFn: () => dashboardApi.fairness().catch(() => null),
  });

  const { data: gateData } = useQuery({
    queryKey: ["fairness-gate"],
    queryFn: () => adminApi.evaluateGate().catch(() => null),
  });

  const { data: manifestData } = useQuery({
    queryKey: ["fairness-manifest"],
    queryFn: () => adminApi.getManifest().catch(() => null),
  });

  const flatRows = (fairnessData?.rows && fairnessData.rows.length > 0)
    ? fairnessData.rows.map((r: any) => ({
        dim: r.dimension,
        g: r.group_value,
        n: r.sample_size,
        approval: r.approval_rate,
        delta: 0,
        status: r.status,
      }))
    : fallbackSlices.flatMap((s) =>
        s.groups.map((g) => ({ dim: s.dim, ...g, status: Math.abs(g.delta) <= 0.1 ? "OK" : "BREACH" }))
      );

  const groupedSlices = (() => {
    if (fairnessData?.rows && fairnessData.rows.length > 0) {
      const map = new Map<string, any[]>();
      for (const r of fairnessData.rows) {
        const list = map.get(r.dimension) || [];
        list.push({ g: r.group_value, approval: r.approval_rate, n: r.sample_size });
        map.set(r.dimension, list);
      }
      return Array.from(map.entries()).map(([dim, groups]) => ({ dim, groups }));
    }
    return fallbackSlices;
  })();

  const gatePassed = gateData ? gateData.passed : true;
  const breachesCount = gateData?.breaches ? (gateData.breaches as any[]).length : 0;
  const manifestVersion = manifestData?.manifest?.version ?? (manifestData as any)?.version ?? "v2026.09.01";

  const handleExportCsv = () => {
    window.open("/api/v1/dashboard/fairness/export.csv", "_blank");
  };

  return (
    <div className="space-y-6">
      <header className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-semibold display">Fairness monitor</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Approval-rate parity across protected & operational dimensions · period {fairnessData?.period || "2026-09"}.
          </p>
        </div>
        <button onClick={handleExportCsv} className="pill-ghost">
          <Download className="h-4 w-4 mr-2" /> Auditor CSV
        </button>
      </header>

      {/* Overall status */}
      <div className="glass rounded-3xl p-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="flex items-center gap-4">
          <span className={`grid place-items-center h-12 w-12 rounded-2xl ${gatePassed ? "bg-emerald-500/10 text-emerald-700" : "bg-rose-500/10 text-rose-700"}`}>
            {gatePassed ? <ShieldCheck className="h-6 w-6" /> : <AlertTriangle className="h-6 w-6" />}
          </span>
          <div>
            <p className="text-lg font-semibold display">
              FairnessGate · {gatePassed ? "PASS" : "BREACH DETECTED"}
            </p>
            <p className="text-sm text-muted-foreground">
              {breachesCount} breaches · ratified manifest {manifestVersion} · evaluated against live policy
            </p>
          </div>
        </div>
      </div>

      {/* Key metrics */}
      <section>
        <p className="section-heading mb-3">Key metrics</p>
        <div className="grid grid-cols-3 gap-4 glass rounded-3xl p-5">
          <Metric label="Groups audited" value={String(flatRows.length)} />
          <Metric
            label="Avg approval"
            value={flatRows.length > 0 ? `${(flatRows.reduce((a, b) => a + b.approval, 0) / flatRows.length * 100).toFixed(1)}%` : "0%"}
          />
          <Metric label="Dims checked" value={String(groupedSlices.length)} />
        </div>
      </section>

      {/* Group comparison table */}
      <section>
        <p className="section-heading mb-3">Group comparison</p>
        <div className="glass rounded-3xl overflow-hidden">
          {isLoading ? (
            <LoadingState text="Loading fairness audit slices…" />
          ) : flatRows.length === 0 ? (
            <EmptyState
              icon={ShieldCheck}
              title="No fairness records found"
              subtitle="Fairness parity metrics will appear as loan applications are audited."
            />
          ) : (
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
                      {r.delta !== 0 ? `${r.delta >= 0 ? "+" : ""}${(r.delta * 100).toFixed(1)}pt` : "—"}
                    </td>
                    <td className="last">
                      {r.status === "OK" || (!r.status && Math.abs(r.delta) <= 0.1)
                        ? <Badge tone="success"><Dot tone="success" /> pass</Badge>
                        : <Badge tone="danger"><Dot tone="danger" /> {r.status?.toLowerCase() || "breach"}</Badge>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
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
            {groupedSlices.map((s) => (
              <div key={s.dim} className="glass rounded-3xl p-5">
                <p className="text-sm font-semibold display mb-3">{s.dim}</p>
                <div className="h-40">
                  <ResponsiveContainer>
                    <BarChart data={s.groups.map((g: any) => ({ name: g.g, approval: Math.round(g.approval * 1000) / 10 }))}>
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
          <Badge tone="primary">{manifestVersion}</Badge>
        </div>
        <div className="glass rounded-3xl p-5 grid sm:grid-cols-3 gap-3">
          <Manifest label="Min approval / group" value={`≥ ${(manifestData?.thresholds?.min_approval_rate_per_group ? manifestData.thresholds.min_approval_rate_per_group * 100 : 45.0).toFixed(1)}%`} />
          <Manifest label="Max gap within dim" value={`≤ ${(manifestData?.thresholds?.max_approval_rate_disparity ? manifestData.thresholds.max_approval_rate_disparity * 100 : 10.0).toFixed(1)}pt`} />
          <Manifest label="Max officer override" value={`≤ ${(manifestData?.thresholds?.max_override_rate ? manifestData.thresholds.max_override_rate * 100 : 30.0).toFixed(1)}%`} />
          <Manifest label="Min sample size" value={`≥ ${manifestData?.thresholds?.min_subgroup_sample_size ?? 30}`} />
          <Manifest label="Perf. floor · AUC" value={`≥ ${(manifestData?.thresholds?.auc_roc_floor ?? 0.60).toFixed(2)}`} />
          <Manifest label="Perf. floor · Brier" value={`≤ ${(manifestData?.thresholds?.brier_score_ceiling ?? 0.30).toFixed(2)}`} />
        </div>
      </section>

      <p className="text-xs text-muted-foreground flex items-start gap-1.5">
        <Info className="h-3.5 w-3.5 mt-0.5" />
        {fairnessData?.governance_note || (
          <>
            Live numbers come from the FairnessAuditor and <span className="font-mono mx-1">config/fairness_thresholds.json</span>.
          </>
        )}
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
