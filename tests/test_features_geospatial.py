"""Unit tests for Earth Observation (EO) and Remote Sensing Geospatial Processor."""

import pytest

from ml.features.geospatial import PILOT_VILLAGE_CATALOG, SatelliteEOProcessor


def test_village_profile_lookup():
    processor = SatelliteEOProcessor()
    profile = processor.get_village_profile("Tibbi")
    assert profile.district == "Hanumangarh"
    assert profile.irrigation_type == "CANAL"
    assert profile.historical_kharif_ndvi_mean > 0.50

    # Fallback lookup for unknown village
    unknown = processor.get_village_profile("UnknownVillage")
    assert unknown.district == "Hanumangarh"
    assert unknown.village_name == "UnknownVillage"


def test_remote_sensing_assessment():
    processor = SatelliteEOProcessor()

    # Normal season assessment for Hanumangarh-Junction
    normal_res = processor.calculate_assessment(
        village_name="Hanumangarh-Junction",
        season="KHARIF",
        observed_ndvi=0.70,
        observed_rainfall_mm=265.0,
    )
    assert normal_res.drought_risk_tier == "LOW"
    assert normal_res.rainfall_deviation_pct == 0.0
    assert normal_res.irrigation_resilience_factor > 0.8

    # Severe drought scenario for rainfed Nohar
    drought_res = processor.calculate_assessment(
        village_name="Nohar",
        season="KHARIF",
        observed_ndvi=0.25,
        observed_rainfall_mm=110.0,
    )
    assert drought_res.drought_risk_tier == "SEVERE"
    assert drought_res.rainfall_deviation_pct < -30.0


def test_generate_feature_snapshot_inputs():
    processor = SatelliteEOProcessor()
    inputs = processor.generate_feature_snapshot_inputs(
        village_name="Sangaria",
        season="RABI",
        land_holding_acres=3.5,
    )

    assert "land_quality_ndvi_avg" in inputs
    assert "ndvi_trend_2season" in inputs
    assert "rainfall_deviation_pct" in inputs
    assert inputs["irrigation_access"] is True
    assert inputs["land_holding_acres"] == 3.5
