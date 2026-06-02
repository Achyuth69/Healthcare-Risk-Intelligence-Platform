"""
API v1 Router — Aggregates all endpoint routers.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, patients, predictions, explanations, rag, admin

api_router = APIRouter()

api_router.include_router(auth.router,         prefix="/auth",         tags=["Authentication"])
api_router.include_router(patients.router,     prefix="/patients",     tags=["Patients"])
api_router.include_router(predictions.router,  prefix="/predictions",  tags=["Predictions"])
api_router.include_router(explanations.router, prefix="/explanations", tags=["Explainability"])
api_router.include_router(rag.router,          prefix="/rag",          tags=["RAG / LLM"])
api_router.include_router(admin.router,        prefix="/admin",        tags=["Admin"])
