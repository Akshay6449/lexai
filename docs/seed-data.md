# Seed Data

LexAI includes idempotent seed scripts for local development. All scripts skip records that already exist — safe to re-run.

## Master Command

```powershell
cd backend
python -m scripts.seed
```

Runs four steps in order:

1. **Users** — admin, manager, reviewer accounts
2. **Playbooks (PostgreSQL)** — playbook and clause rows
3. **Playbooks (Qdrant)** — vector embeddings + sync vector IDs to Postgres
4. **Demo contracts** — sample contracts, clauses, approvals, audit logs

## Individual Scripts

| Command | What it seeds |
|---------|---------------|
| `python -m scripts.seed` | Everything (master) |
| `python -m scripts.seed_users` | Login accounts only |
| `python -m scripts.seed_playbooks_db` | Postgres playbooks only |
| `python -m scripts.seed_playbooks` | Qdrant vectors only |
| `python -m scripts.seed_demo_data` | Demo contracts only |

## Default Login Accounts

| Email | Password | Role |
|-------|----------|------|
| admin@lexai.com | Admin@1234 | admin |
| manager@lexai.com | Admin@1234 | legal_manager |
| reviewer@lexai.com | Admin@1234 | legal_reviewer |

Password for all accounts: **Admin@1234** (matches UI quick-login buttons).

Created by `scripts/seed_users.py` using bcrypt via `hash_password()`.

## Playbook Data

Shared constants in `scripts/seed_data.py`:

| Playbook | Contract Type | Clauses |
|----------|---------------|---------|
| NDA Standards | NDA | 4 (liability, confidentiality, termination, governing law) |
| MSA Standards | MSA | 4 (indemnification, IP, payment, data privacy) |
| SLA Standards | SLA | 2 (liability, termination) |

Postgres rows go to `playbooks` and `playbook_clauses` tables.
Vectors go to Qdrant collection `lexai_playbooks`.

## Demo Contracts

Created by `scripts/seed_demo_data.py` and assigned to `reviewer@lexai.com`:

| Contract | Type | Status | Risk | Notes |
|----------|------|--------|------|-------|
| Acme Corp Mutual NDA | NDA | reviewed | 32 (low) | 2 clauses |
| TechVendor MSA — Cloud Services | MSA | pending_approval | 87 (critical) | 3 clauses, pending approval |
| GlobalHost SLA — Infrastructure | SLA | approved | 48 (medium) | 2 clauses |

Also creates audit log entries for dashboard recent activity.

## Idempotent Behavior

| Entity | Skip condition |
|--------|----------------|
| Users | Email already exists |
| Playbooks | Name already exists |
| Playbook clauses | Title exists under same playbook |
| Contracts | Name already exists |
| Qdrant vectors | Upserted each run (may duplicate vectors on re-seed) |

Re-running the full seed is safe for Postgres data. Qdrant may accumulate duplicate vectors if re-seeded repeatedly — delete the collection in Qdrant Cloud dashboard to reset.

## Prerequisites

Before seeding:

1. PostgreSQL `lexai` database exists
2. API has been started at least once (tables created via `init_db()`), **or** run seed after first uvicorn start
3. `QDRANT_URL` and `QDRANT_API_KEY` configured for vector seeding

Users and demo contracts only need Postgres. Qdrant step will log warnings if Qdrant is unreachable but other steps still succeed.

**Note:** Step 3 calls `sync_vector_ids()` to write `qdrant_vector_id` and `last_synced_at` back to Postgres. All timestamps in seed scripts use naive UTC to match the database schema.

## Creating Additional Users

After seeding, admins can create users via API:

```http
POST /api/v1/users
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "email": "newuser@lexai.com",
  "full_name": "New User",
  "password": "SecurePass123!",
  "role": "legal_reviewer"
}
```

## Related Docs

- [Getting Started](getting-started.md) — when to run seed
- [Database](database.md) — table schemas
- [RAG and Qdrant](rag-and-qdrant.md) — vector seeding detail
