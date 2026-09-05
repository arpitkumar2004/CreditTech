# Phase 6 — Production hardening (ML/finance-scoped)

**Status:** Implemented — 2026-09-03
**Entry gate:** P5 complete; 83 pre-P6 tests green.
**User-descoped from the generic P6 brief:** SSO/OIDC login, borrower session
tokens, RE OAuth 2.0 + mTLS + idempotency, SMS/IVR grievance intake. The
assignment is ML/finance-oriented — production auth/RE-transport hardening is
carried as a known deferral (see `LIMITATIONS`).

## 1. Scope

| In (delivered) | Out (descoped per user) |
|----|----|
| Ratified fairness thresholds + `FairnessGate` | Officer SSO/OIDC + RBAC |
| Model promotion gate (fairness + performance) | Borrower JWT session tokens |
| DB-level append-only triggers (SQLite + Postgres DDL) | RE OAuth 2.0 client-credentials + mTLS |
| PDF score report (WeasyPrint → ReportLab → built-in fallback) | Idempotency/retry for RE handoff |
| Production smoke-test framework (AA / Geospatial / Bureau) | SMS/IVR grievance webhook |
| DR backup + restore + parity verification | |
| Security hardening middleware (headers, rate limit, body cap) | |

## 2. Code layout

```
config/fairness_thresholds.json                    # ratified manifest (v2026.09.01)

services/core/monitoring/governance.py             # FairnessGate + manifest loader
services/core/admin/promotion.py                   # ModelPromotionService + perf minimums
services/core/admin/router.py                      # /admin/models/{v}/promote, /admin/fairness/*
services/core/shared/audit_triggers.py             # SQLite + Postgres DDL install
services/core/dashboard/pdf.py                     # html_to_pdf() with graceful backend fallback
services/core/ops/smoke.py                         # AA/Geospatial/Bureau smoke checks
services/core/ops/dr.py                            # backup / restore / row-count parity
services/core/ops/router.py                        # /ops/smoke/integrations
services/core/shared/security_middleware.py        # SecurityHeaders + BodySize + RateLimit

scripts/backup.py                                  # CLI: python -m scripts.backup
scripts/restore.py                                 # CLI: python -m scripts.restore
```

## 3. Fairness governance (§8.3, §17.2)

`config/fairness_thresholds.json` is the ratified manifest — versioned,
`ratified_by` + `ratified_at` recorded. `FairnessGate.evaluate(period)` loads
the manifest, hashes it (`manifest_hash`), pulls the latest fairness-audit
period from the DB, and returns a `FairnessGateResult` with:

- `passed: bool` — no ratified threshold breached
- `breaches: list[ThresholdBreach]` — dim / group / metric / value / threshold / rule
- `skipped_insufficient: int` — `INSUFFICIENT_SAMPLE` rows are excluded

Rules per dimension:

- `min_approval_rate` — per-group floor
- `max_override_rate` — per-officer ceiling
- `max_approval_gap` — max-min across groups within a dimension

The gate is **descriptive-first**: on failure it returns a structured
report the model owner and external auditor can act on.

## 4. Model promotion pipeline

`ModelPromotionService.promote_to_active(model_version)` runs a two-check gate
before flipping `active`:

1. **Performance** — AUC ≥ 0.60, Gini ≥ 0.20, KS ≥ 0.15, Brier ≤ 0.30
   (pilot minimums, ratified alongside the fairness manifest).
2. **Fairness** — `FairnessGate` on the latest period.

Both must pass. Failure raises `PromotionBlocked` carrying the full report;
the registry is not mutated. Success advances `candidate → validated → active`,
demoting any prior active model to `retired`.

Endpoints:
| Method | Path | Purpose |
|-|-|-|
| GET  | `/api/v1/admin/fairness/manifest` | Read the ratified manifest + hash |
| GET  | `/api/v1/admin/fairness/gate?period=` | Dry-run FairnessGate |
| GET  | `/api/v1/admin/models/{v}/promotion-check` | Dry-run promotion gate |
| POST | `/api/v1/admin/models/{v}/promote` | Gate + promote to active |

Blocked promotions return `409` with the full report body.

## 5. Audit append-only enforcement

`services/core/shared/audit_triggers.install_append_only_triggers()`
installs dialect-specific triggers on both `officer_decision_log` and
`grievance_audit_log`:

- **SQLite:** `BEFORE UPDATE/DELETE` triggers that `RAISE(ABORT, ...)`.
- **Postgres:** trigger function `raise_append_only()` raising SQLSTATE
  `insufficient_privilege`.

Called from application startup (`init_db`) and from the test fixture, so
mutation attempts fail at the database — not just the app layer. See
`tests/test_p6_append_only.py` for proof.

## 6. PDF score report

`services/core/dashboard/pdf.html_to_pdf(html)` returns `(pdf_bytes, backend)`:

1. Try WeasyPrint (full HTML/CSS fidelity — production install).
2. Fall back to ReportLab (basic text render — common in Python envs).
3. Fall back to a self-contained minimal PDF writer (guarantees a valid
   `application/pdf` byte-string with no external dependency, so CI always
   produces a real PDF).

Endpoint: `GET /api/v1/report/score/{score_id}/pdf` — returns
`Content-Type: application/pdf`, header `X-PDF-Backend` names the backend
used for observability.

## 7. Smoke-test framework

`services/core/ops/smoke.run_all()` exercises the AA / Geospatial / Bureau
connectors and returns:

- `PASS` — real sandbox creds present + response valid
- `BLOCKED` — no live creds; ran against local mock (dev/CI happy path)
- `FAIL` — connector reachable but response invalid
- `ERROR` — connector unreachable / exception

Live creds are detected by env: `AA_API_KEY` / `AA_BASE_URL`,
`BUREAU_API_KEY` / `BUREAU_BASE_URL`, `GEOSPATIAL_API_KEY` /
`GEOSPATIAL_BASE_URL`. `DEMO*` or missing values → `BLOCKED`. Nothing is
fabricated. Endpoint: `POST /api/v1/ops/smoke/integrations`.

## 8. DR (backup + restore)

`services/core/ops/dr.py` + `scripts/{backup,restore}.py`:

- `backup_sqlite(src, dst)` uses `sqlite3.Connection.backup()` — safe under
  concurrent writes.
- `restore_sqlite(backup, target)` — file copy with parent dir creation.
- `row_counts(db)` + `verify_parity(pre, post)` — automated drill check.

`tests/test_p6_dr.py::test_backup_and_restore_preserves_row_counts` runs a
full seed → backup → restore → parity assertion.

## 9. Security middleware

Applied globally in `main.py`:

- **SecurityHeadersMiddleware** — `X-Content-Type-Options: nosniff`,
  `Referrer-Policy: no-referrer`, `X-Frame-Options: DENY`, HSTS, CSP for
  HTML responses.
- **BodySizeLimitMiddleware** — `413` on bodies over 1 MiB.
- **RateLimitMiddleware** — 240 req/min per client IP (in-process bucket).
  Disabled in tests via `DISABLE_RATE_LIMIT=1` (set by conftest) since a
  single test host shares the bucket.

## 10. Tests

Full backend suite: **110 / 110 pass** (83 pre-P6 + 27 P6):

- `tests/test_p6_fairness_gate.py` (7)
- `tests/test_p6_promotion.py` (4)
- `tests/test_p6_append_only.py` (4)
- `tests/test_p6_pdf.py` (2)
- `tests/test_p6_smoke.py` (4)
- `tests/test_p6_dr.py` (2)
- `tests/test_p6_security.py` (3)

Existing P0–P5 suite is unchanged and green.

## 11. Limitations / carried deferrals

Per user scoping for this ML-oriented assignment, the following remain
deferred and are not blocking gates:

- Officer auth remains header-based; production SSO/OIDC + RBAC deferred.
- Borrower auth for grievance intake remains header-based.
- RE OAuth 2.0 client-credentials + mTLS + retry/idempotency deferred.
- SMS/IVR grievance intake deferred.
- WeasyPrint is not a hard dependency; production install would upgrade
  PDF fidelity (built-in fallback ships now).
- Postgres append-only triggers are shipped as DDL but only unit-tested
  against SQLite (matching the pilot DB); production install requires
  running the DDL on the target Postgres.
