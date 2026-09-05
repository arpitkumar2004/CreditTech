# Phase 3 — ML System Documentation

**Status:** v1 baseline delivered • proxy/synthetic training data • production
predictive validity NOT claimed.
**Last updated:** 2026-09-03

---

## 1. Scope of what P3 delivers

* Deterministic feature engineering pipeline over the 5 Cs framework
* Reproducible training-data assembly (synthetic + optional Home Credit)
* Weighted logistic scorecard v1 with calibration
* Exact-Shapley explanations (linear-model closed form; numerically identical
  to `shap.LinearExplainer` — we avoid the runtime dep)
* Bilingual reason-code rendering for every feature the model uses
* Fairness evaluation on proxy dimensions (`gender`, `landholding_band`)
* File-based model registry with promotion status
* Scoring service that loads the active registered model at request time

Explicitly **deferred** to post-pilot (per roadmap §9): XGBoost/LightGBM
candidate, fairness gate on real repayment outcomes, DVC dataset/model
versioning, drift monitoring against production ground truth.

---

## 2. Where the code lives

```
ml/
  features/
    schema.py          # authoritative allow-list of model features
    pipeline.py        # build_feature_vector() + tag_season()
  training/
    datasets.py        # SyntheticSHGGenerator, HomeCreditLoader
    scorecard.py       # LogisticScorecard (runtime) + ScorecardTrainer
  evaluation/
    metrics.py         # AUC/Gini/Brier + demographic_parity
    explain.py         # ScorecardSHAPExplainer (exact Shapley for linear)
  registry/
    registry.py        # ModelRegistry + ModelRecord + promotion
    store/             # <version>/scorecard.json + training_report.json

scripts/
  train_scorecard.py   # train -> evaluate -> fairness -> register [-> promote]

services/core/
  scoring/service.py   # loads registry-active model; falls back to defaults
  scoring/schemas.py   # ScoreResponse now includes feature_version
  explainability/service.py  # runtime bilingual reason-code templates
```

---

## 3. Training data provenance (P3.2)

### 3.1 Synthetic SHG / farmer data (primary)

Generator: `ml.training.datasets.SyntheticSHGGenerator`. Deterministic with
`seed`. Ground-truth labels are drawn from a Bernoulli over a hand-authored
logit intended to encode 5-Cs intuition (higher SHG repayment, attendance,
asset score, NDVI, etc. -> higher P(repay)). Label noise `N(0, 0.5)` prevents
perfect separability. **AUC/Gini computed on this data validate the pipeline;
they are not claims of real-world predictive validity.**

### 3.2 Home Credit Default Risk (optional development anchor)

Adapter: `ml.training.datasets.HomeCreditLoader`. Loads
`data/home_credit/application_train.csv` if present. Only three columns are
mapped into the CreditTech schema (`AMT_INCOME_TOTAL/12 -> monthly_avg_credit_inflow`,
`AMT_CREDIT * 0.01 -> shg_cumulative_savings`, `-DAYS_EMPLOYED/365.25 -> shg_membership_years`).
The mapping is documented in code as a **development-only alignment** — the
Home Credit population is not the CreditTech target population.

If the file is absent, `load()` returns `available=False` and the training
pipeline runs synthetic-only. We never fabricate rows.

Every dataset carries a `DatasetInfo(source, kind, samples, feature_version,
schema_hash, transformations, limitations)` which the registry persists as the
training-data provenance record.

---

## 4. Runtime model (P3.3)

`ml.training.scorecard.LogisticScorecard` — linear model over the P0 features.
Two initialisation modes:

* `LogisticScorecard()` — hand-authored 5-Cs weights (from Jonnalagadda & Babu
  2026), used only when no registered model exists.
* `LogisticScorecard.from_artifact(path)` — reads a `{intercept, weights,
  model_version, feature_version}` JSON dumped by the trainer/registry.

`ScorecardTrainer` fits `sklearn.LogisticRegression(penalty='l2',
class_weight='balanced')`. Features are standardised inside the trainer for
optimisation and coefficients are converted back to raw-unit space before
export so the runtime scorecard accepts un-scaled feature values without a
scaler dependency.

Score calibration is unchanged from earlier phases:
* 0–100: `round(P(repay) * 100, 1)`
* 300–900: standard scorecard `offset + factor * ln(odds)` (PDO=20, base 50:1
  at 600), clamped to [300, 900]

Confidence band width is a function of the number of source rails that
contributed to the snapshot (5 / 8 / 12 / 18 points either side for 4 / 3 / 2
/ 1 rails). This is a coarse proxy for uncertainty; see the ADR on scoring
uncertainty for the fuller picture.

---

## 5. Explainability (P3.5)

`ml.evaluation.explain.ScorecardSHAPExplainer` computes exact Shapley
contributions `phi_i = w_i * (x_i - E[x_i])`. Reference `E[x_i]` is taken from
the trained model's per-feature training-set mean (recorded in
`training_report.json → feature_means`) when available, and falls back to a
hand-tuned domain prior otherwise.

`services.core.explainability.service.ExplainabilityService` maps each
feature/direction pair to a bilingual template. The runtime templates and the
`docs/phase0/shap_reason_code_templates.md` library are the authoritative,
governance-ratifiable sources.

Rendering guarantees:
* deterministic ordering (`|shap|` desc, then feature name asc)
* unknown features silently ignored (cannot crash on stray data)
* non-coercible values skipped, not zero-imputed
* no PII / no protected attributes / no monitored-only fields ever appear

---

## 6. Fairness (P3.4)

`ml.evaluation.metrics.demographic_parity` reports approval-rate disparity per
group (reference = largest group). It **does not** invent a tolerance. The
returned record includes `status: "pending_governance"` until governance
ratifies a threshold; the training script writes this alongside the metric so
model reviewers see the pending state on every registration.

Group attributes come from a separate `sensitive` DataFrame — they are never
inspected by the feature pipeline or by the model. `SyntheticSHGGenerator`
emits `gender` and `landholding_band` for this purpose only. On the mixed
synth + Home Credit training frame, non-synthetic rows are marked `UNKNOWN`
and dropped from parity computation.

Known limitations (recorded in every fairness result):
* proxy/synthetic data — sample-size and generator-bias effects limit
  interpretability
* no ratified fairness tolerance yet (pending governance)
* small groups (`n < 30`) flagged as low-confidence

---

## 7. Model registry (P3.6)

File-based JSON registry at `ml/registry/store/registry.json`.
Each record: `model_version, feature_version, model_type, training_dataset
(DatasetInfo dict), training_dataset_hash, trained_at, metrics, fairness,
artifact_path, artifact_hash, promotion_status, limitations, code_version,
notes`.

Promotion state machine: `candidate → validated → active → retired`. Promoting
a new model to `active` automatically retires the previously active model
(guarantees single-active invariant). Skip transitions raise `ValueError` —
`candidate → active` requires explicit `validated` step.

Training success does NOT auto-promote. `scripts/train_scorecard.py` defaults
to `--promote candidate`; validation and activation are separate audited calls.

---

## 8. Scoring integration (P3.7)

`ScoringService(db, model_version=...)`:
* If `model_version` is provided, loads that specific registered model.
* Else loads the registry's active model.
* If no registry entry exists, uses the built-in default `LogisticScorecard()`
  (backward-compatible with pre-P3 behaviour so unit tests still work without
  a trained artifact).

API response now includes both `model_version` and `feature_version` so
downstream systems (RE handoff, decision UI, audit) can pin decisions to a
specific model+feature combination.

---

## 9. How to reproduce

```bash
# Full pipeline: synthetic only, promote to active
python -m scripts.train_scorecard --model-version v1.0.0-logistic \
  --n-synth 3000 --promote active

# With Home Credit added
python -m scripts.train_scorecard --model-version v1.0.1-logistic \
  --home-credit data/home_credit/application_train.csv --n-synth 3000
```

Verify:
```bash
python -m pytest tests/test_features.py tests/test_ml_training.py \
                 tests/test_explainability.py tests/test_scoring_e2e_registry.py -q
```

---

## 10. Limitations & risks

* **No real repayment data.** All metrics are computed on proxy/synthetic
  labels. Do not represent AUC/Gini as production predictive validity.
* **Home Credit alignment is weak.** Only three columns are mapped; using the
  concatenated frame trains a model whose feature-importance interpretation
  is muddled. This mode is a development option, not the default.
* **Fairness tolerance is unratified.** The registry records disparity numbers
  but no gate; a model can be promoted despite a large disparity if a human
  reviewer accepts it. This is expected — the ratification decision is a
  governance action, not a code change.
* **Runtime uses closed-form linear Shapley, not `shap` package.** The values
  are exact for the logistic model class we ship. If we move to XGBoost
  post-pilot, this must be replaced with `shap.TreeExplainer` and the
  templates re-reviewed.
* **Registry lock/concurrency.** Registry writes are not process-safe; the
  training script is designed to be run by a single operator. A DB-backed
  registry is a post-pilot upgrade.
