# AA FIU Onboarding Checklist

**Phase 0 — Ongoing (3–6 months)**
**Last Updated:** 2026-09-03
**Status:** Repo-side playbook complete (integration flow, checklist,
mock connector). Actual NBFC-AA onboarding is external item **E2** in
`phase0_status_tracker.md` and must be tracked there.

---

## 1. Regulatory model

CreditTech operates as an **FIU (Financial Information User)** in the
Account Aggregator ecosystem, integrating **through a licensed NBFC-AA
partner** (Finvu, OneMoney, CAMS-AA, NADL, or Perfios-AA). CreditTech
does **not** hold an NBFC-AA license itself and must not attempt to
call FIP endpoints directly.

## 2. Prerequisites (external — owner: Platform + Legal)

- [ ] Shortlist NBFC-AA partners against pricing + SLA
- [ ] Execute partnership agreement with selected NBFC-AA
- [ ] Legal review of NBFC-AA agreement (DPDP + AA Master Directions)

## 3. Technical Onboarding

- [ ] Obtain AA sandbox credentials from NBFC-AA partner
- [ ] Register FIU entity with the AA ecosystem (via NBFC-AA)
- [ ] Configure FI types: `DEPOSIT`, `TERM_DEPOSIT`, `RECURRING_DEPOSIT`,
      `MUTUAL_FUNDS` (if applicable)
- [ ] Implement consent flow (create → approve → fetch → revoke) —
      **implemented in repo**: see `services/core/consent/service.py`
      and `services/core/ingestion/connectors.py::AccountAggregatorConnector`.
- [ ] Test consent artifact creation in sandbox
- [ ] Test FI data fetch in sandbox against mock borrower accounts
- [ ] Validate data decryption (AA uses session-key-based encryption)
- [ ] Map AA FI schema to CreditTech feature schema — mock payload
      shape frozen in `services/core/ingestion/mocks/server.py`

## 4. Compliance

- [ ] DPDP consent language reviewed by legal (**blocks P1 DoD via E5**)
- [ ] Purpose limitation documented for each FI type — see
      `docs/phase0/consent_record_schema_spec.md` §Purpose enum
- [ ] Data retention policy aligned with DPDP (≥7 years for consent
      audit; raw AA payload retention TBD by legal)
- [ ] Breach notification procedure documented
- [ ] Consent revocation flow tested end-to-end — covered by
      `tests/test_consent.py::test_revoke_consent`

## 5. Production Readiness (Phase 6–7)

- [ ] Production credentials obtained and stored in AWS Secrets Manager
      (staging + prod separately)
- [ ] mTLS certificates configured on ECS task
- [ ] Rate limits confirmed with NBFC-AA
- [ ] Production smoke test passed
- [ ] Monitoring/alerting configured for AA API failure rate,
      p99 latency, and consent-fetch error codes

## 6. Repo-side integration surface

| Concern | Location |
|---|---|
| Consent creation / hash-chain | `services/core/consent/service.py` |
| AA connector (real + mock URL routing) | `services/core/ingestion/connectors.py` |
| Mock AA endpoint (used by tests + `docker compose`) | `services/core/ingestion/mocks/server.py::mock_aa_fetch` |
| Config knobs (AA base URL, client id/secret) | `services/core/config.py` |
| End-to-end pipeline test with active consent | `tests/test_ingestion.py::test_trigger_ingestion_success` |

## 7. Key Contacts (fill on partner selection — external)

| Role | Organization | Contact |
|---|---|---|
| AA Partner Technical Lead | *TBD by BD* | *TBD* |
| CreditTech AA Integration Lead | CreditTech | *TBD by platform* |
| Legal / Compliance | CreditTech | *TBD by legal* |

*The empty contact cells above are not verified negative results — they
are external items that BD/Platform/Legal fill in through
`phase0_status_tracker.md` E2 as onboarding progresses.*

## 8. Definition of Done for E2

E2 (`phase0_status_tracker.md`) closes when:

* NBFC-AA partnership agreement signed and stored.
* Sandbox `client_id` is present in AWS Secrets Manager under
  `credittech/staging/aa/client_id`.
* Contacts table (§7) has non-TBD entries.
* At least one live sandbox fetch has been recorded end-to-end in the
  staging environment (evidence: DataPull row with source=AA and
  status=SUCCESS).
