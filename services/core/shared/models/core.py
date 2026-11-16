"""Core demographic models: Village and Borrower."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from services.core.database import Base
from services.core.shared.types import GUID

if TYPE_CHECKING:
    from services.core.shared.models.consent import ConsentRecord
    from services.core.shared.models.ingestion import DataPull, FeatureSnapshot
    from services.core.shared.models.scoring import Score


class Village(Base):
    __tablename__ = "villages"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    site_type: Mapped[str] = mapped_column(String(50), nullable=False)
    state: Mapped[str] = mapped_column(String(50), nullable=False)
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    block: Mapped[str] = mapped_column(String(100), nullable=True)
    agro_climatic_zone: Mapped[str] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    borrowers: Mapped[list[Borrower]] = relationship(back_populates="village")


class Borrower(Base):
    __tablename__ = "borrowers"
    __table_args__ = (
        Index("idx_borrowers_village_created", "village_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )

    # PII fields — stored encrypted / hashed
    aadhaar_ref_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, comment="SHA-256 of Aadhaar number"
    )
    name_encrypted: Mapped[str] = mapped_column(
        Text, nullable=False, comment="AES-256-GCM encrypted"
    )
    phone_encrypted: Mapped[str] = mapped_column(
        Text, nullable=False, comment="AES-256-GCM encrypted"
    )

    # Non-PII demographic (used for fairness monitoring, not as model features)
    village_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("villages.id"), nullable=False
    )
    gender: Mapped[str] = mapped_column(
        String(10),
        CheckConstraint("gender IN ('M', 'F', 'OTHER')"),
        nullable=False,
    )
    age: Mapped[int] = mapped_column(Integer, nullable=True)
    landholding_band: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint(
            "landholding_band IN ('LANDLESS', 'MARGINAL', 'SMALL', 'SEMI_MEDIUM', 'MEDIUM', 'LARGE')"
        ),
        nullable=True,
    )
    language: Mapped[str] = mapped_column(String(20), default="hi")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    village: Mapped[Village] = relationship(back_populates="borrowers")
    consent_records: Mapped[list[ConsentRecord]] = relationship(back_populates="borrower")
    data_pulls: Mapped[list[DataPull]] = relationship(back_populates="borrower")
    feature_snapshots: Mapped[list[FeatureSnapshot]] = relationship(back_populates="borrower")
    scores: Mapped[list[Score]] = relationship(back_populates="borrower")

