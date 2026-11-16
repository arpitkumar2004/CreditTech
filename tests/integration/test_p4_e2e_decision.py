"""P4.7 — End-to-end: application -> score -> review -> decision -> RE handoff."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.core.shared.models import (
    Borrower,
    FeatureSnapshot,
    OfficerDecisionLog,
    Village,
)

OFFICER_HEADERS = {"X-Officer-Id": "officer_e2e", "X-Officer-Role": "LOAN_OFFICER"}


@pytest.mark.asyncio
async def test_end_to_end_application_score_decision_handoff(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    # 1. Setup: application (borrower + feature snapshot)
    village = Village(
        name="E2E-Village",
        site_type="IRRIGATED_COTTON",
        state="Rajasthan",
        district="Hanumangarh",
    )
    db_session.add(village)
    await db_session.flush()
    borrower = Borrower(
        aadhaar_ref_hash="c" * 64,
        name_encrypted="enc",
        phone_encrypted="enc",
        village_id=village.id,
        gender="F",
        age=34,
        landholding_band="SMALL",
    )
    db_session.add(borrower)
    await db_session.flush()
    snapshot = FeatureSnapshot(
        borrower_id=borrower.id,
        feature_version="v1.0.0",
        features_json={
            "shg_repayment_rate": 0.98,
            "shg_meeting_attendance_pct": 0.95,
            "shg_savings_consistency": 0.1,
            "shg_membership_years": 6.0,
            "shg_grade": "A",
            "utility_payment_ontime_pct": 0.92,
            "estimated_crop_income_kharif": 25000.0,
            "estimated_crop_income_rabi": 22000.0,
            "income_stability_cv": 0.2,
            "monthly_avg_credit_inflow": 8000.0,
            "shg_cumulative_savings": 30000.0,
            "bank_balance_avg_6m": 6000.0,
            "asset_score": 0.7,
            "land_holding_acres": 2.0,
            "irrigation_access": True,
            "land_quality_ndvi_avg": 0.6,
            "ndvi_trend_2season": 0.05,
            "rainfall_deviation_pct": -5.0,
            "crop_insurance_enrolled": True,
        },
        season_tag="RABI",
        sources_used=["AA", "GEOSPATIAL", "SHG_FPO"],
    )
    db_session.add(snapshot)
    await db_session.commit()

    # 2. Score
    score_resp = await client.post(
        "/api/v1/score/",
        json={
            "borrower_id": str(borrower.id),
            "feature_snapshot_id": str(snapshot.id),
        },
    )
    assert score_resp.status_code == 201, score_resp.text
    score_body = score_resp.json()
    score_id = score_body["id"]
    assert score_body["model_version"]
    assert score_body["feature_version"]

    # 3. Review payload for the officer
    review = await client.get(
        f"/api/v1/decision/review/{score_id}", headers=OFFICER_HEADERS
    )
    assert review.status_code == 200
    rbody = review.json()
    assert rbody["model_recommendation"] in ("APPROVE", "REVIEW", "REJECT")
    assert rbody["existing_decision"] is None
    assert rbody["partial_data"] is True  # BUREAU not in sources_used

    # 4. Decide — align with recommendation to avoid needing override reason.
    decision_body: dict = {"score_id": score_id, "decision": "APPROVED"}
    if rbody["model_recommendation"] != "APPROVE":
        decision_body["override_reason"] = (
            "Officer accepts loan on additional field-visit evidence"
        )
    dec = await client.post(
        "/api/v1/decision/", json=decision_body, headers=OFFICER_HEADERS
    )
    assert dec.status_code == 201, dec.text

    # 5. RE handoff
    hand = await client.post(
        "/api/v1/handoff/submit",
        json={
            "score_id": score_id,
            "partner_re_id": "PARTNER_BANK_E2E",
            "requested_amount": 45000.0,
            "requested_tenure_months": 12,
            "purpose": "CROP_INPUT",
        },
    )
    assert hand.status_code == 200
    assert hand.json()["status"] == "SUBMITTED"

    # 6. Audit + review pack now shows the decision
    audit = await client.get(
        f"/api/v1/decision/audit/{score_id}", headers=OFFICER_HEADERS
    )
    assert audit.status_code == 200
    assert len(audit.json()) == 1

    review2 = await client.get(
        f"/api/v1/decision/review/{score_id}", headers=OFFICER_HEADERS
    )
    assert review2.json()["existing_decision"] is not None

    # 7. Immutability: audit row anchors the model + feature version.
    r = await db_session.execute(
        select(OfficerDecisionLog).where(OfficerDecisionLog.score_id == score_id)
    )
    entry = r.scalars().first()
    assert entry is not None
    assert entry.model_version_at_decision == score_body["model_version"]
    assert entry.feature_version_at_decision == score_body["feature_version"]
