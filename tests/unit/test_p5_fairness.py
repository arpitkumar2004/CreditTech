"""P5 — Fairness batch, dimensions, insufficient-sample handling, CSV export."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.core.monitoring.service import MIN_SAMPLE_SIZE, FairnessAuditor
from services.core.shared.models import (
    Borrower,
    FairnessAuditLog,
    LoanApplication,
    OfficerDecisionLog,
    Score,
    Village,
)

OFFICER_HEADERS = {"X-Officer-Id": "off1", "X-Officer-Role": "LOAN_OFFICER"}


async def _seed_case(
    db: AsyncSession,
    *,
    gender: str,
    landholding: str,
    district: str,
    officer_id: str,
    decision: str,
    model_rec: str,
    is_override: bool,
) -> None:
    v = Village(name=f"V-{uuid.uuid4().hex[:6]}", site_type="X", state="RJ", district=district)
    db.add(v)
    await db.flush()
    b = Borrower(
        aadhaar_ref_hash=uuid.uuid4().hex + uuid.uuid4().hex,
        name_encrypted="e", phone_encrypted="e",
        village_id=v.id, gender=gender, age=30, landholding_band=landholding,
    )
    db.add(b)
    await db.flush()
    s = Score(
        borrower_id=b.id, feature_snapshot_id=uuid.uuid4(),
        model_version="v1.0.0-logistic", score=70.0,
        confidence_lower=60.0, confidence_upper=80.0,
    )
    db.add(s)
    await db.flush()
    la = LoanApplication(
        borrower_id=b.id, score_id=s.id, partner_re_id="BANK_01",
        requested_amount=25000.0, requested_tenure_months=12, purpose="AGRI",
        officer_decision=decision,
    )
    db.add(la)
    db.add(OfficerDecisionLog(
        score_id=s.id, loan_application_id=la.id, officer_id=officer_id,
        decision=decision, model_recommendation=model_rec, is_override=is_override,
        override_reason="reason" if is_override else None,
        model_score_at_decision=70.0, model_version_at_decision="v1.0.0-logistic",
        feature_version_at_decision="v1.0.0",
    ))
    await db.commit()


@pytest.mark.asyncio
async def test_fairness_batch_computes_all_four_dimensions(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    for _ in range(2):
        await _seed_case(db_session, gender="F", landholding="MARGINAL",
                         district="Hanumangarh", officer_id="off1",
                         decision="APPROVED", model_rec="APPROVE", is_override=False)
    await _seed_case(db_session, gender="M", landholding="SMALL",
                     district="Sehore", officer_id="off1",
                     decision="REJECTED", model_rec="APPROVE", is_override=True)

    r = await client.post("/api/v1/monitoring/fairness-audit?period=2026-W35")
    assert r.status_code == 200

    rows = (await db_session.execute(select(FairnessAuditLog))).scalars().all()
    dims = {row.dimension for row in rows}
    assert dims == {"GENDER", "LANDHOLDING", "GEOGRAPHY", "OFFICER"}


@pytest.mark.asyncio
async def test_insufficient_sample_marked_and_rate_nulled(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    # Only 2 borrowers total — well below MIN_SAMPLE_SIZE
    await _seed_case(db_session, gender="F", landholding="MARGINAL",
                     district="Hanumangarh", officer_id="off1",
                     decision="APPROVED", model_rec="APPROVE", is_override=False)
    await _seed_case(db_session, gender="M", landholding="SMALL",
                     district="Sehore", officer_id="off2",
                     decision="REJECTED", model_rec="REJECT", is_override=False)

    await FairnessAuditor(db_session).run_audit("2026-W35")
    rows = (await db_session.execute(select(FairnessAuditLog))).scalars().all()
    assert rows, "expected at least one fairness row"
    assert all(r.status == "INSUFFICIENT_SAMPLE" for r in rows)
    assert all(r.approval_rate is None for r in rows)
    assert all(r.override_rate is None for r in rows)
    assert MIN_SAMPLE_SIZE >= 5  # sanity


@pytest.mark.asyncio
async def test_override_rate_uses_officer_decision_log(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    # 3 approvals matching APPROVE, 2 overrides (REJECT vs APPROVE)
    for _ in range(3):
        await _seed_case(db_session, gender="F", landholding="MARGINAL",
                         district="Hanumangarh", officer_id="off1",
                         decision="APPROVED", model_rec="APPROVE", is_override=False)
    for _ in range(2):
        await _seed_case(db_session, gender="F", landholding="MARGINAL",
                         district="Hanumangarh", officer_id="off1",
                         decision="REJECTED", model_rec="APPROVE", is_override=True)

    auditor = FairnessAuditor(db_session, min_sample_size=1)
    await auditor.run_audit("2026-W36")
    rows = (await db_session.execute(
        select(FairnessAuditLog).where(FairnessAuditLog.dimension == "OFFICER")
    )).scalars().all()
    assert len(rows) == 1
    assert rows[0].group_value == "off1"
    assert rows[0].sample_size == 5
    assert abs(rows[0].override_rate - 0.4) < 1e-6


@pytest.mark.asyncio
async def test_fairness_csv_export(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _seed_case(db_session, gender="F", landholding="MARGINAL",
                     district="Hanumangarh", officer_id="off1",
                     decision="APPROVED", model_rec="APPROVE", is_override=False)
    await FairnessAuditor(db_session, min_sample_size=1).run_audit("2026-W37")

    r = await client.get(
        "/api/v1/monitoring/fairness-audit/export.csv?period=2026-W37",
        headers=OFFICER_HEADERS,
    )
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    assert "attachment" in r.headers["content-disposition"]
    body = r.text
    assert body.splitlines()[0].startswith("period,dimension,group_value")
    assert "2026-W37" in body


@pytest.mark.asyncio
async def test_fairness_audit_list_requires_officer_auth(
    client: AsyncClient,
) -> None:
    r = await client.get("/api/v1/monitoring/fairness-audit")
    assert r.status_code == 401
