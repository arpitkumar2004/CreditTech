"""initial schema

Revision ID: 14323a45982d
Revises:
Create Date: 2026-09-03 10:44:59.289394

Creates the full 10-entity ORM schema from services.core.shared.models
including all CHECK constraints. Works on PostgreSQL (production) and
SQLite (in-memory test harness / offline autogenerate) thanks to the
cross-dialect TypeDecorators in services.core.shared.types.
"""
from collections.abc import Sequence

import sqlalchemy as sa

import services.core.shared.types  # noqa: F401 — referenced by GUID/JSONB/INET columns
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "14323a45982d"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


TS = sa.DateTime(timezone=True)
NOW = sa.text("(CURRENT_TIMESTAMP)")


def upgrade() -> None:
    op.create_table(
        "fairness_audit_log",
        sa.Column("id", services.core.shared.types.GUID(), nullable=False),
        sa.Column("period", sa.String(length=20), nullable=False),
        sa.Column("dimension", sa.String(length=30), nullable=False),
        sa.Column("group_value", sa.String(length=50), nullable=False),
        sa.Column("approval_rate", sa.Float(), nullable=False),
        sa.Column("sample_size", sa.Integer(), nullable=False),
        sa.Column("override_rate", sa.Float(), nullable=True),
        sa.Column("computed_at", TS, server_default=NOW, nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "dimension IN ('GENDER', 'GEOGRAPHY', 'LANDHOLDING', 'OFFICER')",
            name="ck_fairness_audit_log_dimension",
        ),
    )

    op.create_table(
        "villages",
        sa.Column("id", services.core.shared.types.GUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("site_type", sa.String(length=50), nullable=False),
        sa.Column("state", sa.String(length=50), nullable=False),
        sa.Column("district", sa.String(length=100), nullable=False),
        sa.Column("block", sa.String(length=100), nullable=True),
        sa.Column("agro_climatic_zone", sa.String(length=100), nullable=True),
        sa.Column("created_at", TS, server_default=NOW, nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "borrowers",
        sa.Column("id", services.core.shared.types.GUID(), nullable=False),
        sa.Column("aadhaar_ref_hash", sa.String(length=64), nullable=False, comment="SHA-256 of Aadhaar number"),
        sa.Column("name_encrypted", sa.Text(), nullable=False, comment="AES-256-GCM encrypted"),
        sa.Column("phone_encrypted", sa.Text(), nullable=False, comment="AES-256-GCM encrypted"),
        sa.Column("village_id", services.core.shared.types.GUID(), nullable=False),
        sa.Column("gender", sa.String(length=10), nullable=False),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("landholding_band", sa.String(length=20), nullable=True),
        sa.Column("language", sa.String(length=20), nullable=False),
        sa.Column("created_at", TS, server_default=NOW, nullable=False),
        sa.Column("updated_at", TS, server_default=NOW, nullable=False),
        sa.ForeignKeyConstraint(["village_id"], ["villages.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("aadhaar_ref_hash"),
        sa.CheckConstraint("gender IN ('M', 'F', 'OTHER')", name="ck_borrowers_gender"),
        sa.CheckConstraint(
            "landholding_band IS NULL OR landholding_band IN "
            "('LANDLESS', 'MARGINAL', 'SMALL', 'SEMI_MEDIUM', 'MEDIUM', 'LARGE')",
            name="ck_borrowers_landholding_band",
        ),
    )

    op.create_table(
        "consent_records",
        sa.Column("id", services.core.shared.types.GUID(), nullable=False),
        sa.Column("borrower_id", services.core.shared.types.GUID(), nullable=False),
        sa.Column("purpose", sa.String(length=50), nullable=False),
        sa.Column("consent_mode", sa.String(length=20), nullable=False),
        sa.Column("aa_consent_id", sa.String(length=128), nullable=True),
        sa.Column("aa_handle", sa.String(length=128), nullable=True),
        sa.Column("fi_types", services.core.shared.types.JSONB(), nullable=False),
        sa.Column("fi_date_range_from", TS, nullable=True),
        sa.Column("fi_date_range_to", TS, nullable=True),
        sa.Column("fetch_frequency", sa.String(length=20), nullable=True),
        sa.Column("data_sources", services.core.shared.types.JSONB(), nullable=False),
        sa.Column("scope_description_en", sa.Text(), nullable=False),
        sa.Column("scope_description_hi", sa.Text(), nullable=True),
        sa.Column("scope_description_local", sa.Text(), nullable=True),
        sa.Column("issued_at", TS, server_default=NOW, nullable=False),
        sa.Column("expires_at", TS, nullable=False),
        sa.Column("revoked_at", TS, nullable=True),
        sa.Column("revocation_reason", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("hash_prev", sa.String(length=64), nullable=False),
        sa.Column("hash_current", sa.String(length=64), nullable=False),
        sa.Column("created_by", sa.String(length=50), nullable=False),
        sa.Column("ip_address", services.core.shared.types.INET(), nullable=True),
        sa.Column("device_id", sa.String(length=128), nullable=True),
        sa.Column("consent_artifact_ref", sa.String(length=256), nullable=True),
        sa.Column("created_at", TS, server_default=NOW, nullable=False),
        sa.Column("updated_at", TS, server_default=NOW, nullable=False),
        sa.ForeignKeyConstraint(["borrower_id"], ["borrowers.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "purpose IN ('credit_scoring', 'identity_verification', "
            "'data_aggregation', 'score_sharing_with_re', 'retraining_consent')",
            name="ck_consent_records_purpose",
        ),
        sa.CheckConstraint(
            "consent_mode IN ('app_self_service', 'bank_sakhi_assisted', 'ivr_voice')",
            name="ck_consent_records_consent_mode",
        ),
        sa.CheckConstraint(
            "fetch_frequency IS NULL OR "
            "fetch_frequency IN ('ONETIME', 'HOURLY', 'DAILY', 'MONTHLY', 'YEARLY')",
            name="ck_consent_records_fetch_frequency",
        ),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'EXPIRED', 'REVOKED', 'SUPERSEDED')",
            name="ck_consent_records_status",
        ),
    )
    op.create_index("idx_consent_borrower_status", "consent_records", ["borrower_id", "status"])
    op.create_index(
        "idx_consent_expires_at",
        "consent_records",
        ["expires_at"],
        postgresql_where=sa.text("status = 'ACTIVE'"),
    )
    op.create_index("idx_consent_hash_chain", "consent_records", ["hash_current"])

    op.create_table(
        "data_pulls",
        sa.Column("id", services.core.shared.types.GUID(), nullable=False),
        sa.Column("borrower_id", services.core.shared.types.GUID(), nullable=False),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("raw_ref", sa.String(length=512), nullable=True, comment="Object storage path to raw response"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("pulled_at", TS, server_default=NOW, nullable=False),
        sa.ForeignKeyConstraint(["borrower_id"], ["borrowers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "source IN ('AA', 'GEOSPATIAL', 'SHG_FPO', 'BUREAU')",
            name="ck_data_pulls_source",
        ),
        sa.CheckConstraint(
            "status IN ('PENDING', 'IN_PROGRESS', 'SUCCESS', 'FAILED', 'TIMEOUT', 'SKIPPED')",
            name="ck_data_pulls_status",
        ),
    )

    op.create_table(
        "feature_snapshots",
        sa.Column("id", services.core.shared.types.GUID(), nullable=False),
        sa.Column("borrower_id", services.core.shared.types.GUID(), nullable=False),
        sa.Column("feature_version", sa.String(length=20), nullable=False),
        sa.Column("features_json", services.core.shared.types.JSONB(), nullable=False, comment="Model-ready features — NO PII"),
        sa.Column("season_tag", sa.String(length=10), nullable=False),
        sa.Column("sources_used", services.core.shared.types.JSONB(), nullable=False),
        sa.Column("computed_at", TS, server_default=NOW, nullable=False),
        sa.ForeignKeyConstraint(["borrower_id"], ["borrowers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "season_tag IN ('KHARIF', 'RABI', 'ZAID')",
            name="ck_feature_snapshots_season_tag",
        ),
    )

    op.create_table(
        "consent_audit_log",
        sa.Column("id", services.core.shared.types.GUID(), nullable=False),
        sa.Column("consent_id", services.core.shared.types.GUID(), nullable=False),
        sa.Column("action", sa.String(length=20), nullable=False),
        sa.Column("actor", sa.String(length=50), nullable=False),
        sa.Column("details", services.core.shared.types.JSONB(), nullable=True),
        sa.Column("performed_at", TS, server_default=NOW, nullable=False),
        sa.ForeignKeyConstraint(["consent_id"], ["consent_records.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "action IN ('CREATED', 'VERIFIED', 'REVOKED', "
            "'EXPIRED_AUTO', 'SUPERSEDED', 'ACCESSED')",
            name="ck_consent_audit_log_action",
        ),
    )

    op.create_table(
        "scores",
        sa.Column("id", services.core.shared.types.GUID(), nullable=False),
        sa.Column("borrower_id", services.core.shared.types.GUID(), nullable=False),
        sa.Column("feature_snapshot_id", services.core.shared.types.GUID(), nullable=False),
        sa.Column("model_version", sa.String(length=50), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("confidence_lower", sa.Float(), nullable=False),
        sa.Column("confidence_upper", sa.Float(), nullable=False),
        sa.Column("sources_used", services.core.shared.types.JSONB(), nullable=False),
        sa.Column("generated_at", TS, server_default=NOW, nullable=False),
        sa.ForeignKeyConstraint(["borrower_id"], ["borrowers.id"]),
        sa.ForeignKeyConstraint(["feature_snapshot_id"], ["feature_snapshots.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "loan_applications",
        sa.Column("id", services.core.shared.types.GUID(), nullable=False),
        sa.Column("borrower_id", services.core.shared.types.GUID(), nullable=False),
        sa.Column("score_id", services.core.shared.types.GUID(), nullable=False),
        sa.Column("partner_re_id", sa.String(length=100), nullable=False),
        sa.Column("requested_amount", sa.Float(), nullable=False),
        sa.Column("requested_tenure_months", sa.Integer(), nullable=False),
        sa.Column("purpose", sa.String(length=50), nullable=False),
        sa.Column("officer_decision", sa.String(length=20), nullable=True),
        sa.Column("decided_at", TS, nullable=True),
        sa.Column("override_reason", sa.Text(), nullable=True),
        sa.Column("approved_amount", sa.Float(), nullable=True),
        sa.Column("created_at", TS, server_default=NOW, nullable=False),
        sa.Column("updated_at", TS, server_default=NOW, nullable=False),
        sa.ForeignKeyConstraint(["borrower_id"], ["borrowers.id"]),
        sa.ForeignKeyConstraint(["score_id"], ["scores.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "officer_decision IS NULL OR "
            "officer_decision IN ('APPROVED', 'REJECTED', 'MORE_INFO_REQUIRED', 'REFERRED')",
            name="ck_loan_applications_officer_decision",
        ),
    )

    op.create_table(
        "reason_codes",
        sa.Column("id", services.core.shared.types.GUID(), nullable=False),
        sa.Column("score_id", services.core.shared.types.GUID(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("feature_name", sa.String(length=100), nullable=False),
        sa.Column("direction", sa.String(length=10), nullable=False),
        sa.Column("shap_value", sa.Float(), nullable=False),
        sa.Column("localized_text_en", sa.Text(), nullable=False),
        sa.Column("localized_text_hi", sa.Text(), nullable=True),
        sa.Column("localized_text_local", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["score_id"], ["scores.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "direction IN ('POSITIVE', 'NEGATIVE')",
            name="ck_reason_codes_direction",
        ),
    )

    op.create_table(
        "repayment_records",
        sa.Column("id", services.core.shared.types.GUID(), nullable=False),
        sa.Column("loan_application_id", services.core.shared.types.GUID(), nullable=False),
        sa.Column("period", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("consented_for_retraining", sa.Boolean(), nullable=False),
        sa.Column("recorded_at", TS, server_default=NOW, nullable=False),
        sa.ForeignKeyConstraint(["loan_application_id"], ["loan_applications.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "status IN ('CURRENT', 'DPD_1_30', 'DPD_31_60', 'DPD_61_90', 'DPD_90_PLUS', 'CLOSED')",
            name="ck_repayment_records_status",
        ),
    )


def downgrade() -> None:
    op.drop_table("repayment_records")
    op.drop_table("reason_codes")
    op.drop_table("loan_applications")
    op.drop_table("scores")
    op.drop_table("consent_audit_log")
    op.drop_table("feature_snapshots")
    op.drop_table("data_pulls")
    op.drop_index("idx_consent_hash_chain", table_name="consent_records")
    op.drop_index(
        "idx_consent_expires_at",
        table_name="consent_records",
        postgresql_where=sa.text("status = 'ACTIVE'"),
    )
    op.drop_index("idx_consent_borrower_status", table_name="consent_records")
    op.drop_table("consent_records")
    op.drop_table("borrowers")
    op.drop_table("villages")
    op.drop_table("fairness_audit_log")
