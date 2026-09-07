"""CLI script to generate regulatory Model Cards and Basel II/III risk dossiers."""

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml.evaluation.model_card import ModelCardGenerator
from ml.registry import ModelRegistry


def main() -> None:
    parser = argparse.ArgumentParser(description="CreditTech Regulatory Model Card Generator")
    parser.add_argument("--version", type=str, default=None, help="Model version (e.g. v1.1.0-woe-scorecard). Defaults to active.")
    parser.add_argument("--out", type=str, default="docs/ml/model_card.md", help="Output file path for markdown model card")
    args = parser.parse_args()

    generator = ModelCardGenerator()
    try:
        rec = generator.get_model_record(args.version)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    out_path = Path(args.out)
    if out_path.is_dir():
        out_path = out_path / f"model_card_{rec.model_version}.md"

    saved_path = generator.save_markdown_dossier(out_path, model_version=rec.model_version)
    print("=" * 60)
    print("CreditTech — Regulatory Model Card Generated Successfully")
    print("=" * 60)
    print(f"Model Version:  {rec.model_version}")
    print(f"Model Type:     {rec.model_type}")
    print(f"Status:         {rec.promotion_status.upper()}")
    print(f"Artifact Hash:  {rec.artifact_hash}")
    print(f"Saved Path:     {saved_path.resolve()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
