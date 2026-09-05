/**
 * Demo dataset for the Officer Portal.
 *
 * Populated deterministically so screens look production-realistic while the
 * ML/data layer is being built out. When the FastAPI backend + registered
 * champion model are wired, this file becomes the fallback used only when the
 * API is unreachable (see lib/api.ts).
 */

export type Decision = "APPROVED" | "REJECTED" | "REFERRED" | "PENDING";

export interface Reason {
  rank: number;
  feature: string;
  direction: "POSITIVE" | "NEGATIVE";
  shap: number;
  en: string;
  hi: string;
}

export interface Application {
  id: string;
  score_id: string;
  borrower_name: string;
  village: string;
  district: string;
  state: string;
  gender: "F" | "M";
  age: number;
  landholding_band: "LANDLESS" | "MARGINAL" | "SMALL" | "SEMI_MEDIUM" | "MEDIUM" | "LARGE";
  score_100: number;
  score_900: number;
  band: "A" | "B" | "C" | "D";
  requested_amount: number;
  tenure_months: number;
  purpose: string;
  submitted_at: string;
  model_recommendation: "APPROVE" | "REVIEW" | "REJECT";
  decision: Decision;
  confidence_lower: number;
  confidence_upper: number;
  sources_used: Array<"SHG_FPO" | "AA" | "GEOSPATIAL" | "BUREAU">;
  reasons: Reason[];
  features: Record<string, number>;
  sakhi: string;
}

const villages = [
  { v: "Suratgarh", d: "Sri Ganganagar", s: "Rajasthan" },
  { v: "Chidawa", d: "Jhunjhunu", s: "Rajasthan" },
  { v: "Hanumangarh", d: "Hanumangarh", s: "Rajasthan" },
  { v: "Nokha", d: "Bikaner", s: "Rajasthan" },
  { v: "Barmer Rural", d: "Barmer", s: "Rajasthan" },
];

const names = [
  "Kavita Devi", "Radha Meena", "Sunita Sharma", "Ramesh Kumar",
  "Prakash Jat", "Meena Bai", "Anita Yadav", "Suraj Prasad",
  "Lakshmi Devi", "Ganga Bishnoi", "Mohan Singh", "Savita Yadav",
  "Bhawana Choudhary", "Deepak Meena", "Kiran Devi", "Vijay Kumar",
  "Pooja Sharma", "Arjun Bishnoi", "Sushila Bai", "Neelam Devi",
];

const purposes = ["Kharif crop inputs", "Rabi seeds & fertiliser", "Dairy cattle purchase", "Farm equipment", "Micro-enterprise (tailoring)", "Poultry setup"];

const sakhis = ["Kanta Meghwal", "Sarita Choudhary", "Beena Devi", "Rekha Prajapat"];

function scoreBand(s: number): "A" | "B" | "C" | "D" {
  if (s >= 75) return "A";
  if (s >= 60) return "B";
  if (s >= 45) return "C";
  return "D";
}

function rec(s: number): "APPROVE" | "REVIEW" | "REJECT" {
  if (s >= 62) return "APPROVE";
  if (s >= 45) return "REVIEW";
  return "REJECT";
}

function mkReasons(seed: number, _features: Record<string, number>): Reason[] {
  const catalogue: Array<{ f: string; en: string; hi: string; sign: 1 | -1 }> = [
    { f: "shg_repayment_rate", en: "Strong SHG repayment history (92% on-time)", hi: "मजबूत SHG चुकौती इतिहास (92% समय पर)", sign: 1 },
    { f: "shg_meeting_attendance_pct", en: "Regular SHG meeting attendance", hi: "नियमित SHG बैठक उपस्थिति", sign: 1 },
    { f: "aa_avg_monthly_credit", en: "Stable monthly cashflow via AA", hi: "AA द्वारा स्थिर मासिक नकदी प्रवाह", sign: 1 },
    { f: "land_quality_ndvi_avg", en: "Healthy NDVI on cultivated land", hi: "कृषि भूमि पर स्वस्थ NDVI", sign: 1 },
    { f: "pm_kisan_regularity", en: "Consistent PM-KISAN receipts", hi: "PM-KISAN नियमित प्राप्तियां", sign: 1 },
    { f: "irrigation_access", en: "Assured irrigation available", hi: "सुनिश्चित सिंचाई उपलब्ध", sign: 1 },
    { f: "income_stability_cv", en: "High income volatility across seasons", hi: "मौसमों में उच्च आय अस्थिरता", sign: -1 },
    { f: "rainfall_deviation_pct", en: "Below-normal rainfall this season", hi: "इस मौसम में सामान्य से कम वर्षा", sign: -1 },
    { f: "utility_payment_ontime_pct", en: "Occasional late utility payments", hi: "कभी-कभी विलंबित उपयोगिता भुगतान", sign: -1 },
  ];
  const picked: Reason[] = [];
  const start = seed % catalogue.length;
  for (let i = 0; i < 5; i++) {
    const c = catalogue[(start + i) % catalogue.length];
    picked.push({
      rank: i + 1,
      feature: c.f,
      direction: c.sign === 1 ? "POSITIVE" : "NEGATIVE",
      shap: Math.round((0.25 - i * 0.04 + ((seed * (i + 1)) % 7) / 100) * 100) / 100 * c.sign,
      en: c.en,
      hi: c.hi,
    });
  }
  return picked;
}

function seededScore(seed: number): number {
  // Deterministic pseudo-random in [30, 92]
  const x = Math.sin(seed * 12.9898) * 43758.5453;
  const frac = x - Math.floor(x);
  return Math.round((30 + frac * 62) * 10) / 10;
}

export const applications: Application[] = Array.from({ length: 42 }).map((_, i) => {
  const s100 = seededScore(i + 1);
  const v = villages[i % villages.length];
  const bands = ["MARGINAL", "SMALL", "SEMI_MEDIUM", "MEDIUM", "LANDLESS", "LARGE"] as const;
  const sources: Application["sources_used"] = i % 5 === 0
    ? ["SHG_FPO", "GEOSPATIAL"]
    : ["SHG_FPO", "AA", "GEOSPATIAL"];
  const features = {
    shg_repayment_rate: 0.78 + ((i * 3) % 22) / 100,
    shg_meeting_attendance_pct: 65 + ((i * 7) % 30),
    aa_avg_monthly_credit: 8000 + ((i * 900) % 15000),
    aa_avg_monthly_debit: 6500 + ((i * 700) % 12000),
    land_quality_ndvi_avg: 0.42 + ((i * 5) % 40) / 100,
    ndvi_trend_2season: -0.1 + ((i * 3) % 30) / 100,
    rainfall_deviation_pct: -25 + ((i * 11) % 60),
    utility_payment_ontime_pct: 60 + ((i * 5) % 35),
    pm_kisan_regularity: 0.5 + ((i * 3) % 45) / 100,
    irrigation_access: i % 3 === 0 ? 0 : 1,
    land_holding_acres: 0.5 + ((i * 4) % 60) / 10,
  };
  const dec: Decision = i < 3 ? "PENDING" : (i % 6 === 0 ? "REFERRED" : (s100 >= 60 ? "APPROVED" : (s100 >= 45 ? "PENDING" : "REJECTED")));
  return {
    id: `LA-2026-${(3040 + i).toString().padStart(5, "0")}`,
    score_id: `sc-${(i + 1).toString(36).padStart(6, "0")}`,
    borrower_name: names[i % names.length],
    village: v.v,
    district: v.d,
    state: v.s,
    gender: (i % 3 === 2 ? "M" : "F") as "F" | "M",
    age: 24 + (i % 32),
    landholding_band: bands[i % bands.length],
    score_100: s100,
    score_900: 300 + Math.round((s100 / 100) * 600),
    band: scoreBand(s100),
    requested_amount: 15000 + ((i * 3500) % 60000),
    tenure_months: 6 + (i % 4) * 6,
    purpose: purposes[i % purposes.length],
    submitted_at: new Date(Date.now() - (i * 3.5 * 3600_000)).toISOString(),
    model_recommendation: rec(s100),
    decision: dec,
    confidence_lower: Math.max(300, 300 + Math.round((s100 / 100) * 600) - 45),
    confidence_upper: Math.min(900, 300 + Math.round((s100 / 100) * 600) + 45),
    sources_used: sources,
    reasons: mkReasons(i + 3, features),
    features,
    sakhi: sakhis[i % sakhis.length],
  };
});

export const portfolioKpis = {
  cumulative_disbursement: 4_82_50_000,
  active_borrowers: 1247,
  pending_applications: applications.filter((a) => a.decision === "PENDING").length,
  approval_rate_30d: 0.612,
  ninety_day_delinquency: 0.037,
  avg_score: 63.4,
  avg_ticket: 28400,
  villages_active: 5,
};

export const applicationsByDay = Array.from({ length: 14 }).map((_, i) => {
  const d = new Date();
  d.setDate(d.getDate() - (13 - i));
  return {
    date: d.toLocaleDateString("en-IN", { day: "2-digit", month: "short" }),
    submitted: 18 + Math.round(Math.sin(i / 2) * 6) + (i % 3),
    approved: 11 + Math.round(Math.sin(i / 2) * 4) + (i % 2),
    rejected: 3 + (i % 2),
  };
});

export const scoreDistribution = [
  { band: "300-450 (D)", count: 42, color: "#dc2626" },
  { band: "451-600 (C)", count: 168, color: "#f59e0b" },
  { band: "601-750 (B)", count: 542, color: "#3b82f6" },
  { band: "751-900 (A)", count: 495, color: "#059669" },
];

export const fairnessSlices = [
  { dim: "Gender", groups: [
    { g: "Female", approval: 0.618, n: 742, delta: 0.006 },
    { g: "Male", approval: 0.591, n: 483, delta: -0.021 },
    { g: "Other", approval: 0.600, n: 22, delta: -0.012 },
  ]},
  { dim: "Landholding", groups: [
    { g: "Landless", approval: 0.583, n: 88, delta: -0.029 },
    { g: "Marginal", approval: 0.622, n: 512, delta: 0.010 },
    { g: "Small", approval: 0.615, n: 398, delta: 0.003 },
    { g: "Semi-Medium", approval: 0.628, n: 141, delta: 0.016 },
    { g: "Medium", approval: 0.595, n: 82, delta: -0.017 },
    { g: "Large", approval: 0.567, n: 26, delta: -0.045 },
  ]},
  { dim: "Site", groups: [
    { g: "Suratgarh", approval: 0.628, n: 271, delta: 0.016 },
    { g: "Chidawa", approval: 0.605, n: 259, delta: -0.007 },
    { g: "Hanumangarh", approval: 0.615, n: 248, delta: 0.003 },
    { g: "Nokha", approval: 0.598, n: 227, delta: -0.014 },
    { g: "Barmer Rural", approval: 0.612, n: 242, delta: 0.000 },
  ]},
];

export const models = [
  {
    version: "v1.0.0-logistic",
    type: "Logistic Scorecard",
    status: "active" as const,
    trained_at: "2026-09-03T10:52:56Z",
    n_train: 2400,
    n_val: 600,
    auc: 0.783,
    gini: 0.565,
    ks: 0.442,
    brier: 0.189,
    dataset: "synthetic_shg_generator",
    dataset_kind: "synthetic" as const,
    fairness_gate: "PASSED" as const,
  },
  {
    version: "v0.9.2-logistic",
    type: "Logistic Scorecard",
    status: "retired" as const,
    trained_at: "2026-08-14T09:12:00Z",
    n_train: 2000,
    n_val: 500,
    auc: 0.751,
    gini: 0.502,
    ks: 0.409,
    brier: 0.204,
    dataset: "synthetic_shg_generator",
    dataset_kind: "synthetic" as const,
    fairness_gate: "PASSED" as const,
  },
  {
    version: "v1.1.0-xgb-candidate",
    type: "XGBoost Challenger",
    status: "candidate" as const,
    trained_at: "2026-09-01T14:30:00Z",
    n_train: 2400,
    n_val: 600,
    auc: 0.812,
    gini: 0.624,
    ks: 0.478,
    brier: 0.171,
    dataset: "synthetic_shg_generator",
    dataset_kind: "synthetic" as const,
    fairness_gate: "PENDING" as const,
  },
];

export interface Grievance {
  id: string;
  borrower_name: string;
  village: string;
  category: "SCORE_DISPUTE" | "DATA_ACCURACY" | "CONSENT_ISSUE" | "OFFICER_CONDUCT" | "OTHER";
  status: "OPEN" | "IN_REVIEW" | "RESOLVED" | "ESCALATED";
  opened_at: string;
  sla_hours_remaining: number;
  summary: string;
  channel: "WEB" | "SAKHI" | "PHONE";
}

export const grievances: Grievance[] = [
  { id: "GRV-000241", borrower_name: "Kavita Devi", village: "Suratgarh", category: "SCORE_DISPUTE", status: "OPEN", opened_at: new Date(Date.now() - 4 * 3600_000).toISOString(), sla_hours_remaining: 44, summary: "Disputes low weight given to SHG history in the model output.", channel: "SAKHI" },
  { id: "GRV-000240", borrower_name: "Ramesh Kumar", village: "Nokha", category: "DATA_ACCURACY", status: "IN_REVIEW", opened_at: new Date(Date.now() - 18 * 3600_000).toISOString(), sla_hours_remaining: 30, summary: "Land parcel area recorded lower than DigiLocker record.", channel: "WEB" },
  { id: "GRV-000239", borrower_name: "Sunita Sharma", village: "Chidawa", category: "OFFICER_CONDUCT", status: "ESCALATED", opened_at: new Date(Date.now() - 40 * 3600_000).toISOString(), sla_hours_remaining: 8, summary: "Requests independent review of rejection with rationale.", channel: "PHONE" },
  { id: "GRV-000238", borrower_name: "Meena Bai", village: "Barmer Rural", category: "CONSENT_ISSUE", status: "RESOLVED", opened_at: new Date(Date.now() - 96 * 3600_000).toISOString(), sla_hours_remaining: 0, summary: "AA consent revocation processed and confirmed.", channel: "SAKHI" },
  { id: "GRV-000237", borrower_name: "Prakash Jat", village: "Hanumangarh", category: "SCORE_DISPUTE", status: "OPEN", opened_at: new Date(Date.now() - 8 * 3600_000).toISOString(), sla_hours_remaining: 40, summary: "Requests re-evaluation with updated rainfall data.", channel: "WEB" },
];

export const officerProfile = {
  id: "OFF-101",
  name: "Priya Nair",
  role: "Senior Loan Officer",
  branch: "Sri Ganganagar Regional Hub",
  avatar_initials: "PN",
};
