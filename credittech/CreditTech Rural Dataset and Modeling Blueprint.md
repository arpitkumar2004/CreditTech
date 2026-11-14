# CreditTech: Rural Dataset and Modeling Blueprint

Prepared for the CreditTech team (Arpit, Aditya, Astha). This is the exact build plan from here: what to fix in the report, what data to generate, every table and column, how to make it realistic, how to validate it, and how to train, explain and report results.

## 1. Ground rules

1. The dataset is **synthetic, calibrated to published Indian aggregates** (NSS 77th round, NABARD Status of Microfinance, PM-Kisan, NRLM norms). Call it that everywhere. Results on it validate the pipeline, not real-world performance.
2. **Generate the label last.** Order: village, household, season and shocks, income and behaviour, the four data rails, then default probability, then the 0/1 label. Never build features from the label.
3. **Honest performance target:** full-model ROC-AUC 0.75 to 0.82, KS 0.35 to 0.50. If any model beats 0.90, treat it as a leakage bug.
4. **Protected attributes** (gender, caste category, age band, landholding band) are stored for fairness audit only. They are never model inputs.
5. One fixed random seed per table so every run reproduces the same files.

## 2. Report problems to fix first (before any new training)

| # | Problem in current report | Fix |
| --- | --- | --- |
| 1 | AUC 0.96 (scorecard) and 0.979 (stacking) on remapped Home Credit + GMSC data look inflated | Re-run on the new dataset; report the honest numbers. Keep the old run only as a clearly labelled proxy benchmark |
| 2 | NDVI and SHG features were mapped using default variance, so the label leaks into features | Features come only from the generator's behavioural and environmental variables |
| 3 | Spatial GroupKFold over 15 villages that were assigned to Kaggle rows | Use leave-village-out CV on villages that carry real shared conditions (rainfall, irrigation, NDVI) |
| 4 | Five different cutoffs (500, 520, 540, 550/650, 600) | One policy: score bands plus one profit cutoff plus one inclusion cutoff, used in every figure |
| 5 | Balanced accuracy and ECE trade-offs differ wildly across models | Report calibration (reliability curve, Brier, ECE) for all five on the same folds |
| 6 | Limitation about proxy mapping is buried | Move it to the Executive Summary and the dataset chapter |

## 3. Timeline and deliverables

| Phase | Work | Output |
| --- | --- | --- |
| 0 | Fix report issues, freeze cutoff policy | Updated chapter 14 and 24 text |
| 1 | Lock anchor table (Section 4) with source links | `anchors.csv` |
| 2 | Write generator (Python, numpy/pandas, seeded) | `generate_dataset.py` |
| 3 | Run validation checks (Section 8) | `validation_report.html` plus plots |
| 4 | Feature engineering (Section 6) | `modeling_features.csv` |
| 5 | Train and benchmark five models plus ablations (Section 9) | Metrics tables, 13 figures |
| 6 | Explainability, fairness, policy and loan-size logic (Section 10) | Reason-code module, fairness logs |
| 7 | Update report and integrate into the app seed pipeline | Final report, demo database |

Suggested folder layout:

```
data/
  raw/            A_borrowers.csv ... H_loans.csv
  latent/         ground_truth_latent.csv   (never used for training)
  processed/      modeling_features.csv
  anchors.csv
  data_dictionary.xlsx
src/ generate_dataset.py  validate_dataset.py  features.py  train.py  explain.py
figures/
```

## 4. Real-world anchors the generator must match

| Quantity | Target value | Source |
| --- | --- | --- |
| Avg monthly income, agricultural household | about Rs 10,218; split wages 4,063, crop 3,798, livestock 1,582, non-farm 641, leasing 134 | NSS 77th round (2018-19) |
| Indebted agricultural households | about 50% | NSS 77th round |
| Avg outstanding loan per agricultural household | about Rs 74,121 | NSS 77th round |
| Share of rural cash debt from institutional sources | about 66% (rest informal) | NSS 77th round |
| Rural households with under 1 ha | about 83% (70% of agricultural households) | NSS 77th round |
| Agricultural household social mix | OBC 45.8%, SC 15.9%, ST 14.2%, others 24.1% | NSS 77th round |
| Rural literacy (age 7+) | about 73% | NSS 77th round |
| SHG average bank loan outstanding | about Rs 2.7 lakh per SHG | NABARD Status of Microfinance 2022-23 |
| SHG gross NPA | about 1.7% nationally (2025), but 8 to 15% in weak states such as UP and Punjab | NABARD / Lok Sabha reply / press |
| Thin-file share, rural marginal borrowers | about 65% with no bureau tradeline | your report |
| PM-Kisan | Rs 6,000 a year in three Rs 2,000 instalments | Govt. of India scheme |

Before finalising, re-check each number from the source and store the link in `anchors.csv`. Where I use a value from general knowledge (marked *verify*), confirm it.

## 5. Population design (1,000 borrowers)

**Observation window:** Jul 2024 to Jun 2025 (one agricultural year). **Loan disbursed:** Jul 2025. **Outcome window:** Jul 2025 to Jun 2026 (12 months).

### 5.1 Villages (8)

| ID | District type | Agro-ecology | Irrigation | Main crops | Borrowers | Climate risk |
| --- | --- | --- | --- | --- | --- | --- |
| V01, V02 | Chandauli-like (east UP) | Canal-irrigated plains | Canal, tube-well | Paddy, wheat | 130, 140 | Low to medium |
| V03, V04 | Mirzapur-like (UP) | Rain-fed, undulating | Mostly rain-fed | Paddy, pulses, millet | 120, 110 | High (drought) |
| V05, V06 | Paschim Medinipur / Purulia-like (West Bengal) | Lateritic, rain-fed paddy | Rain-fed, some ponds | Paddy, vegetables | 135, 120 | Medium to high |
| V07, V08 | Vidarbha-like (Maharashtra) | Dryland cotton-soy | Rain-fed, borewell | Cotton, soybean, pigeon pea | 115, 130 | High, price risk |

Each village gets its own latent parameters: rainfall anomaly for the year, canal reliability, market distance, mean NDVI shift, and an SHG-health score. These create realistic village-level correlation, which is what makes leave-village-out CV meaningful.

### 5.2 Segments and target default rates

| Segment | Count | Description | Target 12-month default (90+ DPD) |
| --- | --- | --- | --- |
| Marginal farmer | 300 | Under 1 ha, mostly own land | about 10% |
| Small farmer | 150 | 1 to 2 ha | about 7% |
| Tenant / sharecropper | 100 | Leased land (Batai), little or no owned land | about 13% |
| SHG woman member | 300 | NRLM-type SHG; many also farm or run livestock | about 4% (higher in weak-SHG villages) |
| Rural micro-enterprise | 150 | Kirana, dairy collection, repair, tailoring, CHC | about 11% |

Overall default about 8 to 9%. Segment rates are calibrated by tuning each segment's intercept, so overall AUC stays in the target range.

### 5.3 Loan products simulated

| Product | Segment | Amount (Rs) | Tenor | Rate (indicative, *verify*) | Repayment |
| --- | --- | --- | --- | --- | --- |
| Crop input (KCC-type) | Farmers, tenants | 20,000 to 1,50,000 | 9 to 12 months | about 7 to 9% | Bullet at harvest |
| SHG-BLP group loan (split to members) | SHG | 1,00,000 to 5,00,000 per group | 18 to 36 months | about 9 to 12% | Monthly |
| Micro-enterprise working capital | Micro-enterprise | 30,000 to 2,00,000 | 12 to 24 months | about 12 to 18% | Monthly |
| Dairy / livestock | Farmers, SHG | 40,000 to 90,000 | 18 to 36 months | about 9 to 12% | Monthly |

Lender mix: RRB 45%, commercial bank 35%, cooperative 20%.

## 6. Table-by-table specification

All tables join on `borrower_id` (format `B0001` to `B1000`). Village joins on `village_id`.

### Table A: `A_borrowers.csv` (1,000 rows)

| Column | Type | Spec |
| --- | --- | --- |
| borrower\_id | str | B0001..B1000 |
| village\_id | str | V01..V08 |
| segment | cat | marginal, small, tenant, shg, microenterprise |
| age | int | 21 to 65, mean about 40 (SHG women 25 to 55) |
| gender | cat | F for SHG segment; about 12% F among others (audit only) |
| caste\_category | cat | General, OBC, SC, ST using NSS mix (audit only) |
| education\_level | cat | none, primary, secondary, graduate; literacy about 73% |
| household\_size | int | 3 to 9, mean about 4.8 |
| dependents | int | 0 to 6 |
| years\_in\_village | int | 3 to age |
| has\_smartphone | bool | about 65% |
| mobile\_digital\_literacy | cat | assisted, basic, comfortable |
| bank\_account\_age\_months | int | PMJDY-era accounts: 6 to 120 |
| bureau\_tradelines | int | 0 for about 65%; else 1 to 4 |
| bureau\_score\_proxy | int/null | null if thin-file; else 450 to 780 |
| consent\_rails\_granted | int | 0 to 4 (completeness driver) |

### Table B: `B_household_land_crop.csv`

| Column | Spec |
| --- | --- |
| land\_owned\_ha | Lognormal, marginal mean about 0.45, small 1.0 to 2.0, tenant 0 to 0.3, micro 0 to 0.5; cap 4 ha |
| land\_leased\_ha | Tenants 0.3 to 1.2; others mostly 0 |
| irrigated\_share | 0 to 1, driven by village irrigation type |
| irrigation\_source | canal, tubewell, borewell, pond, rainfed |
| primary\_crop, secondary\_crop | By village crop mix |
| cropping\_intensity | 1.0 to 2.2 (higher with irrigation) |
| livestock\_units | 0 to 6 (cattle, buffalo, goat as cow-equivalents) |
| livestock\_value\_inr | 0 to 2,00,000, linked to units |
| owns\_pump\_or\_tractor | bool |
| house\_type | kutcha, semi-pucca, pucca |
| asset\_index | 0 to 100, from house, vehicle, appliance, livestock |
| land\_title\_clear | bool; false for about 30% (informal and ancestral land) |
| has\_crop\_insurance\_pmfby | bool, about 25 to 40% depending on village |
| enterprise\_type, enterprise\_age\_years, enterprise\_monthly\_sales | For micro-enterprise segment only |

### Table C: `C_aa_monthly.csv` (12,000 rows, borrower x month)

Simulates Account Aggregator bank statements in monthly summary form (matches your Sahamati FIU mock format).

| Column | Spec |
| --- | --- |
| borrower\_id, month | Jul 2024 to Jun 2025 |
| total\_credits\_inr | Seasonal: peaks after kharif harvest (Oct to Dec) and rabi (Mar to May); NSS-scaled so annual mean income matches Section 4 |
| total\_debits\_inr | Credits times 0.85 to 1.05, with festival spikes (Oct to Nov) and sowing spikes (Jun to Jul) |
| closing\_balance\_inr | Rolling balance, floor at 0 with occasional overdraft attempts |
| min\_balance\_inr | Monthly minimum |
| upi\_txn\_count | 0 to 40, mean about 8 (higher for micro-enterprise) |
| cash\_withdrawal\_share | 0.3 to 0.95 |
| bounced\_or\_failed\_txn | 0 to 3 |
| days\_balance\_below\_500 | 0 to 30 |
| emi\_or\_loan\_debit\_inr | Existing obligations (about 50% of borrowers have some) |
| informal\_lender\_flag | bool, small share of debits to private lenders |
| dbt\_credits\_inr | PM-Kisan, pensions, MGNREGA, other subsidy credits |

### Table D: `D_shg_ledger.csv`

SHG-level and member-level fields (about 80 SHGs of 10 to 15 members; non-SHG borrowers get null or a flag of not-a-member).

| Column | Spec |
| --- | --- |
| shg\_id, shg\_age\_months | 6 to 120 |
| member\_tenure\_months | 3 to shg\_age |
| meetings\_held\_12m, meetings\_attended\_12m | About 12 to 48 held; attendance 50 to 100% |
| savings\_regularity\_pct | 40 to 100 |
| weekly\_savings\_inr | About 50 to 200 (monthly 200 to 800) |
| member\_savings\_corpus\_inr | Accumulated savings, 1,000 to 40,000 |
| internal\_loans\_taken | 0 to 4 |
| internal\_repayment\_rate | 0.60 to 1.00 (skewed high) |
| shg\_panchasutra\_score | 0 to 5 (regular meetings, savings, inter-loaning, repayment, bookkeeping; *verify* NRLM wording) |
| shg\_grade | A, B, C |
| prior\_bank\_linkage | bool, about 60% |
| shg\_bank\_loan\_repaid\_pct | 0.70 to 1.00 |
| shg\_village\_health | Latent group-level effect shared by members (drives within-group correlation) |

### Table E: `E_utility_digital.csv`

| Column | Spec |
| --- | --- |
| electricity\_connection | metered, flat-rate, none |
| bills\_paid\_12m, bills\_on\_time\_12m | 0 to 12 (only if metered) |
| avg\_days\_late | 0 to 45 |
| arrears\_inr | 0 to 5,000; disputed\_flag small share |
| disconnection\_events\_12m | 0 to 2 |
| mobile\_recharge\_months\_active | 0 to 12 |
| avg\_recharge\_inr | 100 to 400, mean about 220 |
| recharge\_regularity | 0 to 1 |
| lpg\_or\_dth\_payment\_regularity | Optional, 0 to 1 |

### Table F: `F_satellite_weather.csv`

Village-season and borrower-plot level.

| Column | Spec |
| --- | --- |
| village\_id, season | kharif 2024, rabi 2024-25 |
| ndvi\_peak | 0.30 to 0.85 (canal villages higher, rain-fed lower) |
| ndvi\_mean\_season | Peak minus 0.10 to 0.20 |
| ndvi\_anomaly\_vs\_5yr | -0.25 to +0.15 |
| rainfall\_total\_mm, rainfall\_pct\_of\_normal | 60 to 130% of normal |
| dry\_spell\_days\_max | 3 to 35 |
| heat\_stress\_days | 0 to 20 |
| cloud\_gap\_days | 0 to 30 (monsoon gaps; flag for SAR fallback) |
| plot\_ndvi\_peak | Village mean plus plot noise (sd about 0.05) |
| plot\_ndvi\_coverage\_pct | 60 to 100 |

### Table G: `G_govt_social.csv`

| Column | Spec |
| --- | --- |
| pm\_kisan\_instalments\_received\_12m | 0 to 3; eligible farmers only |
| mgnrega\_days\_12m | 0 to 100, mean about 35 (landless and marginal higher) |
| pension\_or\_other\_dbt | bool |
| pmjdy\_account | bool |
| insurance\_pmjjby\_pmsby | bool, about 40% |
| ration\_card\_type | AAY, PHH, none |
| fpo\_member | bool, about 8% |
| fpo\_transactions\_12m | 0 to 20 |

### Table H: `H_loans.csv`

| Column | Spec |
| --- | --- |
| loan\_id, borrower\_id | One loan per borrower |
| product, lender\_type | See Section 5.3 |
| loan\_amount\_inr, tenor\_months, interest\_rate\_pct | As above |
| repayment\_mode | bullet\_harvest, monthly |
| purpose | seeds, fertiliser, livestock, working\_capital, equipment |
| disbursal\_month | Jul 2025 |
| max\_dpd\_12m | 0 to 180 |
| ever\_30dpd, ever\_60dpd | bool |
| **default\_flag** | **1 if 90+ DPD within 12 months, else 0 (the model target)** |
| restructured\_flag | bool |

### Table L: `ground_truth_latent.csv` (validation only)

`latent_repayment_will`, `latent_income_shock`, `latent_health_event`, `latent_crop_failure`, `latent_price_shock`, `true_pd`. Never fed to models. It lets you prove the generator, and later check what the model recovers.

## 7. Generation logic (how the label is made)

1. **Village latents:** draw rainfall anomaly, canal reliability, market distance, SHG health per village.
2. **Household latents:** `repayment_will` \~ Normal(0,1) (character), `skill` \~ Normal(0,1), `assets` from land and livestock, income base from lognormal (sigma 0.5) scaled by segment multiplier (marginal 0.8, small 1.4, tenant 0.75, SHG 0.85, micro 1.3). Income mix follows the NSS split in Section 4.
3. **Shocks (annual, independent):** crop failure probability rises with low rain and low irrigation (rain-fed drought village up to 25%, canal village about 6%). Health event about 8%. Livestock loss about 4%. Price shock higher in V07 and V08.
4. **Rails follow latents, with noise:**
   - AA inflows scale with income, seasonality, and shocks. Volatility rises with rain-fed crops.
   - SHG repayment and attendance track `repayment_will` plus group health plus noise (correlation about 0.5, not 0.9).
   - Utility punctuality tracks `repayment_will` weakly (about 0.3).
   - NDVI tracks village rainfall and irrigation; plot NDVI adds plot noise.
5. **True PD:**

`logit(PD) = b0(segment) - 0.9*repayment_will - 0.6*capacity_z - 0.3*capital_z - 0.2*collateral_z + 0.7*crop_failure + 0.5*health_event + 0.4*price_shock + 0.35*FOIR_z + eps`, with `eps ~ Normal(0, 0.8)`.

6. **Label:** `default ~ Bernoulli(PD)`. Tune each `b0(segment)` by binary search to hit Section 5.2 rates. Check that full-model AUC falls in 0.75 to 0.82. If it goes above, raise `eps` sigma; below, lower it.
7. **Realism layer:**
   - Missingness: bureau fields 65% null by design; AA field-level missing 2 to 3%; utility 5% (unmetered); satellite coverage gaps 3 to 8% in monsoon; SHG null for non-members. Missing-at-random plus a few missing-not-at-random (thin-file borrowers more likely to lack AA).
   - Outliers: lognormal with winsorisation at p1 and p99 (about 1 to 2% genuine tail). No negative incomes, balances below overdraft floor, or impossible ages.
   - Round numbers: loan amounts in Rs 5,000 steps, recharges in Rs 10 steps.

## 8. Dataset validation checklist (must pass before training)

| Check | Pass condition |
| --- | --- |
| Mean monthly household income | Within 10% of NSS anchor |
| Income composition | Each source within 15% of NSS share |
| Indebtedness | 45 to 55% of households with outstanding debt |
| Land distribution | About 70 to 83% under 1 ha |
| Segment default rates | Within 1.5 pts of Section 5.2 |
| Overall default | 8 to 9% |
| Single-feature AUC | None above 0.70 (leakage check) |
| Information Value per feature | Between 0.02 and 0.40; any IV above 0.5 is suspicious |
| Correlations | SHG repayment vs attendance 0.3 to 0.6; no pair above 0.85 |
| Village effects | Default rate spread across villages 4 to 16%; rain-fed villages highest |
| Missingness | Matches Section 7.7 targets |
| Duplicates, impossible values | Zero |
| Reproducibility | Same seed gives byte-identical files |

## 9. Feature store and modeling

### 9.1 The 21 core features (matches your 5-Cs report)

| C | Feature | Rail | Source columns |
| --- | --- | --- | --- |
| Character | shg\_repayment\_rate | SHG | internal\_repayment\_rate |
| Character | shg\_attendance\_pct | SHG | attended / held |
| Character | savings\_regularity\_pct | SHG | savings\_regularity\_pct |
| Character | utility\_on\_time\_ratio | Utility | bills\_on\_time / bills\_paid |
| Character | recharge\_regularity | Utility | recharge\_regularity |
| Character | account\_age\_months | AA | bank\_account\_age\_months |
| Capacity | avg\_monthly\_inflow | AA | mean total\_credits |
| Capacity | inflow\_cv | AA | std / mean of credits |
| Capacity | inflow\_outflow\_ratio | AA | credits / debits |
| Capacity | income\_diversification | AA + B | Herfindahl index across income sources |
| Capacity | foir | AA + H | (existing EMI + new EMI) / monthly inflow |
| Capacity | govt\_transfer\_share | AA + G | dbt\_credits / total\_credits |
| Capital | avg\_daily\_balance | AA | mean closing balance |
| Capital | shg\_savings\_corpus | SHG | member\_savings\_corpus\_inr |
| Capital | livestock\_value | B | livestock\_value\_inr |
| Collateral | effective\_land\_ha | B | owned + 0.5 x leased |
| Collateral | irrigated\_share | B | irrigated\_share |
| Collateral | asset\_index | B | asset\_index |
| Conditions | ndvi\_peak\_mean | Satellite | mean of plot\_ndvi\_peak across two seasons |
| Conditions | rainfall\_pct\_normal | Satellite | rainfall\_pct\_of\_normal |
| Conditions | crop\_insurance\_flag | B | has\_crop\_insurance\_pmfby |

### 9.2 Six extension features (new, to show added value)

`inflow_trend_slope` (12-month regression slope), `seasonal_amplitude` (peak-to-trough ratio), `months_low_balance` (count of months below Rs 500), `ndvi_anomaly` (vs 5-year mean), `rail_completeness_pct`, `thin_file_flag`. Also `loan_to_income_ratio` as a policy feature.

All features are computed in `features.py` from the raw tables with documented formulas, so the same code runs on real AA data later.

### 9.3 Models (keep your five)

1. Standardized Logistic Regression (baseline)
2. WoE Scorecard (champion, monotonic, 300 to 900 scale)
3. Calibrated Random Forest
4. Monotonic Gradient Boosting (HistGradientBoosting with monotonic constraints)
5. Stacking meta-ensemble

### 9.4 Evaluation protocol

| Item | Setting |
| --- | --- |
| Split | Stratified 70/30 hold-out for headline numbers |
| Robust check | Leave-one-village-out CV (8 folds); report mean and range |
| Metrics | ROC-AUC, Gini, KS, PR-AUC, Brier, ECE, accuracy and balanced accuracy at the policy cutoff |
| Calibration | Reliability curve per model; isotonic or Platt where needed |
| Segment analysis | AUC and default rate by segment and by village |
| **Ablation by rail** | Compare: bureau-proxy only; plus AA; plus SHG; plus utility; plus satellite; all rails. This is the proof that alternative data helps |
| Thin-file lift | Approval rate gain at a fixed bad rate vs the bureau-proxy-only model |
| Stability | PSI of each feature and score across villages (below 0.10 pass) |
| Latency | Single-row inference time per model |

## 10. Explainability, fairness and policy

**Explainability**

- WoE points per feature (closed-form) and TreeSHAP for boosted models.
- Top 3 reason codes per applicant in plain English and Hindi, written in simple village language, with one line on what would improve the score (for example, attending more SHG meetings, or paying electricity bills before the due date).
- Counterfactual hint: the smallest feature change that moves the applicant up one band.

**Fairness (audit only)**

- Compare approval rate, default rate among approved, and false-reject rate by gender, caste category, landholding band, and village type.
- Report disparate impact ratio (flag below 0.80) and the gaps at the policy cutoff.
- If a gap is found, fix with feature review or threshold review. Never by feeding protected attributes into the model.

**Policy (one story, used everywhere)**

- Score bands: Reject, Manual Review, Approve. Choose bands from the profit curve with cost inputs Rs 6,500 margin and Rs 42,000 loss per default (from your report).
- One profit-max cutoff and one inclusion cutoff, both computed on the hold-out set and shown on a single figure.
- Loan size recommender: `max_loan = min(product_cap, 40% x monthly_inflow x repayment_months)`, adjusted by score band. Show it next to the score.
- Seasonal repayment schedule suggestion: bullet at harvest for crop loans, monthly for micro-enterprise.
- Officer override stays in the app. Log and measure override outcomes.

## 11. Figures to regenerate (keep your 13, plus 4 new)

Keep: ROC, PR, KS, reliability curves, confusion matrices, score distribution by decision zone, feature importance (SHAP and Gini), profit vs cutoff, fairness parity, fairness frontier, PSI by village, hyperparameter surfaces.

Add: **rail ablation bar chart**, **thin-file lift chart**, **leave-village-out AUC by village**, **dataset realism panel** (synthetic vs NSS anchors).

## 12. Report edits

- Executive Summary: replace AUC claims with the new honest numbers; state clearly that data is synthetic and calibrated to NSS and NABARD.
- Chapter 14: replace the Home Credit and GMSC remapping story with this generator, and keep the old run as an appendix proxy benchmark.
- Chapter 23: new tables and figures; state leave-village-out results.
- Chapter 24 (Limitations): add selection bias (only borrowers who got loans), synthetic-label caveat, and no real repayment history yet.
- Cutoff story: one policy throughout.

## 13. Path to real data (when you test on real borrowers)

1. Keep the same column contract. Map real AA JSON fields into Table C columns, and SHG passbooks (digitised by Sakhis) into Table D.
2. Run in **shadow mode** first: score applicants, do not use the score to decide, compare against actual outcomes.
3. Monitor PSI for each feature against the synthetic baseline. If PSI exceeds 0.25, retrain.
4. First real retrain threshold: about 500 to 1,000 loans with at least 12 months of outcomes.
5. Keep consent, DPDP logging and fairness audits on from day one.

## 14. Approval checklist before generation

- [ ] Villages and segment counts confirmed (Section 5)
- [ ] Anchor values re-verified against sources (Section 4)
- [ ] Cutoff policy decided (Section 10)
- [ ] Target AUC range agreed (0.75 to 0.82)
- [ ] Team agrees to present results as synthetic-data validation
