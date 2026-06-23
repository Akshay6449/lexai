"""
Analysis API — clauses, risk detail, RAG results, audit log per contract.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from auth.jwt_handler import require_any_legal
from core.database import AsyncSession, get_db, Contract, Clause, AuditLog, User
from sqlalchemy.orm import selectinload

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────

class ClauseOut(BaseModel):
    id: str
    clause_type: str
    section_reference: Optional[str]
    original_text: str
    suggested_text: Optional[str]
    risk_level: Optional[str]
    risk_score: Optional[int]
    confidence_score: Optional[float]
    explanation: Optional[str]
    business_impact: Optional[str]
    rag_source: Optional[str]
    rag_similarity: Optional[float]


class RiskBreakdown(BaseModel):
    overall_score: int
    overall_level: str
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    clauses: list[ClauseOut]


class AuditEntry(BaseModel):
    id: str
    agent_name: Optional[str]
    action: str
    details: Optional[str]
    duration_ms: Optional[int]
    tokens_used: Optional[int]
    langsmith_trace_id: Optional[str]
    created_at: str


# ── Routes ───────────────────────────────────────────────────

@router.get("/{contract_id}/clauses", response_model=list[ClauseOut])
async def get_clauses(
    contract_id: str,
    clause_type: Optional[str] = None,
    risk_level: Optional[str] = None,
    current_user: User = Depends(require_any_legal),
    db: AsyncSession = Depends(get_db),
):
    await _assert_contract(contract_id, db)
    q = select(Clause).where(Clause.contract_id == contract_id)
    if clause_type:
        q = q.where(Clause.clause_type == clause_type)
    if risk_level:
        q = q.where(Clause.risk_level == risk_level)
    clauses = (await db.execute(q)).scalars().all()
    return [_clause_out(c) for c in clauses]


@router.get("/{contract_id}/risk", response_model=RiskBreakdown)
async def get_risk_breakdown(
    contract_id: str,
    current_user: User = Depends(require_any_legal),
    db: AsyncSession = Depends(get_db),
):
    contract = await _assert_contract(contract_id, db)
    clauses = (
        await db.execute(select(Clause).where(Clause.contract_id == contract_id))
    ).scalars().all()

    return RiskBreakdown(
        overall_score=contract.risk_score or 0,
        overall_level=contract.risk_level or "low",
        critical_count=sum(1 for c in clauses if c.risk_level == "critical"),
        high_count=sum(1 for c in clauses if c.risk_level == "high"),
        medium_count=sum(1 for c in clauses if c.risk_level == "medium"),
        low_count=sum(1 for c in clauses if c.risk_level == "low"),
        clauses=[_clause_out(c) for c in clauses],
    )


@router.get("/{contract_id}/audit", response_model=list[AuditEntry])
async def get_audit_log(
    contract_id: str,
    current_user: User = Depends(require_any_legal),
    db: AsyncSession = Depends(get_db),
):
    await _assert_contract(contract_id, db)
    logs = (
        await db.execute(
            select(AuditLog)
            .where(AuditLog.contract_id == contract_id)
            .order_by(AuditLog.created_at)
        )
    ).scalars().all()
    return [
        AuditEntry(
            id=str(lg.id),
            agent_name=lg.agent_name,
            action=lg.action,
            details=lg.details,
            duration_ms=lg.duration_ms,
            tokens_used=lg.tokens_used,
            langsmith_trace_id=lg.langsmith_trace_id,
            created_at=lg.created_at.isoformat(),
        )
        for lg in logs
    ]


@router.get("/{contract_id}/summary")
async def get_executive_summary(
    contract_id: str,
    current_user: User = Depends(require_any_legal),
    db: AsyncSession = Depends(get_db),
):
    contract = await _assert_contract(contract_id, db)
    return {
        "contract_id": contract_id,
        "contract_name": contract.name,
        "executive_summary": contract.executive_summary,
        "risk_score": contract.risk_score,
        "risk_level": contract.risk_level,
        "ai_confidence": contract.ai_confidence,
    }


# ── Helpers ──────────────────────────────────────────────────

async def _assert_contract(contract_id: str, db: AsyncSession) -> Contract:
    c = (await db.execute(select(Contract).where(Contract.id == contract_id))).scalar_one_or_none()
    if not c:
        raise HTTPException(404, "Contract not found.")
    return c


def _clause_out(c: Clause) -> ClauseOut:
    return ClauseOut(
        id=str(c.id),
        clause_type=c.clause_type,
        section_reference=c.section_reference,
        original_text=c.original_text,
        suggested_text=c.suggested_text,
        risk_level=c.risk_level,
        risk_score=c.risk_score,
        confidence_score=c.confidence_score,
        explanation=c.explanation,
        business_impact=c.business_impact,
        rag_source=c.rag_source,
        rag_similarity=c.rag_similarity,
    )
