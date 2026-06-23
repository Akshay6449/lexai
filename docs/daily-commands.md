# Daily Commands

Quick reference for everyday LexAI development after [initial setup](getting-started.md).

## Start Your Session

```powershell
cd C:\mytools\lexai\backend
.\venv\Scripts\Activate.ps1
```

## Start the Dev Server

```powershell
uvicorn main:app --reload --port 8000
```

- `--reload` watches for code changes and auto-restarts
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs

## Seed Data

```powershell
# Full seed (users + playbooks + Qdrant + demo contracts) — safe to re-run
python -m scripts.seed

# Qdrant playbook vectors only
python -m scripts.seed_playbooks

# Users only
python -m scripts.seed_users
```

## Run Tests

```powershell
pytest tests/ -v

# With coverage report
pytest tests/ -v --cov=. --cov-report=term-missing
```

See [Testing](testing.md) for details.

## Database

```powershell
# Connect via psql
psql -U postgres -d lexai

# List tables
\dt

# Check users
SELECT email, role FROM users;
```

## Useful API Calls

Replace `TOKEN` with a JWT from login.

```powershell
# Health (no auth)
curl http://localhost:8000/health

# Login
curl -X POST http://localhost:8000/api/v1/auth/login `
  -H "Content-Type: application/json" `
  -d '{"email":"admin@lexai.com","password":"Admin@1234"}'

# Qdrant stats (auth required)
curl http://localhost:8000/api/v1/playbooks/qdrant/stats `
  -H "Authorization: Bearer TOKEN"
```

## Stop the Server

Press `Ctrl+C` in the terminal running uvicorn.

## Related Docs

- [Getting Started](getting-started.md) — first-time setup
- [Troubleshooting](troubleshooting.md) — common issues
