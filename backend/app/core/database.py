"""
Database Configuration — Async SQLAlchemy with asyncpg
Supabase Transaction Pooler fix:
  Add ?prepared_statement_cache_size=0 to the URL
  This disables asyncpg prepared statement caching at the URL level
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
    logger.info("Building DB engine", prefix=url[:40])

    # ── SQLite (local dev) ────────────────────────────────────
    if url.startswith("sqlite"):
        return create_async_engine(
            url,
            echo=settings.DEBUG,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

    # ── PostgreSQL via Supabase Transaction Pooler ────────────
    # Ensure asyncpg driver prefix
    if "postgresql://" in url and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # Append prepared_statement_cache_size=0 to disable prepared statements
    # This is the asyncpg URL-level parameter — overrides everything
    if "prepared_statement_cache_size" not in url:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}prepared_statement_cache_size=0"

    logger.info("PostgreSQL URL ready", has_cache_disable="prepared_statement_cache_size=0" in url)

    return create_async_engine(
        url,
        poolclass=NullPool,   # no connection reuse — safest for PgBouncer
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
