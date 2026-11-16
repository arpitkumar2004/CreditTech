# Design Document: Cloud-Native Managed Monolith Database & Environment Architecture
**Date:** 2026-11-16  
**Status:** Approved by Architectural Review  
**Authors:** CreditTech Engineering & Architecture Team  
**Scope:** Production Database Strategy, Multi-Environment Isolation, Read-Replica Routing, and Decoupled ML Training  

---

## 1. Intent & Context

CreditTech is preparing for pilot deployment serving real rural borrowers, Bank Sakhis, and partner bank loan officers across pilot clusters (Cluster Alpha in Chandauli and Cluster Beta in Mirzapur). 

As real users start submitting live applications, the engineering team requires an operational architecture that guarantees:
1. **Uninterrupted, High-Availability Underwriting (OLTP):** Zero-downtime serving with latency $<150\text{ ms}$, guarded by PostgreSQL transaction pooling and append-only cryptographic audit logs.
2. **Safe, Multi-Environment Development:** Complete isolation between Local Development (SQLite/Docker), Staging (Cloud PostgreSQL sandbox), and Production (Multi-AZ Managed PostgreSQL), preventing live PII exposure and accidental schema breaks.
3. **Decoupled Analytics & ML Lifecycle:** Analytical dashboard queries and continuous model retraining run against read-replicas/offline extracts without locking primary OLTP tables or stealing CPU/IOPS from live borrower applications.

---

## 2. Goals, Non-Goals, and Anti-Goals

### Goals
- **Environment Parity & Cascading Configuration:** Support environment-specific configs via Pydantic (`.env`, `.env.development`, `.env.staging`, `.env.production`) dynamically evaluated at runtime.
- **Read-Replica Query Routing:** Implement a FastAPI dependency (`get_read_db`) that routes heavy read queries (specifically `services/core/dashboard/router.py`) to a read-replica database if configured, falling back seamlessly to the primary database when running locally or on single-instance PostgreSQL.
- **Zero-Downtime Migration CI Gate:** Provide `scripts/check_migrations.py` running native Alembic checks and AST analysis verifying backward-compatible schema changes (Expand-Contract pattern).
- **Consent-Gated ML Training Data Extractor:** Provide `scripts/extract_gold_dataset.py` that queries the read-replica via the canonical 5-table relational join, strictly filters `consented_for_retraining == True`, verifies 12-month loan maturity ($Y \in \{0, 1\}$), strips prohibited PII, and outputs versioned Parquet feature datasets.
- **PgBouncer Transaction Pooling Compatibility:** Configure `connect_args={"statement_cache_size": 0}` for `asyncpg` when running against PgBouncer in transaction mode.
- **Local Staging Parity via Docker Compose:** Update `docker-compose.yml` with dual profiles: a lightweight dev profile and a PostgreSQL 16 + PgBouncer profile matching production cloud topology.

### Non-Goals
- Migrating to a distributed microservices architecture (CreditTech remains a clean, high-performance modular monolith).
- Setting up external CDC engines (e.g. Debezium / Kafka) at this pilot stage.
- Modifying core loan scoring mathematical models or existing Alembic revisions.

### Anti-Goals
- **Anti-Goal 1 (Direct OLTP ML Retraining):** Running ML training queries directly against the primary write database.
- **Anti-Goal 2 (Destructive DDL):** Permitting non-backward-compatible migrations (e.g. adding `NOT NULL` columns without defaults, or dropping columns) that cause 500 errors during rolling deployments.
- **Anti-Goal 3 (PII in Training Vectors):** Allowing raw borrower names, phones, or Aadhaar hashes to leak into training data extracts.
- **Anti-Goal 4 (Write Operations on Read-Replica):** Directing mutating operations (such as `/monitoring/fairness-audit` which commits audit log records) to `get_read_db`.

---

## 3. Approaches Considered & Selected

Three architectural paths were evaluated:

1. **Approach 1: Cloud-Native Managed Monolith (SELECTED):**
   - Single managed PostgreSQL 16 instance (AWS RDS Aurora / GCP Cloud SQL) with Multi-AZ failover and 1 Read Replica for analytics and dashboard charts.
   - Containerized FastAPI modular monolith on AWS ECS Fargate or GCP Cloud Run with PgBouncer connection pooling.
   - Local development on SQLite or local Docker PostgreSQL; offline retraining script extracts consented gold Parquet files.
   - *Rationale:* Selected by user. Delivers complete regulatory compliance, high availability, and operational simplicity at lowest cloud cost ($\approx \$150 - \$300/\text{mo}$).

2. **Approach 2: Enterprise Decoupled Lakehouse & Microservices (REJECTED):**
   - Independent microservices for underwriting, consent, and ML serving with Debezium CDC streaming to BigQuery/Snowflake.
   - *Trade-off:* High infrastructure cost ($\approx \$1,500+/\text{mo}$) and significant operational overhead premature for pilot scale (50–5,000 borrowers).

3. **Approach 3: Evolutionary Modular Bridge (REJECTED as distinct option; subsumed into Approach 1):**
   - Implementing clean domain interfaces in Approach 1 so transitioning to a separate lakehouse later requires zero core application rewrites.

---

## 4. Detailed Component Design

### 4.1 Multi-Environment Settings Architecture (`services/core/config.py`)
Enhance `Settings` to dynamically load environment variables based on `APP_ENV`:
```python
import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

_env = os.getenv("APP_ENV", "development").lower()

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", f".env.{_env}"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_env: str = "development"  # development | staging | production
    app_debug: bool = False
    
    # Primary Database (Writes & Critical Operational Reads)
    database_url: str = "sqlite+aiosqlite:///./credittech.db"
    database_echo: bool = False
    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_statement_cache_size: int = 0  # 0 disables asyncpg statement cache for PgBouncer
    
    # Optional Read Replica (Analytics / Dashboard Charts)
    database_read_url: str | None = None
    database_read_pool_size: int = 5
    database_read_max_overflow: int = 10
```

### 4.2 Dual-Engine Database Routing (`services/core/database.py`)
- **Primary Engine (`engine`):** Handles all transactional writes and real-time loan underwriting via `get_db()`.
- **Read-Replica Engine (`read_engine`):**
  - If `database_read_url` is configured and different from `database_url`:
    - Checks dialect: applies `pool_size`, `max_overflow`, and `connect_args={"statement_cache_size": 0}` if PostgreSQL.
    - Creates `async_read_session_factory`.
  - If `database_read_url` is `None` (e.g. SQLite local dev or single-instance PostgreSQL):
    - `read_engine = engine`
    - `async_read_session_factory = async_session_factory`
- **Dependencies:**
  ```python
  async def get_db() -> AsyncGenerator[AsyncSession, None]:
      """Primary transactional database session."""
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
      """Read-only database session for analytics and dashboards."""
      async with async_read_session_factory() as session:
          try:
              yield session
          finally:
              await session.close()
  ```
- **Engine Disposal (`close_db`):**
  ```python
  async def close_db() -> None:
      await engine.dispose()
      if read_engine is not engine:
          await read_engine.dispose()
  ```
- **Router Integration:** Update `services/core/dashboard/router.py` (specifically `/dashboard/charts`, `/dashboard/portfolio`, `/dashboard/fairness`, `/dashboard/report/{score_id}`) to use `Depends(get_read_db)`. Note: `/monitoring/fairness-audit` in `monitoring/router.py` writes audit log records, so it strictly stays on `get_db`.
- **Test Fixtures (`tests/conftest.py`):**
  ```python
  app.dependency_overrides[get_db] = override_get_db
  app.dependency_overrides[get_read_db] = override_get_db
  ```

### 4.3 Zero-Downtime Migration & CI Enforcement (`scripts/check_migrations.py`)
A standalone Python check script to be run in local verification and CI:
1. Runs Alembic check via the Python API (`alembic.command.check(alembic_cfg)`) to verify schema sync.
2. Inspects new Alembic migration scripts in `alembic/versions/` (excluding baseline `14323a45982d_initial_schema.py`):
   - Flags `op.add_column` calls where `nullable=False` and `server_default` is missing.
   - Flags `op.drop_column` or `op.drop_table` calls, requiring destructive cleanup to be in an explicit separate PR.
3. Fails with non-zero exit code if violations are detected.

### 4.4 Consent-Gated Gold Dataset Extractor (`scripts/extract_gold_dataset.py`)
Offline extraction pipeline satisfying DPDP Act 2023 §6/§8 and RBI DLG:
1. Connects to `database_read_url` (or primary in dev).
2. Executes the canonical 5-table relational join:
   ```python
   query = (
       select(
           RepaymentRecord.id.label("repayment_id"),
           RepaymentRecord.status.label("repayment_status"),
           RepaymentRecord.disbursed_at,
           FeatureSnapshot.features_json,
           Borrower.gender,
           Borrower.landholding_band,
           Village.name.label("village_name"),
           Village.agro_climatic_zone,
       )
       .join(LoanApplication, RepaymentRecord.loan_application_id == LoanApplication.id)
       .join(Score, LoanApplication.score_id == Score.id)
       .join(FeatureSnapshot, Score.feature_snapshot_id == FeatureSnapshot.id)
       .join(Borrower, LoanApplication.borrower_id == Borrower.id)
       .join(Village, Borrower.village_id == Village.id)
       .where(RepaymentRecord.consented_for_retraining == True)
       .where(RepaymentRecord.disbursed_at <= maturity_cutoff)
   )
   ```
3. Parses `features_json` and validates each feature against `MODEL_FEATURE_NAMES`.
4. Asserts **zero prohibited PII fields** exist in the extract.
5. Computes target label $Y$:
   - $Y = 1$ (Good): `status in ('CURRENT', 'CLOSED')`.
   - $Y = 0$ (Default): `status == 'DPD_90_PLUS'`.
   - Rows with intermediate/transitional DPD (`'DPD_1_30'`, `'DPD_31_60'`, `'DPD_61_90'`) are excluded to prevent maturity noise.
6. Exports compressed versioned Parquet (`data/gold/credit_train_vX.Y.Z.parquet`) via `pyarrow` (with CSV fallback if pyarrow unavailable).
7. Adds `pyarrow>=16.0.0` to `[project.optional-dependencies] ml` in `pyproject.toml`.

### 4.5 Staging / Production Docker Parity (`docker-compose.yml`)
Add support for:
- `db`: PostgreSQL 16 container.
- `pgbouncer`: PgBouncer container fronting the primary database in transaction pooling mode.
- `web`: FastAPI application configured to connect through PgBouncer.

---

## 5. Testing & Verification Plan

1. **Unit Tests for Configuration & Replica Routing:**
   - `tests/unit/test_multi_environment_config.py`: Test `.env` cascading and validation across development, staging, and production presets.
   - `tests/unit/test_db_replica_routing.py`: Test `get_read_db()` fallback to primary when `database_read_url` is None, and proper routing when replica is supplied.
2. **Migration CI Verification:**
   - Execute `python scripts/check_migrations.py` to confirm current schema passes 100%.
3. **Data Extractor Verification:**
   - Execute `python scripts/extract_gold_dataset.py --dry-run` against seeded `credittech.db` to verify consent filtering, zero-PII assertions, and Parquet generation.
4. **Full Regression Test Suite:**
   - Run `pytest` to guarantee all 170+ existing tests continue to pass.
