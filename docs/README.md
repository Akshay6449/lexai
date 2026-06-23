# LexAI Documentation

Welcome to the LexAI documentation. This folder is the single source of truth for architecture, setup, API usage, and operations.

## Table of Contents

| Document | Description |
|----------|-------------|
| [Overview](overview.md) | Problem statement, use case, roles, and permissions |
| [Design Rationale](design-rationale.md) | Why PostgreSQL, Qdrant, LangGraph, LangSmith, and six agents |
| [Architecture](architecture.md) | System layers, data flow, multi-agent pipeline |
| [Tech Stack](tech-stack.md) | Languages, frameworks, and pinned dependency versions |
| [Project Structure](project-structure.md) | Repository layout and package purposes |
| [Getting Started](getting-started.md) | First-time local setup (step-by-step) |
| [Daily Commands](daily-commands.md) | Day-to-day development workflow |
| [Configuration](configuration.md) | Environment variables reference |
| [Database](database.md) | PostgreSQL schema, enums, relationships |
| [API Reference](api-reference.md) | REST endpoints by module |
| [Authentication](authentication.md) | JWT, RBAC, login flow |
| [AI Agents](ai-agents.md) | Six-agent LangGraph pipeline |
| [RAG and Qdrant](rag-and-qdrant.md) | Vector search, embeddings, Qdrant Cloud |
| [Seed Data](seed-data.md) | Seed scripts, default logins, demo data |
| [Frontend](frontend.md) | Web UI served at `/` (technical reference) |
| [UI Walkthrough](ui-walkthrough.md) | Screen-by-screen guide to the web app |
| [Testing](testing.md) | Running pytest and test layout |
| [Troubleshooting](troubleshooting.md) | Common errors and fixes |
| [Deployment](deployment.md) | Optional Docker Compose deployment |

## Suggested Paths

Pick a path based on your goal. Each step builds on the previous one.

### Path A — First time on the project (recommended)

Run the app, then understand how it works.

| Step | Doc | Why read it |
|------|-----|-------------|
| 1 | [Overview](overview.md) | What LexAI does, who uses it, roles and permissions |
| 2 | [Getting Started](getting-started.md) | Install, configure `.env`, seed DB, start the server |
| 3 | [UI Walkthrough](ui-walkthrough.md) | Log in, upload a contract, explore dashboard and approvals |
| 4 | [Design Rationale](design-rationale.md) | Why PostgreSQL, Qdrant, LangGraph, six agents, LangSmith |
| 5 | [Architecture](architecture.md) | Layers, request lifecycle, pipeline diagram |
| 6 | [AI Agents](ai-agents.md) | What each of the six agents does |
| 7 | [Project Structure](project-structure.md) | Where code lives in the repo |
| 8 | [Daily Commands](daily-commands.md) | Commands you will use every day |

### Path B — Backend / API developer

After Path A steps 1–2 (or if the app already runs locally):

| Step | Doc | Why read it |
|------|-----|-------------|
| 1 | [Architecture](architecture.md) | System design and data flow |
| 2 | [Design Rationale](design-rationale.md) | Technology choices and tradeoffs |
| 3 | [Project Structure](project-structure.md) | Packages, routes, agents, scripts |
| 4 | [Database](database.md) | Tables, enums, relationships |
| 5 | [Authentication](authentication.md) | JWT, RBAC, login flow |
| 6 | [API Reference](api-reference.md) | REST endpoints by module |
| 7 | [AI Agents](ai-agents.md) | Pipeline stages and state |
| 8 | [RAG and Qdrant](rag-and-qdrant.md) | Embeddings, vector search, seeding |
| 9 | [Configuration](configuration.md) | All environment variables |
| 10 | [Testing](testing.md) | pytest layout and commands |

### Path C — Operators / DevOps

Get LexAI running in an environment and keep it healthy.

| Step | Doc | Why read it |
|------|-----|-------------|
| 1 | [Getting Started](getting-started.md) | Local baseline setup |
| 2 | [Configuration](configuration.md) | Postgres, Qdrant, Groq, JWT keys |
| 3 | [Seed Data](seed-data.md) | Users, playbooks, demo contracts |
| 4 | [RAG and Qdrant](rag-and-qdrant.md) | Qdrant Cloud vs local, vector seed |
| 5 | [Deployment](deployment.md) | Docker Compose (optional) |
| 6 | [Troubleshooting](troubleshooting.md) | Common errors and fixes |

### Path D — Product / legal stakeholder (no code)

Understand the product without diving into implementation.

| Step | Doc | Why read it |
|------|-----|-------------|
| 1 | [Overview](overview.md) | Problem, use case, roles |
| 2 | [UI Walkthrough](ui-walkthrough.md) | Screens and demo login flow |
| 3 | [Design Rationale](design-rationale.md) | Six-agent workflow in plain terms (§ Six Agents) |
| 4 | [Seed Data](seed-data.md) | Demo accounts and sample contracts |

### Quick reference (anytime)

| Need | Doc |
|------|-----|
| Env vars | [Configuration](configuration.md) |
| Dependency versions | [Tech Stack](tech-stack.md) |
| UI implementation | [Frontend](frontend.md) |
| Something broken | [Troubleshooting](troubleshooting.md) |

## Recommended Reading Order

Short lists if you prefer a minimal checklist.

### New developers

1. [Overview](overview.md) → 2. [Getting Started](getting-started.md) → 3. [UI Walkthrough](ui-walkthrough.md) → 4. [Design Rationale](design-rationale.md) → 5. [Architecture](architecture.md) → 6. [AI Agents](ai-agents.md) → 7. [Project Structure](project-structure.md) → 8. [API Reference](api-reference.md)

### Operators / DevOps

1. [Getting Started](getting-started.md) → 2. [Configuration](configuration.md) → 3. [Seed Data](seed-data.md) → 4. [RAG and Qdrant](rag-and-qdrant.md) → 5. [Troubleshooting](troubleshooting.md) → 6. [Deployment](deployment.md)

## Quick Links

- **App UI:** http://localhost:8000/
- **Swagger API:** http://localhost:8000/docs
- **Health check:** http://localhost:8000/health
