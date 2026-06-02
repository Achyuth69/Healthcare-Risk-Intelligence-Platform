"""
Model Training Pipeline
Trains XGBoost, Random Forest, and LightGBM for each disease type.
Includes hyperparameter tuning with Optuna and cross-validation.

Usage:
    python -m app.ml.training.train_models --disease all
    python -m app.ml.training.train_models --disease diabetes --tune --n-trials 100
"""
import argparse
import json
import pickle
import time
from pathlib import Path
from typing import Dict, Tuple, Any

import numpy as np
import pandas as pd
import structlog
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    roc_auc_score, f1_score, precision_score,
    recall_score, average_precision_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split

logger = structlog.get_logger(__name__)

DISEASE_TYPES = ["diabetes", "heart_disease", "hypertension", "kidney_disease", "stroke"]
MODEL_DIR = Path("models")
MODEL_DIR.mkdir(exist_ok=True)


# ── Synthetic Data Generator ──────────────────────────────────

def load_training_data(disease_type: str) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Generate synthetic training data for a disease type.
    Replace with real EHR data loader in production.
    """
    rng = np.random.default_rng(seed=42)
    n = 10_000

    data = pd.DataFrame({
        "age":               rng.integers(18, 90, n).astype(float),
        "bmi":               np.clip(rng.normal(27, 5, n), 15, 60),
        "bp_systolic":       np.clip(rng.normal(125, 20, n), 80, 220),
        "bp_diastolic":      np.clip(rng.normal(80, 12, n), 50, 140),
        "heart_rate":        np.clip(rng.normal(72, 12, n), 40, 180),
        "glucose_level":     np.clip(rng.normal(100, 25, n), 50, 400),
        "hba1c":             np.clip(rng.normal(5.7, 1.2, n), 3.5, 15),
        "cholesterol_total": np.clip(rng.normal(195, 40, n), 100, 400),
        "cholesterol_ldl":   np.clip(rng.normal(115, 35, n), 30, 300),
        "cholesterol_hdl":   np.clip(rng.normal(55, 15, n), 20, 120),
        "triglycerides":     np.clip(rng.normal(140, 60, n), 30, 600),
        "gender_male":       rng.binomial(1, 0.5, n).astype(float),
        "smoking_current":   rng.binomial(1, 0.15, n).astype(float),
        "smoking_former":    rng.binomial(1, 0.20, n).astype(float),
        "alcohol_heavy":     rng.binomial(1, 0.10, n).astype(float),
        "activity_sedentary":rng.binomial(1, 0.30, n).astype(float),
        "has_hypertension":  rng.binomial(1, 0.30, n).astype(float),
        "has_heart_disease": rng.binomial(1, 0.10, n).astype(float),
        "family_hx_diabetes":rng.binomial(1, 0.25, n).astype(float),
        "family_hx_heart":   rng.binomial(1, 0.20, n).astype(float),
    })

    if disease_type == "diabetes":
        risk = (
            0.30 * (data["glucose_level"] > 126).astype(float)
            + 0.25 * (data["hba1c"] > 6.5).astype(float)
            + 0.15 * (data["bmi"] > 30).astype(float)
            + 0.10 * data["family_hx_diabetes"]
            + 0.10 * (data["age"] > 45).astype(float)
            + 0.10 * data["activity_sedentary"]
        )
    elif disease_type == "heart_disease":
        risk = (
            0.25 * (data["cholesterol_ldl"] > 160).astype(float)
            + 0.20 * (data["bp_systolic"] > 140).astype(float)
            + 0.15 * data["smoking_current"]
            + 0.15 * data["has_hypertension"]
            + 0.15 * (data["age"] > 55).astype(float)
            + 0.10 * data["family_hx_heart"]
        )
    elif disease_type == "hypertension":
        risk = (
            0.30 * (data["bp_systolic"] > 130).astype(float)
            + 0.20 * (data["bmi"] > 30).astype(float)
            + 0.20 * (data["age"] > 50).astype(float)
            + 0.15 * data["alcohol_heavy"]
            + 0.15 * data["activity_sedentary"]
        )
    else:
        risk = rng.uniform(0, 1, n)

    noise = rng.normal(0, 0.1, n)
    labels = (risk + noise > 0.5).astype(int)

    logger.info(
        "Training data generated",
        disease=disease_type,
        n_samples=n,
        positive_rate=f"{labels.mean():.2%}",
    )
    return data, pd.Series(labels)


# ── Hyperparameter Tuning ─────────────────────────────────────

def tune_xgboost(X_train: np.ndarray, y_train: np.ndarray, n_trials: int = 50) -> Dict:
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    import xgboost as xgb

    def objective(trial):
        params = {
            "n_estimators":      trial.suggest_int("n_estimators", 100, 1000),
            "max_depth":         trial.suggest_int("max_depth", 3, 10),
            "learning_rate":     trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "subsample":         trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree":  trial.suggest_float("colsample_bytree", 0.6, 1.0),
            "min_child_weight":  trial.suggest_int("min_child_weight", 1, 10),
            "reg_alpha":         trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
            "reg_lambda":        trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),
            "eval_metric": "auc", "random_state": 42, "n_jobs": -1,
        }
        model = xgb.XGBClassifier(**params)
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        return cross_val_score(model, X_train, y_train, cv=cv, scoring="roc_auc").mean()

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=n_trials, show_progress_bar=True)
    return study.best_params


def tune_random_forest(X_train: np.ndarray, y_train: np.ndarray, n_trials: int = 30) -> Dict:
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    def objective(trial):
        params = {
            "n_estimators":     trial.suggest_int("n_estimators", 100, 500),
            "max_depth":        trial.suggest_int("max_depth", 5, 30),
            "min_samples_split":trial.suggest_int("min_samples_split", 2, 20),
            "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 10),
            "max_features":     trial.suggest_categorical("max_features", ["sqrt", "log2"]),
            "class_weight": "balanced", "random_state": 42, "n_jobs": -1,
        }
        model = RandomForestClassifier(**params)
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        return cross_val_score(model, X_train, y_train, cv=cv, scoring="roc_auc").mean()

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=n_trials, show_progress_bar=True)
    return study.best_params


def tune_lightgbm(X_train: np.ndarray, y_train: np.ndarray, n_trials: int = 50) -> Dict:
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    import lightgbm as lgb

    def objective(trial):
        params = {
            "n_estimators":      trial.suggest_int("n_estimators", 100, 1000),
            "max_depth":         trial.suggest_int("max_depth", 3, 12),
            "learning_rate":     trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "num_leaves":        trial.suggest_int("num_leaves", 20, 300),
            "subsample":         trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree":  trial.suggest_float("colsample_bytree", 0.6, 1.0),
            "min_child_samples": trial.suggest_int("min_child_samples", 5, 100),
            "reg_alpha":         trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
            "reg_lambda":        trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),
            "class_weight": "balanced", "random_state": 42, "n_jobs": -1, "verbose": -1,
        }
        model = lgb.LGBMClassifier(**params)
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        return cross_val_score(model, X_train, y_train, cv=cv, scoring="roc_auc").mean()

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=n_trials, show_progress_bar=True)
    return study.best_params


# ── Training ──────────────────────────────────────────────────

def train_and_evaluate(
    disease_type: str,
    tune: bool = False,
    n_trials: int = 50,
) -> Dict[str, Any]:
    """Full training pipeline for one disease type."""
    import xgboost as xgb
    import lightgbm as lgb
    from imblearn.over_sampling import SMOTE

    logger.info("Starting training", disease=disease_type, tune=tune)
    start = time.time()

    X_df, y = load_training_data(disease_type)
    X = X_df.values.astype(np.float32)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    smote = SMOTE(random_state=42)
    X_res, y_res = smote.fit_resample(X_train, y_train)
    logger.info("SMOTE applied", original=len(y_train), resampled=len(y_res))

    results = {}

    # XGBoost
    logger.info("Training XGBoost", disease=disease_type)
    xgb_params = tune_xgboost(X_res, y_res, n_trials) if tune else {
        "n_estimators": 300, "max_depth": 6, "learning_rate": 0.05,
        "subsample": 0.8, "colsample_bytree": 0.8,
        "eval_metric": "auc", "random_state": 42, "n_jobs": -1,
    }
    xgb_model = xgb.XGBClassifier(**xgb_params)
    xgb_model.fit(X_res, y_res, eval_set=[(X_test, y_test)], verbose=False)
    results["xgboost"] = _evaluate(xgb_model, X_test, y_test)
    _save_model(xgb_model, disease_type, "xgboost")

    # Random Forest
    logger.info("Training Random Forest", disease=disease_type)
    rf_params = tune_random_forest(X_res, y_res, n_trials // 2) if tune else {
        "n_estimators": 200, "max_depth": 15,
        "class_weight": "balanced", "random_state": 42, "n_jobs": -1,
    }
    rf_model = RandomForestClassifier(**rf_params)
    rf_model.fit(X_res, y_res)
    results["random_forest"] = _evaluate(rf_model, X_test, y_test)
    _save_model(rf_model, disease_type, "random_forest")

    # LightGBM
    logger.info("Training LightGBM", disease=disease_type)
    lgbm_params = tune_lightgbm(X_res, y_res, n_trials) if tune else {
        "n_estimators": 300, "max_depth": 7, "learning_rate": 0.05,
        "num_leaves": 63, "class_weight": "balanced",
        "random_state": 42, "n_jobs": -1, "verbose": -1,
    }
    lgbm_model = lgb.LGBMClassifier(**lgbm_params)
    lgbm_model.fit(X_res, y_res)
    results["lightgbm"] = _evaluate(lgbm_model, X_test, y_test)
    _save_model(lgbm_model, disease_type, "lightgbm")

    elapsed = time.time() - start
    logger.info("Training complete", disease=disease_type, elapsed_s=round(elapsed, 1))

    metrics_path = MODEL_DIR / f"{disease_type}_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(results, f, indent=2)

    return results


def _evaluate(model, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
    y_pred  = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    return {
        "roc_auc":       round(roc_auc_score(y_test, y_proba), 4),
        "avg_precision": round(average_precision_score(y_test, y_proba), 4),
        "f1":            round(f1_score(y_test, y_pred), 4),
        "precision":     round(precision_score(y_test, y_pred), 4),
        "recall":        round(recall_score(y_test, y_pred), 4),
    }


def _save_model(model, disease_type: str, model_type: str):
    path = MODEL_DIR / f"{model_type}_{disease_type}.pkl"
    with open(path, "wb") as f:
        pickle.dump(model, f, protocol=pickle.HIGHEST_PROTOCOL)
    logger.info("Model saved", path=str(path))


# ── CLI ───────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train healthcare risk models")
    parser.add_argument("--disease", choices=DISEASE_TYPES + ["all"], default="all")
    parser.add_argument("--tune", action="store_true")
    parser.add_argument("--n-trials", type=int, default=50)
    args = parser.parse_args()

    diseases = DISEASE_TYPES if args.disease == "all" else [args.disease]
    all_results: Dict[str, Any] = {}

    for disease in diseases:
        metrics = train_and_evaluate(disease, tune=args.tune, n_trials=args.n_trials)
        all_results[disease] = metrics
        print(f"\n{'='*55}")
        print(f"  {disease.upper()}")
        for mtype, m in metrics.items():
            print(f"  {mtype:15s}  AUC={m['roc_auc']:.4f}  F1={m['f1']:.4f}  Recall={m['recall']:.4f}")

    print("\n✓ All models trained and saved to ./models/")
