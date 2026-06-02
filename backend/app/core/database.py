"""
Database — Async SQLAlchemy with asyncpg
Tables are pre-created via Supabase SQL Editor — no create_all needed.
NullPool prevents connection reuse across requests.
"""
import structlog
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool, StaticPool
from fastapi import HTTPException, status

from app.config import settings

logger = structlog.get_logger(__name__)


class Base(DeclarativeBase):
    pass


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

    # ── PostgreSQL (Supabase) ─────────────────────────────────
    # Normalize to asyncpg dialect
    pg_url = url
    if not pg_url.startswith("postgresql+asyncpg://"):
        pg_url = pg_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    # Remove any existing query params — add our own
    if "?" in pg_url:
        pg_url = pg_url.split("?")[0]
    # Add statement_cache_size=0 via URL parameter (asyncpg native)
    pg_url = pg_url + "?prepared_statement_cache_size=0"

    logger.info("Building PostgreSQL engine", url_prefix=pg_url[:50])

    return create_async_engine(
        pg_url,
        poolclass=NullPool,
        echo=settings.DEBUG,
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
