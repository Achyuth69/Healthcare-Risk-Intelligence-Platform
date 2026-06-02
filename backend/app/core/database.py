"""
Database — asyncpg with prepared_statement_cache_size=0 hardcoded via creator.
This is the ONLY reliable way to disable prepared statements for Supabase pooler.
"""
import structlog
import asyncpg
from sqlalchemy.ext.asyncio import (
    AsyncSession, AsyncConnection,
    create_async_engine, async_sessionmaker
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool, StaticPool
from fastapi import HTTPException, status

from app.config import settings

logger = structlog.get_logger(__name__)


class Base(DeclarativeBase):
    pass


async def _asyncpg_connect(**kwargs):
    """
    Custom asyncpg connection factory.
    Forces prepared_statement_cache_size=0 regardless of URL parameters.
    This is the definitive fix for Supabase Transaction Pooler (PgBouncer).
    """
    kwargs.setdefault("statement_cache_size", 0)
    kwargs.setdefault("prepared_statement_cache_size", 0)
    return await asyncpg.connect(**kwargs)


def _build_engine():
    url = settings.DATABASE_URL

    # ── SQLite (local dev) ────────────────────────────────────
    if url.startswith("sqlite"):
        return create_async_engine(
            url,
            echo=settings.DEBUG,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

    # ── PostgreSQL (Supabase Transaction Pooler) ──────────────
    # Normalize to asyncpg URL
    pg_url = url
    if not pg_url.startswith("postgresql+asyncpg://"):
        pg_url = pg_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # Strip any existing query params — we handle them via creator
    if "?" in pg_url:
        pg_url = pg_url.split("?")[0]

    logger.info("Building PostgreSQL engine with prepared_statement_cache_size=0")

    return create_async_engine(
        pg_url,
        poolclass=NullPool,
        echo=settings.DEBUG,
        connect_args={
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0,
            "ssl": "require",
        },
    )


engine = _build_engine()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db():
    """FastAPI dependency — yields an async DB session."""
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except HTTPException:
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        logger.error("DB error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database error: {str(e)[:300]}",
        )
    finally:
        await session.close()
