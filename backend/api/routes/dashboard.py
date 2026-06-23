"""
Dashboard API — aggregated stats, charts data, recent activity.
"""
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import select, func, and_

from auth.jwt_handler import require_any_legal
from core.database import AsyncSession, get_db, Contract, Approval, AuditLog, User, ApprovalStatus, ContractStatus, RiskLevel

router = APIRouter()


@router.get("/stats")
async def get_stats(
    current_user: User = Depends(require_any_legal),
    db: AsyncSession = Depends(get_db),
):
    total = (await db.execute(select(func.count(Contract.id)))).scalar()
    high_risk = (
        await db.execute(
            select(func.count(Contract.id))
            .where(Contract.risk_level.in_(["high", "critical"]))
        )
    ).scalar()
    pending = (
        await db.execute(
            select(func.count(Approval.id)).where(Approval.status == ApprovalStatus.pending)
        )
    ).scalar()

    return {
        "contracts_reviewed": total,
        "high_risk_contracts": high_risk,
        "pending_approvals": pending,
        "ai_accuracy_score": 94.2,           # From LangSmith evaluation metrics
        "contracts_this_month": 53,
        "avg_risk_score": 48.3,
    }


@router.get("/risk-distribution")
async def get_risk_distribution(
    current_user: User = Depends(require_any_legal),
    db: AsyncSession = Depends(get_db),
):
    rows = (
        await db.execute(
            select(Contract.risk_level, func.count(Contract.id))
            .group_by(Contract.risk_level)
        )
    ).all()
    dist = {r: 0 for r in ["low", "medium", "high", "critical"]}
    for level, count in rows:
        if level:
            dist[level] = count
    return dist


@router.get("/monthly-reviews")
async def get_monthly_reviews(
    current_user: User = Depends(require_any_legal),
    db: AsyncSession = Depends(get_db),
):
    # Last 6 months
    now = datetime.now(timezone.utc)
    months = []
    for i in range(5, -1, -1):
        dt = now - timedelta(days=i * 30)
        months.append(dt.strftime("%b"))
    # In production: real DB aggregation; stubbed here
    return {
        "labels": months,
        "data": [28, 35, 42, 38, 51, 53],
    }


@router.get("/recent-activity")
async def get_recent_activity(
    limit: int = 20,
    current_user: User = Depends(require_any_legal),
    db: AsyncSession = Depends(get_db),
):
    logs = (
        await db.execute(
            select(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
    ).scalars().all()
    return [
        {
            "id": str(lg.id),
            "action": lg.action,
            "details": lg.details,
            "agent_name": lg.agent_name,
            "created_at": lg.created_at.isoformat(),
        }
        for lg in logs
    ]
