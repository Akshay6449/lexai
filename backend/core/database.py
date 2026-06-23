"""
Database engine, session factory, and all ORM models.
"""
import enum
import uuid
from datetime import datetime
from typing import AsyncGenerator

import logging
logger = logging.getLogger(__name__)

from sqlalchemy import (
    Column, String, Integer, Float, Text, Boolean,
    DateTime, Enum, ForeignKey, Index, CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, relationship

from core.config import settings


# ── Engine & Session ─────────────────────────────────────────

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    echo=settings.DEBUG,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database connected successfully.")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise


# ── Base ─────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


# ── Enums ────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    admin = "admin"
    legal_manager = "legal_manager"
    legal_reviewer = "legal_reviewer"


class ContractType(str, enum.Enum):
    NDA = "NDA"
    MSA = "MSA"
    SLA = "SLA"
    Vendor = "Vendor"
    Employment = "Employment"


class ContractStatus(str, enum.Enum):
    processing = "processing"
    reviewed = "reviewed"
    pending_approval = "pending_approval"
    approved = "approved"
    rejected = "rejected"
    error = "error"


class RiskLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class ClauseType(str, enum.Enum):
    confidentiality = "confidentiality"
    liability = "liability"
    indemnification = "indemnification"
    termination = "termination"
    payment = "payment"
    data_privacy = "data_privacy"
    intellectual_property = "intellectual_property"
    governing_law = "governing_law"


class ApprovalStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    approved_with_conditions = "approved_with_conditions"


# ── Models ───────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.legal_reviewer)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    contracts = relationship("Contract", back_populates="uploaded_by_user", foreign_keys="Contract.uploaded_by")
    approvals_reviewed = relationship("Approval", back_populates="reviewed_by_user", foreign_keys="Approval.reviewed_by")


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(500), nullable=False)
    contract_type = Column(Enum(ContractType), nullable=False)
    counterparty = Column(String(255), nullable=True)
    file_path = Column(String(1000), nullable=False)
    file_hash = Column(String(64), nullable=True)        # SHA-256 for dedup
    file_size_bytes = Column(Integer, nullable=True)
    playbook = Column(String(255), nullable=True)
    status = Column(Enum(ContractStatus), default=ContractStatus.processing, index=True)
    risk_score = Column(Integer, nullable=True)
    risk_level = Column(Enum(RiskLevel), nullable=True, index=True)
    ai_confidence = Column(Float, nullable=True)
    executive_summary = Column(Text, nullable=True)
    langsmith_trace_id = Column(String(100), nullable=True)
    processing_duration_ms = Column(Integer, nullable=True)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("risk_score BETWEEN 0 AND 100", name="risk_score_range"),
        Index("ix_contracts_status_risk", "status", "risk_level"),
    )

    uploaded_by_user = relationship("User", back_populates="contracts", foreign_keys=[uploaded_by])
    clauses = relationship("Clause", back_populates="contract", cascade="all, delete-orphan")
    approval = relationship("Approval", back_populates="contract", uselist=False)
    audit_logs = relationship("AuditLog", back_populates="contract", cascade="all, delete-orphan")


class Clause(Base):
    __tablename__ = "clauses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    clause_type = Column(Enum(ClauseType), nullable=False, index=True)
    section_reference = Column(String(50), nullable=True)    # e.g. "Section 8.2"
    original_text = Column(Text, nullable=False)
    suggested_text = Column(Text, nullable=True)
    risk_level = Column(Enum(RiskLevel), nullable=True)
    risk_score = Column(Integer, nullable=True)
    confidence_score = Column(Float, nullable=True)
    explanation = Column(Text, nullable=True)
    business_impact = Column(Text, nullable=True)
    rag_source = Column(String(500), nullable=True)
    rag_similarity = Column(Float, nullable=True)
    qdrant_vector_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("risk_score BETWEEN 0 AND 100", name="clause_risk_score_range"),
    )

    contract = relationship("Contract", back_populates="clauses")


class Approval(Base):
    __tablename__ = "approvals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.id", ondelete="CASCADE"), unique=True, nullable=False)
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.pending, index=True)
    notes = Column(Text, nullable=True)
    conditions = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)

    contract = relationship("Contract", back_populates="approval")
    requested_by_user = relationship("User", foreign_keys=[requested_by])
    reviewed_by_user = relationship("User", back_populates="approvals_reviewed", foreign_keys=[reviewed_by])


class Playbook(Base):
    __tablename__ = "playbooks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    contract_type = Column(Enum(ContractType), nullable=True)
    clause_count = Column(Integer, default=0)
    qdrant_synced = Column(Boolean, default=False)
    last_synced_at = Column(DateTime, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    clauses = relationship("PlaybookClause", back_populates="playbook", cascade="all, delete-orphan")


class PlaybookClause(Base):
    __tablename__ = "playbook_clauses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    playbook_id = Column(UUID(as_uuid=True), ForeignKey("playbooks.id", ondelete="CASCADE"), nullable=False)
    clause_type = Column(Enum(ClauseType), nullable=False)
    title = Column(String(255), nullable=False)
    standard_text = Column(Text, nullable=False)
    notes = Column(Text, nullable=True)
    qdrant_vector_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    playbook = relationship("Playbook", back_populates="clauses")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    agent_name = Column(String(100), nullable=True)
    action = Column(Text, nullable=False)
    details = Column(Text, nullable=True)       # JSON string for extra metadata
    duration_ms = Column(Integer, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    langsmith_trace_id = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    contract = relationship("Contract", back_populates="audit_logs")
