"""
Contracts API — upload, list, get, delete.
File validation, SHA-256 dedup, async agent trigger.
"""
import hashlib
import logging
import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import select, desc, delete
from sqlalchemy.orm import selectinload

from auth.jwt_handler import get_current_user, require_any_legal
from core.config import settings
from core.database import (
    AsyncSession, get_db, Contract, ContractStatus, ContractType,
    RiskLevel, User, AuditLog, Clause
)

router = APIRouter()
logger = logging.getLogger(__name__)


# ── Schemas ──────────────────────────────────────────────────

class ContractSummary(BaseModel):
    id: str
    name: str
    contract_type: str
    counterparty: Optional[str]
    status: str
    risk_score: Optional[int]
    risk_level: Optional[str]
    ai_confidence: Optional[float]
    created_at: str
    clause_count: int = 0

    class Config:
        from_attributes = True


class ContractDetail(ContractSummary):
    executive_summary: Optional[str]
    langsmith_trace_id: Optional[str]
    processing_duration_ms: Optional[int]


# ── Helpers ──────────────────────────────────────────────────

def _validate_file(file: UploadFile) -> None:
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: .{ext}. Allowed: {settings.ALLOWED_EXTENSIONS}")


async def _read_and_hash(file: UploadFile) -> tuple[bytes, str]:
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit.")
    return content, hashlib.sha256(content).hexdigest()


def _save_file(content: bytes, filename: str, file_hash: str) -> str:
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{file_hash[:12]}_{uuid.uuid4().hex[:8]}_{Path(filename).name}"
    path = upload_dir / safe_name
    path.write_bytes(content)
    return str(path)


# ── Routes ───────────────────────────────────────────────────

@router.post("/upload", response_model=ContractDetail, status_code=201)
async def upload_contract(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    contract_type: str = Form(...),
    counterparty: Optional[str] = Form(None),
    playbook: Optional[str] = Form(None),
    current_user: User = Depends(require_any_legal),
    db: AsyncSession = Depends(get_db),
):
    _validate_file(file)
    content, file_hash = await _read_and_hash(file)

    # Deduplication check
    existing = (
        await db.execute(select(Contract).where(Contract.file_hash == file_hash))
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(409, "Duplicate contract: this file has already been uploaded.")

    # Validate contract type enum
    try:
        ct = ContractType(contract_type)
    except ValueError:
        raise HTTPException(400, f"Invalid contract_type. Must be one of: {[e.value for e in ContractType]}")

    file_path = _save_file(content, file.filename, file_hash)

    contract = Contract(
        name=file.filename,
        contract_type=ct,
        counterparty=counterparty,
        file_path=file_path,
        file_hash=file_hash,
        file_size_bytes=len(content),
        playbook=playbook or "Standard Corporate Playbook",
        status=ContractStatus.processing,
        uploaded_by=current_user.id,
    )
    db.add(contract)
    db.add(AuditLog(
        contract_id=contract.id,
        user_id=current_user.id,
        action="CONTRACT_UPLOADED",
        details=f"File: {file.filename} ({len(content)//1024}KB)",
    ))
    await db.flush()

    # Kick off AI pipeline asynchronously
    background_tasks.add_task(_run_agent_pipeline, str(contract.id), file_path, ct.value)

    await db.commit()
    contract = await _get_or_404(str(contract.id), db)
    return _to_detail(contract)


async def _run_agent_pipeline(contract_id: str, file_path: str, contract_type: str):
    """Background task — runs the full LangGraph agent pipeline."""
    try:
        from agents.pipeline import run_contract_pipeline
        await run_contract_pipeline(contract_id, file_path, contract_type)
    except Exception:
        logger.exception(f"[Pipeline] Background task failed for contract {contract_id}")


def _authorize_contract_mutation(contract: Contract, user: User) -> None:
    if str(contract.uploaded_by) != str(user.id) and user.role != "admin":
        raise HTTPException(403, "Not authorized to modify this contract.")


@router.post("/{contract_id}/analyze", response_model=ContractDetail)
async def reanalyze_contract(
    contract_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_any_legal),
    db: AsyncSession = Depends(get_db),
):
    contract = await _get_or_404(contract_id, db)
    _authorize_contract_mutation(contract, current_user)

    if not os.path.exists(contract.file_path):
        raise HTTPException(404, "Contract file not found on disk. Re-upload the document.")

    await db.execute(delete(Clause).where(Clause.contract_id == contract.id))
    contract.status = ContractStatus.processing
    contract.risk_score = None
    contract.risk_level = None
    contract.executive_summary = None
    contract.ai_confidence = None
    contract.langsmith_trace_id = None
    contract.processing_duration_ms = None
    await db.flush()

    background_tasks.add_task(
        _run_agent_pipeline,
        str(contract.id),
        contract.file_path,
        contract.contract_type.value,
    )
    await db.commit()
    contract = await _get_or_404(contract_id, db)
    return _to_detail(contract)


@router.get("", response_model=list[ContractSummary])
async def list_contracts(
    status: Optional[str] = None,
    risk_level: Optional[str] = None,
    contract_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(require_any_legal),
    db: AsyncSession = Depends(get_db),
):
    q = select(Contract).options(selectinload(Contract.clauses)).order_by(desc(Contract.created_at))
    if status:
        q = q.where(Contract.status == status)
    if risk_level:
        q = q.where(Contract.risk_level == risk_level)
    if contract_type:
        q = q.where(Contract.contract_type == contract_type)
    q = q.limit(limit).offset(offset)
    results = (await db.execute(q)).scalars().all()
    return [_to_summary(c) for c in results]


@router.get("/{contract_id}", response_model=ContractDetail)
async def get_contract(
    contract_id: str,
    current_user: User = Depends(require_any_legal),
    db: AsyncSession = Depends(get_db),
):
    contract = await _get_or_404(contract_id, db)
    return _to_detail(contract)


@router.delete("/{contract_id}", status_code=204)
async def delete_contract(
    contract_id: str,
    current_user: User = Depends(require_any_legal),
    db: AsyncSession = Depends(get_db),
):
    contract = await _get_or_404(contract_id, db)
    _authorize_contract_mutation(contract, current_user)
    # Remove file
    if os.path.exists(contract.file_path):
        os.remove(contract.file_path)
    await db.delete(contract)
    await db.commit()


# ── Helpers ──────────────────────────────────────────────────

async def _get_or_404(contract_id: str, db: AsyncSession) -> Contract:
    c = (
        await db.execute(
            select(Contract)
            .options(selectinload(Contract.clauses))
            .where(Contract.id == contract_id)
        )
    ).scalar_one_or_none()
    if not c:
        raise HTTPException(404, "Contract not found.")
    return c


def _to_summary(c: Contract) -> ContractSummary:
    return ContractSummary(
        id=str(c.id),
        name=c.name,
        contract_type=c.contract_type,
        counterparty=c.counterparty,
        status=c.status,
        risk_score=c.risk_score,
        risk_level=c.risk_level,
        ai_confidence=c.ai_confidence,
        created_at=c.created_at.isoformat(),
        clause_count=len(c.clauses) if c.clauses else 0,
    )


def _to_detail(c: Contract) -> ContractDetail:
    return ContractDetail(
        **_to_summary(c).__dict__,
        executive_summary=c.executive_summary,
        langsmith_trace_id=c.langsmith_trace_id,
        processing_duration_ms=c.processing_duration_ms,
    )
