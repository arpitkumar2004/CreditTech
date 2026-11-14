# CreditTech Relational Schema & Integrity Invariant Matrix

This specification details the structural architecture, primary and foreign key constraints, cardinality, and statutory regulatory invariants governing the CreditTech platform database.

| Entity | Primary Key | Foreign Keys | Cardinality | Key Constraints & Invariants | Regulatory Purpose |
| :--- | :--- | :--- | :---: | :--- | :--- |
| **`borrowers`** | `id` (UUID) | `village_id` (VARCHAR) | Anchor | `aadhaar_hash` is unique salted SHA-256; direct mobile phone numbers encrypted at rest with AES-256-GCM; direct PII isolated from model feature matrix $X$. | DPDP Act 2023 Citizen Sovereignty & PII Shield |
| **`consent_records`** | `id` (UUID) | `borrower_id` (UUID) | 1 : N | Immutable append-only; cryptographic SHA-256 hash chaining $H_n = \text{SHA256}(H_{n-1} \parallel \text{Payload}_n)$; status in `GRANTED`, `REVOKED`, `EXPIRED`; unilateral revocation instantly blocks downstream scoring. | DPDP Act 2023 Purpose Limitation & Revocability |
| **`feature_snapshots`** | `id` (UUID) | `borrower_id` (UUID), `consent_id` (UUID) | 1 : N | Persists the 21 continuous and categorical 5-Cs features at loan application time; strictly immutable; zero in-place updates. | BCBS SR 11-7 Model Governance & Audit Freeze |
| **`score_results`** | `id` (UUID) | `feature_id` (UUID) | 1 : 1 | `scaled_score` bounded strictly between 300 and 900 points; `decision_zone` derived deterministically from policy cutoffs; persists local TreeSHAP reason codes in bilingual JSON (Hindi/English). | RBI Digital Lending Guidelines (2022) Clause 6.3 |
| **`applications`** | `id` (UUID) | `borrower_id` (UUID), `score_id` (UUID) | 1 : N | Unique composite constraint `(borrower_id, created_at)` prevents duplicate concurrent open applications; state machine: `PENDING` $\rightarrow$ `UNDERWRITTEN` $\rightarrow$ `SANCTIONED` \| `REJECTED`. | Core Credit Origination State Machine |
| **`officer_decisions`** | `id` (UUID) | `application_id` (UUID) | 1 : 1 | Append-only table guarded by SQLite trigger preventing UPDATE or DELETE; database trigger strictly requires `override_reason` and free-text `justification_note` if `is_override = True`. | Statutory Underwriting Dissent Audit Trail |
| **`re_handoffs`** | `id` (UUID) | `application_id` (UUID) | 1 : 1 | Generates external reference idempotency token and SHA-256 payload digest for transmission to Regulated Entity (RE) partner Core Banking Systems (CBS). | Commercial Bank CBS Interoperability |
| **`grievance_records`** | `id` (UUID) | `borrower_id` (UUID) | 1 : N | `sla_deadline` automatically computed as `created_at + 30 days`; status machine: `OPEN` $\rightarrow$ `IN_REVIEW` $\rightarrow$ `RESOLVED`; auditable resolution notes. | RBI Digital Lending Statutory 30-Day SLA Redressal |
| **`audit_events`** | `id` (UUID) | None | 1 : N | Append-only system event bus logging `actor_role`, `actor_id`, `endpoint`, and `payload_hash`; protected against modification by triggers. | Non-Repudiation Security & Regulatory Compliance |
| **`model_promotions`** | `id` (UUID) | None | 1 : N | Logs candidate and champion semantic version tags; records automated Fairness Gate disparity scores (Gender $\le 20\%$, Landholding $\le 25\%$); requires multi-party sign-off to bypass. | RBI Fair Lending & Algorithmic Parity Oversight |

