/**
 * Thin API client for the CreditTech FastAPI backend.
 * Vite dev server proxies /api to http://localhost:8000 (see vite.config.ts).
 */

const BASE = import.meta.env.VITE_API_BASE ?? "/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { "content-type": "application/json", ...(init?.headers ?? {}) },
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
