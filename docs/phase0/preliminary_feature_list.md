# Preliminary Feature List — Alternative Credit Scoring

**Phase 0 Interim Deliverable — Due: Week 4**  
**Status:** DRAFT — Enables SHAP reason-code template library to begin  
**Last Updated:** 2026-08-31

---

## 1. Purpose

This document defines the preliminary feature set for CreditTech's credit scoring model. Features are organized by the "5 Cs" framework (Character, Capacity, Capital, Collateral, Conditions) with seasonal/crop-cycle awareness. Each feature includes its data source, expected availability at pilot launch, and whether it's eligible for SHAP reason-code generation.

---

## 2. Feature Inventory

### 2.1 Character — Repayment Behaviour & Discipline

| Feature ID | Feature Name | Data Source | Type | Description | Reason-Code Eligible | Pilot Availability |
|-----------|-------------|-------------|------|-------------|---------------------|-------------------|
| C001 | `shg_repayment_rate` | SHG/FPO | Float [0,1] | % of SHG internal loans repaid on time | ✅ Yes | Semi-manual CSV |
| C002 | `shg_meeting_attendance_pct` | SHG/FPO | Float [0,100] | % of SHG meetings attended in last 12 months | ✅ Yes | Semi-manual CSV |
| C003 | `shg_savings_consistency` | SHG/FPO | Float [0,1] | Std dev of monthly savings deposits (lower = more consistent) | ✅ Yes | Semi-manual CSV |
| C004 | `shg_membership_years` | SHG/FPO | Int | Years of active SHG membership | ✅ Yes | Semi-manual CSV |
| C005 | `shg_grade` | SHG/FPO | Categorical | NABARD SHG grade (A/B/C/D) | ✅ Yes | Semi-manual CSV |
| C006 | `utility_payment_ontime_pct` | AA/Bureau | Float [0,100] | % of electricity/water bills paid on time | ✅ Yes | AA or Bureau |
| C007 | `existing_loan_repayment_status` | Bureau | Categorical | Current status of any existing formal loans | ✅ Yes | Bureau connector |
| C008 | `upi_transaction_regularity` | AA | Float | Coefficient of variation of monthly UPI transaction counts | ✅ Yes | AA connector |

### 2.2 Capacity — Income & Cash Flow

| Feature ID | Feature Name | Data Source | Type | Description | Reason-Code Eligible | Pilot Availability |
|-----------|-------------|-------------|------|-------------|---------------------|-------------------|
| CA001 | `estimated_crop_income_kharif` | Geospatial + Manual | Float (₹) | Estimated income from Kharif season crops | ✅ Yes | Geospatial + manual |
| CA002 | `estimated_crop_income_rabi` | Geospatial + Manual | Float (₹) | Estimated income from Rabi season crops | ✅ Yes | Geospatial + manual |
| CA003 | `income_stability_cv` | AA/Manual | Float | Coefficient of variation of monthly income over 12 months | ✅ Yes | AA connector |
| CA004 | `monthly_avg_credit_inflow` | AA | Float (₹) | Average monthly credit inflows in bank account | ✅ Yes | AA connector |
| CA005 | `pm_kisan_beneficiary` | Manual/DigiLocker | Binary | Whether borrower receives PM-KISAN transfers | ✅ Yes | Manual entry |
| CA006 | `pm_kisan_regularity` | AA | Float [0,1] | % of expected PM-KISAN installments actually received on time | ✅ Yes | AA connector |
| CA007 | `mandi_sale_frequency` | Manual/e-NAM | Int | Number of mandi sales recorded in last 12 months | ✅ Yes | Semi-manual |
| CA008 | `diversification_index` | Manual | Float | Income source diversification (crops + dairy + labour + etc.) | ✅ Yes | Manual entry |

### 2.3 Capital — Assets & Savings

| Feature ID | Feature Name | Data Source | Type | Description | Reason-Code Eligible | Pilot Availability |
|-----------|-------------|-------------|------|-------------|---------------------|-------------------|
| CP001 | `shg_cumulative_savings` | SHG/FPO | Float (₹) | Total savings deposited with SHG | ✅ Yes | Semi-manual CSV |
| CP002 | `bank_balance_avg_6m` | AA | Float (₹) | Average bank balance over last 6 months | ✅ Yes | AA connector |
| CP003 | `bank_balance_min_6m` | AA | Float (₹) | Minimum bank balance in last 6 months | ✅ Yes | AA connector |
| CP004 | `asset_score` | Manual | Float | Weighted asset index (land + livestock + equipment + dwelling) | ✅ Yes | Manual entry |
| CP005 | `kcc_holder` | Manual/Bureau | Binary | Whether borrower holds a Kisan Credit Card | ✅ Yes | Bureau/manual |
| CP006 | `kcc_utilization_pct` | Bureau | Float [0,100] | % of KCC limit currently utilized | ✅ Yes | Bureau connector |

### 2.4 Collateral — Land & Physical Assets

| Feature ID | Feature Name | Data Source | Type | Description | Reason-Code Eligible | Pilot Availability |
|-----------|-------------|-------------|------|-------------|---------------------|-------------------|
| CL001 | `land_holding_acres` | Manual/DigiLocker | Float | Total cultivable land in acres | ✅ Yes | Manual entry |
| CL002 | `land_ownership_type` | Manual | Categorical | Owned / Leased / Sharecropped / Community | ✅ Yes | Manual entry |
| CL003 | `irrigation_access` | Manual/Geospatial | Binary | Whether land has irrigation infrastructure | ✅ Yes | Geospatial + manual |
| CL004 | `land_quality_ndvi_avg` | Geospatial | Float [0,1] | Average NDVI score over last 2 seasons | ✅ Yes | Geospatial connector |

### 2.5 Conditions — External / Environmental

| Feature ID | Feature Name | Data Source | Type | Description | Reason-Code Eligible | Pilot Availability |
|-----------|-------------|-------------|------|-------------|---------------------|-------------------|
| CO001 | `ndvi_trend_2season` | Geospatial | Float [-1,1] | NDVI trend (improving/declining) over last 2 seasons | ✅ Yes | Geospatial connector |
| CO002 | `rainfall_deviation_pct` | Geospatial/IMD | Float (%) | Deviation from normal rainfall in borrower's block | ✅ Yes | Geospatial connector |
| CO003 | `crop_type_primary` | Manual | Categorical | Primary crop grown (Rice/Wheat/Cotton/Sugarcane/Vegetables/Other) | ✅ Yes | Manual entry |
| CO004 | `crop_insurance_enrolled` | Manual/PMFBY | Binary | Whether enrolled in PMFBY crop insurance | ✅ Yes | Manual entry |
| CO005 | `site_type` | System | Categorical | Village pilot site type (as defined in Village table) | ⚠️ Monitored only | System |
| CO006 | `agro_climatic_zone` | System | Categorical | ICAR agro-climatic zone of borrower's village | ⚠️ Monitored only | System |
| CO007 | `season_tag` | System | Categorical | Current agricultural season (Kharif/Rabi/Zaid) | ✅ Yes | System |

### 2.6 Digital Activity — Behavioural Signals

| Feature ID | Feature Name | Data Source | Type | Description | Reason-Code Eligible | Pilot Availability |
|-----------|-------------|-------------|------|-------------|---------------------|-------------------|
| D001 | `upi_monthly_txn_count` | AA | Int | Average monthly UPI transactions | ✅ Yes | AA connector |
| D002 | `upi_monthly_volume` | AA | Float (₹) | Average monthly UPI transaction volume | ✅ Yes | AA connector |
| D003 | `mobile_recharge_monthly_avg` | AA | Float (₹) | Average monthly mobile recharge amount | ✅ Yes | AA connector |
| D004 | `bank_account_age_months` | AA/Bureau | Int | Age of primary bank account in months | ✅ Yes | AA/Bureau |

### 2.7 Demographic / Control Variables (NOT used as model features)

| Feature ID | Feature Name | Purpose | Used in Model? |
|-----------|-------------|---------|----------------|
| DM001 | `gender` | Fairness monitoring dimension | ❌ Monitored only |
| DM002 | `age` | Included as feature (not protected) | ✅ Yes |
| DM003 | `village_id` | Fairness monitoring dimension | ❌ Monitored only |
| DM004 | `landholding_band` | Fairness monitoring dimension | ❌ Monitored only |

> [!WARNING]
> **Explicitly excluded features:** Caste, religion, health status, ethnicity. Geography (`site_type`, `agro_climatic_zone`, `village_id`) is **monitored for proxy-discrimination** but never used as a raw model feature.

---

## 3. Feature Availability Matrix (Pilot Launch)

| Data Source | Features | Automated? | Fallback |
|------------|----------|-----------|----------|
| AA Connector | C006, C008, CA003–CA006, CP002–CP003, D001–D004 | ✅ Yes (with consent) | Score with lower confidence band |
| Geospatial Connector | CA001–CA002 (partial), CL003–CL004, CO001–CO002 | ✅ Yes (vendor API) | Score with lower confidence band |
| SHG/FPO Ingestion | C001–C005, CP001 | ⚠️ Semi-manual CSV/UI | Manual entry by Bank Sakhi |
| Bureau Connector | C007, CP005–CP006, D004 | ✅ Yes (CIC test env) | Score without bureau features |
| Manual Entry | CA005, CA007–CA008, CL001–CL002, CO003–CO004, CP004 | ❌ Manual | Bank Sakhi-assisted |

---

## 4. Seasonality Tags

Every `FeatureSnapshot` must carry a `season_tag`:

| Season | Months | Crop Cycle |
|--------|--------|-----------|
| `KHARIF` | Jun–Oct | Rice, Cotton, Sugarcane, Soybean |
| `RABI` | Nov–Mar | Wheat, Mustard, Chickpea, Barley |
| `ZAID` | Mar–Jun | Vegetables, Watermelon, Cucumber |

Feature engineering must be **season-aware**: e.g., `estimated_crop_income_kharif` is only meaningful if computed from Kharif-season data.

---

## 5. Version Control

- **Feature version:** `v1.0.0` (pilot launch)
- Every `FeatureSnapshot` record stores `feature_version` to enable reproducibility
- Adding a new feature increments the minor version; changing a feature definition increments the major version

---

*This feature list enables the SHAP reason-code template library draft to begin. Final feature names will be confirmed after Phase 3 model training.*
