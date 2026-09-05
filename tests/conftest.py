"""Test configuration and fixtures for pytest."""

import asyncio
import os
from collections.abc import AsyncGenerator, Generator

os.environ.setdefault("DISABLE_RATE_LIMIT", "1")

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from services.core.config import Settings, get_settings
from services.core.database import Base, get_db
from services.core.main import app

# Use SQLite in-memory database for fast testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Settings override for testing."""
    settings = get_settings()
    settings.app_env = "testing"
    settings.database_url = TEST_DATABASE_URL
    settings.secret_key = "test_secret_key_for_jwt_auth_testing"
    settings.pii_encryption_key = "dGVzdF9waWlfZW5jcnlwdGlvbl9rZXlfMzJieXRl"
    return settings


@pytest.fixture(autouse=True)
async def setup_test_db() -> AsyncGenerator[None, None]:
    """Create tables before tests, drop them after."""
    from services.core.shared.audit_triggers import install_append_only_triggers

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await install_append_only_triggers(conn)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional database session for tests."""
    async with TestingSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an HTTP client pointing to the FastAPI app with DB overridden."""
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
