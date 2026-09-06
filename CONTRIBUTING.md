# Contributing to CreditTech

Thank you for contributing to CreditTech! This project is an AI-driven digital lending decision-support platform designed to expand credit access for farmers, Self-Help Groups (SHGs), and rural micro-enterprises across India.

To maintain regulatory rigor, data security, model fairness, and engineering excellence, please review the guidelines below before submitting changes.

---

## 🏗️ Architecture Overview

The codebase is organized into three primary layers:

```
CreditTech/
├── services/core/        # FastAPI modular monolith (Backend API)
│   ├── consent/          # Append-only consent ledger & cryptographic hash chaining
│   ├── ingestion/        # Parallel 4-rail connector orchestrator (AA, Satellite, Bureau, SHG)
│   ├── scoring/          # Scorecard inference & registry lookup
│   ├── explainability/   # Exact Shapley values & bilingual (EN/HI) reason codes
│   ├── decisioning/      # Loan officer decisioning & override audit logging
│   ├── handoff/          # Regulated Entity (RE) export generation
│   ├── grievance/        # Dispute intake & 48-hour SLA appeal clock
│   ├── monitoring/       # FairnessAuditor & live parity monitor
│   ├── admin/            # Promotion gate & model registry management
│   ├── ops/              # Readiness probes, smoke tests, & DR backup/restore
│   └── shared/           # DB session, security middleware, structlog correlation
├── ml/                   # Machine Learning pipeline & artifacts
│   ├── features/         # WoE/IV transformation engine & spatial feature engineering
│   ├── training/         # Monotonic GBDT & WoE scorecard trainers
│   ├── evaluation/       # Spatial GroupKFold, calibration, & fairness metrics
│   └── registry/         # Versioned model artifacts & immutable JSON metadata
├── apps/borrower-app/    # Unified React + Vite frontend (Bank Sakhi & Loan Officer portal)
├── infra/                # Terraform infrastructure modules (staging/production)
├── config/               # Fairness thresholds manifest & configuration
└── tests/                # Unit, integration, fairness gate, and load tests
```

---

## 🚀 Getting Started

### Prerequisites

- **Python:** 3.10 or higher
- **Node.js:** 18 LTS or higher (`npm` 9+)
- **Git:** 2.30+

### 1. Python Backend Setup

```bash
# Clone the repository
git clone https://github.com/arpitkumar2004/CreditTech.git
cd CreditTech

# Set up virtual environment
python -m venv .venv
.venv\Scripts\activate       # Windows PowerShell / CMD
# source .venv/bin/activate  # Linux / macOS

# Install dependencies
pip install -e ".[dev]"

# Configure environment variables
cp .env.example .env
```

### 2. Frontend Setup

```bash
cd apps/borrower-app
npm install
```

### 3. Running Locally

**Terminal 1 (Backend API):**
```bash
# Runs at http://127.0.0.1:8000 (OpenAPI docs at http://127.0.0.1:8000/docs)
.venv\Scripts\python -m uvicorn services.core.main:app --reload --host 127.0.0.1 --port 8000
```

**Terminal 2 (Frontend App):**
```bash
# Runs at http://localhost:5173
cd apps/borrower-app
npm run dev
```

---

## 🧪 Testing & Verification

All automated tests must pass before opening a pull request.

```bash
# Run the complete test suite (120+ tests)
.venv\Scripts\pytest -v

# Run with test coverage
.venv\Scripts\pytest --cov=services --cov=ml

# Run specific test suites
.venv\Scripts\pytest tests/test_p6_security.py -v
.venv\Scripts\pytest tests/test_p6_fairness_gate.py -v
.venv\Scripts\pytest tests/test_p6_load.py -v

# Verify frontend TypeScript compilation & production build
cd apps/borrower-app
npm run build
```

---

## 🔒 Security & Data Privacy Principles

When contributing to CreditTech, adhere strictly to our safety baseline:

1. **Zero Raw PII Storage:** Direct identifiers (Aadhaar, PAN) must never be stored in plain text. Always compute irreversible HMAC hashes (`Aadhaar reference hash`) or encrypt via AES-256-GCM.
2. **Strict Schema Separation:** Borrower PII columns are strictly isolated from feature vectors and scoring data to prevent accidental leakage.
3. **Structured Log Scrubbing:** Never log borrower names, phone numbers, raw identifiers, or plaintext tokens. Use `structlog` with automated masking.
4. **Append-Only Auditing:** Loan officer decisions, grievances, and consent logs are append-only. Never add `UPDATE` or `DELETE` triggers or endpoints to these tables.
5. **Fail-Safe Startup Validation:** Critical secrets (`SECRET_KEY`, `PII_ENCRYPTION_KEY`) must not be left as default placeholders in non-development environments.

---

## 📊 Model Governance & Fairness Gate

Any new or updated ML model must adhere to the 4-phase production ML strategy:

1. **Spatial GroupKFold Validation:** Spatial cross-validation on `village_id` clusters to prevent geographical data leakage.
2. **Interpretability by Design:** Credit scorecards must use monotonic binning, Weight of Evidence (WoE), and exact Shapley feature attribution.
3. **Fairness Gate Compliance:** Models are evaluated across protected attributes (Gender, Social Category, Landholding Band, Agro-climatic Zone). A model **cannot** be promoted to production if it violates the thresholds defined in `config/fairness_thresholds.json`.

---

## 📝 Commit Conventions

We follow Conventional Commits:

- `feat:` A new feature (e.g., `feat(ingestion): add satellite ndvi anomaly alert`)
- `fix:` A bug fix (e.g., `fix(scoring): handle null values in landholding binning`)
- `docs:` Documentation improvements (e.g., `docs(readme): update system architecture diagram`)
- `test:` Adding or updating tests (e.g., `test(security): add request-id correlation test`)
- `refactor:` Code refactoring without behavioral change
- `perf:` Performance optimization

---

## 🤝 Pull Request Checklist

Before submitting your PR, ensure:

- [ ] All backend tests pass (`.venv\Scripts\pytest`).
- [ ] Frontend builds without errors (`npm run build`).
- [ ] New features or endpoints include automated tests.
- [ ] No secrets, credentials, or API keys are committed.
- [ ] If ML models were updated, fairness gate evaluation was executed.
- [ ] Commit messages follow conventional commit guidelines.
