"""P5 — Institutional dashboard, fairness views, and score report."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from services.core.monitoring.service import FairnessAuditor
from services.core.shared.models import (
    Borrower,
    FeatureSnapshot,
    LoanApplication,
    OfficerDecisionLog,
    ReasonCode,
    Score,
    Village,
)

OFFICER_HEADERS = {"X-Officer-Id": "off1", "X-Officer-Role": "LOAN_OFFICER"}


@pytest.fixture
async def scored_borrower(db_session: AsyncSession) -> Score:
    v = Village(name="Pilot Village", site_type="IRRIGATED",
                state="Rajasthan", district="Hanumangarh")
    db_session.add(v)
    await db_session.flush()
    b = Borrower(
        aadhaar_ref_hash="d" * 64,
        name_encrypted="e", phone_encrypted="e",
        village_id=v.id, gender="F", age=32, landholding_band="MARGINAL",
    )
    db_session.add(b)
    await db_session.flush()
    snap = FeatureSnapshot(
        borrower_id=b.id, feature_version="v1.0.0",
        features_json={"shg_repayment_rate": 0.95},
        season_tag="RABI", sources_used=["AA", "SHG_FPO"],
    )
    db_session.add(snap)
    await db_session.flush()
    s = Score(
        borrower_id=b.id, feature_snapshot_id=snap.id,
        model_version="v1.0.0-logistic", score=71.0,
        confidence_lower=64.0, confidence_upper=78.0,
        sources_used=["AA", "SHG_FPO"],
    )
    db_session.add(s)
    await db_session.flush()
    db_session.add(ReasonCode(
        score_id=s.id, rank=1, feature_name="shg_repayment_rate",
        direction="POSITIVE", shap_value=0.2,
        localized_text_en="Strong SHG repayment history",
        localized_text_hi="SHG चुकौती इतिहास मजबूत",
    ))
    la = LoanApplication(
        borrower_id=b.id, score_id=s.id, partner_re_id="BANK_01",
        requested_amount=25000.0, requested_tenure_months=12, purpose="AGRI",
        officer_decision="APPROVED",
    )
    db_session.add(la)
    db_session.add(OfficerDecisionLog(
        score_id=s.id, loan_application_id=la.id, officer_id="off1",
        decision="APPROVED", model_recommendation="APPROVE",
        is_override=False, override_reason=None,
        model_score_at_decision=71.0, model_version_at_decision="v1.0.0-logistic",
        feature_version_at_decision="v1.0.0",
    ))
    await db_session.commit()
    return s


@pytest.mark.asyncio
async def test_portfolio_metrics(client: AsyncClient, scored_borrower: Score) -> None:
    r = await client.get("/api/v1/dashboard/portfolio", headers=OFFICER_HEADERS)
    assert r.status_code == 200
    m = r.json()
    assert m["borrowers"] == 1
    assert m["scores_generated"] == 1
    assert m["applications_total"] == 1
    assert m["applications_approved"] == 1
    assert m["approval_rate"] == 1.0
    assert m["disbursed_amount_approved"] == 25000.0
    assert m["officer_decisions_total"] == 1
    assert m["officer_override_rate"] == 0.0


@pytest.mark.asyncio
async def test_portfolio_requires_officer_auth(client: AsyncClient) -> None:
    r = await client.get("/api/v1/dashboard/portfolio")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_dashboard_fairness_view(
    client: AsyncClient, scored_borrower: Score, db_session: AsyncSession
) -> None:
    await FairnessAuditor(db_session, min_sample_size=1).run_audit("2026-W40")
    r = await client.get("/api/v1/dashboard/fairness", headers=OFFICER_HEADERS)
    assert r.status_code == 200
    body = r.json()
    assert body["period"] == "2026-W40"
    dims = {row["dimension"] for row in body["rows"]}
    assert "GENDER" in dims and "OFFICER" in dims
    assert "governance_note" in body


@pytest.mark.asyncio
async def test_score_report_renders(
    client: AsyncClient, scored_borrower: Score
) -> None:
    r = await client.get(
        f"/api/v1/report/score/{scored_borrower.id}?partner_re_id=BANK_01",
        headers=OFFICER_HEADERS,
    )
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    html = r.text
    assert "CreditTech" in html
    assert "Score" in html
    assert "GOOD" in html
    assert "v1.0.0-logistic" in html
    assert "Strong SHG repayment history" in html
    assert "APPROVED" in html
    assert "BANK_01" in html


@pytest.mark.asyncio
async def test_score_report_404_for_unknown(client: AsyncClient) -> None:
    fake = uuid.uuid4()
    r = await client.get(f"/api/v1/report/score/{fake}", headers=OFFICER_HEADERS)
    assert r.status_code == 404
