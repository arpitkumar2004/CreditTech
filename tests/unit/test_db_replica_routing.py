"""Unit tests for dual-engine database routing (get_read_db) & PgBouncer support."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

import services.core.database as db_module
from services.core.config import Settings
from services.core.dashboard.router import report_router
from services.core.dashboard.router import router as dashboard_router
from services.core.database import (
    _build_engine_kwargs,
    close_db,
    create_engines,
    get_read_db,
)


@pytest.mark.asyncio
async def test_get_read_db_yields_session():
    """Verify get_read_db yields a valid AsyncSession and closes cleanly."""
    session_count = 0
    async for session in get_read_db():
        assert isinstance(session, AsyncSession)
        session_count += 1
    assert session_count == 1


@pytest.mark.asyncio
async def test_get_read_db_rollback_on_error():
    """Verify get_read_db rolls back the session if an unhandled error occurs."""
    mock_session = AsyncMock(spec=AsyncSession)
    mock_factory = MagicMock(return_value=mock_session)
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None

    with patch.object(db_module, "async_read_session_factory", mock_factory):
        gen = get_read_db()
        session = await anext(gen)
        assert session is mock_session
        with pytest.raises(RuntimeError, match="Query failure"):
            await gen.athrow(RuntimeError("Query failure"))

    mock_session.rollback.assert_awaited_once()
    mock_session.close.assert_awaited_once()


def test_read_engine_aliased_when_read_url_none():
    """When database_read_url is None or equal to database_url, read_engine aliases primary."""
    # Module defaults
    assert db_module.read_engine is db_module.engine
    assert db_module.async_read_session_factory is db_module.async_session_factory

    # Explicit settings with read_url=None
    cfg_none = Settings(
        database_url="sqlite+aiosqlite:///./primary.db",
        database_read_url=None,
    )
    p_eng, p_fact, r_eng, r_fact = create_engines(cfg_none)
    try:
        assert r_eng is p_eng
        assert r_fact is p_fact
    finally:
        p_eng.sync_engine.dispose()

    # Explicit settings with read_url == database_url
    cfg_same = Settings(
        database_url="sqlite+aiosqlite:///./primary.db",
        database_read_url="sqlite+aiosqlite:///./primary.db",
    )
    p_eng2, p_fact2, r_eng2, r_fact2 = create_engines(cfg_same)
    try:
        assert r_eng2 is p_eng2
        assert r_fact2 is p_fact2
    finally:
        p_eng2.sync_engine.dispose()


@pytest.mark.asyncio
async def test_read_engine_distinct_when_read_url_configured():
    """When database_read_url is distinct, a separate read_engine is instantiated."""
    cfg = Settings(
        database_url="sqlite+aiosqlite:///./primary_test.db",
        database_read_url="sqlite+aiosqlite:///./replica_test.db",
    )
    p_eng, p_fact, r_eng, r_fact = create_engines(cfg)
    try:
        assert r_eng is not p_eng
        assert r_fact is not p_fact
        assert "replica_test.db" in str(r_eng.url)
        assert "primary_test.db" in str(p_eng.url)
    finally:
        await p_eng.dispose()
        await r_eng.dispose()


def test_dialect_statement_cache_and_pool_kwargs():
    """Verify statement_cache_size is passed for asyncpg and pool kwargs are set."""
    # PostgreSQL with statement_cache_size == 0
    pg_kwargs = _build_engine_kwargs(
        "postgresql+asyncpg://user:pass@localhost:5432/credittech",
        pool_size=10,
        max_overflow=20,
        statement_cache_size=0,
    )
    assert pg_kwargs["pool_size"] == 10
    assert pg_kwargs["max_overflow"] == 20
    assert pg_kwargs["pool_pre_ping"] is True
    assert pg_kwargs["connect_args"] == {"statement_cache_size": 0}

    # SQLite (must NOT have pool_size or connect_args for statement_cache_size)
    sqlite_kwargs = _build_engine_kwargs(
        "sqlite+aiosqlite:///./test.db",
        pool_size=10,
        max_overflow=20,
        statement_cache_size=0,
    )
    assert "connect_args" not in sqlite_kwargs
    assert "pool_size" not in sqlite_kwargs
    assert "max_overflow" not in sqlite_kwargs


@pytest.mark.asyncio
async def test_close_db_aliased_engine():
    """close_db() disposes primary engine once when read_engine is aliased."""
    mock_engine = AsyncMock()
    with patch.object(db_module, "engine", mock_engine), patch.object(
        db_module, "read_engine", mock_engine
    ):
        await close_db()
        assert mock_engine.dispose.await_count == 1


@pytest.mark.asyncio
async def test_close_db_distinct_engines():
    """close_db() disposes both primary and read engines when distinct."""
    mock_primary = AsyncMock()
    mock_read = AsyncMock()
    with patch.object(db_module, "engine", mock_primary), patch.object(
        db_module, "read_engine", mock_read
    ):
        await close_db()
        assert mock_primary.dispose.await_count == 1
        assert mock_read.dispose.await_count == 1


def test_dashboard_routes_depend_on_get_read_db():
    """Verify analytics and report routes depend on get_read_db and not get_db."""
    # Dashboard router routes
    charts_route = next(r for r in dashboard_router.routes if r.path == "/dashboard/charts")
    portfolio_route = next(r for r in dashboard_router.routes if r.path == "/dashboard/portfolio")
    fairness_route = next(r for r in dashboard_router.routes if r.path == "/dashboard/fairness")
    export_route = next(
        r for r in dashboard_router.routes if r.path == "/dashboard/fairness/export.csv"
    )

    for route in [charts_route, portfolio_route, fairness_route, export_route]:
        dep_calls = [d.call for d in route.dependant.dependencies]
        assert get_read_db in dep_calls, f"Route {route.path} missing get_read_db dependency"
        assert db_module.get_db not in dep_calls, f"Route {route.path} should not depend on get_db"

    # Report router routes
    score_route = next(r for r in report_router.routes if r.path == "/report/score/{score_id}")
    pdf_route = next(r for r in report_router.routes if r.path == "/report/score/{score_id}/pdf")

    for route in [score_route, pdf_route]:
        dep_calls = [d.call for d in route.dependant.dependencies]
        assert get_read_db in dep_calls, f"Route {route.path} missing get_read_db dependency"
        assert db_module.get_db not in dep_calls, f"Route {route.path} should not depend on get_db"
