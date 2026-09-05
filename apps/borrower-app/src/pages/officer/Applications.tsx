import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Search, Download, ArrowUpRight, Plus } from "lucide-react";
import { Badge, Dot } from "@/components/ui/badge";
import { Avatar } from "@/components/ui/avatar";
import { applications, type Application } from "@/lib/mockData";
import { formatINR, formatDateShort } from "@/lib/utils";

type Filter = "ALL" | "PENDING" | "APPROVED" | "REJECTED" | "REFERRED";
const filters: Filter[] = ["ALL", "PENDING", "APPROVED", "REJECTED", "REFERRED"];

export default function Applications() {
  const [filter, setFilter] = useState<Filter>("ALL");
  const [q, setQ] = useState("");

  const items = useMemo(() => {
    return applications
      .filter((a) => (filter === "ALL" ? true : a.decision === filter))
      .filter((a) =>
        q.trim() === ""
          ? true
          : (a.borrower_name.toLowerCase().includes(q.toLowerCase()) ||
             a.id.toLowerCase().includes(q.toLowerCase()) ||
             a.village.toLowerCase().includes(q.toLowerCase())),
      );
  }, [filter, q]);

  const counts = useMemo(() => {
    const c: Record<Filter, number> = { ALL: applications.length, PENDING: 0, APPROVED: 0, REJECTED: 0, REFERRED: 0 };
    applications.forEach((a) => { c[a.decision as Filter] = (c[a.decision as Filter] ?? 0) + 1; });
    return c;
  }, []);

  return (
    <div className="space-y-6">
      <header className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-semibold display">Applications</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Review the queue · officer decisions logged with SHAP rationale.
          </p>
        </div>
        <div className="flex gap-2">
          <Link to="/applications/new" className="pill"><Plus className="h-4 w-4 mr-1.5" /> New application</Link>
          <button className="pill-ghost"><Download className="h-4 w-4 mr-2" /> Export CSV</button>
        </div>
      </header>

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex items-center gap-2 bg-white/70 rounded-full px-3.5 py-2 border border-white/70 flex-1">
          <Search className="h-4 w-4 text-muted-foreground" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search borrower, application ID, village…"
            className="bg-transparent outline-none text-sm flex-1 placeholder:text-muted-foreground"
          />
        </div>
        <div className="flex items-center gap-2 overflow-x-auto no-scrollbar">
          {filters.map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={
                "shrink-0 rounded-full px-3.5 py-1.5 text-xs font-medium border transition " +
                (filter === f
                  ? "bg-primary text-primary-foreground border-primary shadow-[0_10px_24px_-10px_rgba(31,55,105,0.5)]"
                  : "bg-white/70 border-white/70 text-muted-foreground hover:text-foreground")
              }
            >
              {f.charAt(0) + f.slice(1).toLowerCase()} · {counts[f]}
            </button>
          ))}
        </div>
      </div>

      <div className="glass rounded-3xl overflow-hidden">
        <div className="flex justify-between items-center px-6 py-4 border-b border-slate-200/40">
          <span className="section-heading">Showing {items.length} of {applications.length}</span>
          <span className="text-xs text-muted-foreground">Most recent first</span>
        </div>
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
        {items.length === 0 && (
          <div className="text-center text-sm text-muted-foreground py-16">No applications match this filter.</div>
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
