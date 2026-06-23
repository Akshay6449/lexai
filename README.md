# LexAI — Enterprise Contract Intelligence Platform

AI-powered contract review and risk analysis for enterprise legal teams. Upload PDF/DOCX contracts, run a 6-agent analysis pipeline, and route high-risk deals for legal manager approval.

## Quick Start

```powershell
cd backend
py -3.13 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy ..\.env.example .env    # edit with your keys
uvicorn main:app --reload --port 8000
python -m scripts.seed       # in a second terminal
```

Open http://localhost:8000/ and log in with `admin@lexai.com` / `Admin@1234`.

Full setup guide: **[docs/getting-started.md](docs/getting-started.md)**

## Documentation

All documentation lives in the **[docs/](docs/)** folder:

| Doc | Description |
|-----|-------------|
| [docs/README.md](docs/README.md) | Documentation index |
| [Overview](docs/overview.md) | Problem statement, use case, roles |
| [Architecture](docs/architecture.md) | System design and agent pipeline |
| [Getting Started](docs/getting-started.md) | First-time local setup |
| [API Reference](docs/api-reference.md) | REST endpoints |
| [Configuration](docs/configuration.md) | Environment variables |
| [Troubleshooting](docs/troubleshooting.md) | Common issues and fixes |

## Links

- **App UI:** http://localhost:8000/
- **API Docs:** http://localhost:8000/docs
- **Health:** http://localhost:8000/health

## Optional: Docker

For containerized deployment, see [docs/deployment.md](docs/deployment.md) and `docker-compose.yml`.
