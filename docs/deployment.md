# Deployment

LexAI is designed for **local-first development**. Docker Compose is available for containerized deployment but is optional.

## Local Development (Recommended)

See [Getting Started](getting-started.md) for the primary setup path:

- Python venv + uvicorn
- Local PostgreSQL
- Qdrant Cloud or local Qdrant binary

## Docker Compose (Optional)

**File:** `docker-compose.yml`

### Services

| Service | Image / Build | Port | Purpose |
|---------|---------------|------|---------|
| `api` | `docker/Dockerfile.api` | 8000 | FastAPI backend |
| `frontend` | `docker/Dockerfile.frontend` | 3000 | Static frontend (nginx) |
| `postgres` | `postgres:16-alpine` | 5432 | PostgreSQL database |
| `qdrant` | `qdrant/qdrant:v1.11.1` | 6333 | Vector database |
| `nginx` | `nginx:1.27-alpine` | 80, 443 | Reverse proxy |
| `migrate` | api image | — | One-shot Alembic migration |
| `seed` | api image | — | One-shot playbook seeder |

### Quick Start (Docker)

```bash
cp .env.example .env
# Edit .env with secrets

docker compose up -d postgres qdrant
docker compose up -d api
docker compose run --rm seed
```

### Docker vs Local Differences

| Setting | Local | Docker Compose |
|---------|-------|----------------|
| `DATABASE_URL` host | `localhost` | `postgres` |
| `QDRANT_URL` | Cloud URL or `localhost:6333` | `http://qdrant:6333` |
| Python version | 3.11+ (your choice) | 3.11 (Dockerfile) |
| UI access | http://localhost:8000/ | http://localhost:3000 or :8000 |

### API Dockerfile

`docker/Dockerfile.api`:

- Multi-stage build (builder + runtime)
- Python 3.11-slim
- Pre-downloads embedding model at build time
- Runs uvicorn with 4 workers

### Frontend Dockerfile

`docker/Dockerfile.frontend`:

- Serves static HTML via nginx on port 80

## Production Considerations

1. **HTTPS** — terminate TLS at nginx or a load balancer
2. **Secrets** — use a secrets manager, not `.env` files in images
3. **Database** — managed PostgreSQL (RDS, Cloud SQL, etc.)
4. **Qdrant** — Qdrant Cloud for managed vector search
5. **CORS** — restrict `ALLOWED_ORIGINS` to your domain
6. **Rate limiting** — tune `RATE_LIMIT_PER_MINUTE` for production load
7. **JWT keys** — mount as secrets volumes, rotate periodically
8. **File uploads** — use persistent storage or object storage (S3) for `UPLOAD_DIR`

## CI/CD

GitHub Actions workflow may exist in `.github/workflows/` for automated testing and deployment. Check the repository for current pipeline configuration.

## Related Docs

- [Getting Started](getting-started.md) — local setup (primary path)
- [Configuration](configuration.md) — environment variables for each environment
- [Troubleshooting](troubleshooting.md) — common deployment issues
