# Tech Stack

## Why This Stack

LexAI combines a **FastAPI monolith** (UI + REST API), **PostgreSQL** (relational app data), **Qdrant** (playbook vector search), and a **LangGraph six-agent pipeline** (Groq LLM + local embeddings). Each piece solves a distinct problem: auth and workflows in SQL, semantic RAG in a vector DB, multi-step legal analysis in an orchestrated graph. LangSmith adds optional LLM tracing.

Full rationale, alternatives (e.g. pgvector vs Qdrant), and MVP scope notes: **[Design Rationale](design-rationale.md)**.

## Summary

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5, CSS3, Tailwind CSS, Vanilla JS (served by FastAPI at `/`) |
| Backend | Python 3.11+, FastAPI 0.138, Uvicorn, Pydantic 2.x |
| AI Orchestration | LangChain 0.3.x, LangGraph, LangSmith |
| LLM | Groq API (LLaMA 3.1 70B Versatile) |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 (384 dimensions) |
| Vector DB | Qdrant Cloud or local Qdrant |
| Database | PostgreSQL 16 |
| Auth | JWT (RS256), bcrypt passwords, RBAC |
| Document parsing | PyMuPDF (PDF), python-docx (DOCX) |

## Python Version

- **Recommended:** Python 3.11 or 3.12
- **Supported:** Python 3.13 (with pinned requirements in `backend/requirements.txt`)
- Use a virtual environment (`venv`) — never install deps globally

## Pinned Dependencies

From `backend/requirements.txt`:

### Core Framework

| Package | Version |
|---------|---------|
| fastapi | 0.138.0 |
| uvicorn[standard] | 0.34.0 |
| pydantic | 2.10.6 |
| pydantic-settings | 2.10.1 |
| email-validator | 2.2.0 |

### Database

| Package | Version |
|---------|---------|
| sqlalchemy | 2.0.50 |
| asyncpg | 0.31.0 |
| alembic | 1.15.2 |

### Auth

| Package | Version |
|---------|---------|
| python-jose[cryptography] | 3.4.0 |
| bcrypt | 4.2.1 |
| passlib[bcrypt] | 1.7.4 |

### AI / LangChain

| Package | Version |
|---------|---------|
| langchain | 0.3.30 |
| langchain-groq | 0.2.4 |
| langchain-community | 0.3.30 |
| langgraph | 0.2.76 |
| langsmith | 0.3.45 |

### Vector DB & Embeddings

| Package | Version |
|---------|---------|
| qdrant-client | 1.13.2 |
| sentence-transformers | 3.4.1 |

### Document Processing

| Package | Version |
|---------|---------|
| PyMuPDF | 1.27.2 |
| python-docx | 1.1.2 |
| python-multipart | 0.0.20 |

### Utilities

| Package | Version |
|---------|---------|
| httpx | 0.28.1 |
| aiofiles | 24.1.0 |
| python-dotenv | 1.1.0 |
| structlog | 25.1.0 |

### Testing

| Package | Version |
|---------|---------|
| pytest | 8.3.5 |
| pytest-asyncio | 0.25.3 |
| pytest-cov | 6.0.0 |
| factory-boy | 3.3.3 |

## External Services

| Service | Required | Purpose |
|---------|----------|---------|
| **PostgreSQL 16** | Yes | Primary application database |
| **Groq API** | Yes | LLM inference for agents 2, 4, 5, 6 |
| **Qdrant** | Yes (for RAG) | Playbook vector similarity search |
| **LangSmith** | No | Optional tracing and observability |

## Why LangChain 0.3.x?

The codebase uses LangChain 0.3-style imports (`from langchain.prompts import ChatPromptTemplate`). Upgrading to LangChain 1.x requires code migration and is intentionally deferred.

## Related Docs

- [Design Rationale](design-rationale.md) — why each technology was chosen
- [Configuration](configuration.md) — API keys and env vars
- [Getting Started](getting-started.md) — install dependencies
