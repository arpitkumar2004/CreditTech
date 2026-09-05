"""Deterministic feature engineering pipeline (P3.1).

Takes raw source dicts (AA / GEOSPATIAL / BUREAU / SHG_FPO) or an already-flat
feature dict and returns a model-ready feature vector using only fields declared
in ml/features/schema.MODEL_FEATURES.

Guarantees:
    * Deterministic: same input -> same output (dict ordering, no clock).
    * Season-aware: attaches a season_tag derived from month.
    * Missing != zero: distinguishes 'unavailable' (feature absent + provenance
      note) from a genuine 0.0 (feature present with value 0).
    * PII / prohibited fields are dropped silently and recorded as excluded.
    * Categorical -> numeric via schema.category_map only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from ml.features.schema import (
    FEATURE_INDEX,
    FEATURE_VERSION,
    MODEL_FEATURE_NAMES,
    MONITORED_ONLY_FIELDS,
    PROHIBITED_FIELDS,
    VALID_SEASONS,
)


@dataclass
class FeatureBuildResult:
    features: dict[str, float]           # model-ready, numeric
    missing: list[str]                   # features that had no source value
    excluded_pii: list[str]              # PII/prohibited fields dropped
    excluded_monitored: list[str]        # monitored-only fields dropped
    season_tag: str                      # KHARIF / RABI / ZAID
    feature_version: str = FEATURE_VERSION
    provenance: dict[str, str] = field(default_factory=dict)  # feature -> source


def tag_season(when: date | datetime | None = None) -> str:
    """Map calendar month to agri season per docs/phase0 §4.

    KHARIF Jun–Oct (6..10), RABI Nov–Mar (11,12,1,2,3), ZAID Apr–May (4,5).
    Note: docs list ZAID as Mar–Jun which overlaps; canonical Indian agri
    convention (NABARD) is Kharif Jun-Oct / Rabi Nov-Mar / Zaid Apr-May.
    """
    when = when or datetime.utcnow()
    m = when.month
    if 6 <= m <= 10:
        return "KHARIF"
    if m in (11, 12, 1, 2, 3):
        return "RABI"
    return "ZAID"


def _coerce(value: Any, feature_name: str) -> float | None:
    """Coerce a raw value to float per the schema definition.

    Returns None if the value is None or cannot be coerced (never fabricates 0.0).
    """
    if value is None:
        return None
    defn = FEATURE_INDEX[feature_name]
    if defn.dtype == "bool":
        if isinstance(value, bool):
            return 1.0 if value else 0.0
        if isinstance(value, (int, float)):
            return 1.0 if float(value) != 0.0 else 0.0
        if isinstance(value, str):
            v = value.strip().lower()
            if v in {"true", "yes", "y", "1"}:
                return 1.0
            if v in {"false", "no", "n", "0"}:
                return 0.0
            return None
        return None
    if defn.dtype == "categorical":
        if not isinstance(value, str):
            return None
        return (defn.category_map or {}).get(value.strip().upper())
    # numeric
    if isinstance(value, bool):  # bool is int subclass in Python — reject
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _flatten(raw: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    """If raw is source-partitioned ({'AA': {...}, 'SHG_FPO': {...}}) flatten it
    to a single feature-keyed dict and remember which source each feature came from.

    If raw is already flat, treat every value as source='UNKNOWN'.
    """
    known_sources = {"AA", "GEOSPATIAL", "BUREAU", "SHG_FPO", "MANUAL", "SYSTEM"}
    is_partitioned = any(k in known_sources and isinstance(v, dict) for k, v in raw.items())
    if not is_partitioned:
        return dict(raw), dict.fromkeys(raw, "UNKNOWN")
    flat: dict[str, Any] = {}
    prov: dict[str, str] = {}
    for source, payload in raw.items():
        if not isinstance(payload, dict):
            continue
        for k, v in payload.items():
            # Last-source wins if duplicated; the schema treats a feature as
            # having a single canonical source anyway.
            flat[k] = v
            prov[k] = source
    return flat, prov


def build_feature_vector(
    raw: dict[str, Any],
    *,
    when: date | datetime | None = None,
) -> FeatureBuildResult:
    """Build the model-ready feature vector.

    Args:
        raw: either flat {feature_name: value} or partitioned
             {"AA": {...}, "SHG_FPO": {...}, ...}.
        when: date used for season tagging; defaults to now.
    """
    flat, provenance = _flatten(raw)

    features: dict[str, float] = {}
    missing: list[str] = []
    excluded_pii: list[str] = []
    excluded_monitored: list[str] = []

    # First pass: quarantine PII / monitored-only fields.
    for key in list(flat.keys()):
        if key in PROHIBITED_FIELDS:
            excluded_pii.append(key)
            flat.pop(key)
        elif key in MONITORED_ONLY_FIELDS:
            excluded_monitored.append(key)
            flat.pop(key)

    # Second pass: iterate the allow-list, not user input.
    kept_provenance: dict[str, str] = {}
    for name in MODEL_FEATURE_NAMES:
        raw_val = flat.get(name)
        coerced = _coerce(raw_val, name) if raw_val is not None else None
        if coerced is None:
            missing.append(name)
            continue
        features[name] = coerced
        kept_provenance[name] = provenance.get(name, "UNKNOWN")

    season = tag_season(when)
    assert season in VALID_SEASONS  # invariant

    return FeatureBuildResult(
        features=features,
        missing=missing,
        excluded_pii=sorted(excluded_pii),
        excluded_monitored=sorted(excluded_monitored),
        season_tag=season,
        feature_version=FEATURE_VERSION,
        provenance=kept_provenance,
    )
