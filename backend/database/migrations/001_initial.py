"""Initial schema — all LexAI tables

Revision ID: 001_initial
Revises: 
Create Date: 2025-06-12 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── users ─────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("admin", "legal_manager", "legal_reviewer", name="userrole"), nullable=False),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("last_login", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # ── contracts ─────────────────────────────────────────────
    op.create_table(
        "contracts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("contract_type", sa.Enum("NDA", "MSA", "SLA", "Vendor", "Employment", name="contracttype"), nullable=False),
        sa.Column("counterparty", sa.String(255), nullable=True),
        sa.Column("file_path", sa.String(1000), nullable=False),
        sa.Column("file_hash", sa.String(64), nullable=True, unique=True),
        sa.Column("file_size_bytes", sa.Integer, nullable=True),
        sa.Column("playbook", sa.String(255), nullable=True),
        sa.Column("status", sa.Enum("processing", "reviewed", "pending_approval", "approved", "rejected", "error", name="contractstatus"), server_default="processing"),
        sa.Column("risk_score", sa.Integer, nullable=True),
        sa.Column("risk_level", sa.Enum("low", "medium", "high", "critical", name="risklevel"), nullable=True),
        sa.Column("ai_confidence", sa.Float, nullable=True),
        sa.Column("executive_summary", sa.Text, nullable=True),
        sa.Column("langsmith_trace_id", sa.String(100), nullable=True),
        sa.Column("processing_duration_ms", sa.Integer, nullable=True),
        sa.Column("uploaded_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        sa.CheckConstraint("risk_score BETWEEN 0 AND 100", name="ck_contracts_risk_score"),
    )
    op.create_index("ix_contracts_status", "contracts", ["status"])
    op.create_index("ix_contracts_risk_level", "contracts", ["risk_level"])
    op.create_index("ix_contracts_created_at", "contracts", ["created_at"])

    # ── clauses ───────────────────────────────────────────────
    op.create_table(
        "clauses",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("contract_id", UUID(as_uuid=True), sa.ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("clause_type", sa.Enum("confidentiality", "liability", "indemnification", "termination", "payment", "data_privacy", "intellectual_property", "governing_law", name="clausetype"), nullable=False),
        sa.Column("section_reference", sa.String(50), nullable=True),
        sa.Column("original_text", sa.Text, nullable=False),
        sa.Column("suggested_text", sa.Text, nullable=True),
        sa.Column("risk_level", sa.Enum("low", "medium", "high", "critical", name="risklevel2"), nullable=True),
        sa.Column("risk_score", sa.Integer, nullable=True),
        sa.Column("confidence_score", sa.Float, nullable=True),
        sa.Column("explanation", sa.Text, nullable=True),
        sa.Column("business_impact", sa.Text, nullable=True),
        sa.Column("rag_source", sa.String(500), nullable=True),
        sa.Column("rag_similarity", sa.Float, nullable=True),
        sa.Column("qdrant_vector_id", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.CheckConstraint("risk_score BETWEEN 0 AND 100", name="ck_clauses_risk_score"),
    )
    op.create_index("ix_clauses_contract_id", "clauses", ["contract_id"])
    op.create_index("ix_clauses_clause_type", "clauses", ["clause_type"])

    # ── approvals ─────────────────────────────────────────────
    op.create_table(
        "approvals",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("contract_id", UUID(as_uuid=True), sa.ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("requested_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("reviewed_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("status", sa.Enum("pending", "approved", "rejected", "approved_with_conditions", name="approvalstatus"), server_default="pending"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("conditions", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("reviewed_at", sa.DateTime, nullable=True),
    )
    op.create_index("ix_approvals_status", "approvals", ["status"])

    # ── playbooks ─────────────────────────────────────────────
    op.create_table(
        "playbooks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("contract_type", sa.Enum("NDA", "MSA", "SLA", "Vendor", "Employment", name="contracttype2"), nullable=True),
        sa.Column("clause_count", sa.Integer, server_default="0"),
        sa.Column("qdrant_synced", sa.Boolean, server_default="false"),
        sa.Column("last_synced_at", sa.DateTime, nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    # ── playbook_clauses ──────────────────────────────────────
    op.create_table(
        "playbook_clauses",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("playbook_id", UUID(as_uuid=True), sa.ForeignKey("playbooks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("clause_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("standard_text", sa.Text, nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("qdrant_vector_id", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # ── audit_logs ────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("contract_id", UUID(as_uuid=True), sa.ForeignKey("contracts.id", ondelete="CASCADE"), nullable=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("agent_name", sa.String(100), nullable=True),
        sa.Column("action", sa.Text, nullable=False),
        sa.Column("details", sa.Text, nullable=True),
        sa.Column("duration_ms", sa.Integer, nullable=True),
        sa.Column("tokens_used", sa.Integer, nullable=True),
        sa.Column("langsmith_trace_id", sa.String(100), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_audit_logs_contract_id", "audit_logs", ["contract_id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("playbook_clauses")
    op.drop_table("playbooks")
    op.drop_table("approvals")
    op.drop_table("clauses")
    op.drop_table("contracts")
    op.drop_table("users")
    for enum in ["userrole", "contracttype", "contracttype2", "contractstatus",
                 "risklevel", "risklevel2", "clausetype", "approvalstatus"]:
        op.execute(f"DROP TYPE IF EXISTS {enum}")
