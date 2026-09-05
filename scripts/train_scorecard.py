"""Train the CreditTech v1 logistic scorecard and register it.

Usage:
    python -m scripts.train_scorecard
        --model-version v1.0.0-logistic
        [--home-credit data/home_credit/application_train.csv]
        [--n-synth 4000]
        [--promote validated]

If --home-credit is not provided or the file is missing, training uses the
synthetic SHG generator alone and records that limitation in the registry.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow "python scripts/train_scorecard.py" from repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ml.evaluation.metrics import demographic_parity
from ml.registry import ModelRegistry
from ml.training.datasets import HomeCreditLoader, SyntheticSHGGenerator
from ml.training.scorecard import ScorecardTrainer


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-version", default="v1.0.0-logistic")
    parser.add_argument("--home-credit", default=None,
                        help="Path to application_train.csv (optional)")
    parser.add_argument("--n-synth", type=int, default=4000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--promote", choices=["candidate", "validated", "active"], default="candidate")
    args = parser.parse_args()

    # 1. Assemble training frame from proxy sources
    import pandas as pd

    synth = SyntheticSHGGenerator(n=args.n_synth, seed=args.seed)
    X_synth, y_synth, sensitive_synth, info_synth = synth.generate()
    print(f"[synthetic] {len(X_synth)} rows, class balance:", y_synth.value_counts(normalize=True).to_dict())

    dataset_info = info_synth
    X, y, sensitive = X_synth, y_synth, sensitive_synth

    if args.home_credit:
        loader = HomeCreditLoader(csv_path=args.home_credit)
        X_hc, y_hc, info_hc = loader.load()
        if info_hc.available:
            print(f"[home_credit] {len(X_hc)} rows, aligned features: {info_hc.transformations}")
            X = pd.concat([X_synth, X_hc], ignore_index=True)
            y = pd.concat([y_synth, y_hc], ignore_index=True)
            # Sensitive attrs undefined for HC rows -> mark as UNKNOWN so parity
            # analysis can filter them out.
            sensitive_extra = pd.DataFrame({
                "gender": ["UNKNOWN"] * len(X_hc),
                "landholding_band": ["UNKNOWN"] * len(X_hc),
            })
            sensitive = pd.concat([sensitive_synth, sensitive_extra], ignore_index=True)
            dataset_info.source += "+kaggle_home_credit_default_risk"
            dataset_info.kind = "proxy"  # mixed
            dataset_info.samples = len(X)
            dataset_info.transformations.append("concat with home_credit after column alignment")
            dataset_info.limitations.append("mixed synthetic+home_credit rows are a development population, not the CreditTech target population")
        else:
            print(f"[home_credit] not available at {loader.csv_path} — synthetic only")

    # 2. Fit
    trainer = ScorecardTrainer(model_version=args.model_version, random_state=args.seed)
    scorecard, report = trainer.fit(X, y)
    print(f"[training] AUC={report.auc:.4f}  Gini={report.gini:.4f}  KS={report.ks:.4f}  Brier={report.brier:.4f}")

    # 3. Fairness (on the validation-equivalent slice — here full X for reporting;
    #    a stricter version would evaluate only on the held-out split).
    proba = [scorecard.predict_probability(row._asdict() if hasattr(row, "_asdict") else row.to_dict())
             for row in X.itertuples(index=False)]
    known_mask = sensitive["gender"] != "UNKNOWN"
    fairness_results: list[dict] = []
    if known_mask.sum() > 0:
        gender_res = demographic_parity(
            [p for p, k in zip(proba, known_mask) if k],
            sensitive.loc[known_mask, "gender"],
            attribute_name="gender",
        )
        band_res = demographic_parity(
            [p for p, k in zip(proba, known_mask) if k],
            sensitive.loc[known_mask, "landholding_band"],
            attribute_name="landholding_band",
        )
        fairness_results = [gender_res.to_dict(), band_res.to_dict()]
        print("[fairness] gender max_disparity:", round(gender_res.max_disparity, 4))
        print("[fairness] landholding_band max_disparity:", round(band_res.max_disparity, 4))

    # 4. Register
    registry = ModelRegistry()
    rec = registry.register(
        scorecard=scorecard,
        training_report=report,
        dataset_info=dataset_info,
        fairness_results=fairness_results,
    )
    print(f"[registry] registered {rec.model_version} status={rec.promotion_status}")
    if args.promote != "candidate":
        # candidate -> validated -> active
        if args.promote == "active":
            registry.promote(rec.model_version, "validated")
            registry.promote(rec.model_version, "active")
        else:
            registry.promote(rec.model_version, args.promote)
        print(f"[registry] promoted to {args.promote}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
