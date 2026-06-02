"""
Database Configuration — Async SQLAlchemy
Supabase Transaction Pooler requires:
  - statement_cache_size=0  (asyncpg connect_arg)
  - pool_pre_ping=False
  - no prepared statements
"""
import structlog
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
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
        )

    # ── Supabase Transaction Pooler (port 6543) ───────────────
    # PgBouncer transaction mode does NOT support prepared statements.
    # Fix: statement_cache_size=0 in asyncpg + NullPool in SQLAlchemy
    # NullPool = no connection reuse = no prepared statement conflicts
    if "pooler.supabase.com" in url or "6543" in url:
        return create_async_engine(
            url,
            poolclass=NullPool,           # new connection per request — safest for pooler
            echo=settings.DEBUG,
            connect_args={
                "ssl": "require",
                "statement_cache_size": 0,   # disable asyncpg prepared statement cache
            },
        )

    # ── Standard PostgreSQL (Render internal DB, AWS RDS) ─────
    return create_async_engine(
        url,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=300,
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
        logger.error("DB session error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database error: {str(e)[:300]}",
        )
    finally:
        await session.close()
