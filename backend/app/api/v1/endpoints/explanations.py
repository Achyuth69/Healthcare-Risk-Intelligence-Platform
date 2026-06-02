"""
Explainability Endpoints — On-demand SHAP / LIME for existing predictions
"""
import structlog
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.rbac import require_permission, Permission, TokenData
from app.core.exceptions import NotFoundException
from app.models.prediction import PredictionRecord
from app.ml.model_registry import ModelRegistry
from app.ml.explainability.shap_explainer import SHAPExplainer
from app.ml.explainability.lime_explainer import LIMEExplainer
from app.ml.feature_engineering import FeatureEngineer
from app.schemas.prediction import SHAPExplanation, LIMEExplanation, PatientFeatures

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get("/shap/{prediction_id}", response_model=SHAPExplanation)
async def get_shap_explanation(
    prediction_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_permission(Permission.EXPLAIN_READ)),
):
    """
    Retrieve or compute SHAP explanation for an existing prediction.
    Returns cached values if available, otherwise computes on-demand.
    """
    result = await db.execute(
        select(PredictionRecord).where(PredictionRecord.id == prediction_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise NotFoundException(f"Prediction {prediction_id} not found.")

    if record.shap_values:
        return SHAPExplanation(**record.shap_values)

    features = PatientFeatures(**record.input_features)
    engineer = FeatureEngineer()
    feature_vector, feature_names = engineer.transform(features)

    registry = ModelRegistry.get_instance()
    explainer = SHAPExplainer(registry, record.disease_type, record.model_type)
    return SHAPExplanation(**explainer.explain(feature_vector, feature_names))


@router.get("/lime/{prediction_id}", response_model=LIMEExplanation)
async def get_lime_explanation(
    prediction_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_permission(Permission.EXPLAIN_READ)),
):
    """
    Retrieve or compute LIME explanation for an existing prediction.
    LIME provides local, human-interpretable feature contributions.
    """
    result = await db.execute(
        select(PredictionRecord).where(PredictionRecord.id == prediction_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise NotFoundException(f"Prediction {prediction_id} not found.")

    if record.lime_explanation:
        return LIMEExplanation(**record.lime_explanation)

    features = PatientFeatures(**record.input_features)
    engineer = FeatureEngineer()
    feature_vector, feature_names = engineer.transform(features)

    registry = ModelRegistry.get_instance()
    explainer = LIMEExplainer(registry, record.disease_type, record.model_type)
    return LIMEExplanation(**explainer.explain(feature_vector, feature_names))


@router.get("/global-importance/{disease_type}")
async def get_global_feature_importance(
    disease_type: str,
    model_type: str = "ensemble",
    current_user: TokenData = Depends(require_permission(Permission.EXPLAIN_READ)),
):
    """
    Global feature importance (mean |SHAP|) across the population.
    Gives a model-level view of which features drive predictions.
    """
    registry = ModelRegistry.get_instance()
    importance = registry.get_feature_importance(disease_type, model_type)
    return {
        "disease_type": disease_type,
        "model_type": model_type,
        "feature_importance": importance,
    }
