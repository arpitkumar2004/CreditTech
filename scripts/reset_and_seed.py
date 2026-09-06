"""Reset and seed the known golden test environment for CreditTech.

Usage:
    python -m scripts.reset_and_seed --reset
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
import uuid
from datetime import datetime, timedelta, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc

from sqlalchemy import text
from services.core.config import get_settings
from services.core.database import Base, async_session_factory, engine, init_db
from services.core.shared.models import (
    Borrower,
    ConsentAuditLog,
    ConsentRecord,
    FairnessAuditLog,
    FeatureSnapshot,
    Grievance,
    GrievanceAuditLog,
    LoanApplication,
    OfficerDecisionLog,
    ReasonCode,
    Score,
    Village,
)
from services.core.shared.test_personas import (
    APP_MEENA_ID,
    APP_RADHIKA_ID,
    APP_RAMU_ID,
    APP_SITA_ID,
    BORROWER_MEENA_ID,
    BORROWER_RADHIKA_ID,
    BORROWER_RAMU_ID,
    BORROWER_SITA_ID,
    CONSENT_MEENA_ID,
    CONSENT_RADHIKA_ID,
    CONSENT_RAMU_ID,
    CONSENT_SITA_ID,
    GRIEVANCE_MEENA_ID,
    SCORE_MEENA_ID,
    SCORE_RADHIKA_ID,
    SCORE_RAMU_ID,
    SCORE_SITA_ID,
    TRIPWIRE_BORROWER_ID,
    TRIPWIRE_CONSENT_ID,
    TRIPWIRE_EXPIRED_BORROWER_ID,
    TRIPWIRE_EXPIRED_CONSENT_ID,
    TRIPWIRE_REVOKED_BORROWER_ID,
    TRIPWIRE_REVOKED_CONSENT_ID,
    TRIPWIRE_SCORE_ID,
    VILLAGE_ALPHA_ID,
    VILLAGE_ALPHA_NAME,
    VILLAGE_BETA_ID,
    VILLAGE_BETA_NAME,
)

settings = get_settings()


def _compute_genesis_hash(borrower_id: uuid.UUID) -> str:
    salt = settings.consent_genesis_salt
    payload = f"GENESIS:{salt}:{borrower_id}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _compute_consent_hash(
    borrower_id: uuid.UUID,
    purpose: str,
    data_sources: list[str],
    issued_at: datetime,
    expires_at: datetime,
    status: str,
    prev_hash: str,
) -> str:
    payload = json.dumps(
        {
            "borrower_id": str(borrower_id),
            "purpose": purpose,
            "data_sources": sorted(data_sources),
            "issued_at": issued_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "status": status,
            "prev_hash": prev_hash,
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


async def reset_database() -> None:
    """Drop all tables and recreate clean schema with append-only triggers."""
    print("🧹 Dropping existing tables and rebuilding database schema...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await init_db()
    print("✅ Schema and append-only audit triggers initialized.")


async def seed_golden_dataset() -> None:
    """Seed the canonical Golden Dataset with permanent test personas & tripwires."""
    print("🌱 Seeding Golden Dataset with permanent personas & tripwires...")
    now = datetime.now(UTC)

    async with async_session_factory() as db:
        # 1. Villages (Cluster Alpha & Cluster Beta)
        village_alpha = Village(
            id=VILLAGE_ALPHA_ID,
            name=VILLAGE_ALPHA_NAME,
            site_type="CANAL_IRRIGATED",
            state="Uttar Pradesh",
            district="Chandauli",
        )
        village_beta = Village(
            id=VILLAGE_BETA_ID,
            name=VILLAGE_BETA_NAME,
            site_type="RAIN_FED",
            state="Uttar Pradesh",
            district="Mirzapur",
        )
        db.add_all([village_alpha, village_beta])
        await db.flush()

        # 2. Permanent Borrowers
        # Radhika Devi (Cluster Alpha - Approved borrower)
        radhika = Borrower(
            id=BORROWER_RADHIKA_ID,
            aadhaar_ref_hash=hashlib.sha256(b"RADHIKA_AADHAAR").hexdigest(),
            name_encrypted="enc:Radhika Devi",
            phone_encrypted="enc:9876543210",
            village_id=VILLAGE_ALPHA_ID,
            gender="F",
            age=34,
            landholding_band="MARGINAL",
        )
        # Sita Kumari (Cluster Alpha - Pending review borrower)
        sita = Borrower(
            id=BORROWER_SITA_ID,
            aadhaar_ref_hash=hashlib.sha256(b"SITA_AADHAAR").hexdigest(),
            name_encrypted="enc:Sita Kumari",
            phone_encrypted="enc:9876543211",
            village_id=VILLAGE_ALPHA_ID,
            gender="F",
            age=29,
            landholding_band="MARGINAL",
        )
        # Ramu Patel (Cluster Beta - Rejected with override)
        ramu = Borrower(
            id=BORROWER_RAMU_ID,
            aadhaar_ref_hash=hashlib.sha256(b"RAMU_AADHAAR").hexdigest(),
            name_encrypted="enc:Ramu Patel",
            phone_encrypted="enc:9876543212",
            village_id=VILLAGE_BETA_ID,
            gender="M",
            age=45,
            landholding_band="SMALL",
        )
        # Meena Verma (Cluster Beta - Active Grievance dispute)
        meena = Borrower(
            id=BORROWER_MEENA_ID,
            aadhaar_ref_hash=hashlib.sha256(b"MEENA_AADHAAR").hexdigest(),
            name_encrypted="enc:Meena Verma",
            phone_encrypted="enc:9876543213",
            village_id=VILLAGE_BETA_ID,
            gender="F",
            age=38,
            landholding_band="MARGINAL",
        )
        # Tripwire Borrowers
        trap_borrower = Borrower(
            id=TRIPWIRE_BORROWER_ID,
            aadhaar_ref_hash=hashlib.sha256(b"TRAP_AADHAAR").hexdigest(),
            name_encrypted="enc:Trap User",
            phone_encrypted="enc:0000000000",
            village_id=VILLAGE_ALPHA_ID,
            gender="F",
            age=30,
            landholding_band="MARGINAL",
        )
        revoked_borrower = Borrower(
            id=TRIPWIRE_REVOKED_BORROWER_ID,
            aadhaar_ref_hash=hashlib.sha256(b"REVOKED_AADHAAR").hexdigest(),
            name_encrypted="enc:Revoked User",
            phone_encrypted="enc:1111111111",
            village_id=VILLAGE_ALPHA_ID,
            gender="M",
            age=40,
            landholding_band="MARGINAL",
        )
        expired_borrower = Borrower(
            id=TRIPWIRE_EXPIRED_BORROWER_ID,
            aadhaar_ref_hash=hashlib.sha256(b"EXPIRED_AADHAAR").hexdigest(),
            name_encrypted="enc:Expired User",
            phone_encrypted="enc:2222222222",
            village_id=VILLAGE_BETA_ID,
            gender="F",
            age=35,
            landholding_band="MARGINAL",
        )

        db.add_all([radhika, sita, ramu, meena, trap_borrower, revoked_borrower, expired_borrower])
        await db.flush()

        # 3. Consents with cryptographic hash chains
        def create_consent_record(
            c_id: uuid.UUID,
            b_id: uuid.UUID,
            status: str = "ACTIVE",
            issued_delta_days: int = 10,
            expires_delta_days: int = 180,
        ) -> tuple[ConsentRecord, ConsentAuditLog]:
            genesis = _compute_genesis_hash(b_id)
            issued = now - timedelta(days=issued_delta_days)
            expires = now + timedelta(days=expires_delta_days)
            data_sources = ["AA", "GEOSPATIAL", "BUREAU", "SHG_FPO"]
            h = _compute_consent_hash(b_id, "credit_scoring", data_sources, issued, expires, status, genesis)
            rec = ConsentRecord(
                id=c_id,
                borrower_id=b_id,
                purpose="credit_scoring",
                consent_mode="bank_sakhi_assisted",
                data_sources=data_sources,
                scope_description_en="Full credit appraisal and scoring",
                issued_at=issued,
                expires_at=expires,
                status=status,
                hash_prev=genesis,
                hash_current=h,
                created_by="system:seed",
            )
            audit_action = "CREATED" if status == "ACTIVE" else ("REVOKED" if status == "REVOKED" else "EXPIRED_AUTO")
            audit = ConsentAuditLog(
                consent_id=c_id,
                action=audit_action,
                actor="system:seed",
                performed_at=issued,
            )
            return rec, audit

        c_radhika, a_radhika = create_consent_record(CONSENT_RADHIKA_ID, BORROWER_RADHIKA_ID)
        c_sita, a_sita = create_consent_record(CONSENT_SITA_ID, BORROWER_SITA_ID)
        c_ramu, a_ramu = create_consent_record(CONSENT_RAMU_ID, BORROWER_RAMU_ID)
        c_meena, a_meena = create_consent_record(CONSENT_MEENA_ID, BORROWER_MEENA_ID)
        c_trap, a_trap = create_consent_record(TRIPWIRE_CONSENT_ID, TRIPWIRE_BORROWER_ID)
        c_revoked, a_revoked = create_consent_record(
            TRIPWIRE_REVOKED_CONSENT_ID, TRIPWIRE_REVOKED_BORROWER_ID, status="REVOKED"
        )
        c_expired, a_expired = create_consent_record(
            TRIPWIRE_EXPIRED_CONSENT_ID, TRIPWIRE_EXPIRED_BORROWER_ID, status="EXPIRED", issued_delta_days=200, expires_delta_days=-10
        )

        db.add_all([
            c_radhika, a_radhika,
            c_sita, a_sita,
            c_ramu, a_ramu,
            c_meena, a_meena,
            c_trap, a_trap,
            c_revoked, a_revoked,
            c_expired, a_expired,
        ])
        await db.flush()

        # 4. Feature Snapshots & Scores
        snap_radhika = FeatureSnapshot(
            borrower_id=BORROWER_RADHIKA_ID,
            feature_version="v1.0.0",
            season_tag="KHARIF",
            sources_used=["AA", "SHG_FPO", "GEOSPATIAL", "BUREAU"],
            features_json={"shg_repayment_rate": 0.98, "shg_meeting_attendance_pct": 92.0, "shg_cumulative_savings": 12500.0, "land_holding_acres": 1.8, "land_quality_ndvi_avg": 0.68},
        )
        snap_sita = FeatureSnapshot(
            borrower_id=BORROWER_SITA_ID,
            feature_version="v1.0.0",
            season_tag="KHARIF",
            sources_used=["AA", "SHG_FPO", "GEOSPATIAL"],
            features_json={"shg_repayment_rate": 0.88, "shg_meeting_attendance_pct": 80.0, "shg_cumulative_savings": 5000.0, "land_holding_acres": 0.9, "land_quality_ndvi_avg": 0.55},
        )
        snap_ramu = FeatureSnapshot(
            borrower_id=BORROWER_RAMU_ID,
            feature_version="v1.0.0",
            season_tag="KHARIF",
            sources_used=["SHG_FPO", "GEOSPATIAL"],
            features_json={"shg_repayment_rate": 0.72, "shg_meeting_attendance_pct": 65.0, "shg_cumulative_savings": 2200.0, "land_holding_acres": 3.0, "land_quality_ndvi_avg": 0.38},
        )
        snap_meena = FeatureSnapshot(
            borrower_id=BORROWER_MEENA_ID,
            feature_version="v1.0.0",
            season_tag="KHARIF",
            sources_used=["SHG_FPO", "GEOSPATIAL", "AA"],
            features_json={"shg_repayment_rate": 0.84, "shg_meeting_attendance_pct": 75.0, "shg_cumulative_savings": 4100.0, "land_holding_acres": 1.1, "land_quality_ndvi_avg": 0.42},
        )
        snap_trap = FeatureSnapshot(
            borrower_id=TRIPWIRE_BORROWER_ID,
            feature_version="v1.0.0",
            season_tag="KHARIF",
            sources_used=["SHG_FPO"],
            features_json={"shg_repayment_rate": 0.90, "land_holding_acres": 1.0},
        )

        db.add_all([snap_radhika, snap_sita, snap_ramu, snap_meena, snap_trap])
        await db.flush()

        score_radhika = Score(
            id=SCORE_RADHIKA_ID,
            borrower_id=BORROWER_RADHIKA_ID,
            feature_snapshot_id=snap_radhika.id,
            model_version="v1.1.0-woe-scorecard",
            score=78.5,
            confidence_lower=710,
            confidence_upper=770,
            sources_used=["AA", "SHG_FPO", "GEOSPATIAL", "BUREAU"],
            generated_at=now - timedelta(days=2),
        )
        score_sita = Score(
            id=SCORE_SITA_ID,
            borrower_id=BORROWER_SITA_ID,
            feature_snapshot_id=snap_sita.id,
            model_version="v1.1.0-woe-scorecard",
            score=64.0,
            confidence_lower=610,
            confidence_upper=660,
            sources_used=["AA", "SHG_FPO", "GEOSPATIAL"],
            generated_at=now - timedelta(days=1),
        )
        score_ramu = Score(
            id=SCORE_RAMU_ID,
            borrower_id=BORROWER_RAMU_ID,
            feature_snapshot_id=snap_ramu.id,
            model_version="v1.1.0-woe-scorecard",
            score=48.0,
            confidence_lower=480,
            confidence_upper=530,
            sources_used=["SHG_FPO", "GEOSPATIAL"],
            generated_at=now - timedelta(days=3),
        )
        score_meena = Score(
            id=SCORE_MEENA_ID,
            borrower_id=BORROWER_MEENA_ID,
            feature_snapshot_id=snap_meena.id,
            model_version="v1.1.0-woe-scorecard",
            score=56.0,
            confidence_lower=550,
            confidence_upper=600,
            sources_used=["SHG_FPO", "GEOSPATIAL", "AA"],
            generated_at=now - timedelta(days=4),
        )
        score_trap = Score(
            id=TRIPWIRE_SCORE_ID,
            borrower_id=TRIPWIRE_BORROWER_ID,
            feature_snapshot_id=snap_trap.id,
            model_version="v1.1.0-woe-scorecard",
            score=70.0,
            confidence_lower=680,
            confidence_upper=720,
            sources_used=["SHG_FPO"],
            generated_at=now - timedelta(days=1),
        )

        db.add_all([score_radhika, score_sita, score_ramu, score_meena, score_trap])
        await db.flush()

        # 5. SHAP Reason Codes
        db.add_all([
            ReasonCode(score_id=SCORE_RADHIKA_ID, rank=1, feature_name="shg_repayment_rate", direction="POSITIVE", shap_value=0.45, localized_text_en="Excellent SHG repayment track record (98%)", localized_text_hi="उत्कृष्ट SHG पुनर्भुगतान ट्रैक रिकॉर्ड (98%)"),
            ReasonCode(score_id=SCORE_RADHIKA_ID, rank=2, feature_name="land_quality_ndvi_avg", direction="POSITIVE", shap_value=0.32, localized_text_en="Healthy crop vegetation index (NDVI: 0.68)", localized_text_hi="स्वस्थ फसल वनस्पति सूचकांक (NDVI: 0.68)"),
            ReasonCode(score_id=SCORE_RAMU_ID, rank=1, feature_name="land_quality_ndvi_avg", direction="NEGATIVE", shap_value=-0.52, localized_text_en="Low vegetative vigor / drought stress (NDVI: 0.38)", localized_text_hi="कम वनस्पति ओज / सूखा तनाव (NDVI: 0.38)"),
            ReasonCode(score_id=SCORE_RAMU_ID, rank=2, feature_name="shg_repayment_rate", direction="NEGATIVE", shap_value=-0.41, localized_text_en="Irregular group savings attendance (65%)", localized_text_hi="अनियमित समूह बचत उपस्थिति (65%)"),
        ])
        await db.flush()

        # 6. Loan Applications & Officer Decisions
        app_radhika = LoanApplication(
            id=APP_RADHIKA_ID,
            borrower_id=BORROWER_RADHIKA_ID,
            score_id=SCORE_RADHIKA_ID,
            partner_re_id="RE-SBI-01",
            requested_amount=50000.0,
            requested_tenure_months=12,
            purpose="Irrigation equipment",
            officer_decision="APPROVED",
            approved_amount=50000.0,
            decided_at=now - timedelta(days=2),
            created_at=now - timedelta(days=2),
        )
        app_sita = LoanApplication(
            id=APP_SITA_ID,
            borrower_id=BORROWER_SITA_ID,
            score_id=SCORE_SITA_ID,
            partner_re_id="RE-SBI-01",
            requested_amount=35000.0,
            requested_tenure_months=12,
            purpose="Crop working capital",
            officer_decision=None,
            created_at=now - timedelta(days=1),
        )
        app_ramu = LoanApplication(
            id=APP_RAMU_ID,
            borrower_id=BORROWER_RAMU_ID,
            score_id=SCORE_RAMU_ID,
            partner_re_id="RE-BOB-01",
            requested_amount=75000.0,
            requested_tenure_months=18,
            purpose="Dryland pulse farming",
            officer_decision="REJECTED",
            decided_at=now - timedelta(days=3),
            created_at=now - timedelta(days=3),
        )
        app_meena = LoanApplication(
            id=APP_MEENA_ID,
            borrower_id=BORROWER_MEENA_ID,
            score_id=SCORE_MEENA_ID,
            partner_re_id="RE-BOB-01",
            requested_amount=40000.0,
            requested_tenure_months=12,
            purpose="Milch cattle purchase",
            officer_decision="REFERRED",
            created_at=now - timedelta(days=4),
        )

        db.add_all([app_radhika, app_sita, app_ramu, app_meena])
        await db.flush()

        # Decisions in append-only log
        decision_radhika = OfficerDecisionLog(
            score_id=SCORE_RADHIKA_ID,
            loan_application_id=APP_RADHIKA_ID,
            officer_id="OFF-001",
            decision="APPROVED",
            model_recommendation="APPROVE",
            is_override=False,
            officer_notes="Strong SHG thrift consistency and reliable canal irrigation.",
            model_score_at_decision=78.5,
            model_version_at_decision="v1.1.0-woe-scorecard",
            feature_version_at_decision="v1.0.0",
            created_at=now - timedelta(days=2),
        )
        decision_ramu = OfficerDecisionLog(
            score_id=SCORE_RAMU_ID,
            loan_application_id=APP_RAMU_ID,
            officer_id="OFF-002",
            decision="REJECTED",
            model_recommendation="REJECT",
            is_override=False,
            officer_notes="Below risk cutoff; severe rain-fed NDVI stress in current cycle.",
            model_score_at_decision=48.0,
            model_version_at_decision="v1.1.0-woe-scorecard",
            feature_version_at_decision="v1.0.0",
            created_at=now - timedelta(days=3),
        )
        db.add_all([decision_radhika, decision_ramu])
        await db.flush()

        # 7. Grievance Record with SLA Clock
        grievance_meena = Grievance(
            id=GRIEVANCE_MEENA_ID,
            borrower_id=BORROWER_MEENA_ID,
            score_id=SCORE_MEENA_ID,
            loan_application_id=APP_MEENA_ID,
            category="SCORE_DISPUTE",
            description="Disputing low NDVI score due to neighboring canal water sharing agreement not reflected in satellite rail. Our SHG maintains an unmapped local lift irrigation channel. Please request field verification.",
            status="OPEN",
            sla_hours=168,
            assigned_to="OFF-002",
            created_at=now - timedelta(hours=14),
            due_at=now - timedelta(hours=14) + timedelta(hours=168),
        )
        grievance_audit = GrievanceAuditLog(
            grievance_id=GRIEVANCE_MEENA_ID,
            from_status=None,
            to_status="OPEN",
            actor="borrower:" + str(BORROWER_MEENA_ID),
            note="Appeal initiated with Bank Sakhi field support.",
            performed_at=now - timedelta(hours=14),
        )
        db.add_all([grievance_meena, grievance_audit])
        await db.flush()

        # 8. Fairness Audit Logs (for FairnessGate compliance)
        for dim, group, sample, rate, o_rate in [
            ("GENDER", "F", 120, 0.68, 0.04),
            ("GENDER", "M", 90, 0.70, 0.05),
            ("GEOGRAPHY", "CANAL_IRRIGATED", 110, 0.72, 0.03),
            ("GEOGRAPHY", "RAIN_FED", 100, 0.65, 0.06),
            ("LANDHOLDING", "MARGINAL", 140, 0.66, 0.04),
            ("LANDHOLDING", "SMALL", 70, 0.73, 0.05),
        ]:
            db.add(FairnessAuditLog(
                period="2026-W36",
                dimension=dim,
                group_value=group,
                sample_size=sample,
                approval_rate=rate,
                override_rate=o_rate,
                status="OK",
                computed_at=now - timedelta(days=5),
            ))

        await db.commit()

    print("✨ Golden Dataset successfully seeded:")
    print("   • Cluster Alpha (Chandauli): Officer Rajesh (OFF-001), Sakhi Sunita, Borrowers Radhika & Sita")
    print("   • Cluster Beta (Mirzapur): Officer Vikram (OFF-002), Sakhi Anita, Borrowers Ramu & Meena")
    print("   • Admin & Risk: Amit Verma (ADMIN-001), Priya Sharma (RISK-001)")
    print("   • Security Tripwires: Trap User, Revoked Consent, Expired Consent")


def main() -> None:
    parser = argparse.ArgumentParser(description="CreditTech Golden Test Environment Reset & Seed")
    parser.add_argument("--reset", action="store_true", help="Drop and rebuild database schema before seeding")
    args = parser.parse_args()

    async def _run() -> None:
        if args.reset:
            await reset_database()
        await seed_golden_dataset()

    asyncio.run(_run())


if __name__ == "__main__":
    main()
