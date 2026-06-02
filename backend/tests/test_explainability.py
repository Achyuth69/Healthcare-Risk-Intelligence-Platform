"""
Explainability Module Tests — SHAP and LIME
"""
import pytest
import numpy as np
from unittest.mock import MagicMock


@pytest.fixture
def mock_registry():
    class MockModel:
        def predict_proba(self, X):
            return np.array([[0.35, 0.65]])
        feature_importances_ = np.ones(42) / 42

    registry = MagicMock()
    bundle = MagicMock()
    bundle.model = MockModel()
    bundle.get_feature_importance.return_value = np.ones(42) / 42
    registry.get_model.return_value = bundle
    return registry


@pytest.fixture
def feature_data():
    rng = np.random.default_rng(seed=0)
    vector = rng.standard_normal((1, 42)).astype(np.float32)
    names = [f"feature_{i}" for i in range(42)]
    return vector, names


def test_shap_explainer_returns_correct_schema(mock_registry, feature_data):
    from app.ml.explainability.shap_explainer import SHAPExplainer
    vector, names = feature_data
    explainer = SHAPExplainer(mock_registry, "diabetes", "xgboost")
    result = explainer.explain(vector, names)

    assert "feature_names" in result
    assert "shap_values" in result
    assert "base_value" in result
    assert "top_features" in result
    assert len(result["top_features"]) <= 10
    for feat in result["top_features"]:
        assert "name" in feat
        assert "shap_value" in feat
        assert feat["direction"] in ("increases_risk", "decreases_risk")


def test_lime_explainer_returns_correct_schema(mock_registry, feature_data):
    from app.ml.explainability.lime_explainer import LIMEExplainer
    vector, names = feature_data
    explainer = LIMEExplainer(mock_registry, "diabetes", "xgboost")
    result = explainer.explain(vector, names)

    assert "feature_contributions" in result
    assert "intercept" in result
    assert "local_prediction" in result
    assert "score" in result
    assert isinstance(result["feature_contributions"], list)


def test_feature_engineering_output_shape():
    from app.ml.feature_engineering import FeatureEngineer, FEATURE_NAMES
    from app.schemas.prediction import PatientFeatures

    features = PatientFeatures(
        age=45, gender="male", bmi=28.0,
        glucose_level=110.0, hba1c=5.9,
        has_diabetes=False, has_hypertension=True,
        has_heart_disease=False, has_kidney_disease=False,
        family_history_diabetes=True, family_history_heart_disease=False,
    )
    engineer = FeatureEngineer()
    vector, names = engineer.transform(features)

    assert vector.shape == (1, len(FEATURE_NAMES))
    assert names == FEATURE_NAMES
    assert not np.any(np.isnan(vector))


def test_feature_engineering_one_hot_gender():
    from app.ml.feature_engineering import FeatureEngineer, FEATURE_NAMES
    from app.schemas.prediction import PatientFeatures

    for gender, male_val, female_val in [("male", 1.0, 0.0), ("female", 0.0, 1.0)]:
        features = PatientFeatures(
            age=30, gender=gender,
            has_diabetes=False, has_hypertension=False,
            has_heart_disease=False, has_kidney_disease=False,
            family_history_diabetes=False, family_history_heart_disease=False,
        )
        engineer = FeatureEngineer()
        vector, names = engineer.transform(features)
        assert vector[0][names.index("gender_male")]   == male_val
        assert vector[0][names.index("gender_female")] == female_val


def test_risk_categorisation():
    from app.api.v1.endpoints.predictions import _categorize_risk
    assert _categorize_risk(0.05) == "low"
    assert _categorize_risk(0.19) == "low"
    assert _categorize_risk(0.20) == "medium"
    assert _categorize_risk(0.49) == "medium"
    assert _categorize_risk(0.50) == "high"
    assert _categorize_risk(0.74) == "high"
    assert _categorize_risk(0.75) == "critical"
    assert _categorize_risk(0.99) == "critical"
