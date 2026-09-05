"""P6 — FairnessGate: manifest loading + pass/fail evaluation."""

from __future__ import annotations

import json

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from services.core.monitoring.governance import (
    DEFAULT_MANIFEST,
    FairnessGate,
    ManifestError,
    load_manifest,
    manifest_hash,
)
from services.core.shared.models import FairnessAuditLog


def test_manifest_loads_and_has_stable_hash() -> None:
    m = load_manifest()
    assert m["version"]
    assert "thresholds" in m
    h1 = manifest_hash(m)
    h2 = manifest_hash(m)
    assert h1 == h2 and len(h1) == 16


def test_missing_manifest_raises(tmp_path) -> None:
    fake = tmp_path / "missing.json"
    with pytest.raises(ManifestError):
        load_manifest(fake)


def test_bad_manifest_raises(tmp_path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"thresholds": {}}))
    with pytest.raises(ManifestError):
        load_manifest(bad)


@pytest.mark.asyncio
async def test_gate_passes_when_within_thresholds(db_session: AsyncSession) -> None:
    # Two OK rows for GENDER within min_approval_rate=0.35, gap 0.05
    db_session.add_all([
        FairnessAuditLog(
            period="2026-W40", dimension="GENDER", group_value="F",
            sample_size=50, approval_rate=0.6, override_rate=0.05, status="OK",
        ),
        FairnessAuditLog(
            period="2026-W40", dimension="GENDER", group_value="M",
            sample_size=60, approval_rate=0.65, override_rate=0.05, status="OK",
        ),
    ])
    await db_session.commit()
    result = await FairnessGate(db_session).evaluate("2026-W40")
    assert result.passed is True
    assert result.breaches == []
    assert result.evaluated_rows == 2


@pytest.mark.asyncio
async def test_gate_flags_low_approval_rate(db_session: AsyncSession) -> None:
    db_session.add(FairnessAuditLog(
        period="2026-W41", dimension="GENDER", group_value="F",
        sample_size=50, approval_rate=0.20, override_rate=0.05, status="OK",
    ))
    await db_session.commit()
    result = await FairnessGate(db_session).evaluate("2026-W41")
    assert result.passed is False
    assert any(b.rule == "min_approval_rate" for b in result.breaches)


@pytest.mark.asyncio
async def test_gate_flags_high_override_rate(db_session: AsyncSession) -> None:
    db_session.add(FairnessAuditLog(
        period="2026-W42", dimension="OFFICER", group_value="off-x",
        sample_size=40, approval_rate=0.6, override_rate=0.80, status="OK",
    ))
    await db_session.commit()
    result = await FairnessGate(db_session).evaluate("2026-W42")
    assert result.passed is False
    assert any(b.rule == "max_override_rate" for b in result.breaches)


@pytest.mark.asyncio
async def test_gate_skips_insufficient_sample_rows(db_session: AsyncSession) -> None:
    db_session.add(FairnessAuditLog(
        period="2026-W43", dimension="GENDER", group_value="O",
        sample_size=3, approval_rate=None, override_rate=None,
        status="INSUFFICIENT_SAMPLE",
    ))
    await db_session.commit()
    result = await FairnessGate(db_session).evaluate("2026-W43")
    assert result.skipped_insufficient == 1
    assert result.evaluated_rows == 0
    assert result.passed is True   # no rows to evaluate = no breach


def test_manifest_default_path_exists() -> None:
    assert DEFAULT_MANIFEST.exists(), (
        f"Ratified thresholds manifest missing at {DEFAULT_MANIFEST}"
    )
