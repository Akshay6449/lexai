# Project Structure

## Repository Layout

```
lexai/
├── backend/                 # FastAPI application (primary codebase)
│   ├── agents/              # Six AI agents + LangGraph pipeline
│   ├── api/routes/          # REST API route modules
│   ├── auth/                # JWT handler, password hashing, RBAC
│   ├── core/                # Config, database models, rate limiter
│   ├── database/migrations/ # Alembic migration file (not wired yet)
│   ├── rag/                 # Qdrant client and embedding helpers
│   ├── scripts/             # Seed scripts for local development
│   ├── templates/           # HTML UI (contract-review-platform.html)
│   ├── tests/               # pytest test suite
│   ├── keys/                # JWT RSA keys (gitignored, create locally)
│   ├── uploads/             # Contract file uploads (runtime)
│   ├── main.py              # FastAPI app entry point
│   └── requirements.txt     # Python dependencies
├── docker/                  # Dockerfiles and nginx config
├── docs/                    # This documentation
├── frontend/                # Standalone frontend (Docker build)
├── .env.example             # Environment template
├── docker-compose.yml       # Optional containerized deployment
└── README.md                # Project hub (links to docs/)
```

## Backend Packages

### `agents/`

| File | Purpose |
|------|---------|
| `pipeline.py` | LangGraph orchestration — wires all six agents |
| `document_extraction_agent.py` | Agent 1: PDF/DOCX parsing and chunking |
| `clause_classification_agent.py` | Agent 2: Groq-based clause classification |
| `rag_retrieval_agent.py` | Agent 3: Qdrant similarity search |
| `risk_analysis_agent.py` | Agent 4: Per-clause and contract risk scoring |
| `recommendation_agent.py` | Agent 5: Clause rewrite suggestions |
| `approval_workflow_agent.py` | Agent 6: Executive summary and approval routing |

### `api/routes/`

| Module | Prefix | Purpose |
|--------|--------|---------|
| `auth.py` | `/api/v1/auth` | Login, refresh, me, logout |
| `users.py` | `/api/v1/users` | User CRUD (admin) |
| `contracts.py` | `/api/v1/contracts` | Upload, list, get, delete |
| `analysis.py` | `/api/v1/analysis` | Clauses, risk, audit, summary |
| `approvals.py` | `/api/v1/approvals` | Approval workflow actions |
| `playbooks.py` | `/api/v1/playbooks` | Playbook management + Qdrant stats |
| `dashboard.py` | `/api/v1/dashboard` | Aggregated stats and activity |

### `auth/`

- `jwt_handler.py` — RS256 token creation/validation, `get_current_user`, role guards (`require_admin`, `require_manager`, `require_any_legal`)

### `core/`

| File | Purpose |
|------|---------|
| `config.py` | Pydantic Settings loaded from `backend/.env` |
| `database.py` | SQLAlchemy engine, ORM models, `init_db()` |
| `rate_limiter.py` | Per-IP request rate limiting |

### `rag/`

- `qdrant_client.py` — `get_qdrant_client()`, collection init, upsert, search, stats

### `scripts/`

| Script | Purpose |
|--------|---------|
| `seed.py` | Master seed runner |
| `seed_users.py` | Default admin/manager/reviewer accounts |
| `seed_playbooks_db.py` | Postgres playbook rows |
| `seed_playbooks.py` | Qdrant vector upsert |
| `seed_demo_data.py` | Sample contracts and audit logs |
| `seed_data.py` | Shared playbook clause constants |

### `templates/`

- `contract-review-platform.html` — Single-page contract review UI served at `GET /`

## Entry Point

`backend/main.py`:

- Creates FastAPI app with lifespan (`init_db()` on startup)
- Registers middleware (CORS, rate limit, request logging)
- Mounts API routers under `/api/v1/*`
- Serves UI at `GET /`
- Exposes `GET /health` and Swagger at `/docs`

## Related Docs

- [Architecture](architecture.md) — how components interact
- [API Reference](api-reference.md) — endpoint details
