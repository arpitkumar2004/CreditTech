# CreditTech — Data Governance, Regulatory Standards & Feature Specification Handbook
**Document Version:** `v2026.09.2`  
**Classification:** Regulatory Compliance & Machine Learning Architecture Standard  
**Governing Authorities & Frameworks:**
* **Reserve Bank of India (RBI):** Digital Lending Guidelines (DLG) · Fair Practices Code for Lenders · Master Direction on Priority Sector Lending (PSL) · Master Circular on Agricultural Advances
* **Digital Personal Data Protection (DPDP) Act 2023:** Statutory Consent Architecture (§6), Purpose Limitation (§8), Right to Correction & Erasure (§12)
* **Basel Committee on Banking Supervision (BCBS):** Basel II/III Internal Ratings-Based (IRB) Model Risk Management (MRM) Framework (aligned with US Fed SR 11-7 / OCC 2011-12)
* **National Bank for Agriculture and Rural Development (NABARD):** Self-Help Group Bank Linkage Programme (SHG-BLP) & e-Shakti Standards
* **The 5 Cs of Credit:** Character, Capacity, Capital, Collateral, Conditions

---

## 1. Executive Summary & Governance Stance

CreditTech is a regulated-finance decision-support technology platform operating as a **Lending Service Provider / Technology Service Provider (LSP/TSP)** for partner Regulated Entities (REs: Commercial Banks, Small Finance Banks, and NBFC-MFIs). CreditTech enables automated, objective credit underwriting for financially active but **bureau-invisible and thin-file rural borrowers** (marginal farmers, Self-Help Group / SHG members, rural artisans, and micro-entrepreneurs).

Under the RBI Digital Lending Guidelines (DLG) and Basel II/III Model Risk Management (MRM) principles, algorithmic credit models cannot operate as uninterpretable black boxes, nor can they ingest arbitrary, unstructured, or predatory personal data. Every dataset, feature, model artifact, and scoring transaction within this repository must adhere to four non-negotiable architectural guardrails:
1. **Strict Zero-PII Isolation:** Direct identity fields are cryptographically encrypted at the persistence layer and barred from entering feature snapshots, training matrices, or model artifacts.
2. **Statutory Consent Binding:** Historical repayment records are strictly gated for model retraining by explicit, revocable DPDP consent.
3. **Monitored-Only Demographic Parity:** Sensitive demographic attributes are mathematically excluded from scoring models and reserved solely for automated fairness audits.
4. **Graceful Multi-Rail Degradation:** No borrower is rejected purely because an external digital rail (e.g. Account Aggregator or Satellite imagery) is momentarily unavailable.

---

## 2. Statutory Compliance & Non-Negotiable Guardrails

### 2.1 Zero PII in Feature Space (DPDP Act 2023 §8 & ADR-2)
Any personal identifier that can directly re-identify a natural person is cryptographically encrypted at the database schema level (`borrowers` table) and is **strictly prohibited from entering feature snapshots, training matrices, or model artifacts**.

#### Prohibited Fields Specification ([ml/features/schema.py](file:///d:/CreditTech/ml/features/schema.py#L69-L74)):
```python
PROHIBITED_FIELDS = frozenset({
    "aadhaar", "aadhaar_ref_hash", "name", "name_encrypted",
    "phone", "phone_encrypted", "caste", "religion", "ethnicity",
    "health_status", "disability_status",
})
```
* **Audit Mandate:** Continuous CI automated tests verify that no column in `PROHIBITED_FIELDS` ever exists in `MODEL_FEATURES` or any DataFrame passed to a trainer.
* **Storage Encryption:** Direct identifiers are encrypted at rest using AES-256-GCM envelope encryption with hardware-backed key rotation.

---

### 2.2 Monitored-Only Fields (Demographic Parity & Subgroup Fairness)
Under the RBI Fair Practices Code and Article 15 of the Constitution of India, credit underwriting must never be conditioned on protected demographic classes or geographic discrimination proxies.

#### Monitored-Only Fields Specification ([ml/features/schema.py](file:///d:/CreditTech/ml/features/schema.py#L76-L80)):
```python
MONITORED_ONLY_FIELDS = frozenset({
    "gender", "landholding_band", "village_id", "site_type", "agro_climatic_zone",
})
```
* **Strict Rule:** These fields are **NEVER model inputs**. They are stored in metadata tables and used exclusively by the [FairnessAuditor](file:///d:/CreditTech/services/core/monitoring/service.py#L47) and [FairnessGate](file:///d:/CreditTech/services/core/monitoring/governance.py#L82).
* **Ratified Disparity Ceilings ([config/fairness_thresholds.json](file:///d:/CreditTech/config/fairness_thresholds.json)):**
  * **Gender Approval Gap:** Maximum approval rate gap $\le 20.0\%$ between Male and Female applicant cohorts (minimum female approval rate $\ge 35.0\%$).
  * **Landholding Disparity:** Maximum approval rate gap $\le 25.0\%$ between Landless/Marginal applicants and Large landholders (minimum marginal approval rate $\ge 30.0\%$).
  * **Geographic Disparity:** Maximum approval rate gap $\le 30.0\%$ across distinct pilot villages / clusters (minimum geographic approval rate $\ge 25.0\%$).
  * **Officer Override Rate:** Human loan officer overrides must not exceed $50.0\%$ in any auditing window to prevent systematic bias reintroduction.

---

### 2.3 DPDP Retraining Consent & Purpose Limitation (DPDP Act 2023 §6, §8, §12)
Under the DPDP Act 2023, personal data collected for loan processing cannot be repurposed for machine learning model training without explicit, informed, and revocable consent.
* **Consent Gating:** Repayment records may only be queried and merged into training datasets if:
  $$\text{RepaymentRecord.consented\_for\_retraining} == \text{True}$$
* **Implementation:** Enforced at the SQL query level in [ml/training/retrain.py](file:///d:/CreditTech/ml/training/retrain.py#L93). Non-consented borrower records are permanently excluded from model retraining matrices.
* **Right to Erasure & Consent Revocation (§12):**
  * If a borrower revokes consent for model retraining, their flag is set to `consented_for_retraining = False` immediately.
  * Their record is automatically purged from all Layer 3 Gold training extracts.
  * Under DPDP §8(2) exemptions for aggregate statistical derived artifacts, existing compiled model weights do not need to be destroyed, but the borrower is barred from all future retraining cycles.

---

### 2.4 Explainability & Actionable Recourse (RBI DLG Mandate)
Under the RBI Digital Lending Guidelines (Principle of Algorithmic Transparency) and the Fair Practices Code for Lenders, rejected or borderline thin-file borrowers have a statutory right to understand why credit was denied and what specific steps can be taken to qualify.

#### Actionable Recourse Architecture ([ml/evaluation/recourse.py](file:///d:/CreditTech/ml/evaluation/recourse.py)):
1. **Partition of Feature Attributes:**
   * **Non-Actionable (Immutable) Attributes:** Features that cannot be reasonably changed by a borrower in the short term must **NEVER** be suggested as recourse. Examples: `land_holding_acres`, `rainfall_deviation_pct`, `agro_climatic_zone`, `gender`, `village_id`, `shg_membership_years`.
   * **Actionable (Behavioral) Attributes:** Attributes within the borrower's control: `shg_meeting_attendance_pct`, `shg_savings_consistency`, `utility_payment_ontime_pct`, `upi_transaction_regularity`, `crop_insurance_enrolled`, `bank_balance_avg_6m`.
2. **Minimal Perturbation Solver:**
   * For borrowers scoring below the approval cutoff ($< 650$), the [CounterfactualRecourseEngine](file:///d:/CreditTech/ml/evaluation/recourse.py#L66) calculates the minimal perturbation vector $\Delta \mathbf{x}$ across actionable dimensions required to lift the projected score to $\ge 650$.
3. **Bilingual Rural Delivery:**
   * Recourse advice is generated simultaneously in English and Hindi (e.g. *"Increase monthly SHG meeting attendance to 90% over the next 3 months"* / *"आगामी 3 महीनों में स्वयं सहायता समूह (SHG) की बैठक उपस्थिति को बढ़ाकर 90% करें"*).

---

## 3. Data Lakehouse Architecture & Tiered Storage Lifecycle

To guarantee complete lineage, reproducibility, and audit readiness, CreditTech implements a **3-Layer Medallion Data Architecture**:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        CREDITTECH 3-LAYER DATA ARCHITECTURE                            │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│   BRONZE LAYER (Raw Landing Zone)                                                      │
│   ├── Account Aggregator FIU JSON (Sahamati)                                           │
│   ├── e-Shakti / NRLM Meeting Registers                                                │
│   ├── Copernicus Sentinel-2 L2A BOA GeoTIFFs                                           │
│   └── Apna Khata / Bhulekh Land Records Extracts                                       │
│       └─► Immutable, append-only, SHA-256 integrity hash, KMS AES-256-GCM              │
│                                                                                        │
│                                   ▼ [ETL & Anonymization]                              │
│                                                                                        │
│   SILVER LAYER (Standardized Feature Store)                                            │
│   ├── Anonymized 21-Feature Vectors (Schema validated via Pydantic)                    │
│   └── Monitored-Only Demographic Metadata (Stored in isolated audit table)             │
│       └─► Zero-PII verified, missing values mapped to explicit bins                    │
│                                                                                        │
│                                   ▼ [Consent Filter & Maturity Gate]                   │
│                                                                                        │
│   GOLD LAYER (Curated Retraining & Evaluation Store)                                   │
│   ├── 12-Month Mature Observation Windows (Matured Repaid/Default labels)              │
│   └── Filter: consented_for_retraining == True ONLY                                    │
│       └─► Spatial GroupKFold Folds for Retraining & Basel Model Card Generation        │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.1 Data Retention & Regulatory Deletion Policies
* **Transaction & Accounting Logs:** Retained for **8 years** following loan closure to comply with the RBI Master Direction on Financial Record Retention and Prevention of Money Laundering Act (PMLA).
* **Earth Observation (EO) Satellite Rasters:** Cached locally for **24 months** per pilot village cluster; older historical raw rasters are offloaded to cold storage with spatial NDVI summary metrics preserved in the feature store.
* **Model Snapshots & Ingestion Checksums:** Retained indefinitely in the [ModelRegistry](file:///d:/CreditTech/ml/registry/registry.py) to enable point-in-time regulatory recreation of historical credit decisions.

---

## 4. Formal Ground-Truth Target Label Specification ($Y$)

Supervised credit risk models require an auditable, legally unambiguous definition of loan default ($Y \in \{0, 1\}$).

### 4.1 Target Label Definitions

| Outcome Class | Numerical Label | Basel II / RBI Regulatory Criterion |
| :--- | :---: | :--- |
| **Repaid / Good** | **$Y = 1$** | Loan fully closed, or currently servicing with **$\text{Days Past Due (DPD)} < 30$** over a 12-month post-disbursal observation window. |
| **Default / Bad** | **$Y = 0$** | Borrower triggers any of the statutory default criteria detailed below. |

#### Statutory Default Trigger Criteria:
1. **General / Microfinance Loans:**
   $$\text{Days Past Due (DPD)} \ge 90 \text{ within 12 months post-disbursal}$$
2. **Agricultural Bullet Loans (Single Harvest Kharif / Rabi):**
   * Failure to service seasonal interest within **30 days post-harvest**, PLUS
   * Zero principal repayment by the conclusion of the **second subsequent agricultural season** (aligning with the RBI Master Circular on Agricultural Advances).
3. **Internal Self-Help Group (SHG) Loans:**
   * Missed **3 consecutive monthly group meetings/repayment cycles** without group-ratified emergency medical/maternity leave.
4. **Restructured / Distressed Loans:**
   * Any loan where the lender has written off principal, settled for a concessional haircut, or restructured terms due to borrower insolvency.

#### Censoring & Windowing Rules:
* **Maturity Window Requirement:** Loans disbursed less than 12 months prior to the training dataset extraction date are **strictly excluded** from training target sets ($Y$) to prevent maturity bias (prematurely labeling active early-stage loans as good).

---

## 5. The 21 Production Feature Specifications (5 Cs of Credit)

The CreditTech feature space consists of **21 authoritative features** grouped into the classical 5 Cs of credit ([ml/features/schema.py](file:///d:/CreditTech/ml/features/schema.py)).

```
                               ┌────────────────────────────────────────────────────────┐
                               │             5 Cs ALTERNATIVE FEATURE SPACE             │
                               └───────────────────────────┬────────────────────────────┘
                                                           │
         ┌───────────────────┬─────────────────────────────┼────────────────────────────┬───────────────────┐
         │                   │                             │                            │                   │
         ▼                   ▼                             ▼                            ▼                   ▼
   ┌───────────┐       ┌───────────┐                 ┌───────────┐                ┌───────────┐       ┌───────────┐
   │ CHARACTER │       │ CAPACITY  │                 │  CAPITAL  │                │COLLATERAL │       │CONDITIONS │
   │ (7 Feats) │       │ (5 Feats) │                 │ (3 Feats) │                │ (3 Feats) │       │ (3 Feats) │
   └───────────┘       └───────────┘                 └───────────┘                └───────────┘       └───────────┘
```

### 5.1 Character (Behavioral Repayment & Community Social Capital)

| # | Feature Name | Data Type | Valid Range | Canonical Source | Monotonic Trend | Description & Transformation Rule | Fallback & Missing Value Handling |
| :-: | :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| 1 | `shg_repayment_rate` | `float` | `0.05` – `1.00` | SHG / FPO | Increasing (Higher = Better) | Ratio of internal SHG loan payments made on time over total scheduled payments (12-month rolling). | Mapped to `Missing` WoE bin if applicant has no prior internal SHG loan. |
| 2 | `shg_meeting_attendance_pct` | `float` | `0.0` – `100.0` | SHG / FPO | Increasing | Percentage of bi-weekly or monthly SHG group meetings attended in person over past 12 months. | Default to village average meeting attendance or `Missing` bin. |
| 3 | `shg_savings_consistency` | `float` | `0.0` – `1.0` | SHG / FPO | Increasing | Ratio of months with required minimum savings deposited without arrears. | Physical register entry verified by Bank Sakhi. |
| 4 | `shg_membership_years` | `int` | `0` – `15` | SHG / FPO | Increasing | Completed years of continuous active membership in an NRLM/NABARD registered SHG. | Clamped at 15 years; 0 if non-member. |
| 5 | `shg_grade` | `categorical` | `A`, `B`, `C`, `D` | SHG / FPO | Categorical | NABARD 10-point SHG group quality rating. Mapped to numeric: `A=1.0, B=0.75, C=0.5, D=0.1`. | If unrated, default to `B` (standard baseline group). |
| 6 | `utility_payment_ontime_pct` | `float` | `0.0` – `100.0` | AA / Bureau | Increasing | Percentage of electricity (DISCOM), water, or LPG utility bills paid on or before due date over last 12 months. | Mapped to `Missing` bin if no utility link available. |
| 7 | `upi_transaction_regularity` | `float` | `0.0` – `1.0` | Account Aggregator | Increasing | Proportion of calendar weeks in last 6 months with at least 1 commercial or retail UPI inflow/outflow. | 0.0 for cash-only applicants; captured in distinct WoE bin. |

---

### 5.2 Capacity (Income Generation & Cashflow Volatility)

| # | Feature Name | Data Type | Valid Range | Canonical Source | Monotonic Trend | Description & Transformation Rule | Fallback & Missing Value Handling |
| :-: | :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| 8 | `estimated_crop_income_kharif` | `float` | `₹0` – `₹300,000` | Geospatial / Manual | Increasing | Projected gross Kharif harvest revenue: $\text{Acreage} \times \text{Crop Yield} \times \text{MSP / Mandi Modal Price}$. | Estimated from district crop-cutting experiment benchmarks if field yield unrecorded. |
| 9 | `estimated_crop_income_rabi` | `float` | `₹0` – `₹300,000` | Geospatial / Manual | Increasing | Projected gross Rabi harvest revenue: $\text{Acreage} \times \text{Crop Yield} \times \text{MSP / Mandi Modal Price}$. | Set to 0 if single-crop rainfed land. |
| 10 | `income_stability_cv` | `float` | `0.05` – `3.0` | Account Aggregator | Decreasing (Lower = Better) | Coefficient of Variation ($\sigma / \mu$) of monthly credits into bank account over 6 months. | Clamped at 3.0; mapped to `Missing` bin if unbanked. |
| 11 | `monthly_avg_credit_inflow` | `float` | `₹500` – `₹100,000` | Account Aggregator | Increasing | Arithmetic mean of total monthly bank credits over the preceding 6 months. | Verified via physical passbook OCR if AA unavailable. |
| 12 | `pm_kisan_regularity` | `float` | `0.0` – `1.0` | Account Aggregator | Increasing | Proportion of scheduled ₹2,000 PM-Kisan Samman Nidhi quarterly tranches successfully received. | Mapped to 0.0 if farmer is not registered under PM-Kisan. |

---

### 5.3 Capital (Financial Reserves & Tangible Assets)

| # | Feature Name | Data Type | Valid Range | Canonical Source | Monotonic Trend | Description & Transformation Rule | Fallback & Missing Value Handling |
| :-: | :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| 13 | `shg_cumulative_savings` | `float` | `₹0` – `₹100,000` | SHG / FPO | Increasing | Total verified cumulative savings deposited in the SHG group bank account. | Extracted from e-Shakti ledger or group passbook. |
| 14 | `bank_balance_avg_6m` | `float` | `₹0` – `₹50,000` | Account Aggregator | Increasing | Average daily balance maintained across verified savings accounts over 180 days. | Bank Sakhi verified passbook minimum balance. |
| 15 | `asset_score` | `float` | `0.0` – `1.0` | Field Manual | Increasing | Composite score of productive rural assets (livestock count, pump sets, agricultural implements). | Computed via standardized field inspection checklist. |

---

### 5.4 Collateral (Land Parcel Security & Productive Quality)

| # | Feature Name | Data Type | Valid Range | Canonical Source | Monotonic Trend | Description & Transformation Rule | Fallback & Missing Value Handling |
| :-: | :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| 16 | `land_holding_acres` | `float` | `0.0` – `50.0` | Land Records / Digilocker | Increasing | Total cultivable agricultural land holding verified via Jamabandi / RoR state land portals. | 0.0 for landless rural artisans and tenant farmers. |
| 17 | `irrigation_access` | `bool` | `True` / `False` | Geospatial / Manual | Binary | Flag: applicant parcel has canal command access or registered energised tubewell. | Verified by geo-tagged field photo or satellite water proxy. |
| 18 | `land_quality_ndvi_avg` | `float` | `0.0` – `1.0` | Sentinel-2 Satellite | Increasing | 5-year historical average Normalized Difference Vegetation Index (NDVI) at parcel centroid during peak flowering. | Generated via [SatelliteEOProcessor](file:///d:/CreditTech/ml/features/geospatial.py#L93). Defaults to village mean if cloudy. |

---

### 5.5 Conditions (Macro Agro-Climatic & Environmental Risk)

| # | Feature Name | Data Type | Valid Range | Canonical Source | Monotonic Trend | Description & Transformation Rule | Fallback & Missing Value Handling |
| :-: | :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| 19 | `ndvi_trend_2season` | `float` | `-0.5` – `+0.5` | Sentinel-2 Satellite | Increasing | Slope of peak vegetative vigor over the 2 preceding seasons. Negative indicates soil/crop stress. | Computed via linear regression over seasonal NDVI maxima. |
| 20 | `rainfall_deviation_pct` | `float` | `-100%` – `+100%` | IMD Gridded Rainfall | Optimal near 0% | Percentage deviation of cumulative seasonal monsoon rainfall from the 30-year district Long Period Average (LPA). | Fetched from IMD 0.25° gridded daily precipitation dataset. |
| 21 | `crop_insurance_enrolled` | `bool` | `True` / `False` | PMFBY Portal | Binary | Active policy enrollment in Pradhan Mantri Fasal Bima Yojana (PMFBY) or weather-based crop insurance. | Digilocker or PMFBY policy certificate upload. |

---

## 6. The 4 Ingestion Rails & Multi-Rail Resilience

Data is ingested through **4 independent, redundant digital rails**:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              THE 4 INGESTION RAILS                                     │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ RAIL 1: Account Aggregator (AA) ──► Anonymized bank cashflow & UPI transactions        │
│ RAIL 2: Community & SHG/FPO     ──► Group registers, meeting attendance, and savings   │
│ RAIL 3: Earth Observation (EO)  ──► Sentinel-2 10m NDVI & IMD gridded precipitation     │
│ RAIL 4: Land, Farm & Bureau     ──► Bhulekh land titles, PMFBY, and MFI inquiry bureau │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 6.1 Rail 1: Account Aggregator (AA) & Digital Banking
* **Ecosystem Partner:** Licensed NBFC-AA (e.g. Setu, Finvu, OneMoney) operating under Sahamati schema standards.
* **Consent Type:** Financial Information User (FIU) fetch with `FIType=DEPOSIT` and `TransactionType=CREDIT_DEBIT`.
* **Data Payload Requirements:**
  * 180 to 365 days of structured bank statements in JSON / XML.
  * Extracted fields: transaction date, amount, credit/debit flag, counterparty VPA/narration, closing balance.
* **Graceful Degradation Fallback:** If AA is unavailable or applicant is unbanked, Bank Sakhi uploads physical bank passbook photos processed via OCR, degrading confidence bands from $\pm 5.0$ to $\pm 8.0$ points.

### 6.2 Rail 2: Community & SHG / FPO / PACS Records
* **Ecosystem Partners:** State Rural Livelihood Missions (SRLM / NRLM), NABARD e-Shakti database, Primary Agricultural Credit Societies (PACS).
* **Data Payload Requirements:**
  * Member registration ID, SHG group name, village code.
  * Meeting attendance log (date, present/absent).
  * Monthly mandatory savings ledger (prescribed amount, deposited amount, deposit date).
  * Internal SHG loan register (disbursed date, amount, EMI schedule, payment history).
* **Graceful Degradation Fallback:** In non-digitized villages, Bank Sakhis enter meeting register summaries countersigned by the SHG President/Secretary.

### 6.3 Rail 3: Earth Observation (EO) Satellite & Meteorological Data
* **Data Sources:** European Space Agency (ESA) Copernicus Sentinel-2 MSI Level-2A (Bottom-of-Atmosphere surface reflectance) and Indian Meteorological Department (IMD) 0.25° gridded rainfall.
* **Processor Implementation:** Handled directly by [SatelliteEOProcessor](file:///d:/CreditTech/ml/features/geospatial.py#L93).
* **Data Payload Requirements:**
  * Land parcel GPS coordinates (boundary polygon or centroid latitude/longitude).
  * Sentinel-2 Band 4 (Red, 665nm) and Band 8 (Near-Infrared, 842nm) 10-meter imagery filtered for $<20\%$ cloud cover.
  * Standard formula:
    $$\text{NDVI} = \frac{\text{B8 (NIR)} - \text{B4 (Red)}}{\text{B8 (NIR)} + \text{B4 (Red)}}$$
  * Seasonal Windows: Kharif (July – October) and Rabi (November – March).
  * IMD daily rainfall gridded accumulation compared against historical district Long Period Average (LPA).

### 6.4 Rail 4: Land Ownership & Public Bureau Data
* **Data Sources:** State Land Records portals (e.g. Apna Khata Rajasthan, MP Bhulekh), PMFBY National Crop Insurance Portal, and Credit Information Companies (CRIF High Mark / Equifax microfinance pulls).
* **Data Payload Requirements:**
  * Land title verification: Khasra/Khatauni number, total parcel area, soil classification (Barani / Chahi / Nahari).
  * Crop insurance verification: PMFBY application number, premium deduction confirmation.
  * Bureau check: Outstanding microfinance loan count, active defaults with other institutional lenders.

---

## 7. Real Production Training Data Schema & Ingestion Template

To execute candidate retraining via [DPDPRetrainingPipeline](file:///d:/CreditTech/ml/training/retrain.py), the data engineering team or partner bank must supply an extract adhering to the following schema:

**Target File Location:** `data/production_training_data.csv`

### 7.1 Column-by-Column Schema Definition

| Column Header | SQL Type | Nullable | Description / Constraint |
| :--- | :---: | :---: | :--- |
| `borrower_id` | `VARCHAR(64)` | No | Anonymized unique identifier (e.g. `B-00821`). |
| `repay_label` | `INT` | No | Target $Y$: `1` = Repaid / Current, `0` = Default ($\ge 90$ DPD). |
| `consented_for_retraining`| `BOOLEAN` | No | Must be `True` under DPDP Act 2023. |
| `gender` | `VARCHAR(10)` | No | Monitored-only: `'F'`, `'M'`, `'OTHER'`. |
| `landholding_band` | `VARCHAR(20)` | No | Monitored-only: `'MARGINAL'`, `'SMALL'`, `'SEMI_MEDIUM'`, `'MEDIUM'`, `'LARGE'`, `'LANDLESS'`. |
| `village_id` | `VARCHAR(100)`| No | Monitored-only cluster ID for spatial cross-validation. |
| `agro_climatic_zone` | `VARCHAR(100)`| Yes | Monitored-only regional zone classification. |
| `shg_repayment_rate` | `FLOAT` | Yes | Feature 1 ($0.05 - 1.00$). |
| `shg_meeting_attendance_pct` | `FLOAT` | Yes | Feature 2 ($0.0 - 100.0$). |
| `shg_savings_consistency` | `FLOAT` | Yes | Feature 3 ($0.0 - 1.0$). |
| `shg_membership_years` | `FLOAT` | Yes | Feature 4 ($0 - 15$). |
| `shg_grade` | `VARCHAR(2)` | Yes | Feature 5 (`'A'`, `'B'`, `'C'`, `'D'`). |
| `utility_payment_ontime_pct` | `FLOAT` | Yes | Feature 6 ($0.0 - 100.0$). |
| `upi_transaction_regularity` | `FLOAT` | Yes | Feature 7 ($0.0 - 1.0$). |
| `estimated_crop_income_kharif` | `FLOAT` | Yes | Feature 8 (₹). |
| `estimated_crop_income_rabi` | `FLOAT` | Yes | Feature 9 (₹). |
| `income_stability_cv` | `FLOAT` | Yes | Feature 10 (Coefficient of variation). |
| `monthly_avg_credit_inflow` | `FLOAT` | Yes | Feature 11 (₹). |
| `pm_kisan_regularity` | `FLOAT` | Yes | Feature 12 ($0.0 - 1.0$). |
| `shg_cumulative_savings` | `FLOAT` | Yes | Feature 13 (₹). |
| `bank_balance_avg_6m` | `FLOAT` | Yes | Feature 14 (₹). |
| `asset_score` | `FLOAT` | Yes | Feature 15 ($0.0 - 1.0$). |
| `land_holding_acres` | `FLOAT` | Yes | Feature 16 (Acres). |
| `irrigation_access` | `BOOLEAN` | Yes | Feature 17 (`True` / `False`). |
| `land_quality_ndvi_avg` | `FLOAT` | Yes | Feature 18 ($0.0 - 1.0$). |
| `ndvi_trend_2season` | `FLOAT` | Yes | Feature 19 ($-0.5 - +0.5$). |
| `rainfall_deviation_pct` | `FLOAT` | Yes | Feature 20 ($-100.0 - +100.0$). |
| `crop_insurance_enrolled` | `BOOLEAN` | Yes | Feature 21 (`True` / `False`). |

### 7.2 Sample Data Rows

```csv
borrower_id,repay_label,consented_for_retraining,gender,landholding_band,village_id,agro_climatic_zone,shg_repayment_rate,shg_meeting_attendance_pct,shg_savings_consistency,shg_membership_years,shg_grade,utility_payment_ontime_pct,upi_transaction_regularity,estimated_crop_income_kharif,estimated_crop_income_rabi,income_stability_cv,monthly_avg_credit_inflow,pm_kisan_regularity,shg_cumulative_savings,bank_balance_avg_6m,asset_score,land_holding_acres,irrigation_access,land_quality_ndvi_avg,ndvi_trend_2season,rainfall_deviation_pct,crop_insurance_enrolled
B-00821,1,True,F,MARGINAL,Tibbi,CANAL_IRRIGATED_NORTH,0.96,92.0,0.85,4,A,95.0,0.40,42000,48000,0.22,7800,1.0,6200,6800,0.60,1.2,True,0.67,0.04,3.5,True
B-00822,0,True,M,LANDLESS,Nohar,ARID_RAIN_FED_WEST,0.62,45.0,0.20,1,C,50.0,0.10,15000,18000,0.85,3200,0.5,1100,1400,0.20,0.0,False,0.36,-0.09,-24.0,False
B-00823,1,True,F,SMALL,Sangaria,CANAL_IRRIGATED_NORTH,0.91,85.0,0.70,3,B,88.0,0.30,55000,60000,0.30,9500,1.0,7500,8200,0.70,2.5,True,0.70,0.02,-1.0,True
B-00824,0,True,F,MARGINAL,Rawatsar,ARID_RAIN_FED_WEST,0.70,60.0,0.30,2,C,65.0,0.15,22000,26000,0.65,4500,0.75,2200,2800,0.35,1.0,False,0.42,-0.04,-18.0,False
```

### 7.3 Minimum Sample Size & Event Floor
To satisfy Basel II/III statistical power requirements for credit scoring:
* **Total Sample Size:** Minimum $\ge 1,500$ completed loans.
* **Default Events Floor:** Minimum $\ge 120$ observed defaults ($Y=0$) to ensure numerical stability in logistic regression parameter estimation and GBDT split points.

---

## 8. Real Data Sourcing & Proxy Acquisition Guide

When real historical bank loans are being curated, the engineering team can utilize three distinct pathways:

### Pathway A: Partner Bank / NBFC Loan Book Extract (Preferred)
* Partner Regional Rural Banks (RRBs) or Small Finance Banks (SFBs) export anonymized historical borrower records over the past 3 fiscal years.
* Data engineering maps core banking system (CBS) tables to the 28-column CSV format using the CreditTech ETL pipeline.

### Pathway B: Public Benchmark Data Adaptation (Home Credit Proxy)
* The Kaggle / Home Credit Default Risk dataset represents thin-file, unbanked borrowers.
* The CreditTech mapping module adapts Home Credit fields to our 21 features (e.g. `AMT_INCOME_TOTAL` $\rightarrow$ `monthly_avg_credit_inflow`, `DAYS_REGISTRATION` $\rightarrow$ `shg_membership_years`).

### Pathway C: High-Fidelity Calibrated Synthetic Generator
* Run `python scripts/seed_pilot_data.py` or use the Monte Carlo Copula generator calibrated against published NABARD e-Shakti state reports and IMD rainfall statistics.

---

## 9. Model Lifecycle, Promotion, Archival & Rollback Governance

CreditTech enforces a rigorous, auditable state machine for all model artifacts governed by [ModelRegistry](file:///d:/CreditTech/ml/registry/registry.py) and [ModelPromotionService](file:///d:/CreditTech/services/core/admin/promotion.py).

```
                      ┌───────────────────────┐
                      │       CANDIDATE       │
                      │  (Trained Artifact)   │
                      └───────────┬───────────┘
                                  │
                                  │ Passed Spatial CV & Fairness Gate
                                  ▼
                      ┌───────────────────────┐
                      │       VALIDATED       │
                      │   (Shadow Scoring)    │
                      └───────────┬───────────┘
                                  │
                                  │ Admin / ML Engineer Promotion
                                  ▼
 ┌─────────────────┐  Demote Old ┌───────────────────────┐
 │     RETIRED     │◄────────────┤        ACTIVE         │
 │   (Archived)    │   Champion  │  (Champion Inference) │
 └────────┬────────┘             └───────────────────────┘
          │
          │ Re-register as new candidate
          │ + Full re-validation against current data
          ▼
   (Re-promoted)
```

### 9.1 The Tripartite Promotion Floor
A candidate model can **NEVER** be promoted to `active` based solely on high AUC. It must satisfy three simultaneous gates:
1. **Quantitative Performance Floor:**
   * $\text{AUC} \ge 0.60$
   * $\text{Gini} \ge 0.20$
   * $\text{Kolmogorov-Smirnov (KS)} \ge 0.15$
   * $\text{Brier Score} \le 0.30$
2. **Fairness Gate P6 Clearance ([services/core/monitoring/governance.py](file:///d:/CreditTech/services/core/monitoring/governance.py#L82)):**
   * Verified by the latest audit cycle across gender ($\le 20\%$ gap) and landholding ($\le 25\%$ gap).
3. **Role-Based Access Control (RBAC):**
   * Promotion can only be triggered by an authorized `ADMIN` or `ML_ENGINEER` with an auditable cryptographic signature.

### 9.2 Shadow Mode Serving Probation
Before any validated model is promoted to active production traffic:
* It must serve as a **challenger model in shadow mode** ([services/core/scoring/service.py](file:///d:/CreditTech/services/core/scoring/service.py#L110-L130)) alongside the active champion for at least **14 to 30 days** (or a minimum of **500 scoring inferences**).
* Runtime tracking measures score correlation ($r_s \ge 0.85$), KS divergence, and latency overhead without impacting live borrower outcomes.

### 9.3 Archival & Retirement Governance
When a new model is promoted to `active`, the incumbent champion is automatically transitioned to `retired`.

#### Can an Archived/Retired Model Be Re-Promoted?
* **The Regulatory Law (Basel II/III MRM & SR 11-7):** A retired model **cannot** simply be toggled back to production without full re-evaluation. Because credit risk distributions, agricultural prices, and macro factors drift continuously, a model that was valid 12 months ago may now violate demographic fairness or produce miscalibrated probabilities.
* **Software State Machine Enforcement:** In [ml/registry/registry.py](file:///d:/CreditTech/ml/registry/registry.py#L188-L195), `retired` is intentionally defined as a terminal status (`retired -> active` is blocked).
* **Formal Re-Promotion Protocol:**
  1. The archived model artifact must be re-registered as a new candidate version (e.g. `v1.1.0-r1`).
  2. It must be evaluated against the **current** spatial validation dataset and the **current** active demographic fairness audit.
  3. Only upon passing all current gates can it be promoted to `active`.
* **Emergency Break-Glass Rollback:** If a live model exhibits catastrophic failure in production and an emergency rollback to a prior version is mandated by bank risk leadership:
  * Two authorized Admins must submit a signed regulatory justification.
  * The prior version is activated, and an immediate automated drift and fairness audit is initiated against current scoring traffic.

---

## 10. Continuous Operational Monitoring & Drift Stability (PSI & CSI)

Scoring traffic is continuously audited against baseline training distributions using [ml/evaluation/drift.py](file:///d:/CreditTech/ml/evaluation/drift.py).

### 10.1 Population Stability Index (PSI)
$$PSI = \sum_{b=1}^{10} \Big( P_{\text{actual}}(b) - P_{\text{expected}}(b) \Big) \times \ln \left( \frac{P_{\text{actual}}(b)}{P_{\text{expected}}(b)} \right)$$

### 10.2 Characteristic Stability Index (CSI)
Calculated identically to PSI for each of the 21 individual input features to isolate specific drivers of population shift.

### 10.3 Basel II/III Stability Action Thresholds
* **$\text{PSI} < 0.10$ (`STABLE`):** Green status. Normal operation.
* **$0.10 \le \text{PSI} < 0.25$ (`MODERATE_DRIFT`):** Amber status. Risk officers review seasonal agricultural shocks, weather anomalies, or changes in applicant sourcing.
* **$\text{PSI} \ge 0.25$ (`SEVERE_DRIFT`):** Red status. Straight-through automated lending is immediately locked; all applications route to manual credit underwriter review; automated retraining pipeline is triggered.

---

## 11. Institutional Model Risk Management (MRM) Sign-Off Checklist

Prior to promoting any model to production serving, the Credit Risk Committee and Lead ML Engineer must sign off on the following checklist:

- [ ] **Data Lineage:** 100% of training data originates from verified Bronze/Silver pipelines with tamper-proof SHA-256 hashes.
- [ ] **Zero PII Confirmation:** Automated CI test proves zero overlap with `PROHIBITED_FIELDS`.
- [ ] **DPDP Retraining Consent:** 100% of records verified with `consented_for_retraining == True`.
- [ ] **Sample Size & Defaults:** Dataset contains $\ge 1,500$ loans with $\ge 120$ observed defaults.
- [ ] **Spatial Group Cross-Validation:** Evaluated via [SpatialGroupValidator](file:///d:/CreditTech/ml/training/validation.py) on unseen villages ($\text{AUC} \ge 0.60, \text{Gini} \ge 0.20, \text{KS} \ge 0.15, \text{Brier} \le 0.30$).
- [ ] **Fairness Gate Passed:** Demographic disparity $\le 20\%$ across gender and $\le 25\%$ across landholding bands on the latest audit period.
- [ ] **Actionable Recourse Verified:** Tested counterfactual pathways for rejected/borderline applicants with bilingual English/Hindi explanations.
- [ ] **Shadow Mode Completed:** Challenger model served in parallel shadow mode for $\ge 14$ days with score correlation $r_s \ge 0.85$.
- [ ] **Regulatory Dossier Generated:** Formal Basel Model Card generated and archived via `python scripts/generate_model_card.py`.
