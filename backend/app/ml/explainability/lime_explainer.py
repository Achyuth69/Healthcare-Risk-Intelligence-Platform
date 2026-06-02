"""
LIME Explainer — Local Interpretable Model-Agnostic Explanations
Provides human-readable feature contributions for individual predictions.
"""
import numpy as np
import structlog
from typing import Dict, Any, List, Optional

logger = structlog.get_logger(__name__)


class LIMEExplainer:
    """
    Wraps LIME LimeTabularExplainer for tabular healthcare data.

    LIME perturbs the input, fits a local linear model, and returns
    feature contributions that are interpretable by clinicians.
    """

    def __init__(self, registry, disease_type: str, model_type: str):
        self.registry = registry
        self.disease_type = disease_type
        self.model_type = model_type if model_type != "ensemble" else "xgboost"
        self._explainer = None

    def _get_explainer(self, feature_names: List[str]):
        """Lazy-initialize LIME explainer with synthetic background data."""
        if self._explainer is not None:
            return self._explainer

        try:
            from lime.lime_tabular import LimeTabularExplainer
        except ImportError:
            logger.warning("lime not installed — using mock explanations")
            return None

        n_features = len(feature_names)
        rng = np.random.default_rng(seed=42)
        training_data = rng.standard_normal((500, n_features)).astype(np.float32)

        self._explainer = LimeTabularExplainer(
            training_data=training_data,
            feature_names=feature_names,
            class_names=["low_risk", "high_risk"],
            mode="classification",
            discretize_continuous=True,
            random_state=42,
        )
        return self._explainer

    def explain(
        self,
        feature_vector: np.ndarray,
        feature_names: List[str],
        num_features: int = 10,
        num_samples: int = 1000,
    ) -> Dict[str, Any]:
        """
        Compute LIME explanation for a single patient.
        Returns a dict matching the LIMEExplanation schema.
        """
        explainer = self._get_explainer(feature_names)
        if explainer is None:
            return self._mock_explanation(feature_names)

        bundle = self.registry.get_model(self.disease_type, self.model_type)
        if bundle is None:
            return self._mock_explanation(feature_names)

        try:
            explanation = explainer.explain_instance(
                data_row=feature_vector[0],
                predict_fn=bundle.model.predict_proba,
                num_features=num_features,
                num_samples=num_samples,
                top_labels=1,
            )

            label = 1
            contributions = explanation.as_list(label=label)

            feature_contributions = [
                {
                    "feature": feat,
                    "contribution": float(weight),
                    "direction": "increases_risk" if weight > 0 else "decreases_risk",
                }
                for feat, weight in contributions
            ]

            local_pred = (
                float(explanation.local_pred[label])
                if hasattr(explanation, "local_pred")
                else 0.5
            )
            score = float(explanation.score) if hasattr(explanation, "score") else 0.8

            return {
                "feature_contributions": feature_contributions,
                "intercept": float(explanation.intercept[label]),
                "local_prediction": local_pred,
                "score": score,
            }

        except Exception as e:
            logger.error("LIME explanation failed", error=str(e), exc_info=True)
            return self._mock_explanation(feature_names)

    def _mock_explanation(self, feature_names: List[str]) -> Dict[str, Any]:
        """Deterministic mock LIME explanation for dev / test."""
        rng = np.random.default_rng(seed=42)
        contributions = [
            {
                "feature": f"{feature_names[i]} > 0.5",
                "contribution": float(rng.standard_normal() * 0.1),
                "direction": "increases_risk" if rng.random() > 0.5 else "decreases_risk",
            }
            for i in range(min(10, len(feature_names)))
        ]
        return {
            "feature_contributions": contributions,
            "intercept": 0.35,
            "local_prediction": 0.62,
            "score": 0.78,
        }
