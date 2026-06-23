# Getting Started

First-time local setup for LexAI on Windows. Linux/macOS steps are similar — adjust paths and shell syntax.

## Prerequisites

Before you begin, ensure you have:

- [ ] **Python 3.11+** installed ([python.org](https://www.python.org/downloads/))
- [ ] **PostgreSQL 16** running locally
- [ ] **Groq API key** from [console.groq.com](https://console.groq.com)
- [ ] **Qdrant Cloud** cluster or local Qdrant ([cloud.qdrant.io](https://cloud.qdrant.io))
- [ ] **OpenSSL** (included with Git for Windows, or install separately)
- [ ] **Git** (to clone the repository)

## Step 1: Clone the Repository

```powershell
git clone <repo-url>
cd lexai
```

## Step 2: Create the PostgreSQL Database

```powershell
psql -U postgres -c "CREATE DATABASE lexai;"
```

If `psql` is not on your PATH, use pgAdmin: right-click **Databases** → **Create** → name it `lexai`.

## Step 3: Python Virtual Environment

```powershell
cd backend
py -3.13 -m venv venv
.\venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

Installation may take several minutes — `sentence-transformers` pulls in PyTorch.

## Step 4: Configure Environment

```powershell
copy ..\.env.example .env
```

Edit `backend/.env` and set these required values:

| Variable | Example | Where to get it |
|----------|---------|-----------------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/lexai` | Your Postgres credentials |
| `GROQ_API_KEY` | `gsk_...` | Groq console |
| `QDRANT_URL` | `https://xxx.cloud.qdrant.io` | Qdrant Cloud dashboard |
| `QDRANT_API_KEY` | `eyJ...` | Qdrant Cloud → API Keys |
| `SECRET_KEY` | 32+ random characters | Generate any secure string |

See [Configuration](configuration.md) for the full variable reference.

## Step 5: Generate JWT Keys

```powershell
mkdir keys
openssl genrsa -out keys/private.pem 2048
openssl rsa -in keys/private.pem -pubout -out keys/public.pem
```

Keys must exist at the paths specified in `JWT_PRIVATE_KEY_PATH` and `JWT_PUBLIC_KEY_PATH` (default: `./keys/`).

## Step 6: Start the API

```powershell
uvicorn main:app --reload --port 8000
```

On first startup, `init_db()` creates all PostgreSQL tables automatically.

You should see log output indicating the database connected successfully.

## Step 7: Seed Data

Open a **second terminal**, activate the venv, and run:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m scripts.seed
```

This creates:

- 3 login users (admin, manager, reviewer)
- Playbooks in PostgreSQL and Qdrant
- 3 demo contracts with clauses and audit logs

See [Seed Data](seed-data.md) for details.

## Step 8: Verify

| Check | URL / Action | Expected |
|-------|--------------|----------|
| Health | http://localhost:8000/health | `{"status":"ok",...}` |
| UI loads | http://localhost:8000/ | Login page (no 500 error) |
| Login | `admin@lexai.com` / `Admin@1234` | Dashboard loads |
| API docs | http://localhost:8000/docs | Swagger UI |

## Default Seed Logins

| Email | Password | Role |
|-------|----------|------|
| admin@lexai.com | Admin@1234 | Admin |
| manager@lexai.com | Admin@1234 | Legal Manager |
| reviewer@lexai.com | Admin@1234 | Legal Reviewer |

## Next Steps

- [UI Walkthrough](ui-walkthrough.md) — tour the web app screen by screen
- [Daily Commands](daily-commands.md) — routine development workflow
- [Troubleshooting](troubleshooting.md) — if something fails
- [API Reference](api-reference.md) — explore the REST API
