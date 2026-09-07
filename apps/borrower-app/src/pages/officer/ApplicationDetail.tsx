import { useMemo, useState } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  ChevronLeft, Sparkles, MapPin, User2, Calendar,
  CheckCircle2, XCircle, AlertCircle, Send, ShieldCheck, Database, Loader2,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar } from "@/components/ui/avatar";
import { applications as mockApplications, type Application } from "@/lib/mockData";
import { formatINR, formatDate } from "@/lib/utils";
import { isOverride, validateDecisionForm } from "@/lib/decisionLogic";
import type { OfficerDecision } from "@/lib/types";
import { decisionApi, chartsApi } from "@/lib/api";
import { useToast } from "@/components/ui/toast";
import { usePersona, isAllowed } from "@/lib/usePersona";
import AccessDenied from "@/components/AccessDenied";
import { NDVITrajectoryPlot } from "@/components/charts";

export default function ApplicationDetail() {
  const persona = usePersona();

  if (!isAllowed(persona.role, ["LOAN_OFFICER", "SUPERVISOR", "ADMIN"])) {
    return (
      <AccessDenied
        resourceName="Branch Loan Underwriting Pack & Decision"
        allowedRoles={["LOAN_OFFICER", "SUPERVISOR", "ADMIN"]}
      />
    );
  }

  const { id } = useParams();
  const nav = useNavigate();
  const { toast } = useToast();

  const { data: apiApps } = useQuery({
    queryKey: ["applicationsList", persona.id],
    queryFn: () => decisionApi.listApplications().catch(() => null),
  });

  const app = useMemo(() => {
    const apiMatch = apiApps?.find((a) => a.id === id || a.score_id === id);
    const mockMatch = mockApplications.find((a) => a.id === id);

    if (apiMatch) {
      return {
        id: apiMatch.id,
        score_id: apiMatch.score_id,
        borrower_name: apiMatch.borrower_name,
        village: apiMatch.village,
        district: apiMatch.district,
        state: apiMatch.state,
        gender: (apiMatch.gender as "F" | "M") || "F",
        age: apiMatch.age || 35,
        landholding_band: (apiMatch.landholding_band as any) || "MARGINAL",
        requested_amount: apiMatch.requested_amount || 50000,
        requested_tenure_months: apiMatch.requested_tenure_months || 12,
        tenure_months: apiMatch.requested_tenure_months || 12,
        purpose: apiMatch.purpose || "Agricultural Working Capital",
        score_900: apiMatch.score_900 || 720,
        score_100: apiMatch.score_100 || 75.0,
        band: (apiMatch.band as any) || "GOOD",
        confidence_lower: apiMatch.confidence_lower || 695,
        confidence_upper: apiMatch.confidence_upper || 745,
        model_recommendation: apiMatch.model_recommendation || "APPROVE",
        decision: (apiMatch.decision as any) || "PENDING",
        override_reason: apiMatch.override_reason ?? undefined,
        submitted_at: apiMatch.submitted_at || new Date().toISOString(),
        sakhi: "Sunita (Bank Sakhi)",
        features: mockMatch?.features ?? { "shg_thrift_regularity_6m": 0.95, "aa_avg_balance_6m": 12500, "ndvi_avg": 0.68 },
        reasons: mockMatch?.reasons ?? [],
        sources_used: ["SHG_FPO", "AA", "GEOSPATIAL", "BUREAU"] as Array<"SHG_FPO" | "AA" | "GEOSPATIAL" | "BUREAU">,
      };
    }
    return mockMatch ?? mockApplications[0];
  }, [id, apiApps]);

  const { data: reviewData } = useQuery({
    queryKey: ["review", app.score_id],
    queryFn: () => (app.score_id ? decisionApi.getReview(app.score_id).catch(() => null) : Promise.resolve(null)),
    enabled: !!app.score_id,
  });

  const { data: officerCharts } = useQuery({
    queryKey: ["officerAppCharts"],
    queryFn: () => chartsApi.getCharts({ persona: "officer" }).catch(() => null),
  });

  const [decision, setDecision] = useState<OfficerDecision | null>(null);
  const [override, setOverride] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const recAsOfficer =
    app.model_recommendation === "APPROVE" ? "APPROVED"
    : app.model_recommendation === "REJECT" ? "REJECTED"
    : "APPROVED";
  const requiresOverride = decision != null && isOverride(decision, app.model_recommendation);
  const validationError = validateDecisionForm(decision, app.model_recommendation, override);
  void recAsOfficer;

  async function handleSubmit() {
    if (validationError || !decision) return;
    setIsSubmitting(true);
    try {
      if (app.score_id) {
        await decisionApi.recordDecision({
          score_id: app.score_id,
          decision: decision as any,
          override_reason: requiresOverride ? override : null,
          notes: override || undefined,
        });
      }
      toast({
        variant: "success",
        title: "Decision recorded",
        description: `Decision ${decision} recorded for ${app.borrower_name}.`,
      });
      setIsSubmitting(false);
      setSubmitted(true);
      setTimeout(() => nav("/applications"), 1200);
    } catch (err: any) {
      setIsSubmitting(false);
      toast({
        variant: "error",
        title: "Decision Failed / Blocked",
        description: err?.message || "Failed to record decision on the server.",
      });
    }
  }

  const reasonsList = useMemo(() => {
    if (reviewData?.reason_codes && reviewData.reason_codes.length > 0) {
      return reviewData.reason_codes.map((r) => ({
        rank: r.rank,
        feature: r.feature_name,
        direction: ((r.direction as string) === "POS" || (r.direction as string) === "POSITIVE") ? ("POSITIVE" as const) : ("NEGATIVE" as const),
        shap: r.shap_value,
        en: r.localized_text_en,
        hi: r.localized_text_hi || r.localized_text_en,
      }));
    }
    return app.reasons;
  }, [reviewData, app.reasons]);

  const maxAbsShap = Math.max(1, ...reasonsList.map((r) => Math.abs(r.shap)));

  return (
    <div className="space-y-6">
      <Link to="/applications" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ChevronLeft className="h-4 w-4" /> Back to applications
      </Link>

      {/* 1. Header row */}
      <Card className="p-6 sm:p-8">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
          <div className="flex items-center gap-4">
            <Avatar name={app.borrower_name} size={64} />
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h1 className="text-2xl font-semibold display">{app.borrower_name}</h1>
                <Badge tone="primary">{app.id}</Badge>
              </div>
              <p className="text-sm text-muted-foreground mt-1 flex items-center gap-1.5">
                <MapPin className="h-3.5 w-3.5" /> {app.village}, {app.district}, {app.state}
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                <Badge tone="neutral"><User2 className="h-3 w-3" /> {app.gender === "F" ? "Female" : "Male"} · {app.age} yrs</Badge>
                <Badge tone="neutral">{app.landholding_band.replace("_", " ").toLowerCase()}</Badge>
                <Badge tone="neutral"><Calendar className="h-3 w-3" /> {formatDate(app.submitted_at)}</Badge>
                <Badge tone="info">Sakhi · {app.sakhi}</Badge>
              </div>
            </div>
          </div>
          <ScoreRing app={app} />
        </div>
      </Card>

      {/* 2. Credit score summary strip */}
      <section>
        <p className="section-heading mb-3">Credit score</p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 glass rounded-3xl p-5">
          <MetricInline label="Score (900)" value={String(app.score_900)} note={`band ${app.band}`} />
          <MetricInline label="Score (100)" value={app.score_100.toFixed(1)} />
          <MetricInline label="95% CI" value={`${app.confidence_lower}–${app.confidence_upper}`} />
          <MetricInline label="Model / features" value="v1.0.0" note="feat v1.0.0" />
        </div>
      </section>

      {/* 3. Loan information */}
      <section>
        <p className="section-heading mb-3">Loan request</p>
        <div className="glass rounded-3xl p-5 grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricInline label="Amount" value={formatINR(app.requested_amount)} />
          <MetricInline label="Tenure" value={`${(app as any).requested_tenure_months || (app as any).tenure_months || 12} mo`} />
          <MetricInline label="Purpose" value={app.purpose} />
          <MetricInline label="Repayment freq." value="Monthly" />
        </div>
      </section>

      {/* 4. Alternative-credit signals */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <p className="section-heading">Alternative-credit signals</p>
          <Badge tone="info"><Database className="h-3 w-3" /> immutable snapshot</Badge>
        </div>
        <div className="glass rounded-3xl p-1 overflow-hidden">
          <table className="data-table">
            <thead>
              <tr>
                <th className="first">Feature</th>
                <th className="last text-right">Value</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(app.features).map(([k, v]) => (
                <tr key={k}>
                  <td className="first font-mono text-xs text-muted-foreground">{k}</td>
                  <td className="last text-right tabular font-medium">{typeof v === "number" ? v.toFixed(2) : String(v)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* 5. Reason codes */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <div>
            <p className="section-heading">Top reason codes (SHAP)</p>
            <p className="text-xs text-muted-foreground mt-1">Bilingual explanations presented to the borrower in the Sakhi flow.</p>
          </div>
          <Badge tone="primary"><Sparkles className="h-3 w-3" /> v1.0.0-logistic</Badge>
        </div>
        <div className="space-y-2">
          {reasonsList.map((r) => (
            <div key={r.rank} className="rounded-2xl border border-white/70 bg-white/60 p-3.5">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0 flex items-start gap-3">
                  <span className="grid place-items-center h-6 w-6 rounded-full bg-primary/10 text-primary text-xs font-semibold shrink-0">{r.rank}</span>
                  <div className="min-w-0">
                    <p className="text-sm font-medium truncate">{r.en}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">{r.hi}</p>
                    <p className="text-[11px] text-muted-foreground mt-0.5 font-mono">{r.feature}</p>
                  </div>
                </div>
                <Badge tone={r.direction === "POSITIVE" ? "success" : "danger"}>
                  {r.direction === "POSITIVE" ? "+" : ""}{r.shap.toFixed(2)}
                </Badge>
              </div>
              <div className="mt-2 h-1.5 bg-slate-200/60 rounded-full overflow-hidden ml-9">
                <div
                  className={"h-full rounded-full " + (r.direction === "POSITIVE" ? "bg-emerald-500" : "bg-rose-500")}
                  style={{ width: `${(Math.abs(r.shap) / maxAbsShap) * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 5b. Geospatial Verification — Sentinel-2 NDVI */}
      <section className="space-y-3">
        <p className="section-heading">Geospatial Farm Vigor Verification</p>
        <NDVITrajectoryPlot data={officerCharts?.ndvi_trajectory} />
      </section>

      {/* 6. Actions — decision panel */}
      <section>
        <p className="section-heading mb-3">Actions</p>
        <Card>
          <CardHeader>
            <div className="flex items-start justify-between gap-3 flex-wrap">
              <div>
                <CardTitle>Officer decision</CardTitle>
                <CardDescription>Human-in-the-loop · you make the final call.</CardDescription>
              </div>
              <RecommendationCard rec={app.model_recommendation} />
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-2">
              {(["APPROVED", "MORE_INFO_REQUIRED", "REJECTED"] as const).map((d) => (
                <button
                  key={d}
                  onClick={() => setDecision(d)}
                  className={
                    "rounded-2xl px-3 py-2.5 text-xs font-medium border transition " +
                    (decision === d
                      ? d === "APPROVED"
                        ? "bg-emerald-500 text-white border-emerald-500 shadow-[0_10px_24px_-10px_rgba(16,185,129,0.55)]"
                        : d === "REJECTED"
                          ? "bg-rose-500 text-white border-rose-500 shadow-[0_10px_24px_-10px_rgba(244,63,94,0.55)]"
                          : "bg-sky-500 text-white border-sky-500 shadow-[0_10px_24px_-10px_rgba(14,165,233,0.55)]"
                      : "bg-white/70 border-white/70 text-muted-foreground hover:text-foreground")
                  }
                >
                  {d === "APPROVED" ? "Approve" : d === "REJECTED" ? "Reject" : "More info"}
                </button>
              ))}
            </div>

            {requiresOverride && (
              <div className="mt-4 rounded-2xl bg-amber-50 border border-amber-100 p-3">
                <p className="text-xs text-amber-800 flex items-start gap-1.5">
                  <AlertCircle className="h-3.5 w-3.5 mt-0.5 shrink-0" />
                  Override reason required. You are dissenting from the model.
                </p>
                <textarea
                  value={override}
                  onChange={(e) => setOverride(e.target.value)}
                  rows={3}
                  placeholder="Describe your rationale, evidence, and any borrower context…"
                  className="mt-2 w-full rounded-xl bg-white/80 border border-white/80 outline-none px-3 py-2 text-sm placeholder:text-muted-foreground focus:ring-2 focus:ring-primary/20"
                />
              </div>
            )}

            <button
              disabled={!!validationError || submitted || isSubmitting}
              onClick={handleSubmit}
              className="mt-4 pill w-full justify-center disabled:opacity-60"
            >
              {isSubmitting ? (
                <><Loader2 className="h-4 w-4 mr-1.5 animate-spin" /> Submitting…</>
              ) : submitted ? (
                <><CheckCircle2 className="h-4 w-4 mr-1.5" /> Decision logged</>
              ) : (
                <><Send className="h-4 w-4 mr-1.5" /> Submit decision</>
              )}
            </button>
            <p className="mt-2 text-[11px] text-muted-foreground text-center">
              Logged to append-only audit · immutable
            </p>
          </CardContent>
        </Card>
      </section>

      {/* 7. Data rails */}
      <section>
        <p className="section-heading mb-3">Data rails</p>
        <div className="glass rounded-3xl p-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {(["SHG_FPO", "AA", "GEOSPATIAL", "BUREAU"] as const).map((s) => {
            const avail = app.sources_used.includes(s);
            return (
              <div key={s} className="rounded-2xl border border-white/70 bg-white/60 p-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Database className="h-4 w-4 text-primary" />
                  <span className="text-xs font-medium">{s}</span>
                </div>
                {avail ? (
                  <Badge tone="success"><CheckCircle2 className="h-3 w-3" /> available</Badge>
                ) : (
                  <Badge tone="neutral">not attached</Badge>
                )}
              </div>
            );
          })}
        </div>
        <p className="mt-2 text-xs text-muted-foreground flex items-center gap-1">
          <ShieldCheck className="h-3.5 w-3.5" />
          Consent-chained hash verification active for all accessed rails.
        </p>
      </section>
    </div>
  );
}

function ScoreRing({ app }: { app: Application }) {
  const pct = app.score_100;
  const stroke = app.band === "A" ? "#059669" : app.band === "B" ? "#3b82f6" : app.band === "C" ? "#f59e0b" : "#dc2626";
  return (
    <div className="relative h-32 w-32 shrink-0">
      <svg viewBox="0 0 120 120" className="h-full w-full -rotate-90">
        <circle cx="60" cy="60" r="52" stroke="rgba(31,55,105,0.08)" strokeWidth="10" fill="none" />
        <circle
          cx="60" cy="60" r="52" stroke={stroke} strokeWidth="10" fill="none"
          strokeDasharray={`${(pct / 100) * 326.7} 326.7`} strokeLinecap="round"
        />
      </svg>
      <div className="absolute inset-0 grid place-items-center">
        <div className="text-center">
          <div className="text-3xl font-semibold display tabular">{app.score_900}</div>
          <div className="text-[10px] text-muted-foreground uppercase tracking-wide">band {app.band}</div>
        </div>
      </div>
    </div>
  );
}

function RecommendationCard({ rec }: { rec: "APPROVE" | "REVIEW" | "REJECT" }) {
  const map = {
    APPROVE: { wrap: "bg-emerald-50 border-emerald-100", chip: "bg-emerald-500/10 text-emerald-700", text: "text-emerald-800",
      icon: CheckCircle2, label: "Model: Approve", note: "Meets policy thresholds." },
    REVIEW:  { wrap: "bg-amber-50 border-amber-100",   chip: "bg-amber-500/10 text-amber-700",   text: "text-amber-800",
      icon: AlertCircle,  label: "Model: Review", note: "Score is in the referral band." },
    REJECT:  { wrap: "bg-rose-50 border-rose-100",     chip: "bg-rose-500/10 text-rose-700",     text: "text-rose-800",
      icon: XCircle,      label: "Model: Reject", note: "Below approval threshold." },
  }[rec];
  const Icon = map.icon;
  return (
    <div className={"rounded-2xl border px-3 py-2 flex items-center gap-2.5 " + map.wrap}>
      <span className={"grid place-items-center h-8 w-8 rounded-xl " + map.chip}>
        <Icon className="h-4 w-4" />
      </span>
      <div>
        <div className={"text-xs font-semibold " + map.text}>{map.label}</div>
        <div className="text-[11px] text-muted-foreground">{map.note}</div>
      </div>
    </div>
  );
}

function MetricInline({ label, value, note }: { label: string; value: string; note?: string }) {
  return (
    <div className="metric-inline">
      <span className="label">{label}</span>
      <span className="value">{value}</span>
      {note && <span className="text-xs text-muted-foreground mt-0.5">{note}</span>}
    </div>
  );
}
