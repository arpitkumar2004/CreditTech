# CreditTech — Project Completion & ML Gap Analysis

**Prepared:** 2026-09-03
**Sources reviewed:** `Credittechplanningcontext.md`, `README.md`, `alternative_credit_scoring_research.md`, `docs/phase0/…` through `docs/phase6/production_hardening.md`, `docs/research/external_benchmark_analysis.md`, `ml/**`, `services/core/**`, `tests/**` (111 passing), `config/fairness_thresholds.json`, `ml/registry/store/registry.json`, and the reference repo `nuhaminae/Credit-Risk-Probability-Model-for-Alternative-Data`.
**Nature of document:** Inspection & assessment only. No new implementation. Percentages are computed from an explicit weighting and evidence pointers below (see §9).

---

## 1. Project Purpose

CreditTech is an **alternative-credit decision-support system for rural India** — farmers, SHG members, FPO participants, and rural micro-enterprises who lack a formal bureau file. The system:

1. Collects **explicit, hash-chained consent** from the borrower via a Bank Sakhi (agent-assisted flow).
2. Ingests four data rails in parallel — Account Aggregator (AA), geospatial/NDVI, bureau (if any), and SHG/FPO manual entry.
3. Generates a **calibrated repayment-probability score** with SHAP reason codes in English + Hindi.
4. Presents the score + reasons to a **loan officer**, whose decision (with override reason when they dissent from the model) is exported to a partner Regulated Entity (RE) via a structured handoff.
5. Continuously monitors **fairness** across gender / geography / landholding / officer-override, and runs a **grievance channel** with SLA.

End-to-end flow: `Consent → Ingest(4 rails) → FeatureSnapshot → Score+SHAP → Officer decision → RE handoff → Portfolio + Fairness dashboards → Grievance loop`.

Target users: (a) rural borrower (via Bank Sakhi), (b) loan officer of a partner RE, (c) institutional / regulatory auditor.

---

## 2. Requirement Checklist (against provided project-scope images + plan)

| # | Requirement | Status | Evidence |
|---|---|---|---|
| 1 | Problem statement + village assessment | COMPLETE | `docs/phase0/*`, planning §2 |
| 2 | Stakeholder mapping | COMPLETE | Planning §3, README |
| 3 | As-Is / To-Be process | PARTIAL | Prose in planning doc; no dedicated as-is/to-be diagram artifact |
| 4 | System architecture | COMPLETE | README + `services/core/**` layout |
| 5 | Data architecture / sources | COMPLETE | `ml/features/schema.py`, planning §7, `docs/phase0/preliminary_feature_list.md` |
| 6 | Technology stack | COMPLETE | README, `pyproject.toml`, `docker-compose.yml` |
| 7 | APIs / DPI / integration (Aadhaar, AA, DigiLocker, PM-Kisan, PMFBY, IMD, Bhuvan) | PARTIAL | Connector code + mock server exist; **live sandbox creds absent** (`services/core/ops/smoke.py` returns `BLOCKED`) |
| 8 | Functional modules | COMPLETE | 12 modules under `services/core/` |
| 9 | User journeys (borrower + Sakhi + officer) | PARTIAL | Backend + `unified `apps/borrower-app` portal covers officer + Sakhi + borrower flows; **end-to-end UI flow not verified in browser** |
| 10 | Security / privacy / governance | PARTIAL | PII separation, security middleware, append-only triggers, hash-chain consent — DONE. SSO/OIDC, mTLS, OAuth 2.0 client-credentials, SMS/IVR — **descoped by user**. |
| 11 | 4–5 village pilot | NOT STARTED (external) | Plan §2.2; pilot launch is P7 external work |
| 12 | Cost / resources plan | PARTIAL | Planning doc §5; no updated budget artifact |
| 13 | Literature / evidence review | COMPLETE | `alternative_credit_scoring_research.md`, `docs/research/external_benchmark_analysis.md` |
| 14 | AI/ML & analytics | **PARTIAL — main gap. See §4–§5.** | Only 1 model (logistic scorecard) on synthetic data |
| 15 | Monitoring / KPIs | PARTIAL | Fairness auditor + institutional dashboard + CSV export ship; **PSI drift monitor, data-quality dashboard not implemented** |
| 16 | Scalability / policy / evidence | PARTIAL | Load harness (60-req burst, plan §9 P6 DoD) ships; policy alignment (RBI DLG, DPDP) documented but not independently reviewed |

---

## 3. Phase Audit (P0–P7 against `Credittechplanningcontext.md` §9)

| Phase | Status | Evidence / Gaps |
|---|---|---|
| **P0 Regulatory & Operational Specs** | ✅ **COMPLETE** | `docs/phase0/{consent_record_schema_spec,preliminary_feature_list,re_api_handoff_spec,shap_reason_code_templates,shg_fpo_ui_spec,aa_fiu_onboarding_checklist,bank_sakhi_device_assessment}.md` all present |
| **P1 Setup + Consent Foundation** | ✅ **COMPLETE** | FastAPI scaffold, Alembic, 10 ORM models, hash-chained consent (`tests/test_consent.py`) |
| **P2 Data Ingestion + Sakhi UI** | 🟡 **PARTIAL** | 4 connectors + mock server + orchestrator w/ graceful degradation (`tests/test_ingestion.py`). **Missing:** browser-tested Sakhi journey; live-cred wiring |
| **P3 Logistic Scorecard + SHAP + Registry** | 🟡 **PARTIAL (functional but shallow)** | Runtime `LogisticScorecard`, SHAP explainer, registry, calibration bins. **Only one model**; no baseline comparison; no CV; no ablation; no feature selection; no WoE (see §4–§5) |
| **P4 Officer Decision Interface** | ✅ **COMPLETE** | `/api/v1/decisions/` with override-reason enforcement + audit; React officer dashboard scaffold |
| **P5 Fairness + Grievance + Institutional Dashboard** | 🟡 **PARTIAL** | Fairness auditor across gender/geography/landholding/officer-override; grievance SLA; CSV export; HTML report. **Missing:** ratified thresholds beyond pilot defaults, drift/PSI monitor, disparate-impact intersectional slices |
| **P6 Production Hardening (ML-scoped)** | ✅ **COMPLETE (as scoped)** | Fairness gate + ratified manifest, promotion pipeline (AUC≥0.60, Gini≥0.20, KS≥0.15, Brier≤0.30 + fairness), append-only triggers, PDF (3-tier), DR + parity, security middleware, load harness (`tests/test_p6_load.py` — 60-req 2× pilot peak). **Descoped by user:** SSO/OIDC, mTLS, OAuth 2.0, SMS/IVR. |
| **P7 Production Deploy & Pilot Launch** | ⛔ **EXTERNAL** | Pre-launch checklist + runbooks folder skeleton exist; all real work (production creds, signed vendor contracts, live borrower onboarding, 4-week stability gate) is outside code scope by user instruction |

---

## 4. Current ML System (as it stands today)

| Aspect | What exists | File |
|---|---|---|
| **Model(s)** | Single `LogisticScorecard` (L2 sklearn LogisticRegression, `class_weight='balanced'`, coefficients re-expressed in raw units so runtime scores on un-scaled features). Default hand-authored 5-Cs weights also usable pre-training. | `ml/training/scorecard.py` |
| **Features** | 21 features across 5 Cs (Character, Capacity, Capital, Collateral, Conditions). SHG signals, AA cashflow, geospatial NDVI/rainfall, land, insurance, PM-Kisan. | `ml/features/schema.py` |
| **Feature engineering** | Numeric coercion, `shg_grade` categorical → numeric map, missing→median imputer stored in training report. **No WoE, no polynomial/interaction features, no rolling/seasonal aggregates beyond feature_snapshot inputs.** | `ml/features/pipeline.py`, `ml/training/scorecard.py:198-206` |
| **Training dataset** | `SyntheticSHGGenerator` (n=3,000, seed=42, Bernoulli labels from hand-authored ground-truth logit + N(0,0.5) noise). Optional `HomeCreditLoader` adapter for Kaggle Home Credit CSV — **not shipped**, `available=False` when absent. | `ml/training/datasets.py` |
| **Target / label** | `repay ∈ {0,1}` — simulated (synthetic only). No real repayment outcomes anywhere in repo. | Same file, `.limitations` explicit |
| **Preprocessing** | Median imputation; internal standardisation during fit only, then coefficients converted back to raw-unit space. Stratified 80/20 split. **No cross-validation, no nested CV, no repeated splits.** | `scorecard.py:198-249` |
| **Calibration** | Reliability-bin table (10 bins) in `TrainingReport`. **No Platt/isotonic calibration wrapper is actually applied** at inference (comment claims sigmoid but code path uses raw `LogisticRegression`). | `scorecard.py:181` (docstring vs implementation) |
| **Explainability** | Exact Shapley on a linear model (analytic). Top-5 reason codes rendered EN + HI. | `ml/evaluation/explain.py`, `docs/phase0/shap_reason_code_templates.md` |
| **Fairness** | Registry stores approval-rate disparities by `gender` and `landholding_band` at training time. Live `FairnessAuditor` computes per-period stats. Ratified manifest `config/fairness_thresholds.json`. `FairnessGate` blocks model promotion on breach. | `services/core/monitoring/governance.py`, `services/core/admin/promotion.py` |
| **Model registry** | JSON store on disk (`ml/registry/store/registry.json`), promotion lifecycle `candidate → validated → active → retired`, artifact hash + training-data hash + fairness snapshot. **1 registered model:** `v1.0.0-logistic`, AUC 0.783 / Gini 0.565 / KS 0.442 / Brier 0.189 (synthetic). | `ml/registry/registry.py` |
| **Scoring output** | `POST /api/v1/score/` → `Score` row with `score_100`, `score_900`, confidence band, `sources_used`, reason codes, model + feature version. | `services/core/scoring/router.py` |
| **Evaluation metrics** | AUC, Gini, KS, Brier, reliability bins. **No PR curve, no PR-AUC, no cost-weighted metric, no threshold-tuning artifact, no bootstrap CIs, no confusion matrix at operating point.** | `scorecard.py`, `ml/evaluation/metrics.py` |
| **Limitations (self-declared)** | "AUC/Gini on this data cannot be interpreted as production predictive validity" (registry.json line 78-84) | Explicit and correct |

---

## 5. ML Gap Analysis — What's still required

Evaluated against this project's **objective** (calibrated PD estimate for thin-file rural borrowers, with fairness + explainability guarantees). Only recommendations justified by objective + available data are listed. "Skip" items are recorded and reasoned so we don't do busywork.

| Item | Recommendation | Reason |
|---|---|---|
| Logistic-regression baseline | ✅ **Keep** (already present) | Interpretable, matches scorecard tradition, easy to govern. |
| **WoE / IV scorecard build** | ✅ **ADD** | Industry-standard for credit; provides monotone binning, stability, and IV-based feature ranking. Even for a small model, WoE outputs are what auditors expect. |
| Random Forest | 🟡 **Optional (baseline only)** | Useful as a nonlinear sanity-check; not for production because SHAP on RF is much heavier and reasons harder to justify to a Bank Sakhi. Train once for benchmark, don't deploy. |
| **XGBoost / LightGBM** | ✅ **ADD as challenger** | Standard challenger. Compare AUC/KS/Brier + calibration vs. logistic. Only promote if gain is material AND fairness gate still passes AND SHAP explanations survive review. |
| Deep-learning / NN | ❌ **Skip** | Not justified by dataset size, interpretability constraints, or rural-officer explainability needs. |
| **Probability calibration** | ✅ **ADD** proper wrapper | Current code documents Platt but doesn't apply it. Add `CalibratedClassifierCV(method='isotonic', cv=5)` and persist Brier + reliability-diagram artifact. |
| **Threshold optimisation** | ✅ **ADD** | Currently no documented cut-off. Need cost-weighted or precision-at-recall analysis and a documented approve/refer/reject threshold set. |
| **Class-imbalance handling** | ✅ Already `class_weight='balanced'`; **document + explore** SMOTE and undersampling as ablations. | Real pilot cohort will likely be ~80/20 repay/default; robustness needed. |
| **Cross-validation** | ✅ **ADD** stratified k-fold (k=5) with per-fold AUC/KS/Brier + CI | Single 80/20 split is thin evidence. |
| **Feature selection** | ✅ **ADD** IV-based + L1-regularised path + permutation importance | Currently uses all 21 features regardless of signal. |
| **Ablation studies** | ✅ **ADD** — score with each of {SHG only, +AA, +Geospatial, +Bureau} to quantify each rail's contribution | Directly demonstrates value of alternative-data sources for stakeholders. |
| **Fairness eval** | 🟡 **EXTEND** — currently gender + landholding + geography + officer-override. Add: age band, agro-climatic zone, intersectional (gender × landholding). Add disparate-impact ratio + statistical parity gap CIs. | Regulator ask. |
| **Explainability** | 🟡 **EXTEND** — add global feature-importance report, SHAP dependence plots per top feature, contrastive counterfactual example per reason code | Present is per-instance top-5; audit view is missing. |
| **Model comparison / model-card** | ✅ **ADD** side-by-side card (logistic vs XGBoost vs WoE-scorecard) with metrics + fairness + calibration + inference latency | Required to justify the promoted champion. |
| **Error analysis** | ✅ **ADD** — segmented residuals, worst-decile false-approves + false-rejects with narrative | Currently nothing. |
| **Robustness / sensitivity** | ✅ **ADD** — perturbation tests on NDVI/rainfall (±10%), missing-rail simulation (drop AA, drop Geo), out-of-village generalisation | Rural signals are noisy; must characterise degradation. |
| **Drift monitoring (PSI / KS)** | ✅ **ADD** | Runtime; needed for the 4-week stability gate in P7. |
| **Reproducibility** | 🟡 **EXTEND** — pin numpy/sklearn/pandas versions in registry entry; store random_state per artifact (already done); add `train_scorecard.py --seed` sweep harness | Foundations exist, just need hardening. |

---

## 6. Dataset Plan

| Dataset | Source | Real/Proxy/Synthetic | Target | Features (relevant) | Purpose | Required? | Status |
|---|---|---|---|---|---|---|---|
| **SyntheticSHGGenerator** | `ml/training/datasets.py` | Synthetic | Simulated `repay` | All 21 model features | Pipeline/regression tests, fairness plumbing, promotion-gate rehearsal | Keep | ✅ In-repo |
| **Kaggle Home Credit Default Risk** | `data/home_credit/application_train.csv` (not shipped) | Real (proxy population) | `1 - TARGET` (repay) | 3 fields mapped (income, credit, tenure) | External predictive-signal sanity check for cashflow-style features | Yes — **ADD** | ⚠️ Adapter present, file absent |
| **Kaggle "Give Me Some Credit"** (Fannie/Freddie style thin-file) | External | Real | 90d delinquency | Utilisation, income, dependents | Public benchmark; validates model quality on thin-file segment | Yes — **ADD** | ❌ Missing |
| **Kaggle "Lending Club" 2007-2018 subset** | External | Real | Loan status (Charged Off vs Fully Paid) | Grade, income, DTI, revolving | Alt-data cashflow-style features benchmark | Optional — SHOULD | ❌ Missing |
| **NABARD SHG audit data / SERP AP** | Govt / NABARD publications | Real (aggregated) | Grade / arrear proxy | SHG grade distribution, savings pattern | Priors + validation of SHG feature ranges | Yes — **ADD** if available | ❌ Missing |
| **PM-KISAN beneficiary receipts** | data.gov.in bulk | Real | — (no label) | PM-Kisan regularity | Feature-realism validation | Optional — SHOULD | ❌ Missing |
| **MODIS/Sentinel NDVI + IMD rainfall** | Bhuvan/Copernicus/IMD | Real | — (no label) | NDVI, rainfall_deviation | Feature realism + geospatial coverage test | Yes — MUST for pilot | ❌ Not wired |
| **CreditTech Pilot repayments** | 4–5 village pilot | Real | Real 90-day repay | All | **Ground truth** for the champion model | Yes — MUST (post-pilot) | ⛔ External / future |

**Separation of what each can / cannot prove:**

- **Synthetic** proves *plumbing* only (registry, promotion, fairness gate, SHAP, calibration bins). AUC/KS on it are structurally meaningless.
- **Home Credit / Give Me Some Credit / Lending Club** prove that the *style of model* discriminates on real behavioural data — not that it works on rural Indian SHG borrowers. Use for challenger comparison, not policy setting.
- **NABARD / PM-Kisan / NDVI** prove *feature realism* (ranges, missingness, seasonality) — no target.
- **Pilot repayments** are the only source that can prove *predictive validity for the target population.* Everything else is scaffolding.

---

## 7. Feature Plan

**Current coverage (from `ml/features/schema.py`):** 21 features across 5 Cs. Sources: SHG_FPO, AA, Geospatial, Manual, Bureau (optional).

**Prohibited (explicitly enforced):** Aadhaar, name/phone, caste, religion, ethnicity, health, disability.
**Monitored-only (never model input):** gender, village_id, landholding_band, site_type, agro_climatic_zone.

### Missing / weak features worth adding (all justifiable, none proxying protected attributes):

| Category | Missing feature | Source | Why |
|---|---|---|---|
| **Repayment behaviour** | Rolling 3-month SHG on-time rate, count of prior loan cycles completed, missed-instalment streak | SHG_FPO | Actual repayment history is the strongest signal for character; currently only aggregate `shg_repayment_rate` |
| **Cash-flow behaviour** | AA credit-inflow CV (volatility), max-drawdown month, salary-vs-non-salary ratio, savings-rate proxy (credit − debit)/credit | AA | Currently only mean inflow + regularity |
| **SHG/FPO behaviour** | Group-level aggregate: village SHG default rate, FPO participation months, produce-sale volume via FPO | SHG_FPO | Group signals often beat individual signals in thin-file cohorts |
| **Agri behaviour** | Crop-diversity index (# crops in year), crop rotation, area under horticulture / high-value crop | Manual+Geospatial | Diversification reduces income risk |
| **Seasonality** | Season-adjusted NDVI (vs. 5-yr village mean), rainfall-percentile-in-village-history, crop-calendar phase at application | Geospatial+IMD | Current NDVI is snapshot; percentile framing prevents cross-region bias |
| **Land / farm indicators** | Soil-health card score, irrigation type (canal/borewell/rainfed), micro-irrigation coverage | Manual+Govt | Yield potential proxies |
| **Geospatial / NDVI** | NDVI drought-year deviation, historical crop-loss frequency (PMFBY claims), village distance-to-market | Geospatial | Conditions dimension is under-populated |
| **Bureau / AA-derived** | If any thin bureau signal present: enquiries in 6m, existing-loan-count, DPD 30/60/90 buckets | Bureau | Only if legitimately present; do not fabricate |
| **Business / enterprise** | For micro-enterprise applicants: GSTIN status, months of GST filings, average GST turnover, ONDC seller-rating | GSTN+ONDC | Currently no path for micro-enterprise borrowers |

**Do NOT add** any feature that proxies caste, religion, health, or disability status, and do not add household-name-based village markers that leak identity.

---

## 8. Reference-Project Comparison — `nuhaminae/Credit-Risk-Probability-Model-for-Alternative-Data`

That project builds a probability-of-default model on eCommerce transaction data (RFM-style features, WoE binning, Logistic + Random Forest + Gradient Boosting, Optuna tuning, MLflow experiment tracking, FastAPI serving, Docker).

| Aspect | Reference project | CreditTech today | Verdict |
|---|---|---|---|
| Dataset | Public transactional (Xente-style) | Synthetic + optional Home Credit | **KEEP** ours (rural-context) + **ADD** their idea of a public-benchmark dataset alongside |
| EDA / profiling | Notebooks with ydata-profiling / pandas-profiling | None in repo | **MISSING** — add an EDA notebook per dataset |
| Preprocessing | Sklearn `Pipeline` w/ ColumnTransformer, WoE, imputer, scaler | Ad-hoc imputer, no formal Pipeline | **ADAPT** — refactor to `sklearn.Pipeline` for reproducibility |
| Feature engineering | RFM aggregates, WoE bins, monotone binning | 5-Cs schema, minimal FE | **ADAPT** — bring WoE + IV-based selection |
| WoE | Yes | **No** | **MISSING** — add WoE scorecard as second champion candidate |
| Models | Logistic, Random Forest, Gradient Boosting w/ Optuna | Logistic only | **ADAPT** — add XGBoost as challenger + RF as sanity |
| Evaluation | ROC-AUC, PR-AUC, F1, confusion matrix, calibration | AUC, KS, Gini, Brier, reliability bins | **ADAPT** — add PR-AUC + confusion matrix at operating point |
| Explainability | SHAP TreeExplainer for RF/GB | Exact linear Shapley for logistic | **KEEP** ours; **ADD** SHAP TreeExplainer if XGBoost is added |
| Deployment | FastAPI + Docker | FastAPI + Docker + full API surface | **KEEP** ours (much broader) |
| Versioning | MLflow tracking + registry | Custom JSON registry with fairness snapshot | **KEEP** ours (registry integrates fairness gate, MLflow doesn't natively) — **NOT NEEDED** to swap |
| Testing | Pytest smoke tests | 111 tests, load harness, DR, fairness gate | **KEEP** ours (materially stronger) |
| Monitoring | Basic | Fairness auditor + grievance SLA + institutional dashboard | **KEEP** ours; **ADD** PSI/KS drift monitor which reference has |
| CI/CD | GitHub Actions | Not configured in repo | **MISSING** — add CI workflow (lint + test) |

**Do not copy** the reference project's architecture wholesale — it's an eCommerce PD model, not a rural-consented alternative-data system. Borrow the **notebook discipline, WoE, Pipeline, and challenger models**; ignore the domain and dataset.

---

## 9. Completion Percentages

**Method:** Each area weighted by the number of `Credittechplanningcontext.md` deliverables it contains. Each deliverable is scored 0 (missing) / 0.5 (partial) / 1 (complete) with evidence pointer. Percentage = weighted sum / weighted total.

| Area | Weight | Score | % | Notes |
|---|---:|---:|---:|---|
| Documentation / research | 10 | 9.0 | **90 %** | Planning, phase docs, research, reference-benchmark analysis all present; as-is/to-be diagrams missing |
| System / backend | 25 | 24.0 | **96 %** | 12 modules, 111 tests, load harness, DR, security middleware, promotion gate; SSO/OIDC and OAuth 2.0 descoped by user (not deducted) |
| Frontend / UI | 10 | 5.0 | **50 %** | `unified `apps/borrower-app` portal covers officer + Sakhi + borrower flows; UI flow not verified in browser |
| Data pipeline | 10 | 5.5 | **55 %** | 4 connectors + mock server + orchestrator; live-cred wiring absent; no data-quality dashboard |
| **ML / data-science** | **20** | **8.5** | **43 %** | One logistic model on synthetic data; no CV, WoE, challenger, ablation, feature-selection artefact, calibration wrapper, threshold optimisation, drift monitor |
| Explainability | 5 | 4.5 | **90 %** | Exact Shapley + bilingual reason codes; global/audit view missing |
| Fairness / governance | 5 | 4.5 | **90 %** | Ratified manifest + FairnessGate + promotion pipeline + audit trail; intersectional & CI-bounded metrics missing |
| Testing | 5 | 4.5 | **90 %** | 111 tests + load harness; no e2e browser tests; no property-based tests |
| Deployment readiness | 10 | 3.0 | **30 %** | Docker + compose exist; production creds absent; CI/CD missing; secrets management not codified; P7 external by user constraint |

**Overall (weighted):** (0.9·10 + 0.96·25 + 0.5·10 + 0.55·10 + 0.43·20 + 0.9·5 + 0.9·5 + 0.9·5 + 0.3·10) / 100 = **68.5 %**

---

## 10. What I Still Have To Do — Prioritised

### 🔴 MUST DO (blocks any credible "complete alternative-credit-scoring project" claim)

1. **Add proper probability calibration** — wrap `LogisticRegression` in `CalibratedClassifierCV(method='isotonic', cv=5)`, re-persist reliability diagram. *Artifact:* `ml/registry/store/<v>/calibration.json` + PNG.
2. **Add stratified 5-fold CV** and report mean±std for AUC/PR-AUC/KS/Brier. *Artifact:* `TrainingReport.cv_folds`.
3. **Add WoE / IV scorecard** as a second candidate. *Artifact:* `ml/training/woe_scorecard.py` + registry entry `v1.0.0-woe`.
4. **Add XGBoost challenger.** *Artifact:* `ml/training/gbm_challenger.py` + registry entry `v1.0.0-xgb`; SHAP TreeExplainer wired to reason-code layer.
5. **Champion-vs-challenger model comparison + model card.** *Artifact:* `docs/ml/model_card_v1.md` (metrics, fairness, calibration, latency, decision).
6. **Threshold optimisation.** Cost-weighted analysis + documented `approve / refer / reject` cut-offs. *Artifact:* `docs/ml/threshold_policy.md` + `config/decision_thresholds.json`.
7. **Rail-ablation study.** Score with {SHG-only, +AA, +Geo, +Bureau}; report ΔAUC per rail. *Artifact:* `docs/ml/rail_ablation.md`.
8. **Load at least one real public benchmark dataset** (Give Me Some Credit or Home Credit) and train the champion candidates on it. *Artifact:* second row in registry with `kind=real`.
9. **PSI / KS drift monitor** as a scheduled job / batch. *Artifact:* `services/core/monitoring/drift.py` + endpoint.
10. **EDA notebook per dataset** with distributions, missingness, class balance, correlation, target leakage check. *Artifact:* `notebooks/eda_<dataset>.ipynb`.

### 🟡 SHOULD DO (materially strengthens the project)

11. **Intersectional fairness** (gender × landholding, gender × age band) with disparate-impact ratio + parity-gap CIs. *Artifact:* extended `FairnessAuditor`.
12. **Feature selection** — IV ≥ 0.02 filter + L1 path + permutation importance. *Artifact:* `docs/ml/feature_selection.md`.
13. **Robustness tests** — NDVI ±10 %, drop-AA, drop-Geospatial, cross-village holdout. *Artifact:* `tests/test_ml_robustness.py`.
14. **CI workflow** — lint (ruff) + tests + coverage. *Artifact:* `.github/workflows/ci.yml`.
15. **Refactor training to sklearn `Pipeline` + `ColumnTransformer`** for reproducibility.
16. **Add data-quality dashboard** (rail freshness, missingness, mock-vs-live rail source).
17. **Browser-test the Sakhi + officer flows** end-to-end and capture screenshots.

### 🟢 OPTIONAL

18. Random-Forest sanity benchmark (train once, do not deploy).
19. Feature-engineering additions from §7 (rolling SHG features, AA volatility, crop diversity, seasonal NDVI-percentile).
20. Notebook using `nannyml` / `evidentlyai` for a nicer drift report.
21. Convert `unified `apps/borrower-app` portal to a Playwright smoke test.

### ⛔ POST-PILOT (only meaningful after real repayment data lands)

- Refit champion on real pilot outcomes.
- Re-run fairness gate on real cohort.
- Recalibrate probability outputs on real base rate.
- Publish champion refresh + external-auditor sign-off.

---

## 11. Final ML Completion Criteria

The system may be called **"CreditTech Alternative Credit Scoring ML system — COMPLETE"** only when **all** of the following exist and are versioned:

- [ ] **Dataset(s):** at least one synthetic (plumbing) + one real public benchmark (predictive-validity anchor) + documented plan for pilot ground truth.
- [ ] **Target definition:** written, unambiguous (90-day arrears? charge-off?) + reason for choice.
- [ ] **EDA:** notebook per dataset with target leakage check, missingness, class balance, feature distributions.
- [ ] **Preprocessing:** sklearn `Pipeline`, imputer statistics persisted, no train-test leak.
- [ ] **Feature engineering:** documented; WoE bins where applied; IV table.
- [ ] **Baseline:** logistic / WoE scorecard registered with performance minimums.
- [ ] **Candidate challenger(s):** at least XGBoost registered; SHAP TreeExplainer wired.
- [ ] **Model comparison:** side-by-side card, promotion decision recorded with rationale.
- [ ] **Calibration:** isotonic wrapper applied, Brier + reliability diagram in registry.
- [ ] **Fairness:** intersectional slices, parity-gap CIs, ratified thresholds, gate integrated with promotion (already ✅), auditor-friendly export (already ✅).
- [ ] **Explainability:** per-instance top-K (already ✅), global feature-importance report, dependence plots, at least one counterfactual example per top reason.
- [ ] **Validation:** stratified 5-fold CV, bootstrap CIs, at least one holdout on a distinct dataset.
- [ ] **Model registry:** artifact hash, training-data hash, code version, fairness snapshot, calibration, promotion status (already ✅ — extend `code_version`).
- [ ] **Reproducibility:** seed, library versions pinned in registry entry, `train_scorecard.py` re-runs deterministically.
- [ ] **Inference:** API returns score + reasons + model_version + feature_version (already ✅).
- [ ] **Limitations:** stated per registered model (already ✅).
- [ ] **Real-data validation plan:** written procedure for refitting/recalibrating on pilot outcomes (P7 external — plan lives in `docs/phase7/` even if execution is external).

---

## Summary Numbers

- **CURRENT COMPLETION:** **68.5 %**  *(weighted across 9 areas — see §9)*
- **ML COMPLETION:** **43 %**  *(single logistic model on synthetic data; missing CV, WoE, challenger, calibration wrapper, threshold policy, ablation, real-data anchor)*
- **DATA COMPLETION:** **~25 %**  *(only synthetic in-repo; one adapter present but unfilled; no real dataset, no geospatial/NDVI feed, no pilot outcomes)*
- **REMAINING BUILD WORK:** **~31.5 %**  *(mostly ML + data + frontend verification + CI/CD; the descoped items — SSO/OIDC, mTLS, OAuth 2.0, SMS/IVR, live pilot — are not counted as remaining)*

**MOST IMPORTANT MISSING ML WORK:** proper calibration wrapper, cross-validation, WoE scorecard, XGBoost challenger with champion/challenger comparison + model card, threshold policy, rail-ablation, drift monitor, and at least one real benchmark dataset actually loaded.

**DATASETS I NEED TO ADD:** Kaggle Home Credit `application_train.csv` (adapter already present), Kaggle Give Me Some Credit (thin-file benchmark), a real NDVI + IMD rainfall sample for at least the 4–5 pilot villages, plus a written plan for post-pilot repayment ingestion.

**MODELS I SHOULD TRAIN:** (a) Logistic with proper calibration (present but incomplete), (b) WoE scorecard, (c) XGBoost challenger with SHAP TreeExplainer. Optional: RF for sanity comparison only. Skip deep learning.

**TOP 10 REMAINING TASKS:** the ten items under §10 MUST DO.

**FINAL RECOMMENDATION:** The **backend, governance, testing, and hardening layers are strong** (P0–P6 substantively complete; 111 tests; load harness; fairness gate wired to promotion). The **ML science layer is thin** — one model on synthetic data, no cross-validation, no challenger, no calibration wrapper, no threshold policy, no ablation, no real dataset actually loaded. Before this can honestly be called *"a properly completed alternative-credit-scoring project"*, the ten MUST-DO items in §10 must ship, especially **calibration + CV + a real-data anchor + a challenger + a model card + threshold policy + drift monitor**. Everything else (Sakhi UI browser test, CI/CD, intersectional fairness) is meaningful polish but secondary to the ML-science gap.
