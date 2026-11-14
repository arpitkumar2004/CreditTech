"""P3.2/P3.3 tests — datasets, trainer, evaluation, and end-to-end registry."""

import math
from pathlib import Path

import pytest

from ml.evaluation.metrics import demographic_parity, evaluate_predictions
from ml.registry import ModelRegistry
from ml.training.datasets import HomeCreditLoader, SyntheticSHGGenerator
from ml.training.scorecard import LogisticScorecard, ScorecardTrainer


def test_synthetic_generator_is_deterministic():
    a_X, a_y, a_s, a_info = SyntheticSHGGenerator(n=200, seed=7).generate()
    b_X, b_y, b_s, b_info = SyntheticSHGGenerator(n=200, seed=7).generate()
    assert a_X.equals(b_X)
    assert (a_y == b_y).all()
    assert a_info.schema_hash == b_info.schema_hash
    assert a_info.kind == "synthetic"
    assert a_info.samples == 200


def test_home_credit_loader_missing_file_is_graceful():
    loader = HomeCreditLoader(csv_path="does/not/exist.csv")
    X, y, info = loader.load()
    assert info.available is False
    assert info.samples == 0
    assert len(X) == 0
    assert len(y) == 0


def test_trainer_fits_and_reports_metrics():
    X, y, _, _ = SyntheticSHGGenerator(n=1500, seed=11).generate()
    trainer = ScorecardTrainer(model_version="v-test-001", random_state=11)
    scorecard, report = trainer.fit(X, y)
    assert isinstance(scorecard, LogisticScorecard)
    # AUC is above chance on synthetic ground truth
    assert not math.isnan(report.auc)
    assert report.auc > 0.7, f"AUC={report.auc} too low on synthetic — check trainer"
    assert 0.0 <= report.brier <= 1.0
    assert set(scorecard.weights.keys()) == set(report.weights.keys())
    assert report.n_train + report.n_val == 1500


def test_prediction_after_training_returns_valid_probability():
    X, y, _, _ = SyntheticSHGGenerator(n=800, seed=3).generate()
    scorecard, _ = ScorecardTrainer(model_version="v-test-002", random_state=3).fit(X, y)
    row = X.iloc[0].to_dict()
    p = scorecard.predict_probability(row)
    assert 0.0 <= p <= 1.0
    s100, s900 = scorecard.calibrate_score(p)
    assert 0.0 <= s100 <= 100.0
    assert 300 <= s900 <= 900


def test_scorecard_artifact_roundtrip(tmp_path: Path):
    sc = LogisticScorecard(model_version="v-test-003")
    p = sc.save_artifact(tmp_path / "sc.json")
    reloaded = LogisticScorecard.from_artifact(p)
    assert reloaded.model_version == "v-test-003"
    assert reloaded.intercept == sc.intercept
    assert reloaded.weights == sc.weights


def test_demographic_parity_reports_disparity_and_pending_governance():
    # All group A approved (prob=0.9), all group B rejected (prob=0.1)
    y_prob = [0.9] * 40 + [0.1] * 40
    groups = (["A"] * 40) + (["B"] * 40)
    res = demographic_parity(y_prob, groups, threshold=0.5, attribute_name="gender")
    assert res.groups["A"]["approval_rate"] == 1.0
    assert res.groups["B"]["approval_rate"] == 0.0
    assert res.max_disparity == pytest.approx(1.0)
    assert res.ratified_tolerance is None
    assert res.to_dict()["status"] == "pending_governance"


def test_evaluate_predictions_basic():
    y_true = [0, 0, 1, 1, 0, 1]
    y_prob = [0.1, 0.2, 0.8, 0.7, 0.3, 0.9]
    m = evaluate_predictions(y_true, y_prob)
    assert m["auc"] == 1.0
    assert m["gini"] == 1.0
    assert 0.0 <= m["brier"] <= 1.0


def test_registry_register_and_promote(tmp_path: Path):
    X, y, sensitive, info = SyntheticSHGGenerator(n=600, seed=1).generate()
    scorecard, report = ScorecardTrainer(model_version="v-reg-001", random_state=1).fit(X, y)

    reg = ModelRegistry(store=tmp_path)
    rec = reg.register(scorecard=scorecard, training_report=report, dataset_info=info)
    assert rec.promotion_status == "candidate"
    assert reg.get_active() is None

    reg.promote("v-reg-001", "validated")
    reg.promote("v-reg-001", "active")
    active = reg.get_active()
    assert active is not None
    assert active.model_version == "v-reg-001"

    # A second model, promoted to active, should retire the first.
    scorecard2, report2 = ScorecardTrainer(model_version="v-reg-002", random_state=2).fit(X, y)
    reg.register(scorecard=scorecard2, training_report=report2, dataset_info=info)
    reg.promote("v-reg-002", "validated")
    reg.promote("v-reg-002", "active")
    assert reg.get_active().model_version == "v-reg-002"
    assert reg.get("v-reg-001").promotion_status == "retired"


def test_registry_rejects_illegal_transition(tmp_path: Path):
    X, y, _, info = SyntheticSHGGenerator(n=300, seed=1).generate()
    scorecard, report = ScorecardTrainer(model_version="v-reg-003", random_state=1).fit(X, y)
    reg = ModelRegistry(store=tmp_path)
    reg.register(scorecard=scorecard, training_report=report, dataset_info=info)
    with pytest.raises(ValueError):
        reg.promote("v-reg-003", "active")  # must go through validated first
