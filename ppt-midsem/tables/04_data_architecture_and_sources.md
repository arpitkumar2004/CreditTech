# Table 4: Data Architecture, Data Sources & Predictive Hypotheses

| Data Category | Representative Data Source / Entity | Statutory & Consent Basis (DPDP / DEPA) | Core Features Extracted | Economic Credit Hypothesis (What It Predicts) |
| :--- | :--- | :--- | :--- | :--- |
| **Financial Cashflow &amp; Banking** | Account Aggregator (AA) framework; 17 RBI-licensed AAs; 284.6M+ accounts linked | DEPA-compliant electronic consent artifact (time-bound, revocable, purpose-limited to `CREDIT_SCORING`) | • Average Daily Balance (ADB)<br>• Monthly UPI inflow frequency<br>• Count of zero-balance days<br>• Inflow-to-obligation ratio | Regularity of cash inflows and buffer liquidity predict near-term debt servicing capacity and cashflow volatility. |
| **Geospatial &amp; Crop Health** | Sentinel-2 multispectral satellite imagery (10m resolution, 5-day revisit) via SatSure | Farmer consent + public land boundary coordinates accessed under state RTI rules | • Mean Kharif/Rabi NDVI vigor<br>• Historical yield deviation (3-yr)<br>• IMD district drought anomaly index<br>• Crop classification confidence (90–95%) | Vegetative vigor and weather resilience predict seasonal crop yield, protecting against agricultural production risk. |
| **Community &amp; Social Capital** | DAY-NRLM e-Shakti SHG ledgers, FPO membership registries, JLG books | Group resolution from SHG Federation / FPO Board + individual member digital opt-in | • SHG membership tenure (months)<br>• Internal thrift savings ratio (actual vs pledged)<br>• Meeting attendance rate (%)<br>• Historical internal loan default count | Sustained peer thrift and group solidarity reflect uncollateralised "Character" and social collateral (96%+ repayment track). |
| **Market &amp; Value-Chain** | e-NAM (National Agriculture Market) electronic mandi receipts, dairy coop records | Platform data-sharing agreement executed with consenting farmer / producer | • Realised crop sales volume (quintals)<br>• Mandi modal price realization<br>• Daily milk pouring consistency (dairy)<br>• Buyer concentration index | Verified off-take transactions demonstrate commercial viability, market access, and realized agricultural income. |
| **Government Welfare &amp; Entitlements** | PM-KISAN database, MISS subsidy records, State Kisan Credit Card registries | Government-to-citizen DPI consent under Jan Samarth / ULI gateway | • PM-KISAN DBT installment regularity<br>• Active KCC operational limit<br>• Interest subvention eligibility flag | Baseline cash income floor from DBT subsidies guarantees minimum household subsistence during adverse price shocks. |
| **Credit Bureau (When Available)** | TransUnion CIBIL / Equifax / Experian / CRIF High Mark | Explicit statutory credit pull consent under Credit Information Companies Act (2005) | • Number of inquiries in past 12 months<br>• Existing formal credit outstanding<br>• Any historical delinquency flag | Acts as a corroborating indicator of over-indebtedness; absence of bureau file does NOT penalize or halt underwriting. |
| **Data Minimisation Exclusions** | *Strictly Excluded by Architecture* | Non-consensual or discriminatory attributes barred under DPDP Act 2023 | • Caste, religion, or community identity<br>• Mobile contact books &amp; SMS logs<br>• Precise geolocation tracking | **Statutory Safeguard:** Eliminates direct and proxy discrimination; prevents predatory digital lending abuses. |

---

### Physical & Cryptographic Data Separation Model

```
┌────────────────────────────────────────────────────────────────────────┐
│                        RAW PII STORAGE (AES-256)                       │
│  Table: `borrowers` (Encrypted at Rest, Isolated Tenant Schema)        │
│  • id: UUID (Primary Key)                                              │
│  • full_name_encrypted: VARBINARY (AES-256-GCM)                        │
│  • mobile_hash: VARCHAR(64) (HMAC-SHA256 with rotating salt)           │
│  • aadhaar_token_hash: VARCHAR(64) (UIDAI Vault Token)                 │
│  • consent_ledger_ref: UUID (FK to immutable audit log)                │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                         One-Way Identifier Hash
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│                   ANONYMOUS FEATURE STORE & SCORING                    │
│  Table: `feature_snapshots` (Zero PII, Pure Numerical Vectors)         │
│  • snapshot_id: UUID                                                   │
│  • borrower_hash: VARCHAR(64) (Opaque Pseudonym)                       │
│  • 21 Normalized Numerical Domain Features (WoE Binned)                │
│  • Table: `credit_scores` (score: 300–900, confidence_band: ±15 to ±45)│
│  • Table: `shap_explanations` (closed-form feature point attributions) │
└────────────────────────────────────────────────────────────────────────┘
```
