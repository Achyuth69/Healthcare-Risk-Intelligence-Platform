"""
Feature Engineering Pipeline
Transforms raw PatientFeatures into a normalized numeric vector
ready for ML model inference.
"""
import json
import numpy as np
from typing import Tuple, List
from pathlib import Path

from app.config import settings
from app.schemas.prediction import PatientFeatures


# Canonical feature order — must match training pipeline
FEATURE_NAMES: List[str] = [
    # Demographics
    "age", "gender_male", "gender_female", "gender_other",
    # Vitals
    "bmi", "bp_systolic", "bp_diastolic", "heart_rate",
    "glucose_level", "hba1c", "cholesterol_total",
    "cholesterol_ldl", "cholesterol_hdl", "triglycerides",
    # Derived vitals
    "pulse_pressure", "bmi_category_underweight",
    "bmi_category_normal", "bmi_category_overweight", "bmi_category_obese",
    "glucose_hba1c_ratio", "cholesterol_ratio",
    # Lifestyle
    "smoking_never", "smoking_former", "smoking_current",
    "alcohol_none", "alcohol_moderate", "alcohol_heavy",
    "activity_sedentary", "activity_light", "activity_moderate", "activity_active",
    # Medical history
    "has_diabetes", "has_hypertension", "has_heart_disease",
    "has_kidney_disease", "family_history_diabetes",
    "family_history_heart_disease",
    # Interaction features
    "age_bmi_interaction", "glucose_bmi_interaction",
    "hypertension_diabetes_interaction",
]

# Imputation defaults (population medians)
IMPUTATION_DEFAULTS = {
    "bmi": 26.5,
    "bp_systolic": 120.0,
    "bp_diastolic": 80.0,
    "heart_rate": 72.0,
    "glucose_level": 95.0,
    "hba1c": 5.5,
    "cholesterol_total": 190.0,
    "cholesterol_ldl": 110.0,
    "cholesterol_hdl": 55.0,
    "triglycerides": 130.0,
}


class FeatureEngineer:
    """
    Stateless feature engineering transformer.
    Applies one-hot encoding, imputation, and interaction features.
    """

    def transform(
        self, features: PatientFeatures
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Transform PatientFeatures into a flat numeric numpy array.

        Returns:
            feature_vector: shape (1, n_features)
            feature_names: list of feature names in order
        """
        f = features
        vec = {}

        # ── Demographics ──────────────────────────────────────
        vec["age"] = float(f.age)
        vec["gender_male"] = 1.0 if f.gender == "male" else 0.0
        vec["gender_female"] = 1.0 if f.gender == "female" else 0.0
        vec["gender_other"] = 1.0 if f.gender == "other" else 0.0

        # ── Vitals (with imputation) ──────────────────────────
        bmi = f.bmi or IMPUTATION_DEFAULTS["bmi"]
        bp_sys = f.blood_pressure_systolic or IMPUTATION_DEFAULTS["bp_systolic"]
        bp_dia = f.blood_pressure_diastolic or IMPUTATION_DEFAULTS["bp_diastolic"]
        hr = f.heart_rate or IMPUTATION_DEFAULTS["heart_rate"]
        glucose = f.glucose_level or IMPUTATION_DEFAULTS["glucose_level"]
        hba1c = f.hba1c or IMPUTATION_DEFAULTS["hba1c"]
        chol_total = f.cholesterol_total or IMPUTATION_DEFAULTS["cholesterol_total"]
        chol_ldl = f.cholesterol_ldl or IMPUTATION_DEFAULTS["cholesterol_ldl"]
        chol_hdl = f.cholesterol_hdl or IMPUTATION_DEFAULTS["cholesterol_hdl"]
        trig = f.triglycerides or IMPUTATION_DEFAULTS["triglycerides"]

        vec["bmi"] = bmi
        vec["bp_systolic"] = bp_sys
        vec["bp_diastolic"] = bp_dia
        vec["heart_rate"] = hr
        vec["glucose_level"] = glucose
        vec["hba1c"] = hba1c
        vec["cholesterol_total"] = chol_total
        vec["cholesterol_ldl"] = chol_ldl
        vec["cholesterol_hdl"] = chol_hdl
        vec["triglycerides"] = trig

        # ── Derived Vitals ────────────────────────────────────
        vec["pulse_pressure"] = bp_sys - bp_dia
        vec["bmi_category_underweight"] = 1.0 if bmi < 18.5 else 0.0
        vec["bmi_category_normal"] = 1.0 if 18.5 <= bmi < 25.0 else 0.0
        vec["bmi_category_overweight"] = 1.0 if 25.0 <= bmi < 30.0 else 0.0
        vec["bmi_category_obese"] = 1.0 if bmi >= 30.0 else 0.0
        vec["glucose_hba1c_ratio"] = glucose / max(hba1c, 0.1)
        vec["cholesterol_ratio"] = chol_total / max(chol_hdl, 0.1)

        # ── Lifestyle ─────────────────────────────────────────
        smoking = (f.smoking_status or "never").lower()
        vec["smoking_never"] = 1.0 if smoking == "never" else 0.0
        vec["smoking_former"] = 1.0 if smoking == "former" else 0.0
        vec["smoking_current"] = 1.0 if smoking == "current" else 0.0

        alcohol = (f.alcohol_use or "none").lower()
        vec["alcohol_none"] = 1.0 if alcohol == "none" else 0.0
        vec["alcohol_moderate"] = 1.0 if alcohol == "moderate" else 0.0
        vec["alcohol_heavy"] = 1.0 if alcohol == "heavy" else 0.0

        activity = (f.physical_activity_level or "sedentary").lower()
        vec["activity_sedentary"] = 1.0 if activity == "sedentary" else 0.0
        vec["activity_light"] = 1.0 if activity == "light" else 0.0
        vec["activity_moderate"] = 1.0 if activity == "moderate" else 0.0
        vec["activity_active"] = 1.0 if activity == "active" else 0.0

        # ── Medical History ───────────────────────────────────
        vec["has_diabetes"] = float(f.has_diabetes)
        vec["has_hypertension"] = float(f.has_hypertension)
        vec["has_heart_disease"] = float(f.has_heart_disease)
        vec["has_kidney_disease"] = float(f.has_kidney_disease)
        vec["family_history_diabetes"] = float(f.family_history_diabetes)
        vec["family_history_heart_disease"] = float(f.family_history_heart_disease)

        # ── Interaction Features ──────────────────────────────
        vec["age_bmi_interaction"] = float(f.age) * bmi / 100.0
        vec["glucose_bmi_interaction"] = glucose * bmi / 1000.0
        vec["hypertension_diabetes_interaction"] = (
            float(f.has_hypertension) * float(f.has_diabetes)
        )

        # ── Assemble in canonical order ───────────────────────
        feature_vector = np.array(
            [vec[name] for name in FEATURE_NAMES], dtype=np.float32
        ).reshape(1, -1)

        return feature_vector, FEATURE_NAMES
