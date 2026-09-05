"""P6 — Production integration smoke-test framework.

Goals:
    * Every external connector (AA / Geospatial / Bureau) exposes a smoke check.
    * When live sandbox credentials are configured via env, the check runs
      against the sandbox.
    * When credentials are absent, the check runs against the local mock
      endpoints so CI still exercises the code path — and it returns a
      `BLOCKED` verdict with `reason="credentials_absent"` so the operator
      knows this is not a production readiness pass.
    * We never fabricate credentials; missing env is always surfaced.

Verdict values:
    * PASS       — real sandbox responded correctly
    * BLOCKED    — no live creds; ran against local mock (dev/CI happy path)
    * FAIL       — connector reachable but response invalid / error
    * ERROR      — connector unreachable / raised exception
"""

from __future__ import annotations

import asyncio
import os
import uuid
from dataclasses import asdict, dataclass
from typing import Any

import httpx

from services.core.ingestion.connectors import (
    AccountAggregatorConnector,
    BureauConnector,
    ConnectorError,
    GeospatialConnector,
)


@dataclass
class SmokeResult:
    connector: str
    verdict: str            # PASS / BLOCKED / FAIL / ERROR
    reason: str
    latency_ms: float
    sample: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


DEMO_BORROWER = uuid.UUID("00000000-0000-0000-0000-000000000001")


def _live_creds_present(prefix: str) -> bool:
    """Live creds are present when both a URL override AND an API key exist
    that are not the DEMO defaults."""
    url = os.environ.get(f"{prefix}_BASE_URL", "")
    key = os.environ.get(f"{prefix}_API_KEY", "")
    if not key or key.startswith("DEMO") or key == "mock_api_key":
        return False
    if not url or "localhost" in url or "testserver" in url or "mock" in url:
        return False
    return True


def _asgi_client_for_mocks() -> httpx.AsyncClient:
    """Wire connectors to the in-process ASGI mock router when no live creds."""
    from services.core.main import app
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
        timeout=10.0,
    )


async def _time(coro):
    loop = asyncio.get_event_loop()
    t0 = loop.time()
    result = await coro
    return result, (loop.time() - t0) * 1000


async def smoke_account_aggregator() -> SmokeResult:
    live = _live_creds_present("AA")
    connector = AccountAggregatorConnector()
    if not live:
        connector.client = _asgi_client_for_mocks()
        connector.base_url = "http://testserver/api/v1/mock/aa"
    try:
        data, latency = await _time(
            connector.fetch_bank_data(DEMO_BORROWER, aa_consent_id="DEMO-CONSENT")
        )
        if not isinstance(data, dict) or "status" not in data:
            return SmokeResult("AA", "FAIL", "missing expected fields", latency, sample=data)
        return SmokeResult(
            "AA",
            "PASS" if live else "BLOCKED",
            "sandbox reachable" if live else "credentials_absent — ran against local mock",
            latency, sample={"status": data.get("status")},
        )
    except ConnectorError as e:
        return SmokeResult("AA", "ERROR", f"ConnectorError: {e}", 0.0)
    except Exception as e:
        return SmokeResult("AA", "ERROR", f"{type(e).__name__}: {e}", 0.0)


async def smoke_geospatial() -> SmokeResult:
    live = _live_creds_present("GEOSPATIAL")
    connector = GeospatialConnector()
    if not live:
        connector.client = _asgi_client_for_mocks()
        connector.base_url = "http://testserver/api/v1/mock/geospatial"
    try:
        data, latency = await _time(
            connector.fetch_satellite_data(DEMO_BORROWER, latitude=27.0, longitude=74.0)
        )
        if not isinstance(data, dict) or "ndvi_avg" not in data:
            return SmokeResult("GEOSPATIAL", "FAIL", "missing expected fields", latency, sample=data)
        return SmokeResult(
            "GEOSPATIAL",
            "PASS" if live else "BLOCKED",
            "sandbox reachable" if live else "credentials_absent — ran against local mock",
            latency, sample={"ndvi_avg": data.get("ndvi_avg")},
        )
    except ConnectorError as e:
        return SmokeResult("GEOSPATIAL", "ERROR", f"ConnectorError: {e}", 0.0)
    except Exception as e:
        return SmokeResult("GEOSPATIAL", "ERROR", f"{type(e).__name__}: {e}", 0.0)


async def smoke_bureau() -> SmokeResult:
    live = _live_creds_present("BUREAU")
    connector = BureauConnector()
    if not live:
        connector.client = _asgi_client_for_mocks()
        connector.base_url = "http://testserver/api/v1/mock/bureau"
    try:
        data, latency = await _time(
            connector.fetch_credit_profile("a" * 64)
        )
        if not isinstance(data, dict):
            return SmokeResult("BUREAU", "FAIL", "non-dict response", latency, sample=None)
        return SmokeResult(
            "BUREAU",
            "PASS" if live else "BLOCKED",
            "sandbox reachable" if live else "credentials_absent — ran against local mock",
            latency, sample={"keys": sorted(list(data.keys()))[:5]},
        )
    except ConnectorError as e:
        return SmokeResult("BUREAU", "ERROR", f"ConnectorError: {e}", 0.0)
    except Exception as e:
        return SmokeResult("BUREAU", "ERROR", f"{type(e).__name__}: {e}", 0.0)


async def run_all() -> dict[str, Any]:
    results = await asyncio.gather(
        smoke_account_aggregator(), smoke_geospatial(), smoke_bureau(),
        return_exceptions=False,
    )
    verdicts = [r.verdict for r in results]
    return {
        "overall": (
            "PASS" if all(v == "PASS" for v in verdicts)
            else "BLOCKED" if all(v in {"PASS", "BLOCKED"} for v in verdicts)
            else "FAIL"
        ),
        "results": [r.to_dict() for r in results],
    }


__all__ = [
    "smoke_account_aggregator", "smoke_geospatial", "smoke_bureau",
    "run_all", "SmokeResult",
]
