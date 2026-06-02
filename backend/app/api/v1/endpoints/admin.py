"""
Admin Endpoints — User management, model status, audit logs, platform stats
"""
import structlog
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.rbac import require_role, Role, TokenData
from app.models.user import User
from app.models.patient import Patient
from app.models.prediction import PredictionRecord, AuditLog
from app.schemas.auth import UserResponse
from app.ml.model_registry import ModelRegistry

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_role(Role.ADMIN)),
):
    """List all registered users (admin only)."""
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return result.scalars().all()


@router.get("/models/status")
async def get_model_status(
    current_user: TokenData = Depends(require_role(Role.ADMIN, Role.RESEARCHER)),
):
    """Get status and metadata of all loaded ML models."""
    registry = ModelRegistry.get_instance()
    return registry.get_status()


@router.get("/audit-logs")
async def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_role(Role.ADMIN)),
):
    """Retrieve audit logs (admin only)."""
    result = await db.execute(
        select(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    logs = result.scalars().all()
    return {"logs": logs, "total": len(logs)}


@router.get("/stats")
async def get_platform_stats(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_role(Role.ADMIN)),
):
    """Platform-wide statistics for the dashboard."""
    total_predictions = await db.scalar(select(func.count(PredictionRecord.id)))
    total_patients    = await db.scalar(select(func.count(Patient.id)))
    total_users       = await db.scalar(select(func.count(User.id)))

    return {
        "total_predictions": total_predictions or 0,
        "total_patients":    total_patients    or 0,
        "total_users":       total_users       or 0,
    }
