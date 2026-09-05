# Phase 4 — Loan Officer Decision Interface

**Status:** Implemented — 2026-09-03
**Entry gate:** Phase 3 complete; RE API/handoff contract spec (`docs/phase0/re_api_handoff_spec.md`) in hand.

Pilot flow this phase closes:

> application → score → confidence → reason codes → supporting evidence → loan officer review → Approve / Reject / More-info → decision + override reason logged → RE handoff

## 1. Scope

| In | Out |
|----|-----|
| Officer review pack API | Officer SSO / OIDC (deferred to P6 hardening) |
| Approve / Reject / More-info decision capture | Auto-decisioning (never — human-in-the-loop is the regulatory control point, ADR-1 & §4) |
| Mandatory override reason when officer disagrees with the model | Bulk decisioning UI |
| Immutable `OfficerDecisionLog` audit trail | Grievance / appeal channel (P5 §31) |
| RE handoff gate + idempotency + payload alignment to P0 contract | Full RE OAuth 2.0 + mTLS wiring (pilot uses signed dev transport; production pinning is P6) |
| Officer web dashboard (React + Vite) | Institutional dashboard (P5) |

## 2. Code layout

```
services/core/decisioning/
    __init__.py
    auth.py          # X-Officer-Id / X-Officer-Role guard
    schemas.py       # DecisionRequest, ReviewPayload, OfficerDecisionRecord
    service.py       # DecisioningService — recommendation, is_override, audit
    router.py        # GET /review/{score_id}, POST /, GET /audit/{score_id}

services/core/handoff/service.py      # decision-gated + idempotent submission
services/core/shared/models.py        # OfficerDecisionLog (append-only)

apps/borrower-app/ (unified portal — officer routes)               # React + Vite UI (borrower app remains separate)
    src/App.tsx
    src/components/{ReviewPanel,DecisionForm,HandoffForm}.tsx
    src/api.ts
    src/decisionLogic.ts              # mirrors backend `is_override`
    src/test/*.test.{ts,tsx}          # vitest coverage of logic + rendering
```

## 3. API contract (backend)

All routes below require the `X-Officer-Id` and `X-Officer-Role` headers. Missing/invalid → 401.

### `GET /api/v1/decision/review/{score_id}`

Returns `ReviewPayload`:

- borrower summary (non-PII: gender, age, landholding band, village, district, state, language)
- `score`, `score_900`, `score_band`, `confidence_lower/upper`
- `model_version`, `feature_version`
- `model_recommendation` — derived from score band per the P0 RE contract's band mapping:
    - `EXCELLENT` / `GOOD` → `APPROVE`
    - `MODERATE` → `REVIEW` (officer discretion; no override concept applies)
    - `HIGH_RISK` / `VERY_HIGH_RISK` → `REJECT`
- `sources_used`, `source_status` (per-rail available/missing across AA/GEOSPATIAL/SHG_FPO/BUREAU), `partial_data` flag
- `reason_codes` (bilingual EN/HI, deterministic order)
- `existing_decision` — latest `OfficerDecisionLog` row for the score, if any

### `POST /api/v1/decision/`

Body: `{score_id, decision, override_reason?, officer_notes?}`

Rules enforced server-side:

- If the officer's decision differs from `model_recommendation`, `override_reason` is required. Missing → 400.
- If the officer agrees with the model, `override_reason` must be absent. Present → 400 (prevents drift from real overrides being drowned out).
- `REVIEW` recommendations never count as an override (the model didn't recommend a specific action).
- Invalid decision values → 422 (Pydantic).

Successful call inserts a new `OfficerDecisionLog` row and mirrors the decision onto `LoanApplication.officer_decision` when a loan application already exists.

### `GET /api/v1/decision/audit/{score_id}`

Returns the append-only chronological audit trail — every decision ever recorded for that score, oldest first. Rows are never updated in place; an amended decision is a new row.

## 4. RE handoff — decision gate + idempotency

`services/core/handoff/service.HandoffService.submit_application` now:

1. Looks up `(score_id, partner_re_id)`. If a `LoanApplication` exists, the same row is returned (idempotent, no duplicate transmit). The router surfaces `status="ALREADY_SUBMITTED"`.
2. Requires an `OfficerDecisionLog` row for the score. Missing → 400 (no officer decision recorded).
3. Requires that the latest decision is `APPROVED`. `REJECTED` / `MORE_INFO_REQUIRED` → 400.
4. Assembles the RE payload per `docs/phase0/re_api_handoff_spec.md §3.1`, including:
   - `credit_assessment.score_band`, `confidence_band`, `model_version`, `feature_version`, `sources_used`, `sources_unavailable`
   - `officer_decision` block: decision, officer_id, decided_at, model_recommendation, is_override, override_reason
5. Signs the payload with `RequestSigner` (HMAC-SHA256) and posts to the mock RE receiver in dev. Any network failure surfaces via graceful fallback with a synthesised `RE-` id (kept from Phase 2 — replaced by real OAuth 2.0 + mTLS in P6).

## 5. Audit trail

`OfficerDecisionLog` fields:

| Field | Purpose |
|-------|---------|
| `officer_id`, `decision`, `created_at` | Who / what / when |
| `model_recommendation`, `is_override`, `override_reason` | Governance & fairness monitor input |
| `model_score_at_decision`, `model_version_at_decision`, `feature_version_at_decision` | Anchors the decision to the exact model + feature contract in use at review time, so a later model swap does not silently rewrite history |
| `officer_notes` | Optional free-text for the officer's own record |
| `loan_application_id` (nullable FK) | Populated when a loan application already exists |

Rows are **append-only**. Amending a decision inserts a new row; earlier rows remain visible via `GET /decision/audit/{score_id}`. This is enforced by convention (no update endpoint) rather than DB triggers; the tighter enforcement is queued for the P6 security review.

## 6. Officer web UI

`apps/borrower-app/ (unified portal — officer routes)` — Vite + React + TypeScript, no external UI framework beyond React. Runs on port 5173, proxies `/api` to the FastAPI backend on `:8000`.

Screens (single page):

1. Lookup form (officer id + score id).
2. `ReviewPanel` — borrower summary, score card, versions, model recommendation, per-rail source status with a `⚠ Partial data` banner when any rail is missing, top reason codes (EN + HI).
3. `DecisionForm` — three radio options; conditional override-reason textarea; client-side validation mirrors the backend's `is_override` rule so the officer sees the constraint before submitting.
4. If a decision already exists for that score, the form is replaced by an "on record" panel — the officer must open the audit trail to see the history and cannot silently overwrite it.
5. `HandoffForm` — only rendered after an `APPROVED` decision. Fields for partner RE id, amount, tenure, purpose.

Vitest coverage:

- `decisionLogic.test.ts` — 9 tests covering `isOverride` and `validateDecisionForm` for every recommendation × decision cell.
- `ReviewPanel.test.tsx` — 3 tests: score/band/versions render, partial-data warning, bilingual reason codes.
- `DecisionForm.test.tsx` — 4 tests: blocks submit without override reason, shows override notice, submits with matching decision, submits an override with a reason.

## 7. Limitations / follow-ups

- Officer auth is header-based for pilot only. Replace with SSO/OIDC + role-based authorization in P6 hardening.
- `OfficerDecisionLog` append-only invariant is enforced only in application code. Add DB trigger / rules in P6.
- RE handoff transport uses the pilot HMAC signer; production OAuth 2.0 client credentials + mTLS wiring is deferred to P6 (`re_api_handoff_spec.md §2`).
- The dashboard does not yet render the P5 institutional views (portfolio, fairness) — that is Phase 5 scope.
