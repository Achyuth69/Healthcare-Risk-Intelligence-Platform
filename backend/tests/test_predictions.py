"""
Prediction API Tests — Integration tests for the risk prediction endpoints.
"""
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app


@pytest.fixture
def patient_payload():
    return {
        "features": {
            "age": 52,
            "gender": "male",
            "bmi": 31.5,
            "blood_pressure_systolic": 145,
            "blood_pressure_diastolic": 92,
            "glucose_level": 118,
            "hba1c": 6.1,
            "cholesterol_total": 210,
            "cholesterol_ldl": 140,
            "cholesterol_hdl": 42,
            "smoking_status": "former",
            "alcohol_use": "moderate",
            "physical_activity_level": "sedentary",
            "has_diabetes": False,
            "has_hypertension": True,
            "has_heart_disease": False,
            "has_kidney_disease": False,
            "family_history_diabetes": True,
            "family_history_heart_disease": False,
        },
        "disease_type": "diabetes",
        "model_type": "ensemble",
        "include_shap": True,
        "include_lime": False,
        "include_llm_narrative": False,
    }


@pytest.mark.asyncio
async def test_predict_returns_risk_score(patient_payload, auth_headers):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/predictions/predict",
            json=patient_payload,
            headers=auth_headers,
        )
    assert response.status_code == 200
    data = response.json()
    assert "risk_score" in data
    assert 0.0 <= data["risk_score"] <= 1.0
    assert data["risk_category"] in ["low", "medium", "high", "critical"]
    assert "prediction_id" in data


@pytest.mark.asyncio
async def test_predict_includes_shap_explanation(patient_payload, auth_headers):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/predictions/predict",
            json=patient_payload,
            headers=auth_headers,
        )
    data = response.json()
    assert data["shap_explanation"] is not None
    assert "top_features" in data["shap_explanation"]
    assert len(data["shap_explanation"]["top_features"]) > 0


@pytest.mark.asyncio
async def test_predict_invalid_disease_type(patient_payload, auth_headers):
    patient_payload["disease_type"] = "invalid_disease"
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/predictions/predict",
            json=patient_payload,
            headers=auth_headers,
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_predict_requires_auth(patient_payload):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/predictions/predict",
            json=patient_payload,
        )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_risk_categorization():
    from app.api.v1.endpoints.predictions import _categorize_risk
    assert _categorize_risk(0.10) == "low"
    assert _categorize_risk(0.35) == "medium"
    assert _categorize_risk(0.60) == "high"
    assert _categorize_risk(0.85) == "critical"


@pytest.mark.asyncio
async def test_feature_engineering():
    from app.ml.feature_engineering import FeatureEngineer, FEATURE_NAMES
    from app.schemas.prediction import PatientFeatures

    features = PatientFeatures(
        age=45,
        gender="female",
        bmi=27.5,
        glucose_level=105,
        has_diabetes=False,
        has_hypertension=False,
        has_heart_disease=False,
        has_kidney_disease=False,
        family_history_diabetes=True,
        family_history_heart_disease=False,
    )

    engineer = FeatureEngineer()
    vector, names = engineer.transform(features)

    assert vector.shape == (1, len(FEATURE_NAMES))
    assert names == FEATURE_NAMES
    assert vector[0][names.index("gender_female")] == 1.0
    assert vector[0][names.index("gender_male")] == 0.0
    assert vector[0][names.index("family_history_diabetes")] == 1.0
