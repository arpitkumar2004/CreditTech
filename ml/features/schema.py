"""Feature schema for CreditTech scoring — the authoritative list of
model-input features, sourced from docs/phase0/preliminary_feature_list.md.

Any feature not listed in MODEL_FEATURES MUST NOT enter the model.
Any field in PROHIBITED_FIELDS MUST NEVER appear in a feature vector.
Any field in MONITORED_ONLY_FIELDS may be used for fairness/monitoring only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

FEATURE_VERSION = "v1.0.0"

FiveC = Literal["character", "capacity", "capital", "collateral", "conditions", "digital"]


@dataclass(frozen=True)
class FeatureDef:
    name: str
    five_c: FiveC
    dtype: Literal["float", "int", "bool", "categorical"]
    source: str
    default_when_missing: float | int | bool | None
    # If categorical, mapping to numeric proxy. None otherwise.
    category_map: dict[str, float] | None = None


MODEL_FEATURES: tuple[FeatureDef, ...] = (
    # Character
    FeatureDef("shg_repayment_rate", "character", "float", "SHG_FPO", None),
    FeatureDef("shg_meeting_attendance_pct", "character", "float", "SHG_FPO", None),
    FeatureDef("shg_savings_consistency", "character", "float", "SHG_FPO", None),
    FeatureDef("shg_membership_years", "character", "int", "SHG_FPO", None),
    FeatureDef(
        "shg_grade",
        "character",
        "categorical",
        "SHG_FPO",
        None,
        category_map={"A": 1.0, "B": 0.75, "C": 0.5, "D": 0.1},
    ),
    FeatureDef("utility_payment_ontime_pct", "character", "float", "AA_OR_BUREAU", None),
    FeatureDef("upi_transaction_regularity", "character", "float", "AA", None),
    # Capacity
    FeatureDef("estimated_crop_income_kharif", "capacity", "float", "GEOSPATIAL_MANUAL", None),
    FeatureDef("estimated_crop_income_rabi", "capacity", "float", "GEOSPATIAL_MANUAL", None),
    FeatureDef("income_stability_cv", "capacity", "float", "AA_MANUAL", None),
    FeatureDef("monthly_avg_credit_inflow", "capacity", "float", "AA", None),
    FeatureDef("pm_kisan_regularity", "capacity", "float", "AA", None),
    # Capital
    FeatureDef("shg_cumulative_savings", "capital", "float", "SHG_FPO", None),
    FeatureDef("bank_balance_avg_6m", "capital", "float", "AA", None),
    FeatureDef("asset_score", "capital", "float", "MANUAL", None),
    # Collateral
    FeatureDef("land_holding_acres", "collateral", "float", "MANUAL_DIGILOCKER", None),
    FeatureDef("irrigation_access", "collateral", "bool", "MANUAL_GEOSPATIAL", None),
    FeatureDef("land_quality_ndvi_avg", "collateral", "float", "GEOSPATIAL", None),
    # Conditions
    FeatureDef("ndvi_trend_2season", "conditions", "float", "GEOSPATIAL", None),
    FeatureDef("rainfall_deviation_pct", "conditions", "float", "GEOSPATIAL_IMD", None),
    FeatureDef("crop_insurance_enrolled", "conditions", "bool", "MANUAL_PMFBY", None),
)

MODEL_FEATURE_NAMES: tuple[str, ...] = tuple(f.name for f in MODEL_FEATURES)
FEATURE_INDEX: dict[str, FeatureDef] = {f.name: f for f in MODEL_FEATURES}

# Absolute prohibited: never used, never monitored — PII / illegal proxies.
PROHIBITED_FIELDS: frozenset[str] = frozenset({
    "aadhaar", "aadhaar_ref_hash", "name", "name_encrypted",
    "phone", "phone_encrypted", "caste", "religion", "ethnicity",
    "health_status", "disability_status",
})

# Allowed for fairness monitoring, never as model inputs.
MONITORED_ONLY_FIELDS: frozenset[str] = frozenset({
    "gender", "village_id", "landholding_band",
    "site_type", "agro_climatic_zone",
})

# Season tag values (docs/phase0 §4)
VALID_SEASONS: tuple[str, ...] = ("KHARIF", "RABI", "ZAID")
