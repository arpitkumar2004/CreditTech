# CreditTech — Production-Ready ML Modeling Strategy & Implementation Roadmap
**Target:** First Real Production-Ready Alternative Credit Scoring Model for Rural India  
**Frameworks:** Basel II/III Model Risk Management (MRM) · RBI Digital Lending Guidelines (DLG) · DPDP Act 2023 · 5 Cs of Credit  
**Target Population:** Thin-File & New-to-Credit (NTC) Rural Borrowers (Smallholder/Marginal Farmers, Self-Help Group / SHG Members, Rural Micro-Enterprises)  
**Author:** ML Engineering & Risk Analytics Team  

---

## Executive Summary: The Gap Between Prototype and Production

CreditTech currently operates on a **bootstrapped baseline** (`v1.0.0-logistic`): a logistic scorecard with literature-grounded coefficients trained on synthetic distributions ($n=3,000$). While the engineering plumbing (fast inference, PII isolation, hash-chained consent, and the P6 fairness gate) is complete, **a model trained on synthetic data cannot be deployed to underwrite real institutional capital.**

To create the **first-ever real, regulator-grade, production-ready alternative credit scoring model for rural India**, we must transition across four axes:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 THE PRODUCTION TRANSITION                              │
├──────────────────────┬───────────────────────────────┬─────────────────────────────────┤
│ Dimension            │ Current State (Prototype)     │ Target State (Production-Ready) │
├──────────────────────┼───────────────────────────────┼─────────────────────────────────┤
│ 1. Data Foundation   │ Synthetic SHG Generator       │ Real Multi-Rail Benchmark Anchor│
│                      │                               │ + Open Agri/NDVI Satellite Data │
├──────────────────────┼───────────────────────────────┼─────────────────────────────────┤
│ 2. Feature Pipeline  │ Ad-hoc Median Imputation      │ Monotonic WoE (Weight of        │
│                      │ & Linear Scaling              │ Evidence) + IV Feature Filter   │
├──────────────────────┼───────────────────────────────┼─────────────────────────────────┤
│ 3. Model Family      │ Single Logistic Regression    │ Champion-Challenger:            │
│                      │                               │ Calibrated WoE Scorecard vs.    │
│                      │                               │ Monotonic Constrained LightGBM  │
├──────────────────────┼───────────────────────────────┼─────────────────────────────────┤
│ 4. Validation        │ Single 80/20 Train/Test Split │ Spatial-Group Stratified 5-Fold │
│                      │                               │ CV + Out-of-Time (OOT) Holdout  │
├──────────────────────┼───────────────────────────────┼─────────────────────────────────┤
│ 5. Calibration       │ Theoretical sigmoid math      │ Empirical Isotonic Calibration  │
│                      │                               │ with Brier Score Minimization   │
├──────────────────────┼───────────────────────────────┼─────────────────────────────────┤
│ 6. Explainability    │ Linear feature delta          │ TreeSHAP / KernelSHAP with      │
│                      │                               │ Actionable Counterfactuals      │
├──────────────────────┼───────────────────────────────┼─────────────────────────────────┤
│ 7. Drift Monitoring  │ Point-in-time snapshot        │ Automated Seasonal PSI/CSI      │
│                      │                               │ & Satellite Crop Health Loop    │
└──────────────────────┴───────────────────────────────┴─────────────────────────────────┘
```

---

## 1. Strategy 1: The Dual-Track Real Data Foundation

### The Rural Data Dilemma
True repayment outcomes for unbanked Indian farmers cannot be downloaded from an open API. If we wait 12 months for pilot loan cycles to mature before building a model, the project stalls. Conversely, if we train only on synthetic data, our AUC numbers are fictional.

### The Solution: A Two-Anchor Grounding Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DATA FOUNDATION ARCHITECTURE                       │
│                                                                             │
│  TRACK A: Real Behavioral Proxy Benchmark      TRACK B: Real Agri-Ecological│
│  (Kaggle Home Credit / Give Me Some Credit)    (Sentinel-2 NDVI & IMD Rain) │
│  ├── Real repayment & default curves           ├── True village distributions│
│  ├── Real non-linear interaction patterns      ├── Spatial variance across   │
│  └── Real class imbalance (8-10% default rate) │   districts & crop seasons  │
│                                                                             │
│                                      │                                      │
│                                      ▼                                      │
│               FUSED SYNTHETIC-REAL CALIBRATION ENGINE                       │
│               • Transfer marginal relationships to rural schema             │
│               • Anchor base-rate probabilities against RBI NPA norms (6-8%) │
│               • Validate feature boundaries with NABARD e-Shakti benchmarks │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Step 1.1: Formal Target Variable Definition ($Y$)
A production credit model requires an unambiguous, legally auditable definition of default:
$$\text{Default } (Y = 1) \iff \text{Days Past Due (DPD)} \ge 90 \text{ within 12 months post-disbursal}$$
* **Agricultural Caveat**: For single-harvest crop loans (Kharif or Rabi bullet repayments), default is defined as **failure to service interest within 30 days of harvest plus zero principal repayment by the end of the second subsequent agricultural season** (aligning with RBI Master Circular on Agricultural Advances).
* **SHG Caveat**: An internal SHG loan is flagged as default if the borrower misses **3 consecutive monthly group meetings/repayment cycles** without group-ratified emergency leave.

#### Step 1.2: Benchmark Datasets to Ingest Immediately
1. **Home Credit Default Risk Dataset** (`application_train.csv`):
   * *Purpose*: Real-world behavioral cashflow dynamics, previous loan repayment streaks, family dependency burdens.
   * *Implementation*: Activate the dormant loader in [ml/training/datasets.py](file:///d:/CreditTech/ml/training/datasets.py#L110) to benchmark model architecture discriminative power.
2. **Kaggle "Give Me Some Credit" (GMSC)**:
   * *Purpose*: Classic thin-file delinquency dynamics, debt ratio strain, and monthly income volatility.
3. **Copernicus Sentinel-2 & IMD Gridded Rainfall (Rajasthan & MP Pilot Districts)**:
   * *Purpose*: Replace synthetic NDVI numbers with true 10m-resolution multi-spectral vegetation indices across pilot village clusters (e.g., Hanumangarh, Rajasthan).

---

## 2. Strategy 2: Regulator-Grade Feature Engineering (WoE & IV)

In consumer credit, "black-box" continuous scaling is rejected by banking regulators because it hides non-linear risk cliffs. The global banking standard (Basel II/III internal ratings-based approach) requires **Weight of Evidence (WoE) Transformation** and **Information Value (IV)** screening.

### 2.1 Weight of Evidence (WoE) Transformation
Every continuous feature is binned into $k$ statistically distinct buckets (preserving monotonicity with default rate):

$$\text{WoE}_i = \ln \left( \frac{\% \text{ Non-Defaults}_i}{\% \text{ Defaults}_i} \right) = \ln \left( \frac{N_i / N_{\text{total}}}{D_i / D_{\text{total}}} \right)$$

* **Why this is critical for rural India**:
  * Automatically isolates missing values into their own bin without imputing artificial medians (crucial when an Account Aggregator or Bureau pull returns empty).
  * Outlier-resistant: A farmer with 50 acres of arid land won't skew model coefficients.
  * Linearizes the relationship between the feature and log-odds of default.

### 2.2 Information Value (IV) Feature Selection
We evaluate the predictive strength of all 40+ candidate features using Information Value:

$$\text{IV} = \sum_{i=1}^{k} \left( \frac{N_i}{N_{\text{total}}} - \frac{D_i}{D_{\text{total}}} \right) \times \text{WoE}_i$$

#### Production Feature Selection Gate:
| Information Value (IV) | Predictive Power | Production Action |
| :--- | :--- | :--- |
| $< 0.02$ | Unpredictable / Noise | **Drop immediately** |
| $0.02 \le \text{IV} < 0.10$ | Weak Predictor | Retain only if essential for 5-Cs coverage |
| $0.10 \le \text{IV} < 0.30$ | Medium Predictor | **Standard feature inclusion** |
| $0.30 \le \text{IV} < 0.50$ | Strong Predictor | **Priority core signal** |
| $\ge 0.50$ | Suspicious / Target Leakage | Audit for forward-looking leakage |

### 2.3 Novel High-Value Rural Features to Add
1. **Repayment Volatility & Cadence**:
   * `shg_consecutive_on_time_streak`: Number of consecutive months with zero delays.
   * `internal_loan_cycle_count`: Number of successfully closed internal SHG cycles (proven proxy for borrower character).
2. **Agricultural Resilience Proxies**:
   * `ndvi_season_peak_ratio`: Ratio of applicant's farm NDVI to the 5-year historical village mean during flowering stage.
   * `irrigation_resilience_factor`: Composite of water source (Canal/Borewell = 1.0, Rainfed = 0.3) multiplied by rainfall deviation.
3. **Cashflow Volatility**:
   * `aa_inflow_coefficient_of_variation` ($\sigma / \mu$): Measures agricultural income lumpiness vs. steady non-farm rural income.

---

## 3. Strategy 3: Champion-Challenger Modeling Architecture

Never deploy a complex model without benchmarking it against an explainable linear baseline. We mandate a **two-horse race**:

```
                              ┌────────────────────────────────────────┐
                              │       RAW ALTERNATIVE DATA (4 RAILS)   │
                              └────────────────────┬───────────────────┘
                                                   │
                                                   ▼
                              ┌────────────────────────────────────────┐
                              │      DATA SANITIZATION & ZERO-PII      │
                              └────────────────────┬───────────────────┘
                                                   │
                         ┌─────────────────────────┴─────────────────────────┐
                         │                                                   │
                         ▼                                                   ▼
           ┌───────────────────────────┐                       ┌───────────────────────────┐
           │    CHAMPION ARCHITECTURE  │                       │   CHALLENGER ARCHITECTURE │
           │   WoE Logistic Scorecard  │                       │  Monotonic-Constrained    │
           │                           │                       │         LightGBM          │
           ├───────────────────────────┤                       ├───────────────────────────┤
           │ • 100% regulatory legible │                       │ • Captures non-linear     │
           │ • Closed-form Shapley math│                       │   agri-climate thresholds │
           │ • Exact points scorecard  │                       │ • Monotonic constraints   │
           │   (Score = Offset - Factor│                       │   prevent counter-        │
           │    * Σ WoE)               │                       │   intuitive decisions     │
           └─────────────┬─────────────┘                       └─────────────┬─────────────┘
                         │                                                   │
                         └─────────────────────────┬─────────────────────────┘
                                                   │
                                                   ▼
                                      ┌─────────────────────────┐
                                      │   FAIRNESS GATE (P6)    │
                                      │  & PROMOTION ARBITER    │
                                      └─────────────────────────┘
```

### 3.1 Champion: The Basel-Compliant WoE Scorecard
* **Model Class**: `sklearn.linear_model.LogisticRegression(C=0.1, penalty='l1', solver='saga')`.
* **Points Conversion**: Convert log-odds directly into points:
  $$\text{Score} = \text{Offset} + \text{Factor} \cdot \ln(\text{odds})$$
  $$\text{Points}_i = -(\beta_i \cdot \text{WoE}_i + \frac{\beta_0}{m}) \cdot \text{Factor}$$
* **Advantage**: Every point won or lost is printed directly on a physical scorecard sheet that an illiterate farmer can understand through a Bank Sakhi.

### 3.2 Challenger: Monotonic-Constrained LightGBM
* **Model Class**: `lightgbm.LGBMClassifier`.
* **Monotonic Constraints (`monotone_constraints`)**:
  * `shg_repayment_rate`: **+1** (Higher repayment must strictly never decrease credit score).
  * `shg_savings_consistency`: **+1**
  * `income_stability_cv`: **-1** (Higher volatility must strictly never increase credit score).
  * `ndvi_trend_2season`: **+1**
  * `rainfall_deviation_pct`: **-1**
* **Why Monotonicity is Non-Negotiable**: Standard gradient boosted trees can produce non-monotonic anomalies (e.g., predicting that saving ₹5,000 makes a borrower *more* risky than saving ₹4,500 due to leaf splitting noise). Monotonic constraints eliminate this risk completely.

---

## 4. Strategy 4: Spatial-Group Cross-Validation & Zero-Leakage Protocol

In agricultural lending, standard random k-fold cross-validation is a **fatal methodological error**.

### The Spatial-Autocorrelation Trap
If farmers from the same village are split randomly between the training and validation sets, the model learns the village's weather/soil outcome from Farmer A and "cheats" when predicting Farmer B. This produces inflated validation AUCs ($\ge 0.85$) that crash to random chance ($\sim 0.52$) when deployed to an unseen pilot village.

### The Protocol: `GroupKFold` on Village & Season
```python
from sklearn.model_selection import GroupKFold

# Guarantee that no village present in train ever appears in validation:
gkf = GroupKFold(n_splits=5)
for train_idx, val_idx in gkf.split(X, y, groups=villages):
    X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
    y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
    # Model evaluation on completely unseen agro-climatic clusters
```

---

## 5. Strategy 5: Rigorous Probability Calibration

A credit scoring model does not just rank borrowers (discrimination/AUC); it outputs the **Probability of Default (PD)** used by the partner bank to calculate capital reserves under RBI rules.

### 5.1 The Calibration Gap
Raw logistic regression or gradient-boosted outputs are often uncalibrated when trained on imbalanced datasets (`class_weight='balanced'`). A model might output $P=0.50$ when the true empirical default frequency in that bin is only $8\%$.

### 5.2 Implementation: Isotonic Calibration Wrapper
```python
from sklearn.calibration import CalibratedClassifierCV

# Calibrate the classifier using 5-fold cross-validation
calibrated_model = CalibratedClassifierCV(
    estimator=base_estimator,
    method='isotonic', # Use 'sigmoid' if validation sample < 1000
    cv='prefit'
)
calibrated_model.fit(X_val, y_val)
```

### 5.3 Acceptance Criteria for Calibration
1. **Brier Score**: $\text{Brier} = \frac{1}{N} \sum (P_i - Y_i)^2 \le 0.12$.
2. **Hosmer-Lemeshow Goodness-of-Fit Test**: $p > 0.05$ (fails to reject the null hypothesis that observed and expected default rates are equal across deciles).
3. **Reliability Diagram**: Slope of empirical vs. predicted probabilities must fall between $0.90$ and $1.10$.

---

## 6. Strategy 6: Explainability, Actionable Recourse & Counterfactuals

Under the RBI Fair Practices Code, when a loan is rejected, the applicant has a legal right to know **why**.

### 6.1 Unified SHAP Layer
* For the **Champion Scorecard**: Use exact closed-form Shapley values ($\phi_i = w_i(x_i - \mathbb{E}[x_i])$).
* For the **Challenger LightGBM**: Use `shap.TreeExplainer(model, feature_perturbation='interventional')`.

### 6.2 Beyond "Why": Actionable Counterfactual Recourse
Telling a marginal farmer *"Your score is low because your land area is 0.5 acres"* is unhelpful and demoralizing because land area cannot be changed.

The production model must implement **Actionable Recourse**:
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ACTIONABLE RECOURSE ENGINE                        │
├─────────────────────────────────────────────────────────────────────────────┤
│ Borrower Status: REJECTED (Score: 512 / Cutoff: 580)                        │
│ Non-Actionable Drivers (Suppressed from advice): Landholding, Age, District │
├─────────────────────────────────────────────────────────────────────────────┤
│ ACTIONABLE PATHWAY TO APPROVAL (Next Kharif Season):                        │
│  1. Increase monthly SHG savings deposit from ₹200 to ₹500 for 4 months.    │
│     -> Estimated Impact: +38 Score Points                                   │
│  2. Attend 100% of upcoming SHG bi-weekly meetings (current: 65%).          │
│     -> Estimated Impact: +22 Score Points                                   │
│  3. Enroll in PMFBY Crop Insurance for the upcoming sowing window.         │
│     -> Estimated Impact: +15 Score Points                                   │
│                                                                             │
│ Resulting Projected Score: 587 (Band: MODERATE / APPROVE)                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Strategy 7: Threshold Optimization & Economic Cost Matrix

Defaulting to $P=0.50$ as a decision threshold is unacceptable in financial lending. The cutoff must be mathematically derived from the lender's risk appetite:

### 7.1 The Economic Loss Function
Let:
* $L_{\text{FN}}$ = Cost of a False Negative (Approving a borrower who defaults) = Loan Principal $\times$ Loss Given Default ($1 - \text{Recovery Rate}$) $\approx 0.70 \times \text{Principal}$.
* $L_{\text{FP}}$ = Cost of a False Positive (Rejecting a creditworthy borrower) = Foregone Net Interest Margin (NIM) + Borrower Acquisition Cost $\approx 0.08 \times \text{Principal}$.

$$\text{Optimal Cutoff } \tau^* = \frac{L_{\text{FP}}}{L_{\text{FP}} + L_{\text{FN}}} = \frac{0.08}{0.08 + 0.70} \approx 0.1025$$

A borrower with a predicted probability of default greater than $\sim 10.25\%$ must be routed to manual underwriter review rather than automated straight-through processing.

### 7.2 Three-Tier Decision Threshold Policy
1. **Green Channel (Auto-Approve)**: Score $\ge 720$ ($P_{\text{default}} \le 4\%$).
2. **Amber Channel (Officer Review Required)**: Score $580 - 719$ ($4\% < P_{\text{default}} \le 12\%$).
3. **Red Channel (Decline with Actionable Recourse)**: Score $< 580$ ($P_{\text{default}} > 12\%$).

---

## 8. Strategy 8: MLOps, Drift Detection & Closed-Loop Retraining

### 8.1 Seasonal Population Stability Index (PSI)
Rural credit exhibits extreme cyclicality (Kharif harvest in Oct/Nov vs. Rabi harvest in Mar/Apr). We run an automated monthly PSI job:

$$\text{PSI} = \sum_{b=1}^{10} \Big( P_{\text{actual}}(b) - P_{\text{expected}}(b) \Big) \times \ln \left( \frac{P_{\text{actual}}(b)}{P_{\text{expected}}(b)} \right)$$

* **$\text{PSI} < 0.10$**: Baseline stable. No action.
* **$0.10 \le \text{PSI} < 0.25$**: Moderate shift. Alert risk officer; inspect rainfall anomalies.
* **$\text{PSI} \ge 0.25$**: Severe distribution shift. Automated lock on auto-approvals; route all applications to manual review.

### 8.2 The Closed-Loop Retraining Trigger
When pilot repayment data matures:
1. Extract records where `repayment_records.consented_for_retraining == True`.
2. Compute actual default flags ($Y \in \{0, 1\}$).
3. Execute automated candidate model retraining via `ml/training/scorecard.py`.
4. Run `ModelPromotionService` across performance and fairness gates.
5. If passed, promote candidate to `active` with zero system downtime.

---

## 9. Concrete Implementation Roadmap: Step-by-Step Deliverables

Here is the exact implementation schedule to build this model in this repository:

### Phase 1: Data Grounding & Benchmarking (Week 1–2)
- [ ] Ingest Kaggle Home Credit into `data/benchmarks/home_credit/`.
- [ ] Connect `SyntheticSHGGenerator` statistical distributions to Home Credit cashflow correlations.
- [ ] Script a Sentinel-2 NDVI extractor for 5 pilot village coordinates using open Copernicus APIs.
- [ ] Persist exploratory data analysis in `notebooks/01_eda_and_target_definition.ipynb`.

### Phase 2: Feature Store & WoE Transformation (Week 3–4)
- [ ] Implement `ml/features/woe.py`: Automated monotonic binning using `optbinning` or custom quantiles.
- [ ] Generate an automated Information Value (IV) summary report across all 21 features.
- [ ] Persist bin cutoffs and WoE tables in `ml/registry/store/features/woe_v1.json`.

### Phase 3: Model Development & Cross-Validation (Week 5–6)
- [ ] Refactor `ScorecardTrainer` to run **Spatial GroupKFold (k=5)** on village clusters.
- [ ] Build `ml/training/woe_scorecard.py` (Champion Logistic Scorecard).
- [ ] Build `ml/training/gbm_challenger.py` (Challenger LightGBM with monotonic constraints).
- [ ] Apply `CalibratedClassifierCV(method='isotonic')` to both models.

### Phase 4: Model Governance & Promotion (Week 7–8)
- [ ] Compare Champion vs. Challenger across:
  * Discrimination: AUC-ROC, Gini, KS Statistic
  * Reliability: Brier Score, Hosmer-Lemeshow $p$-value
  * Fairness: Demographic Parity Ratio across Gender & Landholding
- [ ] Generate the formal model card: `docs/ml/model_card_v1.md`.
- [ ] Submit challenger to `POST /api/v1/admin/models/{version}/promote` to verify automatic gating.

---

## 10. Summary: The Production Standard

By executing this strategy, CreditTech will not just have an ML script; it will possess **the first regulator-audited, DPDP-compliant, satellite-verified alternative credit scoring engine in India**. 

It protects the partner bank against agricultural systemic risk, complies with RBI transparency mandates, and opens formal banking to thousands of creditworthy rural families.
