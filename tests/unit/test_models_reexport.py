"""Verify all SQLAlchemy ORM models are re-exported from services.core.shared.models."""

from services.core.shared import models


def test_all_models_reexported():
    expected_models = [
        "Borrower",
        "Village",
        "ConsentRecord",
        "ConsentAuditLog",
        "FeatureSnapshot",
        "DataPull",
        "Score",
        "ReasonCode",
        "LoanApplication",
        "OfficerDecisionLog",
        "RepaymentRecord",
        "FairnessAuditLog",
        "Grievance",
        "GrievanceAuditLog",
    ]
    for name in expected_models:
        assert hasattr(models, name), f"Missing model {name} in services.core.shared.models"
