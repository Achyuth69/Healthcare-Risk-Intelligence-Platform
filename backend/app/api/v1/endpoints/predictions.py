"""
Prediction Endpoints — Disease risk prediction with explainability
"""
import time
import uuid
import structlog
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.rbac import require_permission, Permission, TokenData
from app.core.exceptions import PredictionException
from app.models.prediction import PredictionRecord
from app.schemas.prediction import (
    PredictionRequest, PredictionResponse,
    BatchPredictionRequest, BatchPredictionResponse,
    SHAPExplanation, LIMEExplanation,
)
from app.ml.model_registry import ModelRegistry
from app.ml.explainability.shap_explainer import SHAPExplainer
from app.ml.explainability.lime_explainer import LIMEExplainer
from app.ml.feature_engineering import FeatureEngineer
from app.rag.pipeline import RAGPipeline

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.post("/predict", response_model=PredictionResponse)
async def predict_risk(
    payload: PredictionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_permission(Permission.PREDICT_WRITE)),
):
    """
    Run disease risk prediction for a patient.

    Returns risk score (0–1), risk category, SHAP/LIME explanations,
    and an optional LLM-generated clinical narrative.
    """
    start_time = time.perf_counter()

    try:
        # ── Feature Engineering ───────────────────────────────
        engineer = FeatureEngineer()
        feature_vector, feature_names = engineer.transform(payload.features)

        # ── Model Prediction ──────────────────────────────────
        registry = ModelRegistry.get_instance()
        risk_score, confidence, model_version = await registry.predict(
            disease_type=payload.disease_type,
            model_type=payload.model_type,
            features=feature_vector,
        )
        risk_category = _categorize_risk(risk_score)

        # ── SHAP Explanations ─────────────────────────────────
        shap_explanation = None
        if payload.include_shap:
            shap_exp = SHAPExplainer(registry, payload.disease_type, payload.model_type)
            shap_result = shap_exp.explain(feature_vector, feature_names)
            shap_explanation = SHAPExplanation(**shap_result)

        # ── LIME Explanations ─────────────────────────────────
        lime_explanation = None
        if payload.include_lime:
            lime_exp = LIMEExplainer(registry, payload.disease_type, payload.model_type)
            lime_result = lime_exp.explain(feature_vector, feature_names)
            lime_explanation = LIMEExplanation(**lime_result)

        # ── Feature Importance ────────────────────────────────
        feature_importance = registry.get_feature_importance(
            payload.disease_type, payload.model_type, feature_names
        )

        # ── LLM Narrative ─────────────────────────────────────
        llm_narrative = None
        if payload.include_llm_narrative:
            try:
                rag = RAGPipeline.get_instance()
                llm_narrative = await rag.generate_clinical_narrative(
                    disease_type=payload.disease_type,
                    risk_score=risk_score,
                    risk_category=risk_category,
                    features=payload.features.model_dump(),
                    shap_top_features=shap_explanation.top_features if shap_explanation else [],
                )
            except Exception as e:
                logger.warning("LLM narrative skipped", error=str(e))
                llm_narrative = (
                    f"Risk assessment complete. {risk_category.title()} risk "
                    f"({risk_score:.1%}) detected for {payload.disease_type.replace('_',' ')}. "
                    "Please consult a healthcare professional for personalised advice."
                )

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        prediction_id = str(uuid.uuid4())

        # ── Persist (background) ──────────────────────────────
        background_tasks.add_task(
            _persist_prediction,
            db=db,
            prediction_id=prediction_id,
            payload=payload,
            risk_score=risk_score,
            risk_category=risk_category,
            confidence=confidence,
            model_version=model_version,
            shap_explanation=shap_explanation,
            lime_explanation=lime_explanation,
            feature_importance=feature_importance,
            llm_narrative=llm_narrative,
            requested_by=current_user.user_id,
        )

        logger.info(
            "Prediction completed",
            disease=payload.disease_type,
            risk_score=round(risk_score, 4),
            category=risk_category,
            elapsed_ms=round(elapsed_ms, 2),
        )

        return PredictionResponse(
            prediction_id=prediction_id,
            patient_id=payload.patient_id,
            disease_type=payload.disease_type,
            model_type=payload.model_type,
            model_version=model_version,
            risk_score=risk_score,
            risk_percentage=round(risk_score * 100, 2),
            risk_category=risk_category,
            confidence=confidence,
            shap_explanation=shap_explanation,
            lime_explanation=lime_explanation,
            feature_importance=feature_importance,
            llm_narrative=llm_narrative,
            processing_time_ms=round(elapsed_ms, 2),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    except Exception as e:
        logger.error("Prediction failed", error=str(e), exc_info=True)
        raise PredictionException(f"Prediction failed: {e}")


@router.post("/predict/batch", response_model=BatchPredictionResponse)
async def batch_predict(
    payload: BatchPredictionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_permission(Permission.PREDICT_WRITE)),
):
    """Run batch predictions for multiple patients (max 100)."""
    start_time = time.perf_counter()
    results, failed = [], 0

    for req in payload.requests:
        try:
            result = await predict_risk(req, BackgroundTasks(), db, current_user)
            results.append(result)
        except Exception as e:
            logger.warning("Batch item failed", error=str(e))
            failed += 1

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    return BatchPredictionResponse(
        results=results,
        total=len(payload.requests),
        failed=failed,
        processing_time_ms=round(elapsed_ms, 2),
    )

@router.get("/history/{patient_id}", response_model=List[PredictionResponse])
async def get_prediction_history(
    patient_id: str,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_permission(Permission.PREDICT_READ)),
):
    """Retrieve prediction history for a patient."""
    result = await db.execute(
        select(PredictionRecord)
        .where(PredictionRecord.patient_id == patient_id)
        .order_by(PredictionRecord.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


# ── Helpers ───────────────────────────────────────────────────

def _categorize_risk(score: float) -> str:
    if score < 0.20:
        return "low"
    elif score < 0.50:
        return "medium"
    elif score < 0.75:
        return "high"
    return "critical"


async def _persist_prediction(
    db: AsyncSession,
    prediction_id: str,
    payload: PredictionRequest,
    risk_score: float,
    risk_category: str,
    confidence: float,
    model_version: str,
    shap_explanation,
    lime_explanation,
    feature_importance,
    llm_narrative,
    requested_by: str,
):
    """Background task: persist prediction to PostgreSQL."""
    try:
        record = PredictionRecord(
            id=prediction_id,
            patient_id=payload.patient_id if payload.patient_id else None,
            requested_by=requested_by if requested_by else None,
            disease_type=payload.disease_type,
            model_type=payload.model_type,
            model_version=model_version,
            risk_score=risk_score,
            risk_category=risk_category,
            confidence=confidence,
            input_features=payload.features.model_dump(),
            shap_values=shap_explanation.model_dump() if shap_explanation else None,
            lime_explanation=lime_explanation.model_dump() if lime_explanation else None,
            feature_importance=feature_importance,
            llm_explanation=llm_narrative,
        )
        db.add(record)
        await db.commit()
    except Exception as e:
        logger.error("Failed to persist prediction", error=str(e))
