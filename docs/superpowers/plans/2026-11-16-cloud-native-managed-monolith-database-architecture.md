# Cloud-Native Managed Monolith Database Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a cloud-native managed monolith database and environment architecture for CreditTech, enabling safe zero-downtime serving for live pilot users, dynamic multi-environment configuration, read-replica query routing for analytics, automated migration safety checks, and consent-gated ML training dataset extraction.

**Architecture:** The application remains a modular monolith FastAPI service. Configuration dynamically cascades across environments (`.env`, `.env.{app_env}`). Database access is split into primary transactional engine (`get_db`) and analytics read-replica engine (`get_read_db`, aliased to primary when replica is unset). PostgreSQL connection pooling is hardened with PgBouncer compatibility (`statement_cache_size=0`). CI enforces zero-downtime Expand-Contract migrations, and offline ML data extraction strictly respects statutory DPDP consent and loan maturity windows.

**Tech Stack:** Python 3.10+, FastAPI, SQLAlchemy (asyncio + asyncpg / aiosqlite), Alembic, Pydantic Settings, PyArrow, Docker Compose, PgBouncer.

**Spec:** [docs/superpowers/specs/2026-11-16-cloud-native-managed-monolith-database-architecture-design.md](file:///d:/CreditTech/docs/superpowers/specs/2026-11-16-cloud-native-managed-monolith-database-architecture-design.md)

## Global Constraints
- Must maintain 100% backward compatibility for all existing routes and tests.
- Direct PII attributes (`name`, `phone`, `aadhaar`) must never enter training data extracts.
- Database access must work seamlessly across SQLite (local dev/test harness) and PostgreSQL (staging/production).
- Mutating endpoints (`/monitoring/fairness-audit`) must strictly use `get_db`; only read-only dashboard endpoints may use `get_read_db`.
- All Python dependencies must be managed via `pyproject.toml`.

## Review Focus
- **Failure Mode 1 (Missing Read Replica in Dev):** When `DATABASE_READ_URL` is omitted, `get_read_db()` must cleanly fall back to the primary engine without raising connection errors.
- **Failure Mode 2 (PgBouncer Prepared Statement Collisions):** In PostgreSQL staging/production, `statement_cache_size=0` must be passed to `asyncpg` to avoid transaction-pool cache errors.
- **Failure Mode 3 (Test Fixture Override Blindspots):** `tests/conftest.py` must override both `get_db` and `get_read_db` so dashboard tests do not leak into unseeded local databases.
- **Failure Mode 4 (DPDP Consent Leak in Extractor):** Borrowers who have not consented for model retraining (`consented_for_retraining == False`) or revoked consent must be strictly excluded from gold datasets.
- **Failure Mode 5 (Premature Loan Labeling / Maturity Bias):** Loans disbursed within the last 12 months must be excluded from ground-truth training default labels ($Y \in \{0, 1\}$).

---

### Task 1: Multi-Environment Cascading Settings & PgBouncer-Ready Configuration

**Files:**
- Modify: `services/core/config.py`
- Test: `tests/unit/test_multi_environment_config.py`

**Steps:**
- [ ] Write unit tests in `tests/unit/test_multi_environment_config.py` verifying:
  - Settings loads default development values when `APP_ENV` is unset or `development`.
  - Settings cascades environment-specific files (`.env`, `.env.{app_env}`).
  - New database configuration fields (`database_read_url`, `database_pool_size`, `database_max_overflow`, `database_statement_cache_size`) are present and validate correctly.
- [ ] Run test: `.venv\Scripts\pytest tests/unit/test_multi_environment_config.py` and confirm it fails (fields missing).
- [ ] Implement changes in `services/core/config.py`:
  - Dynamically resolve `_env = os.getenv("APP_ENV", "development").lower()`.
  - Configure `SettingsConfigDict(env_file=(".env", f".env.{_env}"), extra="ignore")`.
  - Add `database_read_url: str | None = None`.
  - Add `database_pool_size: int = 5`, `database_max_overflow: int = 10`, `database_statement_cache_size: int = 0`.
  - Add `database_read_pool_size: int = 5`, `database_read_max_overflow: int = 10`.
- [ ] Run test: `.venv\Scripts\pytest tests/unit/test_multi_environment_config.py` and confirm it passes.
- [ ] Commit: `git commit -m "feat(config): add multi-environment cascading settings and read replica configs"`

---

### Task 2: Dual-Engine Database Routing (`get_read_db`) & Router Integration

**Files:**
- Modify: `services/core/database.py`
- Modify: `services/core/dashboard/router.py`
- Modify: `tests/conftest.py`
- Test: `tests/unit/test_db_replica_routing.py`

**Steps:**
- [ ] Write unit tests in `tests/unit/test_db_replica_routing.py` verifying:
  - `get_read_db` yields a valid `AsyncSession`.
  - When `database_read_url` is `None`, `read_engine` aliases directly to `engine`.
  - When `database_read_url` is configured (SQLite or PostgreSQL), a dedicated `read_engine` is instantiated.
  - `close_db()` disposes both engines properly.
  - Endpoints in `services/core/dashboard/router.py` function properly when injected with `get_read_db`.
- [ ] Run test: `.venv\Scripts\pytest tests/unit/test_db_replica_routing.py` and confirm it fails.
- [ ] Modify `services/core/database.py`:
  - Support `connect_args={"statement_cache_size": settings.database_statement_cache_size}` for asyncpg when `database_statement_cache_size == 0`.
  - If `settings.database_read_url` is set and not equal to `settings.database_url`:
    - Create `read_engine` using the same dialect-safe connection pool kwargs.
    - Create `async_read_session_factory`.
  - Else:
    - `read_engine = engine`
    - `async_read_session_factory = async_session_factory`
  - Implement `async def get_read_db() -> AsyncGenerator[AsyncSession, None]:`
  - Update `close_db()` to dispose both `engine` and `read_engine` (if distinct).
- [ ] Modify `services/core/dashboard/router.py`:
  - Import `get_read_db` from `services.core.database`.
  - Update `/dashboard/charts`, `/dashboard/portfolio`, `/dashboard/fairness`, and `/dashboard/report/{score_id}` to use `Depends(get_read_db)`.
- [ ] Modify `tests/conftest.py`:
  - Import `get_read_db` and register: `app.dependency_overrides[get_read_db] = override_get_db`.
- [ ] Run tests:
  - `.venv\Scripts\pytest tests/unit/test_db_replica_routing.py`
  - `.venv\Scripts\pytest tests/unit/test_dashboard_charts.py tests/unit/test_p5_dashboard.py`
  - Confirm all pass.
- [ ] Commit: `git commit -m "feat(database): implement get_read_db dependency and wire dashboard analytics routes"`

---

### Task 3: Zero-Downtime Migration CI Gate (`scripts/check_migrations.py`)

**Files:**
- Create: `scripts/check_migrations.py`
- Test: `tests/unit/test_migration_checks.py`

**Steps:**
- [ ] Write unit tests in `tests/unit/test_migration_checks.py` verifying:
  - Check passes when database schema matches Alembic head.
  - Safety check passes on existing baseline revision `14323a45982d`.
  - Safety check detects and flags AST violations:
    - `op.add_column` with `nullable=False` and no `server_default`.
    - `op.drop_column` or `op.drop_table`.
- [ ] Run test: `.venv\Scripts\pytest tests/unit/test_migration_checks.py` and confirm it fails.
- [ ] Implement `scripts/check_migrations.py`:
  - Run `alembic.command.check(alembic_cfg)` to verify schema synchronization.
  - Inspect all revisions in `alembic/versions/` (excluding baseline) using `ast.parse` for unsafe DDL patterns.
  - Output clean error messages and exit with code 1 if violations are found, 0 if clean.
  - Provide `--check-schema-only` and `--check-safety-only` CLI flags.
- [ ] Run tests:
  - `.venv\Scripts\pytest tests/unit/test_migration_checks.py`
  - `.venv\Scripts\python scripts/check_migrations.py`
  - Confirm all pass.
- [ ] Commit: `git commit -m "feat(ci): add check_migrations script to enforce Expand-Contract zero-downtime DDL"`

---

### Task 4: Consent-Gated Gold Dataset Extractor & Parquet Support

**Files:**
- Modify: `pyproject.toml`
- Create: `scripts/extract_gold_dataset.py`
- Test: `tests/unit/test_gold_dataset_extractor.py`

**Steps:**
- [ ] Update `pyproject.toml`:
  - Add `"pyarrow>=16.0.0"` under `[project.optional-dependencies] ml`.
- [ ] Write unit tests in `tests/unit/test_gold_dataset_extractor.py` verifying:
  - Extractor joins `RepaymentRecord -> LoanApplication -> Score -> FeatureSnapshot + Borrower + Village`.
  - Only rows with `consented_for_retraining == True` are extracted.
  - Disbursal date $>12$ months maturity window is respected.
  - Target labeling $Y \in \{0, 1\}$ ($Y=1$ for `CURRENT`/`CLOSED`, $Y=0$ for `DPD_90_PLUS`, transitional DPD excluded).
  - Assertion error is raised if any field in `PROHIBITED_FIELDS` is present in exported feature columns.
  - Exports valid Parquet (or CSV fallback).
- [ ] Run test: `.venv\Scripts\pytest tests/unit/test_gold_dataset_extractor.py` and confirm it fails.
- [ ] Implement `scripts/extract_gold_dataset.py`:
  - CLI arguments: `--output-dir`, `--maturity-months` (default 12), `--format` (parquet or csv), `--dry-run`.
  - Connects to database via `async_session_factory` (or read-replica).
  - Executes canonical 5-table query.
  - Maps `features_json` into flattened columns matching `MODEL_FEATURE_NAMES`.
  - Saves file with generation metadata (timestamp, row count, positive rate).
- [ ] Run test: `.venv\Scripts\pytest tests/unit/test_gold_dataset_extractor.py` and confirm it passes.
- [ ] Test CLI run: `.venv\Scripts\python scripts/extract_gold_dataset.py --dry-run` against seeded `credittech.db`.
- [ ] Commit: `git commit -m "feat(ml): implement DPDP consent-gated gold training dataset extractor"`

---

### Task 5: Staging & Production Parity Docker Compose & Environment Templates

**Files:**
- Modify: `docker-compose.yml`
- Create: `config/pgbouncer/pgbouncer.ini`
- Create: `config/pgbouncer/userlist.txt`
- Create: `.env.example`
- Create: `.env.development.example`
- Create: `.env.production.example`

**Steps:**
- [ ] Create `config/pgbouncer/pgbouncer.ini`:
  - Set `pool_mode = transaction`.
  - Set `max_client_conn = 100`, `default_pool_size = 20`.
- [ ] Create `config/pgbouncer/userlist.txt` with dev/staging credential hashes.
- [ ] Modify `docker-compose.yml`:
  - Upgrade Postgres image to `postgres:16-alpine`.
  - Add `pgbouncer` service fronting the database on port 6432.
  - Configure `web` service to connect via `pgbouncer`.
- [ ] Create `.env.example`, `.env.development.example`, and `.env.production.example` documenting all configuration keys.
- [ ] Run full regression suite:
  - `.venv\Scripts\pytest` (all 170+ unit and integration tests).
  - `.venv\Scripts\python scripts/check_migrations.py`
  - `.venv\Scripts\python -c "from services.core.main import app; print('App OK')"`
- [ ] Commit: `git commit -m "feat(infra): update docker-compose with PostgreSQL 16, PgBouncer, and environment templates"`
