"""
Healthcare Risk Intelligence Platform — FastAPI Application Entry Point
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
    configure_logging()
    logger.info("Starting HealthRisk AI", version=settings.APP_VERSION, env=settings.APP_ENV)

    # DB — non-fatal startup
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized")
        await _seed_admin()
    except Exception as e:
        logger.error("DB init failed — check DATABASE_URL env var", error=str(e))
        logger.warning("App starting WITHOUT database — auth/predictions will return 503")
    # ML Models
    from app.ml.model_registry import ModelRegistry
    await ModelRegistry.initialize()
    logger.info("ML models loaded")

    # RAG Pipeline
    try:
        from app.rag.pipeline import RAGPipeline
        await RAGPipeline.initialize()
        logger.info("RAG pipeline ready")
    except Exception as e:
        logger.warning("RAG mock mode", error=str(e))

    # LLM Engine
    try:
        from app.ml.llm.inference import LLMInferenceEngine
        await LLMInferenceEngine.initialize()
        logger.info("LLM engine ready")
    except Exception as e:
        logger.warning("LLM mock mode", error=str(e))

    yield

    logger.info("Shutting down")
    await engine.dispose()


def create_application() -> FastAPI:
    app = FastAPI(
        title="Healthcare Risk Intelligence Platform",
        description="Explainable AI for disease risk prediction.",
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── CORS — allow ALL origins (required for Vercel ↔ Render) ──
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,   # must be False when allow_origins=["*"]
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Request timing
    @app.middleware("http")
    async def add_process_time(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Process-Time"] = f"{(time.perf_counter()-start):.4f}"
        return response

    # Domain exception handler
    @app.exception_handler(HealthRiskException)
    async def domain_exc(request: Request, exc: HealthRiskException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.error_code, "detail": exc.detail},
        )

    # Catch-all exception handler
    @app.exception_handler(Exception)
    async def generic_exc(request: Request, exc: Exception):
        logger.error("Unhandled error", exc_info=exc, path=request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "INTERNAL_ERROR", "detail": "An unexpected error occurred."},
        )

    # Prometheus
    Instrumentator(
        should_group_status_codes=True,
        excluded_handlers=["/health", "/metrics"],
    ).instrument(app).expose(app, endpoint="/metrics")

    # Routes
    app.include_router(api_router, prefix="/api/v1")

    # Health check
    @app.get("/health", tags=["Health"])
    async def health():
        return {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV,
            "build": "asyncpg-connect-args-v7",
        }

    @app.get("/db-test", tags=["Health"])
    async def db_test():
        from urllib.parse import urlparse
        url = settings.DATABASE_URL
        try:
            p = urlparse(url)
            safe_url = f"{p.scheme}://{p.username}:***@{p.hostname}:{p.port}{p.path}"
        except Exception:
            safe_url = "parse error"
        try:
            async with engine.connect() as conn:
                from sqlalchemy import text
                await conn.execute(text("SELECT 1"))
            "build": "asyncpg-connect-args-v7"}
        except Exception as e:
            return {"database": "failed", "url_used": safe_url, "error": str(e), "build": "asyncpg-connect-args-v7"}

    return app


app = create_application()


async def _seed_admin():
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
            logger.info("Admin user created")
