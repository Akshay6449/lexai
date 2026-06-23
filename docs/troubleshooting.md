# Troubleshooting

Common issues when running LexAI locally and how to fix them.

## Installation

### `pip install` fails on PyMuPDF

**Symptom:** Build error mentioning Visual Studio or `Unable to find Visual Studio`.

**Cause:** Old PyMuPDF version without a pre-built wheel for your Python version.

**Fix:** Use the pinned version in `requirements.txt` (`PyMuPDF==1.27.2`) with Python 3.11+. Alternatively use Python 3.11 instead of 3.13.

### `asyncpg` build fails

**Symptom:** C compilation errors during `pip install asyncpg`.

**Fix:** Upgrade to `asyncpg>=0.31.0` (pinned in requirements) which has Python 3.13 wheels.

### `email-validator` import error on startup

**Symptom:**

```
ImportError: email-validator is not installed, run `pip install pydantic[email]`
```

**Fix:**

```powershell
pip install email-validator
```

Already listed in `requirements.txt` — reinstall if missing.

## Application Startup

### `GET /` returns 500 Internal Server Error

**Symptom:** Health check works but the UI at `/` crashes.

**Cause:** Starlette 1.x changed `TemplateResponse` argument order.

**Fix:** Ensure `main.py` uses:

```python
return templates.TemplateResponse(request, "contract-review-platform.html")
```

### Database connection refused

**Symptom:**

```
Database connection failed: connection refused
```

**Fix:**

1. Start PostgreSQL service
2. Verify `DATABASE_URL` in `backend/.env` matches your host, port, user, password
3. Confirm database `lexai` exists: `psql -U postgres -c "\l"`

### `database "lexai" does not exist`

**Fix:**

```powershell
psql -U postgres -c "CREATE DATABASE lexai;"
```

### JWT / login errors

**Symptom:** `FileNotFoundError` for `keys/private.pem` or invalid token errors.

**Fix:** Generate RSA keys:

```powershell
cd backend
mkdir keys
openssl genrsa -out keys/private.pem 2048
openssl rsa -in keys/private.pem -pubout -out keys/public.pem
```

## Authentication

### Login returns 401 Invalid credentials

**Cause:** No users in the database.

**Fix:**

```powershell
python -m scripts.seed
```

Default login: `admin@lexai.com` / `Admin@1234`

### Login returns 403 Account deactivated

**Cause:** User `is_active` is false.

**Fix:** Update via admin API or re-seed users.

### Login or seed returns 500 — timezone / datetime error

**Symptom:**

```
asyncpg.exceptions.DataError: can't subtract offset-naive and offset-aware datetimes
```

Often on `POST /api/v1/auth/login` (updating `last_login`) or during `python -m scripts.seed` when syncing Qdrant vector IDs.

**Cause:** PostgreSQL columns use `TIMESTAMP WITHOUT TIME ZONE`. The ORM stores **naive UTC** datetimes (`datetime.utcnow()`). Passing timezone-aware values (e.g. `datetime.now(timezone.utc)`) into those columns makes asyncpg fail on UPDATE/INSERT.

**Fix:** Use naive UTC for any value written to a `DateTime` column:

```python
from datetime import datetime

# Correct for DB columns
now = datetime.utcnow()

# Avoid for DB columns
# datetime.now(timezone.utc)
```

Affected areas in the codebase: login (`last_login`), approval review (`reviewed_at`), playbook sync (`last_synced_at`), and seed scripts. JWT token claims may still use timezone-aware datetimes — those are not persisted to Postgres.

If you see this error after pulling an older branch, restart uvicorn so route changes reload.

## Qdrant

### Qdrant connection or auth failed

**Symptom:** Warnings in logs: `[Qdrant] Startup check failed` or upsert returns 0 vectors.

**Fix:**

1. Set `QDRANT_URL` to your cluster URL (not `http://qdrant:6333` unless using Docker)
2. Set `QDRANT_API_KEY` for Qdrant Cloud
3. Verify cluster is running in Qdrant Cloud dashboard

### RAG always returns stub matches

**Cause:** Qdrant unreachable or collection empty.

**Fix:**

1. Run `python -m scripts.seed` or `python -m scripts.seed_playbooks`
2. Check stats: `GET /api/v1/playbooks/qdrant/stats` (with auth token)

### Qdrant client version mismatch warning

**Symptom:** Log warning on startup or seed:

```
Qdrant client version X.Y.Z is incompatible with server version A.B.C
```

**Cause:** Local `qdrant-client` package version differs from your Qdrant Cloud cluster version.

**Fix:** Usually non-fatal — upserts and search still work. To silence the warning, bump `qdrant-client` in `requirements.txt` to a version closer to your cluster, or pass `check_version=False` in `get_qdrant_client()` (already optional in code).

## Testing

### `ModuleNotFoundError: No module named 'auth'`

**Cause:** pytest run from wrong directory without Python path set.

**Fix:** Run from `backend/` directory. A `pytest.ini` with `pythonpath = .` is included — see [Testing](testing.md).

## Performance

### First request is very slow

**Cause:** `sentence-transformers` downloads and loads the embedding model on first use.

**Fix:** Normal on first run. Subsequent requests are faster. Model is cached locally after download.

### `pip install` takes a long time

**Cause:** PyTorch (~120 MB+) is installed as a dependency of `sentence-transformers`.

**Fix:** Expected behavior. Wait for install to complete.

## Still Stuck?

1. Check server logs in the uvicorn terminal
2. Hit http://localhost:8000/health to confirm API is up
3. Review [Getting Started](getting-started.md) verification checklist
4. Open an issue with the full error traceback
