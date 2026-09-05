
# External Project Benchmark — Ideas Worth Pulling Into CreditTech

**Purpose:** Compare CreditTech against three public rural-credit/agri-finance projects and pull in only
the ideas that are actually additive to what's already built. Not a rewrite recommendation — CreditTech
is materially further along than all three (working consent ledger, 40+ feature 5-Cs framework, live
ingestion orchestrator, fairness auditing, CI/CD, Terraform baseline). This is a targeted gap list.

**Reviewed:**
1. [agri-access](https://github.com/clchinkc/agri-access) — Indonesia, satellite + foundation-model credit risk, Basel III/SLIK framing
2. [Krishi-Patra](https://github.com/pr4t1kdas-cell/Krishi-Patra-Dynamic-Crop-Finance-Platform) — NABARD hackathon entry, dynamic crop-linked finance, "digital twin" concept
3. [Credit-Risk-Probability-Model-for-Alternative-Data](https://github.com/nuhaminae/Credit-Risk-Probability-Model-for-Alternative-Data) — WoE/IV scorecard modeling discipline, DVC, proxy-label governance

---

## 1. What CreditTech already does better or differently (don't change these)

| Area | CreditTech | The three repos |
|---|---|---|
| Consent/compliance | Cryptographic hash-chained, append-only, DPDP-mapped `ConsentRecord` with revoke/verify/audit endpoints | None have a consent ledger at all |
| Data breadth | 40+ features across 5 Cs (SHG behaviour, AA, bureau, geospatial, digital activity), with explicit fairness-monitoring dimensions and excluded protected attributes | Each repo is single-rail (geospatial-only, or transactional-only) |
| Fairness governance | `FairnessAuditor` computing demographic-parity + override rates across gender/landholding/geography, `DataRetentionWorker` for DPDP purging | Not present in any of the three |
| Infra/CI | Terraform (`infra/`), full GitHub Actions pipeline (lint/type/test/build/deploy/smoke), Docker Compose with in-process mocks for all 4 rails | Krishi-Patra and agri-access are hackathon-grade (no CI, no IaC); the credit-risk repo has CI but no IaC |
| Tamper-evidence | Hash-chain (cheap, no infra) | Krishi-Patra proposes Hyperledger Fabric for the same guarantee |

**Recommendation: do not adopt blockchain.** Krishi-Patra's Hyperledger Fabric idea solves a problem
CreditTech's hash-chained `ConsentRecord` already solves, at a fraction of the operational cost — important
in a low-connectivity rural deployment where running a permissioned-blockchain node network is a real
liability. Keep this as a documented, deliberate decision so it doesn't get re-litigated later.

---

## 2. Gaps worth closing — ranked by effort vs. impact

### 2.1 Post-disbursement dynamic monitoring (from Krishi-Patra) — **highest impact, moderate effort**
**Gap:** CreditTech's `GeospatialConnector` (NDVI, rainfall deviation) is currently only called *once*, at
origination, via `IngestionOrchestrator`. `services/core/monitoring/service.py` only does fairness
auditing + PII retention — there is no loop that re-checks an *active* borrower's crop health during the
loan tenure.

**What Krishi-Patra does that's genuinely novel:** ties loan terms/alerts to *ongoing* satellite-derived
crop condition, not just a point-in-time score at origination.

**Concrete integration:** Add a `CropHealthMonitor` alongside the existing `FairnessAuditor` /
`DataRetentionWorker` classes in `services/core/monitoring/service.py`. Re-run `GeospatialConnector.fetch_satellite_data`
periodically (e.g. weekly during active season) for borrowers with a disbursed `LoanApplication`, diff
against the NDVI/rainfall values captured at scoring time, and:
- Flag officers when NDVI trend crosses a defined deterioration threshold (early-warning, not automated action).
- Auto-suggest a PMFBY insurance-claim workflow when the deterioration pattern matches known crop-loss signatures.
This reuses the connector and consent scope you already have (`ingestion` purpose already covers geospatial
data under active consent) — no new data rail, no new vendor.

### 2.2 Insurance trigger from a static feature to an active workflow — **low effort, real pilot value**
**Gap:** `crop_insurance_enrolled` (CO004) and PM-KISAN fields exist as static scoring inputs only. Neither
Krishi-Patra's "automated insurance generation" idea needs to be built in full — but the *pattern* (turn a
data point you already ingest into an officer-facing action) is worth borrowing at small scale: when 2.1's
monitor detects a deterioration crossing threshold *and* `crop_insurance_enrolled = true`, surface a
pre-filled PMFBY claim-assistance prompt on the officer dashboard. This is a UI/workflow addition on data
that's already flowing, not a new integration.

### 2.3 Open-weight remote-sensing fallback to de-risk the geospatial vendor dependency — **from agri-access**
**Gap:** Phase 0 tracker item **E3 (geospatial vendor contract)** is still `☐ open` and blocks P2's geospatial
connector going live with real credentials. Right now there's a single path: wait for a signed vendor
contract.

**What agri-access does differently:** uses an open-weight foundation model (IBM/NASA Prithvi-EO-2.0) against
free Sentinel/Copernicus imagery instead of a paid vendor API for the satellite-derived features.

**Recommendation:** don't replace the vendor path (a contracted, SLA-backed geospatial vendor is the right
long-term choice for a regulated lending product) — but evaluate an open-data fallback (Sentinel-2 via
Google Earth Engine / Copernicus, feeding the same `NDVI`/`rainfall_deviation_pct` fields your scorecard
already expects) as a **parallel, no-contract path to unblock pilot testing of `GeospatialConnector` and
`land_quality_ndvi_avg` / `ndvi_trend_2season` features** before E3 closes. This turns a hard external
blocker into something engineering can de-risk in parallel, which is exactly the kind of item the Phase 0/1
planning summary flagged as "engineering can proceed against mocks" — this extends that same principle to
real (if lower-SLA) data instead of only synthetic mocks.

### 2.4 WoE/IV encoding — for when the scorecard graduates from deterministic to trained — **from the credit-risk-model repo**
**Gap:** `ml/training/scorecard.py` is explicitly a **pre-pilot, hand-set-weight bootstrap** ("In the absence
of historical repayment data... bootstraps credit scores using a deterministic weighted logistic scorecard").
That's the right call for launch. But there's no documented plan yet for the transition to a *trained* model
once pilot repayment data starts landing — and `pyproject.toml`'s `ml` extra already lists `scikit-learn`,
`xgboost`, `lightgbm`, `shap`, unused so far.

**What the credit-risk repo does well:** Weight-of-Evidence encoding + Information Value feature selection —
the standard, regulator-legible technique for turning binned alternative-data features (which is exactly
what your 5-Cs feature list already is — CV/percentile/binary fields) into an auditable scorecard, explicitly
framed for Basel-style governance.

**Recommendation:** when Phase 3 revisits `ml/training/scorecard.py` with real pilot outcome data, adopt
WoE/IV as the encoding step feeding a trained logistic model (or the XGBoost/LightGBM options already in
the `ml` extra) — it keeps the audit trail the RBI/DPDP consent design already cares about, and slots
directly on top of the existing 5-Cs feature table instead of requiring new features.

### 2.5 Explicit target-variable ("default") definition and proxy-label risk note — **very low effort**
**Gap:** Nowhere in `docs/phase0/*` or the planning docs is "default" formally defined (e.g. DPD90+, missed
Kharif/Rabi cycle repayment, SHG default flag). The credit-risk-model repo is unusually candid about this:
it names its proxy label explicitly and documents the business risk of using a proxy.

**Recommendation:** add a half-page section to `preliminary_feature_list.md` or a new
`docs/phase0/target_variable_definition.md` defining the default proxy CreditTech will train against once
pilot data exists, and naming the known risk (proxy misclassification / regulatory misalignment) up front.
Cheap to write now, and it's exactly the kind of document a NABARD/RBI reviewer or investor will ask for.

### 2.6 DVC for pilot training data — **defer until pilot data exists**
**Gap:** `ml/registry/` is scaffolded but empty. Once real repayment/outcome data starts flowing from the
pilot (feeding 2.4's trained model), there's no dataset/model-artifact versioning plan yet.

**Recommendation:** low priority today (no training data exists yet), but worth a one-line note in the
Phase 3 planning section: adopt DVC (or equivalent) pointed at `ml/registry/` when the first real training
run happens, so model versions are reproducible and auditable — same spirit as the Alembic migration
discipline already in place for the DB schema.

### 2.7 Name-check Basel II/III framing in planning docs — **documentation-only, near-zero effort**
**Gap:** CreditTech's actual design choices already satisfy Basel-style model-risk-management principles
(interpretable model by default, documented reason codes, calibrated 300–900 bureau-equivalent score,
explicit non-use of protected attributes) — but no document says so explicitly. Both agri-access (Basel
III/SLIK) and the credit-risk repo (Basel II) lead with this framing, which reads well to regulators/NABARD/
investors even though the underlying rigor is comparable to what CreditTech already has.

**Recommendation:** add 2–3 sentences to `Credittechplanningcontext.md` or the README mapping current design
choices to Basel II model-risk-management principles (interpretability-over-complexity trade-off, documented
calibration, auditable feature governance). No code change — just makes existing rigor legible externally.

### 2.8 "Digital twin" framing for the officer dashboard UI — **cosmetic, optional**
**Gap:** Krishi-Patra's pitch-level "Crop Digital Twin" concept (a simple visual trend of a farm's satellite-
derived health over time) is a UX idea, not a new data pipeline — CreditTech already ingests the NDVI/rainfall
series that would drive it. Worth considering as a panel in `services/core/templates/dashboard.html` or the
`apps/borrower-app (unified portal, officer routes)` app: a small NDVI/rainfall trend line per borrower, reusing 2.1's monitoring data
once it exists. Not urgent; flagging so it's on the radar for the officer UI pass in apps/borrower-app.

---

## 3. Suggested sequencing

| # | Item | Depends on | Effort | Where it lands |
|---|---|---|---|---|
| 2.5 | Target-variable definition doc | Nothing | Trivial | New doc, this week |
| 2.7 | Basel framing paragraph | Nothing | Trivial | `Credittechplanningcontext.md` / README |
| 2.3 | Open-data geospatial fallback (Sentinel-2/GEE) | Nothing (parallel to E3) | Small | `GeospatialConnector`, unblocks pilot testing ahead of vendor contract |
| 2.2 | Insurance-trigger prompt on officer dashboard | 2.1 | Small | unified portal officer routes, `monitoring/service.py` |
| 2.1 | Post-disbursement `CropHealthMonitor` | Real disbursed loans (Phase 4+) | Medium | `services/core/monitoring/service.py` |
| 2.4 | WoE/IV-encoded trained scorecard | Pilot repayment data | Medium-large | `ml/training/scorecard.py`, Phase 3 revisit |
| 2.6 | DVC for `ml/registry/` | 2.4 | Small | Tooling/CI |
| 2.8 | Digital-twin trend panel | 2.1 | Small, optional | unified portal, `dashboard.html` |

**Explicitly not recommended:** Hyperledger/blockchain (§1), full replacement of the vendor geospatial rail
with a foundation model (§2.3 is a fallback/de-risk path, not a replacement), and Jupyter-notebook-first
development (CreditTech's service-oriented FastAPI structure is already more production-ready than the
notebook-first repos it was compared against).
