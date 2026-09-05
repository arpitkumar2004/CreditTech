# ConsentRecord Schema Specification

**Phase 0 Interim Deliverable — Due: Week 2**  
**Status:** DRAFT — Requires legal counsel sign-off before P1 schema lock  
**Last Updated:** 2026-08-31

---

## 1. Purpose

This document specifies the schema for CreditTech's consent ledger — an append-only, hash-chained table in PostgreSQL that records every consent artifact created, modified, or revoked during the borrower onboarding and data-access lifecycle.

### Regulatory Basis

- **DPDP Act 2023 & Rules 2025:** Consent must be free, specific, informed, unconditional, unambiguous; revocable at any time; retained for ≥7 years post-relationship.
- **AA Master Directions (RBI):** FIU must present a valid, unexpired consent artifact for every data pull; consent scope must specify FI types, date range, and frequency.
- **RBI Fair Practices Code:** Borrower must be informed of purpose before data collection.

---

## 2. Schema Definition

### 2.1 ConsentRecord Table

```sql
CREATE TABLE consent_records (
    -- Primary key
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Borrower reference
    borrower_id     UUID        NOT NULL REFERENCES borrowers(id) ON DELETE RESTRICT,

    -- Consent details
    purpose         VARCHAR(50) NOT NULL CHECK (purpose IN (
                        'credit_scoring',
                        'identity_verification',
                        'data_aggregation',
                        'score_sharing_with_re',
                        'retraining_consent'
                    )),
    consent_mode    VARCHAR(20) NOT NULL CHECK (consent_mode IN (
                        'app_self_service',
                        'bank_sakhi_assisted',
                        'ivr_voice'
                    )),

    -- AA-specific fields (nullable for non-AA consent types)
    aa_consent_id   VARCHAR(128),        -- AA ecosystem consent artifact ID
    aa_handle       VARCHAR(128),        -- Borrower's AA handle (VUA)
    fi_types        JSONB       NOT NULL DEFAULT '[]',  -- ["DEPOSIT", "TERM_DEPOSIT", ...]
    fi_date_range_from  DATE,
    fi_date_range_to    DATE,
    fetch_frequency VARCHAR(20) CHECK (fetch_frequency IN (
                        'ONETIME', 'HOURLY', 'DAILY', 'MONTHLY', 'YEARLY'
                    )),

    -- Data sources consented for
    data_sources    JSONB       NOT NULL DEFAULT '["AA"]',
    -- e.g. ["AA", "GEOSPATIAL", "SHG_FPO", "BUREAU"]

    -- Consent scope description (human-readable, localized)
    scope_description_en  TEXT  NOT NULL,
    scope_description_hi  TEXT,          -- Hindi translation
    scope_description_local TEXT,        -- Pilot state local language

    -- Lifecycle timestamps
    issued_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at      TIMESTAMPTZ NOT NULL,
    revoked_at      TIMESTAMPTZ,
    revocation_reason VARCHAR(255),

    -- Consent status (derived, but stored for query efficiency)
    status          VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN (
                        'ACTIVE', 'EXPIRED', 'REVOKED', 'SUPERSEDED'
                    )),

    -- Hash chain for tamper evidence (ADR-6)
    hash_prev       VARCHAR(64) NOT NULL,  -- SHA-256 of the previous record's hash
    hash_current    VARCHAR(64) NOT NULL,  -- SHA-256 of this record's content

    -- Audit metadata
    created_by      VARCHAR(50) NOT NULL,  -- system | borrower_id | sakhi_id
    ip_address      INET,
    device_id       VARCHAR(128),
    consent_artifact_ref  VARCHAR(256),    -- S3/GCS path to signed consent PDF

    -- Timestamps
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for common query patterns
CREATE INDEX idx_consent_borrower_status ON consent_records(borrower_id, status);
CREATE INDEX idx_consent_aa_consent_id ON consent_records(aa_consent_id) WHERE aa_consent_id IS NOT NULL;
CREATE INDEX idx_consent_expires_at ON consent_records(expires_at) WHERE status = 'ACTIVE';
CREATE INDEX idx_consent_hash_chain ON consent_records(hash_current);
```

### 2.2 ConsentAuditLog Table (append-only mutation log)

```sql
CREATE TABLE consent_audit_log (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    consent_id      UUID        NOT NULL REFERENCES consent_records(id),
    action          VARCHAR(20) NOT NULL CHECK (action IN (
                        'CREATED', 'VERIFIED', 'REVOKED',
                        'EXPIRED_AUTO', 'SUPERSEDED', 'ACCESSED'
                    )),
    actor           VARCHAR(50) NOT NULL,  -- system | borrower_id | sakhi_id | officer_id
    details         JSONB,
    performed_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_consent_id ON consent_audit_log(consent_id);
CREATE INDEX idx_audit_performed_at ON consent_audit_log(performed_at);
```

---

## 3. Hash-Chain Algorithm

Each `ConsentRecord` contains a cryptographic hash chain per ADR-6:

```python
import hashlib
import json

def compute_consent_hash(record: dict, prev_hash: str) -> str:
    """
    Compute SHA-256 hash for tamper-evident consent chain.
    Fields included: borrower_id, purpose, data_sources, issued_at, expires_at, status
    """
    payload = json.dumps({
        "borrower_id": str(record["borrower_id"]),
        "purpose": record["purpose"],
        "data_sources": sorted(record["data_sources"]),
        "issued_at": record["issued_at"].isoformat(),
        "expires_at": record["expires_at"].isoformat(),
        "status": record["status"],
        "prev_hash": prev_hash,
    }, sort_keys=True)

    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
```

**Genesis hash:** The first record for each borrower uses `hash_prev = SHA256("GENESIS:<borrower_id>")`.

---

## 4. Business Rules

| Rule | Description |
|------|-------------|
| **R1** | A consent record is **never deleted or mutated** — only new records are appended |
| **R2** | Revoking a consent creates a new audit log entry and sets `revoked_at` + `status = REVOKED` on the existing record |
| **R3** | A data pull **cannot proceed** if no ACTIVE consent exists for the requested `purpose` + `data_sources` combination |
| **R4** | Consent expiry is checked at pull-time, not on a schedule (lazy expiration) |
| **R5** | When a borrower re-consents, the old record is marked `SUPERSEDED` and a new record is created with `hash_prev` pointing to the old record's `hash_current` |
| **R6** | `expires_at` must be ≤ 12 months from `issued_at` (AA regulatory limit) |
| **R7** | All consent records must be retained for **≥ 7 years** after relationship end (DPDP) |

---

## 5. API Contract (Preview)

```
POST   /api/v1/consent/              → Create consent record
GET    /api/v1/consent/{id}          → Retrieve consent record
GET    /api/v1/consent/borrower/{id} → List all consent records for borrower
POST   /api/v1/consent/{id}/revoke   → Revoke consent
GET    /api/v1/consent/{id}/verify   → Verify consent is active + hash-chain valid
GET    /api/v1/consent/{id}/audit    → Get audit trail for consent
```

---

## 6. Open Questions for Legal Review

1. Is the `consent_mode = 'bank_sakhi_assisted'` flow compliant with DPDP's "free and informed" requirement if the Sakhi reads the scope aloud?
2. Does `ivr_voice` consent require a recording of the voice confirmation to be stored as the artifact?
3. Are the 5 `purpose` categories sufficient, or does DPDP require more granular purpose specification?
4. Should `revocation_reason` be mandatory or optional?

---

*This spec must be reviewed by legal counsel before the ConsentRecord schema is locked in Phase 1.*
