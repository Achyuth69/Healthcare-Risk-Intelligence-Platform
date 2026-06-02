"""
Healthcare Risk Intelligence Platform — FastAPI Application Entry Point
Production-grade setup with middleware, monitoring, and lifecycle management.
"""
import time
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import settings
from app.core.database import engine, Base
from app.core.logging import configure_logging
from app.api.v1.router import api_router
from app.core.exceptions import HealthRiskException

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown hooks."""
    configure_logging()
    logger.info("Starting Healthcare Risk Intelligence Platform",
                version=settings.APP_VERSION, env=settings.APP_ENV)

    # ── Database (non-fatal — app still starts if DB unreachable) ──
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized")
        await _seed_admin()
    except Exception as e:
        logger.error("DB init failed — running without DB (check DATABASE_URL)", error=str(e))

    # ── ML Models ─────────────────────────────────────────────
    from app.ml.model_registry import ModelRegistry
    await ModelRegistry.initialize()
    logger.info("ML models loaded into registry")

    # ── RAG Pipeline ──────────────────────────────────────────
    try:
        from app.rag.pipeline import RAGPipeline
        await RAGPipeline.initialize()
        logger.info("RAG pipeline initialized")
    except Exception as e:
        logger.warning("RAG pipeline init skipped (mock mode)", error=str(e))

    # ── LLM Engine ────────────────────────────────────────────
    try:
        from app.ml.llm.inference import LLMInferenceEngine
        await LLMInferenceEngine.initialize()
        logger.info("LLM engine initialized")
    except Exception as e:
        logger.warning("LLM engine init skipped (mock mode)", error=str(e))

    yield

    logger.info("Shutting down Healthcare Risk Intelligence Platform")
    await engine.dispose()


def create_application() -> FastAPI:
    app = FastAPI(
        title="Healthcare Risk Intelligence Platform",
        description=(
            "Production-grade Explainable AI platform for disease risk prediction "
            "with SHAP/LIME explanations, fine-tuned LLM, and RAG-powered clinical insights."
        ),
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── Middleware ────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_allowed_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # ── Request Timing Middleware ─────────────────────────────
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        response.headers["X-Process-Time"] = f"{duration:.4f}"
        return response

    # ── Exception Handlers ────────────────────────────────────
    @app.exception_handler(HealthRiskException)
    async def health_risk_exception_handler(request: Request, exc: HealthRiskException):
        logger.warning("Domain exception", detail=exc.detail, code=exc.error_code)
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.error_code, "detail": exc.detail},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception", exc_info=exc, path=request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "INTERNAL_ERROR", "detail": "An unexpected error occurred."},
        )

    # ── Prometheus Metrics ────────────────────────────────────
    Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/health", "/metrics"],
    ).instrument(app).expose(app, endpoint="/metrics")

    # ── Routers ───────────────────────────────────────────────
    app.include_router(api_router, prefix="/api/v1")

    # ── Health Check ─────────────────────────────────────────
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV,
        }

    return app


app = create_application()


async def _seed_admin():
    """Create default admin user if none exists."""
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    from app.core.security import hash_password
    from app.models.user import User

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.email == "admin@healthrisk.ai")
        )
        if result.scalar_one_or_none() is None:
            admin = User(
                email="admin@healthrisk.ai",
                hashed_password=hash_password("Admin@123!"),
                full_name="System Administrator",
                role="admin",
                is_active=True,
                is_verified=True,
            )
            session.add(admin)
            await session.commit()
            logger.info("Default admin user created", email="admin@healthrisk.ai")
