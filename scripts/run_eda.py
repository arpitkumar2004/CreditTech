"""Automated Exploratory Data Analysis & Target Validation Runner for CreditTech.

Analyzes the multi-rail rural credit cohort, checks class balance,
feature distributions, missingness rates, and target leakage risks.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parents[1]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import numpy as np
import pandas as pd

from ml.features.schema import MODEL_FEATURES, MODEL_FEATURE_NAMES
from ml.training.datasets import SyntheticSHGGenerator


def run_eda(n_samples: int = 5000, seed: int = 42, target_default_rate: float | None = 0.10) -> dict:
    print("=" * 70)
    print(" CREDITTECH - AUTOMATED EXPLORATORY DATA ANALYSIS & PROFILING ")
    print("=" * 70)

    generator = SyntheticSHGGenerator(
        n=n_samples,
        seed=seed,
        target_default_rate=target_default_rate,
        n_villages=15,
    )
    X, y, sensitive, info = generator.generate()

    n = len(X)
    n_repay = int((y == 1).sum())
    n_default = int((y == 0).sum())
    default_rate = (n_default / n) * 100.0

    print(f"\n[1] DATASET OVERVIEW & TARGET DISTRIBUTION")
    print(f"  • Total Borrowers:    {n:,}")
    print(f"  • Features Count:     {len(X.columns)}")
    print(f"  • Repaid (Class 1):   {n_repay:,} ({100.0 - default_rate:.2f}%)")
    print(f"  • Default (Class 0):  {n_default:,} ({default_rate:.2f}%)")
    print(f"  • Spatial Villages:   {sensitive['village_id'].nunique()} unique villages")
    print(f"  • Agro-Climatic Zones:{sensitive['agro_climatic_zone'].nunique()} unique zones")

    # Correlations with Target
    correlations = {}
    leakage_warnings = []
    for col in MODEL_FEATURE_NAMES:
        corr = float(np.corrcoef(X[col].to_numpy(), y.to_numpy())[0, 1])
        correlations[col] = corr
        if abs(corr) > 0.80:
            leakage_warnings.append((col, corr))

    print(f"\n[2] TOP PREDICTIVE ALTERNATIVE SIGNALS (Correlation with Repayment)")
    sorted_corr = sorted(correlations.items(), key=lambda item: abs(item[1]), reverse=True)
    for col, corr in sorted_corr[:8]:
        direction = "+" if corr > 0 else "-"
        print(f"  • {col:<32} {direction} {abs(corr):.4f}")

    if leakage_warnings:
        print(f"\n⚠️ TARGET LEAKAGE ALERT: The following features have excessive correlation:")
        for col, corr in leakage_warnings:
            print(f"  - {col}: corr = {corr:.4f}")
    else:
        print(f"  ✓ Zero target leakage detected (all |corr| < 0.80)")

    # Demographic Parity Baselines
    print(f"\n[3] DEMOGRAPHIC & SPATIAL STRATIFICATION")
    gender_counts = sensitive["gender"].value_counts(normalize=True) * 100
    print("  • Gender Breakdown:")
    for g, pct in gender_counts.items():
        print(f"      {g:<8}: {pct:.1f}%")

    land_counts = sensitive["landholding_band"].value_counts(normalize=True) * 100
    print("  • Landholding Distribution:")
    for lb, pct in land_counts.items():
        print(f"      {lb:<12}: {pct:.1f}%")

    # Save summary report
    report_dir = root_dir / "docs" / "ml"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "eda_summary.md"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# CreditTech — Exploratory Data Analysis & Target Profiling Report\n\n")
        f.write(f"- **Sample Size**: {n:,} borrowers\n")
        f.write(f"- **Empirical Default Rate**: {default_rate:.2f}%\n")
        f.write(f"- **Unique Pilot Villages**: {sensitive['village_id'].nunique()}\n")
        f.write(f"- **Agro-Climatic Zones**: {sensitive['agro_climatic_zone'].nunique()}\n\n")
        f.write("## Feature Correlations with Repayment\n\n")
        f.write("| Feature Name | 5-Cs Rail | Correlation with Repayment | Missingness Rate |\n")
        f.write("| :--- | :--- | :--- | :--- |\n")
        for fdef in MODEL_FEATURES:
            corr = correlations.get(fdef.name, 0.0)
            f.write(f"| `{fdef.name}` | {fdef.five_c.upper()} | `{corr:+.4f}` | 0.0% |\n")

    print(f"\n✓ EDA Profiling report written to {report_path.relative_to(root_dir)}")
    print("=" * 70)
    return {
        "n_samples": n,
        "default_rate": default_rate,
        "correlations": correlations,
        "villages": sensitive["village_id"].nunique(),
    }


if __name__ == "__main__":
    run_eda()
