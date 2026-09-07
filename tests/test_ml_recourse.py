"""Unit tests for Actionable Recourse and Counterfactual Explanation Engine."""

import pytest

from ml.evaluation.recourse import (
    NON_ACTIONABLE_FEATURES,
    CounterfactualRecourseEngine,
)
from ml.training.datasets import SyntheticSHGGenerator
from ml.training.woe_scorecard import WoEScorecardTrainer


@pytest.fixture(scope="module")
def trained_scorecard():
    gen = SyntheticSHGGenerator(n=500, seed=42, n_villages=5)
    X, y, _, _ = gen.generate()
    trainer = WoEScorecardTrainer(min_iv=0.01, random_state=42)
    scorecard, _ = trainer.fit(X, y)
    return scorecard


def test_recourse_for_borderline_borrower(trained_scorecard):
    # Construct a weak borrower with low scores
    weak_borrower = {
        "shg_repayment_rate": 0.65,
        "shg_meeting_attendance_pct": 55.0,
        "shg_savings_consistency": 0.20,
        "shg_membership_years": 1,
        "shg_grade": "C",
        "utility_payment_ontime_pct": 60.0,
        "upi_transaction_regularity": 0.10,
        "estimated_crop_income_kharif": 20000.0,
        "estimated_crop_income_rabi": 25000.0,
        "income_stability_cv": 0.70,
        "monthly_avg_credit_inflow": 4000.0,
        "pm_kisan_regularity": 0.50,
        "shg_cumulative_savings": 1500.0,
        "bank_balance_avg_6m": 2000.0,
        "asset_score": 0.3,
        "land_holding_acres": 1.0,
        "irrigation_access": False,
        "land_quality_ndvi_avg": 0.35,
        "ndvi_trend_2season": -0.05,
        "rainfall_deviation_pct": -15.0,
        "crop_insurance_enrolled": False,
    }

    engine = CounterfactualRecourseEngine(trained_scorecard)
    recourse = engine.generate_recourse(weak_borrower, target_score=650)

    assert recourse["eligible"] is True
    assert recourse["current_score"] < 650
    assert recourse["projected_score"] >= recourse["current_score"]
    assert len(recourse["pathways"]) > 0

    for item in recourse["pathways"]:
        # Verify strict non-actionable boundary
        assert item["feature_name"] not in NON_ACTIONABLE_FEATURES
        assert item["target_value"] >= item["current_value"]
        assert len(item["guidance_en"]) > 0
        assert len(item["guidance_hi"]) > 0
        assert item["projected_score_impact"] >= 0


def test_recourse_already_approved_borrower(trained_scorecard):
    strong_borrower = {
        "shg_repayment_rate": 0.99,
        "shg_meeting_attendance_pct": 98.0,
        "shg_savings_consistency": 0.95,
        "shg_membership_years": 5,
        "shg_grade": "A",
        "utility_payment_ontime_pct": 98.0,
        "upi_transaction_regularity": 0.85,
        "estimated_crop_income_kharif": 65000.0,
        "estimated_crop_income_rabi": 70000.0,
        "income_stability_cv": 0.15,
        "monthly_avg_credit_inflow": 12000.0,
        "pm_kisan_regularity": 1.0,
        "shg_cumulative_savings": 15000.0,
        "bank_balance_avg_6m": 12000.0,
        "asset_score": 0.8,
        "land_holding_acres": 4.0,
        "irrigation_access": True,
        "land_quality_ndvi_avg": 0.75,
        "ndvi_trend_2season": 0.15,
        "rainfall_deviation_pct": 2.0,
        "crop_insurance_enrolled": True,
    }

    engine = CounterfactualRecourseEngine(trained_scorecard)
    curr_s = engine._get_score_900(strong_borrower)
    recourse = engine.generate_recourse(strong_borrower, target_score=curr_s)

    # Should report not eligible because already >= target_score
    assert recourse["eligible"] is False
    assert recourse["current_score"] >= curr_s
    assert len(recourse["pathways"]) == 0
