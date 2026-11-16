"""Async SQLAlchemy database engine and session management."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from services.core.config import Settings, get_settings


def _build_engine_kwargs(
    url: str,
    *,
    echo: bool = False,
    pool_size: int = 5,
    max_overflow: int = 10,
    statement_cache_size: int = 0,
) -> dict:
    """Build engine connection arguments adapting for SQLite vs PostgreSQL/asyncpg."""
    kwargs: dict = {"echo": echo}
    # SQLite (used by tests / local dev) does not support connection pool args or PgBouncer statement_cache_size.
    if not url.startswith("sqlite"):
        kwargs.update(
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,
        )
        if "postgresql" in url or "asyncpg" in url:
            kwargs["connect_args"] = {"statement_cache_size": statement_cache_size}
    return kwargs


def create_engines(
    cfg: Settings | None = None,
) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession], AsyncEngine, async_sessionmaker[AsyncSession]]:
    """Initialize primary and read-replica database engines and session factories."""
    if cfg is None:
        cfg = get_settings()

    primary_kwargs = _build_engine_kwargs(
        cfg.database_url,
        echo=cfg.database_echo,
        pool_size=cfg.database_pool_size,
        max_overflow=cfg.database_max_overflow,
        statement_cache_size=cfg.database_statement_cache_size,
    )
    p_engine = create_async_engine(cfg.database_url, **primary_kwargs)
    p_factory = async_sessionmaker(
        p_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    if cfg.database_read_url and cfg.database_read_url != cfg.database_url:
        read_kwargs = _build_engine_kwargs(
            cfg.database_read_url,
            echo=cfg.database_echo,
            pool_size=cfg.database_read_pool_size,
            max_overflow=cfg.database_read_max_overflow,
            statement_cache_size=cfg.database_statement_cache_size,
        )
        r_engine = create_async_engine(cfg.database_read_url, **read_kwargs)
        r_factory = async_sessionmaker(
            r_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    else:
        r_engine = p_engine
        r_factory = p_factory

    return p_engine, p_factory, r_engine, r_factory


settings = get_settings()

engine, async_session_factory, read_engine, async_read_session_factory = create_engines(settings)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""

    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_read_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session for read-only / analytics queries."""
    async with async_read_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Create all tables (development only — use Alembic in production)."""
    from services.core.shared.audit_triggers import install_append_only_triggers

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await install_append_only_triggers(conn)


async def close_db() -> None:
    """Dispose of the engine connection pool(s)."""
    await engine.dispose()
    if read_engine is not engine:
        await read_engine.dispose()
