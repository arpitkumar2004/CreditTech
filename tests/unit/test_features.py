"""P3.1 tests — feature engineering pipeline."""

from datetime import datetime

from ml.features.pipeline import build_feature_vector, tag_season
from ml.features.schema import FEATURE_VERSION, MODEL_FEATURE_NAMES


def test_tag_season_boundaries():
    assert tag_season(datetime(2026, 6, 15)) == "KHARIF"
    assert tag_season(datetime(2026, 10, 31)) == "KHARIF"
    assert tag_season(datetime(2026, 11, 1)) == "RABI"
    assert tag_season(datetime(2026, 2, 15)) == "RABI"
    assert tag_season(datetime(2026, 4, 15)) == "ZAID"


def test_complete_flat_input_produces_all_features():
    raw = {name: 1.0 for name in MODEL_FEATURE_NAMES if name != "shg_grade"}
    raw["shg_grade"] = "B"
    raw["irrigation_access"] = True
    raw["crop_insurance_enrolled"] = False

    res = build_feature_vector(raw, when=datetime(2026, 7, 1))
    assert res.feature_version == FEATURE_VERSION
    assert res.season_tag == "KHARIF"
    assert set(res.features).issuperset(set(MODEL_FEATURE_NAMES))
    assert res.features["shg_grade"] == 0.75
    assert res.features["irrigation_access"] == 1.0
    assert res.features["crop_insurance_enrolled"] == 0.0
    assert res.missing == []


def test_missing_rail_is_reported_not_zeroed():
    raw = {"shg_repayment_rate": 0.95}  # nothing else
    res = build_feature_vector(raw)
    assert "shg_repayment_rate" in res.features
    # zero != missing: zero is a valid value; missing means "no source data"
    assert "monthly_avg_credit_inflow" in res.missing
    assert "monthly_avg_credit_inflow" not in res.features


def test_invalid_values_are_treated_as_missing_not_zeroed():
    raw = {"shg_repayment_rate": "notanumber", "land_holding_acres": None}
    res = build_feature_vector(raw)
    assert "shg_repayment_rate" in res.missing
    assert "land_holding_acres" in res.missing


def test_prohibited_pii_fields_dropped():
    raw = {
        "shg_repayment_rate": 0.9,
        "aadhaar": "1234-5678-9012",
        "name": "Sita Devi",
        "caste": "X",
    }
    res = build_feature_vector(raw)
    assert "aadhaar" in res.excluded_pii
    assert "name" in res.excluded_pii
    assert "caste" in res.excluded_pii
    assert not any(f in res.features for f in ["aadhaar", "name", "caste"])


def test_monitored_only_fields_excluded_from_features():
    raw = {"shg_repayment_rate": 0.9, "gender": "F", "village_id": "abc",
           "landholding_band": "SMALL"}
    res = build_feature_vector(raw)
    assert set(res.excluded_monitored) == {"gender", "landholding_band", "village_id"}
    assert "gender" not in res.features


def test_deterministic_output():
    raw = {"shg_repayment_rate": 0.9, "asset_score": 0.4, "land_holding_acres": 2.5,
           "irrigation_access": True, "shg_grade": "A"}
    a = build_feature_vector(raw, when=datetime(2026, 12, 1))
    b = build_feature_vector(raw, when=datetime(2026, 12, 1))
    assert a.features == b.features
    assert a.season_tag == b.season_tag
    assert a.missing == b.missing


def test_source_partitioned_input_flattens():
    raw = {
        "AA": {"upi_transaction_regularity": 0.3, "bank_balance_avg_6m": 5000.0},
        "SHG_FPO": {"shg_repayment_rate": 0.98, "shg_grade": "A"},
        "GEOSPATIAL": {"land_quality_ndvi_avg": 0.7, "ndvi_trend_2season": 0.1},
    }
    res = build_feature_vector(raw, when=datetime(2026, 7, 1))
    assert res.features["shg_grade"] == 1.0
    assert res.provenance["shg_repayment_rate"] == "SHG_FPO"
    assert res.provenance["bank_balance_avg_6m"] == "AA"
