"""Unit tests for multi-environment cascading configuration and PgBouncer database settings."""

import importlib

import pytest
from pydantic import ValidationError

import services.core.config
from services.core.config import Settings, get_settings


def test_default_settings_development_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings loads default development values when APP_ENV is unset or 'development'."""
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("DATABASE_READ_URL", raising=False)
    monkeypatch.delenv("DATABASE_POOL_SIZE", raising=False)
    monkeypatch.delenv("DATABASE_MAX_OVERFLOW", raising=False)
    monkeypatch.delenv("DATABASE_STATEMENT_CACHE_SIZE", raising=False)
    monkeypatch.delenv("DATABASE_READ_POOL_SIZE", raising=False)
    monkeypatch.delenv("DATABASE_READ_MAX_OVERFLOW", raising=False)

    settings = Settings()
    assert settings.app_env == "development"
    assert settings.is_development is True
    assert settings.is_production is False
    assert settings.database_read_url is None
    assert settings.database_pool_size == 5
    assert settings.database_max_overflow == 10
    assert settings.database_statement_cache_size == 0
    assert settings.database_read_pool_size == 5
    assert settings.database_read_max_overflow == 10


def test_database_configuration_fields_and_types() -> None:
    """Verify new database configuration fields are present and typed correctly."""
    settings = Settings(
        database_read_url="postgresql+asyncpg://readonly:secret@localhost:5432/credittech_read",
        database_pool_size=15,
        database_max_overflow=20,
        database_statement_cache_size=0,
        database_read_pool_size=8,
        database_read_max_overflow=12,
    )
    assert settings.database_read_url == "postgresql+asyncpg://readonly:secret@localhost:5432/credittech_read"
    assert isinstance(settings.database_read_url, str)
    assert settings.database_pool_size == 15
    assert isinstance(settings.database_pool_size, int)
    assert settings.database_max_overflow == 20
    assert isinstance(settings.database_max_overflow, int)
    assert settings.database_statement_cache_size == 0
    assert isinstance(settings.database_statement_cache_size, int)
    assert settings.database_read_pool_size == 8
    assert isinstance(settings.database_read_pool_size, int)
    assert settings.database_read_max_overflow == 12
    assert isinstance(settings.database_read_max_overflow, int)


def test_database_configuration_validation_errors() -> None:
    """Integer database configuration fields reject invalid types."""
    with pytest.raises(ValidationError):
        Settings(database_pool_size="not_an_int")

    with pytest.raises(ValidationError):
        Settings(database_statement_cache_size="invalid")


def test_dynamic_env_file_resolution(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify dynamic cascading env_file tuple based on APP_ENV."""
    # Staging env
    monkeypatch.setenv("APP_ENV", "staging")
    mod = importlib.reload(services.core.config)
    assert mod._env == "staging"
    env_file = mod.Settings.model_config.get("env_file")
    assert env_file == (".env", ".env.staging")

    # Production env with uppercase check
    monkeypatch.setenv("APP_ENV", "PRODUCTION")
    mod = importlib.reload(services.core.config)
    assert mod._env == "production"
    env_file = mod.Settings.model_config.get("env_file")
    assert env_file == (".env", ".env.production")

    # Unset default
    monkeypatch.delenv("APP_ENV", raising=False)
    mod = importlib.reload(services.core.config)
    assert mod._env == "development"
    env_file = mod.Settings.model_config.get("env_file")
    assert env_file == (".env", ".env.development")


def test_cascading_env_files_loading(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify values cascade correctly: .env provides baseline, .env.{env} overrides."""
    env_base = tmp_path / ".env"
    env_prod = tmp_path / ".env.production"

    env_base.write_text(
        "APP_NAME=CreditTech Base\n"
        "DATABASE_POOL_SIZE=8\n"
        "DATABASE_READ_POOL_SIZE=6\n",
        encoding="utf-8",
    )
    env_prod.write_text(
        "APP_NAME=CreditTech Production\n"
        "DATABASE_READ_URL=postgresql+asyncpg://reader:secret@prod-ro:5432/credittech\n"
        "DATABASE_READ_POOL_SIZE=16\n",
        encoding="utf-8",
    )

    # Change working directory so relative .env files are found
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("APP_ENV", "production")
    mod = importlib.reload(services.core.config)

    settings = mod.Settings()
    assert settings.app_name == "CreditTech Production"
    assert settings.database_pool_size == 8
    assert settings.database_read_pool_size == 16
    assert settings.database_read_url == "postgresql+asyncpg://reader:secret@prod-ro:5432/credittech"


def test_get_settings_caching() -> None:
    """get_settings returns cached singleton and re-caches after cache_clear."""
    get_settings.cache_clear()
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
    get_settings.cache_clear()
