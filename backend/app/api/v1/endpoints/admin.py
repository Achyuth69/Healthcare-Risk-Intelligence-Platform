"""
Admin Endpoints — User management, model status, audit logs, platform stats
"""
import structlog
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from app.core.database import get_db
from app.core.rbac import require_role, Role, TokenData
from app.models.user import User
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
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return result.scalars().all()


@router.get("/models/status")
async def get_model_status(
    current_user: TokenData = Depends(require_role(Role.ADMIN, Role.RESEARCHER)),
):
    registry = ModelRegistry.get_instance()
    return registry.get_status()


@router.get("/audit-logs")
async def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_role(Role.ADMIN)),
):
    result = await db.execute(
        select(AuditLog).order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
    )
    logs = result.scalars().all()
    return {"logs": logs, "total": len(logs)}


@router.get("/stats")
async def get_platform_stats(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_role(Role.ADMIN)),
):
    """Real-time platform statistics for the dashboard."""
    total_predictions = await db.scalar(select(func.count(PredictionRecord.id))) or 0
    total_patients    = await db.scalar(
        select(func.count(func.distinct(PredictionRecord.patient_id)))
    ) or 0
    total_users = await db.scalar(select(func.count(User.id))) or 0

    # Risk distribution
    risk_rows = await db.execute(
        select(PredictionRecord.risk_category, func.count(PredictionRecord.id))
        .group_by(PredictionRecord.risk_category)
    )
    risk_dist = {row[0]: row[1] for row in risk_rows}
    high_risk_count = risk_dist.get("high", 0) + risk_dist.get("critical", 0)

    # Disease breakdown
    disease_rows = await db.execute(
        select(
            PredictionRecord.disease_type,
            func.count(PredictionRecord.id).label("total"),
            func.count(PredictionRecord.id).filter(
                PredictionRecord.risk_category.in_(["high", "critical"])
            ).label("high_risk"),
            func.round((func.avg(PredictionRecord.risk_score) * 100).cast(
                __import__("sqlalchemy").Numeric(5, 1)
            ), 1).label("avg_risk"),
        ).group_by(PredictionRecord.disease_type)
    )
    disease_breakdown = [
        {
            "disease": row.disease_type,
            "predictions": row.total,
            "high_risk": row.high_risk,
            "avg_risk_pct": float(row.avg_risk or 0),
        }
        for row in disease_rows
    ]

    # Daily trend — last 14 days
    try:
        trend_rows = await db.execute(text("""
            SELECT DATE(created_at) AS day,
                   COUNT(*) AS predictions,
                   COUNT(*) FILTER (WHERE risk_category IN ('high','critical')) AS high_risk
            FROM prediction_records
            WHERE created_at >= NOW() - INTERVAL '14 days'
            GROUP BY DATE(created_at)
            ORDER BY day
        """))
        daily_trend = [
            {"day": str(row.day), "predictions": row.predictions, "high_risk": row.high_risk}
            for row in trend_rows
        ]
    except Exception:
        daily_trend = []

    # Role distribution
    role_rows = await db.execute(
        select(User.role, func.count(User.id)).group_by(User.role)
    )
    role_dist = {row[0]: row[1] for row in role_rows}

    return {
        "total_predictions": total_predictions,
        "total_patients":    total_patients,
        "total_users":       total_users,
        "high_risk_count":   high_risk_count,
        "risk_distribution": risk_dist,
        "disease_breakdown": disease_breakdown,
        "daily_trend":       daily_trend,
        "role_distribution": role_dist,
    }
