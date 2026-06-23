# LexAI Documentation

Welcome to the LexAI documentation. This folder is the single source of truth for architecture, setup, API usage, and operations.

## Table of Contents

| Document | Description |
|----------|-------------|
| [Overview](overview.md) | Problem statement, use case, roles, and permissions |
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

## Recommended Reading Order

### New developers

1. [Overview](overview.md)
2. [Architecture](architecture.md)
3. [Getting Started](getting-started.md)
4. [UI Walkthrough](ui-walkthrough.md)
5. [Project Structure](project-structure.md)
6. [AI Agents](ai-agents.md)
7. [API Reference](api-reference.md)

### Operators / DevOps

1. [Getting Started](getting-started.md)
2. [Configuration](configuration.md)
3. [Seed Data](seed-data.md)
4. [RAG and Qdrant](rag-and-qdrant.md)
5. [Troubleshooting](troubleshooting.md)
6. [Deployment](deployment.md)

## Quick Links

- **App UI:** http://localhost:8000/
- **Swagger API:** http://localhost:8000/docs
- **Health check:** http://localhost:8000/health
