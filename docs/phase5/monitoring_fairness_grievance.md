# Phase 5 — Fairness batch · Grievance/Appeal · Institutional Dashboard · Score Report

**Status:** Implemented — 2026-09-03
**Entry gate:** P4 complete; `OfficerDecisionLog` populated with `is_override`, `officer_id`, and model/feature versions per P4.

Pilot flow this phase closes:

> officer decisions → weekly fairness batch (descriptive stats) → institutional dashboard → grievance / appeal with SLA clock → branded score report

## 1. Scope

| In | Out |
|----|-----|
| Weekly fairness batch (approval-rate parity + officer override-rate) across GENDER / GEOGRAPHY / LANDHOLDING / OFFICER | Real-time fairness alerting (out — sample sizes too small at pilot scale, §17.2) |
| Insufficient-sample handling — rows persisted with `status='INSUFFICIENT_SAMPLE'` and `approval_rate=NULL` | Auto-promote/demote model based on fairness metrics (external auditor gate — P6/§8.3) |
| Fairness CSV export for the external auditor | Ratified parity thresholds (governance decision — pending ratification, marked `PENDING_GOVERNANCE`) |
| Grievance / appeal channel with SLA clock, status transitions, escalation, append-only audit | SMS/IVR intake channels (P6 field-ops) |
| Institutional dashboard: portfolio metrics, fairness view, grievance count | Self-serve BI (out — small internal dashboard only, §7.2) |
| Branded HTML score-report endpoint | PDF rendering (out — HTML is sufficient for the pilot handoff; PDF is a P6 polish item) |

## 2. Code layout

```
services/core/monitoring/
    service.py       # FairnessAuditor (4 dimensions + INSUFFICIENT_SAMPLE + CSV export)
    router.py        # POST fairness-audit, GET list, GET export.csv, POST retention-purge

services/core/grievance/
    __init__.py
    schemas.py       # GrievanceCreate/Update/Record + ALLOWED_TRANSITIONS
    service.py       # SLA clock, transitions, auto-escalate, append-only audit
    router.py        # /grievances CRUD + audit + escalate-overdue

services/core/dashboard/
    __init__.py
    service.py       # portfolio metrics, fairness view, branded score-report HTML
    router.py        # /dashboard/portfolio, /dashboard/fairness, /dashboard/fairness/export.csv,
                     # /report/score/{score_id}

services/core/shared/models.py
    FairnessAuditLog # + status column, nullable approval_rate/override_rate
    Grievance        # + GrievanceAuditLog (append-only)
```

## 3. Fairness batch — design and invariants

`FairnessAuditor.run_audit(period)` computes, per dimension, per group:

- `sample_size` — count of distinct `LoanApplication` rows (or `OfficerDecisionLog` rows for OFFICER)
- `approval_rate` = approved / total (or `NULL` when below `MIN_SAMPLE_SIZE`)
- `override_rate` = # overrides / total, where **overrides come from `OfficerDecisionLog.is_override`** (not the free-text `override_reason` on `LoanApplication`, which is populated by unrelated flows).

Small-sample guard: `MIN_SAMPLE_SIZE = 30` (pilot). Groups below the threshold are persisted with `status='INSUFFICIENT_SAMPLE'` and `NULL` rates so downstream dashboards can show the group's existence without over-claiming a fairness signal. This addresses §17.2 (small buckets, don't over-alert) directly.

Governance stance: the auditor computes **descriptive statistics only**. It does not invent parity thresholds. Where governance thresholds have not been ratified by the external fairness auditor (§8.3), row status is `PENDING_GOVERNANCE`. The pilot's day-1 posture is `OK` / `INSUFFICIENT_SAMPLE` only; `PENDING_GOVERNANCE` is reserved for the auditor's ratified thresholds when they arrive.

### API

| Method | Path | Purpose |
|-|-|-|
| `POST` | `/api/v1/monitoring/fairness-audit?period=2026-W35` | Run the batch for a period |
| `GET`  | `/api/v1/monitoring/fairness-audit?period=&dimension=` | List rows (officer-auth) |
| `GET`  | `/api/v1/monitoring/fairness-audit/export.csv?period=` | CSV export for auditor |
| `GET`  | `/api/v1/dashboard/fairness?period=` | Latest-period fairness view (JSON) |
| `GET`  | `/api/v1/dashboard/fairness/export.csv?period=` | Same CSV, dashboard route |

## 4. Grievance / appeal channel

`Grievance` is borrower-scoped and category-tagged (`SCORE_DISPUTE`, `DECISION_APPEAL`, `DATA_ACCURACY`, `CONSENT_ISSUE`, `OTHER`).

**SLA clock:** starts at creation; `due_at = created_at + sla_hours` (default 168h = 7 days). `is_overdue` is computed from `now() > due_at` and only when status is not `RESOLVED` / `CLOSED`.

**State machine:**

```
OPEN ─────────┬─▶ IN_REVIEW ────┬─▶ RESOLVED ─▶ CLOSED
              ├─▶ ESCALATED ────┤
              └─▶ RESOLVED      │
                                └─▶ ESCALATED
```

Terminal states: `RESOLVED`, `CLOSED`. Invalid transitions return 400. Every transition inserts a `GrievanceAuditLog` row (append-only). `POST /escalate-overdue` bulk-transitions overdue `OPEN`/`IN_REVIEW` grievances to `ESCALATED` for RBI Fair Practices Code compliance.

### API

| Method | Path | Auth | Purpose |
|-|-|-|-|
| `POST`   | `/api/v1/grievances/` | `X-Borrower-Id` (must match body) | Create grievance, start SLA |
| `GET`    | `/api/v1/grievances/{id}` | borrower (own id) OR officer | Fetch grievance |
| `GET`    | `/api/v1/grievances/?status=&overdue_only=` | officer | List / filter |
| `PATCH`  | `/api/v1/grievances/{id}` | officer | Update status / notes |
| `GET`    | `/api/v1/grievances/{id}/audit` | officer | Immutable audit trail |
| `POST`   | `/api/v1/grievances/escalate-overdue` | officer / system | Auto-escalate past SLA |

## 5. Institutional dashboard

Aggregate, non-PII metrics for partner RE management and NABARD stakeholders (§17.2). No borrower-level fields exposed here.

- `GET /api/v1/dashboard/portfolio` — borrowers, scores, applications by decision, approval rate, disbursed amount (approved), officer decision count, override count + rate, open grievances.
- `GET /api/v1/dashboard/fairness` — latest fairness period rows + `governance_note`.
- `GET /api/v1/dashboard/fairness/export.csv` — CSV for the auditor.

## 6. Branded score report

`GET /api/v1/report/score/{score_id}?partner_re_id=...` — self-contained HTML with:

- CreditTech branding header
- Non-PII borrower summary (gender / age band / landholding / village / district / state)
- Score, 900-scale calibration, band, confidence interval
- Model + feature versions, model recommendation (from P4 band mapping)
- Bilingual reason codes (EN + HI)
- Latest officer decision block (decision, officer, override flag, reason)
- Footer stating that the loan officer remains the final decision-maker (§ADR-1)

HTML output is escaped at every dynamic insertion point. PDF conversion is a P6 polish item; the RE contract already accepts the JSON handoff (P0 §3.1) and this HTML supplement, so PDF is not on the P5 critical path.

## 7. Tests

Backend suite: **83 / 83 pass** — 65 pre-P5 + 18 new:

- `tests/test_p5_fairness.py` (5): all-4-dimensions computed; insufficient sample → NULL rates + status; override rate uses `OfficerDecisionLog.is_override`; CSV export; auth guard.
- `tests/test_p5_grievance.py` (7): creation starts SLA clock; missing borrower header → 401; mismatched header → 403; status transitions + audit trail + invalid-transition → 400; overdue detection + auto-escalate; list requires officer auth; borrower reads own grievance only.
- `tests/test_p5_dashboard.py` (5): portfolio metrics; auth guard; fairness view; score report renders (with reason codes + officer decision); 404 for unknown score.
- `tests/test_p5_e2e.py` (1): application → score → officer decision → fairness batch → dashboard → borrower grievance → officer resolves → dashboard + report reflect final state.

## 8. Limitations / P6 follow-ups

- Officer auth is header-based; SSO/OIDC + fine-grained RBAC (per-partner-RE scoping) is P6.
- Borrower auth for grievance intake is header-based (`X-Borrower-Id`); production replaces with the borrower app's session token.
- `GrievanceAuditLog` and `OfficerDecisionLog` append-only invariants are enforced at the application layer; DB triggers/rules are P6 hardening.
- Score-report HTML only; PDF renderer deferred.
- Fairness thresholds are unratified pilot-defaults; the external auditor's ratified thresholds land in P6 alongside the model-promotion gate.
- Institutional dashboard is JSON/CSV endpoints only; a UI front-end (React panel in the unified `apps/borrower-app` portal) is deferred to the post-P5 field polish.
