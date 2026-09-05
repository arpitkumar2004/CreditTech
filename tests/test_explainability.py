"""P3.5 tests — SHAP-equivalent contributions + reason-code rendering."""

from ml.evaluation.explain import ScorecardSHAPExplainer
from ml.training.scorecard import LogisticScorecard
from services.core.explainability.service import ExplainabilityService


def _scorecard():
    return LogisticScorecard()


def test_positive_and_negative_contributions():
    sc = _scorecard()
    expl = ScorecardSHAPExplainer(sc)
    # High repayment rate + low utility payments -> mixed signs
    features = {"shg_repayment_rate": 100.0, "utility_payment_ontime_pct": 40.0}
    contrib = expl.compute_shap_values(features)
    by_feat = {c["feature"]: c for c in contrib}
    assert by_feat["shg_repayment_rate"]["shap_value"] > 0
    assert by_feat["utility_payment_ontime_pct"]["shap_value"] < 0


def test_missing_features_are_skipped_safely():
    sc = _scorecard()
    expl = ScorecardSHAPExplainer(sc)
    contrib = expl.compute_shap_values({"shg_repayment_rate": None, "asset_score": 0.7})
    features_out = {c["feature"] for c in contrib}
    assert "shg_repayment_rate" not in features_out
    assert "asset_score" in features_out


def test_unknown_feature_ignored():
    sc = _scorecard()
    expl = ScorecardSHAPExplainer(sc)
    contrib = expl.compute_shap_values({"asset_score": 0.9, "not_a_real_feature": 1.0})
    features_out = {c["feature"] for c in contrib}
    assert "not_a_real_feature" not in features_out


def test_deterministic_top_n_ordering():
    sc = _scorecard()
    expl = ScorecardSHAPExplainer(sc)
    features = {
        "shg_repayment_rate": 100.0,
        "asset_score": 0.9,
        "land_quality_ndvi_avg": 0.9,
        "ndvi_trend_2season": 0.3,
        "utility_payment_ontime_pct": 95.0,
    }
    a = expl.compute_shap_values(features)
    b = expl.compute_shap_values(features)
    assert [c["feature"] for c in a] == [c["feature"] for c in b]


def test_reason_code_rendering_bilingual():
    svc = ExplainabilityService()
    shap_values = [
        {"feature": "shg_repayment_rate", "value": 96.0, "shap_value": 2.7},
        {"feature": "income_stability_cv", "value": 1.1, "shap_value": -0.24},
    ]
    codes = svc.render_reason_codes(shap_values, limit=5)
    assert len(codes) == 2
    assert codes[0]["direction"] == "POSITIVE"
    assert "96.0" in codes[0]["localized_text_en"]
    assert codes[0]["localized_text_hi"]
    assert codes[1]["direction"] == "NEGATIVE"


def test_reason_code_skips_unmapped_features():
    svc = ExplainabilityService()
    shap_values = [{"feature": "not_in_template_lib", "value": 1.0, "shap_value": 1.0}]
    assert svc.render_reason_codes(shap_values, limit=5) == []
