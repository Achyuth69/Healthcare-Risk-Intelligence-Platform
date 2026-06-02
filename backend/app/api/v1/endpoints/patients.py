"""
Patient Endpoints — CRUD with encrypted PII
"""
import structlog
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.rbac import require_permission, Permission, TokenData
from app.core.exceptions import NotFoundException
from app.core.security import encrypt_field, decrypt_field
from app.models.patient import Patient
from app.schemas.prediction import PatientFeatures

router = APIRouter()
logger = structlog.get_logger(__name__)


class PatientCreateRequest(PatientFeatures):
    ssn: Optional[str] = None
    dob: Optional[str] = None


class PatientResponse(BaseModel):
    id: str
    age: int
    gender: str
    bmi: Optional[float] = None
    blood_pressure_systolic: Optional[float] = None
    blood_pressure_diastolic: Optional[float] = None
    glucose_level: Optional[float] = None
    hba1c: Optional[float] = None
    has_diabetes: bool
    has_hypertension: bool
    has_heart_disease: bool
    has_kidney_disease: bool
    family_history_diabetes: bool
    family_history_heart_disease: bool

    model_config = {"from_attributes": True}


@router.post("/", response_model=PatientResponse, status_code=201)
async def create_patient(
    payload: PatientCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_permission(Permission.PATIENT_WRITE)),
):
    """Create a new patient record with encrypted PII."""
    patient = Patient(
        **payload.model_dump(exclude={"ssn", "dob"}),
        encrypted_ssn=encrypt_field(payload.ssn) if payload.ssn else None,
        encrypted_dob=encrypt_field(payload.dob) if payload.dob else None,
    )
    db.add(patient)
    await db.flush()
    await db.refresh(patient)
    logger.info("Patient created", patient_id=str(patient.id))
    return patient


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_permission(Permission.PATIENT_READ)),
):
    """Retrieve a patient by ID."""
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise NotFoundException(f"Patient {patient_id} not found.")
    return patient


@router.get("/", response_model=List[PatientResponse])
async def list_patients(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_permission(Permission.PATIENT_READ)),
):
    """List patients with pagination."""
    result = await db.execute(
        select(Patient).offset(skip).limit(limit).order_by(Patient.created_at.desc())
    )
    return result.scalars().all()


@router.delete("/{patient_id}", status_code=204)
async def delete_patient(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_permission(Permission.PATIENT_DELETE)),
):
    """Delete a patient record (GDPR right to erasure)."""
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise NotFoundException(f"Patient {patient_id} not found.")
    await db.delete(patient)
    logger.info("Patient deleted", patient_id=patient_id, by=current_user.user_id)
