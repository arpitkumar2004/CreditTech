# Model Card: CreditTech Alternative Credit Scoring Suite (v1.1.0)
**Date:** 2026-09-07  
**Model Family:** Champion (WoE Scorecard) vs. Challenger (Monotonic GBDT)  
**Standard:** Mitchell et al. (2019) · Basel II/III Model Risk Management · RBI DLG  

---

## 1. Model Details
* **Champion Model (`v1.1.0-woe-scorecard`)**: L1-regularized Logistic Regression over monotonic Weight of Evidence (WoE) binned features with empirical isotonic probability calibration.
* **Challenger Model (`v1.1.0-gbm-challenger`)**: Monotonic-constrained Gradient Boosted Decision Trees (GBDT) with directional constraints on repayment, attendance, and NDVI.
* **Target Variable ($Y$)**: 1 = Repaid on time, 0 = Default (Delinquency $\ge 90$ DPD within 12 months or crop-cycle harvest default).
* **Feature Version**: `v1.0.0` (21 features across Character, Capacity, Capital, Collateral, Conditions).

---

## 2. Quantitative Performance Comparison

| Metric | Champion (`v1.1.0-woe-scorecard`) | Challenger (`v1.1.0-gbm-challenger`) | Promotion Floor Minimum |
| :--- | :--- | :--- | :--- |
| **ROC-AUC** | **0.9096** | 0.9158 | $\ge 0.60$ (PASS) |
| **Gini ($2 \cdot 	ext{AUC} - 1$)** | **0.8192** | 0.8316 | $\ge 0.20$ (PASS) |
| **Kolmogorov-Smirnov (KS)** | **0.6912** | 0.7031 | $\ge 0.15$ (PASS) |
| **Brier Score (Calibration)** | **0.0483** | 0.0464 | $\le 0.30$ (PASS) |
| **PR-AUC** | **0.9930** | 0.9935 | N/A |
| **Spatial GroupKFold** | 5-Fold Village Stratification | 5-Fold Village Stratification | Zero Spatial Leakage |
| **Explainability Method** | Closed-form exact Shapley | TreeSHAP Interventional | Bilingual (EN/HI) |

---

## 3. Demographic Fairness & Parity Audits

Evaluated against the ratified threshold manifest (`config/fairness_thresholds.json`):

### Gender Parity
* **Champion**: Female approval = `98.18%`, Male approval = `97.67%` (Disparity Gap = `2.33%`, Threshold $\le 20\%$)
* **Status**: **PASS (OK)**

### Landholding Band Parity
* **Champion**: Marginal farmers = `97.97%`, Small farmers = `98.23%` (Max Gap = `1.31%`, Threshold $\le 25\%$)
* **Status**: **PASS (OK)**

---

## 4. Ethical Considerations & Caveats
1. **PII Isolation**: No direct identifiers (Aadhaar, name, phone) enter the feature space.
2. **Monitored-Only Fields**: Gender and landholding band are preserved exclusively for disparity auditing and never enter model weights.
3. **Actionable Recourse**: When an applicant is scored below cutoff, non-actionable factors (e.g., land size, age) are suppressed from rejection explanations, and concrete steps (SHG savings streak, PMFBY insurance) are provided.
