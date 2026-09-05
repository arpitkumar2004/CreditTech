
# Phase 0 — External Deliverables Status Tracker

Phase 0 has two kinds of deliverables:

1. **In-repo specs** — closed by writing/reviewing markdown in `docs/phase0/`.
2. **External items** — signed contracts, vendor credentials, regulator
   endorsements, physical device procurement. These cannot be closed from
   code and must be tracked separately.

This file is the single source of truth for the external items until they
are all closed and Phase 0 is formally complete.

## In-repo specs (DONE)

| # | Deliverable | File | Status |
|---|---|---|---|
| 1 | ConsentRecord schema spec (Week-2 interim) | `docs/phase0/consent_record_schema_spec.md` | ✅ done |
| 2 | Preliminary feature list (Week-4 interim) | `docs/phase0/preliminary_feature_list.md` | ✅ done |
| 3 | RE API / handoff contract spec (M2) | `docs/phase0/re_api_handoff_spec.md` | ✅ done |
| 4 | SHG/FPO manual entry UI spec (M2) | `docs/phase0/shg_fpo_ui_spec.md` | ✅ repo-side complete (pending E6 field-ops approval) |
| 5 | SHAP reason-code template library (bilingual) | `docs/phase0/shap_reason_code_templates.md` | ✅ draft; final pass triggered by P3 close |
| 6 | AA FIU onboarding playbook | `docs/phase0/aa_fiu_onboarding_checklist.md` | ✅ playbook complete (external onboarding is E2) |
| 7 | Bank Sakhi device + site connectivity template | `docs/phase0/bank_sakhi_device_assessment.md` | ✅ selection criteria + survey template complete (per-site data is E8) |

## External items (OPEN — owner must update)

| # | Item | Owner | Blocking for | Target date | Status | Evidence |
|---|---|---|---|---|---|---|
| E1 | Signed partner RE Letter of Intent | Business/BD | P4 handoff design; P7 launch | M4 | ☐ open | link to signed PDF |
| E2 | AA FIU onboarding completed via licensed NBFC-AA (sandbox creds in hand) | Platform + Legal | P2 AA connector real-cred validation (moved to P6 gate if slipping); P7 | M6 | ☐ open | sandbox `client_id` in Secrets Manager |
| E3 | Geospatial vendor contract signed | BD + ML lead | P2 geospatial connector real-cred validation; P7 | M4 | ☐ open | vendor name + contract ref |
| E4 | NABARD pilot endorsement | Founder/BD | P7 launch | M6 | ☐ open | endorsement letter |
| E5 | Legal counsel sign-off on consent flow + ConsentRecord schema | Legal | **P1 DoD ("post-legal-review")** and P7 | M2 | ☐ open | signed memo attached to `consent_record_schema_spec.md` |
| E6 | Field-ops approval of SHG/FPO UI spec | Field ops lead | P2 UI build | M3 | ☐ open | approval note on `shg_fpo_ui_spec.md` |
| E7 | SHAP reason-code template — final pass in all pilot state languages | Content owner (P0) | P3 close | Triggered by P3 completion | ☐ open | commit updating template file |
| E8 | Bank Sakhi devices procured + tested at site 1 | Field ops | P7 launch at site 1 | M6 | ☐ open | procurement receipts + site-1 test report |

## Update protocol

- Owners update their row (`☐ open` → `✅ done` with evidence link) in a PR.
- The Phase 0 close checklist is: all E1–E8 rows marked ✅ with evidence attached.
- Until E5 (legal sign-off) is closed, the ConsentRecord schema is treated as
  **provisional** — any change requested by legal must be applied to the
  ORM (`services/core/shared/models.py`) and the spec together in a single PR.
