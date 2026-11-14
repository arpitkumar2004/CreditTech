"""P6 — Production smoke-test framework verdicts."""

from __future__ import annotations

import pytest

from services.core.ops import smoke as smoke_mod


def test_live_creds_absent_by_default(monkeypatch) -> None:
    monkeypatch.delenv("AA_API_KEY", raising=False)
    monkeypatch.delenv("BUREAU_API_KEY", raising=False)
    monkeypatch.delenv("GEOSPATIAL_API_KEY", raising=False)
    assert smoke_mod._live_creds_present("AA") is False
    assert smoke_mod._live_creds_present("BUREAU") is False
    assert smoke_mod._live_creds_present("GEOSPATIAL") is False


def test_live_creds_detected_when_real_env(monkeypatch) -> None:
    monkeypatch.setenv("BUREAU_API_KEY", "live-secret-xyz")
    monkeypatch.setenv("BUREAU_BASE_URL", "https://sandbox.bureau.example.com/v1")
    assert smoke_mod._live_creds_present("BUREAU") is True


def test_demo_prefix_is_not_live(monkeypatch) -> None:
    monkeypatch.setenv("AA_API_KEY", "DEMO-anything")
    monkeypatch.setenv("AA_BASE_URL", "https://real.example.com")
    assert smoke_mod._live_creds_present("AA") is False


@pytest.mark.asyncio
async def test_smoke_all_returns_blocked_verdict_without_creds(monkeypatch) -> None:
    monkeypatch.delenv("AA_API_KEY", raising=False)
    monkeypatch.delenv("BUREAU_API_KEY", raising=False)
    monkeypatch.delenv("GEOSPATIAL_API_KEY", raising=False)
    result = await smoke_mod.run_all()
    assert result["overall"] in {"BLOCKED", "FAIL"}
    for r in result["results"]:
        assert r["connector"] in {"AA", "GEOSPATIAL", "BUREAU"}
        assert r["verdict"] in {"BLOCKED", "PASS", "FAIL", "ERROR"}
