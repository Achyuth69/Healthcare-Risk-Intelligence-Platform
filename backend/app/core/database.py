"""
Database Configuration — Async SQLAlchemy
Uses NullPool for ALL PostgreSQL connections to avoid
PgBouncer / Supabase Transaction Pooler prepared statement conflicts.
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
    logger.info("Building DB engine", url_prefix=url[:30])

    # ── SQLite (local dev) ────────────────────────────────────
    if url.startswith("sqlite"):
        return create_async_engine(
            url,
            echo=settings.DEBUG,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

    # ── ALL PostgreSQL — NullPool + no prepared statements ────
    # NullPool: new connection per request, no pool reuse.
    # This is the ONLY safe option for Supabase Transaction Pooler
    # (PgBouncer in transaction mode bans prepared statements).
    return create_async_engine(
        url,
        poolclass=NullPool,
        echo=settings.DEBUG,
        execution_options={"no_parameters": True},
        connect_args={
            "ssl": "require",
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0,
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
        logger.error("DB session error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database error: {str(e)[:300]}",
        )
    finally:
        await session.close()
