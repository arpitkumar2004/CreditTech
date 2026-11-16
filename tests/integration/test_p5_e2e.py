"""P5 — End-to-end: application -> score -> decision -> monitoring -> grievance."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.core.monitoring.service import FairnessAuditor
from services.core.shared.models import (
    Borrower,
    FairnessAuditLog,
    FeatureSnapshot,
    Grievance,
    LoanApplication,
    OfficerDecisionLog,
    Score,
    Village,
)

OFFICER_HEADERS = {"X-Officer-Id": "off1", "X-Officer-Role": "LOAN_OFFICER"}


@pytest.mark.asyncio
async def test_p5_full_pilot_flow(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    # 1. Seed a borrower + score + officer decision (application -> score -> decision)
    v = Village(name="V-e2e", site_type="X", state="RJ", district="Hanumangarh")
    db_session.add(v)
    await db_session.flush()
    b = Borrower(
        aadhaar_ref_hash="e" * 64,
        name_encrypted="e", phone_encrypted="e",
        village_id=v.id, gender="F", age=29, landholding_band="MARGINAL",
    )
    db_session.add(b)
    await db_session.flush()
    snap = FeatureSnapshot(
        borrower_id=b.id, feature_version="v1.0.0",
        features_json={"shg_repayment_rate": 0.9},
        season_tag="RABI", sources_used=["SHG_FPO"],
    )
    db_session.add(snap)
    await db_session.flush()
    s = Score(
        borrower_id=b.id, feature_snapshot_id=snap.id,
        model_version="v1.0.0-logistic", score=45.0,
        confidence_lower=35.0, confidence_upper=55.0, sources_used=["SHG_FPO"],
    )
    db_session.add(s)
    await db_session.flush()
    la = LoanApplication(
        borrower_id=b.id, score_id=s.id, partner_re_id="BANK_01",
        requested_amount=20000.0, requested_tenure_months=9, purpose="AGRI",
        officer_decision="REJECTED",
    )
    db_session.add(la)
    db_session.add(OfficerDecisionLog(
        score_id=s.id, loan_application_id=la.id, officer_id="off1",
        decision="REJECTED", model_recommendation="REJECT",
        is_override=False, override_reason=None,
        model_score_at_decision=45.0, model_version_at_decision="v1.0.0-logistic",
        feature_version_at_decision="v1.0.0",
    ))
    await db_session.commit()

    # 2. Monitoring — fairness batch runs (min_sample_size=1 so we get real rows)
    await FairnessAuditor(db_session, min_sample_size=1).run_audit("2026-W41")
    rows = (await db_session.execute(select(FairnessAuditLog))).scalars().all()
    assert len(rows) >= 4  # gender+landholding+geography+officer

    # 3. Dashboard reflects state
    r_dash = await client.get("/api/v1/dashboard/portfolio", headers=OFFICER_HEADERS)
    assert r_dash.status_code == 200
    m = r_dash.json()
    assert m["applications_total"] == 1
    assert m["applications_rejected"] == 1
    assert m["approval_rate"] == 0.0

    # 4. Borrower files an appeal
    r_g = await client.post(
        "/api/v1/grievances/",
        headers={"X-Borrower-Id": str(b.id)},
        json={
            "borrower_id": str(b.id),
            "score_id": str(s.id),
            "loan_application_id": str(la.id),
            "category": "DECISION_APPEAL",
            "description": "Please re-examine — my SHG history is strong.",
        },
    )
    assert r_g.status_code == 201
    gid = r_g.json()["id"]

    # 5. Officer moves to IN_REVIEW then RESOLVED
    r_u1 = await client.patch(
        f"/api/v1/grievances/{gid}", headers=OFFICER_HEADERS,
        json={"status": "IN_REVIEW"},
    )
    assert r_u1.status_code == 200
    r_u2 = await client.patch(
        f"/api/v1/grievances/{gid}", headers=OFFICER_HEADERS,
        json={"status": "RESOLVED", "resolution_notes": "Re-review complete"},
    )
    assert r_u2.status_code == 200

    # 6. Dashboard portfolio now shows 0 open grievances
    m2 = (await client.get("/api/v1/dashboard/portfolio", headers=OFFICER_HEADERS)).json()
    assert m2["grievances_open"] == 0

    # 7. Score report renders
    r_rep = await client.get(
        f"/api/v1/report/score/{s.id}", headers=OFFICER_HEADERS
    )
    assert r_rep.status_code == 200
    assert "REJECTED" in r_rep.text

    # 8. Grievance persists with resolved_at set
    g = (await db_session.execute(
        select(Grievance).where(Grievance.id == uuid.UUID(gid))
    )).scalar_one()
    assert g.status == "RESOLVED"
    assert g.resolved_at is not None
