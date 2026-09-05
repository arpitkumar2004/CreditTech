
# CreditTech — Phase 0 & Phase 1 Planning Summary

**Project:** Alternative Credit Scoring for Rural India (LSP/TSP model)
**Timeline reference:** Phase 0 = Months 1–6 (runs in parallel with Phase 1). Phase 1 = Months 1–2 (starts Day 1).
**Source of truth:** `Credittechplanningcontext.md` §9 (roadmap) + `docs/phase0/*` + `services/core/*`.

---

## PHASE 0 — Regulatory, Vendor & Field Prep

### Goal
Secure every external dependency (regulator, RE partner, vendors, field devices, legal sign-off, community-facing specs) **before** code depends on them. Phase 0 is the "de-risk the non-code stuff" phase — its outputs unblock Phases 1–4.

### What was planned (per §9 of the roadmap)

| Deliverable | Purpose | Hard deadline |
|---|---|---|
| AA FIU onboarding via licensed NBFC-AA | Legal path to consume Account Aggregator data | End of P0 (M6) |
| Partner RE Letter of Intent + RE API/handoff contract spec | Defines who consumes the score and in what format | LoI: end of P0; contract spec: **M2** (unblocks P4) |
| Geospatial vendor contract | Locks NDVI/crop-health data supply | End of P0 |
| NABARD pilot endorsement | Sponsor sign-off for village pilot | End of P0 |
| Legal consent-flow review | DPDP + AA Master Directions sign-off | Rolling |
| **ConsentRecord schema spec** | Unblocks P1 schema design | **Week 2** |
| **Preliminary feature list** | Unblocks reason-code template drafting | **Week 4** |
| **SHG/FPO manual entry UI spec** | Unblocks P2 UI build | **Month 2** |
| **RE API/handoff contract spec** | Unblocks P4 handoff design | **Month 2** |
| SHAP reason-code template library draft (bilingual) | Enables reason-code rendering in P3 | Draft in P0; final pass triggered by P3 |
| Bank Sakhi device assessment + site connectivity survey | Confirms hardware/network feasibility at each of 5 sites | End of P0 |

### Definition of Done (roadmap §9)
- Signed RE LoI + agreed API/handoff contract spec
- AA sandbox credentials in hand
- Geospatial API contract signed
- Legal sign-off on consent flows
- SHG/FPO UI spec approved by field operations
- SHAP template library draft complete in all pilot state languages
- Bank Sakhi devices procured and tested at site 1

### What is DONE (evidence in repo)

All seven **document-shaped** deliverables are checked in under `docs/phase0/`:

| File | Deliverable it covers |
|---|---|
| `consent_record_schema_spec.md` | ConsentRecord schema spec (Week-2 interim output) |
| `preliminary_feature_list.md` | 40+ alternative-data features under 5 Cs (Week-4 interim output) |
| `re_api_handoff_spec.md` | RE API/handoff REST/JSON contract (M2 output) |
| `shg_fpo_ui_spec.md` | Offline-first Bank Sakhi manual-entry UI spec (M2 output) |
| `shap_reason_code_templates.md` | Bilingual (English/Hindi) SHAP → reason-code template library |
| `aa_fiu_onboarding_checklist.md` | AA FIU integration playbook |
| `bank_sakhi_device_assessment.md` | Device selection + site connectivity template |

### What is REMAINING (external/off-repo, cannot be closed by code alone)

These are process/relationship items — not files. None of them can be marked done from the codebase:

- ☐ **Signed RE Letter of Intent** (contract-level, not a spec)
- ☐ **AA FIU onboarding actually completed** with a licensed NBFC-AA → **sandbox credentials in hand**
- ☐ **Signed geospatial vendor contract** (specific vendor selected; matches open question #2)
- ☐ **NABARD pilot endorsement** obtained
- ☐ **Legal counsel sign-off** on the documented consent flow
- ☐ **Field ops approval** of the SHG/FPO UI spec (spec exists; approval is an external act)
- ☐ **SHAP template library final pass** — triggered *after* P3 confirms the exact feature set (currently a draft)
- ☐ **Bank Sakhi devices procured & tested at site 1** (physical procurement)

### Phase 0 status summary
**All seven planned document/spec deliverables exist in the repo.** The remaining Phase 0 work is entirely external: signed contracts, vendor credentials, regulator endorsement, legal sign-off, and physical device procurement. These are timeline-blocking for pilot launch (Phase 7) but do not block Phases 1–3 of engineering work.

---

## PHASE 1 — Project Setup & Consent Foundation

### Goal
Establish the one service that everything else depends on: a **tamper-evident, legally-reviewed Consent Service** on a working cloud + CI/CD + local-dev baseline, so subsequent phases can build against a stable foundation.

### What was planned (per §9)

| Task | Notes |
|---|---|
| Cloud accounts + IaC baseline | Terraform/equivalent in `infra/` |
| CI/CD skeleton | GitHub Actions: lint → type-check → test → build → deploy staging → smoke → manual promote |
| PostgreSQL schema — `Borrower` + project scaffolding in Week 1 | Do not lock ConsentRecord schema until P0 legal review lands (Week 2) |
| Full schema after ConsentRecord confirmed: `DataPull`, `FeatureSnapshot`, `Score`, `ReasonCode`, `LoanApplication`, `FairnessAuditLog` | 10 core entities per §7.1 |
| Consent Service: create / hash-chain / revoke / verify | Append-only, cryptographic chain (ADR-6) |
| Docker Compose local dev with mocked connectors for all 4 rails | So every engineer can run the full stack offline |

### Definition of Done (roadmap §9)
- Consent record can be **created, hash-chain-verified, retrieved, and revoked**
- A "hello world" deploys through the full CI/CD pipeline
- Every engineer can run the full stack locally against mocks
- ConsentRecord schema is post-legal-review (not assumed)

### What is DONE (evidence in repo)

| Planned item | Evidence |
|---|---|
| Modern packaging | `pyproject.toml` |
| Containerized dev environment | `Dockerfile`, `docker-compose.yml` |
| Env template | `.env.example` (referenced in README §3) |
| Async DB + settings | `services/core/database.py`, `services/core/config.py` |
| Structured JSON logging with PII scrubbing | `services/core/shared/logging.py` |
| ORM schema — 10 core entities | `services/core/shared/models.py` |
| Consent Service (lifecycle) | `services/core/consent/service.py` + `router.py` — create, retrieve, revoke, verify, audit endpoints wired at `/api/v1/consent/*` |
| DB migration engine | `alembic.ini`, `alembic/env.py`, `alembic/versions/` |

Additional folders already scaffolded beyond P1 scope (belong to P2/P3/P4/P5): `ingestion/`, `scoring/`, `explainability/`, `handoff/`, `monitoring/`, `simulation/`, `templates/`, plus `ml/{features,training,evaluation,registry}` and `apps/borrower-app` (unified portal).

### What is REMAINING for Phase 1 specifically

- ☐ **`infra/` directory is empty** — no IaC baseline committed. Cloud accounts + Terraform/equivalent config is a stated P1 deliverable and is missing.
- ☐ **CI/CD pipeline not verified** — no `.github/workflows/` visible in the tracked tree; the "hello world deploys through the full pipeline" DoD cannot be confirmed.
- ☐ **Legal-reviewed ConsentRecord schema** — the *spec* exists in `docs/phase0/consent_record_schema_spec.md` and the ORM implements it, but the roadmap's DoD requires **post-legal-review** confirmation. That sign-off is a Phase 0 external item still open (see above).
- ☐ **Mocked connectors for all 4 rails available in Docker Compose** — mock server exists (`services/core/ingestion/mocks/server.py` per README) but that's a Phase 2 artifact; Phase 1 wanted stubbed placeholders wired into `docker-compose.yml` so every engineer can boot the full stack. Verify the compose file actually spins the mock server up as a service.
- ☐ **"Every engineer can run the full stack locally against mocks"** — needs a runbook test on a clean machine; not verifiable from files alone.

### Phase 1 status summary
The **core P1 goal (working Consent Service with hash-chained ledger, ORM for all 10 entities, Alembic migrations, structured logging with PII scrubbing, Docker Compose)** is done in code. The **infrastructure baseline (`infra/`) and CI/CD workflow are the two concrete P1 deliverables missing** from the repo. The legal-review DoD gate is externally blocked on Phase 0.

---

## Cross-Phase Observations

1. **Scope creep past P1 is already visible in the repo** — Phase 2 (ingestion connectors, mocks), Phase 3 (scorecard, SHAP), and Phase 4/5 folders exist. Per the README, Phases 0–3 are all claimed complete. That is **ahead of the roadmap's Month 1–4 timeline** — worth confirming that the P1 DoD (especially IaC + CI/CD + legal review of ConsentRecord) was not skipped in the rush to build downstream services.

2. **What blocks pilot go-live is Phase 0 external items, not code.** Signed RE LoI, AA credentials, NABARD endorsement, legal sign-off, and Bank Sakhi devices are the true critical path. Engineering can (and has) proceeded against mocks.

3. **AA real-credential validation** is explicitly deferred to the Phase 6 entry gate if credentials are not yet in hand — this is the documented escape hatch and should be tracked as an outstanding risk today.

---

## Consolidated Punchlist

**Phase 0 — external items tracked in `docs/phase0/phase0_status_tracker.md`** (E1–E8):
Signed RE LoI, AA FIU credentials, geospatial vendor contract, NABARD endorsement,
legal sign-off on consent flow, field-ops approval of SHG/FPO UI spec, SHAP
template final pass (P3-triggered), Bank Sakhi device procurement + site-1 test.
Owners update the tracker as items close.

**Phase 1 — in-repo closures (this pass):**
- ✅ `infra/` populated with a Terraform baseline: `versions.tf`, `modules/{network,database,container_app,storage}`, and `envs/{staging,production}` compositions. India-region (`ap-south-1`), managed Postgres + Fargate + S3, no Kubernetes — matches ADR-5.
- ✅ `.github/workflows/ci.yml` added — ruff, mypy, alembic upgrade, pytest (with a Postgres service container), container build, `pip-audit`, gitleaks.
- ✅ `.github/workflows/deploy-staging.yml` added — gated on CI success, runs `terraform apply` for staging and smoke-tests `/health`, with a manual-approval production promote job.
- ✅ Mock connectors already wired in-process (`services/core/main.py:89`) — a single `docker compose up` gives the full stack against mocks, satisfying the P1 "every engineer runs the full stack locally" DoD.
- ✅ Baseline Alembic migration `alembic/versions/14323a45982d_initial_schema.py` created; every table + FK + index + CHECK constraint from the ORM is included. Upgrade/downgrade/upgrade cycle verified against SQLite. Cross-dialect column types added in `services/core/shared/types.py` so the same migration runs on PostgreSQL (production) and SQLite (test harness).
- ✅ Full pytest suite green (21/21). Ingestion pipeline test now exercises all four mock rails end-to-end via `httpx.ASGITransport` (fix in `services/core/ingestion/connectors.py`).
- ✅ `docker-compose.yml` `web` command now runs `alembic upgrade head` before uvicorn, so a fresh `docker compose up --build` reaches a migrated schema before serving traffic.
- ✅ `pyproject.toml` build backend fixed (`setuptools.build_meta`) so `pip install -e ".[dev,ml]"` — used by CI — actually resolves.
- ⏳ `ConsentRecord` schema remains **provisional** until Phase-0 item E5 (legal sign-off) closes — enforcement described in the status tracker.
