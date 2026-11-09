# Table 9: Security, Privacy & Regulatory Compliance Matrix

| Regulatory Regime / Statutory Act | Governing Authority | Statutory Requirement & Scope | CreditTech Implementation Mechanism |
| :--- | :--- | :--- | :--- |
| **RBI Digital Lending Directions (Sept 2022 / Revised 2025)** | Reserve Bank of India (Department of Regulation) | • Regulated Entities (REs) must retain sole underwriting and sanction authority.<br>• CreditTech must operate strictly as a **Lending Service Provider (LSP)**.<br>• Direct fund disbursement to borrower bank account (no escrow/pass-through).<br>• Provision of Key Facts Statement (KFS) and cooling-off period. | • CreditTech provides decision-support scoring only; never touches borrower loan funds or disbursals.<br>• Mandatory underwriter cockpit ensures human-in-the-loop sanctioning.<br>• Automated generation of standardized KFS and APR disclosures. |
| **Default Loss Guarantee (DLG / FLDG) Guidelines (June 2023)** | Reserve Bank of India | • First-Loss Default Guarantees capped at **5% of total loan portfolio**.<br>• Must be backed by fixed deposits, cash, or bank guarantees.<br>• Invocation timeline capped at 120 days of default. | • Partner agreements strictly capped at $\le 5\%$ portfolio DLG.<br>• Eliminates uncapped balance-sheet credit risk for the technology platform. |
| **Digital Personal Data Protection (DPDP) Act 2023 &amp; Rules 2025** | Data Protection Board of India / MeitY | • Consent must be free, specific, informed, unconditional, and revocable.<br>• Strict Purpose Limitation bound to credit underwriting.<br>• Mandatory Data Breach Notification within 72 hours.<br>• Storage limitation: data wiped once purpose is fulfilled. | • SHA-256 hash-chained immutable consent ledger ($H_n = \text{SHA256}(H_{n-1} \parallel \text{Tx} \parallel t)$).<br>• Background `DataRetentionWorker` executes cryptographic PII wipes after 30-day underwriting TTL.<br>• 60-second revocation execution. |
| **Account Aggregator Master Directions (RBI 2016, amended 2023)** | Reserve Bank of India (FinTech Department) | • Data-blind transmission: AAs cannot view or store transmitted financial data.<br>• Financial Information Users (FIUs) must decrypt data only under explicit consent. | • Certified FIU integration via licensed AA gateway.<br>• Ephemeral memory decryption; raw JSON bank statements immediately transformed into numerical feature vectors. |
| **Credit Information Companies (Regulation) Act (CICRA 2005)** | Reserve Bank of India | • Bureau data can only be accessed with explicit borrower consent.<br>• Strict prohibition against unauthorized secondary commercialization. | • Single-use consent token; credit bureau pull used exclusively to identify over-indebtedness; absence of bureau history does not penalize score. |
| **Algorithmic Fairness &amp; Model Governance** | Self-Imposed Technical Safeguards (IIT Kharagpur) | • Non-discrimination across gender, social caste, and marginal landholding cohorts.<br>• Prevention of proxy-variable discrimination (e.g. zip code standing in for caste). | • **Pre-promotion FairnessGate:** Enforces Disparate Impact Ratio (DIR) $\ge 0.80$ (Four-Fifths Rule).<br>• Blocks model deployment with HTTP 409 Conflict if disparity exceeds threshold.<br>• Continuous Population Stability Index (PSI &lt; 0.10) monitoring. |

---

### Security Controls Summary

| Security Domain | Architectural Control Implemented | Verification Invariant |
| :--- | :--- | :--- |
| **Encryption at Rest** | AES-256-GCM encryption on all sensitive database fields (name, phone, Aadhaar token). | Raw PII is completely unreadable without KMS key injection. |
| **Encryption in Transit** | TLS 1.3 enforced across all external and internal API calls; strict HSTS enabled. | Plaintext HTTP requests automatically dropped or upgraded. |
| **API Perimeter Defense** | Rate limiting (240 req/min), Request ID middleware, 1 MiB payload size ceiling. | Prevents DDoS attacks and memory exhaustion exploits. |
| **Tamper-Evidence** | PostgreSQL row-level DDL triggers enforcing append-only immutability on decision and grievance tables. | Modifying or deleting a historical credit decision raises database exception. |
| **Auditing &amp; Recourse** | End-to-end trace ID logged across all micro-events; RBI ombudsman escalation pathway. | Full reproducibility of every credit score generated within past 7 years. |
