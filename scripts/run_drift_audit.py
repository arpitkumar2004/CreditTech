"""CLI script to run Population Stability Index (PSI) and Characteristic Stability Index (CSI) drift audit."""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.core.database import async_session_factory
from services.core.monitoring.service import DriftMonitorService


async def main() -> None:
    parser = argparse.ArgumentParser(description="CreditTech ML Drift Audit CLI")
    parser.add_argument("--limit", type=int, default=500, help="Max scoring records to audit")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    async with async_session_factory() as session:
        monitor = DriftMonitorService(session)
        report = await monitor.compute_drift_audit(limit=args.limit)

        if args.json:
            print(json.dumps(report, indent=2))
            return

        print("=" * 60)
        print("CreditTech — Population & Characteristic Stability Audit (PSI/CSI)")
        print("=" * 60)
        print(f"Status: {report.get('status')}")
        print(f"Evaluated Scores: {report.get('evaluated_scores_count', 0)}")
        print(f"Evaluated Feature Records: {report.get('evaluated_features_count', 0)}")
        print(f"Model Version: {report.get('model_version')}")

        psi_info = report.get("score_psi")
        if psi_info:
            print("-" * 60)
            print(f"Score Distribution PSI: {psi_info.get('psi'):.4f} [{psi_info.get('status')} - {psi_info.get('alert_level')}]")
            print(f"Action: {psi_info.get('action_required')}")

        csi_info = report.get("feature_csi")
        if csi_info and "overall_csi" in csi_info:
            print("-" * 60)
            print(f"Overall Feature CSI: {csi_info.get('overall_csi'):.4f} [{csi_info.get('overall_status')}]")
            print(f"Highest Drift Feature: {csi_info.get('highest_drift_feature')}")
            print("Feature Breakdown:")
            for feat, res in csi_info.get("features", {}).items():
                print(f"  - {feat:30s}: PSI={res.get('psi'):.4f} [{res.get('status')}]")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
