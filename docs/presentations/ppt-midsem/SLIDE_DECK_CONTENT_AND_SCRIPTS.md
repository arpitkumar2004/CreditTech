# Master Slide Deck Blueprint: Content, Visuals & Verbatim Scripts

**Project:** CreditTech — Alternative Credit Scoring for Rural Financial Inclusion  
**Candidate:** Arpit Kumar (IIT Kharagpur)  
**Target Deck:** `CreditTech_MidSem_Presentation.pptx` (16 Slides, 16:9 Widescreen)  
**Tone:** Research-grade, mathematically disciplined, intellectually rigorous, and institutionally grounded.  

---

## Slide 1: Title & Academic Attribution

- **Category:** THESIS DEFENSE / MID-SEMESTER EVALUATION
- **Slide Header:** CreditTech: Alternative Credit Scoring & Decision-Support Architecture for Rural Financial Inclusion
- **Visual Layout:**
  - Deep Navy hero canvas (`#0A192F`) with subtle royal blue accent line.
  - Academic metadata card:
    - Candidate: Arpit Kumar | Integrated Dual Degree (Chemical Eng. + AI Micro-Specialization), IIT Kharagpur
    - Advisor / Review Committee: Department of Chemical Engineering & Center of Excellence in AI
    - Institutional Scope: Concept, Architecture, DPI Integration & 4–5 Village Pilot Design
- **Slide Content:**
  - *Core Paradigm:* Lending Service Provider (LSP) decision-support bridge built on India's Digital Public Infrastructure (DPI).
  - *Engineering Foundation:* 5-Layer Modular Monolith (FastAPI + PostgreSQL + React 19 PWA).
  - *Multi-Source Ingestion:* 4-Rail engine fusing Account Aggregator, Sentinel-2 10m NDVI, e-Shakti SHG thrift, and land registries.
  - *Responsible AI:* Monotonic WoE Scorecard Champion, exact closed-form bilingual SHAP explainability, and automated DPDP cryptographic consent ledger.
- **Verbatim Speaker Script:**
  > *"Respected Professor and members of the evaluation committee, good morning. Today, I am presenting the mid-semester conceptual design, technical architecture, and pilot blueprint for CreditTech: an alternative credit scoring and decision-support platform engineered specifically to resolve thin-file credit exclusion in rural India.*
  > *While India has achieved historic milestones in universal bank account ownership and real-time digital payments, formal credit access for smallholder farmers and rural women remains structurally constrained. Over the next 15 minutes, I will present our end-to-end framework—from secondary data need assessment and stakeholder mapping, to our 5-layer modular system architecture, DPI integration with Account Aggregator and ULI, and our stratified 5-site empirical pilot design."*

---

## Slide 2: Executive Overview: Unlocking Rural Credit Invisibility via Responsible AI

- **Category:** EXECUTIVE SUMMARY
- **Slide Header:** Executive Summary: Solving the Rural Credit Invisibility Trap through Responsible AI & Open DPI
- **Visual Layout:** 4-Quadrant Card Grid (Problem → Solution → Technical Approach → Impact Outcome).
- **Slide Content:**
  - **1. The Problem (The Inclusion Paradox):** 89% of Indian adults have bank accounts, but only 13% borrow formally (Findex 2025). 57% of rural households are agricultural (0.74 ha avg. holding); CIBIL scores them as '-1', trapping them in 36–48% informal moneylender debt.
  - **2. The Solution (Unbundled LSP):** Pure Lending Service Provider (LSP) under RBI Digital Lending Guidelines. Provides alternative scoring intelligence to Regulated Entities (RRBs/PACS) without holding balance-sheet risk or borrower deposits.
  - **3. The Approach (4-Rail DPI Architecture):** Fuses Account Aggregator cashflows, Sentinel-2 10m satellite NDVI, SHG e-Shakti community savings, and ULI land records into a 21-feature domain store with graceful degradation.
  - **4. Target Outcomes (Pilot Validation):** Cuts appraisal turnaround time from 14 days to &lt; 1 hour; delivers +20–30% approval uplift for thin-file borrowers; maintains PAR90 &le; 2.0% (vs. 6.2% sectoral agri GNPA); guarantees Disparate Impact Ratio (DIR) &ge; 0.80 across gender.
- **Verbatim Speaker Script:**
  > *"To orient the committee, Slide 2 provides our executive overview across four pillars.*
  > *First, the core paradox: India has won the battle for bank accounts, but lost the battle for formal credit. Millions of productive farmers are invisible to traditional credit bureaus simply because they lack salary slips or registered land mortgages.*
  > *Second, our solution: CreditTech operates strictly as an LSP under RBI guidelines, providing decision-support intelligence to banks rather than taking balance sheet risk.*
  > *Third, our technical approach: We ingest multi-source alternative signals—from Account Aggregator cashflows to 10-meter satellite vegetative health and SHG peer savings.*
  > *And fourth, our projected outcomes: A rigorous 9–12 month pilot designed to cut loan turnaround from two weeks to under an hour, while guaranteeing strict algorithmic fairness across gender and landholding size."*

---

## Slide 3: Problem & Village-Level Need Assessment (Topic 1)

- **Category:** PROBLEM & NEED ASSESSMENT
- **Slide Header:** The Rural Credit Gap: 120M+ Productive Borrowers Trapped by Structural Information Asymmetry
- **Visual Layout:** 6 Metric KPI Highlight Cards + 2 Analytical Synthesis Containers (Refer: `tables/01_secondary_data_need_assessment.md`).
- **Slide Content:**
  - **Secondary Data Benchmark Metrics:**
    - `89% vs 13%`: Adults with bank account (2024) vs. adults borrowing formally (World Bank Findex 2025).
    - `67.0 / 100`: RBI Financial Inclusion Index (July 2025); Usage (weighted 45%) severely lags Access.
    - `0.74 ha`: Average rural landholding, down from 1.08 ha in 2016 (NABARD NAFIS 2021–22); 86% small/marginal.
    - `₹30 Lakh Cr`: Addressable MSME credit gap (24% of total demand); widens to 35% for women (SIDBI 2025).
    - `6.2% vs 2.5%`: Agriculture GNPA vs system-wide GNPA (RBI 2024), driving bank risk-aversion.
    - `10.05 Cr`: Women mobilised across 90.9 Lakh SHGs under DAY-NRLM with &gt;96% repayment track (PIB 2025).
  - **Structural Diagnosis:**
    - *Collateral Failure:* 86% of farmers operate fragmented holdings or oral sharecropping; cannot execute registered mortgages.
    - *Bureau Failure:* Conventional credit bureaus (CIBIL) depend on backward-looking formal loan repayments; thin-file farmers receive Score -1.
    - *The Informality Trap:* 14-day sowing window forces 23.4% of farmers to informal moneylenders charging 36% to 48% APR.
- **Verbatim Speaker Script:**
  > *"Slide 3 establishes our empirical problem statement, synthesized from official secondary datasets including the World Bank Global Findex 2025, RBI's Financial Inclusion Index, and NABARD's NAFIS survey.*
  > *Notice the stark asymmetry in our data: While 89% of Indian adults own bank accounts, only 13% borrowed formally last year—and just 10% among women. Furthermore, average landholdings have shrunk to 0.74 hectares. Because 86% of Indian farmers are small or marginal, they cannot provide the clear land titles required for traditional mortgages.*
  > *Meanwhile, commercial banks face a 6.2% Gross NPA ratio in agriculture, making them structurally risk-averse. When an unbanked farmer applies, the automated credit bureau returns a score of -1. Because agricultural planting windows last only 14 days, the farmer cannot endure weeks of branch delays—they turn to local moneylenders charging 36% to 48% interest. This credit gap is fundamentally an information asymmetry problem, not a capital shortage."*

---

## Slide 4: Stakeholder & Institutional Mapping (Topic 2)

- **Category:** STAKEHOLDER MAPPING
- **Slide Header:** Institutional Mapping: Anchoring Decision-Support Within India's Regulated Financial Fabric
- **Visual Layout:** 4-Quadrant Institutional Matrix + Visual Hub (Refer: `diagrams/06_stakeholder_mapping.svg` & `tables/02_stakeholder_matrix.md`).
- **Slide Content:**
  - **1. Demand Side (End Borrowers & Community):**
    - Small & marginal farmers (&lt;2 ha), rural women SHG members, 10,000 FPOs (covering 30 lakh farmers under SFAC).
    - Provide authentic non-bureau repayment trails (e-Shakti books) and peer social collateral.
  - **2. Supply Side (Regulated Lenders & Apex Bodies):**
    - Regional Rural Banks (43 RRBs), 63k+ PACS, Small Finance Banks, and NBFC-MFIs.
    - Hold the loan balance sheet, credit risk, and sole sanction authority.
    - NABARD & SIDBI act as apex refinance anchors and pilot sponsors.
  - **3. Digital Public Infrastructure (DPI Operators):**
    - Sahamati (Account Aggregator), RBI Innovation Hub (ULI), NPCI (UPI), UIDAI (Aadhaar).
    - Provide standard consent and data rails; eliminates bilateral proprietary integrations.
  - **4. Governance & Oversight (Regulators & Independent Auditors):**
    - Reserve Bank of India (enforcing 2022/2026 Digital Lending Directions and 5% DLG caps).
    - Data Protection Board of India (DPDP Act 2023 compliance).
    - Independent Academic Auditors (IIT Kharagpur: demographic fairness audits, DIR &ge; 0.80).
- **Verbatim Speaker Script:**
  > *"Slide 4 presents our stakeholder and institutional mapping.*
  > *A fatal flaw of many fintech proposals is attempting to bypass established institutions. In contrast, CreditTech is deliberately architected to amplify existing rural trust anchors.*
  > *As shown in our four-quadrant map, CreditTech operates at the nexus of four groups:*
  > *On the demand side: smallholders and 90.9 lakh SHGs who provide rich community data.*
  > *On the capital side: Regional Rural Banks and PACS, backed by NABARD, who retain full underwriting authority.*
  > *On the data infrastructure side: India's DPI rails—Sahamati Account Aggregators and RBI's Unified Lending Interface.*
  > *And on the governance side: the RBI, the Data Protection Board, and an independent academic evaluation team at IIT Kharagpur ensuring algorithmic non-discrimination.*
  > *This positioning ensures full regulatory legitimacy from day one."*

---

## Slide 5: Existing System (As-Is): Bureau Failure & Informality Trap (Topic 3)

- **Category:** AS-IS WORKFLOW ANALYSIS
- **Slide Header:** Existing Rural Lending (As-Is): A Linear, Paper-Heavy Process Gated by Bureau Blindness
- **Visual Layout:** Horizontal Process Failure Diagram + Systemic Pain Points Table (Refer: `diagrams/01_as_is_workflow.svg` & `tables/03_as_is_vs_to_be.md`).
- **Slide Content:**
  - **As-Is Linear Workflow (5 Stages):**
    1. *Farmer Application:* Paper forms, manual land patta copies, requires 3–5 branch visits.
    2. *Physical Verification:* Loan officer field visit to farm plot; subjective appraisal; guarantor required.
    3. *Data Silos:* Revenue land records, bank statements, and subsidy data sit in disconnected manual silos.
    4. *Bureau Gating:* Credit bureau query (CIBIL); returns Score -1 (No History); automated rejection.
    5. *Informal Fallback:* Application rejected after 10–20 days; farmer forced to moneylender (36–48% APR).
  - **Empirical Pain Points:**
    - *Unbearable TAT:* 10 to 20 business days exceeds the critical 14-day Kharif input purchasing window.
    - *Collateral Bias:* 86% of farmers operating &lt;2 ha or oral tenancy are automatically excluded.
    - *Bureau Blindness:* Ignores 12.18 lakh crore of SHG credit with &gt;96% repayment track record.
    - *High Fixed Cost-to-Serve:* Physical verification makes small-ticket loans (₹25k–₹50k) unprofitable for banks.
- **Verbatim Speaker Script:**
  > *"Slide 5 dissects the existing As-Is rural credit journey.*
  > *Today, the process is linear, paper-heavy, and bureau-gated. A smallholder farmer travels multiple times to a bank branch, submitting physical land documents. A loan officer must manually conduct field verification, which introduces high administrative costs and subjective human bias.*
  > *When the bank pulls a credit bureau report, the applicant returns a score of -1. Traditional bureaus have zero visibility into utility payments, UPI cashflows, or SHG savings.*
  > *After 10 to 20 days of bureaucratic delay, the loan is either rejected or drastically downsized. Because seeds must be planted immediately after monsoon arrival, the farmer has no choice but to borrow from informal moneylenders at extortionate 36% to 48% interest rates. The As-Is system fails both the borrower and the bank."*

---

## Slide 6: Proposed System (To-Be): Multi-Source Decision-Support (Topic 4)

- **Category:** TO-BE SYSTEM PARADIGM
- **Slide Header:** Proposed System (To-Be): Consent-Based Multi-Source Scoring Delivering Same-Day Decisions
- **Visual Layout:** Horizontal To-Be Workflow Diagram + Comparative Dimension Card (Refer: `diagrams/02_to_be_workflow.svg` & `tables/03_as_is_vs_to_be.md`).
- **Slide Content:**
  - **To-Be Digital Architecture Flow:**
    - *Assisted Digital Onboarding:* Mobile PWA / Bank Sakhi assisted portal; regional language voice/text prompts.
    - *DPDP-Compliant Consent:* Explicit, revocable DEPA consent artifact logged in SHA-256 cryptographic ledger.
    - *Parallel 4-Rail Ingestion:* Account Aggregator, Sentinel-2 10m NDVI, e-Shakti SHG ledgers, and ULI land registry.
    - *Alternative Scoring Engine:* Calibrated score (300–900) + exact bilingual SHAP reason codes generated in &lt; 3 minutes.
    - *Regulated Underwriter Sanction:* Loan officer review cockpit; ULI document dispatch; same-day CBS disbursal.
  - **As-Is vs. To-Be Quantitative Contrast:**
    - Underwriting Inputs: Bureau + Land Deed $\rightarrow$ 4-Rail Multi-Source Ingestion Engine.
    - Appraisal Turnaround: 10–20 Business Days $\rightarrow$ &lt; 3 Minutes Scoring (&lt; 24 hr bank disbursal).
    - Thin-File Approval Uplift: 0% (Automatic Rejection) $\rightarrow$ +20% to +30% uplift for creditworthy smallholders.
    - Decision Transparency: Opaque subjective discretion $\rightarrow$ Top-5 Explainable SHAP drivers (Hindi &amp; English).
- **Verbatim Speaker Script:**
  > *"Slide 6 presents our proposed To-Be system architecture.*
  > *CreditTech reframes the entire credit journey around a single principle: turning every consented, legally verifiable signal about a borrower's real economic life into an explainable score in minutes.*
  > *The farmer or Bank Sakhi initiates the application on a tablet. With explicit, time-bound consent captured in our DPDP ledger, our backend orchestrates parallel ingestion across four rails: Account Aggregator cashflows, Sentinel-2 satellite crop health, e-Shakti community savings, and ULI land data.*
  > *Within three minutes, our scoring engine generates a calibrated score on the standard 300 to 900 scale, complete with bilingual SHAP explanations. The loan officer reviews the profile on their cockpit and sanctions the loan the same day. We replace a 20-day ordeal with a 3-minute intelligence pipeline."*

---

## Slide 7: Complete System Architecture (Topic 5)

- **Category:** SYSTEM ARCHITECTURE
- **Slide Header:** System Architecture: A 5-Layer Modular Monolith Built for Resilience & Sub-Millisecond Serving
- **Visual Layout:** 5-Layer Modular Monolith Architectural Blueprint (Refer: `diagrams/03_system_architecture_5layers.svg`).
- **Slide Content:**
  - **Layer 1: Identity &amp; Consent Management:** Aadhaar e-KYC, DigiLocker, DPDP-compliant SHA-256 hash-chained immutable consent ledger, assisted Bank Sakhi PWA.
  - **Layer 2: Multi-Rail Ingestion Engine:** Async parallel connectors for Account Aggregator (AA), Sentinel-2 10m multispectral imagery, e-Shakti SHG ledgers, and bureau records. Enforces *Graceful Degradation*.
  - **Layer 3: Intelligence &amp; Responsible AI Scoring:** 21-feature domain store (5 Cs of credit), Monotonic WoE Scorecard (Champion, AUC 0.96) + Monotonic LightGBM (Challenger, AUC 0.98), exact bilingual SHAP explainability, and population drift monitor.
  - **Layer 4: Decisioning &amp; Policy Gateway:** OCEN 4.0 LSP orchestration, statutory eligibility rules engine, and ULI document hand-off.
  - **Layer 5: Channel, Servicing &amp; Governance:** Touch-first React 19 PWA, Loan Officer Decision Cockpit with mandatory dissent override logging, and closed-loop repayment feedback loops.
- **Verbatim Speaker Script:**
  > *"Slide 7 details our complete 5-layer system architecture.*
  > *We deliberately architected CreditTech as a modular monolith built with FastAPI, PostgreSQL, and React 19.*
  > *Layer 1 manages identity and consent using SHA-256 hash chaining.*
  > *Layer 2 handles parallel ingestion across our four data rails with built-in Graceful Degradation.*
  > *Layer 3 is our machine learning intelligence core, serving our champion WoE scorecard in under 0.04 milliseconds.*
  > *Layer 4 enforces lending policy and interfaces with OCEN and ULI.*
  > *And Layer 5 powers the front-end channels for Bank Sakhis and bank underwriters.*
  > *Why a monolith rather than microservices? Because at projected pilot volumes of 15 to 30 decisions per day, microservices introduce distributed network latency and operational failure points. Our modular architecture delivers sub-millisecond inference with clean, separable code boundaries."*

---

## Slide 8: Data Architecture, Data Sources & PII Isolation (Topic 6)

- **Category:** DATA ARCHITECTURE & PRIVACY
- **Slide Header:** Data Architecture: 7 Ingestion Streams with Strict Physical & Cryptographic PII Separation
- **Visual Layout:** Dual-Panel Architecture Card (Data Streams & Hypotheses vs. PII Separation Schema; Refer: `tables/04_data_architecture_and_sources.md`).
- **Slide Content:**
  - **7 Alternative Ingestion Streams & Economic Hypotheses:**
    1. *Account Aggregator (AA):* Bank &amp; UPI cashflows $\rightarrow$ predicts cashflow volatility &amp; debt service capacity.
    2. *Geospatial &amp; Earth Observation:* Sentinel-2 10m NDVI &amp; IMD drought risk $\rightarrow$ predicts crop yield &amp; weather shocks.
    3. *Community &amp; SHG:* e-Shakti thrift ledgers $\rightarrow$ captures uncollateralized peer trust and social capital.
    4. *Market &amp; Mandi:* e-NAM transactions &amp; dairy milk pouring $\rightarrow$ reflects realized agricultural income.
    5. *Government Welfare:* PM-KISAN &amp; KCC registries $\rightarrow$ establishes baseline household cash floor.
    6. *Bureau Pull:* CIBIL/Experian pull $\rightarrow$ corroborating signal of over-indebtedness (not a gate).
    7. *Data Minimisation Exclusions:* Explicitly excludes caste, religion, contacts, SMS, or real-time location.
  - **Physical &amp; Cryptographic Separation Model:**
    - Sensitive PII (Name, Phone, Aadhaar) encrypted via AES-256-GCM in isolated `borrowers` table.
    - Feature Store (`feature_snapshots`) contains purely anonymous numerical vectors linked only by opaque UUID.
- **Verbatim Speaker Script:**
  > *"Slide 8 details our data architecture and privacy safeguards.*
  > *Every data source ingested by CreditTech maps to an explicit economic credit hypothesis. We never harvest data simply because it is available.*
  > *Crucially, we resolve the central vulnerability of digital credit: data privacy. Under India's DPDP Act 2023, we enforce strict physical and cryptographic separation of Personally Identifiable Information from our machine learning feature store.*
  > *As shown in our schema diagram, borrower identities are encrypted using AES-256 in an isolated table. The feature store and scoring models operate exclusively on anonymized numerical vectors. No analytics script or external model ever has access to plaintext borrower identities."*

---

## Slide 9: Technology Stack & Engineering Decision Records (Topic 7)

- **Category:** TECHNOLOGY STACK & ADRs
- **Slide Header:** Technology Stack: Open-Standard Engineering Choices Backed by Formal ADRs
- **Visual Layout:** 4-Tier Stack Grid + 4 Architecture Decision Record (ADR) Cards (Refer: `tables/05_technology_stack_justification.md`).
- **Slide Content:**
  - **Production Technology Choices:**
    - *Client Tier:* React 19, Vite, Tailwind CSS, Lucide Icons (Touch-first mobile PWA; offline caching).
    - *Application Tier:* Python 3.12, FastAPI (Asynchronous modular monolith; OpenAPI 3.1 contract).
    - *Persistence &amp; Audit:* PostgreSQL 16, SQLAlchemy 2.0 Async, Alembic (ACID compliance; append-only triggers).
    - *Machine Learning:* Scikit-learn, Monotonic WoE binning, LightGBM, SHAP TreeExplainer.
  - **Architecture Decision Records (ADRs):**
    - `ADR-1: Modular Monolith over Microservices:` Eliminates network serialization latency, Docker Swarm overhead, and distributed transaction complexity at pilot scale.
    - `ADR-2: In-Process ML Serving over SageMaker:` Executes inference in Python memory (&lt; 0.04 ms), saving significant cloud hosting costs and eliminating remote API failure points.
    - `ADR-3: Native Asyncio over Celery/Redis:` Eliminates external broker infrastructure dependencies for I/O-bound multi-rail API requests.
    - `ADR-4: PostgreSQL Hash Chaining over Blockchain:` Provides mathematical tamper-evidence for consent logs ($H_n = \text{SHA256}(H_{n-1} \parallel \text{TxData})$) at zero gas cost.
- **Verbatim Speaker Script:**
  > *"Slide 9 outlines our technology stack and Architecture Decision Records (ADRs).*
  > *Every technical choice was driven by empirical need rather than startup hype.*
  > *First, we chose a Modular Monolith over microservices. At pilot scale, microservices introduce distributed network latency and complex failure cascades. Our monolith achieves sub-0.04 millisecond model inference in-process.*
  > *Second, we chose native Python asyncio over Celery and Redis, reducing cloud infrastructure complexity.*
  > *Third, we implemented mathematical SHA-256 hash chaining within PostgreSQL rather than using a complex blockchain, providing tamper-evident consent ledgers at zero transaction cost.*
  > *Every decision reflects production discipline and academic rigor."*

---

## Slide 10: API / DPI & Institutional Integration Framework (Topic 8)

- **Category:** DPI INTEGRATION
- **Slide Header:** DPI Integration Framework: Orchestrating National Public Rails to Eliminate Bilateral Friction
- **Visual Layout:** Central Orchestration Hub Diagram (Refer: `diagrams/04_dpi_integration_hub.svg` & `tables/06_dpi_and_institutional_integration.md`).
- **Slide Content:**
  - **Integration with 4 National Public Rails:**
    - *1. Account Aggregator (AA / Sahamati):* Certified Financial Information User (FIU); ingests structured financial cashflow data from 17 licensed AAs covering 284M+ accounts under signed DEPA consent.
    - *2. Unified Lending Interface (ULI / RBI):* Standardized dispatch gateway delivering credit scores, risk tiers, and Top-5 SHAP reasons directly to bank Core Banking Systems (CBS) without custom bank-by-bank integrations.
    - *3. Open Credit Enablement Network (OCEN 4.0):* Implements standard LSP-to-Lender API contracts for digital loan origination and offer presentation.
    - *4. DPDP Consent Architecture:* Phased compliance aligned to MeitY 2025 Rules; 7-year audit retention; 60-second revocation execution.
  - **Graceful Degradation Resilience:**
    - If an external rail times out (e.g. cloud cover blocking satellite optical revisit), the system rescales feature weights, widens the confidence band ($\pm 45$ vs $\pm 15$), and delivers a valid partial score.
- **Verbatim Speaker Script:**
  > *"Slide 10 illustrates our API and DPI integration framework.*
  > *CreditTech acts as an intelligent orchestration hub connecting India's national digital public infrastructure with regulated lenders.*
  > *We integrate with four primary rails:*
  > *The Account Aggregator network for consented cashflows;*
  > *The RBI's Unified Lending Interface for seamless document and score hand-off to bank core systems;*
  > *The OCEN protocol for open lending contracts;*
  > *And MeitY's DPDP consent framework for user rights management.*
  > *Crucially, we built Graceful Degradation: if monsoon clouds obstruct optical satellite passes, our engine does not crash with an HTTP 500. It dynamically rescales available feature weights and outputs a confidence-calibrated score. The pipeline never halts."*

---

## Slide 11: Functional Modules: M1 to M9 Specifications (Topic 9)

- **Category:** FUNCTIONAL ARCHITECTURE
- **Slide Header:** Functional Modules: 9 Interlocking Subsystems from Consent to Closed-Loop Feedback
- **Visual Layout:** 9-Module Specification Table with SLA & Security Invariants (Refer: `tables/07_functional_modules_m1_m9.md`).
- **Slide Content:**
  - **M1 · Onboarding &amp; Consent:** Aadhaar e-KYC, DPDP multi-lingual consent, assisted Bank Sakhi toggle (SLA &lt; 5 min).
  - **M2 · Data Aggregation:** Async multi-rail orchestrator; normalizes raw API payloads into 21-feature vectors (SLA &lt; 3 min).
  - **M3 · Alternative Scoring:** Dual Champion WoE / Challenger LightGBM engine; outputs 300–900 score (Inference &lt; 0.04 ms).
  - **M4 · Explainability &amp; SHAP:** Computes closed-form Shapley values; outputs Top-5 adverse action reason codes in Hindi and English.
  - **M5 · Fairness &amp; Drift Monitor:** Automated gate enforcing Disparate Impact Ratio (DIR &ge; 0.80) and PSI &lt; 0.10.
  - **M6 · Lender Decision Cockpit:** Underwriter dashboard with SHAP waterfall charts and mandatory dissent override logging.
  - **M7 · Loan Lifecycle &amp; Feedback:** Tracks repayment performance; channels real repayment labels into quarterly retraining pipelines.
  - **M8 · Grievance Redressal:** Borrower dispute channel with 14-day statutory resolution SLA per RBI guidelines.
  - **M9 · Institutional Dashboard:** Portfolio-level inclusion and PAR analytics cockpit for NABARD and bank executives.
- **Verbatim Speaker Script:**
  > *"Slide 11 details our nine core functional modules.*
  > *From Module M1, which handles multi-channel assisted onboarding and cryptographic consent capture;*
  > *To Module M2 for parallel multi-rail ingestion;*
  > *Module M3, which runs our sub-millisecond scoring engine;*
  > *Module M4, generating bilingual SHAP explanations;*
  > *Module M5, running automated algorithmic fairness gates;*
  > *Module M6, our underwriter review cockpit;*
  > *Module M7, tracking closed-loop repayment performance;*
  > *Module M8, managing borrower disputes;*
  > *And Module M9, providing institutional oversight for NABARD and bank executives.*
  > *Every module enforces strict SLAs, input validations, and security invariants."*

---

## Slide 12: User Journey & End-to-End SLAs (Topic 10)

- **Category:** USER EXPERIENCE & PROCESS FLOW
- **Slide Header:** User Journey: Compressing a 20-Day Bureau Ordeal into a 4-Step Same-Day Experience
- **Visual Layout:** 4-Node Circular Process Flow with Target SLAs (Refer: `diagrams/05_borrower_user_journey.svg` & `tables/08_user_journey_sla.md`).
- **Slide Content:**
  - **Step 1: Application (&lt; 5 Minutes):**
    - Borrower or Bank Sakhi inputs demographic basics and loan intent on a touch-first PWA tablet.
    - Offline caching allows data entry even in areas with zero cellular connectivity.
  - **Step 2: Consent &amp; e-KYC (&lt; 5 Minutes):**
    - Instant Aadhaar OTP verification; signs electronic Account Aggregator consent artifact.
    - Transaction block appended to SHA-256 immutable consent ledger.
  - **Step 3: Scoring &amp; Explanation (&lt; 3 Minutes):**
    - 4-rail parallel ingestion pulls cashflows, satellite NDVI, and SHG ledgers.
    - Outputs calibrated credit score (300–900) + Top-5 SHAP reasons in conversational Hindi &amp; English.
  - **Step 4: Sanction &amp; Disbursal (Same Working Day):**
    - Loan officer reviews score and satellite crop map on Underwriter Cockpit.
    - Digital sanction letter issued; loan capital disbursed straight to borrower account via ULI.
    - Automated `DataRetentionWorker` executes cryptographic PII purge after 30-day underwriting TTL.
- **Verbatim Speaker Script:**
  > *"Slide 12 illustrates the user journey and process SLAs.*
  > *While our backend coordinates complex multi-rail integrations, the experience for a rural borrower is compressed into four simple, transparent steps:*
  > *Step 1: The applicant inputs their request via a Bank Sakhi tablet in under five minutes.*
  > *Step 2: Instant Aadhaar e-KYC and electronic consent capture in under five minutes.*
  > *Step 3: Automated multi-rail ingestion and score generation in under three minutes, providing immediate, transparent reason codes.*
  > *And Step 4: Same-day underwriter sanction and bank account disbursal via ULI.*
  > *Finally, our automated DataRetentionWorker executes a cryptographic wipe of all raw PII once the 30-day underwriting TTL expires, ensuring zero lingering privacy exposure."*

---

## Slide 13: Security, Privacy & Regulatory Framework (Topic 11)

- **Category:** GOVERNANCE & REGULATION
- **Slide Header:** Regulatory Compliance: Multi-Regime Guardrails Governing LSP Operations & Data Privacy
- **Visual Layout:** 3 Regulatory Column Pillars + Security Invariants Card (Refer: `tables/09_security_and_regulatory_matrix.md`).
- **Slide Content:**
  - **1. RBI Digital Lending Directions (2022 / Revised 2025):**
    - CreditTech operates strictly as an LSP; Regulated Entities retain sole credit underwriting and sanction authority.
    - Direct fund flow from bank CBS to borrower account (zero third-party escrow or pass-through accounts).
    - Default Loss Guarantee (DLG / FLDG) strictly capped at 5% of portfolio, backed by fixed deposits.
  - **2. Digital Personal Data Protection (DPDP) Act 2023 &amp; Rules 2025:**
    - Explicit, informed, and revocable consent; strict Purpose Limitation bound to credit underwriting.
    - Section 8(7) Storage Limitation: automated cryptographic PII scrubbing upon 30-day TTL expiration.
    - 72-hour breach notification workflow aligned to Data Protection Board protocols.
  - **3. Pre-Promotion Algorithmic Fairness Gates:**
    - Enforces US EEOC Four-Fifths Rule: Disparate Impact Ratio (DIR) $\ge 0.80$ across gender and landholding cohorts.
    - Automated CI/CD promotion gate blocks model deployment with HTTP 409 Conflict if disparity exceeds threshold.
- **Verbatim Speaker Script:**
  > *"Slide 13 addresses our regulatory and data governance framework.*
  > *Fintech deployments must strictly comply with governing law. We anchor CreditTech in three statutory regimes:*
  > *First, RBI's Digital Lending Guidelines. We operate strictly as an LSP. Disbursals flow directly between bank and borrower, and any credit risk sharing is legally capped at the mandatory 5% DLG ceiling.*
  > *Second, India's DPDP Act 2023. We enforce strict purpose limitation, instantaneous consent revocation, and automated cryptographic data scrubbing once underwriting concludes.*
  > *And third, our pre-promotion FairnessGate. Borrowers cannot be discriminated against based on gender or marginal land status. We enforce a mathematical Disparate Impact Ratio floor of 0.80. If any updated model breaches this threshold, deployment is automatically halted."*

---

## Slide 14: Initial 4–5 Village Pilot Design across Diverse Agro-Climatic Zones (Topic 12)

- **Category:** PILOT BLUEPRINT
- **Slide Header:** Stratified Pilot Design: 5 Agro-Climatic Site Archetypes Stress-Testing Model Generalizability
- **Visual Layout:** 5-Site Cohort Matrix + 6 Quantitative Evaluation KPI Boxes (Refer: `diagrams/07_pilot_village_matrix.svg` & `tables/10_village_pilot_design_kpis.md`).
- **Slide Content:**
  - **Stratified Agro-Climatic Cohort (5 Sites, 1,000 Borrowers, 9–12 Months):**
    - *Site A (Irrigated Cotton/Wheat — Western UP / RJ, 200 Borrowers):* Tests TAT speed (&lt;1 hr) and credit limit adequacy for existing KCC holders.
    - *Site B (Rainfed Millets/Soybean — Marathwada / MP, 200 Borrowers):* Tests Sentinel-2 NDVI &amp; IMD drought risk during monsoon dry spells.
    - *Site C (SHG-Dense Southern Model — AP / Telangana, 250 Borrowers):* Tests peer social collateral and e-Shakti ledgers for women's micro-enterprises.
    - *Site D (Allied-Activity Dairy — Anand / Odisha, 200 Borrowers):* Tests high-frequency non-crop cashflows (daily milk pouring data) for debt service.
    - *Site E (Low-Bandwidth Tribal — Jharkhand / CG, 150 Borrowers):* Tests Graceful Degradation and offline Bank Sakhi PWA tablet onboarding.
  - **Evaluation KPIs:**
    - Median TAT: &lt; 1 hour (vs. 10–15 days As-Is) | Approval Uplift: +20% to +30% for thin-file borrowers.
    - PAR90: &le; 2.0% (vs. 6.2% agri GNPA benchmark) | Fairness Ratio: DIR &ge; 0.80 across gender.
- **Verbatim Speaker Script:**
  > *"Slide 14 details our empirical field implementation strategy.*
  > *Rather than testing CreditTech in a single convenient village, we designed a stratified sampling framework across five distinct agro-climatic zones:*
  > *Site A in irrigated Uttar Pradesh tests turnaround speed where formal credit already exists.*
  > *Site B in rainfed Marathwada tests satellite drought models under severe weather risk.*
  > *Site C in Andhra Pradesh tests SHG peer savings for women entrepreneurs.*
  > *Site D in Gujarat tests non-crop cashflows using dairy cooperative pouring data.*
  > *And Site E in Jharkhand stress-tests our offline Bank Sakhi workflow in low-connectivity areas.*
  > *Covering 1,000 borrowers over a full 9-to-12 month agricultural cycle, this pilot will empirically measure approval uplift, portfolio-at-risk, and model stability across diverse Indian farming systems."*

---

## Slide 15: Preliminary Cost & Resource Requirements (Topic 13)

- **Category:** FINANCIAL & RESOURCE BUDGET
- **Slide Header:** Resource Requirements: Indicative ₹1.85–2.90 Crore Budget for a 9–12 Month Multi-Site Pilot
- **Visual Layout:** Itemized Budget Allocation Table + Institutional In-Kind Contributions Card (Refer: `tables/11_cost_and_resource_requirements.md`).
- **Slide Content:**
  - **Indicative Itemized Pilot Budget (₹1.85 – ₹2.90 Crore):**
    - *1. Core Engineering &amp; MLOps (5–7 FTEs, 9–12 mo):* ₹85.0 – ₹120.0 L (43.5%) — ML, Backend, PWA, Data/DPI Engineers.
    - *2. Satellite Data Licensing (SatSure / Planet API):* ₹15.0 – ₹30.0 L (9.8%) — 10k hectares across 5 pilot blocks.
    - *3. Account Aggregator &amp; DPI Integration:* ₹8.0 – ₹15.0 L (5.3%) — Certified FIU gateway, ~1,500 consent pulls.
    - *4. Cloud Hosting &amp; Security Architecture:* ₹10.0 – ₹18.0 L (6.5%) — India-region MeitY-empanelled CSP, encrypted backups.
    - *5. Field Operations &amp; Bank Sakhi Enablement:* ₹25.0 – ₹40.0 L (14.5%) — 20 rugged tablets, vernacular training, literacy camps.
    - *6. Independent Fairness &amp; Legal Audit:* ₹10.0 – ₹18.0 L (6.5%) — Academic audit retainer (IIT Kharagpur) + DPDP legal counsel.
    - *7. Monitoring, Evaluation &amp; Reporting:* ₹8.0 – ₹12.0 L (4.4%) — Baseline, midline, and endline surveys.
    - *8. Contingency Reserve (15%):* ₹24.0 – ₹37.0 L (12.5%) — Buffer for API price shifts and monsoon contingencies.
  - **Note on Loan Capital:** Excludes credit capital, which is funded and disbursed strictly by partner banks.
  - **In-Kind Resources:** NABARD district coordination, partner RRB CBS integration, and State Rural Livelihood Mission networks.
- **Verbatim Speaker Script:**
  > *"Slide 15 provides our preliminary cost and resource requirements for the pilot phase.*
  > *Scaled from public fintech disclosures and SIDBI survey operational benchmarks, our total indicative budget is ₹1.85 to ₹2.90 Crore over a 9-to-12 month deployment.*
  > *Core engineering constitutes roughly 44% of expenditure, covering a dedicated 5-to-7 member team.*
  > *Field operations—including rugged tablets for Bank Sakhis and village financial literacy workshops—accounts for 15%.*
  > *Commercial satellite imagery licensing and Account Aggregator transaction fees represent 15%.*
  > *And we allocate dedicated retainers for independent academic fairness audits and legal compliance.*
  > *Crucially, CreditTech does not require lending capital—the loans themselves are disbursed directly from partner bank balance sheets."*

---

## Slide 16: Literature, Policy & Real-World Case Evidence (Topic 14)

- **Category:** LITERATURE EVIDENCE & CONCLUSION
- **Slide Header:** Academic Grounding: Rooted in Peer-Reviewed Literature & Real-World Fintech Analogues
- **Visual Layout:** 4 Literature Quadrants + Defense Conclusion Hero Banner (Refer: `tables/12_literature_and_case_evidence.md`).
- **Slide Content:**
  - **Academic Literature Foundations:**
    - *Alternative Data Predictability:* Berg et al. (2020, *Rev. Fin. Studies*); Kshetri (2021, *Risks*); FAO STI Portal (2020).
    - *Smallholder Seasonality:* Systematic Review (*Computers &amp; Electronics in Agri*, 2025); Njuguna &amp; Sowon (2020, *AfriCHI*).
    - *Social Capital Signals:* Jonnalagadda &amp; Babu (2026, *IRJMS*); NABARD NAFIS (2021–22).
    - *Explainability &amp; Fairness:* Bücker et al. (2020, *JORS*); Agosto et al. (2023, *Data Science*); JMSRR Systematic Review (2026).
  - **Real-World Operational Precedents:**
    - *Kaleidofin (Ki Score):* 10M+ customers decisioned (98% women), $8B disbursements, 20–30% approval uplift, PAR90 &lt; 2%.
    - *SatSure (SatSource):* Statewide UP rollout; 90–95% crop ID accuracy; cut TAT from 15 days to &lt; 30 minutes.
    - *Upstart &amp; Tala:* 20–44% approval rate uplift across thin-file cohorts globally.
    - *RBI ULI:* ₹27,000 Cr disbursed across 600k loans (Dec 2024); validates national appetite for digital credit rails.
  - **The Stated Research Gap &amp; Conclusion:**
    - CreditTech provides the *first open, replicable, village-level framework* simultaneously integrating DPI (AA + ULI), SHG social collateral, and an automated algorithmic fairness gate (DIR &ge; 0.80).
- **Verbatim Speaker Script:**
  > *"To conclude, Slide 16 positions CreditTech within the peer-reviewed literature and operating fintech evidence.*
  > *Foundational research by Berg et al. in the Review of Financial Studies and applied case studies from Kaleidofin and SatSure prove that alternative data can accurately predict debt repayment while expanding inclusion.*
  > *However, the existing literature leaves a critical gap: there is no open, scientifically audited framework that combines Account Aggregators, satellite crop vigor, and SHG social trust with enforceable algorithmic fairness gates across multiple agro-climatic zones.*
  > *CreditTech bridges this exact gap.*
  > *We have established the technical architecture, data governance models, and pilot blueprints to deliver rural credit with dignity and risk discipline.*
  > *Thank you very much for your time and guidance. I welcome your questions and critical evaluation."*
