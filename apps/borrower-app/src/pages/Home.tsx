import { Link } from "react-router-dom";
import {
  ArrowUpRight, TrendingUp, Users, ClipboardList, ShieldCheck,
  Percent, Activity, MapPin,
} from "lucide-react";
import {
  AreaChart, Area, ResponsiveContainer, Tooltip, XAxis, YAxis,
  CartesianGrid, PieChart, Pie, Cell,
} from "recharts";
import { useQuery } from "@tanstack/react-query";
import { Badge, Dot } from "@/components/ui/badge";
import { Avatar } from "@/components/ui/avatar";
import {
  portfolioKpis, applicationsByDay, scoreDistribution, applications, officerProfile,
} from "@/lib/mockData";
import { formatINR, formatDateShort } from "@/lib/utils";
import { dashboardApi, decisionApi } from "@/lib/api";

export default function Home() {
  const { data: metrics } = useQuery({
    queryKey: ["portfolioMetrics"],
    queryFn: () => dashboardApi.portfolio().catch(() => null),
  });

  const { data: apiApps } = useQuery({
    queryKey: ["applicationsList"],
    queryFn: () => decisionApi.listApplications().catch(() => null),
  });

  const recent = apiApps && apiApps.length > 0
    ? apiApps.slice(0, 6).map((a) => ({
        id: a.id,
        borrower_name: a.borrower_name,
        village: a.village,
        gender: a.gender as "F" | "M",
        age: a.age,
        score_900: a.score_900,
        band: a.band,
        decision: a.decision,
        model_recommendation: a.model_recommendation,
        requested_amount: a.requested_amount,
        submitted_at: a.submitted_at,
      }))
    : applications.slice(0, 6);

  const pendingCount = metrics?.applications_pending ?? portfolioKpis.pending_applications;
  const disbAmount = metrics?.disbursed_amount_approved ?? portfolioKpis.cumulative_disbursement;
  const activeBorrowers = metrics?.borrowers ?? portfolioKpis.active_borrowers;
  const approvalRate = metrics?.approval_rate != null
    ? `${(metrics.approval_rate * 100).toFixed(1)}%`
    : `${(portfolioKpis.approval_rate_30d * 100).toFixed(1)}%`;

  const kpis = [
    { icon: TrendingUp, label: "Cumulative disbursement", value: formatINR(disbAmount, { compact: true }), sub: "+12.4% MoM" },
    { icon: Users, label: "Active borrowers", value: activeBorrowers.toLocaleString("en-IN"), sub: `${portfolioKpis.villages_active} villages` },
    { icon: ClipboardList, label: "Pending review", value: String(pendingCount), sub: "SLA · under 24h" },
    { icon: Percent, label: "Approval rate", value: approvalRate, sub: "Within fairness band" },
  ];

  return (
    <div className="space-y-6">
      <header>
        <p className="text-sm text-muted-foreground flex items-center gap-1.5">
          <ShieldCheck className="h-4 w-4" /> Welcome back
        </p>
        <h1 className="mt-1 text-2xl sm:text-3xl font-semibold display">
          Overview · {officerProfile.name.split(" ")[0]}
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          {pendingCount} applications await your review. Fairness gate is passing across all monitored dimensions.
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          <Badge tone="success"><Dot tone="success" /> Fairness gate: PASS</Badge>
          <Badge tone="primary">Model v1.0.0-logistic active</Badge>
          <Badge tone="info"><MapPin className="h-3 w-3" /> {portfolioKpis.villages_active} pilot villages</Badge>
        </div>
      </header>

      {/* Key metrics strip */}
      <section className="glass rounded-3xl p-5 grid grid-cols-2 lg:grid-cols-4 gap-6">
        {kpis.map((k) => (
          <div key={k.label} className="flex items-center gap-3">
            <span className="inline-grid place-items-center h-11 w-11 rounded-2xl bg-primary/10 text-primary shrink-0">
              <k.icon className="h-5 w-5" />
            </span>
            <div className="min-w-0">
              <p className="text-[11px] uppercase tracking-wide text-muted-foreground">{k.label}</p>
              <p className="text-xl font-semibold display tabular">{k.value}</p>
              <p className="text-[11px] text-muted-foreground truncate">{k.sub}</p>
            </div>
          </div>
        ))}
      </section>

      {/* Primary actions */}
      <div className="flex flex-wrap gap-2">
        <Link to="/applications" className="pill">Open queue <ArrowUpRight className="ml-1.5 h-4 w-4" /></Link>
        <Link to="/applications/new" className="pill-ghost">New application</Link>
        <Link to="/fairness" className="pill-ghost">Fairness</Link>
      </div>

      {/* Charts */}
      <section className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="glass rounded-3xl p-5 lg:col-span-2">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm font-semibold display">Applications — last 14 days</p>
              <p className="text-xs text-muted-foreground">Submitted vs. approved</p>
            </div>
            <Badge tone="success"><Activity className="h-3 w-3" /> healthy</Badge>
          </div>
          <div className="h-64 mt-3">
            <ResponsiveContainer>
              <AreaChart data={applicationsByDay} margin={{ top: 10, right: 10, bottom: 0, left: -20 }}>
                <defs>
                  <linearGradient id="g1" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="hsl(220 45% 22%)" stopOpacity={0.25} />
                    <stop offset="100%" stopColor="hsl(220 45% 22%)" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="g2" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="hsl(152 68% 40%)" stopOpacity={0.25} />
                    <stop offset="100%" stopColor="hsl(152 68% 40%)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="hsl(220 30% 92%)" strokeDasharray="3 4" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: "hsl(220 15% 45%)" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: "hsl(220 15% 45%)" }} axisLine={false} tickLine={false} width={40} />
                <Tooltip contentStyle={{ borderRadius: 14, border: "1px solid hsl(220 30% 90%)", background: "rgba(255,255,255,0.95)", fontSize: 12 }} />
                <Area type="monotone" dataKey="submitted" stroke="hsl(220 45% 22%)" fill="url(#g1)" strokeWidth={2} />
                <Area type="monotone" dataKey="approved" stroke="hsl(152 68% 40%)" fill="url(#g2)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="glass rounded-3xl p-5">
          <p className="text-sm font-semibold display">Score distribution</p>
          <p className="text-xs text-muted-foreground">1,247 active borrowers</p>
          <div className="h-48 mt-2">
            <ResponsiveContainer>
              <PieChart>
                <Pie data={scoreDistribution} dataKey="count" nameKey="band" innerRadius={45} outerRadius={72} paddingAngle={2}>
                  {scoreDistribution.map((s) => <Cell key={s.band} fill={s.color} />)}
                </Pie>
                <Tooltip contentStyle={{ borderRadius: 14, border: "1px solid hsl(220 30% 90%)", background: "rgba(255,255,255,0.95)", fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <ul className="mt-3 space-y-1.5">
            {scoreDistribution.map((s) => (
              <li key={s.band} className="flex items-center justify-between text-xs">
                <span className="flex items-center gap-2 text-muted-foreground">
                  <span className="h-2 w-2 rounded-full" style={{ background: s.color }} />
                  {s.band}
                </span>
                <span className="tabular font-medium">{s.count}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* Recent applications table */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <p className="section-heading">Recent applications</p>
          <Link to="/applications" className="text-sm text-primary inline-flex items-center gap-1 hover:underline">
            See all <ArrowUpRight className="h-4 w-4" />
          </Link>
        </div>
        <div className="glass rounded-3xl overflow-hidden overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th className="first">Borrower</th>
                <th>Application</th>
                <th>Amount</th>
                <th>Score</th>
                <th>Decision</th>
                <th className="last">Date</th>
              </tr>
            </thead>
            <tbody>
              {recent.map((a) => (
                <tr key={a.id}>
                  <td className="first">
                    <Link to={`/applications/${a.id}`} className="flex items-center gap-3 hover:text-primary">
                      <Avatar name={a.borrower_name} size={30} />
                      <div>
                        <div className="font-medium">{a.borrower_name}</div>
                        <div className="text-xs text-muted-foreground">{a.village}</div>
                      </div>
                    </Link>
                  </td>
                  <td className="text-xs text-muted-foreground tabular">{a.id}</td>
                  <td className="tabular font-medium">{formatINR(a.requested_amount)}</td>
                  <td className="tabular font-semibold display">{a.score_900} <span className="text-[11px] text-muted-foreground font-normal">{a.band}</span></td>
                  <td><DecisionPill decision={a.decision} /></td>
                  <td className="last text-xs text-muted-foreground">{formatDateShort(a.submitted_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function DecisionPill({ decision }: { decision: string }) {
  const map = {
    APPROVED: { tone: "success" as const, label: "Approved" },
    REJECTED: { tone: "danger" as const, label: "Rejected" },
    REFERRED: { tone: "info" as const, label: "Referred" },
    PENDING:  { tone: "warning" as const, label: "Pending" },
  }[decision] ?? { tone: "neutral" as const, label: decision };
  return <Badge tone={map.tone}><Dot tone={map.tone as any} />{map.label}</Badge>;
}
