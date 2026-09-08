/**
 * Thin API client for the CreditTech FastAPI backend.
 * Vite dev server proxies /api to http://localhost:8000 (see vite.config.ts).
 */

const BASE = import.meta.env.VITE_API_BASE ?? "/api/v1";

// ── Persona & Role Management (Reproducible Test Environment) ────
export interface DevPersona {
  key: string;
  id: string;
  name: string;
  role: "LOAN_OFFICER" | "BANK_SAKHI" | "BORROWER" | "RISK_OFFICER" | "ADMIN";
  branchOrVillage: string;
  description: string;
  borrowerId?: string;
}

export const DEV_PERSONAS: Record<string, DevPersona> = {
  OFFICER_RAJESH: {
    key: "OFFICER_RAJESH",
    id: "OFF-001",
    name: "Rajesh Kumar",
    role: "LOAN_OFFICER",
    branchOrVillage: "Chandauli Rural (Cluster Alpha)",
    description: "Branch Loan Officer · Underwriting & Decisions",
  },
  OFFICER_VIKRAM: {
    key: "OFFICER_VIKRAM",
    id: "OFF-002",
    name: "Vikram Singh",
    role: "LOAN_OFFICER",
    branchOrVillage: "Mirzapur Hill (Cluster Beta)",
    description: "Branch Loan Officer · Rain-fed Farm Underwriting",
  },
  SAKHI_SUNITA: {
    key: "SAKHI_SUNITA",
    id: "SAKHI-001",
    name: "Sunita Devi",
    role: "BANK_SAKHI",
    branchOrVillage: "Tara Jivanpur Village",
    description: "Bank Sakhi · Assisted Onboarding & SHG Entry",
  },
  BORROWER_RADHIKA: {
    key: "BORROWER_RADHIKA",
    id: "BORR-RADHIKA",
    name: "Radhika Devi",
    role: "BORROWER",
    branchOrVillage: "Tara Jivanpur (Approved · Dairy)",
    description: "Borrower · Dairy Expansion · Approved ₹50,000",
    borrowerId: "00000000-0000-0000-0002-000000000001",
  },
  BORROWER_SITA: {
    key: "BORROWER_SITA",
    id: "BORR-SITA",
    name: "Sita Kumari",
    role: "BORROWER",
    branchOrVillage: "Chandauli (Under Review · Crop)",
    description: "Borrower · Micro Crop Loan · Under Review ₹35,000",
    borrowerId: "00000000-0000-0000-0002-000000000002",
  },
  BORROWER_RAMU: {
    key: "BORROWER_RAMU",
    id: "BORR-RAMU",
    name: "Ramu Patel",
    role: "BORROWER",
    branchOrVillage: "Barmer (Actionable Recourse)",
    description: "Borrower · Tract Equipment · Action Plan ₹80,000",
    borrowerId: "00000000-0000-0000-0002-000000000003",
  },
  BORROWER_MEENA: {
    key: "BORROWER_MEENA",
    id: "BORR-MEENA",
    name: "Meena Verma",
    role: "BORROWER",
    branchOrVillage: "Mirzapur Hills (Live Dispute)",
    description: "Borrower · Live Grievance & SLA Escalation",
    borrowerId: "00000000-0000-0000-0002-000000000004",
  },
  SAKHI_MANJU: {
    key: "SAKHI_MANJU",
    id: "SAKHI-003",
    name: "Manju Kanwar",
    role: "BANK_SAKHI",
    branchOrVillage: "Sri Ganganagar Canal Zone",
    description: "Bank Sakhi · Assisted Onboarding & Field Surveys",
  },
  RISK_PRIYA: {
    key: "RISK_PRIYA",
    id: "RISK-001",
    name: "Priya Sharma",
    role: "RISK_OFFICER",
    branchOrVillage: "Head Office Risk Division",
    description: "Credit Risk Officer · Fairness & Disparity Audits",
  },
  ADMIN_AMIT: {
    key: "ADMIN_AMIT",
    id: "ADMIN-001",
    name: "Amit Verma",
    role: "ADMIN",
    branchOrVillage: "MLOps & Systems",
    description: "System Admin · Model Promotion & Registry",
  },
};

export function getActivePersona(): DevPersona {
  if (typeof window === "undefined") return DEV_PERSONAS.OFFICER_RAJESH;
  const stored = localStorage.getItem("credittech_dev_persona");
  if (stored && DEV_PERSONAS[stored]) {
    return DEV_PERSONAS[stored];
  }
  return DEV_PERSONAS.OFFICER_RAJESH;
}

export function setActivePersona(personaKey: string): void {
  if (DEV_PERSONAS[personaKey]) {
    localStorage.setItem("credittech_dev_persona", personaKey);
    window.dispatchEvent(
      new CustomEvent("credittech_persona_changed", {
        detail: DEV_PERSONAS[personaKey],
      })
    );
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const persona = getActivePersona();
  const authHeaders: Record<string, string> = {
    "content-type": "application/json",
  };

  if (persona.role === "BORROWER") {
    if (persona.borrowerId) {
      authHeaders["X-Borrower-Id"] = persona.borrowerId;
    }
  } else {
    authHeaders["X-Officer-Id"] = persona.id;
    authHeaders["X-Officer-Role"] = persona.role;
  }

  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      ...authHeaders,
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status}: ${body || res.statusText}`);
  }
  return res.json() as Promise<T>;
}


// ── Consent ────────────────────────────────────────────
export interface ConsentSummary {
  id: string;
  borrower_id: string;
  purpose: string;
  status: string;
  data_sources: string[];
  issued_at: string;
  expires_at: string;
}

export const consentApi = {
  get: (id: string) => request<ConsentSummary>(`/consent/${id}`),
  forBorrower: (borrowerId: string) =>
    request<ConsentSummary[]>(`/consent/borrower/${borrowerId}`),
  verify: (id: string) => request<{ valid: boolean; reason?: string }>(`/consent/${id}/verify`),
};

// ── SHG/FPO manual ingestion (Bank Sakhi entry) ────────
export interface SakhiEntryPayload {
  borrower_id: string;
  shg_data: {
    shg_name: string;
    nabard_grade: "A" | "B" | "C" | "D";
    membership_years: number;
    monthly_savings: number;
    total_savings: number;
    loans_taken: number;
    loans_repaid: number;
    meeting_attendance_pct: number;
  };
  farmer_data: {
    land_holding_acres: number;
    land_ownership: "OWN" | "LEASE" | "SHARE_CROP";
    irrigation_access: boolean;
    crop_type_primary: string;
    estimated_monthly_income: number;
  };
  created_by: string;
}

export const ingestApi = {
  submitSakhiEntry: (payload: SakhiEntryPayload) =>
    request<{ status: string }>(`/ingest/shg-fpo`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  triggerAggregation: (borrowerId: string) =>
    request<{ overall_status: string; feature_snapshot_id: string | null; sources: unknown[] }>(
      `/ingest/trigger`,
      {
        method: "POST",
        body: JSON.stringify({
          borrower_id: borrowerId,
          purpose: "credit_scoring",
          data_sources: ["AA", "GEOSPATIAL", "BUREAU"],
        }),
      }
    ),
};

// ── Applications & Officer Decisioning ─────────────────
export interface ApiApplication {
  id: string;
  borrower_id: string;
  borrower_name: string;
  village: string;
  district: string;
  state: string;
  gender: string;
  age: number;
  landholding_band: string;
  requested_amount: number;
  requested_tenure_months: number;
  purpose: string;
  score_id: string;
  score_900: number;
  score_100: number;
  band: string;
  confidence_lower: number;
  confidence_upper: number;
  model_recommendation: "APPROVE" | "REVIEW" | "REJECT";
  decision: "PENDING" | "APPROVED" | "REJECTED" | "MORE_INFO_REQUIRED";
  override_reason: string | null;
  submitted_at: string;
  decided_at: string | null;
}

export interface ReviewPayload {
  score_id: string;
  borrower_id?: string;
  borrower_name?: string | null;
  borrower?: {
    id: string;
    gender: string;
    age: number;
    landholding_band: string;
    village: string | null;
    district: string | null;
    state: string | null;
  };
  borrower_summary?: {
    borrower_id: string;
    borrower_name?: string | null;
    gender: string;
    age: number;
    landholding_band: string;
    village: string | null;
    district: string | null;
    state: string | null;
    language?: string;
    application_id?: string;
    requested_amount?: number;
    requested_tenure_months?: number;
    purpose?: string;
  };
  score?: number;
  score_900?: number;
  score_band?: string;
  confidence_lower?: number;
  confidence_upper?: number;
  credit_assessment?: {
    score: number;
    score_900: number;
    score_band: string;
    model_version: string;
    feature_version: string;
    model_recommendation: "APPROVE" | "REVIEW" | "REJECT";
  };
  model_version?: string;
  feature_version?: string;
  model_recommendation?: "APPROVE" | "REVIEW" | "REJECT";
  sources_used?: string[];
  sources_status?: { source: string; available: boolean }[];
  source_status?: { source: string; available: boolean }[];
  partial_data: boolean;
  reason_codes: {
    rank: number;
    feature_name: string;
    direction: string;
    shap_value: number;
    localized_text_en: string;
    localized_text_hi: string | null;
  }[];
  features?: Record<string, any>;
  generated_at?: string;
  existing_decision?: {
    id?: string;
    decision: string;
    is_override: boolean;
    override_reason: string | null;
    officer_id: string;
    created_at: string;
  } | null;
}

export const applicationsApi = {
  list: () => request<ApiApplication[]>("/decision/applications"),
  get: (id: string) => request<ReviewPayload>(`/decision/applications/${id}`),
};

export const decisionApi = {
  listApplications: () => request<ApiApplication[]>("/decision/applications"),
  getReview: (scoreId: string) => request<ReviewPayload>(`/decision/review/${scoreId}`),
  record: (payload: {
    score_id: string;
    decision: "APPROVED" | "REJECTED" | "MORE_INFO_REQUIRED";
    override_reason?: string | null;
    officer_notes?: string | null;
  }) =>
    request<{
      id: string;
      score_id: string;
      officer_id: string;
      decision: string;
      model_recommendation: string;
      is_override: boolean;
      override_reason: string | null;
      created_at: string;
    }>("/decision/", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  recordDecision: (payload: {
    score_id: string;
    decision: "APPROVED" | "REJECTED" | "MORE_INFO_REQUIRED";
    override_reason?: string | null;
    officer_notes?: string | null;
    notes?: string | null;
  }) =>
    request<{
      id: string;
      score_id: string;
      officer_id: string;
      decision: string;
      model_recommendation: string;
      is_override: boolean;
      override_reason: string | null;
      created_at: string;
    }>("/decision/", {
      method: "POST",
      body: JSON.stringify({
        score_id: payload.score_id,
        decision: payload.decision,
        override_reason: payload.override_reason,
        officer_notes: payload.officer_notes ?? payload.notes,
      }),
    }),
  getAudit: (scoreId: string) => request<unknown[]>(`/decision/audit/${scoreId}`),
};

// ── Dashboard & Governance ─────────────────────────────
export interface PortfolioMetrics {
  borrowers: number;
  scores_generated: number;
  applications_total: number;
  applications_pending: number;
  applications_approved: number;
  applications_rejected: number;
  applications_more_info: number;
  approval_rate: number | null;
  disbursed_amount_approved: number;
  officer_decisions_total: number;
  officer_override_count: number;
  officer_override_rate: number | null;
  grievances_open: number;
}

export const dashboardApi = {
  portfolio: () => request<PortfolioMetrics>("/dashboard/portfolio"),
  fairness: (period?: string) =>
    request<{
      period: string | null;
      rows: {
        id?: string;
        period?: string;
        dimension: string;
        group_value: string;
        approval_rate: number | null;
        sample_size?: number;
        override_rate?: number | null;
        total_applications?: number;
        approved_applications?: number;
        threshold_value?: number;
        breach_detected?: boolean;
        status?: string;
        audited_at?: string;
        computed_at?: string;
      }[];
      governance_note?: string;
    }>(period ? `/dashboard/fairness?period=${period}` : "/dashboard/fairness"),
};

// ── Model Registry & Governance ────────────────────────
export interface RegisteredModel {
  model_version: string;
  feature_version: string;
  model_type: string;
  trained_at: string;
  promotion_status: "candidate" | "validated" | "active" | "retired";
  metrics: {
    auc: number;
    gini: number;
    ks: number;
    brier: number;
  };
  limitations?: string[];
  fairness?: { results?: unknown[] };
}

export const modelsApi = {
  list: () => request<RegisteredModel[]>("/admin/models"),
  listModels: () => request<RegisteredModel[]>("/admin/models"),
  manifest: () =>
    request<{ manifest_hash: string; manifest: { version: string; dimensions: Record<string, unknown> }; thresholds?: Record<string, any>; version?: string }>(
      "/admin/fairness/manifest"
    ),
  getManifest: () =>
    request<{ manifest_hash?: string; manifest?: { version: string; dimensions: Record<string, unknown> }; thresholds?: Record<string, any>; version?: string }>(
      "/admin/fairness/manifest"
    ),
  fairnessGate: (period?: string) =>
    request<{ passed: boolean; manifest_hash: string; breaches: unknown[]; checked_period: string }>(
      period ? `/admin/fairness/gate?period=${period}` : "/admin/fairness/gate"
    ),
  evaluateGate: (period?: string) =>
    request<{ passed: boolean; manifest_hash: string; breaches: unknown[]; checked_period: string }>(
      period ? `/admin/fairness/gate?period=${period}` : "/admin/fairness/gate"
    ),
  promote: (version: string) =>
    request<{ promoted: boolean; report: unknown }>(`/admin/models/${version}/promote`, {
      method: "POST",
    }),
  check: (version: string) =>
    request<unknown>(`/admin/models/${version}/promotion-check`),
};
export const adminApi = modelsApi;

// ── Grievances ─────────────────────────────────────────
export interface ApiGrievance {
  id: string;
  borrower_id: string;
  category: "INTEREST_RATE" | "REJECTED_LOAN" | "DATA_ACCURACY" | "CONSENT_BREACH" | "OTHER" | string;
  description?: string;
  summary?: string;
  status: "OPEN" | "IN_REVIEW" | "ESCALATED" | "RESOLVED" | "CLOSED" | string;
  due_at?: string;
  sla_deadline?: string;
  resolution_notes?: string | null;
  created_at: string;
}

export const grievancesApi = {
  list: (status?: string) => request<ApiGrievance[]>(status ? `/grievances/?status=${status}` : "/grievances/"),
  get: (id: string) => request<ApiGrievance>(`/grievances/${id}`),
  create: (payload: {
    borrower_id: string;
    category: string;
    description?: string;
    summary?: string;
    score_id?: string | null;
    loan_application_id?: string | null;
  }) =>
    request<ApiGrievance>("/grievances/", {
      method: "POST",
      headers: { "X-Borrower-Id": payload.borrower_id },
      body: JSON.stringify({
        borrower_id: payload.borrower_id,
        category: payload.category,
        description: payload.description || payload.summary || "Grievance dispute",
        score_id: payload.score_id,
        loan_application_id: payload.loan_application_id,
      }),
    }),
  update: (
    id: string,
    payload: {
      status?: string;
      resolution_notes?: string;
      note?: string;
      notes?: string;
    }
  ) =>
    request<ApiGrievance>(`/grievances/${id}`, {
      method: "PATCH",
      body: JSON.stringify({
        status: payload.status,
        resolution_notes: payload.resolution_notes,
        note: payload.note || payload.notes,
      }),
    }),
  audit: (id: string) => request<unknown[]>(`/grievances/${id}/audit`),
  escalateOverdue: () => request<{ escalated: number }>("/grievances/escalate-overdue", { method: "POST" }),
};
export const grievanceApi = grievancesApi;

// ── Partner RE Handoff ─────────────────────────────────
export const handoffApi = {
  submit: (
    payloadOrScoreId: string | {
      score_id: string;
      partner_re_id: string;
      requested_amount: number;
      requested_tenure_months: number;
      purpose: string;
    },
    optionalPayload?: {
      partner_re_id?: string;
      requested_amount?: number;
      requested_tenure_months?: number;
      purpose?: string;
    }
  ) => {
    const body = typeof payloadOrScoreId === "string"
      ? { score_id: payloadOrScoreId, ...optionalPayload }
      : payloadOrScoreId;
    return request<{
      loan_application_id: string;
      status: string;
      message: string;
    }>("/handoff/submit", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },
};

// ── Persona Decision Charts & Validation Dossier ─────────
export interface PersonaChartsParams {
  persona?: "admin" | "officer" | "borrower" | "risk_officer" | "bank_sakhi";
  modelVersion?: string;
  borrowerId?: string;
}

export const chartsApi = {
  getCharts: (params?: PersonaChartsParams) => {
    const q = new URLSearchParams();
    if (params?.persona) q.set("persona", params.persona);
    if (params?.modelVersion) q.set("model_version", params.modelVersion);
    if (params?.borrowerId) q.set("borrower_id", params.borrowerId);
    const qs = q.toString();
    return request<any>(`/dashboard/charts${qs ? `?${qs}` : ""}`);
  },
};


