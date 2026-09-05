"""P6 — Security hardening: headers + rate limit + body cap."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_security_headers_applied(client: AsyncClient) -> None:
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.headers.get("x-content-type-options") == "nosniff"
    assert r.headers.get("referrer-policy") == "no-referrer"
    assert r.headers.get("x-frame-options") == "DENY"
    assert "strict-transport-security" in r.headers


@pytest.mark.asyncio
async def test_body_size_limit_enforced(client: AsyncClient) -> None:
    huge = "x" * (1_048_577)  # 1 MiB + 1
    r = await client.post(
        "/api/v1/grievances/",
        headers={
            "X-Borrower-Id": "00000000-0000-0000-0000-000000000000",
            "Content-Type": "application/json",
        },
        content=huge,
    )
    assert r.status_code == 413


@pytest.mark.asyncio
async def test_rate_limit_kicks_in(monkeypatch) -> None:
    """Unit-test the middleware directly; global bypass is on in conftest."""
    from starlette.applications import Starlette
    from starlette.routing import Route
    from starlette.responses import PlainTextResponse
    from httpx import ASGITransport
    from services.core.shared.security_middleware import RateLimitMiddleware

    monkeypatch.delenv("DISABLE_RATE_LIMIT", raising=False)

    async def ok(_):
        return PlainTextResponse("ok")

    app = Starlette(routes=[Route("/ok", ok)])
    app.add_middleware(RateLimitMiddleware, per_minute=5)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
        codes = [(await ac.get("/ok")).status_code for _ in range(8)]
    assert codes.count(429) >= 1
    assert codes[:5] == [200] * 5
