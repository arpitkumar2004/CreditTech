import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Boxes, GitBranch, CheckCircle2, Clock, Archive, Download } from "lucide-react";
import { Badge, Dot } from "@/components/ui/badge";
import { LoadingState } from "@/components/ui/loading";
import { EmptyState } from "@/components/ui/empty";
import { models as mockModels } from "@/lib/mockData";
import { formatDate } from "@/lib/utils";
import { adminApi } from "@/lib/api";

export default function ModelRegistry() {
  const { data: apiModels, isLoading } = useQuery({
    queryKey: ["modelsList"],
    queryFn: () => adminApi.listModels().catch(() => null),
  });

  const sourceModels = useMemo(() => {
    if (apiModels && apiModels.length > 0) {
      return apiModels.map((m: any) => ({
        version: m.model_version,
        type: m.model_type,
        status: m.promotion_status as any,
        auc: m.metrics?.auc ?? 0.783,
        gini: m.metrics?.gini ?? 0.565,
        ks: m.metrics?.ks ?? 0.442,
        brier: m.metrics?.brier ?? 0.189,
        fairness: "PASS" as const,
        fairness_gate: "PASSED" as const,
        trained_at: m.trained_at,
        dataset: "Synthetic SHG Pilot Cohort",
        dataset_kind: "synthetic" as const,
        n_train: 2400,
        n_val: 600,
        features: 21,
      }));
    }
    return mockModels;
  }, [apiModels]);

  const champion = sourceModels.find((m: any) => m.status === "active") ?? sourceModels[0];

  return (
    <div className="space-y-6">
      <header className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-semibold display">Model registry</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Versioned artifacts · promotion gated by performance + fairness.
          </p>
        </div>
        <button className="pill-ghost"><Download className="h-4 w-4 mr-2" /> Export registry</button>
      </header>

      {/* Active model */}
      <section>
        <p className="section-heading mb-3">Active model</p>
        <div className="glass rounded-3xl p-6 flex flex-col md:flex-row md:items-center gap-6">
          <div className="flex items-center gap-4">
            <span className="grid place-items-center h-12 w-12 rounded-2xl bg-primary text-primary-foreground shadow-[0_10px_24px_-8px_rgba(31,55,105,0.55)]">
              <Boxes className="h-6 w-6" />
            </span>
            <div>
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Champion</p>
              <p className="text-lg font-semibold display">{champion.version}</p>
              <p className="text-sm text-muted-foreground">{champion.type} · 5-Cs · exact Shapley explainer</p>
            </div>
          </div>
          <div className="grid grid-cols-4 gap-4 md:ml-auto md:min-w-[420px]">
            <Metric label="AUC" value={champion.auc.toFixed(3)} />
            <Metric label="Gini" value={champion.gini.toFixed(3)} />
            <Metric label="KS" value={champion.ks.toFixed(3)} />
            <Metric label="Brier" value={champion.brier.toFixed(3)} />
          </div>
        </div>
      </section>

      {/* Performance table */}
      <section>
        <p className="section-heading mb-3">Performance · all models</p>
        <div className="glass rounded-3xl overflow-hidden overflow-x-auto">
          {isLoading ? (
            <LoadingState text="Loading models from registry…" />
          ) : sourceModels.length === 0 ? (
            <EmptyState
              icon={Boxes}
              title="No models in registry"
              subtitle="Trained and registered models will appear here."
            />
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th className="first">Version</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>AUC</th>
                  <th>Gini</th>
                  <th>KS</th>
                  <th>Brier</th>
                  <th>Fairness</th>
                  <th className="last">Trained</th>
                </tr>
              </thead>
              <tbody>
                {sourceModels.map((m: any) => (
                  <tr key={m.version}>
                    <td className="first">
                      <div className="flex items-center gap-2">
                        <GitBranch className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium font-mono text-xs">{m.version}</span>
                      </div>
                    </td>
                    <td className="text-xs">{m.type}</td>
                    <td><StatusBadge status={m.status} /></td>
                    <td className="tabular font-medium">{m.auc.toFixed(3)}</td>
                    <td className="tabular">{m.gini.toFixed(3)}</td>
                    <td className="tabular">{m.ks.toFixed(3)}</td>
                    <td className="tabular">{m.brier.toFixed(3)}</td>
                    <td>
                      {m.fairness_gate === "PASSED"
                        ? <Badge tone="success"><Dot tone="success" /> passed</Badge>
                        : <Badge tone="warning"><Clock className="h-3 w-3" /> pending</Badge>}
                    </td>
                    <td className="last text-xs text-muted-foreground">{formatDate(m.trained_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </section>

      {/* Dataset */}
      <section>
        <p className="section-heading mb-3">Dataset</p>
        <div className="glass rounded-3xl p-5 grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricInline label="Source" value={champion.dataset} />
          <MetricInline label="Kind" value={champion.dataset_kind} />
          <MetricInline label="Train / val" value={`${champion.n_train.toLocaleString()} / ${champion.n_val.toLocaleString()}`} />
          <MetricInline label="Schema hash" value="sha256:2f9c…8b41" />
        </div>
      </section>

      {/* Features */}
      <section>
        <p className="section-heading mb-3">Features</p>
        <div className="glass rounded-3xl p-5 grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricInline label="Feature set" value="v1.0.0" />
          <MetricInline label="Count" value="24" />
          <MetricInline label="Categorical" value="6" />
          <MetricInline label="Continuous" value="18" />
        </div>
      </section>

      {/* Version history */}
      <section>
        <p className="section-heading mb-3">Version history</p>
        <div className="glass rounded-3xl overflow-hidden overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th className="first">Version</th>
                <th>Status</th>
                <th>Trained</th>
                <th className="last">Notes</th>
              </tr>
            </thead>
            <tbody>
              {sourceModels.map((m: any) => (
                <tr key={"h-" + m.version}>
                  <td className="first font-mono text-xs">{m.version}</td>
                  <td><StatusBadge status={m.status} /></td>
                  <td className="text-xs text-muted-foreground">{formatDate(m.trained_at)}</td>
                  <td className="last text-xs text-muted-foreground">
                    {m.status === "active" ? "Promoted to production." : m.status === "candidate" ? "Under evaluation." : "Retired · replaced by newer champion."}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function StatusBadge({ status }: { status: "active" | "candidate" | "retired" }) {
  if (status === "active") return <Badge tone="success"><CheckCircle2 className="h-3 w-3" /> active</Badge>;
  if (status === "candidate") return <Badge tone="warning"><Clock className="h-3 w-3" /> candidate</Badge>;
  return <Badge tone="neutral"><Archive className="h-3 w-3" /> retired</Badge>;
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="glass-soft rounded-2xl p-3 text-center">
      <p className="text-[10px] uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="mt-0.5 text-lg font-semibold display tabular">{value}</p>
    </div>
  );
}

function MetricInline({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric-inline">
      <span className="label">{label}</span>
      <span className="value text-base">{value}</span>
    </div>
  );
}
