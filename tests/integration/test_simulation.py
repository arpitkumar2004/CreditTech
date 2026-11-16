"""Unit test for the End-to-End Pilot Simulation Router."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_end_to_end_simulation_run(client: AsyncClient) -> None:
    """Trigger the simulated loan lifecycle run and verify output states."""
    response = await client.post("/api/v1/simulate/run")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"
    assert data["borrower_id"] is not None
    assert 0.0 <= data["score_100"] <= 100.0
    assert 300 <= data["score_900"] <= 900
    assert data["decision"] == "APPROVED"
    assert data["re_approved_amount"] == 30000.0
    assert data["data_retention_purged_borrowers"] == 1
