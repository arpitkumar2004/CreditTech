# CreditTech — Decision Graphs & Visual Storyboarding Handbook
**Document Version:** `v2026.09.1`  
**Classification:** Institutional Credit Underwriting, Model Risk Management (MRM) & Statutory Compliance  
**Target Stakeholders:** Regulated Entities (Banks/SFBs/NBFCs) · RBI Inspection Officers · DPDP Auditors · Credit Risk Committees · Field Loan Officers · Rural Borrowers  

---

## 1. Executive Vision: Visual Storytelling in Regulated Rural Credit

In traditional lending, algorithmic decisions are often hidden behind complex statistical tables that obscure the human reality of the borrower and the systemic risks of the portfolio. Under the **RBI Digital Lending Guidelines (DLG)**, **DPDP Act 2023**, and **Basel II/III Model Risk Management (MRM)** standards, charts are not decorative: **every graph must tell an unambiguous, auditable story that drives a definitive business, risk, or regulatory decision**.

This handbook establishes the **20 indispensable visual decision graphs** implemented in CreditTech, organized across 6 real-world operational narrative acts.

---

## Act 1: The Borrower's Journey — Alternative Data & Financial Inclusion

### Graph 1: The Thin-File Cashflow Pulse (Bank Inflow vs. Volatility Envelope)
* **The Story:** Traditional credit bureaus see zero history for **Ramesh**, a 38-year-old marginal farmer in Tibbi. But his Account Aggregator (AA) cashflow timeline tells a story of disciplined economic activity: small daily UPI pulses from milk sales to the local dairy cooperative (₹250–₹400/day), supplemented by quarterly ₹2,000 PM-Kisan tranches, maintaining an average balance above ₹5,500 despite seasonal agricultural dry spells.
* **Visual Representation:**
```
Balance (₹)
10,000 ┤                                          ▲ PM-Kisan (₹2,000)
       │                         ▲ PM-Kisan       │
 7,500 ┼ - - - - - - - - - - - - ┼ - - - - - - - -┼ - - - - - - - 6M Mean (₹6,200)
       │    /\    /\/\    /\     │    /\/\   /\   │  /\/\
 5,000 ┤───/  \──/    \──/  \───/ \──/    \_/  \_/ \/    \──────── Min Safety Floor (₹3,000)
       │  Daily Milk Cooperative UPI Inflows (₹250-400)
     0 ┼───┬──────┬──────┬──────┬──────┬──────┬──────┬──────┬──► Month
          M1     M2     M3     M4     M5     M6     M7     M8
```
* **Decision Driven:** Proves cashflow liquidity and stability ($CV \le 0.40$), justifying an automated credit line of ₹40,000 without requiring physical collateral.

---

### Graph 2: The Community Pillar — 36-Month SHG Savings & Meeting Discipline Timeline
* **The Story:** **Shanti Devi** belongs to the Marudhara Mahila Self-Help Group. The graph plots 36 consecutive monthly group meeting attendance logs and ₹200 mandatory savings deposits. It reveals 95% in-person meeting attendance, with the only dip occurring during the November Rabi harvesting labor window.
* **Visual Representation:**
```
Attendance %
100% ┤ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■   ■ ■ ■ ■ ■ ■ ■ ■ ■ ■   ■ ■ ■ ■ ■ ■ ■ ■  (95% Average)
     │                     ■                     ■
 75% ┤                     │                     │  ◄── Rabi Harvest Labour Dips
     │                     ▼                     ▼      (Group-Ratified Leave)
 50% ┤
     └─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─► Month (1-36)
Savings: ₹200/mo Uninterrupted Ledger ──► Total Accumulated Savings: ₹7,200 (Grade A)
```
* **Decision Driven:** Validates high social capital and peer-guaranteed moral collateral, raising her Character score and unlocking priority group-lending rates.

---

### Graph 3: Earth Observation Satellite NDVI Trajectory vs. Drought (The Farm's Real Pulse)
* **The Story:** In July 2026, localized rainfall in Nohar district was 24% below normal, prompting informal moneylenders to claim crops were ruined. But CreditTech’s Sentinel-2 10m Normalized Difference Vegetation Index (NDVI) temporal profile demonstrates that Farmer Ramesh’s canal-irrigated plot reached peak vegetative vigor (NDVI = 0.68) during flowering, proving irrigation resilience against meteorological drought.
* **Visual Representation:**
```
NDVI Index
 0.8 ┤                                       * * * Peak Vegetative Vigor (0.68)
     │                                   * *       * *
 0.6 ┼ - - - - - - - - - - - - - - - - * - - - - - - - * - - Healthy Crop Baseline (0.50)
     │                             * *                   *
 0.4 ┤             * * *         *                         *  [Canal Parcel Resilient]
     │         * *       * * * *                           ──────────────────────────
 0.2 ┤ * * * *                                             . . Rainfed Parched (0.28)
     └─┬─────────┬─────────┬─────────┬─────────┬─────────┬─────────► Date
     June 1   June 20   July 10   Aug 01    Aug 25    Sept 15   (Kharif Season)
```
* **Decision Driven:** Prevents false-positive distress rejections, approving the seasonal bullet loan backed by verified crop health.

---

## Act 2: The Underwriting Desk — Transparent Decisions & Borrower Rights

### Graph 4: Portfolio Score Distribution & The 3 Institutional Decision Zones
* **The Story:** The risk committee visualizes the entire applicant population across the 300–900 score distribution. The chart establishes three clear operational bands: Straight-Through Processing (STP) auto-approvals, human underwriter reviews, and adverse action declines.
* **Visual Representation:**
```
Frequency
  ▲
  │                       │  ZONE 2: REVIEW  │  ZONE 1: AUTO-APPROVE
  │                       │  (Score 550-649) │  (Score >= 650)
  │                       │  Human Officer   │  Straight-Through
  │                       │  Verification    │  Disbursal (STP)
  │                       ├──────────────────┼─────────────────────
  │                 ┌───┐ │ ┌───┐            │
  │           ┌───┐ │   │ │ │   │ ┌───┐      │ ┌───┐
  │     ┌───┐ │   │ │   │ │ │   │ │   │ ┌───┐│ │   │ ┌───┐
  │ ┌───┤   │ │   │ │   │ │ │   │ │   │ │   ││ │   │ │   │ ┌───┐
  └─┴───┴───┴─┴───┴─┴───┴─┴─┴───┴─┴───┴─┴───┴┴─┴───┴─┴───┴─┴───┴──►
   300         450       550                650                 900
     ZONE 3: REJECT (<550)
     Adverse Action Notice
```
* **Decision Driven:** Calibrates bank straight-through automation to 65% of applicants, containing operational costs while routing borderline applicants to human credit officers.

---

### Graph 5: Local SHAP Feature Contribution Waterfall (Adverse Action Notice)
* **The Story:** Under RBI Digital Lending Guidelines, an adverse credit decision cannot be an opaque black box. When applicant **Kailash** is scored at 595 (below the 650 cutoff), this waterfall plot transparently displays the exact points contributed or deducted by each factor in bilingual format.
* **Visual Representation:**
```
Expected Score Baseline: 610
-------------------------------------------------------------------------
+45 pts │ ██████████████████████████████        │ SHG Grade 'A' (उच्च समूह गुणवत्ता)
+35 pts │ ██████████████████████                │ Canal Irrigation (सिंचाई उपलब्धता)
+18 pts │ ███████████                           │ Utility Bills 95% On-Time (बिजली बिल)
-55 pts │                   ░░░░░░░░░░░░░░░░░░░░│ Volatile Cashflow (अनियमित बैंक लेनदेन)
-38 pts │                   ░░░░░░░░░░░░░░      │ Low Meeting Attendance (72% बैठक)
-20 pts │                   ░░░░░░░             │ No Crop Insurance (फसल बीमा नहीं)
-------------------------------------------------------------------------
Final Calibrated Score: 595 (Zone 2 — Human Underwriter Review)
```
* **Decision Driven:** Produces the mandatory RBI Key Fact Statement (KFS) and adverse action notice, giving the borrower full transparency and eliminating predatory denial practices.

---

### Graph 6: The "Path to Yes" — Counterfactual Actionable Recourse Ladder
* **The Story:** Instead of abandoning a rejected applicant, CreditTech computes the minimal perturbation vector of behavioral changes to elevate their score above 650 within 90 days. Immutable attributes (landholding, gender, weather) are locked; only realistic personal actions are suggested.
* **Visual Representation:**
```
Score
700 ┤                                                [★ APPROVED]
    │                                                Projected: 662
650 ┼ - - - - - - - - - - - - - - - - - - - - - - - -┬───────────── Cutoff (650)
    │                                ┌───────────────┤
    │                                │ +22 pts:      │
    │                ┌───────────────┤ Maintain 100% │
    │                │ +26 pts:      │ SHG Savings   │
    │                │ Increase SHG  │ Consistency   │
600 ┤ ┌──────────────┤ Meeting to 90%│               │
    │ │ Initial Score│               │               │
    │ │ 585 (REJECT) │               │               │
    └─┴──────────────┴───────────────┴───────────────┴─────────────►
        Current        Step 1          Step 2          Target (3 Months)
```
* **Decision Driven:** Empowers the borrower with financial literacy and clear milestones, converting rejected applicants into future qualified borrowers.

---

### Graph 7: Multi-Rail Dynamic Confidence Band Waterfall (ADR-5)
* **What it plots:** Error bars indicating scoring uncertainty based on verified data rail completeness.
* **The Story:** When Account Aggregator data is unavailable, confidence intervals expand from $\pm 5$ to $\pm 18$ points. A borrower scoring 655 with wide uncertainty is routed to a Bank Sakhi for passbook verification rather than given an unverified automated sanction.
* **Decision Driven:** Implements graceful degradation so unbanked borrowers are never penalized for digital infrastructure gaps.

---

## Act 3: The Risk Committee Desk — Basel II/III Model Soundness & Capital

### Graph 8: Kolmogorov-Smirnov (KS) Separation & Cutoff Optimization
* **The Story:** The Chief Risk Officer must defend the 650 approval cutoff to bank auditors. The KS plot proves that at Score = 650, the separation between creditworthy borrowers ($F_{\text{good}}$) and defaults ($F_{\text{bad}}$) is maximized ($KS = 0.462$), proving the model achieves optimal risk sorting.
* **Visual Representation:**
```
Cumulative %
100% ┤                                 .------- Goods F_good(s)
     │                         . '   /
     │                 . '    /     /
     │           . '         /     /
     │      . '   ◄───────► /     /    ◄── Max Distance: KS = 0.462
     │  . '        Max KS  /     /         at Score = 650
     │ /                  /     /
     │/                  /     /
  0% ┼──────────────────/─────/─────────────── Bads F_bad(s)
    300                650   750             900  (Credit Score)
```
* **Decision Driven:** Formally ratifies the pilot approval floor. Meets the Basel IRB promotion condition ($KS \ge 0.15$).

---

### Graph 9: Cumulative Gains / Lift Curve (Default Capture Efficiency)
* **The Story:** Demonstrates that by declining the bottom 20% of scores, the bank eliminates **65% of all portfolio defaults**, while approving 92% of good borrowers.
* **Visual Representation:**
```
% Defaults Captured
100% ┤                                 .------- Model Curve (65% at Decile 2)
     │                         . '   /
 80% ┤                 . '    /
 60% ┤           . '         /   ◄── Captures 65% of all defaults in lowest 20% scores
 40% ┤      . '   /
 20% ┤  . '      /               . . . Random Guess Baseline (45° Line)
     │ /        /
  0% ┼───────────────────────────────────────►
     0%        20%       40%       60%     100%  (% Population Ranked by Risk)
```
* **Decision Driven:** Establishes regulatory capital provisions under Basel II Internal Ratings-Based (IRB) formula.

---

### Graph 10: Score Calibration Curve (Reliability Diagram)
* **The Story:** Verifies that predicted repayment probabilities match reality. When the model predicts an 80% repayment rate in bin 8, the actual observed rate is 78.8% ($\text{Brier} \le 0.30$), proving absence of probability inflation.
* **Decision Driven:** Confirms that expected credit loss ($ECL = PD \times LGD \times EAD$) estimates submitted to banking regulators are mathematically un-biased.

---

### Graph 11: Champion vs. Challenger Shadow Dual-Run Scatterplot
* **The Story:** A scatterplot tracking 1,000 live scoring events evaluated simultaneously by Champion (WoE Scorecard) and Challenger (Monotonic GBM). The tight clustering along the 45° diagonal confirms high rank correlation ($r_s = 0.89$), while the 4% disagreement quadrant isolates applicants where non-linear interactions rescued the score.
* **Decision Driven:** Verifies shadow-mode probation criteria before promoting challenger models to active status.

---

## Act 4: The Statutory Fairness & Board Desk — Ethical Lending & Parity

### Graph 12: Demographic Approval Parity vs. The 20% Ratified Ceiling
* **The Story:** Under Article 15 and the RBI Fair Practices Code, algorithmic credit must never discriminate against women or vulnerable landless farmers. This graph plots actual approval rates side-by-side with the 20% ratified ceiling line:
* **Visual Representation:**
```
Approval Rate %
100% ┤    ┌────────┐      ┌────────┐
     │    │  95.6% │      │  94.9% │      ┌──────────────────────────────────┐
 80% ┤    │ Female │      │  Male  │      │ Max Disparity Gap: 0.7%          │
     │    │ (SHG)  │      │        │      │ Ratified Ceiling:  20.0% [PASS]  │
 60% ┤    │        │      │        │      └──────────────────────────────────┘
     │    │        │      │        │
 40% ┤    │        │      │        │ - - - - - - - - - - - - Minimum Floor (35%)
     │    │        │      │        │
  0% └────┴────────┴──────┴────────┴─────────────────────────────────────────►
```
* **Decision Driven:** Clearance of the P6 Fairness Gate. Confirms that women SHG members achieve superior repayment discipline that is rewarded by the scoring algorithm.

---

### Graph 13: Landholding Equity (Marginal vs. Small vs. Landless)
* **The Story:** Traditional lenders demand land title deeds (Jamabandi/RoR), excluding tenant farmers and landless rural artisans. CreditTech’s parity chart proves that landless applicants achieve a 92.5% approval rate (vs 94.7% for marginal farmers), well within the 25% landholding disparity ceiling.
* **Decision Driven:** Demonstrates to NABARD that community social capital effectively substitutes for physical land collateral.

---

### Graph 14: Loan Officer Override Vigilance Monitor (Human Bias Control Chart)
* **The Story:** Tracks the weekly override rate (% of model recommendations overturned by human credit officers) across branches against the **50.0% regulatory redline**. It instantly flags Branch C, where officers overturned 58% of model approvals for female applicants, triggering an internal vigilance inquiry.
* **Decision Driven:** Prevents discretionary human bias from undermining objective, fair algorithmic underwriting.

---

## Act 5: The Operations & MLOps Desk — Drift Detection & Climate Shocks

### Graph 15: Population Stability Index (PSI) Early Warning Radar
* **The Story:** Plots live monthly score distribution shifts against the training baseline. During normal months, PSI remains green ($<0.10$). In August 2026, severe rainfall deficit caused PSI to spike to 0.26, instantly tripping the automated circuit breaker and freezing straight-through auto-sanctions.
* **Visual Representation:**
```
PSI Score
 0.30 ┤                                     ▲ SPIKE: 0.26 [CIRCUIT BREAKER TRIPPED]
      │                                     │ Automated Lending Locked;
 0.25 ┼ - - - - - - - - - - - - - - - - - - ┼ - - - - - - - - Severe Drift Redline
      │                                    / \
 0.20 ┤                                   /   \
      │                                  /     \
 0.10 ┼ - - - - - - - - - - - - - - - - / - - - \ - - - - - - Moderate Drift Amber
      │    o-------o-------o-------o   /         \
 0.00 ┴────┴───────┴───────┴───────┴──/───────────┴──────────────────────────────►
          Apr     May     Jun     Jul     Aug     Sept  (2026 Audit Periods)
```
* **Decision Driven:** Implements BCBS stability compliance by automatically shifting the bank from algorithmic straight-through approval to conservative manual committee review during regional shocks.

---

### Graph 16: The 21-Feature Characteristic Stability (CSI) Diagnostics Heatmap
* **The Story:** When Graph 15 trips an alert, the data engineering team turns to the $21 \times 12$ CSI heatmap. The chart reveals that while 20 features remained stable (green), `rainfall_deviation_pct` turned deep red ($CSI = 0.34$), confirming that the drift was an external climate shock rather than an internal data pipeline failure.
* **Decision Driven:** Prevents unnecessary model retrainings during transitory weather events; directs credit teams to verify PMFBY crop insurance enrollment.

---

### Graph 17: Spatial Cross-Validation Village Generalization Cluster Map
* **The Story:** Visualizes the 5 pilot village clusters (Hanumangarh, Tibbi, Sangaria, Rawatsar, Nohar). Proves that models are validated out-of-village (`GroupKFold`), ensuring the algorithm does not memorize localized micro-climates and successfully generalises to new administrative blocks.
* **Decision Driven:** Guarantees geographic portability before expanding platform operations to new districts.

---

## Act 6: The Statutory Privacy & Legal Desk — DPDP Act 2023 Compliance

### Graph 18: Tamper-Evident Cryptographic Hash Chain Consent Ledger
* **The Story:** Visualizes the immutable SHA-256 blockchain-style hash chain linking every consent event. Demonstrates to the Data Protection Board of India that borrower consent records cannot be retroactively injected, altered, or backdated.
* **Visual Representation:**
```
┌───────────────────────────┐      ┌───────────────────────────┐      ┌───────────────────────────┐
│     GENESIS RECORD        │      │    CONSENT #001 (ACTIVE)  │      │    REVOCATION #002 (REV)  │
│  Borrower: B-00821        │      │  Purpose: Scoring         │      │  Reason: Borrower Opt-Out │
│  Hash: a1b2...c3d4        ├───►  │  Prev_Hash: a1b2...c3d4   ├───►  │  Prev_Hash: e5f6...g7h8   │
│  Timestamp: 2026-08-01    │      │  Current_Hash: e5f6...g7h8│      │  Current_Hash: 9i0j...k1l2│
└───────────────────────────┘      └───────────────────────────┘      └───────────────────────────┘
```
* **Decision Driven:** Provides irrefutable legal evidence of statutory consent under Section 6 of the DPDP Act 2023.

---

### Graph 19: The DPDP Retraining Pool Funnel & Right to Erasure Waterfall
* **The Story:** Under DPDP §12, borrowers can revoke consent for model retraining at any time. This funnel visualizes the strict filtration: from 10,000 total loans, only matured 12-month loans with active `consented_for_retraining == True` enter the training dataset, proving zero non-consented data leakage.
* **Visual Representation:**
```
Total Scored Loans (10,000)
    │
    ▼ [Filter: 12-Month Maturity Window]
Matured Closed / 90-DPD Loans (4,200)
    │
    ▼ [Filter: consented_for_retraining == True]
Active DPDP Consented Pool (3,650)  ──► [550 Revoked / Opted-Out: Purged from Gold Layer]
    │
    ▼ [Spatial GroupKFold Split]
Clean Final Retraining Matrix (3,650 Rows, 0 PII, 0 Monitored Fields)
```
* **Decision Driven:** Protects the institution against severe regulatory penalties (up to ₹250 crore under DPDP Act 2023) by mathematically enforcing consent boundaries.

---

### Graph 20: 3-Layer Medallion Architecture Lineage DAG
* **The Story:** Visualizes the physical segregation of data: Bronze (raw external API responses with PII), Silver (standardized 21-feature vectors with PII quarantined), and Gold (curated retraining pool with consent gating).
* **Decision Driven:** Establishes regulatory architectural proof that direct personal identifiers (`aadhaar`, `phone`, `caste`) can never physically enter machine learning training weights.

---

## 7. Institutional Decision Matrix Summary

| Act | # | Graph Title | Primary Narrative / Story Revealed | Statutory / Business Decision Taken |
| :--- | :-: | :--- | :--- | :--- |
| **Act 1** | 1 | **Cashflow Pulse** | Discloses invisible daily dairy earnings & PM-Kisan tranches. | Unlocks ₹40k credit line without physical bureau history. |
| | 2 | **SHG Savings Discipline** | 36 months of ₹200 savings proves unblemished peer commitment. | Replaces physical collateral with community moral collateral. |
| | 3 | **Sentinel-2 NDVI Health** | Shows peak vegetative vigor (0.68) defying rain deficit. | Approves agricultural advance by proving crop resilience. |
| **Act 2** | 4 | **3-Zone Score Distribution** | Calibrates portfolio risk appetite and review queue sizing. | Sets 650 cutoff; automates 65% straight-through lending. |
| | 5 | **Local SHAP Waterfall** | Explains exact score deductions in bilingual Hindi/English. | Generates statutory RBI Key Fact Statement adverse notice. |
| | 6 | **Actionable Recourse Ladder** | Converts cold rejection into achievable 90-day progress plan. | Retains borrower in financial inclusion ecosystem. |
| | 7 | **Multi-Rail Uncertainty** | Error bars widen when Account Aggregator is unlinked. | Triggers passbook OCR verification instead of auto-rejection. |
| **Act 3** | 8 | **KS Separation Plot** | Peak separation ($KS = 0.462$) occurs at Score = 650. | Defends operational cutoff to bank risk committee. |
| | 9 | **Cumulative Lift Chart** | Declining bottom 20% captures 65% of all defaults. | Allocates Basel II Internal Ratings-Based capital provisions. |
| | 10 | **Decile Calibration** | Predicted probabilities match empirical default rates. | Validates un-biased Expected Credit Loss calculations. |
| | 11 | **Champion vs Challenger** | Proves rank correlation ($r_s = 0.89$) in live shadow mode. | Clears candidate model to replace incumbent champion. |
| **Act 4** | 12 | **Gender Parity Bar** | Female SHG approval gap is 0.7% (vs 20% ceiling). | Clears P6 Fairness Gate for production deployment. |
| | 13 | **Landholding Equity** | Landless applicants achieve 92.5% approval rate. | Proves non-discriminatory access for tenant farmers. |
| | 14 | **Officer Override Monitor** | Alerts when branch officers reject 58% of female approvals. | Triggers vigilance inspection to stop human bias. |
| **Act 5** | 15 | **PSI Drift Radar** | Spikes to 0.26 during seasonal monsoon deficit. | Activates circuit breaker; locks automated lending. |
| | 16 | **CSI Feature Heatmap** | Isolates weather rail as root cause of drift (not bank API). | Directs team to inspect PMFBY crop insurance policies. |
| | 17 | **Spatial CV Cluster Map** | Proves model generalises across unseen pilot villages. | Authorises geographic rollout to neighboring districts. |
| **Act 6** | 18 | **Hash-Chain Consent Ledger** | SHA-256 chain proves consent was never backdated. | Satisfies statutory audit under DPDP Act 2023 §6. |
| | 19 | **Retraining Consent Funnel** | 550 opted-out borrowers purged from Gold training store. | Enforces statutory Right to Erasure under DPDP Act §12. |
| | 20 | **3-Layer Medallion DAG** | Shows zero PII entering feature space or training sets. | Proves Purpose Limitation under DPDP Act §8. |
