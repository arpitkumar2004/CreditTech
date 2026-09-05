"""Mock server endpoints for external APIs.

Serves Account Aggregator, Geospatial, and Bureau test payloads
to simplify local development and testing.
"""

import uuid
from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix="/mock", tags=["Developer Mocks"])


@router.get("/aa/fetch/{borrower_id}")
async def mock_aa_fetch(borrower_id: uuid.UUID) -> dict[str, Any]:
    """Returns simulated Account Aggregator bank transaction data."""
    return {
        "borrower_id": str(borrower_id),
        "status": "COMPLETED",
        "avg_balance_6m": 8450.0,
        "avg_credit_inflow": 12500.0,
        "upi_regularity": 0.85,
        "pm_kisan_regularity": 1.0,
        "transactions_count_3m": 142,
    }


@router.get("/geospatial/analysis")
async def mock_geospatial_analysis(
    borrower_id: uuid.UUID, lat: float, lon: float, seasons: int = 2
) -> dict[str, Any]:
    """Returns simulated crop health (NDVI) and weather statistics."""
    return {
        "borrower_id": str(borrower_id),
        "latitude": lat,
        "longitude": lon,
        "seasons_analyzed": seasons,
        "ndvi_avg": 0.72,
        "ndvi_trend": 0.08,  # Positive trend
        "rainfall_dev": -2.5,  # -2.5% below normal
        "irrigation_detected": True,
        "crop_cycles_count": 2,
    }


@router.get("/bureau/report/{aadhaar_hash}")
async def mock_bureau_report(aadhaar_hash: str) -> dict[str, Any]:
    """Returns simulated credit bureau records."""
    return {
        "aadhaar_hash": aadhaar_hash,
        "has_kcc": True,
        "kcc_utilization": 42.5,  # 42.5% of credit limit
        "active_loans_count": 1,
        "overdue_loans_count": 0,
        "delinquency_status": "CURRENT",
        "score_cibil": 680,
    }
