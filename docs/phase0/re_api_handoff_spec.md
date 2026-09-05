# RE API / Handoff Contract Specification

**Phase 0 Deliverable — Due: Month 2**  
**Status:** DRAFT — Must be agreed with partner RE before Phase 4 begins  
**Last Updated:** 2026-08-31

---

## 1. Overview

This document specifies the API contract between CreditTech (LSP/TSP) and the Partner Regulated Entity (RE — bank/NBFC) for the loan application handoff. CreditTech generates a credit score + evidence package; the RE receives it and makes the final lending decision.

### Integration Model

```
CreditTech (LSP)                          Partner RE
┌─────────────────┐                  ┌─────────────────┐
│  Scoring Engine  │ ── HTTPS/mTLS ──│  Loan Processing │
│  + Evidence Pack │ ── POST ──────→ │  System (LPS)    │
│                  │ ←── Response ── │                  │
│  Decision Capture│ ── Callback ──→ │  Decision Webhook│
└─────────────────┘                  └─────────────────┘
```

---

## 2. Authentication & Security

| Parameter | Specification |
|-----------|--------------|
| Transport | HTTPS (TLS 1.3 minimum) |
| Mutual Auth | mTLS with X.509 client certificates |
| API Auth | OAuth 2.0 client_credentials grant |
| Token Endpoint | `POST /oauth/token` (RE-provided) |
| Token Lifetime | 3600 seconds (RE-configurable) |
| IP Allowlisting | CreditTech production IPs whitelisted at RE firewall |
| Data Encryption | Payload-level encryption for PII fields (AES-256-GCM) |
| Rate Limit | 100 requests/hour (pilot), 1000 req/hr (production) |

---

## 3. API Endpoints

### 3.1 Submit Loan Application

**`POST /api/v1/loan-applications`**

Submit a scored loan application with evidence package to the RE.

**Request Headers:**
```http
Content-Type: application/json
Authorization: Bearer <access_token>
X-Request-ID: <uuid>
X-CreditTech-Timestamp: <ISO 8601>
X-CreditTech-Signature: <HMAC-SHA256 of body>
```

**Request Body:**
```json
{
  "application_id": "CT-2026-00001",
  "submitted_at": "2026-09-15T10:30:00+05:30",

  "borrower": {
    "credittech_borrower_ref": "uuid",
    "aadhaar_reference_hash": "sha256_hash",
    "name_encrypted": "AES-256-GCM encrypted",
    "phone_encrypted": "AES-256-GCM encrypted",
    "village": "Pilot Village 1",
    "district": "District Name",
    "state": "State Name",
    "gender": "F",
    "age": 35,
    "landholding_band": "MARGINAL"
  },

  "credit_assessment": {
    "score": 72,
    "score_band": "GOOD",
    "confidence_band": {
      "lower": 65,
      "upper": 79
    },
    "model_version": "v1.0.0-logistic",
    "sources_used": ["AA", "GEOSPATIAL", "SHG_FPO"],
    "sources_unavailable": ["BUREAU"],
    "assessment_timestamp": "2026-09-15T10:28:45+05:30"
  },

  "reason_codes": [
    {
      "rank": 1,
      "feature": "shg_repayment_rate",
      "direction": "POSITIVE",
      "description_en": "Excellent SHG loan repayment history (98%)",
      "description_hi": "उत्कृष्ट SHG ऋण चुकौती इतिहास (98%)",
      "shap_value": 0.15
    },
    {
      "rank": 2,
      "feature": "shg_savings_consistency",
      "direction": "POSITIVE",
      "description_en": "Consistent monthly SHG savings deposits",
      "description_hi": "नियमित मासिक SHG बचत जमा",
      "shap_value": 0.12
    },
    {
      "rank": 3,
      "feature": "ndvi_trend_2season",
      "direction": "NEGATIVE",
      "description_en": "Declining crop health trend over last 2 seasons",
      "description_hi": "पिछले 2 मौसमों में फसल स्वास्थ्य में गिरावट",
      "shap_value": -0.08
    }
  ],

  "loan_request": {
    "requested_amount": 50000,
    "currency": "INR",
    "purpose": "CROP_INPUT",
    "requested_tenure_months": 12,
    "crop_cycle": "RABI_2026"
  },

  "consent_reference": {
    "consent_id": "uuid",
    "consent_issued_at": "2026-09-01T09:00:00+05:30",
    "consent_expires_at": "2027-03-01T09:00:00+05:30",
    "consent_artifact_url": "https://storage.credittech.in/consents/uuid.pdf"
  },

  "supporting_evidence": {
    "shg_membership_certificate_url": "https://...",
    "land_record_url": "https://...",
    "crop_insurance_url": "https://..."
  }
}
```

**Response — Success (202 Accepted):**
```json
{
  "re_application_id": "RE-2026-LN-12345",
  "credittech_application_id": "CT-2026-00001",
  "status": "RECEIVED",
  "estimated_decision_sla_hours": 24,
  "received_at": "2026-09-15T10:30:05+05:30"
}
```

**Response — Validation Error (422):**
```json
{
  "error": "VALIDATION_ERROR",
  "details": [
    {"field": "borrower.aadhaar_reference_hash", "message": "Invalid hash format"}
  ]
}
```

### 3.2 Decision Webhook (RE → CreditTech)

**`POST /api/v1/webhooks/re-decision`** (CreditTech endpoint)

The RE calls this endpoint when a loan decision is made.

```json
{
  "re_application_id": "RE-2026-LN-12345",
  "credittech_application_id": "CT-2026-00001",
  "decision": "APPROVED",
  "decided_at": "2026-09-16T14:00:00+05:30",
  "decided_by": "LOAN_OFFICER_ID_123",
  "approved_amount": 40000,
  "approved_tenure_months": 12,
  "interest_rate_pct": 7.0,
  "override_reason": null,
  "conditions": [
    "Crop insurance enrollment required before disbursal"
  ]
}
```

**Decision values:** `APPROVED` | `REJECTED` | `MORE_INFO_REQUIRED` | `REFERRED`

### 3.3 Application Status Query

**`GET /api/v1/loan-applications/{re_application_id}/status`**

```json
{
  "re_application_id": "RE-2026-LN-12345",
  "status": "UNDER_REVIEW",
  "last_updated": "2026-09-16T09:00:00+05:30"
}
```

---

## 4. Score Band Mapping

| Score Range | Band | Interpretation |
|------------|------|----------------|
| 0–30 | VERY_HIGH_RISK | Likely decline; manual review recommended |
| 31–50 | HIGH_RISK | Additional data or collateral may be needed |
| 51–65 | MODERATE | Standard underwriting; loan officer discretion |
| 66–80 | GOOD | Favorable; streamlined approval path |
| 81–100 | EXCELLENT | Strong candidate; fast-track eligible |

---

## 5. Error Codes

| Code | HTTP Status | Description |
|------|------------|-------------|
| `AUTH_FAILED` | 401 | Invalid or expired token |
| `CERT_INVALID` | 403 | mTLS certificate validation failed |
| `VALIDATION_ERROR` | 422 | Request body validation failed |
| `DUPLICATE_APPLICATION` | 409 | Application ID already submitted |
| `RATE_LIMIT_EXCEEDED` | 429 | Exceeded request rate limit |
| `RE_UNAVAILABLE` | 503 | RE system temporarily unavailable |

---

## 6. SLA Agreement

| Metric | Target |
|--------|--------|
| Application submission → RE acknowledgement | < 5 seconds |
| RE decision SLA | < 24 hours (business hours) |
| Webhook delivery (RE → CreditTech) | < 30 seconds after decision |
| Webhook retry policy | 3 retries with exponential backoff (1min, 5min, 30min) |

---

## 7. Fallback: Structured Export (if API not available at pilot)

If the partner RE cannot expose an API at pilot launch, CreditTech will generate a **structured CSV/JSON export** file:

```
CT-Export-2026-09-15.json
├── application_id
├── borrower_summary (name, village, demographic)
├── credit_score + confidence_band
├── reason_codes (top 5)
├── loan_request details
└── consent_reference
```

Delivered via: Encrypted email / SFTP to designated RE contact.

---

*This contract must be agreed by the partner RE's technology team before Phase 4 implementation begins.*
