"""
Patient Model — Encrypted PII fields, clinical data
SQLite-compatible (uses JSON instead of JSONB, String UUID)
"""
from typing import Optional
from sqlalchemy import String, Float, Integer, Text, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class Patient(Base, UUIDMixin, TimestampMixin):
    """
    Core patient record.
    PII fields (ssn, dob) are stored encrypted via Fernet AES.
    """
    __tablename__ = "patients"

    # ── Encrypted PII ─────────────────────────────────────────
    encrypted_ssn: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    encrypted_dob: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Demographics ──────────────────────────────────────────
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    gender: Mapped[str] = mapped_column(String(20), nullable=False)
    ethnicity: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    zip_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # ── Vitals ────────────────────────────────────────────────
    bmi: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    blood_pressure_systolic: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    blood_pressure_diastolic: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    heart_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    glucose_level: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hba1c: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cholesterol_total: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cholesterol_ldl: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cholesterol_hdl: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    triglycerides: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # ── Lifestyle ─────────────────────────────────────────────
    smoking_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    alcohol_use: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    physical_activity_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # ── Medical History ───────────────────────────────────────
    has_diabetes: Mapped[bool] = mapped_column(Boolean, default=False)
    has_hypertension: Mapped[bool] = mapped_column(Boolean, default=False)
    has_heart_disease: Mapped[bool] = mapped_column(Boolean, default=False)
    has_kidney_disease: Mapped[bool] = mapped_column(Boolean, default=False)
    family_history_diabetes: Mapped[bool] = mapped_column(Boolean, default=False)
    family_history_heart_disease: Mapped[bool] = mapped_column(Boolean, default=False)

    # ── Medications ───────────────────────────────────────────
    medications: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<Patient id={self.id} age={self.age} gender={self.gender}>"
