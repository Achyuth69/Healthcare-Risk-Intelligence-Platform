"""
Application Configuration
Centralized settings management using Pydantic BaseSettings.
"""
from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Application ──────────────────────────────────────────
    APP_NAME: str = "HealthRiskAI"
    APP_ENV: str = "development"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str

    # ── Database ─────────────────────────────────────────────
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # ── JWT ──────────────────────────────────────────────────
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Redis ────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── ChromaDB ─────────────────────────────────────────────
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001
    CHROMA_COLLECTION_NAME: str = "healthcare_docs"

    # ── LLM / HuggingFace ────────────────────────────────────
    HUGGINGFACE_TOKEN: Optional[str] = None
    LLM_MODEL_NAME: str = "meta-llama/Meta-Llama-3-8B-Instruct"
    FINE_TUNED_MODEL_PATH: str = "/models/llama3-healthcare-finetuned"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # ── AWS ──────────────────────────────────────────────────
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = "healthrisk-models"
    S3_PDF_BUCKET: str = "healthrisk-documents"

    # ── Encryption ───────────────────────────────────────────
    ENCRYPTION_KEY: str

    # ── CORS ─────────────────────────────────────────────────
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v: str) -> str:
        return v

    def get_allowed_origins(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    # ── Model Paths ──────────────────────────────────────────
    MODEL_ARTIFACTS_DIR: str = "/app/models"
    XGBOOST_MODEL_PATH: str = "/app/models/xgboost_risk_model.pkl"
    RF_MODEL_PATH: str = "/app/models/rf_risk_model.pkl"
    LGBM_MODEL_PATH: str = "/app/models/lgbm_risk_model.pkl"
    SCALER_PATH: str = "/app/models/feature_scaler.pkl"
    FEATURE_NAMES_PATH: str = "/app/models/feature_names.json"

    # ── Logging ──────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # ── Monitoring ───────────────────────────────────────────
    PROMETHEUS_PORT: int = 9090


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance — call once, reuse everywhere."""
    return Settings()


settings = get_settings()
