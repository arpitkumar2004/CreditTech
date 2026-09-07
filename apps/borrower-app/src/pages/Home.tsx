import { Link } from "react-router-dom";
import {
  ArrowUpRight,
  TrendingUp,
  Users,
  ClipboardList,
  ShieldCheck,
  Percent,
  Activity,
  MapPin,
  CheckCircle2,
  FileText,
  Sparkles,
  HelpCircle,
  FilePlus2,
} from "lucide-react";
import {
  AreaChart,
  Area,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { useQuery } from "@tanstack/react-query";
import { Badge, Dot } from "@/components/ui/badge";
import {
  portfolioKpis,
  applicationsByDay,
  scoreDistribution,
  applications,
} from "@/lib/mockData";
import { formatINR } from "@/lib/utils";
import { dashboardApi, decisionApi, chartsApi, type DevPersona } from "@/lib/api";
import { usePersona } from "@/lib/usePersona";
import {
  RecourseLadderPlot,
  CashflowPulsePlot,
  ScoreZonesPlot,
  NDVITrajectoryPlot,
} from "@/components/charts";

export default function Home() {
  const persona = usePersona();

  if (persona.role === "BORROWER") {
    return <BorrowerHome persona={persona} />;
  }

  if (persona.role === "BANK_SAKHI") {
    return <BankSakhiHome persona={persona} />;
  }

  return <StaffHome persona={persona} />;
}

// ── 1. Borrower Self-Service Portal View ────────────────────────────────────

function BorrowerHome({ persona }: { persona: DevPersona }) {
  const { data: borrowerCharts } = useQuery({
    queryKey: ["borrowerCharts", persona.borrowerId],
    queryFn: () => chartsApi.getCharts({ persona: "borrower", borrowerId: persona.borrowerId }).catch(() => null),
  });

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <header className="glass rounded-3xl p-6 relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold text-primary uppercase tracking-wider">
              <Sparkles className="h-4 w-4" />
              <span>Self-Service Borrower Portal · DPDP Act 2023 Compliant</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground mt-1">
              Namaste, {persona.name}
            </h1>
            <p className="text-sm text-muted-foreground mt-1 flex items-center gap-2">
              <MapPin className="h-3.5 w-3.5" />
              <span>{persona.branchOrVillage}</span>
              <span>·</span>
              <span className="font-mono text-xs">ID: {persona.borrowerId ?? persona.id}</span>
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="glass-soft px-3.5 py-1.5 rounded-full text-xs font-medium text-emerald-700 flex items-center gap-1.5 border border-emerald-500/30">
              <CheckCircle2 className="h-4 w-4 text-emerald-600" />
              <span>Consent Verified Active</span>
            </span>
          </div>
        </div>
      </header>

      {/* Credit Score & Underwriting Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Score Card */}
        <div className="md:col-span-2 glass rounded-3xl p-6 space-y-5">
          <div className="flex items-start justify-between">
            <div>
              <span className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">
                Alternative Credit Appraisal
              </span>
              <h3 className="text-lg font-bold text-foreground mt-0.5">
                Composite Rural Credit Score
              </h3>
            </div>
            <Badge tone="success">Model: v1.1.0-woe-scorecard</Badge>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-6 p-4 rounded-2xl bg-white/70 border border-white/80 shadow-sm">
            <div className="text-center sm:text-left">
              <div className="text-4xl font-extrabold text-primary tabular-nums tracking-tight">
                {borrowerCharts?.borrower_summary?.current_score ?? 771} <span className="text-sm font-medium text-muted-foreground">/ 900</span>
              </div>
              <div className="text-xs font-semibold text-emerald-600 uppercase tracking-wide mt-0.5">
                {borrowerCharts?.borrower_summary?.current_band ?? "Band A · Good (Low Credit Risk)"}
              </div>
              <div className="text-[11px] text-muted-foreground mt-1">
                90% Confidence Interval: [{borrowerCharts?.borrower_summary?.confidence_range?.[0] ?? 710} – {borrowerCharts?.borrower_summary?.confidence_range?.[1] ?? 770}]
              </div>
            </div>

            <div className="h-12 w-px bg-slate-200 hidden sm:block" />

            <div className="space-y-1.5 text-xs text-muted-foreground flex-1">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 shrink-0" />
                <span><strong>Consistently active SHG group savings:</strong> 98% on-time repayment</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 shrink-0" />
                <span><strong>Canal-irrigated farmland:</strong> High vegetative vigor index (NDVI: 0.68)</span>
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <span className="text-xs font-semibold text-foreground uppercase tracking-wider">
              Consented Data Rails
            </span>
            <div className="flex flex-wrap gap-2">
              <span className="pill-ghost !py-1 !px-2.5 text-xs">Account Aggregator (AA)</span>
              <span className="pill-ghost !py-1 !px-2.5 text-xs">Geospatial Satellite Rail</span>
              <span className="pill-ghost !py-1 !px-2.5 text-xs">SHG / FPO Group Records</span>
              <span className="pill-ghost !py-1 !px-2.5 text-xs">Credit Bureau</span>
            </div>
          </div>
        </div>

        {/* Loan Application Status */}
        <div className="glass rounded-3xl p-6 space-y-4 flex flex-col justify-between">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">
                Application Status
              </span>
              <Badge tone="success">APPROVED</Badge>
            </div>

            <div className="space-y-1">
              <div className="text-2xl font-bold text-foreground">
                ₹50,000
              </div>
              <div className="text-xs text-muted-foreground">
                12 Months Tenure · 10.5% p.a.
              </div>
            </div>

            <div className="text-xs text-muted-foreground space-y-1 pt-2 border-t border-slate-200/50">
              <div><strong>Purpose:</strong> Irrigation equipment & organic seeds</div>
              <div><strong>Partner RE:</strong> State Bank of India (RE-SBI-01)</div>
              <div><strong>Underwriter:</strong> Rajesh Kumar (OFF-001)</div>
            </div>
          </div>

          <div className="space-y-2 pt-4">
            <Link to="/consent" className="pill w-full justify-center text-xs">
              <FileText className="h-3.5 w-3.5 mr-1.5" />
              View Consent Chain
            </Link>
            <Link to="/grievances?tab=file" className="pill-ghost w-full justify-center text-xs">
              <HelpCircle className="h-3.5 w-3.5 mr-1.5" />
              Dispute / File Appeal
            </Link>
          </div>
        </div>
      </div>

      {/* Actionable Recourse Progress Ladder */}
      <RecourseLadderPlot
        data={borrowerCharts?.borrower_summary}
        steps={borrowerCharts?.recourse_ladder}
      />

      {/* 12-Month Cashflow & Mutual SHG Savings Pulse */}
      <CashflowPulsePlot data={borrowerCharts?.cashflow_pulse} />
    </div>
  );
}

// ── 2. Bank Sakhi Field Portal View ────────────────────────────────────────

function BankSakhiHome({ persona }: { persona: DevPersona }) {
  const { data: sakhiCharts } = useQuery({
    queryKey: ["sakhiCharts"],
    queryFn: () => chartsApi.getCharts({ persona: "borrower" }).catch(() => null),
  });

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <header className="glass rounded-3xl p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold text-emerald-700 uppercase tracking-wider">
              <Users className="h-4 w-4 text-emerald-600" />
              <span>Bank Sakhi Assisted Field Portal</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground mt-1">
              {persona.name}
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              Field Agent · {persona.branchOrVillage} · Field Onboarding & Data Ingestion
            </p>
          </div>

          <Link to="/applications/new" className="pill gap-2">
            <FilePlus2 className="h-4 w-4" />
            New Borrower Onboarding
          </Link>
        </div>
      </header>

      {/* Field Actions Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Link to="/applications/new" className="glass rounded-2xl p-5 hover:bg-white transition space-y-2 group">
          <div className="h-10 w-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center group-hover:scale-105 transition-transform">
            <FilePlus2 className="h-5 w-5" />
          </div>
          <div className="font-semibold text-sm text-foreground">Sakhi Entry Form</div>
          <p className="text-xs text-muted-foreground">Capture SHG thrift, meetings & land details for a new borrower.</p>
        </Link>

        <Link to="/borrowers" className="glass rounded-2xl p-5 hover:bg-white transition space-y-2 group">
          <div className="h-10 w-10 rounded-xl bg-blue-500/10 text-blue-600 flex items-center justify-center group-hover:scale-105 transition-transform">
            <Users className="h-5 w-5" />
          </div>
          <div className="font-semibold text-sm text-foreground">Four-Rail Ingestion</div>
          <p className="text-xs text-muted-foreground">Trigger Account Aggregator, Geospatial, Bureau and SHG pulls.</p>
        </Link>

        <Link to="/consent" className="glass rounded-2xl p-5 hover:bg-white transition space-y-2 group">
          <div className="h-10 w-10 rounded-xl bg-violet-500/10 text-violet-600 flex items-center justify-center group-hover:scale-105 transition-transform">
            <FileText className="h-5 w-5" />
          </div>
          <div className="font-semibold text-sm text-foreground">Consent Verification</div>
          <p className="text-xs text-muted-foreground">Verify active DPDP consent and inspect cryptographic hash-chain.</p>
        </Link>

        <Link to="/grievances" className="glass rounded-2xl p-5 hover:bg-white transition space-y-2 group">
          <div className="h-10 w-10 rounded-xl bg-amber-500/10 text-amber-600 flex items-center justify-center group-hover:scale-105 transition-transform">
            <HelpCircle className="h-5 w-5" />
          </div>
          <div className="font-semibold text-sm text-foreground">Assisted Appeals</div>
          <p className="text-xs text-muted-foreground">Submit score dispute or appeal on behalf of a SHG borrower.</p>
        </Link>
      </div>

      {/* Field Counseling & Borrower Recourse Telemetry */}
      <div className="space-y-4 pt-2">
        <h3 className="text-base font-semibold text-foreground">
          Assisted Borrower Counseling & Recourse Ladder
        </h3>
        <RecourseLadderPlot
          data={sakhiCharts?.borrower_summary}
          steps={sakhiCharts?.recourse_ladder}
        />
        <CashflowPulsePlot data={sakhiCharts?.cashflow_pulse} />
      </div>
    </div>
  );
}

// ── 3. Staff & Officer Dashboard View ──────────────────────────────────────

function StaffHome({ persona }: { persona: DevPersona }) {
  const { data: metrics } = useQuery({
    queryKey: ["portfolioMetrics"],
    queryFn: () => dashboardApi.portfolio().catch(() => null),
  });

  const { data: apiApps } = useQuery({
    queryKey: ["applicationsList"],
    queryFn: () => decisionApi.listApplications().catch(() => null),
  });

  const { data: officerCharts } = useQuery({
    queryKey: ["officerCharts"],
    queryFn: () => chartsApi.getCharts({ persona: "officer" }).catch(() => null),
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
        <div className="flex items-center gap-3 mt-1 flex-wrap">
          <h1 className="text-2xl sm:text-3xl font-semibold display">
            Overview · {persona.name}
          </h1>
          <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-primary/10 text-primary uppercase tracking-wider">
            {persona.role.replace("_", " ")}
          </span>
        </div>
        <p className="text-sm text-muted-foreground mt-1">
          {persona.branchOrVillage} · {pendingCount} applications await underwriting review.
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          <Badge tone="success"><Dot tone="success" /> Fairness gate: PASS</Badge>
          <Badge tone="primary">Model v1.1.0-woe-scorecard active</Badge>
          <Badge tone="info"><MapPin className="h-3 w-3" /> 15 village clusters</Badge>
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
                    <stop offset="0%" stopColor="hsl(150 40% 35%)" stopOpacity={0.25} />
                    <stop offset="100%" stopColor="hsl(150 40% 35%)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.05)" />
                <XAxis dataKey="day" tick={{ fontSize: 11 }} tickLine={false} />
                <YAxis tick={{ fontSize: 11 }} tickLine={false} />
                <Tooltip />
                <Area type="monotone" dataKey="submitted" stroke="hsl(220 45% 22%)" fill="url(#g1)" strokeWidth={2} />
                <Area type="monotone" dataKey="approved" stroke="hsl(150 40% 35%)" fill="url(#g2)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Score distribution */}
        <div className="glass rounded-3xl p-5">
          <p className="text-sm font-semibold display">Score bands</p>
          <p className="text-xs text-muted-foreground">Active borrower distribution</p>
          <div className="h-48 mt-2">
            <ResponsiveContainer>
              <PieChart>
                <Pie data={scoreDistribution} dataKey="count" nameKey="band" innerRadius={50} outerRadius={70} paddingAngle={4}>
                  {scoreDistribution.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={["#16a34a", "#2563eb", "#ca8a04", "#dc2626"][index % 4]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs mt-2">
            {scoreDistribution.map((d, i) => (
              <div key={d.band} className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full" style={{ backgroundColor: ["#16a34a", "#2563eb", "#ca8a04", "#dc2626"][i % 4] }} />
                <span className="text-muted-foreground">{d.band}:</span>
                <span className="font-semibold">{d.count}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Recent applications table */}
      <section className="glass rounded-3xl p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <p className="text-sm font-semibold display">Recent applications</p>
            <p className="text-xs text-muted-foreground">Prioritized by SLA clock</p>
          </div>
          <Link to="/applications" className="pill-ghost text-xs">View all</Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200/60 text-muted-foreground">
                <th className="pb-2">Borrower</th>
                <th className="pb-2">Village</th>
                <th className="pb-2">Score</th>
                <th className="pb-2">Recommendation</th>
                <th className="pb-2">Status</th>
                <th className="pb-2 text-right">Amount</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200/40">
              {recent.map((a) => (
                <tr key={a.id} className="hover:bg-white/50 transition">
                  <td className="py-2.5 font-medium">{a.borrower_name}</td>
                  <td className="py-2.5 text-muted-foreground">{a.village}</td>
                  <td className="py-2.5 font-semibold">{a.score_900}</td>
                  <td className="py-2.5">
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-100 text-slate-700">
                      {a.model_recommendation}
                    </span>
                  </td>
                  <td className="py-2.5">
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-100 text-emerald-800">
                      {a.decision}
                    </span>
                  </td>
                  <td className="py-2.5 text-right font-medium">{formatINR(a.requested_amount)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Underwriter Telemetry: 3-Zone Decision Spectrum & Satellite Vigor */}
      <section className="space-y-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-foreground">
            Underwriter Decision Support & Field Telemetry
          </h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            Automated STP approval zones, branch override distribution, and Sentinel-2 multi-spectral crop vigor
          </p>
        </div>
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <ScoreZonesPlot data={officerCharts?.score_zones} />
          <NDVITrajectoryPlot data={officerCharts?.ndvi_trajectory} />
        </div>
      </section>
    </div>
  );
}
