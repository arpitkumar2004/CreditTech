"""CreditTech application configuration via pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────
    app_name: str = "CreditTech"
    app_env: str = "development"
    app_debug: bool = False
    app_version: str = "0.1.0"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # ── Database ─────────────────────────────────────────────
    database_url: str = "sqlite+aiosqlite:///./credittech.db"
    database_echo: bool = False

    # ── Security ─────────────────────────────────────────────
    secret_key: str = "CHANGE_ME_TO_A_RANDOM_64_CHAR_STRING"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    # ── PII Encryption ───────────────────────────────────────
    pii_encryption_key: str = "CHANGE_ME_TO_A_32_BYTE_BASE64_KEY"

    # ── Consent ──────────────────────────────────────────────
    consent_max_duration_days: int = 365
    consent_genesis_salt: str = "credittech-genesis-v1"

    # ── External Connectors ──────────────────────────────────
    aa_base_url: str = "http://localhost:8001/mock/aa"
    aa_client_id: str = "mock_client_id"
    aa_client_secret: str = "mock_client_secret"
    # Phase 0 external item E2. When False, AA connector is mock-validated only —
    # real-credential validation is deferred to the Phase 6 entry gate.
    aa_credentials_available: bool = False

    geospatial_base_url: str = "http://localhost:8001/mock/geospatial"
    geospatial_api_key: str = "mock_api_key"

    bureau_base_url: str = "http://localhost:8001/mock/bureau"
    bureau_api_key: str = "mock_api_key"

    # ── Logging ──────────────────────────────────────────────
    log_level: str = "INFO"
    log_format: str = "json"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
