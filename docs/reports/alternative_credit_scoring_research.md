# Alternative Credit Scoring for Financial Inclusion: AI-Driven Lending for Farmers, SHGs & Rural Enterprise
## Comprehensive Research Reference — Thesis & ML Prototype Guide

**Prepared:** August 2026  
**Purpose:** Deep-dive research compilation covering GitHub repos, competition winners, modern AI models, datasets, academic literature, institutional reports, industry players, and a prototype blueprint.

---

## Table of Contents

1. [Topic Overview & Significance](#1-topic-overview--significance)
2. [Key Academic Papers & Institutional Reports](#2-key-academic-papers--institutional-reports)
3. [Alternative Data Sources — What the Models Use](#3-alternative-data-sources--what-the-models-use)
4. [Modern AI / ML Models Used in This Space](#4-modern-ai--ml-models-used-in-this-space)
5. [GitHub Repositories — Study & Fork These](#5-github-repositories--study--fork-these)
6. [Datasets You Can Use for Your Prototype](#6-datasets-you-can-use-for-your-prototype)
7. [Competition Winners & Their Approaches](#7-competition-winners--their-approaches)
8. [Industry Players & Startup Ecosystem](#8-industry-players--startup-ecosystem)
9. [India-Specific Context: SHGs, NABARD, KCC, RBI](#9-india-specific-context-shgs-nabard-kcc-rbi)
10. [Prototype Blueprint — Build Your ML Model](#10-prototype-blueprint--build-your-ml-model)
11. [Thesis Angles & Research Gaps](#11-thesis-angles--research-gaps)
12. [LinkedIn & Online Communities to Follow](#12-linkedin--online-communities-to-follow)
13. [Full Reference List](#13-full-reference-list)

---

## 1. Topic Overview & Significance

### The Problem
Nearly **50% of smallholder farmers in India** lack access to formal institutional credit, relying instead on exploitative moneylenders charging 24–48% annual interest. Globally, **1.4 billion adults remain unbanked** (World Bank, 2024), with the majority concentrated in rural South Asia, Sub-Saharan Africa, and Southeast Asia.

Traditional credit scoring (CIBIL/FICO) fails this population because:
- No credit history ("thin-file" or "no-file" borrowers)
- No formal salary slips or tax returns
- Collateral-free or low-collateral situations
- Seasonal/irregular income patterns
- Limited digital footprint

### Why This Matters
- India's fintech sector: valued at $31B (2022), projected $84B by 2025 (22% CAGR)
- Digital lending market projected to reach $350B by 2023 (from $110B in 2019)
- 350+ fintechs compete in India's alternative lending market (2025)
- SHG-Bank Linkage: 12+ million SHGs linked to banks via NABARD, managing ₹1.12 lakh crore in credit (2024)
- Kisan Credit Card (KCC): 182 million cards issued, but only ~10% effectively utilised

### Your Thesis Contribution
You are proposing a **machine learning-powered alternative credit scoring system** specifically designed for farmers, SHGs, and rural enterprises — using non-traditional data such as satellite imagery, mobile money behaviour, social group repayment history, utility payments, and crop yield proxies.

---

## 2. Key Academic Papers & Institutional Reports

### Must-Read Papers (Cite These in Your Thesis)

#### Foundational / Core
| Paper | Source | Year | Key Contribution |
|-------|--------|------|-----------------|
| "Machine Learning (ML) Technologies for Digital Credit Scoring in Rural Finance: A Literature Review" | MDPI Risks, 9(11), 192 | 2021 | Most comprehensive survey of ML models for rural finance; compares ANN, SVM, RF, XGBoost, hybrid models |
| "Financial Inclusion and Alternate Credit Scoring: Role of Big Data and ML in Fintech" | Agarwal, Alok, Ghosh, Gupta — SSRN #3507827 | 2020 | Foundational paper; uses 1M+ unbanked borrower dataset; shows AI-enabled scoring dramatically improves inclusion |
| "Enhancing Credit Scoring Accuracy with a Comprehensive Evaluation of Alternative Data" | PLOS ONE / PMC 11108212 | 2024 | Comprehensive evaluation of which alternative data types improve accuracy most |
| "Design of Contextual Agricultural Credit Scoring for Kisan Credit Card: NLP + ML" | ScienceDirect (Indian Journal) | 2026 | **Most India-specific** paper; NLP on farmer language + ML for KCC scheme |
| "Growth Potential of ML in Credit Risk Predicting of Farmers in Industry 4.0" | Chai et al., Int. Journal of Finance & Economics (Wiley) | 2025 | Industry 4.0 framework for farmer credit; IoT + satellite + ML |
| "Impact of Social Networks on Digital Credit Assessment for Rural Residents" | Information Systems Frontiers, Springer | 2025 | Uses social network analysis (SNA) to predict rural creditworthiness — directly relevant to SHGs |
| "Artificial Intelligence and SHGs: Enabling Financial Inclusion in India" | ResearchGate #343122520 | 2020 | Only paper directly on AI + SHG credit scoring |
| "From Data to Dignity: AI-Powered Credit Scoring for an Inclusive India" | ResearchGate #397640896 | 2025 | Indian-context survey; bias, fairness, inclusivity |
| "Role of Fintech & Alternative Credit Scoring for Smallholder Farmers in India" | ResearchGate #383694168 | 2024 | Roadblocks analysis + fintech ecosystem India |
| "AI-Powered Credit Scoring Models: Transforming Financial Inclusion in Rural India" | IRT / Shodh Sagar | 2024 | Case studies + model comparison |
| "A Study of AI-Based Credit Scoring Tools in Rural Nigeria" | WJARR | 2025 | Cross-country comparison; useful for thesis global context |
| "Machine Learning & AI Powered Credit Scoring for Islamic Microfinance + Blockchain" | MDPI Risks | 2026 | Novel hybrid: blockchain + ML for microfinance |
| "Hybrid Boosted Attention-Based LightGBM for Enhanced Credit Risk Assessment" | Nature Humanities & Social Sciences Comms | 2025 | State-of-the-art model; attention mechanism + LightGBM |
| "FSL-BDP: Federated Survival Learning with Bayesian Differential Privacy for Credit Risk" | arXiv 2601.11134 | 2026 | Privacy-preserving ML for credit; relevant for SHG data sensitivity |
| "Attention-Based Dynamic Multilayer Graph Neural Networks for Loan Default Prediction" | European Journal of OR, ScienceDirect | 2024 | GNN approach for loan networks — applicable to SHG group lending |
| "Explainable AI (XAI) Using SHAP and LIME for Credit Scoring" | ResearchGate #391998247 | 2025 | Key XAI methods for making model decisions interpretable to regulators |
| "Interpretable AI in Credit Scoring: Comparative Survey of SHAP, LIME, Hybrid Approaches" | R Discovery / The American Journals | 2025 | Which explainability method works best for credit |

#### Institutional Reports (Authoritative — Cite in Literature Review)
| Report | Publisher | Year | What It Contains |
|--------|-----------|------|-----------------|
| **"Cracking the Credit Code: Alternative Data and AI for Financial Inclusion"** | IFC (World Bank Group) | 2026 | Flagship IFC report; alternative data + AI in emerging markets; women entrepreneurs focus |
| **"Alternative Data for Credit Scoring: Special Report"** | Alliance for Financial Inclusion (AFI) | 2025 | 32-country survey; regulatory frameworks; country case studies (Kenya, Ghana, Mexico, Philippines) |
| **"The Use of Alternative Data in Credit Risk Assessment"** | World Bank Documents | 2025 | Policy + risk framework; opportunities and dangers |
| **"Innovation for Inclusion: Roadmap for Inclusive Finance Policy"** | CGAP | 2025 | Regulatory policy roadmap for fintech-driven inclusion |
| **"Alternative Data Credit Scoring Platforms for Smallholder Farmers"** | FAO STI Portal | 2024 | FAO survey of existing platforms; satellite + farm data |
| **"Launching into Space: Using Satellite Imagery in Financial Services"** | Caribou Global | 2024 | Deep dive on satellite-based credit assessment |
| **"SHG-Bank Linkage: A Success Story"** | World Bank / Open Knowledge | Ongoing | Foundational reference on India's SHG model |
| **"How AI Credit Scoring Models Can Boost Financial Inclusion"** | World Economic Forum | 2025 | WEF perspective; responsible deployment |
| **"Innovative Financing for Inclusive Credit Fintechs in Africa"** | CGAP Focus Note | 2024 | Funding models + approach for inclusive fintech |

---

## 3. Alternative Data Sources — What the Models Use

This is the core innovation in your thesis. Divide into **tiers** for your model architecture:

### Tier 1: Conventional Alternative Data (Available & Proven)
| Data Source | Relevance | Availability in India |
|-------------|-----------|----------------------|
| Mobile phone usage patterns (calls, data, recharge frequency) | Strong predictor of economic activity | High (telecom APIs) |
| Utility payment history (electricity, water) | Bill regularity = credit discipline | Medium (DISCOMs) |
| UPI/digital payment transaction history | Volume, frequency, merchant types | High (NPCI ecosystem) |
| SHG savings deposit records & repayment history | Direct group creditworthiness | High (NABARD e-Shakti) |
| KCC (Kisan Credit Card) transaction patterns | Crop cycle-aligned cash flows | Medium (bank data) |
| PM-Kisan direct benefit transfer records | Income regularity indicator | High (Aadhaar-linked) |
| Mandi (market) transaction records | Crop sales verification | Medium |

### Tier 2: Geospatial & Remote Sensing Data
| Data Source | What It Tells | Tools |
|-------------|---------------|-------|
| Satellite NDVI (Normalized Difference Vegetation Index) | Crop health → yield estimate | Sentinel-2, Landsat (free) |
| Satellite imagery time-series | Land ownership, crop area verification | Google Earth Engine |
| Weather/rainfall data | Crop risk, drought exposure | IMD, NOAA |
| Soil health data | Productivity potential | ICAR soil maps |
| Geospatial farm boundary data | Land parcel validation | Bhuvan, DigiLocker |

### Tier 3: Behavioural & Psychometric Data
| Data Source | Notes |
|-------------|-------|
| Psychometric assessments | Predicts repayment intent; used by Entrepreneurial Finance Lab (EFL) |
| Social network centrality in SHG | Who is the "connector" — better repayment |
| Mobile app usage patterns | Financial literacy proxy |
| e-Shakti SHG meeting attendance | Group discipline indicator |
| Market intelligence (crop prices) | Helps model income volatility |

### Tier 4: Emerging / Frontier Data
| Data Source | Status |
|-------------|--------|
| WhatsApp/vernacular chat logs (NLP-based) | Experimental; privacy concerns |
| Transaction graph networks (GNN) | Research stage; powerful for SHG peer-group analysis |
| Drone imagery for crop verification | Pilot stage in India |
| IoT farm sensors | Premium agritech startups only |
| Blockchain-linked farm records | Nascent |

---

## 4. Modern AI / ML Models Used in This Space

### Model Hierarchy (from Traditional → State-of-the-Art)

#### Level 1: Baseline Models (Always Benchmark Against These)
- **Logistic Regression** — Industry standard; interpretable; regulatory-friendly
- **Decision Tree** — Transparent; good for rural field officers to explain
- **Naïve Bayes** — Fast; works with small datasets

#### Level 2: Strong Performers (Your Core Models)
- **Random Forest** — Handles missing data well; good for heterogeneous rural data
- **XGBoost** — Best single-model performance across most credit competitions; handles imbalanced data
- **LightGBM** — Faster than XGBoost; good for large-scale data; 2024-2025 Kaggle favourite
- **CatBoost** — Excellent for categorical features (district, crop type, caste category)

#### Level 3: Deep Learning Models
- **LSTM / GRU** — For sequential/time-series data (seasonal crop cycles, repayment schedules)
- **Transformer-based models** — For NLP on loan applications in vernacular languages
- **Tabular-specific: TabNet** — Attention-based transformer for tabular credit data (Google Brain, 2021)
- **AutoML (H2O.ai, Auto-sklearn)** — Rapid baseline; use in prototyping phase

#### Level 4: Graph & Network Models (Cutting Edge for SHGs)
- **Graph Neural Networks (GNN)** — Models the SHG group guarantee network; who vouches for whom affects default probability
- **GraphSAGE / Graph Attention Networks (GAT)** — Node classification on borrower-lender graphs
- **Dynamic Multilayer GNN** — For time-evolving SHG group structures (2024 EJOR paper)

#### Level 5: Privacy-Preserving & Federated
- **Federated Learning** — Train model across multiple banks/MFIs without sharing raw SHG data
- **Differential Privacy** — Add noise to protect individual borrower data
- **Blockchain + ML hybrid** — Audit trail for loan decisions; used in Islamic microfinance context

### Explainability Layer (Critical for Regulatory Compliance)
- **SHAP (SHapley Additive exPlanations)** — Gold standard; shows which features drove each decision
- **LIME (Local Interpretable Model-Agnostic Explanations)** — Local explanations for individual loan applicants
- **Counterfactual explanations** — "If you saved ₹500/month for 6 months, your score would improve by X"

### Recommended Prototype Architecture
```
Input Layer:
  ├── Tabular features (demographics, SHG records, KCC data) → XGBoost / LightGBM
  ├── Time-series features (repayment history, savings trends) → LSTM
  ├── Geospatial features (NDVI, rainfall, soil) → Random Forest / CNN
  └── Network features (SHG peer group) → Graph Attention Network

Fusion Layer:
  └── Stacking / Ensemble → Meta-learner (Logistic Regression on predictions)

Output Layer:
  ├── Credit score (0–1000 scale)
  ├── Risk bucket (Low / Medium / High / Very High)
  └── SHAP explanation → "Top 3 reasons for your score"
```

---

## 5. GitHub Repositories — Study & Fork These

### Competition Solutions (Best Quality Code)
| Repository | What It Shows | Stars | Link |
|-----------|---------------|-------|------|
| **open-solution-home-credit** (minerva-ml) | Complete pipeline for Home Credit competition; feature engineering + ensembling | ★1k+ | [github.com/minerva-ml/open-solution-home-credit](https://github.com/minerva-ml/open-solution-home-credit) |
| **Kaggle_Home_Credit** (kozodoi) | Clean solution; LightGBM + feature engineering; well-documented | ★200+ | [github.com/kozodoi/Kaggle_Home_Credit](https://github.com/kozodoi/Kaggle_Home_Credit) |
| **home-credit-default-risk** (NoxMoon) | Multiple model approaches compared | ★100+ | [github.com/NoxMoon/home-credit-default-risk](https://github.com/NoxMoon/home-credit-default-risk) |
| **Kaggle-HomeCreditDefaultRisk** (pklauke) | Denoising Autoencoder + Neural Net + GBDT hybrid; top 4% finish | ★ | [github.com/pklauke/Kaggle-HomeCreditDefaultRisk](https://github.com/pklauke/Kaggle-HomeCreditDefaultRisk) |
| **home-credit-default-risk-complete** (FajrinCd) | Complete pipeline with SHAP explainability | ★ | [github.com/FajrinCd/home-credit-default-risk-complete](https://github.com/FajrinCd/home-credit-default-risk-complete) |
| **Home-Credit-Default-Risk** (yakupkaplan) | Well-structured EDA + modelling | ★ | [github.com/yakupkaplan/Home-Credit-Default-Risk](https://github.com/yakupkaplan/Home-Credit-Default-Risk) |
| **Kaggle-GiveMeSomeCredit** (DrIanGregory) | Classic "Give Me Some Credit" dataset solution | ★ | [github.com/DrIanGregory/Kaggle-GiveMeSomeCredit](https://github.com/DrIanGregory/Kaggle-GiveMeSomeCredit) |
| **loan-default-risk-system** (shashi-hue) | Lending Club + XGBoost + SHAP; business-optimised thresholds | ★ | [github.com/shashi-hue/loan-default-risk-system](https://github.com/shashi-hue/loan-default-risk-system) |
| **Kaggle-Lending-Club** (maciejbiesek) | Multiple ML techniques on Lending Club data | ★ | [github.com/maciejbiesek/Kaggle-Lending-Club-Loan-Data](https://github.com/maciejbiesek/Kaggle-Lending-Club-Loan-Data) |

### Credit Scoring Topic Pages (Browse for More)
- GitHub Topic: [credit-scoring](https://github.com/topics/credit-scoring?o=desc&s=updated)
- GitHub Topic: [credit-score](https://github.com/topics/credit-score?o=asc&s=stars)
- GitHub Topic: [home-credit-default-risk](https://github.com/topics/home-credit-default-risk)
- GitHub Topic: [lending-club](https://github.com/topics/lending-club)

### Specialised Repos for Your Thesis Prototype
| Repository | Why Relevant |
|-----------|--------------|
| **FynXai** (Hrishit-Patil) — AI credit scoring + OCR + XGBoost + SHAP + LIME | Directly shows how to combine alternative data + explainability |
| **Overview-Consumer-Credit-Risk-Assessment** (zhxmdy) | Credit dataset survey and comparison |
| **credit-scoring-mlflow** | Shows MLOps pipeline for credit models (production-ready) |

### How to Search GitHub for More
Search these terms on GitHub:
- `alternative credit scoring financial inclusion`
- `agricultural credit machine learning India`
- `microfinance credit risk python`
- `rural lending XGBoost`
- `SHG group lending machine learning`
- `satellite crop yield credit`

---

## 6. Datasets You Can Use for Your Prototype

### Ready-to-Use Datasets (Download Now)
| Dataset | Source | Features | Size | Link |
|---------|--------|----------|------|------|
| **Home Credit Default Risk** | Kaggle | 120+ features; payment history; previous applications | 300K rows | kaggle.com/c/home-credit-default-risk |
| **Give Me Some Credit** | Kaggle | 10 features; delinquency, debt ratio | 150K rows | kaggle.com/c/GiveMeSomeCredit |
| **Lending Club Loan Data** | Kaggle | 150+ features; loan grade, purpose, employment | 2.2M rows | kaggle.com/datasets/wordsforthewise/lending-club |
| **African Credit Scoring Challenge** | Zindi | Financial behaviour data; 2,000+ participants | — | zindi.world/competitions/african-credit-scoring-challenge |
| **Credit Scoring Utiva Challenge** | Kaggle | Africa-focused; alternative data | — | kaggle.com/competitions/credit-scoring-utiva-challenge |
| **Alternative Credit Scoring** (sai10py) | Kaggle | Alternative variable credit scoring dataset | — | kaggle.com/datasets/sai10py/alternative-credit-scoring |
| **Financial Inclusion in Africa** | Zindi | Who has bank accounts; 33K rows; East Africa | 33K | zindi.world/competitions/financial-inclusion-in-africa |
| **NABARD SHG Data** (e-Shakti) | NABARD Portal | SHG membership, savings, repayment records | Varies | nabard.org — request access |
| **PM-KISAN Beneficiary Data** | Data.gov.in | Farmer demographic + benefit data | Large | data.gov.in |
| **India Agriculture Statistics** | Indiastat | Credit flow, crop production, land records | — | indiastat.com |
| **Sentinel-2 Satellite Data** | ESA / Google Earth Engine | NDVI, crop health, land use | Free | earthengine.google.com |
| **IMD Rainfall Data** | India Met Department | District-level rainfall; drought risk | Free | imd.gov.in |

### How to Build Your Own Synthetic Dataset (for Prototype)
If real SHG data is unavailable, synthesise it:
```python
# Features to generate:
features = {
    # Demographics
    'age': [25, 65],
    'gender': ['M', 'F'],
    'district': [list_of_indian_districts],
    'caste_category': ['General', 'OBC', 'SC', 'ST'],
    
    # SHG-specific
    'shg_member_years': [0, 15],
    'shg_savings_monthly_avg': [100, 5000],  # INR
    'shg_meeting_attendance_pct': [0, 100],
    'shg_internal_lending_repaid_pct': [0, 100],
    'shg_credit_grade': ['A', 'B', 'C', 'D'],  # NABARD grades
    
    # Farmer-specific
    'land_holding_acres': [0.5, 10],
    'crop_type': ['Rice', 'Wheat', 'Cotton', 'Sugarcane', 'Vegetables'],
    'irrigation_access': [0, 1],
    'kcc_holder': [0, 1],
    'pm_kisan_beneficiary': [0, 1],
    
    # Alternative digital
    'mobile_recharge_monthly_avg': [50, 500],
    'upi_transactions_per_month': [0, 50],
    'electricity_bill_paid_ontime_pct': [0, 100],
    
    # Satellite-derived (proxy)
    'ndvi_score_last_season': [0.0, 1.0],
    'rainfall_deviation_pct': [-50, 50],  # vs normal
    
    # Target
    'default': [0, 1]  # 0 = repaid, 1 = defaulted
}
```

---

## 7. Competition Winners & Their Approaches

### Kaggle: Home Credit Default Risk (2018 — Still Most Relevant)
**Competition:** Predict loan default for borrowers with little/no credit history (exactly your use case)  
**7,198 teams; $70,000 prize pool**

**Winner approach (1st place — Aguiar):**
- Feature engineering on 7 tables (application, bureau, previous applications, payment history)
- 900+ engineered features using aggregation (mean, max, min, std of payment delays)
- LightGBM ensemble as primary model
- Stacking with neural network for final blend
- Key insight: **payment behaviour patterns** (how many days late, minimum payment ratio) were far more predictive than demographics

**Key GitHub solutions:**
- [minerva-ml/open-solution-home-credit](https://github.com/minerva-ml/open-solution-home-credit) — Full pipeline
- [kozodoi/Kaggle_Home_Credit](https://github.com/kozodoi/Kaggle_Home_Credit) — Clean implementation

**Lesson for your thesis:** Feature engineering on **behavioural sequences** (SHG repayment patterns over time) is more valuable than demographic data alone.

---

### Zindi: African Credit Scoring Challenge (2024–2025, $5,000 prize)
**1,020 active participants; Evaluation: F1-Score**

**Top approaches (based on Zindi community posts):**
- LightGBM / XGBoost ensembles dominated the leaderboard
- Feature interactions between payment history variables
- Class imbalance handling via SMOTE + class weighting
- Cross-validation strategy: stratified k-fold on target variable
- Winners required to submit credit scoring function that bins model output into risk categories

**Lesson:** F1-score optimisation for imbalanced datasets — critical since loan defaults are rare events (typically 5–20% of portfolio).

---

### Zindi: Financial Inclusion in Africa (Ongoing)
**Task:** Predict who has a bank account (financial inclusion classification)  
**Dataset:** 33,000 individuals across Kenya, Rwanda, Tanzania, Uganda  
**Variables:** Mobile money, education, employment, household size, remittances

**Top approaches:**
- Random Forest and XGBoost dominated
- Mobile money usage was the single strongest predictor
- Rural vs urban feature interaction was critical

**Lesson for SHG thesis:** Membership in group savings schemes was a strong positive predictor of financial inclusion — validates using SHG membership as a feature.

---

### RBI HaRBInger Hackathons (India-specific)

**HaRBInger 2025 (Completed):**
- Theme: Secure and Inclusive Banking
- Winners built: India CBDC innovations, tokenised KYC, AI fraud detection tools
- Financial inclusion track focused on reaching rural and un/underbanked

**HaRBInger 2024 (3rd Edition — Winners Announced January 2025):**
- Financial inclusion category winners built AI-driven KYC simplification for rural borrowers
- Approach: combining Aadhaar verification + alternative data scoring

**Takeaway for you:** RBI Hackathon themes directly validate your thesis topic. Consider submitting your prototype here.

---

### MIT Solve — Financial Inclusion Challenge
MIT Solve runs annual challenges on financial inclusion and economic prosperity. Past winners in this space have built:
- Community-based credit scoring using SHG group performance data
- Satellite + mobile data fusion models for farmer credit
- Voice-based financial literacy + scoring in local languages

**Relevant MIT Solve Winners to Study:**
- [solve.mit.edu/solutions/97520](https://solve.mit.edu/solutions/97520)
- [solve.mit.edu/solutions/85730](https://solve.mit.edu/solutions/85730)
- [solve.mit.edu/solutions/95241](https://solve.mit.edu/solutions/95241)

---

### Singapore FinTech Festival — Global SFF FinTech Award (2021)
**Winner:** FinScore (alternative credit scoring provider)  
FinScore uses telco data (call detail records, SMS, data usage patterns) to score unbanked individuals in Southeast Asia. Their model achieved 85%+ AUC vs 72% for traditional models on the same population.

**Key methodology:**
- Telco behavioural features: recharge recency, frequency, monetary value (RFM)
- Network topology features (who calls whom, call duration)
- XGBoost + logistic regression ensemble

---

## 8. Industry Players & Startup Ecosystem

### Global Leaders in Alternative Credit Scoring
| Company | Approach | Geography |
|---------|----------|-----------|
| **FICO (Score XD)** | Utility + mobile bills + non-trad data for thin-file borrowers | USA, global |
| **TransUnion (CreditVision)** | Alternative data + extended account history | 30+ countries |
| **Equifax** | ML on expanded data sources; machine learning pipelines | USA, India |
| **TrustDecision** | Behavioural biometrics + device intelligence | Asia |
| **Credolab** | Mobile metadata (60,000+ features from phone sensors) | Southeast Asia |
| **FinScore** | Telco CDR (Call Detail Record) analysis | Philippines, SE Asia |
| **Entrepreneurial Finance Lab (EFL)** | Psychometric scoring for SME loans | Emerging markets |
| **Begini** | Alternative data for SME lending | Global |
| **RiskSeal** | Digital footprint scoring | India, global |

### India-Specific Agrifintech Players
| Company | What They Do | AI/ML Use |
|---------|-------------|-----------|
| **CropIn** | Crop monitoring + satellite data → credit scoring for banks | Satellite imagery + ML for crop yield prediction |
| **Stellapps** | Dairy farmer data → credit scoring for dairy co-ops | IoT milk production data → creditworthiness |
| **Jai Kisan (Arboretum)** | Rural lending platform; alternative data scoring | ML-based rural credit underwriting |
| **FarMart** | Farmer procurement + credit linkage | Transaction data → credit scoring |
| **AgroStar** | Agri advisory + input credit | Farmer data aggregation |
| **Samunnati** | Agri value chain financing; SHG & FPO lending | Value chain data for credit decisions |
| **Dvara KGFS** | Financial inclusion for rural India; wealth management + credit | Financial health scoring |
| **Kinara Capital** | MSME / rural enterprise credit | Alternative data; 24-hour loan decisions |
| **Avanti Finance** | SHG and microfinance-adjacent lending | Digital credit infrastructure |
| **GoodScore** | AI credit health platform (₹13M Series A, 2025) | AI-powered credit improvement suggestions |

### MFI & SHG-Linked Lenders Using Technology
- **Bandhan Bank** — Grew from MFI; SHG linkage model
- **Ujjivan SFB** — Digital credit for microfinance clients
- **Spandana Sphoorty** — Technology-driven MFI credit assessment
- **CreditAccess Grameen** — SHG-linked rural credit
- **ESAF Small Finance Bank** — SHG group-based lending

---

## 9. India-Specific Context: SHGs, NABARD, KCC, RBI

### Self-Help Groups (SHGs) — Why They Matter for Your Model
- **12+ million SHGs** linked to banks via NABARD SHG-Bank Linkage Programme (SBLP)
- **~87 million members**, of whom **88%+ are women** (rural women empowerment)
- Total bank credit outstanding: ₹1.12 lakh crore (2024)
- SHGs are graded A/B/C/D by NABARD based on: meetings regularity, savings discipline, internal lending quality, repayment to bank, bookkeeping quality

**Why SHG data is gold for your model:**
The group guarantee structure means you have:
- Historical repayment data (group liability)
- Savings behaviour data (weekly/fortnightly savings)
- Social peer pressure effects on default risk
- Meeting attendance as proxy for engagement

### NABARD e-Shakti Initiative
- Digital platform that captures SHG data: savings, loans, repayments, member profiles
- Data available for research via NABARD — **contact NABARD's Micro Credit Innovations Department**
- e-Shakti has digitised 1.5+ million SHGs as of 2024

### Kisan Credit Card (KCC) Scheme
- 182 million cards issued; only ~10% utilisation
- Provides short-term credit for crop cultivation + allied activities
- Banks use crop area × MSP as credit limit proxy — no ML currently used!
- **Opportunity:** Your model can improve KCC credit limit setting using satellite-derived crop area and yield estimates

### RBI Regulatory Framework
- RBI's Account Aggregator (AA) Framework (2021) — enables consent-based data sharing for credit scoring
- DigiLocker for land records, crop insurance certificates
- OCEN (Open Credit Enablement Network) — API framework for embedded credit
- UPI transaction data as alternative credit signal (with AA consent)
- RBI HaRBInger hackathon validates regulatory appetite for innovation

### Key Indian Policy Documents for Literature Review
- RBI Report of the Internal Working Group on Digital Lending (2021)
- NABARD Annual Report 2024–25 (SHG-Bank Linkage data)
- NITI Aayog: Digital Payments — India's Leapfrog (2021)
- Ministry of Finance: Jan Dhan Yojana progress reports
- RBI Financial Inclusion Index (FI-Index) reports

---

## 10. Prototype Blueprint — Build Your ML Model

### Phase 1: Data Collection & Preparation
```
Data Sources:
1. Kaggle: Home Credit Default Risk dataset (baseline)
2. Zindi: African Credit Scoring Challenge dataset
3. Kaggle: Alternative Credit Scoring dataset
4. Synthetic SHG data (generate using the schema above)
5. Satellite NDVI proxy (Google Earth Engine free tier)
6. Publicly available Indian district rainfall data (IMD)

Tools:
- Python 3.11+
- pandas, numpy for data processing
- scikit-learn for baseline models
- XGBoost, LightGBM, CatBoost for main models
- PyTorch Geometric or DGL for GNN components
- SHAP for explainability
- MLflow for experiment tracking
```

### Phase 2: Feature Engineering (Most Important Step)
```python
# Critical feature groups for alternative credit scoring:

# 1. Repayment behaviour features (from SHG data)
df['repayment_consistency_score'] = ...  # Std dev of repayment delays
df['avg_days_late'] = ...
df['on_time_payment_rate'] = (timely_payments / total_payments)
df['savings_growth_rate'] = (current_savings - initial_savings) / months

# 2. Group dynamics features (SHG-specific)
df['group_cohesion_score'] = ...  # All members present at meetings
df['internal_lending_recovery_rate'] = ...
df['peer_default_rate_in_group'] = ...  # Network effect

# 3. Agricultural features
df['crop_income_stability'] = ...  # CV of income across seasons
df['ndvi_trend'] = ...  # Is crop health improving?
df['rainfall_adequacy'] = ...  # vs crop water requirement

# 4. Digital activity features
df['upi_velocity'] = upi_transactions / months_active
df['mobile_recharge_rfm'] = ...  # Recency, Frequency, Monetary

# 5. Socioeconomic features
df['asset_score'] = weighted_asset_index  # Land + livestock + equipment
df['pm_kisan_regular'] = ...  # Receives PM-KISAN on time
```

### Phase 3: Model Training & Evaluation
```python
# Train-test split respecting temporal order (crucial for credit)
# Use time-based split: train on years 1-3, test on year 4

# Key metrics for imbalanced credit dataset:
metrics = {
    'AUC-ROC': ...,          # Primary metric (0.75+ is good)
    'AUC-PR': ...,           # Better for imbalanced data
    'F1 Score': ...,         # Balance precision/recall
    'KS Statistic': ...,     # Classic credit scoring metric
    'Gini Coefficient': ..., # = 2*AUC - 1; industry standard
    'PSI': ...,              # Population Stability Index (drift monitoring)
}

# Handle class imbalance:
# Option 1: SMOTE oversampling (sklearn)
# Option 2: Class weights in XGBoost (scale_pos_weight)
# Option 3: Threshold tuning on probability output
```

### Phase 4: Credit Score Calibration
```python
# Convert model probability to 300-900 credit score
def probability_to_score(pd, min_score=300, max_score=900, pdo=20, base_score=600, base_odds=50):
    """
    pd: probability of default (0-1)
    pdo: points to double odds
    Standard credit scorecard calibration
    """
    import numpy as np
    factor = pdo / np.log(2)
    offset = base_score - factor * np.log(base_odds)
    odds = (1 - pd) / pd
    score = offset + factor * np.log(odds)
    return np.clip(score, min_score, max_score)
```

### Phase 5: Explainability Dashboard
```python
# SHAP values for each prediction
import shap
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test)

# For each borrower, output:
# "Your credit score is 680/900
# Top factors INCREASING your score:
#   + SHG repayment rate: 98% (excellent)
#   + Monthly savings: ₹1,200 (consistent)
# Top factors DECREASING your score:
#   - No digital payment activity
#   - Below-average NDVI (crop health concern)"
```

### Phase 6: Bias & Fairness Testing
```python
# Test for bias across:
# - Gender (women vs men in SHGs)
# - Caste category (SC/ST vs General)
# - Geography (irrigated vs rainfed districts)
# - Land holding size (marginal vs small farmers)

from aif360.metrics import BinaryLabelDatasetMetric
# Measure: disparate impact, equal opportunity difference
# Fix: reweighing, adversarial debiasing, calibrated eq. odds
```

### Recommended Tech Stack for Thesis Prototype
| Layer | Tool |
|-------|------|
| Data processing | Python, pandas, numpy |
| ML models | XGBoost, LightGBM, scikit-learn |
| Deep learning | PyTorch (LSTM, TabNet) |
| GNN (optional) | PyTorch Geometric, DGL |
| Explainability | SHAP, LIME |
| Experiment tracking | MLflow |
| Bias detection | IBM AIF360, Fairlearn |
| Visualisation | Matplotlib, Seaborn, Plotly |
| Web dashboard | Streamlit (fastest for prototype demo) |
| Geospatial | Google Earth Engine, geopandas |

---

## 11. Thesis Angles & Research Gaps

### Identified Research Gaps (Use These to Frame Your Contribution)

1. **SHG-specific ML model** — Almost no papers have built a credit scoring model explicitly using SHG internal transaction data as features. This is your biggest unique contribution.

2. **Multilayer data fusion for Indian farmers** — Most papers use one data type. A model combining SHG records + satellite NDVI + mobile behaviour + KCC data has not been built and published for the Indian context.

3. **Fairness/bias in rural credit AI** — Very few papers examine algorithmic bias along caste/gender lines for Indian agricultural credit. This is both a research gap and a policy imperative.

4. **Vernacular NLP for credit** — NLP on Hindi/regional language loan applications and SHG meeting notes is unexplored territory.

5. **GNN on SHG group networks** — Treating SHG members as nodes in a social graph (connected by membership, internal lending) and using GNN for scoring is novel.

6. **Explainability for field officers** — Translating SHAP explanations into actionable, simple-language feedback for rural bank field officers is an HCI/AI research gap.

7. **Dynamic credit scoring** — Most models are static; building a model that updates scores seasonally (with crop cycle) is novel for India.

### Suggested Thesis Structure
```
Chapter 1: Introduction
  - Problem statement: credit exclusion of rural India
  - Research objectives
  - Scope (farmers + SHGs + rural enterprises)
  
Chapter 2: Literature Review
  - Traditional credit scoring limitations
  - ML in credit scoring (2015–2026 survey)
  - Alternative data: types, challenges, regulations
  - SHG-Bank Linkage Programme: data potential
  
Chapter 3: Methodology
  - Data collection: sources and justification
  - Feature engineering framework
  - Model selection and architecture
  - Evaluation metrics
  - Explainability approach
  - Fairness testing methodology
  
Chapter 4: Results
  - Baseline vs alternative data models
  - Model performance comparison
  - SHAP analysis: key credit drivers
  - Fairness audit results
  
Chapter 5: Discussion
  - Comparison with existing literature
  - Policy implications
  - Limitations
  
Chapter 6: Conclusion & Future Work
  - Prototype overview
  - Recommendations for NABARD/RBI/MFIs
  - Future: federated learning, vernacular NLP, GNN
```

---

## 12. LinkedIn & Online Communities to Follow

### Key Thought Leaders to Follow on LinkedIn
Search and follow these terms/people on LinkedIn:
- **Sumit Agarwal** (NUS) — Co-author of landmark fintech financial inclusion paper
- **Pulak Ghosh** (IIM Bangalore) — ML + fintech + India
- Search: `#AlternativeCreditScoring` `#AgriFintech` `#FinancialInclusion` `#RuralFinance`
- Search: `#SHGBankLinkage` `#KisanCreditCard` `#NABARD`

### Key LinkedIn Articles to Search
- "Alternative Credit Scoring in India" — RBL Bank Blog
- "How AI is transforming rural credit in India" — Multiple Inc42 authors
- "NABARD SHG digitisation: what it means for credit" — Banking sector articles
- "Satellite data for farm lending" — AgriBazaar blog

### Online Communities
| Community | Platform | What You'll Find |
|-----------|----------|-----------------|
| **Zindi** | zindi.world | African ML competitions; credit scoring challenges; winner code |
| **Kaggle** | kaggle.com | Global datasets + notebooks + competition discussions |
| **FinDev Gateway** | findevgateway.org | Microfinance + financial inclusion research hub |
| **CGAP Blog** | cgap.org/blog | World Bank fintech inclusion insights |
| **IFC Publications** | ifc.org | IFC reports on emerging market lending |
| **NABARD Publications** | nabard.org | SHG data, annual reports, e-Shakti updates |
| **Hugging Face** | huggingface.co | NLP models for vernacular credit applications |
| **Papers With Code** | paperswithcode.com | ML papers + code for credit scoring |

### Key Newsletters & Portals
- **FinanceInclusion.tech** — Alternative data + fintech
- **Inc42** (inc42.com) — Indian fintech startup coverage
- **The Ken** (the-ken.com) — Deep-dive Indian fintech journalism
- **Mint / Economic Times / Business Standard** — NABARD, RBI, SHG policy news

---

## 13. Full Reference List

### Academic Papers
1. AnilKumar & Sharma. "Machine Learning (ML) Technologies for Digital Credit Scoring in Rural Finance: A Literature Review." *MDPI Risks* 9(11), 192. 2021. https://www.mdpi.com/2227-9091/9/11/192

2. Agarwal, S., Alok, S., Ghosh, P., & Gupta, S. "Financial Inclusion and Alternate Credit Scoring: Role of Big Data and Machine Learning in Fintech." *SSRN Working Paper #3507827*. 2020. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3507827

3. "Enhancing Credit Scoring Accuracy with a Comprehensive Evaluation of Alternative Data." *PLOS ONE / PMC 11108212*. 2024. https://pmc.ncbi.nlm.nih.gov/articles/PMC11108212/

4. "Design of Contextual Agricultural Credit Scoring Model for Kisan Credit Card Scheme in India: An Application of NLP and Machine Learning." *ScienceDirect (S0970389626000352)*. 2026. https://www.sciencedirect.com/science/article/pii/S0970389626000352

5. Chai et al. "Growth Potential of Machine Learning in Credit Risk Predicting of Farmers in the Industry 4.0 Era." *International Journal of Finance & Economics*, Wiley. 2025. https://onlinelibrary.wiley.com/doi/10.1002/ijfe.3010

6. "Impact of Social Networks on Digital Credit Assessment for Rural Residents: A Study Using Machine Learning Methods." *Information Systems Frontiers*, Springer. 2025. https://link.springer.com/article/10.1007/s10796-025-10630-1

7. "Artificial Intelligence and SHGs: Enabling Financial Inclusion in India." *ResearchGate #343122520*. 2020. https://www.researchgate.net/publication/343122520_Artificial_Intelligence_and_SHGs_Enabling_Financial_Inclusion_in_India

8. "From Data to Dignity: AI-Powered Credit Scoring for an Inclusive India." *ResearchGate #397640896*. 2025. https://www.researchgate.net/publication/397640896_From_Data_To_Dignity_Ai-Powered_Credit_Scoring_For_An_Inclusive_India

9. "Role of Fintech and Alternative Credit Scoring Methods in Accelerating Financial Inclusion of Smallholder Farmers in India." *ResearchGate #383694168*. 2024. https://www.researchgate.net/publication/383694168_Role_of_Fintech_and_Alternative_Credit_Scoring_Methods_in_Accelerating_the_Financial_Inclusion_of_Smallholder_Farmers_in_India

10. "AI-Powered Credit Scoring Models: Transforming Financial Inclusion in Rural India." *IRT / Shodh Sagar*. 2024. https://irt.shodhsagar.com/index.php/j/article/view/1513

11. "Machine Learning & AI Powered Credit Scoring for Islamic Microfinance + Blockchain." *MDPI Risks 14(1), 12*. 2026. https://doi.org/10.3390/risks14010012

12. "Hybrid Boosted Attention-Based LightGBM for Enhanced Credit Risk Assessment." *Nature: Humanities and Social Sciences Communications*. 2025. https://www.nature.com/articles/s41599-025-05230-y

13. "Attention-Based Dynamic Multilayer Graph Neural Networks for Loan Default Prediction." *European Journal of Operational Research, ScienceDirect*. 2024. https://www.sciencedirect.com/science/article/pii/S0377221724007288

14. "FSL-BDP: Federated Survival Learning with Bayesian Differential Privacy for Credit Risk." *arXiv 2601.11134*. 2026. https://arxiv.org/html/2601.11134

15. "Explainable AI (XAI) Using SHAP and LIME for Credit Scoring." *ResearchGate #391998247*. 2025. https://www.researchgate.net/publication/391998247_Explainable_AI_XAI_Using_SHAP_and_LIME_for_Financial_Fraud_Detection_and_Credit_Scoring

16. "Interpretable AI in Credit Scoring: Comparative Survey of SHAP, LIME, Hybrid Approaches." *R Discovery*. 2025. https://discovery.researcher.life/article/interpretable-ai-in-credit-scoring

17. "A Study of AI-Based Credit Scoring Tools in Rural Nigeria." *WJARR*. 2025. https://wjarr.com/sites/default/files/fulltext_pdf/WJARR-2025-2884.pdf

18. "Enhancing Credit Scoring with Alternative Data." *SEEJPH*. 2024. https://www.seejph.com/index.php/seejph/article/download/3584/2381/5422

19. "The Effect of AI-Enabled Credit Scoring on Financial Inclusion: Evidence from 1M+ Underserved Population." *MIS Quarterly* 48(4). 2024. https://misq.umn.edu/misq/article/48/4/1803/2314/

20. "Credit Risk Analysis for SMEs Using Graph Neural Networks in Supply Chain." *ACM BDAIDE 2025*. 2025. https://dl.acm.org/doi/full/10.1145/3767052.3767065

21. "Transaction Graph-Based Predictive Model for Credit Scoring in DeFi." *Int. Journal of Data Science & Analytics*, Springer. 2026. https://link.springer.com/article/10.1007/s41060-026-01097-7

22. "Satellite Monitoring: How Banks Use Space Data to Assess Farm Lending." *AgroTech Space*. 2025. https://agrotech.space/2025/05/23/satellite-monitoring-banks-farm-lending/

23. "Big Data Architecture for Credit Assessment of Farmers Using Satellite Data." *Medium / Rhavif Budiman*. https://rhavifbudiman.medium.com/big-data-architecture-for-credit-assessment-of-farmers-using-satellite-data-f544e3523445

24. "Drivers of Credit Uptake by Smallholder Farmers: Evidence from India." *ResearchGate #403832987*. 2024. https://www.researchgate.net/publication/403832987_Drivers_of_Credit_Uptake_by_Smallholder_Farmers

### Institutional Reports
25. IFC. *Cracking the Credit Code: Alternative Data and AI for Financial Inclusion*. World Bank Group, 2026. https://www.ifc.org/en/insights-reports/2026/cracking-the-credit-code-alternative-data-and-ai-for-financial-inclusion

26. Alliance for Financial Inclusion (AFI). *Alternative Data for Credit Scoring: Special Report*. January 2025. https://afi-global.org/wp-content/uploads/2025/02/Alternative-Data-for-Credit-Scoring.pdf

27. World Bank. *The Use of Alternative Data in Credit Risk Assessment: Opportunities and Risks*. 2025. https://documents1.worldbank.org/curated/en/099031325132018527/pdf/P179614-3e01b947-cbae-41e4-85dd-2905b6187932.pdf

28. CGAP. *Innovation for Inclusion: Roadmap for Inclusive Finance Policy*. 2025. https://www.cgap.org/research/innovation-for-inclusion-roadmap-for-inclusive-finance-policy

29. FAO STI Portal. *Alternative Data Credit Scoring Platforms for Smallholder Farmers*. 2024. https://sti-portal.fao.org/classes/alternative-data-credit-scoring-platforms-smallholder-farmers

30. World Economic Forum. "How AI Credit Scoring Models Can Boost Financial Inclusion." 2025. https://www.weforum.org/stories/2025/10/how-responsibly-deploying-ai-credit-scoring-models-can-progress-financial-inclusion/

31. World Bank / NABARD. *SHG-Bank Linkage: A Success Story*. Open Knowledge. https://openknowledge.worldbank.org/entities/publication/780d5067-4b75-5988-80f7-62dea6b492e1

32. CGAP. *Innovative Financing for Inclusive Credit Fintechs in Africa*. Focus Note. https://www.cgap.org/sites/default/files/publications/FN_Innovative%20Funding%20Approaches_final_0_1.pdf

33. Caribou Global. *Launching into Space: Using Satellite Imagery in Financial Services*. 2024. https://caribou.global/publications/launching-into-space-using-satellite-imagery-in-financial-services/

### Competition & Platform Resources
34. Zindi African Credit Scoring Challenge. https://zindi.world/competitions/african-credit-scoring-challenge
35. Zindi Financial Inclusion in Africa. https://zindi.world/competitions/financial-inclusion-in-africa
36. Kaggle Home Credit Default Risk. https://www.kaggle.com/c/home-credit-default-risk
37. Kaggle Give Me Some Credit. https://www.kaggle.com/c/GiveMeSomeCredit
38. Kaggle Alternative Credit Scoring Dataset. https://www.kaggle.com/datasets/sai10py/alternative-credit-scoring
39. MIT Solve Financial Inclusion Challenges. https://solve.mit.edu

### GitHub Repositories
40. minerva-ml/open-solution-home-credit. https://github.com/minerva-ml/open-solution-home-credit
41. kozodoi/Kaggle_Home_Credit. https://github.com/kozodoi/Kaggle_Home_Credit
42. Hrishit-Patil/FynXai. https://github.com/Hrishit-Patil/FynXai
43. shashi-hue/loan-default-risk-system. https://github.com/shashi-hue/loan-default-risk-system
44. FajrinCd/home-credit-default-risk-complete. https://github.com/FajrinCd/home-credit-default-risk-complete
45. pklauke/Kaggle-HomeCreditDefaultRisk. https://github.com/pklauke/Kaggle-HomeCreditDefaultRisk

### Industry / News Sources
46. RBI HaRBInger 2025 Hackathon Results. https://www.cryptotimes.io/2026/05/19/rbi-harbinger-2025-winners-feature-india-cbdc-tokenised-kyc-ai-fraud-tools/
47. India Alternative Lending Market Report 2025. https://www.globenewswire.com/news-release/2026/01/05/3212542/0/en/India-Alternative-Lending-Market-Report-2025
48. AgriBazaar. "From Satellite Data to Smarter Loans." https://blog.agribazaar.com/from-satellite-data-to-smarter-loans-how-digital-farm-intelligence-is-transforming-agriculture/
49. Alternative Credit Scoring in India — RBL Bank. https://www.rbl.bank.in/blog/banking/credit-cards/expanding-financial-access-with-alternative-scoring
50. India AI in Agriculture Credit Scoring Market. https://www.researchandmarkets.com/reports/6209853/india-ai-in-agriculture-credit-scoring-market

---

*This document is a live research reference. Update as new papers and competition results emerge. Last updated: August 2026.*
