"""Unit tests for Regulatory Model Card Generator."""

import pytest

from ml.evaluation.model_card import ModelCardGenerator
from ml.registry import ModelRegistry


def test_model_card_generation():
    generator = ModelCardGenerator()
    md_content = generator.generate_markdown("v1.1.0-woe-scorecard")

    # Verify key sections
    assert "CreditTech — Model Risk Management (MRM) Dossier" in md_content
    assert "v1.1.0-woe-scorecard" in md_content
    assert "Zero PII in Feature Space" in md_content
    assert "DPDP Retraining Consent Boundary" in md_content
    assert "AUC-ROC" in md_content
    assert "Empirical Probability Calibration" in md_content
    assert "Fairness & Demographic Parity Gate" in md_content


def test_model_card_save_file(tmp_path):
    generator = ModelCardGenerator()
    out_file = tmp_path / "test_model_card.md"
    saved = generator.save_markdown_dossier(out_file, model_version="v1.1.0-woe-scorecard")

    assert saved.exists()
    content = saved.read_text(encoding="utf-8")
    assert "Artifact SHA-256" in content
    assert len(content) > 1000
