# CreditTech Data Access & Permissions Matrix

This matrix governs all API endpoints, resources, and state transitions in CreditTech, serving as the source of truth for automated authorization testing.

---

## 1. Resource × Persona Permissions Matrix

Legend:
- `✅ ALLOWED`: Permitted action
- `❌ FORBIDDEN`: Blocked with `403 Forbidden` or `401 Unauthorized`
- `👁️ VIEW_ONLY`: Read-only access
- `OWN`: Restricted strictly to records matching caller's identity (`X-Borrower-Id`)

| Resource / Endpoint | `GUEST` | `BORROWER` | `BANK_SAKHI` | `LOAN_OFFICER` | `RISK_OFFICER` | `ADMIN` / `ML` | `RE_PARTNER` |
|---|---|---|---|---|---|---|---|
| **System Probes** (`/health`, `/ready`) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **API Docs** (`/docs`, `/openapi.json`) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Consent Create** (`POST /api/v1/consent/`) | ❌ | OWN | ✅ (Assisted) | ❌ | ❌ | ❌ | ❌ |
| **Consent Lookup** (`GET /api/v1/consent/{id}`) | ❌ | OWN | ✅ | ✅ | 👁️ | 👁️ | 👁️ |
| **Consent Revoke** (`POST /api/v1/consent/{id}/revoke`)| ❌ | OWN | ❌ | ❌ | ❌ | ❌ | ❌ |
| **SHG Profile Ingest** (`POST /api/v1/ingest/shg-fpo`) | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ | ❌ |
| **Trigger 4-Rail Ingest** (`POST /api/v1/ingest/trigger`) | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ | ❌ |
| **Generate Score** (`POST /api/v1/score/`) | ❌ | ❌ | ✅ (Trigger) | ✅ | ❌ | ✅ | ❌ |
| **View Score & Reasons** (`GET /api/v1/score/{id}`) | ❌ | OWN | 👁️ | ✅ | 👁️ | 👁️ | 👁️ |
| **Officer Decision** (`POST /api/v1/decisions/`) | ❌ | ❌ | ❌ | ✅ (Approve/Reject)| ❌ | ❌ | ❌ |
| **RE Loan Handoff** (`POST /api/v1/handoff/{app_id}`) | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ (Fetch) |
| **Open Grievance** (`POST /api/v1/grievances/`) | ❌ | OWN | ✅ (Assisted) | ❌ | ❌ | ❌ | ❌ |
| **Triage Grievance** (`PATCH /api/v1/grievances/{id}`) | ❌ | ❌ | ❌ | ✅ (Update SLA) | ❌ | ✅ | ❌ |
| **Portfolio Metrics** (`GET /api/v1/dashboard/portfolio`) | ❌ | ❌ | ❌ | 👁️ | 👁️ | 👁️ | 👁️ |
| **Fairness Audit** (`GET /api/v1/dashboard/fairness`) | ❌ | ❌ | ❌ | 👁️ | ✅ | ✅ | 👁️ |
| **Auditor CSV Export** (`GET .../fairness/export.csv`) | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| **List Models** (`GET /api/v1/admin/models`) | ❌ | ❌ | ❌ | 👁️ | 👁️ | ✅ | ❌ |
| **Fairness Manifest** (`GET /api/v1/admin/fairness/manifest`)| ❌ | ❌ | ❌ | 👁️ | 👁️ | ✅ | ❌ |
| **Fairness Gate Dry-Run** (`GET /api/v1/admin/fairness/gate`)| ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ |
| **Model Promotion** (`POST /api/v1/admin/models/{v}/promote`)| ❌ | ❌ | ❌ | ❌ (403) | ❌ (403) | ✅ (Gated) | ❌ |
| **Integration Smoke Tests** (`POST /api/v1/ops/smoke/...`)| ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |

---

## 2. Horizontal Privilege Tripwires

```text
Borrower A (Radhika) ───[ GET /score/{Score_B} ]───► 403 Forbidden ❌
Borrower A (Radhika) ───[ GET /grievances/{Grv_B} ]─► 401/403 Forbidden ❌
Borrower A (Radhika) ───[ POST /consent/revoke (Consent_B) ]─► 403 Forbidden ❌
```

## 3. Vertical Privilege Tripwires

```text
Loan Officer (Rajesh) ───[ POST /admin/models/promote ]───► 403 Forbidden ❌
Bank Sakhi (Sunita)   ───[ POST /decisions/ ]─────────────► 401/403 Forbidden ❌
Borrower (Radhika)    ───[ POST /admin/models/promote ]───► 401 Unauthorized ❌
Borrower (Radhika)    ───[ GET /admin/models ]────────────► 401 Unauthorized ❌
```

## 4. State & Business Tripwires

| State / Condition | Action Attempted | Expected System Verdict |
|---|---|---|
| Revoked Consent | Score generation | ❌ `400 Bad Request` (Consent not active) |
| Expired Consent | Feature aggregation | ❌ `400 Bad Request` (Consent expired) |
| Already Decided Application | Duplicate decision submission | ❌ `409 Conflict` (Application already finalized) |
| Settled Grievance | Modifying resolution notes | ❌ `400 Bad Request` (Grievance already closed) |
| Immutable Audit Log | Direct DB UPDATE / DELETE | ❌ `Database Trigger Exception` (Table is append-only) |
| Model Failing Fairness Gate | Admin promote attempt | ❌ `409 Conflict` (Promotion blocked by fairness gate) |
