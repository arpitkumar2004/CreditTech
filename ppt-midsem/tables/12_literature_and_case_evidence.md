# Table 12: Literature, Policy & Real-World Case Evidence Synthesis

### 12.1 Foundational Literature Synthesis & CreditTech Architectural Response

| Research Stream | Seminal Citations | Core Empirical / Theoretical Finding | CreditTech Architectural & Design Response |
| :--- | :--- | :--- | :--- |
| **Predictive Value of Alternative Footprints** | • Berg et al. (2020), *Rev. Fin. Studies*<br>• FAO STI Portal (2020)<br>• Kshetri (2021), *Risks* | Behavioural digital footprints and non-financial metadata predict default risk as well as, or better than, credit bureau scores for thin-file borrowers. | **Multi-Rail Ingestion Engine (M2):** Ingests Account Aggregator cashflows, Sentinel-2 satellite NDVI, and SHG community savings to construct a holistic 5-Cs profile. |
| **Smallholder Data Sparsity & Seasonality** | • ScienceDirect Systematic Review (2025)<br>• Njuguna &amp; Sowon (2020), *ACM AfriCHI* | Generic urban ML models fail in agriculture because farm income is episodic (120-day crop cycles) and data is sparse; requires domain-specific feature engineering. | **Crop-Cycle Aware Feature Store (M3):** Computes cashflow volatility relative to Kharif/Rabi harvest schedules; applies monotonic WoE binning with Laplace smoothing. |
| **Social Collateral in Group Microcredit** | • PIB / DAY-NRLM (2025)<br>• NAFIS (2021–22), NABARD | SHG-Bank Linkage sustains &gt;96% repayment discipline through peer monitoring and collective trust, yet remains completely invisible to CIBIL/Experian. | **Character Feature Rail:** Treats SHG membership tenure, thrift savings regularity, and meeting attendance as primary predictive features (Information Value: 0.42–0.68). |
| **Algorithmic Fairness &amp; Governance** | • Bücker et al. (2020), *JORS*<br>• Agosto et al. (2023), *Data Science*<br>• JMSRR Systematic Review (2026) | Bias in credit scoring stems from historical training data and proxy variables (e.g. zip code proxying caste). Explainability and fairness must be enforced algorithmically. | **Automated Pre-Promotion FairnessGate (M5):** Mandates Disparate Impact Ratio (DIR) $\ge 0.80$ across gender and landholding cohorts; deploys exact closed-form bilingual SHAP. |
| **DPI Adoption &amp; Integration Friction** | • Advances in Consumer Research (2025)<br>• Business Standard / ULI (2026) | While Account Aggregator has scaled to 284M+ accounts, large-lender adoption of ULI and land digitization remain uneven across districts. | **Graceful Degradation Architecture:** System never hard-fails on API timeouts; rescales feature weights and widens confidence intervals ($\pm 45$ vs $\pm 15$). |

---

### 12.2 Real-World Case Evidence (Operational Analogues)

| Operational Fintech / Platform | Scale & Market Footprint | Operating Architecture & Data Ingested | Reported Real-World Impact & Credit Outcome | CreditTech Relevance & Differentiation |
| :--- | :--- | :--- | :--- | :--- |
| **Kaleidofin (Ki Score / Ki View)** | • 10M+ customers decisioned (98% women).<br>• ~$8B disbursements enabled.<br>• 57+ partner MFIs, NBFCs, banks. | Combines geospatial socio-economic indices, customer contextual behaviour, and cashflow data. | • **+20% to +30% approval uplift** over traditional bureau models.<br>• Portfolio-at-Risk (PAR90) maintained **&lt; 2.0%**. | Proves alternative scoring works at scale in India; CreditTech extends this with open DPI rails (AA + ULI) and public fairness gates. |
| **SatSure (SatSource / SatCollect)** | • Statewide deployment in Uttar Pradesh (17–18% of India's KCC accounts).<br>• Commercial bank partnerships (SBI, ICICI). | 13 spectral satellite bands, 5-day revisit, cadastral boundary overlay, road/market density. | • **90% to 95% crop-ID accuracy**.<br>• Cut agricultural loan turnaround time from **10–15 days to &lt; 30 minutes**. | Validates Sentinel-2 satellite imagery as an institutional underwriting input recognized by commercial banks. |
| **Global Benchmark: Upstart &amp; Tala** | • Upstart (US, AI underwriting).<br>• Tala (Emerging markets, 7.5M+ borrowers). | Mobile device metadata, behavioral cashflow, non-traditional transaction trails. | • **20% to 44% approval rate uplift**.<br>• Tala: 63% are first-time borrowers; 84% reported improved livelihood quality. | Confirms global viability of alternative credit scoring for financial inclusion, while highlighting need for strong privacy guardrails. |
| **RBI Unified Lending Interface (ULI)** | • National public infrastructure.<br>• ₹27,000 Crore disbursed across 600,000 loans (Dec 2024). | Universal consent gateway connecting land records, satellite data, milk cooperatives, and bank CBS. | • Standardises digital KCC appraisal.<br>• Constrained by land record silos and cautious bank adoption. | CreditTech integrates directly with ULI as an intelligent scoring layer, resolving the data-friction bottleneck for partner RRBs. |

---

### 12.3 Stated Academic Research Gap Justifying CreditTech

> **The Empirical Research Gap:**  
> The existing literature and commercial fintech deployments (Kaleidofin, SatSure, Upstart) demonstrate that alternative data can successfully predict credit risk at the national portfolio level.  
> However, **there is currently no open, scientifically evaluated, multi-institution framework that simultaneously integrates:**  
> 1. India's public Digital Public Infrastructure stack (**Account Aggregator + ULI**),  
> 2. Community social collateral (**SHG e-Shakti and FPO collective trust**),  
> 3. An enforceable, pre-deployment **algorithmic fairness gate (DIR $\ge 0.80$)**,  
> 4. Validated through a **reproducible village-level empirical benchmark across multiple agro-climatic zones**.  
>  
> CreditTech is specifically engineered to bridge this gap, providing an auditable, open-architecture blueprint for academic defense and institutional adoption.
