# CreditTech Persona & Role Matrix

This document defines the **canonical authorization source of truth** for all user personas interacting with the CreditTech platform.

---

## 1. Persona Definitions

| Persona Code | Persona Name | Representative Identity | Primary Domain & Responsibility | Channel / Client |
|---|---|---|---|---|
| `GUEST` | Anonymous Caller | Unauthenticated | Public status checks, health monitoring, API documentation | Web / cURL |
| `BORROWER` | Rural Borrower / Farmer | Radhika Devi (`BORROWER-A1`), Sita Kumari (`BORROWER-A2`) | Consents to data sharing, views own score report, files appeals/disputes | Web Portal / Mobile Web |
| `BANK_SAKHI` | Field Business Correspondent | Sunita Devi (`SAKHI-001`), Anita Bai (`SAKHI-002`) | Assisted onboarding, captures SHG/FPO records, initiates multi-rail aggregation | Field Web App (Tablet/Mobile) |
| `LOAN_OFFICER` | Branch Credit Officer | Rajesh Kumar (`OFF-001`), Vikram Singh (`OFF-002`) | Assesses applicant risk, reviews SHAP explanations, enters dissent overrides, records credit decisions | Officer Desktop Portal |
| `RISK_OFFICER` | Institutional Risk Auditor | Priya Sharma (`RISK-001`) | Audits demographic & geographic fairness parity, evaluates fairness gate, inspects model risk | Risk Management Console |
| `ADMIN` / `ML_ENGINEER` | ML Ops & System Administrator | Amit Verma (`ADMIN-001`) | Manages model registry lifecycle, triggers model promotion gates, configures system policies | Admin CLI & Portal |
| `RE_PARTNER` | Regulated Lending Institution | Partner Bank Core Banking System | Ingests structured loan packages, receives immutable audit logs & hash chains | Automated API Webhooks |

---

## 2. Authentication & Identity Headers Contract

In the pilot environment, authentication is header-based to facilitate integration testing and demonstration:

| Persona | Header Keys & Sample Values |
|---|---|
| `GUEST` | *(None)* |
| `BORROWER` | `X-Borrower-Id: 00000000-0000-0000-0000-000000000001` |
| `BANK_SAKHI` | `X-Officer-Id: SAKHI-001`, `X-Officer-Role: BANK_SAKHI` |
| `LOAN_OFFICER` | `X-Officer-Id: OFF-001`, `X-Officer-Role: LOAN_OFFICER` |
| `RISK_OFFICER` | `X-Officer-Id: RISK-001`, `X-Officer-Role: RISK_OFFICER` |
| `ADMIN` / `ML_ENGINEER` | `X-Officer-Id: ADMIN-001`, `X-Officer-Role: ADMIN` |
| `RE_PARTNER` | `X-RE-Partner-Id: RE-SBI-01`, `X-RE-Auth-Token: <token>` |

---

## 3. Geographic & Organizational Boundaries

To prevent unauthorized horizontal data access, borrowers and field staff are bound to geographic clusters:

```text
CREDITTECH SYSTEM
│
├── CLUSTER ALPHA (Chandauli District — Canal Irrigated)
│   ├── Branch: Chandauli Rural Branch (BR-001)
│   ├── Loan Officer: Rajesh Kumar (OFF-001)
│   ├── Bank Sakhi: Sunita Devi (SAKHI-001)
│   └── Borrowers:
│       ├── Radhika Devi (BORROWER-A1, Score 745, Approved)
│       └── Sita Kumari (BORROWER-A2, Score 630, Pending Review)
│
└── CLUSTER BETA (Mirzapur District — Rain-Fed)
    ├── Branch: Mirzapur Hill Branch (BR-002)
    ├── Loan Officer: Vikram Singh (OFF-002)
    ├── Bank Sakhi: Anita Bai (SAKHI-002)
    └── Borrowers:
        ├── Ramu Patel (BORROWER-B1, Score 510, Rejected with Override)
        └── Meena Verma (BORROWER-B2, Score 580, Active Dispute)
```

---

## 4. Core Privilege Boundaries

1. **Horizontal Borrower Isolation:**
   - A `BORROWER` can only access their own consent records, score reports, and grievance appeals. Querying any record belonging to another borrower returns `403 Forbidden` or `401 Unauthorized`.
2. **Vertical Officer/Admin Segregation:**
   - A `LOAN_OFFICER` can record credit decisions and file officer notes, but **cannot promote machine learning models** or alter ratified fairness thresholds.
   - An `ADMIN` / `ML_ENGINEER` can promote models and inspect admin metrics, but is audited when making policy modifications.
3. **Field Agent Non-Decision Boundary:**
   - A `BANK_SAKHI` can collect and submit borrower field data, but **cannot record loan underwriting decisions** (`Approve` / `Reject`).
4. **Append-Only Immutability:**
   - No persona (including Admin) can delete or alter existing decision logs, consent hashes, or settled grievance records.
