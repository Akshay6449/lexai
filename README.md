# LexAI — Enterprise Contract Intelligence Platform

> Production-ready AI Contract Review Agent platform for enterprise legal teams.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     LexAI Platform                          │
├───────────────┬─────────────────────┬───────────────────────┤
│  Frontend     │  FastAPI Backend     │  AI Agent Layer       │
│  HTML/CSS/JS  │  REST API + WS       │  LangGraph Pipeline   │
│  Tailwind CSS │  JWT + RBAC          │  6 Specialized Agents │
├───────────────┴─────────────────────┴───────────────────────┤
│               Infrastructure Layer                          │
│  PostgreSQL  │  Qdrant Vector DB  │  Groq API  │ LangSmith  │
└─────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5, CSS3, Tailwind CSS, Vanilla JS |
| Backend | Python 3.11, FastAPI, Uvicorn |
| AI Orchestration | LangChain, LangGraph, LangSmith |
| LLM | Groq API (LLaMA 3.1 70B) |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 |
| Vector DB | Qdrant |
| Database | PostgreSQL 16 |
| Auth | JWT (RS256), RBAC |
| Docs | PDF (PyMuPDF), DOCX (python-docx) |
| Containerization | Docker, Docker Compose |
| CI/CD | GitHub Actions |

## Multi-Agent Pipeline

```
Document Upload
      │
      ▼
┌─────────────────┐
│ Agent 1:        │  PyMuPDF / python-docx
│ Doc Extraction  │  Chunk + tokenize
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Agent 2:        │  Groq LLaMA 3.1 70B
│ Clause Classify │  8 clause types
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Agent 3:        │  Qdrant ANN search
│ RAG Retrieval   │  SentenceTransformers
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Agent 4:        │  Risk score 0–100
│ Risk Analysis   │  4 risk levels
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Agent 5:        │  Clause rewrites
│ Recommendations │  Business impact
└────────┬────────┘
         │
    Risk Score > 80?
       /        \
     Yes         No
      │           │
      ▼           ▼
┌──────────┐  ┌────────┐
│ Agent 6: │  │  Done  │
│ Approval │  │ Report │
│ Workflow │  └────────┘
└──────────┘
```

## Roles & Permissions

| Permission | Legal Reviewer | Legal Manager | Admin |
|-----------|---------------|--------------|-------|
| Upload contracts | ✓ | ✓ | ✓ |
| View analysis | ✓ | ✓ | ✓ |
| Comment on clauses | ✓ | ✓ | ✓ |
| Approve/Reject | ✗ | ✓ | ✓ |
| Manage users | ✗ | ✗ | ✓ |
| Manage playbooks | ✗ | ✓ | ✓ |
| View audit logs | ✗ | ✓ | ✓ |
| System config | ✗ | ✗ | ✓ |

## Quick Start

```bash
# 1. Clone and configure
git clone https://github.com/yourorg/lexai.git
cd lexai
cp .env.example .env
# Fill in GROQ_API_KEY, LANGSMITH_API_KEY, JWT_PRIVATE_KEY

# 2. Start all services
docker compose up -d

# 3. Run migrations
docker compose exec api alembic upgrade head

# 4. Seed playbooks into Qdrant
docker compose exec api python -m scripts.seed_playbooks

# 5. Access
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
# Qdrant UI: http://localhost:6333/dashboard
```

## Environment Variables

```env
# AI
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.1-70b-versatile
LANGSMITH_API_KEY=ls__...
LANGSMITH_PROJECT=lexai-production

# Database
DATABASE_URL=postgresql+asyncpg://lexai:secret@postgres:5432/lexai

# Vector DB
QDRANT_URL=http://qdrant:6333
QDRANT_COLLECTION=lexai_playbooks

# Auth
JWT_PRIVATE_KEY_PATH=./keys/private.pem
JWT_PUBLIC_KEY_PATH=./keys/public.pem
JWT_ALGORITHM=RS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# App
SECRET_KEY=your-secret-key-min-32-chars
RISK_APPROVAL_THRESHOLD=80
MAX_UPLOAD_SIZE_MB=50
ALLOWED_EXTENSIONS=pdf,docx
RATE_LIMIT_PER_MINUTE=100
```
