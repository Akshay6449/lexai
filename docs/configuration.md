# Configuration

All settings are loaded from `backend/.env` via Pydantic Settings (`backend/core/config.py`). Copy `.env.example` to `backend/.env` and fill in your values.

**Never commit `backend/.env` to version control** — it contains secrets.

## App

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `APP_NAME` | string | `LexAI` | Application display name |
| `APP_ENV` | string | `production` | Environment label (`development`, `production`) |
| `DEBUG` | bool | `false` | Enable SQL echo and verbose logging |
| `SECRET_KEY` | string | **required** | App secret (min 32 characters) |
| `ALLOWED_ORIGINS` | list | `["http://localhost:3000", ...]` | CORS allowed origins (JSON array) |
| `ALLOWED_HOSTS` | list | `["*"]` | TrustedHost middleware allowed hosts |

## Database

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DATABASE_URL` | string | **required** | Async PostgreSQL DSN (`postgresql+asyncpg://...`) |
| `DB_POOL_SIZE` | int | `10` | SQLAlchemy connection pool size |
| `DB_MAX_OVERFLOW` | int | `20` | Max overflow connections beyond pool |

**Local example:**

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/lexai
```

## Vector DB (Qdrant)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `QDRANT_URL` | string | `http://qdrant:6333` | Qdrant cluster URL |
| `QDRANT_API_KEY` | string | `""` | API key (required for Qdrant Cloud) |
| `QDRANT_COLLECTION` | string | `lexai_playbooks` | Collection name for playbook vectors |
| `QDRANT_VECTOR_SIZE` | int | `384` | Embedding dimensions (must match model) |

**Qdrant Cloud example:**

```env
QDRANT_URL=https://your-cluster-id.cloud.qdrant.io
QDRANT_API_KEY=your-api-key-here
QDRANT_COLLECTION=lexai_playbooks
```

**Local Qdrant example:**

```env
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
```

## AI / Groq

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `GROQ_API_KEY` | string | **required** | Groq API key |
| `GROQ_MODEL` | string | `llama-3.3-70b-versatile` | LLM model for agents |
| `GROQ_TEMPERATURE` | float | `0.1` | Sampling temperature |
| `GROQ_MAX_TOKENS` | int | `4096` | Max tokens per LLM call |
| `EMBEDDING_MODEL` | string | `sentence-transformers/all-MiniLM-L6-v2` | Sentence embedding model |
| `EMBEDDING_BATCH_SIZE` | int | `32` | Batch size for embedding generation |

## LangSmith (Optional)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `LANGSMITH_API_KEY` | string | `""` | LangSmith API key (leave empty to disable) |
| `LANGSMITH_PROJECT` | string | `lexai-production` | LangSmith project name |
| `LANGSMITH_TRACING` | bool | `true` | Enable/disable trace export |

For local dev, set `LANGSMITH_TRACING=false` if you do not have a LangSmith key.

## Authentication

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `JWT_PRIVATE_KEY_PATH` | string | `./keys/private.pem` | RSA private key for signing |
| `JWT_PUBLIC_KEY_PATH` | string | `./keys/public.pem` | RSA public key for verification |
| `JWT_ALGORITHM` | string | `RS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | int | `60` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | int | `7` | Refresh token lifetime |

## File Upload

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MAX_UPLOAD_SIZE_MB` | int | `50` | Maximum upload file size |
| `ALLOWED_EXTENSIONS` | list | `["pdf", "docx"]` | Permitted file extensions |
| `UPLOAD_DIR` | string | `/tmp/lexai_uploads` | Directory for stored uploads |

**Local example:**

```env
UPLOAD_DIR=./uploads
```

## Risk & Rate Limiting

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `RISK_APPROVAL_THRESHOLD` | int | `80` | Contract risk score triggering approval workflow |
| `RATE_LIMIT_PER_MINUTE` | int | `100` | Per-IP API request limit |

## Security Notes

1. Rotate `SECRET_KEY` and API keys if they are ever exposed.
2. Use strong, unique passwords for PostgreSQL in production.
3. Restrict `ALLOWED_ORIGINS` and `ALLOWED_HOSTS` in production (not `*`).
4. Keep JWT private keys out of version control — `backend/keys/` should be gitignored.
5. Qdrant Cloud API keys grant full cluster access — treat as secrets.

## Related Docs

- [Getting Started](getting-started.md) — initial `.env` setup
- [RAG and Qdrant](rag-and-qdrant.md) — Qdrant Cloud configuration
- [Authentication](authentication.md) — JWT key generation
