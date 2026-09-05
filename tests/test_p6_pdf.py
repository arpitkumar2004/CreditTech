"""P6 — PDF renderer + endpoint."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from services.core.dashboard.pdf import html_to_pdf
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


def test_html_to_pdf_returns_valid_pdf_header() -> None:
    pdf, backend = html_to_pdf(
        "<html><body><h1>CreditTech</h1><p>Score: 71</p></body></html>"
    )
    assert isinstance(pdf, bytes)
    assert pdf.startswith(b"%PDF-")
    assert b"%%EOF" in pdf[-32:]
    assert backend in {"weasyprint", "reportlab", "builtin-minimal"}


@pytest.fixture
async def scored(db_session: AsyncSession) -> Score:
    v = Village(name="V", site_type="X", state="RJ", district="D")
    db_session.add(v); await db_session.flush()
    b = Borrower(
        aadhaar_ref_hash="z" * 64, name_encrypted="e", phone_encrypted="e",
        village_id=v.id, gender="F", age=30, landholding_band="MARGINAL",
    )
    db_session.add(b); await db_session.flush()
    snap = FeatureSnapshot(
        borrower_id=b.id, feature_version="v1.0.0",
        features_json={"shg_repayment_rate": 0.95},
        season_tag="RABI", sources_used=["SHG_FPO"],
    )
    db_session.add(snap); await db_session.flush()
    s = Score(
        borrower_id=b.id, feature_snapshot_id=snap.id,
        model_version="v1.0.0-logistic", score=71.0,
        confidence_lower=64.0, confidence_upper=78.0,
        sources_used=["SHG_FPO"],
    )
    db_session.add(s); await db_session.flush()
    db_session.add(ReasonCode(
        score_id=s.id, rank=1, feature_name="shg_repayment_rate",
        direction="POSITIVE", shap_value=0.2,
        localized_text_en="Strong SHG history", localized_text_hi="मजबूत",
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
async def test_pdf_endpoint_returns_pdf(client: AsyncClient, scored: Score) -> None:
    r = await client.get(
        f"/api/v1/report/score/{scored.id}/pdf?partner_re_id=BANK_01",
        headers=OFFICER_HEADERS,
    )
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content.startswith(b"%PDF-")
    assert "X-PDF-Backend" in r.headers
