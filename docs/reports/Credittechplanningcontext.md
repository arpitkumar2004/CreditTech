# CreditTech — Engineering & ML Roadmap

### From Zero → Village Pilot MVP → Production Scale

**Prepared as a technical companion to:** *Alternative Credit Scoring for Financial Inclusion* (Arpit Kumar, IIT Kharagpur, Aug 2026)

**Role stack applied:** Principal Software Engineer · Senior ML Engineer · Solutions Architect · SRE · Security Engineer · Product Engineer · Technical PM

> **Scope note:** This document is an engineering blueprint, not legal, compliance, or investment advice. Every reference to RBI/DPDP/AA regulation reflects the source report's own citations and is meant to inform architecture decisions — final compliance sign-off requires your own legal counsel, NABARD, and your partner Regulated Entity (RE).

---

## Missing Assumptions & Questions That Would Change the Architecture

The source report defines the product, the regulatory posture, and the pilot parameters in detail, but leaves several build-level decisions open. I've made explicit assumptions below and flagged the questions whose answers would most change the architecture. Everything after this section is built on these assumptions; revisit them before locking in Stage 2+ decisions (§19).

**Assumptions made:**

1. CreditTech remains a pure **LSP/TSP** — it never touches borrower funds or holds credit risk itself. This removes payment-processing/PCI-DSS scope entirely.

2. One partner RE per pilot village-site, onboarded sequentially, not simultaneously.

3. Hosting on a public cloud **India region** (AWS ap-south-1 / GCP asia-south1) satisfies data-localisation intent for the pilot; not a sovereign/NIC government cloud.

4. Android-first client (98% of rural internet usage is Android/Indic-language per IAMAI–Kantar); no iOS in v1.

5. Tabular gradient-boosted models — **no GPU** needed for training or inference at pilot scale.

6. "Minutes, not days" scoring SLA (§11 of source report) means **near-real-time synchronous/async request-response**, not a streaming system.

7. CreditTech integrates with AA as a **Financial Information User (FIU)** via a licensed NBFC-AA — it does *not* become a registered Consent Manager itself.

8. SHG/FPO and e-NAM data are **not yet fully API-accessible** in most pilot villages; v1 assumes semi-manual/CSV ingestion with a path to API integration later.

9. ULI integration is **deferred past v1** — large-lender ULI adoption is still "muted" per the source report's own citation (Business Standard, 2026); v1 integrates directly with the partner RE via an OCEN-style API instead.

10. One shared pan-pilot model with site-type as a feature, not five separate per-village models (data volume at 750–1,250 borrowers is too thin to train five models well).

**Questions to answer before Stage 2 (§19):**

| # | Question | Why it changes the architecture |

|---|---|---|

| 1 | Will CreditTech ever hold credit risk / disburse funds directly? | Determines whether NBFC licensing, PCI-equivalent controls, and treasury systems are ever needed |

| 2 | Which specific geospatial/EO vendor — hosted API (e.g., SatSure-style) or raw Sentinel-2 requiring an in-house pipeline? | Buy-vs-build call; raw imagery needs a GPU/compute-heavy processing pipeline, an API doesn't |

| 3 | Does the partner RE expose an OCEN-compatible API, or is handoff manual/file-based at pilot stage? | Changes Layer 4 from "API orchestration" to "structured export + human handoff" |

| 4 | Is multi-state rollout funded/expected within 12 months of pilot end? | Determines how much Stage 3–4 scaling work (§19) is worth doing *during* the pilot vs after |

| 5 | Will SHG/FPO data arrive via API, CSV, or fully manual field collection? | Changes Layer 2 ingestion from an integration task to a data-entry/OCR pipeline |

| 6 | Is a dedicated Data Protection Officer / compliance hire budgeted, or does engineering own DPDP operational compliance? | Affects Phase sequencing (§9) and whether consent-ledger tooling is built early or late |

| 7 | Does "offline-first" mean offline *data capture* only, or offline *scoring* too? | Materially changes client architecture — offline scoring needs an on-device model |

| 8 | Fixed-schedule retraining (post-Kharif/Rabi) or drift-triggered? Who signs off model promotion — internal team or the external fairness auditor? | Determines MLOps pipeline design and governance gating (§8, §17) |

---

## 0. Executive Summary

CreditTech is not a consumer app chasing viral growth — it's a **regulated-finance decision-support system** serving 750–1,250 borrowers across 4–5 villages in its first 9–12 months, sitting between borrower-side data (Account Aggregator, satellite/geospatial, SHG/FPO, bureau) and a partner bank/NBFC's own underwriting. That changes almost every standard "startup MVP" instinct:

- **Traffic is low, stakes are high.** At pilot scale you'll process maybe 5–15 scoring requests/day. The engineering risk is not "will it scale" — it's "will a wrong or unfair score damage a real borrower's access to credit and CreditTech's regulatory standing." Correctness, explainability, and fairness monitoring are MVP-day-one requirements, not V2 polish.

- **The hard part isn't the ML model — it's data integration and consent.** Four external data rails (AA, geospatial, SHG/FPO, bureau) each have different reliability, latency, and consent semantics. The "graceful degradation" design principle in the source report (§6) is the single most important architectural decision in this document.

- **Simplicity is not optional — it's mandatory.** A 5–7 person team building a 9–12 month pilot cannot afford Kubernetes, microservices, or a custom MLOps platform. A well-organized monolith, managed Postgres, and boring infrastructure will beat a "scalable" architecture that never ships the pilot.

This roadmap treats the 4–5 village pilot as the MVP, and defines explicit, evidence-gated stages (§19) for what changes at 10K, 100K, and 1M+ borrowers — most of which should **not** be built now.

---

## 1. Product Understanding

### 1.1 Problem

Formal Indian lenders under-serve financially-active-but-bureau-invisible borrowers (small/marginal farmers, SHG members, rural micro-enterprises) because bureau-based underwriting requires a repayment history these borrowers structurally don't have. The problem exists because India built world-class **payments and identity** rails (UPI, Aadhaar) a decade before it built **creditworthiness-signal** rails. Existing point solutions (Kaleidofin, SatSure) prove the model works at national fintech scale but haven't been validated as a *replicable, multi-institution, village-level* design integrating simultaneously with AA + ULI/OCEN + community institutions + a formal fairness audit — that's the specific gap CreditTech fills.

### 1.2 Users

| User type | Technical literacy | Primary interface | Permissions |

|---|---|---|---|

| Farmer / SHG member / micro-entrepreneur (borrower) | Low–medium, low bandwidth | Android app, IVR/USSD, Bank Sakhi-assisted | Apply, consent, view own score/reasons, appeal |

| Bank Sakhi / BC (assisted-channel operator) | Medium | Web/mobile assisted-onboarding tool | Submit on behalf of borrower, cannot see raw PII beyond what's needed |

| Loan officer (partner RE) | Medium–high | Lender Decision Interface (web) | View score + reason codes + evidence, approve/reject/request more info |

| NABARD / pilot sponsor / partner RE management | High | Institutional Dashboard | Read-only portfolio analytics, fairness-audit reports |

| CreditTech ML/eng team | High | Internal admin, model registry, monitoring | Full internal access, no direct borrower PII access without audit log |

| Independent fairness auditor | High | Read-only audit export | Approval-parity data, model documentation |

### 1.3 Core Use Cases

```text

Must-have (MVP / pilot)

├── Consent-based onboarding (Aadhaar e-KYC + AA consent)

├── Multi-source data aggregation with graceful degradation

├── Alternative score + confidence band generation

├── Human-readable reason codes (top-5, localized language)

├── Loan-officer decision interface (human-in-the-loop)

├── Basic fairness/drift monitoring (gender, geography, landholding)

├── Borrower grievance/appeal channel

└── Institutional dashboard (basic portfolio metrics)

Should-have (late pilot / early scale)

├── Automated SHG/FPO/e-NAM API ingestion (replacing manual pilot ingestion)

├── ULI-compatible hand-off

├── Scheduled + drift-triggered retraining pipeline

└── Multi-RE routing (more than one lender per site)

Nice-to-have (post-pilot)

├── Native offline scoring on-device

├── Multi-state, multi-language expansion tooling

├── Self-serve RE onboarding portal

└── Telecom/utility signal (opt-in only, explicitly deferred per privacy design)

Explicitly out of scope (v1 and beyond, by design)

├── CreditTech becoming a Regulated Entity / holding credit risk

├── Direct fund disbursal or repayment collection

├── Caste/religion/protected-attribute features, or geography used as a proxy for them

└── iOS app (no evidence of rural iOS demand)

```

### 1.4 MVP Definition

```text

MVP = The 4–5 village pilot system (750–1,250 borrowers, 9–12 months)

├── Consent + onboarding (app / IVR / Bank Sakhi)

├── 3 of 4 ingestion rails automated (AA + geospatial + bureau); SHG/FPO semi-manual

├── One shared scoring model (XGBoost/LightGBM) + logistic scorecard fallback

├── SHAP-based reason codes in local language

├── Loan-officer web dashboard (single partner RE integration, OCEN-style API or manual export)

├── Fairness monitor (batch, weekly — not real-time streaming)

└── Institutional dashboard (basic charts, not self-serve BI)

```

**What should NOT be built in V1, and why:** ULI integration (immature ecosystem adoption — building against it now risks building against a moving target); multi-lender orchestration (only one RE per site in the pilot design); a custom feature store platform (a handful of versioned Postgres tables suffice at this data volume); Kubernetes/microservices (team size and traffic don't justify the operational tax); a fully automated retraining pipeline (9–12 months = at most one full Kharif–Rabi cycle, i.e., maybe one or two retrains total — automating this is premature).

---

## 2. Requirements Engineering

### 2.1 Functional Requirements (representative — full set in a proper PRD)

| Requirement | Input | Processing | Output | Key failure/edge cases |

|---|---|---|---|---|

| Consent capture | Aadhaar, borrower purpose selection | e-KYC verification, DEPA consent artifact generation | Signed, time-bound, revocable consent record | Borrower has no Aadhaar-linked mobile → Bank Sakhi-assisted OTP fallback; consent later revoked mid-process → halt ingestion, log |

| Multi-source ingestion | Consent record, borrower ID | Parallel calls to AA / geospatial / SHG-FPO / bureau connectors | Normalized borrower profile with per-source status flag | Any single rail times out/unavailable → proceed with partial data + lower confidence band, never hard-fail |

| Score generation | Normalized profile | Feature engineering → model inference → calibration | Score (0–100) + confidence band | <2 of 4 sources available → flag for manual review instead of auto-score |

| Explainability | Score + feature vector | SHAP value computation | Top-5 reason codes, localized | Feature not human-interpretable (e.g. embedding) → excluded from reason-code candidates by design |

| Loan officer review | Score, reasons, evidence | Present to human decision-maker | Approve/Reject/More-info decision, logged | Loan officer overrides score → capture override reason for the fairness/drift monitor |

| Fairness monitoring | Batch of scored applications | Approval-rate parity computation across gender/geography/landholding | Weekly report, alert on threshold breach | Small sample size per bucket at pilot scale → widen confidence intervals, don't over-alert |

| Grievance/appeal | Borrower dispute | Route to human reviewer, re-examine with borrower input | Resolution + audit trail | No response within SLA → auto-escalate |

### 2.2 Non-Functional Requirements (initial targets — assumptions, revisit post-pilot)

| Dimension | Pilot target | Basis |

|---|---|---|

| Score-generation latency | < 2 minutes (system), < 1 hour end-to-end incl. loan officer review | Source report §11 SLA table |

| Availability | Business-hours reliability (~95%), not 24/7 five-nines | Pilot scale, human-in-loop process anyway |

| Throughput | Peak ~20–30 applications/day across all 5 sites | 750–1,250 borrowers over 9–12 months |

| Score availability under partial data | ≥ 90% of applicants still get a confidence-weighted score with 1 of 4 rails down | Source report §13.3 KPI |

| Data durability | No data loss on consent records or scored applications; encrypted backups | Regulatory audit requirement |

| Security | Encryption at rest/in transit, India-region hosting, RBAC | DPDP + AA Master Directions |

| Explainability coverage | 100% of scores must ship with reason codes | RBI Fair Practices / disclosure norms |

| Fairness | Gender approval-gap narrowed ≥50% vs baseline; PAR90 ≤2% | Source report §13.3 KPI |

---

## 3. Knowledge Prerequisites

| Concept | Why needed | Depth | When |

|---|---|---|---|

| RBI Digital Lending Directions & LSP/RE model | Defines what CreditTech is legally allowed to build | Working knowledge | **Before** — shapes every architecture decision |

| Account Aggregator (AA) / DEPA consent model | Primary data-ingestion rail | Working knowledge of API + consent flow | Before MVP |

| DPDP Act & Rules 2025 | Consent, breach-notification, data-minimisation obligations | Working knowledge | Before MVP |

| Gradient-boosted trees (XGBoost/LightGBM) | Core scoring model | Practical/applied | While building |

| SHAP explainability | Mandatory reason codes | Practical/applied | While building |

| Fairness metrics (demographic parity, equalized odds) | Governance requirement, not academic exercise | Practical/applied | While building |

| REST/JSON API design, OAuth2/mTLS | Every DPI integration | Practical | Before MVP |

| Feature stores / versioned features | Reproducibility for a regulated model | Conceptual → practical | While building |

| Basic geospatial/EO data handling (NDVI, crop classification) | Understanding a vendor API's output, not building EO from scratch | Conceptual | While building |

| MLOps: model registry, drift detection | Required for production, not day-1 pilot | Conceptual now, practical for production | Before production readiness |

| OCEN protocol | Lender hand-off contract | Working knowledge | Before Stage 2 lender integration |

| Distributed systems, sharding, event-driven architecture | Only relevant at 100K+ users | Conceptual only | Wait until scaling (§19, Stage 4+) |

**Learn before building:** RBI/AA/DPDP regulatory basics, REST API design, gradient boosting fundamentals.

**Learn while building:** SHAP, fairness metrics, OCEN, feature versioning, geospatial vendor APIs.

**Wait until scaling:** Kubernetes, sharding, event-driven architecture, multi-region design, advanced MLOps (canary model rollout, online feature stores).

---

## 4. System Architecture (MVP)

```text

Borrower

  ↓ (app / IVR / Bank Sakhi web)

Onboarding & Consent Service  ──→  Consent Ledger (Postgres, append-only)

  ↓

Data Aggregation Service (async orchestrator)

  ├─→ AA Connector (FIU via licensed NBFC-AA)

  ├─→ Geospatial Connector (vendor API)

  ├─→ SHG/FPO Ingestion (CSV import + manual entry UI, pilot stage)

  └─→ Bureau Connector (licensed CIC)

  ↓ (per-source status + normalized profile)

Feature Store (versioned Postgres tables)

  ↓

Scoring Service

  ├─ XGBoost/LightGBM ensemble (primary)

  └─ Logistic scorecard (regulatory fallback / low-confidence path)

  ↓

Explainability Service (SHAP) → Reason Codes (localized)

  ↓

Lender Decision Interface (web) ←→ Partner RE (OCEN-style API or structured export)

  ↓

Loan Lifecycle & Repayment Feedback (consented) → feeds back into training data

  ↓ (parallel, async)

Fairness & Drift Monitor (weekly batch job) → Institutional Dashboard

```

**Component responsibilities:**

- **Onboarding & Consent Service** — the only service allowed to write consent records; every downstream call must present a valid, unexpired consent token.

- **Data Aggregation Service** — orchestrates the 4 ingestion rails **in parallel with independent timeouts**; this is where graceful degradation is implemented (never blocks on the slowest rail).

- **Feature Store** — small, versioned, crop-cycle-aware (Kharif/Rabi seasonality tags). Not a dedicated feature-store *product* at this scale — just disciplined table design with feature version columns.

- **Scoring Service** — synchronous request/response for the pilot's traffic volume; no need for a streaming/batch split yet.

- **Lender Decision Interface** — the human-in-the-loop boundary; this is a deliberate architectural choice, not a UI afterthought — it's the regulatory control point.

- **Fairness & Drift Monitor** — runs as a scheduled batch job, not real-time, because sample sizes per bucket are too small at pilot scale for meaningful real-time alerting.

**Sync vs async:** Consent capture and score generation are synchronous from the borrower's perspective (they wait, or return later within the app). Internally, the 4 ingestion calls run **async/parallel**. Fairness monitoring, model retraining, and institutional reporting are async batch jobs.

---

## 5. Architecture Decision Records

**ADR-1: Monolith vs Microservices**

```text

Decision: Modular monolith (single deployable, internally organized by domain module)

Why: 5–7 engineers, <30 requests/day, 9–12 month timeline

Alternatives: 1) Microservices per layer  2) Serverless functions per connector  3) Monolith

Why we chose this: Microservices add deployment/observability/networking overhead with zero

  benefit at this traffic. A monolith with clean internal module boundaries (consent, ingestion,

  scoring, explainability, decisioning) preserves a future extraction path without paying the cost now.

Advantages: Fast to build, one thing to deploy/monitor/secure, easy local dev

Disadvantages: A bug in one module can affect deploy of the whole system; scaling is coarse-grained

Future migration path: Extract the Data Aggregation Service first (it's the natural seam — different

  scaling profile, external-API-bound) once traffic or team size justifies it

When insufficient: Multiple partner REs + multiple states + a dedicated ML team wanting independent

  deploy cadence (roughly Stage 3–4, §19)

```

**ADR-2: Database — PostgreSQL (managed)**

```text

Decision: Single managed PostgreSQL instance (e.g., RDS/Cloud SQL, India region)

Why: Relational integrity for consent/audit trails is a regulatory requirement, not a preference

Alternatives: 1) NoSQL (MongoDB)  2) SQLite  3) PostgreSQL

Why we chose this: Consent, score, and loan-decision records need ACID transactions and strong

  schema/constraints for auditability. NoSQL's flexibility is not a benefit for regulated records.

  SQLite doesn't support the concurrent writes or managed backups a regulated pilot needs.

Advantages: Strong consistency, mature tooling, easy to reason about for auditors

Disadvantages: Vertical scaling ceiling eventually; not built for very high write throughput

Future migration path: Read replicas → then partition by site/state → then consider a data

  warehouse (OLAP) for the Institutional Dashboard once portfolio analytics outgrow OLTP queries

When insufficient: Sustained high write volume at 100K+ borrowers (Stage 4, §19)

```

**ADR-3: Synchronous REST vs GraphQL vs gRPC**

```text

Decision: REST/JSON (OCEN itself is REST/JSON)

Why: Every external DPI rail (AA, OCEN, ULI) is REST/JSON; matching it minimizes translation layers

Alternatives: 1) GraphQL  2) gRPC  3) REST

Why we chose this: No internal polyglot-service need for gRPC's binary efficiency; no complex

  client query-shaping need for GraphQL. REST also has the widest audit/security tooling ecosystem.

Disadvantages: Some over/under-fetching on richer dashboard views (acceptable at this scale)

Future migration path: Add a thin GraphQL/BFF layer only if the Institutional Dashboard's query

  needs outgrow simple REST endpoints

```

**ADR-4: Model serving — inline synchronous inference vs dedicated serving infra**

```text

Decision: Load the model in-process (or a lightweight sidecar) behind the Scoring Service; no

  dedicated model-serving cluster (no Triton/KServe/SageMaker endpoints)

Why: Tabular gradient-boosted models are small (MBs) and CPU-fast; a dedicated serving layer is

  pure overhead at <30 inferences/day

Alternatives: 1) Managed model-serving endpoint  2) In-process load  3) Serverless function per score

Why we chose this: Simplicity — one fewer moving part, one fewer network hop, one fewer bill

Disadvantages: Model updates require a service redeploy (acceptable given retraining happens at

  most a few times during the pilot)

Future migration path: Extract to a dedicated internal inference endpoint once (a) multiple

  services need to call the model, or (b) retraining cadence increases enough that redeploy-per-

  update becomes disruptive

When insufficient: Multi-state rollout with independent model versions per region (Stage 3+, §19)

```

**ADR-5: Cloud provider & deployment target**

```text

Decision: A single managed public cloud, India region (AWS ap-south-1 or GCP asia-south1);

  containers on a managed container service (e.g., ECS/Cloud Run), not Kubernetes

Why: Data-localisation intent satisfied by region selection; managed containers give restart/

  scaling basics without the operational tax of running/patching a Kubernetes control plane

Alternatives: 1) Kubernetes (EKS/GKE)  2) Serverless functions  3) Managed containers  4) VPS

Why we chose this: The team doesn't have dedicated platform/SRE headcount; Kubernetes' benefits

  (multi-tenant scheduling, complex rollout strategies) don't apply at single-digit-service scale

Disadvantages: Less portable than K8s if you later need multi-cloud or on-prem/govt-cloud hosting

Future migration path: If NABARD/regulator requires sovereign/government cloud hosting, this is a

  redeploy, not a rearchitecture, as long as containerization is maintained from day one

When insufficient: True multi-region active-active requirements (Stage 5–6, §19)

```

**ADR-6: Consent ledger design — not blockchain**

```text

Decision: Append-only table in PostgreSQL with cryptographic hash-chaining per record, not a

  blockchain/DLT

Why: DPDP requires an auditable, tamper-evident, ≥7-year-retained consent trail — not decentralization

Alternatives: 1) Permissioned blockchain  2) Hash-chained append-only relational table  3) Plain mutable table

Why we chose this: A hash-chained table gives tamper-evidence and auditability without DLT's

  operational complexity, consensus overhead, or unfamiliar tooling for a small team

Disadvantages: Doesn't offer decentralized trust across institutions (not a pilot requirement —

  CreditTech itself, not a multi-party consortium, is the system of record here)

Future migration path: If NABARD/multiple REs later require a shared, cross-institution consent

  registry, revisit — but that's a multi-institution product decision, not a technical inevitability

```

**ADR-7: Geospatial data — open-data fallback path alongside the vendor contract**

```text

Decision: Build `GeospatialConnector` to support a secondary open-data source (Sentinel-2/Copernicus

  via Google Earth Engine, free-tier) that can populate the same NDVI/rainfall-deviation fields as

  the paid vendor API, used for interim pilot validation only — not as a vendor replacement

Why: Phase 0 external item E3 (geospatial vendor contract) has no committed close date and blocks

  P2's geospatial connector from validating against real data; a benchmarking review of public

  agri-fintech projects (docs/research/external_benchmark_analysis.md) showed at least one comparable

  project running entirely on open-weight EO foundation models against free Sentinel imagery instead

  of a paid vendor — evidence that an open-data path is viable for this feature set (NDVI, rainfall

  deviation) even if lower-SLA

Alternatives: 1) Wait for E3 to close before any real-data testing  2) Build only against mocks

  until the vendor contract signs  3) Build an open-data fallback path in parallel with BD's vendor

  negotiation

Why we chose this: Removes a hard external dependency from the P2 critical path without reversing the

  Build vs Buy decision (§22) — the vendor API stays primary for pilot/production; the open-data path

  is a validation/interim/cross-check signal only, selected via existing per-connector config

Advantages: P2 geospatial connector work and `land_quality_ndvi_avg` / `ndvi_trend_2season` feature

  testing can proceed against real (if lower-resolution) satellite data before E3 closes, matching the

  same "engineering proceeds against mocks/interim data while Phase 0 externals are pending" principle

  already applied elsewhere in this roadmap

Disadvantages: Sentinel-2 (10 m resolution, ~5-day revisit) has lower resolution and no SLA compared

  to a commercial vendor; must not be relied on for production scoring without revisiting this decision

Future migration path: Retire the open-data path once E3 closes and vendor production credentials

  pass the P7 pre-launch smoke test — or keep it permanently as a low-cost cross-validation signal

  against the primary vendor feed if it proves valuable during the pilot

```

---

## 6. Technology Stack

```text

Frontend (borrower):     Lightweight Android app (Kotlin or React Native), offline data-capture

                          only (not offline scoring per assumption #7); IVR/USSD fallback via a

                          telephony provider (e.g., Exotel/Knowlarity, India-based)

Frontend (loan officer/

  institutional):         React + a component library (internal web app, desktop-first)

Backend:                  Python (FastAPI) — same language as the ML stack, minimizes handoff

                          friction between backend and ML engineers

Database:                 PostgreSQL (managed, India region)

Cache:                    None at pilot scale (add Redis only if the geospatial API proves slow

                          and cacheable — see §18)

Queue:                    Lightweight async task queue (e.g., Celery+Redis, or cloud-native

                          managed queue) for the 4 parallel ingestion calls and batch jobs

Storage:                  Object storage (S3/GCS, India region) for raw satellite imagery tiles,

                          consent-artifact PDFs, uploaded documents

ML:                       XGBoost / LightGBM (primary), scikit-learn LogisticRegression (fallback

                          scorecard), SHAP (explainability)

Model serving:            In-process load behind the Scoring Service (ADR-4)

Authentication:           Aadhaar e-KYC (OTP/biometric) for borrowers; OAuth2/JWT + RBAC for

                          internal and loan-officer users; mTLS on all AA/OCEN API calls

Infrastructure:           Managed containers (ECS/Cloud Run) + managed Postgres + object storage

CI/CD:                    GitHub Actions (lint → type-check → test → build → deploy staging → 

                          smoke test → manual promote to production)

Monitoring:                Managed APM (e.g., CloudWatch/Cloud Monitoring) + a lightweight

                          dashboard for model/fairness metrics (custom, small)

Logging:                  Centralized structured logs (JSON), India-region retention

Analytics:                Institutional Dashboard is purpose-built (small internal BI), not a

                          general analytics platform at pilot scale

```

Rationale threads through every row: prefer **managed services over self-hosted**, prefer **one language (Python) across backend+ML** to reduce team-size strain, and avoid any tool whose main selling point is scale you don't have yet.

---

## 7. Data Architecture

### 7.1 Core entities (initial schema, simplified)

```text

Borrower(id, aadhaar_ref[hashed], name, village_id, gender, landholding_band, phone, language)

ConsentRecord(id, borrower_id, purpose, aa_handle, scope, issued_at, expires_at, revoked_at, hash_prev)

DataPull(id, borrower_id, source[AA|GEO|SHG|BUREAU], status, raw_ref[object storage], pulled_at)

FeatureSnapshot(id, borrower_id, feature_version, features_json, season_tag, computed_at)

Score(id, borrower_id, model_version, score, confidence_band, sources_used, generated_at)

ReasonCode(id, score_id, rank, feature_name, direction, localized_text)

LoanApplication(id, borrower_id, score_id, partner_re_id, officer_decision, decided_at, override_reason)

RepaymentRecord(id, loan_application_id, period, status, consented_for_retraining)

Village(id, name, site_type, state, agro_climatic_zone)

FairnessAuditLog(id, period, dimension, group, approval_rate, sample_size)

```

### 7.2 What happens at 10K / 100K / 1M / 10M+ borrowers

| Scale | What changes |

|---|---|

| 10K | Still single Postgres instance; add read replica for Institutional Dashboard queries so reporting never competes with the scoring path for connections |

| 100K | Partition large tables (DataPull, FeatureSnapshot, Score) by time/state; consider a small OLAP store (e.g., a managed warehouse) for the dashboard, separate from OLTP; introduce proper caching for the geospatial connector |

| 1M | Split the single database by domain (consent/ingestion vs scoring vs decisioning) — not full microservice-per-table, but logical database separation; sharding by state/region becomes reasonable given India's state-level regulatory variation anyway |

| 10M+ | Full read/write separation, multi-region within India for latency/DR, dedicated data-warehouse pipeline for portfolio analytics, formal data-retention/archival tiering to cold storage for records past DPDP-mandated retention needs |

**PII handling:** raw PII (Aadhaar reference, name, phone) is stored separately from the model-ready `FeatureSnapshot` table from day one (per source report §12.2) — this is not a "do it later" item; it's the single control that limits breach blast-radius and should be schema-enforced in the MVP.

---

## 8. ML System Design

### 8.1 Data

- **Sources:** AA transaction history, geospatial/EO crop-land signals, SHG-BLP repayment ledgers, e-NAM/market data, KCC/govt scheme status, bureau data where it exists. Explicitly excluded: caste, religion, health; geography is *monitored*, not used as a raw feature, to avoid proxy-discrimination (per the fairness literature the source report cites, §3.3).

- **Labeling:** ground truth is repayment outcome, only available after loan tenure — meaning the pilot's *first* model cannot be trained on CreditTech's own outcomes yet. Bootstrap with the partner RE's historical bureau-scored portfolio (if available) plus published feature-relationship literature (the "5 Cs" weighting from Jonnalagadda & Babu, 2026, cited in the source report) to build the v1 scorecard, then retrain on real pilot outcomes once repayment data starts arriving.

- **Target-variable definition (must be fixed before any post-pilot training, per §9 post-pilot table):** define "default" as an explicit proxy — e.g. DPD90+ (90+ days past due) on the RE's repayment ledger, or missed-repayment-across-a-full-crop-cycle for SHG-routed loans where DPD tracking doesn't apply cleanly — and document it as a first-class artifact, not an implicit modeling choice. Record the known risk up front: a proxy label can misclassify genuine hardship-driven late payment (e.g. a bad monsoon) as the same "default" class as unwillingness to repay, which is a real regulatory-misalignment and fairness risk in an agricultural portfolio — this must be reviewed alongside the fairness gate (§8.3), not treated as a purely technical labeling detail.

- **Bias/leakage:** watch for temporal leakage (using post-loan repayment behavior as a pre-loan feature) and geography-as-proxy leakage explicitly.

### 8.2 Model

- **Baseline:** weighted logistic scorecard on the "5 Cs" framework (character/capacity/capital/collateral/conditions) — interpretable by construction, doubles as the regulatory fallback path when confidence is low.

- **Candidate:** XGBoost/LightGBM ensemble on the full alternative-data feature set.

- **Candidate feature encoding — WoE/IV:** encode the candidate's input features (the same 5-Cs feature table the baseline scorecard already uses) with Weight-of-Evidence binning and select/rank by Information Value before training. This is the standard technique for turning alternative-data features into a regulator-legible, auditable form for exactly this kind of Basel-style scorecard modeling, and it keeps the candidate's feature pipeline consistent with the interpretability bar the logistic baseline already sets — rather than feeding raw features straight into a black-box ensemble. Apply this at the same point retraining happens (§8.4), once real pilot outcome labels exist.

- **Selection:** the candidate must beat the baseline on AUC/KS *and* pass the fairness gate (§8.3) before promotion — beating the baseline on accuracy alone is not sufficient for production promotion.

### 8.3 Evaluation

| Type | Metrics |

|---|---|

| Offline | AUC, KS-statistic, calibration curve, feature-importance stability across folds |

| Fairness (offline, pre-promotion gate) | Demographic parity + equalized-odds gap across gender, landholding-size band, geography — must be within the tolerance the fairness auditor sets before a model can be promoted |

| Online | Approval-rate uplift vs baseline, score-availability-under-partial-data rate |

| Business | PAR90, approval-gap narrowing, reason-code comprehension survey (per source report §13.3 KPIs) |

**Regulatory framing:** the baseline model choice (interpretable-by-construction logistic scorecard, promoted only past a fairness gate, with the candidate ensemble held to the same bar plus an explainability layer) already follows Basel II/III model-risk-management principles — favouring interpretability over raw predictive power where the two trade off, documented calibration, and auditable feature governance. This isn't a new requirement; it's worth naming explicitly in pilot/investor/regulator-facing material since the substance is already designed in.

### 8.4 ML Pipeline

```text

Raw pulls (AA/GEO/SHG/Bureau) → Validation (schema + range checks) → Feature engineering

  (crop-cycle-aware, seasonality-tagged) → Training (offline, on a fixed cadence — not continuous

  at pilot scale) → Evaluation (accuracy + fairness gate) → Model Registry (versioned, with

  training-data snapshot reference) → Deployment (redeploy Scoring Service with new model artifact)

  → Inference (synchronous, per-application) → Monitoring (weekly batch: drift + fairness) →

  Retraining (triggered by season boundary or significant drift, human-approved before promotion)

```

- **Training-data/model versioning tool:** once real pilot outcome data starts feeding `ml/registry/` (post-pilot table below), version it with DVC (or equivalent) rather than ad-hoc file copies — same reproducibility discipline the Alembic migration history already gives the DB schema, applied to training datasets and model artifacts. Not needed pre-pilot since no training data exists yet; add it at the same trigger point as the first XGBoost/LightGBM training run.

- **Batch vs real-time:** batch for training/monitoring; synchronous request-response for inference (traffic volume doesn't justify a streaming architecture).

- **CPU vs GPU:** CPU only — gradient-boosted trees on tabular data of this size don't benefit meaningfully from GPU.

- **Model versioning/rollback:** every promoted model is tagged with its training-data snapshot and evaluation report; rollback = redeploy the previous artifact, which is why in-process model loading (ADR-4) must still support a "pin to version N" config flag.

- **Drift:** data drift (feature distributions shifting, e.g. a new season's rainfall pattern) and concept drift (the relationship between features and repayment changing) are both plausible given seasonal agricultural income — this is *why* the fairness/drift monitor is a first-class MVP module, not a production-only add-on.

---

## 9. Building the MVP — Phased Plan (Revised: 7 Phases + Post-Pilot)

> **Timeline note:** Phase 0 takes 3–6 months and runs in parallel with Phase 1 (which starts immediately). The development phases (1–7) take 7–8 months. Total project duration from first action to pilot go-live is **12–18 months**. The original "9–12 months" was measured from Phase 0 completion, not from project start.

| Phase | Timeline | Objective | Key tasks | Definition of done |

|---|---|---|---|---|

| 0 — Regulatory, vendor & field prep | Months 1–6 (parallel with Phase 1) | Secure all external dependencies before code depends on them | AA FIU onboarding via licensed NBFC-AA; partner RE LoI + **RE API/handoff contract spec** (data format, auth, SLA — agreed alongside LoI, must precede P4); geospatial vendor contract; NABARD pilot endorsement; legal consent-flow review; **SHG/FPO entry UI spec** (offline flow, field-validation rules, dual-entry reconciliation workflow — must precede P2 UI build); SHAP reason-code template library draft on domain-known features (content in pilot languages — not code; final update pass triggered after P3 confirms feature set); Bank Sakhi device procurement + site connectivity assessment at each pilot site. **Interim outputs with hard deadlines:** (a) preliminary ConsentRecord schema spec → week 2, unblocks P1 schema design; (b) preliminary feature list for template library → week 4, enables template library draft to begin; (c) SHG/FPO UI spec → month 2, unblocks P2 UI build; (d) RE API/handoff contract spec → month 2, unblocks P4 handoff design | Signed RE LoI; RE API/handoff contract spec documented and agreed; AA sandbox credentials in hand; geospatial API contract signed; legal sign-off on consent flows; SHG/FPO UI spec approved by field operations; SHAP reason-code template library draft complete in all pilot state languages; Bank Sakhi devices procured and tested at site 1 |

| 1 — Project setup & consent foundation | Months 1–2 (starts day 1) | Establish the one service everything else depends on | Cloud accounts + IaC baseline; CI/CD skeleton; PostgreSQL schema — Borrower and project scaffolding in week 1; **ConsentRecord schema locked only after P0 interim consent spec arrives (week 2)** — do not pre-empt the legal review; full schema (DataPull, FeatureSnapshot, Score, ReasonCode, LoanApplication, FairnessAuditLog) after ConsentRecord is confirmed; Consent Service (create / hash-chain / revoke / verify); Docker Compose local dev with mocked connectors for all four ingestion rails | Consent record can be created, hash-chain-verified, retrieved, and revoked; `hello world` deploys through the full pipeline; every engineer can run the full stack locally against mocks; ConsentRecord schema is post-legal-review, not assumed |

| 2 — Data ingestion, SHG/FPO entry UI & Android app start | Months 2–3 | Wire all four data rails; build the highest-friction, highest-risk UI; begin Android borrower app | **Entry gate:** P1 complete; SHG/FPO UI spec from P0 in hand before UI build begins. AA connector (FIU, against AA sandbox if credentials in hand — otherwise built against mocks with an explicit carry-forward flag; real-credential validation becomes a P6 gate item); geospatial connector (vendor sandbox, async, per-connector timeout); bureau connector (CIC test environment); SHG/FPO manual entry UI built against P0 spec (offline-capable, mobile-first, field-validation rules, dual-entry reconciliation workflow); async orchestrator with independent per-rail timeouts. **Android borrower app skeleton starts here** (Kotlin, offline-first architecture, data-capture screens — mobile developer parallel workstream; not blocked by backend completion) | Graceful-degradation test suite passes for every single-rail-down combination; SHG/FPO entry UI reviewed by a Bank Sakhi proxy for usability; Android app skeleton builds and runs on a ≤2 GB RAM test device; **DoD note:** if AA credentials not yet in hand, AA connector is mock-validated only — "real-credential validation" is explicitly carried to P6 entry gate |

| 3 — Logistic scorecard, SHAP & model registry | Months 3–4 | Deploy the v1 production model — logistic scorecard only (XGBoost deferred: no real repayment outcomes exist until post-pilot) | Feature engineering pipeline (5 Cs framework, Kharif/Rabi seasonality tags, versioned Postgres feature tables); logistic scorecard calibrated on best available proxy/synthetic data; SHAP wired to scorecard; reason codes rendered using P0 template library draft; **P3 completion triggers the template library final update pass** — the assigned P0 content owner updates any feature names or descriptions that differ from the domain-expert draft; model registry entry (version tag, training-data snapshot, evaluation report). Android borrower app main screens built in parallel (mobile developer) | Scorecard produces a score + confidence band + localised reason codes end-to-end; model registry records training-data provenance; evaluation report shows calibration, Gini, and demographic parity on proxy dataset; **template library final update pass complete and merged before P3 closes** |

| 4 — Loan officer decision interface | Months 4–5 | Build the primary regulated touchpoint | **Entry gate:** P3 complete; RE API/handoff contract spec from P0 in hand. FastAPI + Jinja2 + HTMX (server-rendered — no React for an internal tool with 20–50 users); score + confidence band + reason codes + evidence display; Approve / Reject / Request-more-info decision capture with mandatory override-reason logging; structured RE handoff export **built to the P0-agreed contract spec** (not assumed — if spec is not in hand, raise as a blocker, do not design to assumptions). Android borrower app continues in parallel (mobile developer) | Loan officer can review a complete synthetic application, record a decision with override reason, and the decision is stored with a full audit trail; **handoff export validated against the agreed RE contract spec — not self-certified** |

| 5 — Fairness monitor, Android app finalisation & institutional dashboard | Months 5–6 | Complete the remaining regulated channels and the monitoring layer | Weekly batch fairness job (approval-rate parity: gender, geography, landholding-size band; override-rate by loan officer as bias signal); grievance/appeal channel (M8) with defined SLA and escalation path per RBI Fair Practices Code; **Android borrower app finalisation** (background sync, edge-case handling, full UI polish, localization — skeleton started P2, main screens built P3/P4, finalised here); institutional dashboard (portfolio metrics, segment breakdown, fairness-audit report export) | Fairness batch job produces a weekly report with alert thresholds; grievance SLA clock functional; **Android app finalised and passing all test cases on a ≤2 GB RAM device** (this phase completes the app, not starts it); dashboard accessible to partner RE management |

| 6 — Integration, security & load testing | Months 6–7 | Verify the complete system works end-to-end under realistic conditions before touching production | Full consent → ingestion → score → decision flow tested on staging; synthetic borrower smoke tests covering all partial-failure paths; security tests (auth/RBAC, PII scrubbing in all log paths, mTLS on all external connectors, input validation); load test verifying the system handles 30 applications/day at 2× pilot-peak volume; **AA real-credential validation gate** — if the AA connector was mock-validated only during P2 (credentials not yet in hand), real-sandbox validation is a mandatory P6 task before P7 entry, not optional | CI green across all test categories; staging smoke tests pass; all security findings resolved; load test passes SLA; **all four connectors validated against real sandbox or production-equivalent credentials — no connector enters P7 having been mock-validated only** |

| 7 — Production deploy & pilot launch | Months 7–8 | Go live at site 1 only; expand to further sites after a stability gate | **Pre-launch gate: production-credential smoke test** — AA, geospatial, and bureau production endpoints differ from sandbox in auth, rate limits, and error responses; test all three against production credentials before any borrower is onboarded; block launch if any rail fails this test; Production deploy (site 1 only); Bank Sakhi training at site 1; borrower onboarding; incident-response runbook live-tested; monitoring dashboards and alert thresholds active; DR restore tested | **Production-credential smoke test passed on all three external rails before first borrower is onboarded**; first real borrower scored end-to-end at site 1; site 1 stable for 4+ weeks before expanding to sites 2–5 |

**Post-pilot (month 12+, triggered by real repayment outcome data):**

| Post-pilot task | Trigger condition |

|---|---|

| XGBoost/LightGBM candidate training on real labelled outcomes | First repayment cycle complete (≥6 months of pilot data, ≥200 resolved outcomes) |

| Fairness gate evaluation on XGBoost candidate with real demographic data | Candidate training complete |

| Model registry: promote XGBoost if it passes gate; keep logistic scorecard otherwise | Fairness gate result |

| Automated SHG/FPO API ingestion (replacing manual entry UI) | SHG federation digitises their records and exposes an API |

| IVR/USSD channel (if Bank Sakhi channel proves insufficient at certain sites) | Site-specific field evidence that IVR is required |

| ULI integration | ULI lender adoption materially improves beyond current muted level |

| Post-disbursement crop-health early-warning monitor — re-run the geospatial connector periodically for borrowers with a disbursed loan, diff NDVI/rainfall trend against the value captured at scoring time, and flag officers when deterioration crosses a defined threshold | Geospatial connector validated on production credentials (P7 gate) + site 1 stable for 4+ weeks |

| PMFBY insurance-trigger prompt on the officer dashboard — when the early-warning monitor above fires for a borrower with `crop_insurance_enrolled = true`, surface a pre-filled claim-assistance prompt rather than requiring the officer to notice and act manually | Post-disbursement monitor (row above) live and validated |

**Key changes from the previous 10-phase plan:**

- **Phase 5 (Candidate model) dissolved** — XGBoost has no real training data in the pilot window; it moves to post-pilot. Running a fairness gate against synthetic data is also meaningless.
- **Phase 8 (Testing) dissolved** — testing is embedded in every phase's definition of done, not a separate late phase.
- **IVR/USSD removed from MVP** — Bank Sakhi-assisted onboarding covers the same population with less engineering complexity; IVR is post-pilot if field evidence demands it.
- **Celery/Redis removed** — FastAPI `asyncio.gather()` handles the four parallel ingestion calls; a cloud-native scheduler (EventBridge/Cloud Scheduler) handles batch jobs.
- **Loan officer UI changed from React to FastAPI + Jinja2/HTMX** — saves a developer-context switch for an internal tool with 20–50 users.
- **SHG/FPO manual entry UI elevated** to a first-class Phase 2 deliverable with explicit spec requirements (offline-capable, mobile-first, dual-entry reconciliation).
- **Phase 0 is explicitly 3–6 months** — AA FIU onboarding, RE LoI negotiation, and NABARD endorsement are months-long processes, not tasks; they must start on day 1.
- **P0 interim outputs added with hard deadlines** — ConsentRecord schema spec (week 2) and preliminary feature list (week 4) are required before P0 closes; P1 and P3 cannot wait for the full 3–6 month Phase 0 window.
- **RE API/handoff contract spec added to P0 deliverables** — agreed alongside the partner RE LoI by month 2; P4 cannot design the structured handoff export without it.
- **SHG/FPO UI spec added as a named P0 deliverable** (due month 2) — required before P2 builds the UI; a field-operations-reviewed spec must precede the build, not be produced during it.
- **Android borrower app start moved to P2** — the mobile developer has no dedicated P2 work otherwise; spreading the build across P2/P3/P4 and completing in P5 eliminates P5 overload.
- **Production-credential smoke test added as a P7 pre-launch gate** — AA/geospatial/bureau production endpoints differ from sandbox; this test runs before any borrower is onboarded and blocks launch if any rail fails.

**Common mistakes to avoid for this specific product:** treating XGBoost as deployable before real repayment outcomes exist; treating the geospatial API as always-available (it won't be, especially in low-connectivity blocks); logging raw PII into application logs (must be scrubbed); adding Celery for a queue before measuring whether a queue is actually needed.

---

## 10. Repository Structure

```text

credittech/

├── apps/

│   ├── borrower-app/          # Android (Kotlin/React Native)

│   └── # (removed — merged into borrower-app unified portal on :5173)

├── services/

│   └── core/                  # FastAPI monolith

│       ├── consent/

│       ├── ingestion/

│       │   ├── aa_connector/

│       │   ├── geospatial_connector/

│       │   ├── shg_fpo_ingestion/

│       │   └── bureau_connector/

│       ├── scoring/

│       ├── explainability/

│       ├── decisioning/

│       └── fairness_monitor/

├── ml/

│   ├── features/               # feature engineering, versioned

│   ├── training/                # training pipelines

│   ├── evaluation/               # offline + fairness evaluation harness

│   └── registry/                  # model artifact metadata

├── infra/                        # IaC (Terraform or equivalent)

├── tests/

├── docs/

└── .github/workflows/

```

Kept flat and domain-organized — no separate repos per microservice, because there are no microservices yet (ADR-1). A `services/core` monolith with clear internal module boundaries is the correct amount of structure for a 5–7 person, 9–12 month build.

---

## 11. Coding Standards

**Mandatory from day one:** type checking (mypy/TypeScript strict), linting in CI, structured logging with PII scrubbing, secrets via a managed secrets manager (never in code/env files committed to git), input validation on every external-facing endpoint, explicit error handling on every external API call (AA/geospatial/bureau *will* fail — treat that as the expected case, not the exception).

**Unnecessary overhead for MVP:** 100% test coverage mandates, a formal API-versioning scheme before you have external API consumers, a custom internal style guide beyond an established linter config, contract-testing infrastructure before you have more than one integration partner.

---

## 12. API Design (representative endpoints)

| Method | Endpoint | Auth | Notes |

|---|---|---|---|

| POST | `/consent` | Borrower session (OTP) | Idempotent on `(borrower_id, purpose)`; returns consent token |

| POST | `/applications` | Consent token | Triggers async ingestion; returns `application_id`, status `pending` |

| GET | `/applications/{id}/status` | Consent token or officer auth | Polling endpoint while ingestion/scoring runs |

| GET | `/applications/{id}/score` | Officer auth (RBAC) | Returns score, confidence band, reason codes |

| POST | `/applications/{id}/decision` | Officer auth | Records approve/reject/more-info + optional override reason |

| POST | `/grievances` | Borrower session | Creates an appeal, SLA clock starts |

| GET | `/dashboard/portfolio` | Institutional auth | Aggregated, non-PII metrics only |

Versioning via URL prefix `/v1/...`) from day one — cheap now, expensive to retrofit once a partner RE has integrated. Rate limiting on all borrower-facing endpoints (brute-force protection on OTP especially). Pagination/filtering only needed on the dashboard endpoints at this data volume.

---

## 13. Security — Threat Model

| Threat | Impact | Probability | Mitigation | Priority |

|---|---|---|---|---|

| OTP/e-KYC brute force | Account takeover, fraudulent applications | Medium | Rate limiting, attempt lockout, Aadhaar-mandated biometric fallback | High |

| PII leakage via logs/backups | DPDP breach, borrower harm, regulatory penalty | Medium | Structured logging with PII scrubbing, encrypted backups, separate PII/feature stores | Critical |

| Compromised AA/OCEN API credentials | Unauthorized data access at scale | Low–Medium | mTLS, credential rotation, least-privilege service accounts | High |

| Model-input manipulation (adversarial gaming of scores) | Unfair credit decisions, financial loss to REs | Low (thin-file pilot, not open API) | Input validation, anomaly detection on feature distributions, human-in-loop decisioning | Medium |

| Proxy-variable bias creeping into features | Discriminatory outcomes, defeats the product's purpose | Medium | Explicit feature-exclusion list, fairness gate before every model promotion, independent audit | Critical |

| Insecure SHG/FPO manual-ingestion pathway | Data integrity/tampering at the weakest link (manual entry) | Medium | Field-level validation, dual-entry or spot-check reconciliation, audit log on manual edits | Medium |

| Dependency/supply-chain vulnerabilities | RCE, data exposure | Low–Medium | Automated dependency scanning in CI, pinned versions | Medium |

| SSRF via geospatial/vendor connector | Internal network exposure | Low | Allow-list outbound domains, connector runs in a restricted network segment | Medium |

| Bank Sakhi-assisted device compromise (shared/public devices) | Unauthorized access to borrower sessions | Medium | Short session TTLs, explicit logout flows, no persisted credentials on assisted devices | Medium |

---

## 14. Privacy & Compliance

*(Engineering framing of the source report's §12 regulatory analysis — not legal advice; validate with counsel.)*

**Applicable frameworks (per the source report's own citations):** RBI Digital Lending Directions (LSP/RE model, DLG cap at 5%), DPDP Act 2023 + Rules 2025 (consent, breach notification, retention), Account Aggregator Master Directions (FIU role, "data-blind" AA design), Credit Information Companies Act 2005 (bureau data). **Not applicable:** HIPAA (no health data), PCI-DSS (CreditTech never touches payment card/fund flows — ADR/assumption #1), children's-data-specific rules (borrowers are adults).

**Engineering implications:**

- Consent capture must be free, specific, informed, unconditional, revocable — build the revocation path *before* launch, not as a fast-follow.

- Data-breach reporting within regulatory timelines requires an incident-response runbook to exist before go-live, not be improvised during an incident.

- Data minimisation is enforced at the schema level (explicit feature-exclusion list, §8.1) — this is a design decision, not a policy document.

- Consent records retained ≥7 years — plan storage/retention lifecycle accordingly from the schema design in §7.

---

## 15. Testing Strategy

```text

Unit tests            — highest volume; every connector, feature transform, scoring function

Integration tests      — consent → ingestion → scoring → decisioning, with mocked external APIs

API tests               — contract tests against AA/OCEN/geospatial connector interfaces

ML tests                 — data validation tests, model regression tests (score shouldn't shift

                            wildly on a fixed test set between versions without explanation),

                            fairness-gate tests (automated, blocking promotion on failure)

End-to-end tests          — full pilot journey on staging, using synthetic borrower profiles

Load tests                 — light; validate the system comfortably handles the pilot's peak

                            (20–30 applications/day), not a hypothetical 10K/day

Security tests               — dependency scanning, basic auth/RBAC test suite

```

At pilot scale, prioritize integration and ML/fairness tests over exhaustive unit coverage — the riskiest failure mode is a silently-degraded or silently-biased score, not a crashed service.

---

## 16. Reliability Engineering

| Component | If it fails... | Mitigation |

|---|---|---|

| AA / geospatial / SHG / bureau connector | Missing data source | Graceful degradation — proceed with reduced confidence, never hard-fail (core design principle) |

| Database | No new applications can be processed | Managed DB with automated backups + point-in-time recovery; single-region acceptable at pilot scale |

| Model service | No scores generated | Fallback logistic scorecard path (ADR already designed for this — it's not an afterthought) |

| Third-party API outage (any rail) | Delayed/partial scoring | Timeouts + retries with backoff on each connector, circuit breaker if a rail is down for an extended period |

| Deployment failure | Downtime | Staging smoke tests + manual promote gate; simple rollback to last-known-good container image |

| Bad config/model push | Wrong or unfair scores at scale | Model promotion requires passing the fairness gate (§8.3) as a hard CI check, not a manual sanity glance |

Do not build circuit breakers, dead-letter queues, or multi-region failover for the pilot — the traffic and stakes don't justify it yet; a well-tested retry/timeout/fallback pattern on each connector is sufficient.

---

## 17. Observability

**Logs:** application errors, connector call outcomes (success/timeout/fail), consent lifecycle events, model-version served per score. **Never log:** raw Aadhaar numbers, full bank statements, raw satellite imagery paths with PII correlation, unmasked phone numbers.

**Metrics:** request rate/error rate/latency per connector; score-availability-under-partial-data rate; approval rate by segment (feeding the fairness monitor); database connection saturation.

**Tracing:** not yet necessary at monolith + single-region scale — revisit once the Data Aggregation Service is extracted (ADR-1 migration path).

**Alerting (human-action-required only):** any connector down > 30 minutes; fairness-gate breach on a promoted model; consent-revocation not propagated within SLA; unusual override rate by a loan officer (possible model distrust or process issue worth investigating, not necessarily a system bug).

---

## 18. Performance

| Potential bottleneck | Why | Detect via | Initial fix | Scaling fix |

|---|---|---|---|---|

| Slow geospatial API | External vendor latency, unpredictable | Per-connector latency metric | Async call with generous timeout + confidence-weighted fallback | Cache per-plot results (land doesn't move) |

| DB connection contention (dashboard vs scoring) | Shared single instance | Connection pool saturation metric | Separate read replica for dashboard queries | Logical DB split (§7.2) |

| Manual SHG/FPO ingestion bottleneck | Human data-entry step | Turnaround-time tracking on this step specifically | Simple validation UI to reduce entry errors/re-work | API integration once SHG federations digitize (assumption #8) |

---

## 19. Scaling Roadmap

**Stage 0 — Local development:** Docker Compose (Postgres + FastAPI + mocked connectors), synthetic borrower data.

**Stage 1 — MVP (the 4–5 village pilot, 750–1,250 borrowers):** As architected in §4–6. Single-region managed cloud, modular monolith, one shared model.

**Stage 2 — 1K–10K borrowers (post-pilot single-state expansion):**

- Traffic assumptions: still low absolute volume, but more sites within one state

- Data assumptions: enough repayment outcomes now exist to retrain on real (not proxy) labels

- Architecture: same monolith; extract Data Aggregation Service if connector volume/latency starts contending with the scoring path

- Infra: add a read replica; introduce basic caching for geospatial lookups

- Expected bottleneck: manual SHG/FPO ingestion becomes the visible throughput ceiling

- Required change: prioritize SHG/FPO API integration (per open question #5)

- Cost drivers: geospatial API query volume, AA consent-fee volume

- What NOT to change yet: no Kubernetes, no multi-region, no microservices split beyond the one extraction above

**Stage 3 — 10K–100K borrowers (multi-state):**

- Architecture: extract Scoring Service + Model Registry as an independent internal service (multiple states may need region/state-specific model variants)

- Infra: partition large tables by state; introduce ULI integration now that ecosystem adoption may have matured (revisit open question #4/#9)

- Expected bottleneck: single-model-fits-all assumption breaks down across very different agro-climatic zones/states

- Required change: per-region model variants sharing a common feature pipeline

- Operational complexity: now justifies a small dedicated platform/SRE function

**Stage 4 — 100K–1M borrowers:**

- Caching, read replicas, and queue-backed async processing become mandatory, not optional

- CDN for the borrower app's static assets; load balancing across multiple backend instances

- Database: consider Kubernetes only now, if operational complexity (many services, need for fine-grained autoscaling) genuinely justifies it — otherwise stay on managed containers

- Multi-RE routing logic becomes a first-class module (multiple partner lenders per state)

**Stage 5 — 1M borrowers (national-scale ambition):**

- Service decomposition beyond scoring (consent, ingestion, decisioning as independent services)

- Event-driven architecture for the ingestion/feedback loop (repayment data flowing back into training)

- Dedicated ML infrastructure (proper feature store, scheduled + drift-triggered retraining pipeline, canary model rollout)

- Multi-region consideration within India for latency and disaster recovery

**Stage 6 — 10M+ borrowers:**

- Full distributed-systems posture: regional architecture aligned to India's state-level regulatory variation, advanced data architecture (warehouse + lake split), formal capacity planning, disaster recovery with tested RTO/RPO, dedicated reliability engineering function

**Evidence gate for every transition:** don't move to the next stage because a stage number sounds impressive — move when the *current* stage's stated bottleneck is measured and confirmed, not anticipated.

---

## 20. Cost Engineering

```text

Top 5 cost drivers (pilot → scale):

1. Geospatial/EO data licensing (per-hectare or per-query — scales directly with borrower count)

2. Account Aggregator per-consent fees (scales directly with applications)

3. Core engineering team cost (largest single line item at pilot stage — see source report §14)

4. Cloud infra & MLOps (grows step-wise, not linearly, as you cross scaling stages)

5. Field operations (Bank Sakhi/BC coordination) — a real cost the tech stack doesn't eliminate,

   only makes more efficient

```

```text

Users ↑ → Applications ↑ → Geospatial + AA API calls ↑ → Compute (ingestion/scoring) ↑

   → DB load ↑ → Read replicas/caching required → Infra cost step-changes upward

```

Per the source report's own pilot cost table (§14), the indicative pilot budget is **₹1.85–2.9 crore** for 9–12 months across 4–5 sites, excluding credit capital (disbursed by the partner RE, not CreditTech). Engineering team cost (₹85–120 lakh) and geospatial/AA integration (₹23–45 lakh combined) dominate — which is exactly why ADR-4 and ADR-5 (avoid dedicated model-serving infra and Kubernetes) matter: they're not academic simplicity preferences, they directly protect this budget.

---

## 21. Cost vs Scale Decision Matrix

| Problem | Cheap solution | Better solution | Expensive solution | Upgrade trigger |

|---|---|---|---|---|

| Database | Single managed Postgres | + read replica | Sharded multi-region cluster | Read contention measured, not assumed |

| Compute | Managed containers, fixed size | Autoscaling managed containers | Kubernetes | Traffic variance genuinely needs fine-grained autoscaling |

| Geospatial data | Pay-per-query API | Cached per-plot results | Own EO processing pipeline | Query volume makes vendor cost exceed the cost of building/maintaining an in-house pipeline |

| Model serving | In-process | Dedicated internal endpoint | Managed model-serving cluster | Multiple internal services need to call the model, or update cadence increases sharply |

| Fairness monitoring | Weekly batch job | Daily batch job | Real-time streaming monitor | Sample size per segment is large enough for real-time alerts to be statistically meaningful |

| Ingestion (SHG/FPO) | Manual/CSV | Semi-automated (SFTP/scheduled import) | Full real-time API integration | SHG federations digitize and expose APIs (external dependency, not purely a CreditTech decision) |

---

## 22. Build vs Buy

| Subsystem | Decision | Why |

|---|---|---|

| Authentication (Aadhaar e-KYC) | Buy/reuse (certified UIDAI-compliant provider) | Never build KYC yourself — regulatory certification burden alone rules it out |

| AA integration | Buy (licensed NBFC-AA + SDK) | Regulatory requirement; building your own AA is a different, heavily licensed business |

| Geospatial/EO data | Buy (vendor API) unless volume/economics justify build later | Building an EO pipeline is a multi-year specialty (see SatSure's own history); not core to CreditTech's value. **Interim exception (ADR-7, §5):** an open-data fallback (Sentinel-2/GEE) is used only to unblock pilot testing while the vendor contract (E3) is still open — not a reversal of this Buy decision |

| Scoring model | Build | This *is* CreditTech's core IP and differentiator |

| Explainability (SHAP) | Use open-source library | Mature, well-understood, no reason to build |

| Model monitoring/MLOps | Build lightweight in-house at pilot scale; consider a managed platform only past Stage 3 | Managed MLOps platforms are overkill and costly for a handful of model versions over a year |

| Payments/disbursal | Not applicable | CreditTech never touches funds (ADR/assumption #1) |

| Observability | Buy (managed APM) | Not a differentiator, mature managed options are cheap at this scale |

---

## 23. Cloud Strategy

**MVP:** managed public cloud, India region, managed containers (not Kubernetes), managed Postgres, managed object storage. **Reconsider at:** genuine multi-region/DR requirements (Stage 5), or an explicit regulatory mandate for sovereign/government cloud hosting (open question #3) — either of which is a redeploy given containerization from day one, not a rearchitecture.

---

## 24. CI/CD

```text

Git push → Lint → Type check → Unit tests → Integration tests (mocked external APIs)

  → Build container → Dependency/security scan → Deploy staging → Smoke tests

  → Manual promote → Production

```

Branch strategy: trunk-based with short-lived feature branches, PR review required (especially for anything touching the scoring/fairness-gate code). Migrations run as an explicit, reviewed CI step, never auto-applied without a human glance given the regulated-data schema. Feature flags for anything touching the scoring path (e.g., rolling a new model version to one site before all five).

---

## 25. Deployment

**Development:** Docker Compose locally, mocked external connectors so engineers aren't dependent on live AA/geospatial credentials for day-to-day work.

**Staging:** mirrors production topology at smaller scale, uses sandbox/test credentials for AA/OCEN/geospatial vendors where available.

**Production:** single-region managed containers behind a load balancer, blue/green or rolling deploy (simple — no need for canary infrastructure at this traffic), health checks gating traffic cutover, database migrations run before service cutover with a tested rollback script.

---

## 26. Disaster Recovery

| Stage | Backup frequency | RPO | RTO | Rationale |

|---|---|---|---|---|

| MVP (pilot) | Daily automated + point-in-time recovery | ~24h (acceptable — human-in-loop process has its own slack) | Same business day | Pilot scale doesn't justify hot standby cost |

| 10K–100K | Daily + PITR, tested quarterly restore | Hours | Hours | Growing borrower reliance on the system justifies tested restores |

| 1M+ | Cross-region backup replication, tested restores monthly | Minutes–hours | Hours | National-scale reliance on the system for credit access |

---

## 27. Migration Strategy

```text

PostgreSQL (single instance)

  → Read replica

  → Logical partitioning by state

  → Sharding (only if truly necessary at 1M+, per §19 Stage 5)

```

```text

Vendor geospatial API

  → Cached vendor results

  → Own EO pipeline (only if volume/economics clearly justify it — a hard-to-reverse, capital-

    intensive decision; treat it as such)

```

Hardest-to-reverse decisions in this system: (1) becoming a Regulated Entity vs staying LSP/TSP — a legal/business-model decision more than a technical one, but it reshapes every layer; (2) choice of AA partner and geospatial vendor — contractual and data-format lock-in; (3) the initial feature set baked into the first production model — changing core features later requires careful retraining and re-validation against the fairness gate, not a quick patch.

---

## 28. Technical Debt

**Safe to postpone:** dedicated MLOps platform, automated retraining pipeline, multi-RE routing, native offline scoring, tracing infrastructure.

**Dangerous — solve before launch:** PII/feature-store separation, consent-revocation propagation, fairness gate on model promotion, graceful-degradation on all 4 ingestion rails, incident-response runbook.

**Catastrophic — could make scaling extremely painful later:** skipping feature versioning (makes any future retraining un-auditable), allowing geography or other proxy variables into the model "just to see if it helps accuracy" (nearly impossible to fully excise trust damage later, and defeats the product's stated purpose), coupling the scoring model tightly to one geospatial vendor's proprietary feature format (blocks future vendor negotiation/switching).

---

## 29. Common Engineering Mistakes (specific to this product)

Treating the geospatial/AA/bureau connectors as "usually available" instead of "often degraded" — the entire architecture's core innovation (graceful degradation) collapses if this assumption is wrong. Building ULI integration early against an immature, "muted"-adoption ecosystem. Optimizing model accuracy without an equally-weighted fairness gate. Under-investing in the SHAP reason-code localization — a technically correct but untranslated/jargon-heavy reason code fails the product's own KPI (≥80% borrower comprehension). Treating the loan-officer override as noise to suppress rather than signal to monitor (overrides are valuable fairness/trust data). Premature Kubernetes/microservices given team size. Storing PII and model features in the same table "for convenience."

---

## 30. Development Order

```text

1. Regulatory scoping + partner RE / AA / geospatial vendor selection (Phase 0)

2. Data model + consent ledger

3. Core backend skeleton + CI/CD

4. Ingestion connectors (with graceful degradation from day one, not retrofitted)

5. Baseline (logistic scorecard) model + explainability wiring

6. Candidate (XGBoost/LightGBM) model + fairness gate

7. Loan-officer decision interface

8. Fairness/drift monitor + institutional dashboard

9. Testing pass (integration + ML/fairness tests especially)

10. Staging deploy + pilot-representative smoke tests

11. Production deploy at site 1

12. Monitor, iterate, expand to sites 2–5

```

This order front-loads the two things hardest to retrofit safely — graceful degradation and the fairness gate — before the ML model or UI polish, because bolting either on after the fact means re-validating everything built on top of them.

---

## 31. First 7 Days

| Day | Goal | Learn | Build | Result |

|---|---|---|---|---|

| 1 | Regulatory grounding | RBI LSP/RE model, AA framework, DPDP basics | Write a one-page compliance-posture doc | Shared understanding across the team of what CreditTech can/can't do |

| 2 | Repo + infra skeleton | Managed container basics | Repo structure (§10), CI skeleton, cloud accounts | `hello world` deploys to staging |

| 3 | Data model | Postgres schema design for regulated audit trails | Consent + Borrower + DataPull tables | Migrations run cleanly |

| 4 | Consent service | DEPA consent-artifact structure | Onboarding & Consent Service, hash-chained ledger | Can create/revoke a consent record via API |

| 5 | First connector (mocked) | AA API sandbox docs | AA connector against sandbox/mock | Ingests a mock AA transaction history |

| 6 | Baseline model | Logistic scorecard / "5 Cs" framework | Scorecard trained on synthetic/proxy data | Produces a score from a mock profile |

| 7 | Explainability | SHAP basics | Wire SHAP onto the baseline model | Score returns with reason codes |

---

## 32. First 30 Days

```text

Week 1 — Foundations (see §31): regulatory grounding, repo/infra, consent service, first connector, baseline model

Week 2 — Full ingestion: remaining connectors (geospatial, bureau, SHG/FPO manual UI) with graceful

  degradation tested; feature engineering pipeline

Week 3 — Candidate model + fairness gate: train XGBoost/LightGBM, build the offline fairness

  evaluation harness, wire model registry

Week 4 — Loan-officer interface + integration: build the decision UI, wire the full consent-to-

  decision flow end-to-end on staging, run the first full pilot-representative test case

```

By day 30: a complete (if unpolished) end-to-end flow runs on staging with synthetic borrowers, and the team has a validated compliance posture, a working baseline+candidate model with a passing fairness gate, and a clear go/no-go read on Phase 0's partner-RE and vendor dependencies.

---

## 33. MVP Definition of Done

```text

[ ] Consent capture, storage, and revocation work end-to-end (DPDP-aligned)

[ ] All 4 ingestion rails integrated (3 automated + 1 semi-manual), graceful degradation tested

[ ] Baseline + candidate models trained, candidate passes the fairness gate

[ ] Every score ships with SHAP-based, localized reason codes

[ ] Loan-officer decision interface functional, decisions logged with override tracking

[ ] Fairness/drift monitor running on a weekly batch cadence

[ ] Grievance/appeal channel functional with SLA tracking

[ ] PII and model features architecturally separated

[ ] Encrypted backups + tested restore, India-region hosting confirmed

[ ] CI/CD pipeline green, staging smoke tests passing

[ ] Incident-response runbook exists

[ ] Institutional dashboard shows basic portfolio metrics

[ ] Known limitations documented (ULI not integrated, SHG/FPO ingestion manual, single shared model)

```

---

## 34. Production Readiness Checklist (post-pilot, before multi-state expansion)

**Application:** all MVP-done items above, plus automated SHG/FPO ingestion and ULI integration reassessed.

**Database:** read replica live, partitioning plan drafted for Stage 3.

**Infrastructure:** autoscaling reviewed against real traffic data (not projections), cost dashboard in place.

**Security:** independent penetration test completed, dependency scanning enforced in CI as a blocking gate.

**ML:** retraining cadence formalized (fixed-schedule + drift-triggered, per open question #8), model registry audit-exportable.

**Observability:** alerting tuned against real incident history (not day-1 guesses), on-call rotation defined if team size allows.

**Reliability:** DR restore tested at least once for real, not just documented.

**Compliance:** independent fairness audit completed and published (per source report §12.2), DPDP Consent Manager registration status reviewed against the Nov 2026 window cited in the source report.

**Cost:** actual pilot spend reconciled against the ₹1.85–2.9 crore indicative budget (§14 of source report), unit economics per scored borrower calculated for the first time.

**Documentation:** architecture docs current, runbooks tested by someone who didn't write them.

**Incident response:** at least one tabletop exercise run.

---

## 35. Decision Tree — "Is the system slow / degraded?"

```text

Is a scoring request slow or failing?

        |

        ├── No → Don't change architecture

        |

        └── Yes

             |

             ├── Is one specific ingestion rail slow/down?

             │      └── Confirm graceful degradation is engaging (confidence-weighted partial

             │          score) rather than blocking — if it's blocking, that's a bug, not a

             │          scaling problem

             |

             ├── Is the DB slow?

             │      ├── Missing index? → add it

             │      ├── Dashboard queries competing with scoring path? → read replica (§7.2, Stage 2)

             │      └── Otherwise → check connection pool sizing before assuming you need a

             │          bigger instance

             |

             ├── Is model inference itself slow?

             │      └── Unlikely at this data size for gradient-boosted trees — check for an

             │          accidental N+1 SHAP recomputation or unbatched feature lookups before

             │          assuming you need dedicated serving infra (ADR-4)

             |

             └── Is it a vendor API (geospatial/AA/bureau) that's inherently slow?

                    ├── Cacheable? (e.g., land plot data doesn't change often) → cache it

                    ├── Consistently slow, not just occasionally? → renegotiate SLA with vendor

                    │   or evaluate an alternative provider

                    └── Otherwise → this is expected variance; make sure the graceful-degradation

                        timeout is tuned to it, don't chase a "fix" for normal third-party latency

```

---

## Final Master Roadmap

```text

IDEA (village-level alternative credit scoring)

 ↓

Requirements (§2) — evidence: written functional/non-functional spec, partner RE sign-off

 ↓

Prerequisite Knowledge (§3) — evidence: team comfortable with AA/DPDP/RBI basics

 ↓

Architecture (§4–6) — evidence: ADRs reviewed and accepted

 ↓

Data Design (§7) — evidence: schema reviewed for PII/feature separation

 ↓

MVP (§9, §33) — evidence: first real borrower scored end-to-end at site 1

 ↓

Testing (§15) — evidence: CI green, fairness gate enforced

 ↓

Deployment (§25) — evidence: staging → production promotion works reliably

 ↓

Observability (§17) — evidence: alerts fire on real incidents, not noise

 ↓

Security (§13) — evidence: threat-model mitigations implemented, not just documented

 ↓

Production (§34) — evidence: all 5 pilot sites live and stable for a full season cycle

 ↓

Measure — evidence: pilot KPIs (§13.3 of source report) tracked against target

 ↓

Identify Bottleneck — evidence: a measured, not assumed, constraint (§18, §35)

 ↓

Scale Only Where Necessary (§19) — evidence: the specific Stage-N trigger has actually occurred

 ↓

Production Evolution — evidence: multi-state rollout backed by pilot outcome data, not optimism

```

**What evidence should move you to the next stage, at every step:** a measured bottleneck, a passed fairness/compliance gate, or a completed pilot-season cycle — never a calendar date or a "just in case" instinct alone.