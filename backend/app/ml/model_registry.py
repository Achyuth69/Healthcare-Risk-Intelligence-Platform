"""
Model Registry — Singleton that loads and manages all ML models.
Supports XGBoost, Random Forest, LightGBM, and ensemble inference.
"""
import asyncio
import json
import pickle
import structlog
from pathlib import Path
from typing import Dict, Optional, Tuple, List
import numpy as np

from app.config import settings
from app.core.exceptions import ModelNotReadyException

logger = structlog.get_logger(__name__)


class ModelBundle:
    """Holds a trained model and its metadata."""
    def __init__(self, model, model_type: str, disease_type: str, version: str):
        self.model = model
        self.model_type = model_type
        self.disease_type = disease_type
        self.version = version
        self.is_ready = True

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict_proba(X)[:, 1]

    def get_feature_importance(self) -> Optional[np.ndarray]:
        if hasattr(self.model, "feature_importances_"):
            return self.model.feature_importances_
        return None


class ModelRegistry:
    """
    Singleton registry for all disease-specific ML models.
    Thread-safe lazy initialization with async support.
    """
    _instance: Optional["ModelRegistry"] = None
    _lock = asyncio.Lock()

    def __init__(self):
        # {disease_type: {model_type: ModelBundle}}
        self._models: Dict[str, Dict[str, ModelBundle]] = {}
        self._initialized = False

    @classmethod
    async def initialize(cls) -> "ModelRegistry":
        """Initialize the registry singleton (called at app startup)."""
        async with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
                await cls._instance._load_all_models()
        return cls._instance

    @classmethod
    def get_instance(cls) -> "ModelRegistry":
        if cls._instance is None:
            raise ModelNotReadyException("ModelRegistry not initialized. Call initialize() first.")
        return cls._instance

    async def _load_all_models(self):
        """Load all model artifacts from disk (or S3 in production)."""
        diseases = ["diabetes", "heart_disease", "hypertension", "kidney_disease", "stroke"]
        model_types = ["xgboost", "random_forest", "lightgbm"]

        for disease in diseases:
            self._models[disease] = {}
            for mtype in model_types:
                try:
                    model = await self._load_model(disease, mtype)
                    if model:
                        self._models[disease][mtype] = ModelBundle(
                            model=model,
                            model_type=mtype,
                            disease_type=disease,
                            version="1.0.0",
                        )
                        logger.info("Model loaded", disease=disease, model_type=mtype)
                except Exception as e:
                    logger.warning(
                        "Model not found, will use mock",
                        disease=disease,
                        model_type=mtype,
                        error=str(e),
                    )
                    # Use mock model for development
                    self._models[disease][mtype] = self._create_mock_bundle(disease, mtype)

        self._initialized = True
        logger.info("All models loaded", total=sum(len(v) for v in self._models.values()))

    async def _load_model(self, disease: str, model_type: str):
        """Load a pickled model from disk."""
        model_dir = Path(settings.MODEL_ARTIFACTS_DIR)
        path = model_dir / f"{model_type}_{disease}.pkl"

        if not path.exists():
            return None

        loop = asyncio.get_event_loop()
        model = await loop.run_in_executor(None, self._load_pickle, path)
        return model

    @staticmethod
    def _load_pickle(path: Path):
        with open(path, "rb") as f:
            return pickle.load(f)

    def _create_mock_bundle(self, disease: str, model_type: str) -> ModelBundle:
        """Create a deterministic mock model bundle for development/testing."""
        class MockModel:
            def predict_proba(self, X):
                # Deterministic, always valid 0-1 score
                val = float(np.sum(np.abs(X[0][:5])))
                score = 0.05 + (val % 0.90)  # always in [0.05, 0.95]
                return np.array([[1.0 - score, score]])

            feature_importances_ = np.ones(42) / 42.0

        bundle = ModelBundle(MockModel(), model_type, disease, "mock-1.0.0")
        return bundle

    async def predict(
        self,
        disease_type: str,
        model_type: str,
        features: np.ndarray,
    ) -> Tuple[float, float, str]:
        """
        Run inference and return (risk_score, confidence, model_version).
        For 'ensemble', averages predictions from all three models.
        """
        if disease_type not in self._models:
            raise ModelNotReadyException(f"No models for disease: {disease_type}")

        if model_type == "ensemble":
            scores = []
            for mtype, bundle in self._models[disease_type].items():
                try:
                    s = float(bundle.predict_proba(features)[0])
                    if not np.isnan(s) and not np.isinf(s):
                        scores.append(np.clip(s, 0.0, 1.0))
                except Exception:
                    pass
            if not scores:
                scores = [0.35]
            risk_score = float(np.clip(np.mean(scores), 0.0, 1.0))
            confidence = float(np.clip(1.0 - np.std(scores), 0.5, 1.0))
            version = "ensemble-1.0.0"
        else:
            if model_type not in self._models[disease_type]:
                raise ModelNotReadyException(f"Model {model_type} not available for {disease_type}")
            bundle = self._models[disease_type][model_type]
            raw = float(bundle.predict_proba(features)[0])
            risk_score = float(np.clip(raw if not np.isnan(raw) else 0.35, 0.0, 1.0))
            confidence = 0.85
            version = bundle.version

        return risk_score, confidence, version

    def get_model(self, disease_type: str, model_type: str) -> Optional[ModelBundle]:
        """Get a specific model bundle."""
        return self._models.get(disease_type, {}).get(model_type)

    def get_feature_importance(
        self,
        disease_type: str,
        model_type: str,
        feature_names: Optional[List[str]] = None,
    ) -> Dict[str, float]:
        """Get feature importance as a named dict. Always returns a dict."""
        from app.ml.feature_engineering import FEATURE_NAMES
        names = feature_names or FEATURE_NAMES

        if model_type == "ensemble":
            all_importances = []
            for bundle in self._models.get(disease_type, {}).values():
                imp = bundle.get_feature_importance()
                if imp is not None:
                    all_importances.append(imp)
            if not all_importances:
                return {n: round(1.0 / len(names), 4) for n in names}
            avg = np.mean(all_importances, axis=0)
        else:
            bundle = self.get_model(disease_type, model_type)
            if not bundle:
                return {n: round(1.0 / len(names), 4) for n in names}
            avg = bundle.get_feature_importance()
            if avg is None:
                return {n: round(1.0 / len(names), 4) for n in names}

        if len(names) == len(avg):
            return {n: round(float(v), 6) for n, v in zip(names, avg)}
        return {f"feature_{i}": round(float(v), 6) for i, v in enumerate(avg)}

    def get_status(self) -> Dict:
        """Return registry status for admin endpoint."""
        status = {}
        for disease, models in self._models.items():
            status[disease] = {
                mtype: {
                    "version": bundle.version,
                    "ready": bundle.is_ready,
                }
                for mtype, bundle in models.items()
            }
        return {"initialized": self._initialized, "models": status}
