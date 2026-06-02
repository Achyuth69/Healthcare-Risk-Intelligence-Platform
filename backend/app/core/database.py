"""
Database — raw asyncpg pool with statement_cache_size=0
bypasses SQLAlchemy's asyncpg wrapper which ignores cache settings.
"""
import asyncpg
import structlog
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool, StaticPool
from fastapi import HTTPException, status

from app.config import settings

logger = structlog.get_logger(__name__)


class Base(DeclarativeBase):
    pass


def _get_pg_dsn() -> str:
    """Return a clean DSN for asyncpg (no driver prefix, no query params)."""
    url = settings.DATABASE_URL
    # Strip sqlalchemy driver prefix
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    # Strip any existing query params
    if "?" in url:
        url = url.split("?")[0]
    return url


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

    # ── PostgreSQL — use NullPool; actual connection via raw asyncpg ──
    pg_url = url
    if not pg_url.startswith("postgresql+asyncpg://"):
        pg_url = pg_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if "?" in pg_url:
        pg_url = pg_url.split("?")[0]

    async def _creator():
        dsn = _get_pg_dsn()
        return await asyncpg.connect(
            dsn,
            statement_cache_size=0,       # ← the actual fix
            prepared_statement_cache_size=0,
            ssl="require",
        )

    return create_async_engine(
        pg_url,
        poolclass=NullPool,
        echo=settings.DEBUG,
        creator=_creator,
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
