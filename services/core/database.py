"""Async SQLAlchemy database engine and session management."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from services.core.config import get_settings

settings = get_settings()

_engine_kwargs: dict = {"echo": settings.database_echo}
# SQLite (used by the in-memory test harness and by offline Alembic
# autogenerate) does not accept the connection-pool keyword args.
if not settings.database_url.startswith("sqlite"):
    _engine_kwargs.update(pool_size=5, max_overflow=10, pool_pre_ping=True)

engine = create_async_engine(settings.database_url, **_engine_kwargs)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


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


async def init_db() -> None:
    """Create all tables (development only — use Alembic in production)."""
    from services.core.shared.audit_triggers import install_append_only_triggers

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await install_append_only_triggers(conn)


async def close_db() -> None:
    """Dispose of the engine connection pool."""
    await engine.dispose()
