# Design Document: CreditTech Pre-Pilot Stabilization & Modular Monolith Hardening

- **Date:** 2026-11-14
- **Author:** Antigravity / Engineering Team
- **Topic:** Codebase Audit, Restructuring, and Pre-Pilot Stabilization
- **Status:** Finalized (Pending User Approval)

---

## 1. Intent & Context

CreditTech is an AI-driven digital lending decision-support platform designed for rural financial inclusion in India (supporting farmers, SHGs, and micro-enterprises). The project has completed MVP development through Phases P0–P6 (FastAPI backend, multi-rail ingestion, SHAP explainability, officer decisioning, fairness auditing, and React frontend).

As the project transitions toward Phase 7 (Pilot Readiness & Live Institution Onboarding), the codebase carries technical debt accumulated during rapid phase deliverables:
1. Untracked duplicated directories (`credittech/` mirror snapshot) and obsolete root prototype scripts (`src/`, `generate_dataset.py`).
2. A brittle ML-to-API serving contract in `services/core/scoring/service.py` where differing artifact serialization formats break the scoring API with runtime `AttributeError`.
3. A flat test directory of 39 files mixing fast unit tests, integration suites, and slow stress/load harnesses (`test_p6_load.py`), slowing down feedback cycles.
4. Monolithic model definitions (545-line `services/core/shared/models.py`) and redundant frontend build outputs committed to git.

This design establishes a clean, maintainable modular monolith architecture for long-term operations without adding premature microservice complexity.

---

## 2. Goals, Non-Goals, and Anti-Goals

### Goals
1. **Repository Hygiene & Dead Code Removal:**
   - Remove untracked duplicate `credittech/` directory and remove the empty tracked root `package-lock.json`.
   - Relocate historical project artifacts and research papers to `docs/reports/` and `docs/presentations/` rather than keeping them scattered in the repository root.
   - Untrack `credittech.db` via `git rm --cached credittech.db` (preserving local dev file while adding `*.db` to `.gitignore`).
   - Move active data generation and diagram generation scripts from loose root files into structured `scripts/` directories (`scripts/data/`, `scripts/figures/`).
   - Clean redundant build artifacts in `apps/borrower-app` (`.d.ts`, `.js`, `.tsbuildinfo` build outputs committed to VCS).
2. **Standardized ML Serving Contract (Bug Fix):**
   - Formalize an explicit `BaseScorecard` interface/protocol in `ml/training/base.py` requiring `.predict_probability(features: dict) -> float` and `.calibrate_score(prob: float) -> tuple[float, int]`.
   - Update `_load_scorecard_from_registry()` in `services/core/scoring/service.py` with a robust model loader `ml.training.loader:load_scorecard_model` that correctly instantiates the appropriate scorecard class (`WoEScorecard`, `LogisticScorecard`, `LogisticBaselineScorecard`, `MonotonicGBMScorecard`, etc.) based on artifact metadata and structure.
   - Re-align the active model in `ml/registry/store/registry.json` with the canonical champion model `v1.1.0-woe-scorecard` (as specified in documentation and verified by tests), while ensuring all candidate/baseline models also deserialize cleanly.
3. **Structured Test Pyramid:**
   - Organize `tests/` into three distinct tiers:
     - `tests/unit/`: fast isolated tests for services, ML feature math, schemas, and utils (< 10 seconds total).
     - `tests/integration/`: database transactions, API route endpoints with in-memory SQLite/Postgres.
     - `tests/performance/`: slow load tests (`test_p6_load.py`), disaster recovery simulations (`test_p6_dr.py`), and stress testing.
   - Configure pytest marks (`@pytest.mark.slow`, `@pytest.mark.load`) in `pyproject.toml` so normal `pytest` runs unit + integration tests rapidly by default.
4. **Domain-Driven Shared Models:**
   - Transform `services/core/shared/models.py` into a clean package `services/core/shared/models/` to prevent SQLAlchemy circular import dependencies while structuring models by business boundary:
     - `core.py`: `Borrower`, `Village`
     - `consent.py`: `ConsentRecord`, `ConsentAuditLog`
     - `ingestion.py`: `FeatureSnapshot`, `DataPull`
     - `scoring.py`: `Score`, `ReasonCode`
     - `decisioning.py`: `LoanApplication`, `OfficerDecision`, `DecisionAuditLog`, `RepaymentRecord`
     - `grievance.py`: `GrievanceRecord`, `GrievanceAuditLog`, `FairnessAuditLog`
   - Preserve 100% backward compatibility by re-exporting all models from `services.core.shared.models.__init__.py` so existing queries, services, and Alembic migrations remain completely untouched.

### Non-Goals
- Migrating from FastAPI to microservices or distributed event brokers (Kafka/RabbitMQ).
- Altering existing database schemas, tables, or creating new Alembic migrations.
- Modifying frontend React application business logic or UI components.
- Retraining or altering machine learning model weights, coefficients, or validation thresholds.

### Anti-Goals
- Breaking any existing import statements (`from services.core.shared.models import Borrower` must work transparently).
- Deleting academic reports, research artifacts, or presentation decks needed for project records (relocated to `docs/`).
- Introducing breaking changes to CI/CD workflows in `.github/workflows/ci.yml`.

---

## 3. Constraints

- **Python Runtime:** Python 3.10 and 3.11 compatibility.
- **Database Engine:** Must maintain parity across SQLite (`sqlite+aiosqlite`) for tests and PostgreSQL (`postgresql+asyncpg`) for staging/production.
- **Test Integrity:** All 120+ existing test cases must pass after restructuring.
- **Zero Production Downtime / No Breaking DB Changes:** Alembic head must remain compatible with current database schemas.

---

## 4. Approaches Considered

### Approach 1: Pre-Pilot Stabilization & Monolith Hardening *(Selected)*
Maintain the modular monolith in a single repository while cleaning dead prototypes, formalizing the ML serving interface, categorizing test layers, and organizing models by domain.
- *Pros:* High cohesion, zero microservice deployment overhead, immediate developer ergonomics, eliminates runtime scoring bugs.
- *Cons:* Requires meticulous re-exporting to prevent import regressions.
- *Decision:* Selected by team as the ideal operational fit for pre-pilot status.

### Approach 2: Full Multi-Package Monorepo (Poetry/Hatch Workspaces)
Extract `ml/` as an installable wheel `credittech-ml` and `services/core` as `credittech-api`.
- *Pros:* Strict architectural boundaries.
- *Cons:* High maintenance friction, editable install overhead during development, premature for a unified engineering team.

### Approach 3: Minimal Hotfix
Only patch `services/core/scoring/service.py` to handle the dictionary artifact.
- *Pros:* Fastest immediate fix.
- *Cons:* Leaves behind technical debt, slow test runs, and high hurdle for new maintainers.

---

## 5. Detailed Technical Specifications

### Area 1: Repository Hygiene & Directory Structure
1. **Archive/Remove Untracked Duplicate Directory:**
   - Remove untracked `credittech/` directory (which contains redundant duplicates of `src/`, `data/`, `figures/`).
2. **Relocate Root Scripts:**
   - Move root prototype scripts into `scripts/`:
     - `generate_dataset.py`, `validate_dataset.py`, `src/generate_dataset.py`, `src/validate_dataset.py` $\rightarrow$ consolidate into `scripts/data/generate_dataset.py` and `scripts/data/validate_dataset.py`.
     - `src/render_all_diagrams.py`, `src/render_er_diagram.py`, `src/generate_figures.py` $\rightarrow$ `scripts/figures/`.
     - `simulate_pilot.py` $\rightarrow$ `scripts/simulate_pilot.py`.
   - Remove obsolete untracked `src/` directory once contents are cleanly housed in `scripts/`.
3. **Relocate Documentation & Presentation Artifacts:**
   - Move tracked root report deliverables to `docs/reports/`:
     - `CreditTech_Final_Project_Report (1) (1).pdf`
     - `CreditTech_Alternative_Credit_Scoring_Report.html`
     - `CreditTech Rural Dataset and Modeling Blueprint.md`
     - `Credittechplanningcontext.md`
     - `alternative_credit_scoring_research.md`, `interview.md`, `report_text.txt`
   - Move `ppt-midsem/` directory to `docs/presentations/ppt-midsem/`.
4. **Root Clean-up & Git Hygiene:**
   - Remove empty tracked root `package-lock.json`.
   - Untrack `credittech.db` with `git rm --cached credittech.db`.
   - Update `.gitignore` to explicitly ignore `*.db`, `*.sqlite3`, and `*.tsbuildinfo`.
   - In `apps/borrower-app/`, remove tracked build outputs (`vite.config.js`, `vite.config.d.ts`, `vitest.config.js`, `vitest.config.d.ts`, `tsconfig.tsbuildinfo`, `tsconfig.node.tsbuildinfo`), keeping strictly `vite.config.ts` and `vitest.config.ts`.

### Area 2: Standardized ML Model Serving Contract
1. **Define `BaseScorecard` Protocol in `ml/training/base.py`:**
   ```python
   from typing import Protocol, Any, runtime_checkable

   @runtime_checkable
   class BaseScorecard(Protocol):
       model_version: str
       feature_version: str
       def predict_probability(self, features: dict[str, Any]) -> float: ...
       def calibrate_score(self, prob_repayment: float) -> tuple[float, int]: ...
   ```
2. **Unified Artifact Loader in `ml/training/loader.py`:**
   Implement `load_scorecard_model(artifact_path: Path, model_type: str | None = None) -> BaseScorecard`:
   - Inspects artifact metadata and file format.
   - If JSON with `woe_transformer` $\rightarrow$ `WoEScorecard.from_dict()`.
   - If JSON with `weights` and `intercept` $\rightarrow$ `LogisticScorecard.from_dict()`.
   - If pickle with `CalibratedClassifierCV` or `LogisticBaselineScorecard` dict $\rightarrow$ `LogisticBaselineScorecard.from_artifact()`.
   - If pickle for GBDT $\rightarrow$ `MonotonicGBMScorecard.from_artifact()`.
   - If pickle for RF $\rightarrow$ `RFScorecard.from_artifact()`.
   - If pickle for Stacking $\rightarrow$ `StackingScorecard.from_artifact()`.
   - Returns a validated `BaseScorecard` instance.
3. **Re-align Active Model in Registry:**
   - Ensure `v1.1.0-woe-scorecard` is set to `"active"` in `ml/registry/store/registry.json`, matching project documentation and test assertions in `test_ml_promotion_pipeline.py`.
4. **Refactor `services/core/scoring/service.py`:**
   - Replace brittle ad-hoc open logic in `_load_scorecard_from_registry()` with `load_scorecard_model()`.
   - Eliminates the `AttributeError: 'dict' object has no attribute 'predict_probability'`.

### Area 3: Test Suite Reorganization
1. **Directory Layout:**
   ```text
   tests/
   ├── conftest.py
   ├── unit/
   │   ├── test_features.py
   │   ├── test_woe.py
   │   ├── test_explainability.py
   │   ├── test_security.py
   │   ├── test_consent.py
   │   ├── test_scoring.py
   │   └── ...
   ├── integration/
   │   ├── test_cuj_workflows.py
   │   ├── test_p4_e2e_decision.py
   │   ├── test_p5_e2e.py
   │   ├── test_scoring_e2e_registry.py
   │   └── ...
   └── performance/
       ├── test_p6_load.py
       └── test_p6_dr.py
   ```
2. **Pytest Configuration (`pyproject.toml`):**
   - Register custom markers:
     - `slow`: Long-running evaluation or retraining tests.
     - `load`: Heavy load-testing harnesses.
   - Set default test execution: `addopts = "-v --tb=short -m 'not load'"` so standard test commands complete within seconds.

### Area 4: Shared Models Modularization
1. **Package Refactor:**
   Transform `services/core/shared/models.py` into a package `services/core/shared/models/`:
   - `core.py`: `Borrower`, `Village`
   - `consent.py`: `ConsentRecord`, `ConsentAuditLog`
   - `ingestion.py`: `FeatureSnapshot`, `DataPull`
   - `scoring.py`: `Score`, `ReasonCode`
   - `decisioning.py`: `LoanApplication`, `OfficerDecision`, `DecisionAuditLog`, `RepaymentRecord`
   - `grievance.py`: `GrievanceRecord`, `GrievanceAuditLog`, `FairnessAuditLog`
   - `__init__.py`: Imports and re-exports all entities so `from services.core.shared.models import ...` continues to function 100% seamlessly.

---

## 6. What's Left to the Builder

The builder is empowered to make tactical implementation decisions regarding:
- Exact subfolder placement of individual unit test files when categorizing from the 39 flat files.
- The specific naming and helper organization in `scripts/data/` vs `scripts/figures/`.
- Minor typing adjustments in `BaseScorecard` to satisfy `mypy` strict checks.

---

## 7. Verification & Success Criteria

1. **Test Suite Execution:**
   - Running `.venv\Scripts\pytest` executes all unit and integration tests with **100% pass rate** (fixing the 2 currently failing scoring tests).
   - Running `.venv\Scripts\pytest tests/performance/test_p6_load.py` independently passes the load harness.
2. **Clean Status:**
   - `git status` shows zero unneeded untracked duplicates (`credittech/` eliminated).
   - Root directory contains only essential project files (`README.md`, `pyproject.toml`, `alembic.ini`, `Dockerfile`, `docker-compose.yml`, license, etc.).
3. **Application Smoke Test:**
   - Running `uvicorn services.core.main:app` starts without import errors and passes the `/health` and `/ready` probes.
