"""P6 — Load test.

Plan §9 P6 DoD: "load test verifying the system handles 30 applications/day
at 2x pilot-peak volume." Pilot peak per §2.2 = 20-30 apps/day across all
5 sites. 2x = 60 scored applications in a working day. System SLA per §2.2
is < 2 minutes per score. This harness proves both throughput and per-request
latency comfortably beat the pilot's daily volume even on a laptop-scale
in-process test.

This is an in-process harness using httpx.ASGITransport — no external
load-gen tool needed, runs in CI. For staging-tier volume testing, see
`docs/phase7/load_test_runbook.md`.
"""

from __future__ import annotations

import statistics
import time

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from services.core.shared.models import Borrower, FeatureSnapshot, Village

# 2x pilot peak per plan §9 P6 DoD
BURST_SIZE = 60
# System SLA per §2.2 — score generation < 2 min
SLA_MS = 120_000
# In-process P95 target (orders of magnitude below SLA)
P95_TARGET_MS = 2_000


@pytest.mark.asyncio
async def test_60_scoring_requests_within_sla(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Fire 2x-peak scoring volume against the running app and assert both
    per-request SLA (§2.2, <2min) and pilot-realistic throughput."""
    village = Village(name="V-load", site_type="X", state="RJ", district="D")
    db_session.add(village)
    await db_session.flush()

    borrowers: list[Borrower] = []
    for i in range(BURST_SIZE):
        b = Borrower(
            aadhaar_ref_hash=f"{i:064d}",
            name_encrypted="e",
            phone_encrypted="e",
            village_id=village.id,
            gender="F" if i % 2 == 0 else "M",
            age=25 + (i % 30),
            landholding_band="MARGINAL" if i % 2 == 0 else "SMALL",
        )
        db_session.add(b)
        borrowers.append(b)
    await db_session.flush()

    for b in borrowers:
        db_session.add(
            FeatureSnapshot(
                borrower_id=b.id,
                feature_version="v1.0.0",
                features_json={
                    "shg_repayment_rate": 0.85,
                    "aa_avg_monthly_credit": 12000.0,
                    "aa_avg_monthly_debit": 9500.0,
                    "land_quality_ndvi_avg": 0.62,
                },
                season_tag="RABI",
                sources_used=["SHG_FPO", "AA", "GEOSPATIAL"],
            )
        )
    await db_session.flush()

    latencies: list[float] = []
    codes: list[int] = []
    t_start = time.perf_counter()
    for b in borrowers:
        t0 = time.perf_counter()
        r = await client.post(
            "/api/v1/score/", json={"borrower_id": str(b.id)}
        )
        latencies.append((time.perf_counter() - t0) * 1000.0)
        codes.append(r.status_code)
    wall_ms = (time.perf_counter() - t_start) * 1000.0

    ok = sum(1 for c in codes if c == 201)
    assert ok == BURST_SIZE, f"{ok}/{BURST_SIZE} scored (codes: {set(codes)})"

    latencies.sort()
    p50 = statistics.median(latencies)
    p95 = latencies[int(len(latencies) * 0.95) - 1]
    p_max = latencies[-1]

    # SLA gate — hard per §2.2
    assert p_max < SLA_MS, f"max {p_max:.0f}ms exceeds SLA {SLA_MS}ms"
    # Tight in-process gate
    assert p95 < P95_TARGET_MS, f"p95 {p95:.0f}ms exceeds {P95_TARGET_MS}ms"

    # Throughput: 60 requests must complete well under a working day
    per_req = wall_ms / BURST_SIZE
    print(
        f"\n[LOAD] volume={BURST_SIZE} wall={wall_ms:.0f}ms "
        f"per_req={per_req:.0f}ms p50={p50:.0f}ms p95={p95:.0f}ms "
        f"max={p_max:.0f}ms ok={ok}"
    )
