# SHG/FPO Data Entry UI Specification

**Phase 0 Deliverable — Due: Month 2**
**Status:** DRAFT — Repo-side content complete; awaiting field-ops approval (external item E6 in `phase0_status_tracker.md`)
**Last Updated:** 2026-09-03
**Owners:** Product (repo-side spec) · Field Ops Lead (external approval)

---

## 1. Purpose

Defines the Android data-capture UI used by a **Bank Sakhi** to record
SHG/FPO membership, savings, and farmer information for a rural
borrower whose alternative-data profile cannot be constructed from
Account Aggregator + geospatial + bureau rails alone. Output of this UI
feeds the `SHG_FPO` ingestion rail (see `services/core/ingestion/schemas.py`
`SHGFPOIngestRequest`).

## 2. Design Constraints

| Constraint | Value | Reason |
|---|---|---|
| Device profile | Android ≥8.0, ≤2 GB RAM | Bank Sakhi kit spec (see `bank_sakhi_device_assessment.md`) |
| Connectivity | Fully offline-capable; opportunistic sync | Rural sites see 2G intermittent (see connectivity table) |
| Locales | Hindi (default) + local state language + English fallback | Pilot states: RJ, MP, Odisha |
| Session length | 15–30 min per borrower | Field-tested Bank Sakhi throughput |
| Reconciliation | Dual-entry required on critical numeric fields | ADR-8 (data integrity for manual entry) |
| Auth | Sakhi login + borrower Aadhaar OTP or biometric | Required before any write |

## 3. Screen Flow

```
[1] Borrower selection
        │  (search by phone / Aadhaar last-4 / QR)
        ▼
[2] Consent capture (required before any data write)
        │  → calls /api/v1/consent/ with mode=bank_sakhi_assisted
        ▼
[3] SHG membership info (name, NABARD grade, tenure, role)
        ▼
[4] Savings & internal-loan history (dual-entry)
        ▼
[5] Land & asset inventory (dual-entry on area)
        ▼
[6] Estimated income & crop cycle
        ▼
[7] Supporting doc upload (SHG passbook photo, land record)
        ▼
[8] Dual-entry reconciliation screen
        │  → shows first-pass vs second-pass; blocks submit on >5% delta
        ▼
[9] Review & submit
        │  → POST /api/v1/ingest/shg-fpo (already implemented)
        ▼
[10] Sync-status screen (queued vs synced count)
```

Every screen has a persistent **"Save & continue later"** action that
writes to the encrypted local SQLite queue.

## 4. Critical Fields — Dual-Entry Required

The Sakhi enters, moves on, and re-enters at the reconciliation screen.
Numeric values are compared with a **±5% tolerance**; categorical
values must match exactly.

| Field | Type | Tolerance |
|---|---|---|
| Monthly savings amount (₹) | numeric | ±5% |
| Cumulative savings (₹) | numeric | ±5% |
| Internal loans taken (count) | integer | exact |
| Internal loans repaid (count) | integer | exact |
| Land owned (acres) | numeric | ±5% |
| Estimated monthly income (₹) | numeric | ±5% |

Non-critical fields (SHG name, crop type, ownership category) require
single entry.

## 5. Validation Rules

* All required fields filled.
* Numeric fields within configured min/max per state.
* Dates cannot be in the future.
* `loans_repaid ≤ loans_taken`.
* If `land_owned > 0`, `land_ownership ∈ {OWN, LEASE, SHARECROP}` required.
* NABARD grade ∈ {A, B, C, D} or "NOT_GRADED".
* Aadhaar OTP / biometric verified within the last 30 min.

## 6. Offline Architecture

```
UI (Kotlin) ──▶ Encrypted local SQLite (SQLCipher, AES-256)
                        │
                        ▼
            Background WorkManager job
                        │  (when network available)
                        ▼
   HTTPS POST → /api/v1/ingest/shg-fpo  (mTLS + JWT Sakhi token)
                        │
                        ▼
          Server ack → mark row synced,
                       purge after 30 days
```

Encryption key is derived from the Sakhi's biometric-unlock secret
(Android Keystore). Rows never leave the device in plaintext.

## 7. Accessibility

* Minimum 16sp base font, 20sp for numeric input.
* High-contrast mode toggle in header.
* Voice readback (Android TTS) on every field label and error.
* All primary actions reachable one-handed (bottom-third of screen).
* Numeric keypad only on numeric fields; no free-text keyboard where
  a value picker suffices.

## 8. Error Handling & Reconciliation

| Situation | UX |
|---|---|
| Duplicate borrower entry today | Warn + require override reason |
| Dual-entry mismatch >5% | Block submit, force re-enter, log both attempts |
| OTP / biometric failure ×3 | Lock Sakhi session 10 min |
| Sync failure | Row stays in local queue; retry with exponential backoff |
| Server 4xx | Show human-readable Hindi error; keep row local |
| Server 5xx | Retry indefinitely; visible "n unsynced" badge |

## 9. Analytics & Audit

Every screen emits a client event to the local audit log (screen id,
timestamp, sakhi id, borrower id, retries). This log syncs alongside
the ingest payload. Server-side these events feed the fairness
monitoring pipeline (`services/core/monitoring/`) — specifically the
"officer" dimension of `FairnessAuditLog`.

## 10. Open Items (external, not repo-blocking)

* Field-ops sign-off on flow ordering (E6 in `phase0_status_tracker.md`).
* Final translation review in each pilot-state language.
* Bank Sakhi device model confirmation (blocks accessibility QA).

*This spec is fully complete on the repo side. Field-ops sign-off (E6)
is required before Phase 2 UI implementation.*
