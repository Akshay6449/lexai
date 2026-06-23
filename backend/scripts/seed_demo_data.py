"""
Seed demo contracts, clauses, approvals, and audit logs for local development.
"""
import asyncio
import logging
from datetime import datetime, timedelta

from sqlalchemy import select

from core.database import (
    AsyncSessionLocal,
    User,
    Contract,
    Clause,
    Approval,
    AuditLog,
    ContractType,
    ContractStatus,
    RiskLevel,
    ClauseType,
    ApprovalStatus,
)

logger = logging.getLogger(__name__)

DEMO_CONTRACTS = [
    {
        "name": "Acme Corp Mutual NDA",
        "contract_type": ContractType.NDA,
        "counterparty": "Acme Corporation",
        "file_path": "./uploads/demo-nda-acme.pdf",
        "status": ContractStatus.reviewed,
        "risk_score": 32,
        "risk_level": RiskLevel.low,
        "ai_confidence": 0.91,
        "executive_summary": "NDA terms are within standard parameters. Minor confidentiality duration variance noted.",
        "playbook": "NDA Standards",
        "clauses": [
            {
                "clause_type": ClauseType.confidentiality,
                "section_reference": "Section 2.1",
                "original_text": "Receiving Party shall maintain confidentiality for three (3) years.",
                "risk_level": RiskLevel.low,
                "risk_score": 25,
                "confidence_score": 0.93,
            },
            {
                "clause_type": ClauseType.liability,
                "section_reference": "Section 8.2",
                "original_text": "Aggregate liability capped at $500,000 or fees paid in prior 12 months.",
                "risk_level": RiskLevel.low,
                "risk_score": 30,
                "confidence_score": 0.89,
            },
        ],
    },
    {
        "name": "TechVendor MSA — Cloud Services",
        "contract_type": ContractType.MSA,
        "counterparty": "TechVendor Inc.",
        "file_path": "./uploads/demo-msa-techvendor.pdf",
        "status": ContractStatus.pending_approval,
        "risk_score": 87,
        "risk_level": RiskLevel.critical,
        "ai_confidence": 0.88,
        "executive_summary": "Critical indemnification carve-out exposes uncapped liability. Legal manager approval required.",
        "playbook": "MSA Standards",
        "needs_approval": True,
        "clauses": [
            {
                "clause_type": ClauseType.indemnification,
                "section_reference": "Section 9.1",
                "original_text": "Vendor shall indemnify Customer for all claims without limitation or cap.",
                "risk_level": RiskLevel.critical,
                "risk_score": 92,
                "confidence_score": 0.96,
                "explanation": "Unlimited indemnification deviates from 2x annual contract value standard.",
            },
            {
                "clause_type": ClauseType.payment,
                "section_reference": "Section 5.3",
                "original_text": "Net 45 payment terms with 2% monthly late fee.",
                "risk_level": RiskLevel.medium,
                "risk_score": 55,
                "confidence_score": 0.84,
            },
            {
                "clause_type": ClauseType.data_privacy,
                "section_reference": "Section 11.2",
                "original_text": "Vendor processes personal data per GDPR Article 32 with 72-hour breach notice.",
                "risk_level": RiskLevel.low,
                "risk_score": 20,
                "confidence_score": 0.90,
            },
        ],
    },
    {
        "name": "GlobalHost SLA — Infrastructure",
        "contract_type": ContractType.SLA,
        "counterparty": "GlobalHost Ltd.",
        "file_path": "./uploads/demo-sla-globalhost.pdf",
        "status": ContractStatus.approved,
        "risk_score": 48,
        "risk_level": RiskLevel.medium,
        "ai_confidence": 0.86,
        "executive_summary": "SLA terms acceptable with standard service credit cap. Approved by legal manager.",
        "playbook": "SLA Standards",
        "clauses": [
            {
                "clause_type": ClauseType.liability,
                "section_reference": "Schedule A",
                "original_text": "Service credits capped at 15% of monthly recurring fees.",
                "risk_level": RiskLevel.medium,
                "risk_score": 45,
                "confidence_score": 0.87,
            },
            {
                "clause_type": ClauseType.termination,
                "section_reference": "Section 12.4",
                "original_text": "Termination for material breach with 30-day cure period.",
                "risk_level": RiskLevel.low,
                "risk_score": 28,
                "confidence_score": 0.91,
            },
        ],
    },
]


async def seed() -> int:
    created = 0
    now = datetime.utcnow()

    async with AsyncSessionLocal() as db:
        reviewer = (
            await db.execute(select(User).where(User.email == "reviewer@lexai.com"))
        ).scalar_one_or_none()
        manager = (
            await db.execute(select(User).where(User.email == "manager@lexai.com"))
        ).scalar_one_or_none()

        if not reviewer:
            logger.warning("  skip demo contracts: reviewer@lexai.com not found — run seed_users first")
            return 0

        for demo in DEMO_CONTRACTS:
            existing = (
                await db.execute(select(Contract).where(Contract.name == demo["name"]))
            ).scalar_one_or_none()
            if existing:
                logger.info(f"  skip contract (exists): {demo['name']}")
                continue

            contract = Contract(
                name=demo["name"],
                contract_type=demo["contract_type"],
                counterparty=demo["counterparty"],
                file_path=demo["file_path"],
                file_hash=f"demo-{demo['name'][:8].lower().replace(' ', '-')}",
                file_size_bytes=128000,
                playbook=demo["playbook"],
                status=demo["status"],
                risk_score=demo["risk_score"],
                risk_level=demo["risk_level"],
                ai_confidence=demo["ai_confidence"],
                executive_summary=demo["executive_summary"],
                processing_duration_ms=4200,
                uploaded_by=reviewer.id,
                created_at=now - timedelta(days=created + 1),
            )
            db.add(contract)
            await db.flush()

            for clause_data in demo["clauses"]:
                db.add(Clause(contract_id=contract.id, **clause_data))

            if demo.get("needs_approval") and manager:
                db.add(Approval(
                    contract_id=contract.id,
                    requested_by=reviewer.id,
                    status=ApprovalStatus.pending,
                    notes="Auto-routed: contract risk score exceeds approval threshold.",
                ))

            db.add(AuditLog(
                contract_id=contract.id,
                user_id=reviewer.id,
                agent_name="Pipeline",
                action="CONTRACT_ANALYSIS_COMPLETE",
                details=f"Analysis completed for '{demo['name']}' — risk score {demo['risk_score']}",
                duration_ms=4200,
                tokens_used=1850,
            ))
            created += 1
            logger.info(f"  created contract: {demo['name']}")

        if manager:
            db.add(AuditLog(
                user_id=manager.id,
                action="USER_LOGIN",
                details="Manager login from seed data",
            ))
        db.add(AuditLog(
            user_id=reviewer.id,
            action="USER_LOGIN",
            details="Reviewer login from seed data",
        ))

        await db.commit()

    logger.info(f"Demo data: {created} contracts created")
    return created


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    asyncio.run(seed())
