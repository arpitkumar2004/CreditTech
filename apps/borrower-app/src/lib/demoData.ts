/**
 * Demo data for pages that showcase borrower-facing views before the backend
 * is wired end-to-end. Deterministic so the UI looks production-ready in demo.
 */

export interface LoanApplication {
  id: string;
  purpose: string;
  amount: number;
  tenure_months: number;
  submitted_at: string;
  status: "APPROVED" | "PENDING" | "REJECTED" | "DISBURSED";
  score_900: number;
  band: "A" | "B" | "C" | "D";
  next_installment?: { date: string; amount: number };
}

export const borrowerApplications: LoanApplication[] = [
  { id: "LA-2026-03042", purpose: "Rabi seeds & fertiliser", amount: 32000, tenure_months: 12, submitted_at: "2026-08-24T09:15:00Z", status: "DISBURSED", score_900: 712, band: "B", next_installment: { date: "2026-09-24", amount: 2950 } },
  { id: "LA-2026-03018", purpose: "Dairy cattle purchase", amount: 55000, tenure_months: 24, submitted_at: "2026-07-11T11:20:00Z", status: "DISBURSED", score_900: 738, band: "A", next_installment: { date: "2026-09-11", amount: 2620 } },
  { id: "LA-2026-02890", purpose: "Kharif crop inputs", amount: 22500, tenure_months: 6, submitted_at: "2026-05-04T08:00:00Z", status: "APPROVED", score_900: 695, band: "B" },
  { id: "LA-2025-01247", purpose: "Micro-enterprise (tailoring)", amount: 18000, tenure_months: 12, submitted_at: "2025-11-14T13:45:00Z", status: "REJECTED", score_900: 588, band: "C" },
];

export interface BorrowerGrievance {
  id: string;
  category: string;
  status: "OPEN" | "IN_REVIEW" | "RESOLVED";
  opened_at: string;
  summary: string;
  officer_response?: string;
}

export const borrowerGrievances: BorrowerGrievance[] = [
  { id: "GRV-000188", category: "SCORE DISPUTE", status: "IN_REVIEW", opened_at: "2026-08-30T08:00:00Z", summary: "Requesting review — SHG history missing from earlier score.", officer_response: "Assigned to officer P. Nair · rescore scheduled." },
  { id: "GRV-000102", category: "CONSENT ISSUE", status: "RESOLVED", opened_at: "2026-06-18T10:00:00Z", summary: "AA consent revocation confirmation.", officer_response: "Confirmed · consent revoked with hash chain integrity preserved." },
];

export const borrowerProfile = {
  name: "Kavita Devi",
  village: "Suratgarh",
  district: "Sri Ganganagar",
  state: "Rajasthan",
  member_since: "2025-04-10",
  shg_group: "Meera Mahila Samuh",
  latest_score: 712,
  latest_band: "B" as const,
};
