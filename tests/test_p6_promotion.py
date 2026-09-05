"""P6 — Model promotion pipeline: fairness + performance gate."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from services.core.admin.promotion import (
    PERFORMANCE_MINIMUMS,
    ModelPromotionService,
    PromotionBlocked,
)
from services.core.shared.models import FairnessAuditLog


class _FakeRecord:
    def __init__(self, mv: str, metrics: dict, status: str = "candidate") -> None:
        self.model_version = mv
        self.metrics = metrics
        self.promotion_status = status


class _FakeRegistry:
    def __init__(self, records: dict[str, _FakeRecord]) -> None:
        self.records = records
        self.promotions: list[tuple[str, str]] = []

    def get(self, mv: str):
        return self.records.get(mv)

    def promote(self, mv: str, to_status: str):
        self.promotions.append((mv, to_status))
        r = self.records[mv]
        r.promotion_status = to_status
        return r


def _good_metrics() -> dict:
    return {
        "auc": 0.75, "gini": 0.50, "ks": 0.35,
        "brier": PERFORMANCE_MINIMUMS["brier_max"] - 0.05,
    }


def _bad_metrics() -> dict:
    return {"auc": 0.55, "gini": 0.10, "ks": 0.10, "brier": 0.40}


@pytest.mark.asyncio
async def test_promotion_blocked_when_performance_bad(db_session: AsyncSession) -> None:
    reg = _FakeRegistry({"m1": _FakeRecord("m1", _bad_metrics())})
    svc = ModelPromotionService(db_session, registry=reg)
    with pytest.raises(PromotionBlocked) as ei:
        await svc.promote_to_active("m1")
    r = ei.value.report
    assert r.performance_pass is False
    assert reg.promotions == []


@pytest.mark.asyncio
async def test_promotion_blocked_when_fairness_bad(db_session: AsyncSession) -> None:
    # Good perf, bad fairness (approval rate below GENDER min)
    db_session.add(FairnessAuditLog(
        period="2026-W50", dimension="GENDER", group_value="F",
        sample_size=40, approval_rate=0.10, override_rate=0.0, status="OK",
    ))
    await db_session.commit()
    reg = _FakeRegistry({"m2": _FakeRecord("m2", _good_metrics())})
    svc = ModelPromotionService(db_session, registry=reg)
    with pytest.raises(PromotionBlocked) as ei:
        await svc.promote_to_active("m2")
    r = ei.value.report
    assert r.performance_pass is True
    assert r.fairness_pass is False
    assert reg.promotions == []


@pytest.mark.asyncio
async def test_promotion_succeeds_when_both_pass(db_session: AsyncSession) -> None:
    db_session.add_all([
        FairnessAuditLog(
            period="2026-W51", dimension="GENDER", group_value="F",
            sample_size=40, approval_rate=0.60, override_rate=0.05, status="OK",
        ),
        FairnessAuditLog(
            period="2026-W51", dimension="GENDER", group_value="M",
            sample_size=40, approval_rate=0.65, override_rate=0.05, status="OK",
        ),
    ])
    await db_session.commit()
    reg = _FakeRegistry({"m3": _FakeRecord("m3", _good_metrics())})
    svc = ModelPromotionService(db_session, registry=reg)
    report = await svc.promote_to_active("m3")
    assert report.passed is True
    assert ("m3", "validated") in reg.promotions
    assert ("m3", "active") in reg.promotions


@pytest.mark.asyncio
async def test_unknown_model_raises(db_session: AsyncSession) -> None:
    reg = _FakeRegistry({})
    svc = ModelPromotionService(db_session, registry=reg)
    with pytest.raises(KeyError):
        await svc.evaluate("does-not-exist")
