import { useMemo, useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import {
  MessageSquareWarning, Clock, CheckCircle2, ArrowUpRight, Filter, Send, AlertTriangle,
} from "lucide-react";
import { Badge, Dot } from "@/components/ui/badge";
import { Avatar } from "@/components/ui/avatar";
import { grievances, type Grievance } from "@/lib/mockData";
import { formatDate } from "@/lib/utils";

type Status = "ALL" | Grievance["status"];
const filters: Status[] = ["ALL", "OPEN", "IN_REVIEW", "ESCALATED", "RESOLVED"];

const tabs = [
  { id: "queue", label: "Queue" },
  { id: "file", label: "File new" },
] as const;
type Tab = typeof tabs[number]["id"];

const categories = ["Score dispute", "Data accuracy", "Consent issue", "Officer conduct", "Other"];

export default function Grievances() {
  const [params, setParams] = useSearchParams();
  const initial: Tab = params.get("tab") === "file" ? "file" : "queue";
  const [tab, setTab] = useState<Tab>(initial);

  useEffect(() => {
    setParams((prev) => {
      const next = new URLSearchParams(prev);
      if (tab === "file") next.set("tab", "file"); else next.delete("tab");
      return next;
    }, { replace: true });
  }, [tab, setParams]);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl sm:text-3xl font-semibold display">Grievances</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Appeal channel · 48-hour SLA · escalation at 8h remaining.
        </p>
      </header>

      <div className="flex items-center gap-2 border-b border-slate-200/60">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={
              "relative px-4 py-2.5 text-sm font-medium transition " +
              (tab === t.id
                ? "text-primary"
                : "text-muted-foreground hover:text-foreground")
            }
          >
            {t.label}
            {tab === t.id && (
              <span className="absolute inset-x-3 -bottom-px h-0.5 rounded-full bg-primary" />
            )}
          </button>
        ))}
      </div>

      {tab === "queue" ? <Queue /> : <FileNew />}
    </div>
  );
}

function Queue() {
  const [f, setF] = useState<Status>("ALL");
  const list = useMemo(() => grievances.filter((g) => f === "ALL" || g.status === f), [f]);

  const stats = useMemo(() => ({
    open: grievances.filter((g) => g.status === "OPEN").length,
    review: grievances.filter((g) => g.status === "IN_REVIEW").length,
    escalated: grievances.filter((g) => g.status === "ESCALATED").length,
    resolved: grievances.filter((g) => g.status === "RESOLVED").length,
  }), []);

  return (
    <div className="space-y-6">
      {/* Key metrics */}
      <section className="glass rounded-3xl p-5 grid grid-cols-2 lg:grid-cols-4 gap-6">
        <Metric icon={MessageSquareWarning} label="Open" value={stats.open} tone="warning" />
        <Metric icon={Filter} label="In review" value={stats.review} tone="info" />
        <Metric icon={AlertTriangle} label="Escalated" value={stats.escalated} tone="danger" />
        <Metric icon={CheckCircle2} label="Resolved (7d)" value={stats.resolved + 8} tone="success" />
      </section>

      {/* Filters */}
      <div className="flex items-center gap-2 overflow-x-auto no-scrollbar">
        {filters.map((s) => (
          <button
            key={s}
            onClick={() => setF(s)}
            className={
              "shrink-0 rounded-full px-3.5 py-1.5 text-xs font-medium border transition " +
              (f === s
                ? "bg-primary text-primary-foreground border-primary shadow-[0_10px_24px_-10px_rgba(31,55,105,0.5)]"
                : "bg-white/70 border-white/70 text-muted-foreground hover:text-foreground")
            }
          >
            {s === "ALL" ? "All" : s.replace("_", " ").toLowerCase()}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="glass rounded-3xl overflow-hidden overflow-x-auto">
        <table className="data-table">
          <thead>
            <tr>
              <th className="first">Case</th>
              <th>Borrower</th>
              <th>Issue</th>
              <th>SLA</th>
              <th>Status</th>
              <th className="last text-right">Action</th>
            </tr>
          </thead>
          <tbody>
            {list.map((g) => (
              <tr key={g.id}>
                <td className="first">
                  <div className="font-mono text-xs text-muted-foreground">{g.id}</div>
                  <div className="text-xs text-muted-foreground">{formatDate(g.opened_at)}</div>
                </td>
                <td>
                  <div className="flex items-center gap-2.5">
                    <Avatar name={g.borrower_name} size={30} />
                    <div>
                      <div className="font-medium text-sm">{g.borrower_name}</div>
                      <div className="text-xs text-muted-foreground">{g.village}</div>
                    </div>
                  </div>
                </td>
                <td>
                  <div className="flex flex-wrap items-center gap-1.5">
                    <Badge tone="neutral">{g.category.replace("_", " ")}</Badge>
                    <Badge tone="info">{g.channel}</Badge>
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground max-w-md line-clamp-1">{g.summary}</p>
                </td>
                <td><SlaBadge hours={g.sla_hours_remaining} status={g.status} /></td>
                <td><StatusBadge status={g.status} /></td>
                <td className="last text-right">
                  <button className="inline-flex items-center gap-1 text-primary text-sm hover:underline">
                    Review <ArrowUpRight className="h-4 w-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {list.length === 0 && (
          <div className="text-center text-sm text-muted-foreground py-12">No grievances match this filter.</div>
        )}
      </div>
    </div>
  );
}

function FileNew() {
  const [cat, setCat] = useState(categories[0]);
  const [summary, setSummary] = useState("");
  const [submitted, setSubmitted] = useState(false);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (summary.trim().length < 15) return;
    setSubmitted(true);
    setTimeout(() => setSubmitted(false), 3500);
    setSummary("");
  }

  return (
    <div className="space-y-6">
      <p className="text-sm text-muted-foreground">
        File an appeal on the borrower's behalf · timestamped · enters the SLA queue immediately.
      </p>
      <form onSubmit={handleSubmit} className="glass rounded-3xl p-6 space-y-4">
        <div>
          <label className="section-heading">Category</label>
          <div className="mt-2 flex flex-wrap gap-2">
            {categories.map((c) => (
              <button
                type="button"
                key={c}
                onClick={() => setCat(c)}
                className={
                  "rounded-full px-3.5 py-1.5 text-xs font-medium border transition " +
                  (cat === c
                    ? "bg-primary text-primary-foreground border-primary shadow-[0_10px_24px_-10px_rgba(31,55,105,0.5)]"
                    : "bg-white/70 border-white/70 text-muted-foreground hover:text-foreground")
                }
              >
                {c}
              </button>
            ))}
          </div>
        </div>
        <div>
          <label className="section-heading">Describe the issue</label>
          <textarea
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
            rows={5}
            placeholder="What happened, when, and any evidence to review."
            className="mt-2 w-full rounded-2xl bg-white/70 border border-white/70 outline-none px-4 py-3 text-sm placeholder:text-muted-foreground focus:ring-2 focus:ring-primary/20"
          />
          <p className="mt-1 text-[11px] text-muted-foreground">{summary.length} / 500 characters · minimum 15</p>
        </div>
        <button
          type="submit"
          disabled={summary.trim().length < 15 || submitted}
          className="pill disabled:opacity-60"
        >
          {submitted ? (
            <><CheckCircle2 className="h-4 w-4 mr-1.5" /> Filed · GRV-000242</>
          ) : (
            <><Send className="h-4 w-4 mr-1.5" /> Submit grievance</>
          )}
        </button>
      </form>
    </div>
  );
}

function Metric({ icon: Icon, label, value, tone }: { icon: any; label: string; value: number; tone: "warning" | "info" | "danger" | "success" }) {
  const bg = { warning: "bg-amber-500/10 text-amber-700", info: "bg-sky-500/10 text-sky-700", danger: "bg-rose-500/10 text-rose-700", success: "bg-emerald-500/10 text-emerald-700" }[tone];
  return (
    <div className="flex items-center gap-3">
      <span className={"grid place-items-center h-10 w-10 rounded-2xl " + bg}><Icon className="h-5 w-5" /></span>
      <div>
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="text-2xl font-semibold display tabular">{value}</p>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: Grievance["status"] }) {
  const map = {
    OPEN: { tone: "warning" as const, label: "Open" },
    IN_REVIEW: { tone: "info" as const, label: "In review" },
    ESCALATED: { tone: "danger" as const, label: "Escalated" },
    RESOLVED: { tone: "success" as const, label: "Resolved" },
  }[status];
  return <Badge tone={map.tone}><Dot tone={map.tone as any} /> {map.label}</Badge>;
}

function SlaBadge({ hours, status }: { hours: number; status: Grievance["status"] }) {
  if (status === "RESOLVED") return <Badge tone="success">SLA met</Badge>;
  if (hours <= 8) return <Badge tone="danger"><Clock className="h-3 w-3" /> {hours}h left</Badge>;
  if (hours <= 24) return <Badge tone="warning"><Clock className="h-3 w-3" /> {hours}h left</Badge>;
  return <Badge tone="info"><Clock className="h-3 w-3" /> {hours}h left</Badge>;
}
