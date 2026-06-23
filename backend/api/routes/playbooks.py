"""Playbooks API — CRUD + Qdrant sync."""
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from auth.jwt_handler import require_manager, require_any_legal, require_admin
from core.database import AsyncSession, get_db, Playbook, PlaybookClause, User

router = APIRouter()


class PlaybookOut(BaseModel):
    id: str
    name: str
    description: Optional[str]
    contract_type: Optional[str]
    clause_count: int
    qdrant_synced: bool
    last_synced_at: Optional[str]
    updated_at: str


class PlaybookCreate(BaseModel):
    name: str
    description: Optional[str] = None
    contract_type: Optional[str] = None


@router.get("", response_model=list[PlaybookOut])
async def list_playbooks(
    current_user: User = Depends(require_any_legal),
    db: AsyncSession = Depends(get_db),
):
    results = (await db.execute(select(Playbook).order_by(Playbook.name))).scalars().all()
    return [_to_out(p) for p in results]


@router.post("", response_model=PlaybookOut, status_code=201)
async def create_playbook(
    payload: PlaybookCreate,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    pb = Playbook(**payload.model_dump(), created_by=current_user.id)
    db.add(pb)
    await db.commit()
    await db.refresh(pb)
    return _to_out(pb)


@router.post("/{playbook_id}/sync")
async def sync_to_qdrant(
    playbook_id: str,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    return {"message": "Qdrant sync disabled in local mode."}


@router.get("/qdrant/stats")
async def qdrant_stats(current_user: User = Depends(require_any_legal)):
    return {"message": "Qdrant disabled in local mode.", "vectors_count": 0}


def _to_out(p: Playbook) -> PlaybookOut:
    return PlaybookOut(
        id=str(p.id), name=p.name, description=p.description,
        contract_type=p.contract_type, clause_count=p.clause_count,
        qdrant_synced=p.qdrant_synced,
        last_synced_at=p.last_synced_at.isoformat() if p.last_synced_at else None,
        updated_at=p.updated_at.isoformat(),
    )
