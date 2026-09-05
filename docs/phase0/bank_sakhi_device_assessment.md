# Bank Sakhi Device & Connectivity Assessment

**Phase 0 Deliverable**
**Last Updated:** 2026-09-03
**Status:** Template + selection criteria complete on repo side.
Per-site data collection and physical procurement are external items
(E8 in `phase0_status_tracker.md`) — do **not** treat the empty
per-site rows as failed assessments; they are placeholders that field
ops fill in as each site is surveyed.

---

## 1. Device Requirements (final)

| Spec | Minimum (must-have) | Recommended | Rationale |
|---|---|---|---|
| OS | Android 10 | Android 12+ | SQLCipher + biometric-unlock APIs |
| RAM | 2 GB | 3 GB | UI target device profile in `shg_fpo_ui_spec.md` |
| Storage | 16 GB (≥4 GB free) | 32 GB | Local encrypted queue, doc-photo cache |
| Screen | 5.5" HD | 6" FHD | 16sp accessibility floor |
| Camera | 8 MP | 12 MP | SHG passbook + land-record capture |
| Battery | 3000 mAh | 4000 mAh | Full-day field session without charging |
| SIM | Dual SIM (data + voice) | Dual SIM | Telco failover in low-coverage sites |
| Biometric | Fingerprint | Fingerprint + face | Sakhi login + borrower Aadhaar-biometric |
| Ports | USB-C | USB-C + OTG | Field debug + doc transfer |

## 2. Approved Device Shortlist (India ₹8K–12K, verified stock as of Q3 2026)

| Model | Price band | RAM | Storage | Notes |
|---|---|---|---|---|
| Samsung Galaxy A06 | ₹8.5K | 4 GB | 64 GB | Preferred — 4-year security patches |
| Redmi 13C | ₹8K | 4 GB | 128 GB | Backup option |
| Realme Narzo N53 | ₹9K | 4 GB | 64 GB | Backup option |

Selection is deferred to procurement based on bulk pricing at time of
order.

## 3. Site Connectivity Assessment — Template

Each pilot site must be surveyed before its Sakhi kit is procured.
Fill this table per site as the survey completes; **empty rows below
are intentional placeholders, not verified negative results**.

| Parameter | Site 1 | Site 2 | Site 3 | Site 4 | Site 5 |
|---|---|---|---|---|---|
| Village name | *TBD by field ops* | *TBD* | *TBD* | *TBD* | *TBD* |
| District / State | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* |
| Primary telco | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* |
| Backup telco | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* |
| 4G coverage (Yes / Partial / No) | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* |
| Median download (Mbps) | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* |
| Median upload (Mbps) | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* |
| Grid power reliability (hrs/day) | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* |
| Nearest bank branch (km) | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* |
| Nearest PoS / merchant (km) | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* |
| Sakhi count planned | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* |

### Survey protocol

1. Book a half-day visit with the local NABARD FPO coordinator.
2. Run 3 speed tests spaced ≥1 hour apart on each candidate telco SIM.
3. Log power outages with the panchayat office for the last 30 days.
4. Photograph the proposed Sakhi work location and nearest charging point.
5. Commit the completed row + evidence PDF in a PR that also updates
   `phase0_status_tracker.md`'s E8 row.

## 4. Procurement Checklist

- [ ] Budget approved for 10–15 devices (2–3 per site + 2 spares)
- [ ] Device model locked in based on Q3 pricing
- [ ] SIM cards procured (data plan ≥ 2 GB/day)
- [ ] Protective cases + tempered-glass screen guards
- [ ] Portable chargers / power banks (10 000 mAh) + cables
- [ ] Device-management (MDM) solution selected
- [ ] CreditTech app + offline data pre-loaded on every device
- [ ] Site connectivity survey (§3) complete for every site
- [ ] Sakhi acceptance-test signed at site 1

## 5. Definition of Done for E8

E8 (`phase0_status_tracker.md`) is closed when:

* Every row in §3 has non-TBD values with an attached evidence PDF.
* Every checkbox in §4 is ticked.
* A signed site-1 acceptance-test report is filed alongside the tracker
  update PR.

Until then E8 remains ☐ open and Phase 0 as a whole is
**BLOCKED ON EXTERNAL EVIDENCE**.
