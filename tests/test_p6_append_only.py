"""P6 — DB-level append-only enforcement on audit tables."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import delete, text, update
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from services.core.shared.models import (
    Borrower,
    FeatureSnapshot,
    Grievance,
    GrievanceAuditLog,
    LoanApplication,
    OfficerDecisionLog,
    Score,
    Village,
)


async def _seed_decision(db: AsyncSession) -> OfficerDecisionLog:
    v = Village(name="V", site_type="X", state="RJ", district="D")
    db.add(v)
    await db.flush()
    b = Borrower(
        aadhaar_ref_hash="p" * 64, name_encrypted="e", phone_encrypted="e",
        village_id=v.id, gender="F", age=30, landholding_band="MARGINAL",
    )
    db.add(b)
    await db.flush()
    snap = FeatureSnapshot(
        borrower_id=b.id, feature_version="v1.0.0",
        features_json={"x": 1.0}, season_tag="RABI", sources_used=["SHG_FPO"],
    )
    db.add(snap)
    await db.flush()
    s = Score(
        borrower_id=b.id, feature_snapshot_id=snap.id,
        model_version="v1.0.0-logistic", score=60.0,
        confidence_lower=55.0, confidence_upper=65.0, sources_used=["SHG_FPO"],
    )
    db.add(s)
    await db.flush()
    la = LoanApplication(
        borrower_id=b.id, score_id=s.id, partner_re_id="BANK_01",
        requested_amount=20000.0, requested_tenure_months=12, purpose="AGRI",
        officer_decision="APPROVED",
    )
    db.add(la)
    odl = OfficerDecisionLog(
        score_id=s.id, loan_application_id=la.id, officer_id="off1",
        decision="APPROVED", model_recommendation="APPROVE",
        is_override=False, override_reason=None,
        model_score_at_decision=60.0, model_version_at_decision="v1.0.0-logistic",
        feature_version_at_decision="v1.0.0",
    )
    db.add(odl)
    await db.commit()
    return odl


@pytest.mark.asyncio
async def test_officer_decision_log_update_blocked(db_session: AsyncSession) -> None:
    odl = await _seed_decision(db_session)
    with pytest.raises((IntegrityError, OperationalError, Exception)) as ei:
        await db_session.execute(
            update(OfficerDecisionLog)
            .where(OfficerDecisionLog.id == odl.id)
            .values(decision="REJECTED")
        )
        await db_session.commit()
    assert "append-only" in str(ei.value).lower() or "abort" in str(ei.value).lower()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_officer_decision_log_delete_blocked(db_session: AsyncSession) -> None:
    odl = await _seed_decision(db_session)
    with pytest.raises((IntegrityError, OperationalError, Exception)) as ei:
        await db_session.execute(
            delete(OfficerDecisionLog).where(OfficerDecisionLog.id == odl.id)
        )
        await db_session.commit()
    assert "append-only" in str(ei.value).lower() or "abort" in str(ei.value).lower()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_grievance_audit_log_update_blocked(db_session: AsyncSession) -> None:
    v = Village(name="V2", site_type="X", state="RJ", district="D2")
    db_session.add(v)
    await db_session.flush()
    b = Borrower(
        aadhaar_ref_hash="q" * 64, name_encrypted="e", phone_encrypted="e",
        village_id=v.id, gender="F", age=30, landholding_band="MARGINAL",
    )
    db_session.add(b)
    await db_session.flush()
    g = Grievance(
        borrower_id=b.id, category="SCORE_DISPUTE", description="test",
        status="OPEN", sla_hours=72,
        due_at=__import__("datetime").datetime.now(__import__("datetime").UTC),
    )
    db_session.add(g)
    await db_session.flush()
    entry = GrievanceAuditLog(
        grievance_id=g.id, from_status=None, to_status="OPEN",
        actor="test", note="opened",
    )
    db_session.add(entry)
    await db_session.commit()

    with pytest.raises((IntegrityError, OperationalError, Exception)) as ei:
        await db_session.execute(
            update(GrievanceAuditLog)
            .where(GrievanceAuditLog.id == entry.id)
            .values(note="tampered")
        )
        await db_session.commit()
    assert "append-only" in str(ei.value).lower() or "abort" in str(ei.value).lower()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_triggers_are_installed(db_session: AsyncSession) -> None:
    r = await db_session.execute(
        text("SELECT name FROM sqlite_master WHERE type='trigger'")
    )
    names = {row[0] for row in r.fetchall()}
    assert "officer_decision_log_no_update" in names
    assert "officer_decision_log_no_delete" in names
    assert "grievance_audit_log_no_update" in names
    assert "grievance_audit_log_no_delete" in names
