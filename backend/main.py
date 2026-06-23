"""
LexAI — FastAPI Application Entry Point
"""
import time
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from core.config import settings
from core.database import init_db
from core.rate_limiter import RateLimiter
from api.routes import auth, contracts, analysis, approvals, playbooks, dashboard, users

logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting LexAI platform...")
    await init_db()
    logger.info("LexAI platform ready.")
    yield
    logger.info("Shutting down LexAI platform.")


app = FastAPI(
    title="LexAI Contract Intelligence API",
    description="Enterprise AI-powered contract review and risk analysis platform.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # for local testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"],   # for local testing; later use settings.ALLOWED_HOSTS
)

rate_limiter = RateLimiter(requests_per_minute=settings.RATE_LIMIT_PER_MINUTE)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    if not await rate_limiter.is_allowed(client_ip):
        return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded."})
    return await call_next(request)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    logger.info(f"{request.method} {request.url.path} → {response.status_code} ({duration_ms}ms)")
    response.headers["X-Response-Time"] = f"{duration_ms}ms"
    return response


# ── UI Route ──────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def serve_ui(request: Request):
    return templates.TemplateResponse("contract-review-platform.html", {"request": request})


# ── API Routes ────────────────────────────────────────────────

app.include_router(auth.router,       prefix="/api/v1/auth",       tags=["Auth"])
app.include_router(users.router,      prefix="/api/v1/users",      tags=["Users"])
app.include_router(contracts.router,  prefix="/api/v1/contracts",  tags=["Contracts"])
app.include_router(analysis.router,   prefix="/api/v1/analysis",   tags=["Analysis"])
app.include_router(approvals.router,  prefix="/api/v1/approvals",  tags=["Approvals"])
app.include_router(playbooks.router,  prefix="/api/v1/playbooks",  tags=["Playbooks"])
app.include_router(dashboard.router,  prefix="/api/v1/dashboard",  tags=["Dashboard"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "version": "1.0.0", "service": "lexai-api"}