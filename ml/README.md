# CreditTech — Machine Learning Engineering Handbook

Welcome to the **CreditTech ML System**. CreditTech builds alternative-data credit scoring and explainability models for thin-file rural Indian borrowers (farmers, SHG members, artisans).

This document is the authoritative quick-start and reference guide for ML engineers working on this repository.

---

## 1. Directory Structure

```
ml/
├── features/               # Feature schema, 5-Cs mapping & transformation pipeline
│   ├── schema.py           # Authoritative MODEL_FEATURES, PROHIBITED_FIELDS & MONITORED_ONLY_FIELDS
│   └── pipeline.py         # Imputation, categorical encoding, and feature vector extraction
├── training/               # Model definitions & training orchestration
│   ├── datasets.py         # Synthetic cohort generators (SyntheticSHGGenerator) & real benchmark loaders
│   └── scorecard.py        # LogisticScorecard implementation, ScorecardTrainer & calibration math
├── evaluation/             # Model evaluation & explainability
│   ├── explain.py          # Closed-form exact Shapley values (ScorecardSHAPExplainer)
│   └── metrics.py          # AUC, Gini, Kolmogorov-Smirnov (KS), Brier score & reliability bins
└── registry/               # Model lifecycle governance
    ├── registry.py         # ModelRegistry managing candidate -> validated -> active -> retired
    └── store/
        └── registry.json   # Persisted model metadata, metrics, fairness snapshots & SHA-256 hashes
```

---

## 2. Non-Negotiable Rules & Regulatory Guardrails

### Rule 1: Zero PII in Feature Space
* **Prohibited Fields**: `aadhaar`, `name`, `phone`, `caste`, `religion`, `ethnicity`, `health_status`, `disability_status`.
* PII fields are encrypted at the database schema level in the `borrowers` table and are strictly stripped before reaching `FeatureSnapshot`.

### Rule 2: Monitored-Only Fields (Never Model Inputs)
* The fields `gender`, `landholding_band`, `village_id`, `site_type`, and `agro_climatic_zone` are defined in `MONITORED_ONLY_FIELDS` in `ml/features/schema.py`.
* **They must NEVER be used as model inputs.** They are used exclusively by `FairnessAuditor` to monitor demographic parity.

### Rule 3: DPDP Consent Boundary
* Historical loan records may only be used for model training/retraining if `RepaymentRecord.consented_for_retraining == True`.

---

## 3. Mathematical Foundations

### 1. Scorecard Formula
Log-odds are computed across the 21 features in the 5 Cs of credit:
$$\text{logit} = \beta_0 + \sum_{i=1}^{21} \beta_i x_i, \quad P(\text{repay}) = \frac{1}{1 + e^{-\text{logit}}}$$

### 2. 300–900 Score Calibration
The probability of repayment $P(\text{repay})$ is calibrated to an industry-standard 300–900 scale:
$$\text{odds} = \frac{P}{1 - P}$$
$$\text{factor} = \frac{20}{\ln(2)}, \quad \text{offset} = 600 - \text{factor} \cdot \ln(50)$$
$$\text{Score}_{900} = \text{clamp}\Big(\lfloor \text{offset} + \text{factor} \cdot \ln(\text{odds}) \rfloor, 300, 900\Big)$$

Score Bands:
* **EXCELLENT** ($\ge 750$): Auto-recommend `APPROVE`
* **GOOD** ($650 - 749$): Recommend `APPROVE`
* **MODERATE** ($550 - 649$): Recommend `REVIEW` (Discretionary)
* **POOR** ($< 550$): Recommend `REJECT`

### 3. Exact Closed-Form Shapley Values
For linear/logistic models, exact Shapley values are computed analytically without sampling variance:
$$\phi_i = w_i \times (x_i - \mathbb{E}[x_i])$$
where $\mathbb{E}[x_i]$ is the training-set feature mean. Top positive and negative $\phi_i$ values are mapped to human-readable bilingual strings in English and Hindi.

---

## 4. Model Governance & Promotion Gate (P6)

Candidate models cannot be promoted to `active` without passing `ModelPromotionService`:

1. **Performance Minimums**:
   * AUC $\ge 0.60$
   * Gini $\ge 0.20$
   * KS $\ge 0.15$
   * Brier $\le 0.30$
2. **Fairness Gate** (`config/fairness_thresholds.json`):
   * **Gender**: Min approval rate $\ge 35\%$, Max approval gap $\le 20\%$
   * **Landholding Band**: Min approval rate $\ge 30\%$, Max approval gap $\le 25\%$
   * **Geography**: Min approval rate $\ge 25\%$, Max approval gap $\le 30\%$
   * **Officer Override**: Max override rate $\le 50\%$

---

## 5. Developer Commands (Windows PowerShell)

### Run ML Unit Tests
```powershell
.venv\Scripts\pytest tests/test_ml_training.py tests/test_features.py tests/test_explainability.py tests/test_scoring.py tests/test_scoring_e2e_registry.py tests/test_p6_promotion.py tests/test_p6_fairness_gate.py -v
```

### Inspect Models in Registry
```powershell
# Using PowerShell's native Invoke-RestMethod (No jq required):
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/admin/models" -Headers @{"X-Officer-Id"="OFF-001"; "X-Officer-Role"="LOAN_OFFICER"} | ConvertTo-Json -Depth 5

# Or using curl formatted with Python:
curl.exe -s http://127.0.0.1:8000/api/v1/admin/models -H "X-Officer-Id: OFF-001" -H "X-Officer-Role: LOAN_OFFICER" | .venv\Scripts\python -m json.tool
```

### Dry-Run Model Promotion Check
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/admin/models/v1.0.0-logistic/promotion-check" -Headers @{"X-Officer-Id"="OFF-001"; "X-Officer-Role"="LOAN_OFFICER"} | ConvertTo-Json -Depth 5
```

---

## 6. Next Steps for Incoming ML Engineers

1. **Add Probability Calibration**: Wrap models with `sklearn.calibration.CalibratedClassifierCV(method='isotonic', cv=5)` to guarantee empirical reliability.
2. **Implement Stratified 5-Fold Cross-Validation**: Move beyond single 80/20 train/test splits.
3. **Build Weight of Evidence (WoE) Scorecard**: Implement monotonic binning and Information Value (IV) rankings.
4. **Develop XGBoost / LightGBM Challenger**: Train a tree-based challenger and connect `shap.TreeExplainer` to the reason code layer.
5. **Add Benchmark Datasets**: Wire real benchmark datasets (e.g. *Kaggle Home Credit Default Risk* or *Give Me Some Credit*).
6. **Implement Drift Monitoring**: Create a Population Stability Index (PSI) and Characteristic Stability Index (CSI) job to detect seasonal drift.
