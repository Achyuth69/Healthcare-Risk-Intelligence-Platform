"""
Database Configuration — Async SQLAlchemy
- SQLite  for local dev
- psycopg (psycopg3) for Supabase/PostgreSQL in production
  psycopg3 does NOT use prepared statements by default → no PgBouncer conflict
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
    logger.info("Building DB engine", prefix=url[:35])

    # ── SQLite (local dev) ────────────────────────────────────
    if url.startswith("sqlite"):
        return create_async_engine(
            url,
            echo=settings.DEBUG,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

    # ── PostgreSQL (production) ───────────────────────────────
    # Convert asyncpg URL → psycopg URL
    # asyncpg: postgresql+asyncpg://...
    # psycopg: postgresql+psycopg://...
    pg_url = url.replace("postgresql+asyncpg://", "postgresql+psycopg://")
    if not pg_url.startswith("postgresql+psycopg://"):
        pg_url = pg_url.replace("postgresql://", "postgresql+psycopg://", 1)

    logger.info("Using psycopg3 driver (no prepared statement conflicts)")

    return create_async_engine(
        pg_url,
        poolclass=NullPool,       # fresh connection per request
        echo=settings.DEBUG,
        connect_args={
            "sslmode": "require",
            "prepare_threshold": None,  # disable server-side prepared statements
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
