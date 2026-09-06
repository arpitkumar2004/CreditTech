import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Search, Download, ArrowUpRight, Plus, Loader2 } from "lucide-react";
import { Badge, Dot } from "@/components/ui/badge";
import { Avatar } from "@/components/ui/avatar";
import { LoadingState } from "@/components/ui/loading";
import { EmptyState } from "@/components/ui/empty";
import { applications as mockApplications, type Application } from "@/lib/mockData";
import { formatINR, formatDateShort } from "@/lib/utils";
import { decisionApi } from "@/lib/api";

import { usePersona, isAllowed } from "@/lib/usePersona";
import AccessDenied from "@/components/AccessDenied";

type Filter = "ALL" | "PENDING" | "APPROVED" | "REJECTED" | "REFERRED";
const filters: Filter[] = ["ALL", "PENDING", "APPROVED", "REJECTED", "REFERRED"];

export default function Applications() {
  const persona = usePersona();

  if (!isAllowed(persona.role, ["LOAN_OFFICER", "SUPERVISOR", "ADMIN"])) {
    return (
      <AccessDenied
        resourceName="Branch Loan Underwriting Queue"
        allowedRoles={["LOAN_OFFICER", "SUPERVISOR", "ADMIN"]}
      />
    );
  }

  const [filter, setFilter] = useState<Filter>("ALL");
  const [q, setQ] = useState("");

  const { data: apiApps, isLoading } = useQuery({
    queryKey: ["applicationsList", persona.id],
    queryFn: () => decisionApi.listApplications().catch(() => null),
  });

  const sourceApps: Application[] = useMemo(() => {
    if (apiApps && apiApps.length > 0) {
      return apiApps.map((a) => ({
        id: a.id,
        score_id: a.score_id,
        borrower_name: a.borrower_name,
        village: a.village,
        district: a.district,
        state: a.state,
        gender: a.gender as "F" | "M",
        age: a.age,
        landholding_band: a.landholding_band as any,
        requested_amount: a.requested_amount,
        tenure_months: a.requested_tenure_months,
        purpose: a.purpose,
        score_900: a.score_900,
        score_100: a.score_100,
        band: a.band as any,
        confidence_lower: a.confidence_lower,
        confidence_upper: a.confidence_upper,
        model_recommendation: a.model_recommendation,
        decision: (a.decision === "MORE_INFO_REQUIRED" ? "REFERRED" : a.decision) as any,
        override_reason: a.override_reason ?? undefined,
        submitted_at: a.submitted_at,
        sources_used: ["AA", "GEOSPATIAL", "SHG_FPO", "BUREAU"],
        reasons: [],
        features: {},
        sakhi: "Sunita (Bank Sakhi)",
      }));
    }
    return mockApplications;
  }, [apiApps]);

  const items = useMemo(() => {
    return sourceApps
      .filter((a) => (filter === "ALL" ? true : a.decision === filter))
      .filter((a) =>
        q.trim() === ""
          ? true
          : (a.borrower_name.toLowerCase().includes(q.toLowerCase()) ||
             a.id.toLowerCase().includes(q.toLowerCase()) ||
             a.village.toLowerCase().includes(q.toLowerCase()))
      );
  }, [sourceApps, filter, q]);

  const counts = useMemo(() => {
    const c: Record<Filter, number> = { ALL: sourceApps.length, PENDING: 0, APPROVED: 0, REJECTED: 0, REFERRED: 0 };
    sourceApps.forEach((a) => { c[a.decision as Filter] = (c[a.decision as Filter] ?? 0) + 1; });
    return c;
  }, [sourceApps]);

  return (
    <div className="space-y-6">
      <header className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-semibold display">Applications</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Incoming loan files with AI-suggested decisioning and reason codes.
          </p>
        </div>
        <div className="flex gap-2">
          {isLoading && (
            <div className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-muted-foreground">
              <Loader2 className="h-3.5 w-3.5 animate-spin" /> Syncing...
            </div>
          )}
          <button className="pill-ghost"><Download className="h-4 w-4 mr-2" /> Export</button>
          <Link to="/officer/grievances?tab=file" className="pill"><Plus className="h-4 w-4 mr-2" /> File grievance</Link>
        </div>
      </header>

      {/* Filter bar */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="relative flex-1 min-w-[240px] max-w-md">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search borrower, ID, village…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            className="w-full pl-10 pr-4 py-2 text-sm rounded-full glass focus:outline-none focus:ring-2 focus:ring-primary/20"
          />
        </div>

        <div className="flex items-center gap-1 p-1 rounded-full glass">
          {filters.map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={
                "px-3.5 py-1 text-xs font-medium rounded-full transition " +
                (filter === f
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground")
              }
            >
              {f.toLowerCase()} · {counts[f]}
            </button>
          ))}
        </div>
      </div>

      <div className="glass rounded-3xl overflow-hidden">
        <div className="flex justify-between items-center px-6 py-4 border-b border-slate-200/40">
          <span className="section-heading">Showing {items.length} of {sourceApps.length}</span>
          <span className="text-xs text-muted-foreground">Most recent first</span>
        </div>
        {isLoading ? (
          <LoadingState text="Loading applications…" />
        ) : items.length === 0 ? (
          <EmptyState
            icon={Search}
            title="No applications found"
            subtitle="No applications match your filter or search criteria."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th className="first">Borrower</th>
                  <th>Application</th>
                  <th>Amount</th>
                  <th>Score</th>
                  <th>Recommendation</th>
                  <th>Decision</th>
                  <th>Date</th>
                  <th className="last text-right">Action</th>
                </tr>
              </thead>
              <tbody>
                {items.map((a) => (
                  <tr key={a.id}>
                    <td className="first">
                      <div className="flex items-center gap-3">
                        <Avatar name={a.borrower_name} size={32} />
                        <div>
                          <div className="font-medium">{a.borrower_name}</div>
                          <div className="text-xs text-muted-foreground">{a.village}, {a.district}</div>
                        </div>
                      </div>
                    </td>
                    <td className="text-muted-foreground tabular text-xs">{a.id}</td>
                    <td className="tabular font-medium">{formatINR(a.requested_amount)}</td>
                    <td>
                      <div className="flex items-baseline gap-1.5">
                        <span className="text-base font-semibold display tabular">{a.score_900}</span>
                        <span className="text-[11px] text-muted-foreground">{a.band}</span>
                      </div>
                    </td>
                    <td><RecommendationBadge r={a.model_recommendation} /></td>
                    <td><DecisionPill decision={a.decision} /></td>
                    <td className="text-xs text-muted-foreground">{formatDateShort(a.submitted_at)}</td>
                    <td className="last text-right">
                      <Link
                        to={`/applications/${a.id}`}
                        className="inline-flex items-center gap-1 text-primary text-sm hover:underline"
                      >
                        Review <ArrowUpRight className="h-4 w-4" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function RecommendationBadge({ r }: { r: Application["model_recommendation"] }) {
  const map = { APPROVE: { tone: "success" as const, label: "Approve" }, REVIEW: { tone: "warning" as const, label: "Review" }, REJECT: { tone: "danger" as const, label: "Reject" } };
  const m = map[r];
  return <Badge tone={m.tone}>{m.label}</Badge>;
}

function DecisionPill({ decision }: { decision: string }) {
  const map: Record<string, { tone: any; label: string }> = {
    APPROVED: { tone: "success", label: "Approved" },
    REJECTED: { tone: "danger", label: "Rejected" },
    REFERRED: { tone: "info", label: "Referred" },
    PENDING:  { tone: "warning", label: "Pending" },
  };
  const m = map[decision] ?? { tone: "neutral", label: decision };
  return <Badge tone={m.tone}><Dot tone={m.tone} />{m.label}</Badge>;
}
