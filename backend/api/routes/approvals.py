"""
Approval Workflow API — human-in-the-loop review.
Only legal_manager and admin can approve/reject.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from auth.jwt_handler import get_current_user, require_manager, require_any_legal
from core.database import (
    AsyncSession, get_db, Approval, ApprovalStatus, Contract,
    ContractStatus, User, AuditLog
)

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────

class ApprovalOut(BaseModel):
    id: str
    contract_id: str
    contract_name: str
    contract_type: str
    risk_score: Optional[int]
    risk_level: Optional[str]
    requested_by: str
    reviewed_by: Optional[str]
    status: str
    notes: Optional[str]
    conditions: Optional[str]
    created_at: str
    reviewed_at: Optional[str]


class ApprovalDecision(BaseModel):
    notes: Optional[str] = None
    conditions: Optional[str] = None     # for approved_with_conditions


# ── Routes ───────────────────────────────────────────────────

@router.get("", response_model=list[ApprovalOut])
async def list_approvals(
    status: Optional[str] = None,
    current_user: User = Depends(require_any_legal),
    db: AsyncSession = Depends(get_db),
):
    q = (
        select(Approval)
        .options(selectinload(Approval.contract), selectinload(Approval.requested_by_user))
        .order_by(Approval.created_at.desc())
    )
    if status:
        q = q.where(Approval.status == status)
    results = (await db.execute(q)).scalars().all()
    return [_to_out(a) for a in results]


@router.get("/pending", response_model=list[ApprovalOut])
async def list_pending(
    current_user: User = Depends(require_any_legal),
    db: AsyncSession = Depends(get_db),
):
    results = (
        await db.execute(
            select(Approval)
            .options(selectinload(Approval.contract))
            .where(Approval.status == ApprovalStatus.pending)
            .order_by(Approval.created_at.asc())
        )
    ).scalars().all()
    return [_to_out(a) for a in results]


@router.post("/{approval_id}/approve", response_model=ApprovalOut)
async def approve_contract(
    approval_id: str,
    decision: ApprovalDecision,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    approval = await _get_or_404(approval_id, db)
    _assert_pending(approval)

    status = ApprovalStatus.approved_with_conditions if decision.conditions else ApprovalStatus.approved
    approval.status = status
    approval.reviewed_by = current_user.id
    approval.notes = decision.notes
    approval.conditions = decision.conditions
    approval.reviewed_at = datetime.utcnow()
    approval.contract.status = ContractStatus.approved

    db.add(AuditLog(
        contract_id=approval.contract_id,
        user_id=current_user.id,
        action="CONTRACT_APPROVED",
        details=f"Approved by {current_user.email}. Conditions: {decision.conditions or 'None'}",
    ))
    await db.commit()
    await db.refresh(approval)
    return _to_out(approval)


@router.post("/{approval_id}/reject", response_model=ApprovalOut)
async def reject_contract(
    approval_id: str,
    decision: ApprovalDecision,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    approval = await _get_or_404(approval_id, db)
    _assert_pending(approval)

    approval.status = ApprovalStatus.rejected
    approval.reviewed_by = current_user.id
    approval.notes = decision.notes
    approval.reviewed_at = datetime.utcnow()
    approval.contract.status = ContractStatus.rejected

    db.add(AuditLog(
        contract_id=approval.contract_id,
        user_id=current_user.id,
        action="CONTRACT_REJECTED",
        details=f"Rejected by {current_user.email}. Reason: {decision.notes or 'None'}",
    ))
    await db.commit()
    await db.refresh(approval)
    return _to_out(approval)


@router.post("/{approval_id}/request-changes")
async def request_changes(
    approval_id: str,
    decision: ApprovalDecision,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    approval = await _get_or_404(approval_id, db)
    _assert_pending(approval)
    approval.notes = f"CHANGES REQUESTED: {decision.notes}"
    db.add(AuditLog(
        contract_id=approval.contract_id,
        user_id=current_user.id,
        action="CHANGES_REQUESTED",
        details=decision.notes,
    ))
    await db.commit()
    return {"message": "Change request recorded."}


# ── Helpers ──────────────────────────────────────────────────

async def _get_or_404(approval_id: str, db: AsyncSession) -> Approval:
    a = (
        await db.execute(
            select(Approval)
            .options(selectinload(Approval.contract))
            .where(Approval.id == approval_id)
        )
    ).scalar_one_or_none()
    if not a:
        raise HTTPException(404, "Approval not found.")
    return a


def _assert_pending(approval: Approval) -> None:
    if approval.status != ApprovalStatus.pending:
        raise HTTPException(409, f"Approval is already '{approval.status}', cannot modify.")


def _to_out(a: Approval) -> ApprovalOut:
    return ApprovalOut(
        id=str(a.id),
        contract_id=str(a.contract_id),
        contract_name=a.contract.name if a.contract else "",
        contract_type=a.contract.contract_type if a.contract else "",
        risk_score=a.contract.risk_score if a.contract else None,
        risk_level=a.contract.risk_level if a.contract else None,
        requested_by=str(a.requested_by),
        reviewed_by=str(a.reviewed_by) if a.reviewed_by else None,
        status=a.status,
        notes=a.notes,
        conditions=a.conditions,
        created_at=a.created_at.isoformat(),
        reviewed_at=a.reviewed_at.isoformat() if a.reviewed_at else None,
    )
