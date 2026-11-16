"""SQLAlchemy ORM models package for CreditTech.

Exports all domain models for full backward compatibility across the application.
"""

from services.core.shared.models.consent import (
    ConsentAuditLog,
    ConsentRecord,
)
from services.core.shared.models.core import (
    Borrower,
    Village,
)
from services.core.shared.models.decisioning import (
    LoanApplication,
    OfficerDecision,
    OfficerDecisionLog,
    RepaymentRecord,
)
from services.core.shared.models.grievance import (
    FairnessAuditLog,
    Grievance,
    GrievanceAuditLog,
)
from services.core.shared.models.ingestion import (
    DataPull,
    FeatureSnapshot,
)
from services.core.shared.models.scoring import (
    ReasonCode,
    Score,
)

__all__ = [
    "Village",
    "Borrower",
    "ConsentRecord",
    "ConsentAuditLog",
    "DataPull",
    "FeatureSnapshot",
    "Score",
    "ReasonCode",
    "LoanApplication",
    "OfficerDecision",
    "OfficerDecisionLog",
    "RepaymentRecord",
    "FairnessAuditLog",
    "Grievance",
    "GrievanceAuditLog",
]

