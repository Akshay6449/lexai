# Database

LexAI uses **PostgreSQL 16** as the primary data store. All ORM models are defined in `backend/core/database.py`.

## Schema Overview

```mermaid
erDiagram
  users ||--o{ contracts : uploads
  users ||--o{ approvals : requests
  users ||--o{ playbooks : creates
  contracts ||--o{ clauses : contains
  contracts ||--o| approvals : has
  contracts ||--o{ audit_logs : logs
  playbooks ||--o{ playbook_clauses : contains
```

## Tables

### `users`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | Primary key |
| email | string(255) | Unique, indexed |
| full_name | string(255) | |
| password_hash | string(255) | bcrypt hash |
| role | enum | `admin`, `legal_manager`, `legal_reviewer` |
| is_active | boolean | Default true |
| last_login | datetime | Nullable |
| created_at | datetime | |
| updated_at | datetime | |

### `contracts`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | Primary key |
| name | string(500) | |
| contract_type | enum | NDA, MSA, SLA, Vendor, Employment |
| counterparty | string(255) | Nullable |
| file_path | string(1000) | Path to uploaded file |
| file_hash | string(64) | SHA-256 for deduplication |
| file_size_bytes | int | Nullable |
| playbook | string(255) | Nullable — matched playbook name |
| status | enum | See ContractStatus below |
| risk_score | int | 0–100 |
| risk_level | enum | low, medium, high, critical |
| ai_confidence | float | Nullable |
| executive_summary | text | Nullable |
| langsmith_trace_id | string(100) | Nullable |
| processing_duration_ms | int | Nullable |
| uploaded_by | UUID | FK → users.id |
| created_at | datetime | Indexed |
| updated_at | datetime | |

### `clauses`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | Primary key |
| contract_id | UUID | FK → contracts.id (CASCADE delete) |
| clause_type | enum | See ClauseType below |
| section_reference | string(50) | e.g. "Section 8.2" |
| original_text | text | |
| suggested_text | text | Nullable — AI rewrite |
| risk_level | enum | Nullable |
| risk_score | int | 0–100 |
| confidence_score | float | Nullable |
| explanation | text | Nullable |
| business_impact | text | Nullable |
| rag_source | string(500) | Nullable — playbook reference |
| rag_similarity | float | Nullable |
| qdrant_vector_id | string(100) | Nullable |
| created_at | datetime | |

### `approvals`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | Primary key |
| contract_id | UUID | FK → contracts.id (unique, CASCADE) |
| requested_by | UUID | FK → users.id |
| reviewed_by | UUID | FK → users.id, nullable |
| status | enum | pending, approved, rejected, approved_with_conditions |
| notes | text | Nullable |
| conditions | text | Nullable |
| created_at | datetime | |
| reviewed_at | datetime | Nullable |

### `playbooks`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | Primary key |
| name | string(255) | |
| description | text | Nullable |
| contract_type | enum | Nullable |
| clause_count | int | Default 0 |
| qdrant_synced | boolean | Default false |
| last_synced_at | datetime | Nullable |
| created_by | UUID | FK → users.id, nullable |
| created_at | datetime | |
| updated_at | datetime | |

### `playbook_clauses`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | Primary key |
| playbook_id | UUID | FK → playbooks.id (CASCADE) |
| clause_type | enum | |
| title | string(255) | |
| standard_text | text | |
| notes | text | Nullable |
| qdrant_vector_id | string(100) | Nullable |
| created_at | datetime | |

### `audit_logs`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | Primary key |
| contract_id | UUID | FK → contracts.id, nullable |
| user_id | UUID | FK → users.id, nullable |
| agent_name | string(100) | Nullable |
| action | text | e.g. USER_LOGIN, CONTRACT_ANALYSIS_COMPLETE |
| details | text | Nullable — JSON or description |
| duration_ms | int | Nullable |
| tokens_used | int | Nullable |
| langsmith_trace_id | string(100) | Nullable |
| ip_address | string(45) | Nullable |
| created_at | datetime | Indexed |

## Enums

### UserRole

`admin` | `legal_manager` | `legal_reviewer`

### ContractType

`NDA` | `MSA` | `SLA` | `Vendor` | `Employment`

### ContractStatus

`processing` | `reviewed` | `pending_approval` | `approved` | `rejected` | `error`

**Lifecycle (summary):**

| From | To | Trigger |
|------|-----|---------|
| — | `processing` | Contract upload or re-analyze |
| `processing` | `reviewed` | AI pipeline completes; risk score below `RISK_APPROVAL_THRESHOLD` (default 80) |
| `processing` | `pending_approval` | AI pipeline completes; risk score at or above threshold; `Approval` row created |
| `processing` | `error` | Pipeline completes but no clauses saved (e.g. extraction/classification failure) |
| `pending_approval` | `approved` | Legal manager or admin approves via API |
| `pending_approval` | `rejected` | Legal manager or admin rejects via API |
| `error` | `processing` | User triggers re-analyze |

See [Architecture — Contract status lifecycle](architecture.md#contract-status-lifecycle) for the full diagram and UI mapping.

### RiskLevel

`low` | `medium` | `high` | `critical`

### ClauseType

`confidentiality` | `liability` | `indemnification` | `termination` | `payment` | `data_privacy` | `intellectual_property` | `governing_law`

### ApprovalStatus

`pending` | `approved` | `rejected` | `approved_with_conditions`

## Date and Time

All `DateTime` columns map to PostgreSQL `TIMESTAMP WITHOUT TIME ZONE`. The application stores **naive UTC** values:

- ORM defaults use `datetime.utcnow` for `created_at`, `updated_at`, etc.
- API routes and seed scripts must assign the same style when updating timestamps (`last_login`, `reviewed_at`, `last_synced_at`).

Do not mix timezone-aware datetimes (`datetime.now(timezone.utc)`) into these columns — asyncpg will raise `can't subtract offset-naive and offset-aware datetimes`. See [Troubleshooting](troubleshooting.md#login-or-seed-returns-500--timezone--datetime-error).

## Table Creation

Tables are created automatically on API startup via `init_db()` in `backend/core/database.py`, which calls `Base.metadata.create_all`.

There is an Alembic migration file at `backend/database/migrations/001_initial.py`, but **Alembic is not wired** (no `alembic.ini`). Schema changes currently require manual migration or recreating the database.

## Connection String

Async SQLAlchemy DSN format:

```
postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DATABASE
```

For GUI tools (pgAdmin, DBeaver), use the sync form:

```
postgresql://USER:PASSWORD@HOST:PORT/DATABASE
```

## Related Docs

- [Seed Data](seed-data.md) — populate tables with demo data
- [Configuration](configuration.md) — `DATABASE_URL` setting
