# Pre-Pilot Stabilization & Modular Monolith Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stabilize the CreditTech modular monolith for Phase 7 pilot readiness by establishing a polymorphic ML model serving contract, modularizing the shared ORM models, restructuring the test suite into fast-feedback pyramids, and cleaning repository legacy debt.

**Architecture:** Maintain the FastAPI modular monolith and ML registry within a unified repository. Standardize model inference behind a `BaseScorecard` protocol and loader in `ml/training/`, modularize `services/core/shared/models/` by business domains with backward-compatible facade re-exports, organize `tests/` into `unit/`, `integration/`, and `performance/`, and relocate historical presentation/report deliverables to `docs/`.

**Tech Stack:** Python 3.10/3.11, FastAPI, SQLAlchemy 2.0 (AsyncIO), Alembic, Pytest, Scikit-learn, XGBoost, LightGBM, React/Vite.

**Spec:** [`docs/superpowers/specs/2026-11-14-pre-pilot-stabilization-design.md`](file:///d:/CreditTech/docs/superpowers/specs/2026-11-14-pre-pilot-stabilization-design.md)

## Global Constraints

- Python runtime compatibility: Python 3.10 and 3.11.
- Database parity: Must maintain full compatibility across SQLite (`sqlite+aiosqlite`) and PostgreSQL (`postgresql+asyncpg`).
- Schema stability: Zero changes to database tables, column definitions, constraints, or Alembic revision heads.
- Import backward compatibility: All imports using `from services.core.shared.models import <Model>` must continue to work seamlessly.
- Test integrity: All existing 120+ backend tests must pass with 100% success rate.
- CI preservation: Linting (`ruff check .`), type checks (`mypy services ml`), and migrations (`alembic upgrade head`) must succeed.

## Review Focus

1. **Active Champion Model Mismatch:** Ensure `ml/registry/store/registry.json` sets `v1.1.0-woe-scorecard` to `"active"` so promotion tests pass, while the loader correctly handles pickled baseline/challenger models.
2. **SQLAlchemy Circular Import Trap:** Ensure `services/core/shared/models/` modules import the shared `Base` without circular references across `Borrower`, `Score`, `FeatureSnapshot`, and `OfficerDecision`.
3. **Alembic Metadata Detection:** Ensure `services.core.shared.models.__init__.py` imports all 12 entities so Alembic does not detect phantom table drops or schema drifts.
4. **Pytest Marker Pollution:** Ensure `addopts = "-v --tb=short -m 'not load'"` prevents slow load tests from executing during regular test loops while allowing explicit execution via `-m load`.
5. **Git Tracking of Untracked DB & Reports:** Ensure `credittech.db` is untracked using `git rm --cached` without deleting local developer copies, and reports are safely relocated under `docs/reports/` using `git mv`.

---

### Task 1: ML Model Serving Contract & Scoring Bug Fix

**Files:**
- Create: `ml/training/base.py`
- Create: `ml/training/loader.py`
- Modify: `services/core/scoring/service.py:20-75`
- Modify: `ml/registry/store/registry.json`
- Test: `tests/unit/test_model_loader.py`
- Test: `tests/test_scoring.py`

**Interfaces:**
- Produces: `BaseScorecard` protocol in `ml/training/base.py`
  ```python
  class BaseScorecard(Protocol):
      model_version: str
      feature_version: str
      def predict_probability(self, features: dict[str, Any]) -> float: ...
      def calibrate_score(self, prob_repayment: float) -> tuple[float, int]: ...
  ```
- Produces: `load_scorecard_model(artifact_path: Path, model_type: str | None = None) -> BaseScorecard` in `ml/training/loader.py`
- Consumes: `ml/registry/registry.py:ModelRegistry`

- [ ] **Step 1: Write the failing unit test for `load_scorecard_model`**

Create `tests/unit/test_model_loader.py` testing that all models currently in `ml/registry/store/` can be loaded and implement `predict_probability` and `calibrate_score`:
```python
from pathlib import Path
import pytest
from ml.registry import ModelRegistry
from ml.training.base import BaseScorecard
from ml.training.loader import load_scorecard_model

def test_load_all_registered_models():
    registry = ModelRegistry()
    models = registry.list_models()
    assert len(models) >= 5
    for record in models:
        artifact = registry.artifact_path(record.model_version)
        assert artifact is not None and artifact.exists()
        scorecard = load_scorecard_model(artifact, model_type=record.model_type)
        assert isinstance(scorecard, BaseScorecard)
        prob = scorecard.predict_probability({})
        assert 0.0 <= prob <= 1.0
        score_100, score_900 = scorecard.calibrate_score(prob)
        assert 0.0 <= score_100 <= 100.0
        assert 300 <= score_900 <= 900
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\pytest tests/unit/test_model_loader.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'ml.training.base'`

- [ ] **Step 3: Define `BaseScorecard` Protocol in `ml/training/base.py`**

Create `ml/training/base.py` defining the runtime-checkable protocol with typing annotations for `model_version`, `feature_version`, `predict_probability`, and `calibrate_score`.

- [ ] **Step 4: Implement `load_scorecard_model` in `ml/training/loader.py`**

Implement `load_scorecard_model(artifact_path: str | Path, model_type: str | None = None) -> BaseScorecard`:
1. Inspect file suffix and header (magic bytes `\x80` for pickle vs JSON).
2. For JSON:
   - If `"woe_transformer"` in payload $\rightarrow$ `WoEScorecard.from_dict(data)`.
   - If `"weights"` and `"intercept"` $\rightarrow$ `LogisticScorecard.from_dict(data)`.
3. For pickle:
   - Load with `pickle.load(f)`.
   - If loaded object is a `dict` with `'classifier'` and `'features'` $\rightarrow$ instantiate `LogisticBaselineScorecard.from_artifact(artifact_path)` or construct `LogisticBaselineScorecard`.
   - If loaded object is `MonotonicGBMScorecard`, `RFScorecard`, or `StackingScorecard`, return directly.

- [ ] **Step 5: Re-align `ml/registry/store/registry.json` active status**

Ensure `v1.1.0-woe-scorecard` has `"promotion_status": "active"` and `v1.1.0-logistic-baseline` has `"promotion_status": "validated"`, matching the canonical champion configuration.

- [ ] **Step 6: Refactor `services/core/scoring/service.py` to use `load_scorecard_model`**

Update `_load_scorecard_from_registry()` in `services/core/scoring/service.py` to delegate artifact instantiation to `load_scorecard_model(artifact, record.model_type)`:
```python
def _load_scorecard_from_registry(model_version: str | None) -> tuple[BaseScorecard, dict | None]:
    registry = ModelRegistry()
    record = registry.get(model_version) if model_version else registry.get_active()
    if record is None:
        return LogisticScorecard(), None
    artifact = registry.artifact_path(record.model_version)
    if artifact is None or not artifact.exists():
        return LogisticScorecard(), None
    scorecard = load_scorecard_model(artifact, model_type=record.model_type)
    ...
```

- [ ] **Step 7: Run test suite to verify scoring tests pass**

Run: `.venv\Scripts\pytest tests/unit/test_model_loader.py tests/test_scoring.py -v`
Expected: PASS (all 7 items in `test_scoring.py` pass with 0 failures).

- [ ] **Step 8: Commit**

```bash
git add ml/training/base.py ml/training/loader.py services/core/scoring/service.py ml/registry/store/registry.json tests/unit/test_model_loader.py
git commit -m "fix(scoring): standardize BaseScorecard protocol and artifact loader"
```

---

### Task 2: Shared Models Modularization & Facade

**Files:**
- Create: `services/core/shared/models/__init__.py`
- Create: `services/core/shared/models/core.py`
- Create: `services/core/shared/models/consent.py`
- Create: `services/core/shared/models/ingestion.py`
- Create: `services/core/shared/models/scoring.py`
- Create: `services/core/shared/models/decisioning.py`
- Create: `services/core/shared/models/grievance.py`
- Delete: `services/core/shared/models.py` (replaced by package)
- Test: `tests/test_data_governance.py`
- Test: `tests/test_consent.py`

**Interfaces:**
- Produces: Modular domain models grouped by subpackage, re-exported via `services/core/shared/models/__init__.py`:
  - `Borrower`, `Village` from `core.py`
  - `ConsentRecord`, `ConsentAuditLog` from `consent.py`
  - `FeatureSnapshot`, `DataPull` from `ingestion.py`
  - `Score`, `ReasonCode` from `scoring.py`
  - `LoanApplication`, `OfficerDecision`, `DecisionAuditLog`, `RepaymentRecord` from `decisioning.py`
  - `GrievanceRecord`, `GrievanceAuditLog`, `FairnessAuditLog` from `grievance.py`
- Consumes: `services/core/database.py:Base`

- [ ] **Step 1: Write verification test for model re-exports**

Create temporary test in `tests/unit/test_models_reexport.py`:
```python
def test_all_models_reexported():
    from services.core.shared import models
    expected_models = [
        "Borrower", "Village", "ConsentRecord", "ConsentAuditLog",
        "FeatureSnapshot", "DataPull", "Score", "ReasonCode",
        "LoanApplication", "OfficerDecision", "DecisionAuditLog",
        "RepaymentRecord", "GrievanceRecord", "GrievanceAuditLog",
        "FairnessAuditLog"
    ]
    for name in expected_models:
        assert hasattr(models, name), f"Missing model {name} in services.core.shared.models"
```

- [ ] **Step 2: Create `services/core/shared/models/` package and split domain classes**

1. Move `Borrower`, `Village` into `services/core/shared/models/core.py`.
2. Move `ConsentRecord`, `ConsentAuditLog` into `services/core/shared/models/consent.py`.
3. Move `FeatureSnapshot`, `DataPull` into `services/core/shared/models/ingestion.py`.
4. Move `Score`, `ReasonCode` into `services/core/shared/models/scoring.py`.
5. Move `LoanApplication`, `OfficerDecision`, `DecisionAuditLog`, `RepaymentRecord` into `services/core/shared/models/decisioning.py`.
6. Move `GrievanceRecord`, `GrievanceAuditLog`, `FairnessAuditLog` into `services/core/shared/models/grievance.py`.
7. In `services/core/shared/models/__init__.py`, import all models and export `__all__`.
8. Remove the old single file `services/core/shared/models.py`.

- [ ] **Step 3: Run model verification and schema tests**

Run: `.venv\Scripts\pytest tests/unit/test_models_reexport.py tests/test_consent.py tests/test_data_governance.py -v`
Expected: PASS

- [ ] **Step 4: Verify Alembic detects no schema changes**

Run: `.venv\Scripts\alembic check`
Expected: Target database is up to date (no ungenerated migrations or dropped tables).

- [ ] **Step 5: Commit**

```bash
git add services/core/shared/models/ tests/unit/test_models_reexport.py
git commit -m "refactor(models): modularize shared ORM models into domain modules"
```

---

### Task 3: Test Suite Reorganization & Pytest Configuration

**Files:**
- Create directory: `tests/unit/`
- Create directory: `tests/integration/`
- Create directory: `tests/performance/`
- Modify: `pyproject.toml:82-86`
- Move existing test files from `tests/` into subdirectories

**Interfaces:**
- Produces: Tiered test structure where default `pytest` runs unit + integration in < 15 seconds.
- Produces: Pytest markers `@pytest.mark.load` and `@pytest.mark.slow`.

- [ ] **Step 1: Configure markers and default addopts in `pyproject.toml`**

Update `pyproject.toml`:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "-v --tb=short -m 'not load'"
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "load: marks tests as heavy load harnesses (deselect with '-m \"not load\"')",
]
```

- [ ] **Step 2: Relocate performance and load tests**

Move:
- `tests/test_p6_load.py` $\rightarrow$ `tests/performance/test_p6_load.py`
- `tests/test_p6_dr.py` $\rightarrow$ `tests/performance/test_p6_dr.py`
Add `@pytest.mark.load` to `tests/performance/test_p6_load.py`.

- [ ] **Step 3: Relocate integration and end-to-end tests**

Move to `tests/integration/`:
- `test_cuj_workflows.py`
- `test_p4_e2e_decision.py`
- `test_p5_e2e.py`
- `test_scoring_e2e_registry.py`
- `test_scoring_shadow.py`
- `test_simulation.py`
- `test_p6_smoke.py`
- `test_p6_security.py`
- `test_p6_promotion.py`
- `test_p6_fairness_gate.py`
- `test_p6_append_only.py`
- `test_p6_pdf.py`

- [ ] **Step 4: Relocate unit tests**

Move remaining domain tests to `tests/unit/`:
- `test_consent.py`, `test_data_governance.py`, `test_early_adopter_db.py`, `test_explainability.py`
- `test_features.py`, `test_features_geospatial.py`, `test_handoff.py`, `test_ingestion.py`
- `test_monitoring.py`, `test_officer_decision.py`, `test_persona_authorization.py`, `test_scoring.py`
- `test_woe.py`, `test_benchmark_loaders.py`, `test_dashboard_charts.py`, `test_p5_dashboard.py`
- `test_p5_fairness.py`, `test_p5_grievance.py`, `test_ml_*.py`

- [ ] **Step 5: Run default test suite to verify fast execution**

Run: `.venv\Scripts\pytest`
Expected: PASS (all unit and integration tests run and pass, load test excluded).

- [ ] **Step 6: Run load test explicitly to verify load suite integrity**

Run: `.venv\Scripts\pytest tests/performance/test_p6_load.py -m load`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add tests/ pyproject.toml
git commit -m "test: reorganize test suite into unit, integration, and performance tiers"
```

---

### Task 4: Repository Hygiene, Dead Code Removal & Asset Relocation

**Files:**
- Move: `CreditTech_Final_Project_Report (1) (1).pdf` $\rightarrow$ `docs/reports/`
- Move: `CreditTech_Alternative_Credit_Scoring_Report.html` $\rightarrow$ `docs/reports/`
- Move: `CreditTech Rural Dataset and Modeling Blueprint.md` $\rightarrow$ `docs/reports/`
- Move: `Credittechplanningcontext.md` $\rightarrow$ `docs/reports/`
- Move: `alternative_credit_scoring_research.md` $\rightarrow$ `docs/reports/`
- Move: `interview.md`, `report_text.txt` $\rightarrow$ `docs/reports/`
- Move: `ppt-midsem/` $\rightarrow$ `docs/presentations/ppt-midsem/`
- Move root scripts: `generate_dataset.py`, `validate_dataset.py` $\rightarrow$ `scripts/data/`
- Move: `simulate_pilot.py` $\rightarrow$ `scripts/simulate_pilot.py`
- Untrack & Ignore: `credittech.db`
- Delete: untracked `credittech/` and untracked root `src/`
- Delete: empty tracked root `package-lock.json`
- Modify: `.gitignore`
- Clean `apps/borrower-app/`: remove tracked build outputs (`vite.config.js`, `vite.config.d.ts`, `vitest.config.js`, `vitest.config.d.ts`, `tsconfig.tsbuildinfo`, `tsconfig.node.tsbuildinfo`)

- [ ] **Step 1: Move documentation, reports, and presentation assets**

Create directories `docs/reports/` and `docs/presentations/` and move the files using `git mv`:
```bash
git mv "CreditTech_Final_Project_Report (1) (1).pdf" docs/reports/
git mv CreditTech_Alternative_Credit_Scoring_Report.html docs/reports/
git mv "CreditTech Rural Dataset and Modeling Blueprint.md" docs/reports/
git mv Credittechplanningcontext.md docs/reports/
git mv alternative_credit_scoring_research.md docs/reports/
git mv interview.md docs/reports/
git mv report_text.txt docs/reports/
git mv ppt-midsem docs/presentations/ppt-midsem
```

- [ ] **Step 2: Relocate scripts to `scripts/` directory**

Create `scripts/data/` and relocate `generate_dataset.py`, `validate_dataset.py`, and `simulate_pilot.py`.
Remove the untracked duplicate directories `credittech/` and `src/`.

- [ ] **Step 3: Untrack `credittech.db` and update `.gitignore`**

1. Untrack local database from git index:
   `git rm --cached credittech.db`
2. Update `.gitignore` adding:
   ```gitignore
   *.db
   *.sqlite3
   *.tsbuildinfo
   credittech/
   ```

- [ ] **Step 4: Remove root `package-lock.json` and clean `apps/borrower-app/` generated outputs**

1. Remove root `package-lock.json`:
   `git rm package-lock.json`
2. Remove generated build artifacts in `apps/borrower-app/`:
   ```bash
   git rm apps/borrower-app/vite.config.js apps/borrower-app/vite.config.d.ts apps/borrower-app/vitest.config.js apps/borrower-app/vitest.config.d.ts apps/borrower-app/tsconfig.tsbuildinfo apps/borrower-app/tsconfig.node.tsbuildinfo
   ```

- [ ] **Step 5: Verify repository status and run full regression checks**

1. Check git cleanliness:
   `git status` (shows clean working tree with only desired changes).
2. Run ruff linter:
   `.venv\Scripts\ruff check .`
3. Run full pytest suite:
   `.venv\Scripts\pytest`
4. Test application startup:
   `.venv\Scripts\python -c "from services.core.main import app; print('App imported successfully')"`

- [ ] **Step 6: Commit**

```bash
git add .
git commit -m "chore: clean repository clutter, relocate historical reports, and gitignore dev database"
```

