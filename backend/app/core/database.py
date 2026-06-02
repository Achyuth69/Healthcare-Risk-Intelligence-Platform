"""
Database Configuration — Async SQLAlchemy
Supports:
  - SQLite   (local dev)         sqlite+aiosqlite:///./healthrisk_dev.db
  - Supabase (production/Render) postgresql+asyncpg://...pooler.supabase.com:6543/postgres
  - Render PG (alternative)      postgresql+asyncpg://...render.com/healthrisk_db
"""
import structlog
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
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

    # ── PostgreSQL via Supabase Transaction Pooler (port 6543) ─
    # Pooler requires statement_cache_size=0 for asyncpg
    if "pooler.supabase.com" in url or "6543" in url:
        return create_async_engine(
            url,
            pool_size=3,
            max_overflow=5,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=settings.DEBUG,
            connect_args={
                "ssl": "require",
                "statement_cache_size": 0,     # required for PgBouncer/Supabase pooler
                "server_settings": {"search_path": "public"},
            },
        )

    # ── Standard PostgreSQL (Render internal, AWS RDS, etc.) ───
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


async def get_db() -> AsyncSession:
    """
    FastAPI dependency — yields an async database session.
    Returns HTTP 503 with a clear message if the database is unreachable.
    """
    try:
        async with AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Database connection failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Database unavailable. "
                "Ensure DATABASE_URL uses Supabase Transaction Pooler port 6543: "
                "postgresql+asyncpg://postgres.YOUR_REF:PASS"
                "@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"
            ),
        )
