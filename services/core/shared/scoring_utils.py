"""Unified scoring and borrower presentation utilities.

Eliminates data disparities across CreditTech by guaranteeing that:
1. Every score has a mathematically coherent 0-100 scale and 300-900 scale representation.
2. Functional bands (EXCELLENT, GOOD, MODERATE, HIGH_RISK, VERY_HIGH_RISK) are assigned consistently.
3. Confidence intervals are bounded and scaled correctly.
4. Encrypted borrower names (e.g. "enc:Radhika Devi") are cleaned for presentation.
"""

from __future__ import annotations

from typing import Any


def clean_borrower_name(raw_name: str | None, borrower_id: Any = None) -> str:
    """Returns a clean, human-readable borrower name."""
    if not raw_name:
        return f"Applicant {str(borrower_id)[:6]}" if borrower_id else "Rural Borrower"
    name = str(raw_name).strip()
    if name.startswith("enc:"):
        name = name[4:].strip()
    elif name.startswith("enc_"):
        name = name[4:].strip()
    if not name or len(name) > 60:
        return f"Applicant {str(borrower_id)[:6]}" if borrower_id else "Rural Borrower"
    return name


def normalize_score(
    score_raw: float,
    conf_lower_raw: float | None = None,
    conf_upper_raw: float | None = None,
) -> dict[str, Any]:
    """Converts any raw score (0-100 or 300-900) into a guaranteed uniform format.

    Returns:
        dict with:
            score_100: float (0.0 to 100.0)
            score_900: int (300 to 900)
            band: str ('EXCELLENT' | 'GOOD' | 'MODERATE' | 'HIGH_RISK' | 'VERY_HIGH_RISK')
            confidence_lower_100: float
            confidence_upper_100: float
            confidence_lower_900: int
            confidence_upper_900: int
            confidence_range_900: list[int, int]
    """
    raw = float(score_raw)
    if raw <= 100.0:
        score_100 = round(raw, 1)
        score_900 = int(round(300.0 + (score_100 / 100.0) * 600.0))
    else:
        score_900 = int(round(raw))
        score_100 = round((score_900 - 300.0) / 6.0, 1)

    score_100 = max(0.0, min(100.0, score_100))
    score_900 = max(300, min(900, score_900))

    # Determine Functional Assessment Band
    if score_100 >= 81.0:
        band = "EXCELLENT"
    elif score_100 >= 66.0:
        band = "GOOD"
    elif score_100 >= 51.0:
        band = "MODERATE"
    elif score_100 >= 31.0:
        band = "HIGH_RISK"
    else:
        band = "VERY_HIGH_RISK"

    # Normalize Confidence Lower Bound
    if conf_lower_raw is not None:
        c_low = float(conf_lower_raw)
        if c_low <= 100.0:
            c_low_100 = round(c_low, 1)
            c_low_900 = int(round(300.0 + (c_low_100 / 100.0) * 600.0))
        else:
            c_low_900 = int(round(c_low))
            c_low_100 = round((c_low_900 - 300.0) / 6.0, 1)
    else:
        c_low_100 = max(0.0, score_100 - 5.0)
        c_low_900 = max(300, score_900 - 30)

    # Normalize Confidence Upper Bound
    if conf_upper_raw is not None:
        c_high = float(conf_upper_raw)
        if c_high <= 100.0:
            c_high_100 = round(c_high, 1)
            c_high_900 = int(round(300.0 + (c_high_100 / 100.0) * 600.0))
        else:
            c_high_900 = int(round(c_high))
            c_high_100 = round((c_high_900 - 300.0) / 6.0, 1)
    else:
        c_high_100 = min(100.0, score_100 + 5.0)
        c_high_900 = min(900, score_900 + 30)

    # Sanity bounds check
    c_low_900 = min(c_low_900, score_900)
    c_high_900 = max(c_high_900, score_900)
    c_low_100 = min(c_low_100, score_100)
    c_high_100 = max(c_high_100, score_100)

    return {
        "score_100": score_100,
        "score_900": score_900,
        "band": band,
        "confidence_lower_100": c_low_100,
        "confidence_upper_100": c_high_100,
        "confidence_lower_900": c_low_900,
        "confidence_upper_900": c_high_900,
        "confidence_range_900": [c_low_900, c_high_900],
    }
