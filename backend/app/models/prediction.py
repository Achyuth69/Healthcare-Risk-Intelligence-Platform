"""
Prediction Record Model — Stores ML predictions and explanations
"""
import uuid
from typing import Optional
from sqlalchemy import String, Float, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class PredictionRecord(Base, UUIDMixin, TimestampMixin):
    """
    Stores every prediction made, including model used,
    risk score, confidence, and full SHAP/LIME explanations.
    """
    __tablename__ = "prediction_records"

    # ── Foreign Keys ──────────────────────────────────────────
    patient_id: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True, index=True
    )
    requested_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    # ── Prediction Details ────────────────────────────────────
    disease_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    model_type: Mapped[str] = mapped_column(String(50), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0.0")

    # ── Risk Scores ───────────────────────────────────────────
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_category: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    # ── Input Features (snapshot at prediction time) ──────────
    input_features: Mapped[dict] = mapped_column(JSON, nullable=False)

    # ── Explanations ──────────────────────────────────────────
    shap_values: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    lime_explanation: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    feature_importance: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # ── LLM Narrative ─────────────────────────────────────────
    llm_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<PredictionRecord id={self.id} "
            f"disease={self.disease_type} "
            f"risk={self.risk_score:.3f}>"
        )


class AuditLog(Base, UUIDMixin, TimestampMixin):
    """Immutable audit trail for all sensitive operations."""
    __tablename__ = "audit_logs"

    user_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
