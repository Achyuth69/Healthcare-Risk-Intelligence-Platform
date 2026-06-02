"""
Prediction Schemas — Request/Response models for risk prediction endpoints.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


class PatientFeatures(BaseModel):
    """Input features for disease risk prediction."""
    # Demographics
    age: int = Field(..., ge=0, le=120, description="Patient age in years")
    gender: str = Field(..., description="Patient gender: male/female/other")
    ethnicity: Optional[str] = Field(None, description="Patient ethnicity")

    # Vitals
    bmi: Optional[float] = Field(None, ge=10.0, le=80.0, description="Body Mass Index")
    blood_pressure_systolic: Optional[float] = Field(None, ge=60.0, le=300.0)
    blood_pressure_diastolic: Optional[float] = Field(None, ge=40.0, le=200.0)
    heart_rate: Optional[float] = Field(None, ge=30.0, le=250.0)
    glucose_level: Optional[float] = Field(None, ge=20.0, le=600.0, description="Fasting glucose mg/dL")
    hba1c: Optional[float] = Field(None, ge=3.0, le=20.0, description="HbA1c percentage")
    cholesterol_total: Optional[float] = Field(None, ge=50.0, le=600.0)
    cholesterol_ldl: Optional[float] = Field(None, ge=10.0, le=400.0)
    cholesterol_hdl: Optional[float] = Field(None, ge=10.0, le=150.0)
    triglycerides: Optional[float] = Field(None, ge=20.0, le=2000.0)

    # Lifestyle
    smoking_status: Optional[str] = Field(None, description="never/former/current")
    alcohol_use: Optional[str] = Field(None, description="none/moderate/heavy")
    physical_activity_level: Optional[str] = Field(None, description="sedentary/light/moderate/active")

    # Medical History (binary flags)
    has_diabetes: bool = False
    has_hypertension: bool = False
    has_heart_disease: bool = False
    has_kidney_disease: bool = False
    family_history_diabetes: bool = False
    family_history_heart_disease: bool = False

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: str) -> str:
        allowed = {"male", "female", "other"}
        if v.lower() not in allowed:
            raise ValueError(f"Gender must be one of: {allowed}")
        return v.lower()


class PredictionRequest(BaseModel):
    patient_id: Optional[str] = Field(None, description="Existing patient ID (optional)")
    features: PatientFeatures
    disease_type: str = Field(..., description="diabetes/heart_disease/hypertension/kidney_disease/stroke")
    model_type: str = Field("ensemble", description="xgboost/random_forest/lightgbm/ensemble")
    include_shap: bool = Field(True, description="Include SHAP explanations")
    include_lime: bool = Field(False, description="Include LIME explanations (slower)")
    include_llm_narrative: bool = Field(True, description="Generate LLM clinical narrative")

    @field_validator("disease_type")
    @classmethod
    def validate_disease(cls, v: str) -> str:
        allowed = {"diabetes", "heart_disease", "hypertension", "kidney_disease", "stroke"}
        if v not in allowed:
            raise ValueError(f"disease_type must be one of: {allowed}")
        return v

    @field_validator("model_type")
    @classmethod
    def validate_model(cls, v: str) -> str:
        allowed = {"xgboost", "random_forest", "lightgbm", "ensemble"}
        if v not in allowed:
            raise ValueError(f"model_type must be one of: {allowed}")
        return v


class SHAPExplanation(BaseModel):
    feature_names: List[str]
    shap_values: List[float]
    base_value: float
    expected_value: float
    top_features: List[Dict[str, Any]]  # [{name, value, shap_value, direction}]


class LIMEExplanation(BaseModel):
    feature_contributions: List[Dict[str, Any]]
    intercept: float
    local_prediction: float
    score: float


class PredictionResponse(BaseModel):
    prediction_id: str
    patient_id: Optional[str]
    disease_type: str
    model_type: str
    model_version: str

    # Risk Assessment
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Probability 0-1")
    risk_percentage: float = Field(..., description="Risk as percentage")
    risk_category: str = Field(..., description="low/medium/high/critical")
    confidence: float

    # Explanations
    shap_explanation: Optional[SHAPExplanation] = None
    lime_explanation: Optional[LIMEExplanation] = None
    feature_importance: Optional[Dict[str, float]] = None
    llm_narrative: Optional[str] = None

    # Metadata
    processing_time_ms: float
    timestamp: str

    model_config = {"from_attributes": True}


class BatchPredictionRequest(BaseModel):
    requests: List[PredictionRequest] = Field(..., max_length=100)


class BatchPredictionResponse(BaseModel):
    results: List[PredictionResponse]
    total: int
    failed: int
    processing_time_ms: float
