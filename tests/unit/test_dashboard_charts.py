"""Tests for persona-tailored decision graphs and charts endpoint."""

import pytest
from httpx import ASGITransport, AsyncClient

from ml.registry import ModelRegistry
from services.core.admin.promotion import ModelPromotionService
from services.core.main import app


@pytest.mark.asyncio
async def test_dashboard_charts_admin_persona(db_session):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/v1/dashboard/charts?persona=admin")
        assert resp.status_code == 200
        data = resp.json()
        assert data["persona"] == "admin"
        assert "model_version" in data
        assert "roc_curve" in data
        assert "auc" in data["roc_curve"]
        assert len(data["roc_curve"]["points"]) > 0

        assert "ks_separation" in data
        assert "max_ks" in data["ks_separation"]
        assert len(data["ks_separation"]["curve"]) > 0

        assert "calibration" in data
        assert "brier_score" in data["calibration"]
        assert len(data["calibration"]["bins"]) > 0

        assert "gains_lift" in data
        assert len(data["gains_lift"]) > 0

        assert "score_distribution" in data
        assert "zones_summary" in data["score_distribution"]

        assert "fairness_parity" in data
        assert data["fairness_parity"]["gender_ceiling"] == 20.0
        assert data["fairness_parity"]["landholding_ceiling"] == 25.0

        assert "drift_radar" in data


@pytest.mark.asyncio
async def test_dashboard_charts_officer_persona(db_session):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/v1/dashboard/charts?persona=officer")
        assert resp.status_code == 200
        data = resp.json()
        assert data["persona"] == "officer"
        assert "score_zones" in data
        assert "stp_approve_pct" in data["score_zones"]
        assert "manual_review_pct" in data["score_zones"]
        assert "actionable_reject_pct" in data["score_zones"]

        assert "confidence_intervals" in data
        assert len(data["confidence_intervals"]) == 5

        assert "ndvi_trajectory" in data
        assert len(data["ndvi_trajectory"]) == 12
        assert data["ndvi_trajectory"][0]["month"] == "Jun"

        assert "branch_overrides" in data
        assert "reasons_breakdown" in data["branch_overrides"]

        assert "feature_importance" in data
        assert len(data["feature_importance"]) >= 4


@pytest.mark.asyncio
async def test_dashboard_charts_borrower_persona(db_session):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/v1/dashboard/charts?persona=borrower")
        assert resp.status_code == 200
        data = resp.json()
        assert data["persona"] == "borrower"
        assert "borrower_summary" in data
        assert data["borrower_summary"]["target_score"] == 650

        assert "recourse_ladder" in data
        assert len(data["recourse_ladder"]) == 3
        # Check bilingual support
        assert "title_hi" in data["recourse_ladder"][0]
        assert "title_en" in data["recourse_ladder"][0]

        assert "cashflow_pulse" in data
        assert len(data["cashflow_pulse"]) == 12

        assert "top_strengths" in data
        assert len(data["top_strengths"]) == 3
        assert "title_hi" in data["top_strengths"][0]


@pytest.mark.asyncio
async def test_promotion_report_includes_plots_data(db_session):
    registry = ModelRegistry()
    active = registry.get_active()
    assert active is not None

    service = ModelPromotionService(db=db_session, registry=registry)
    report = await service.evaluate(active.model_version)
    assert report.model_version == active.model_version
    assert isinstance(report.plots_data, dict)
    assert ("roc_auc" in report.plots_data or "roc_curve" in report.plots_data)
    assert "ks_separation" in report.plots_data
    assert "calibration" in report.plots_data
