"""
Test Configuration — Fixtures for pytest
"""
import pytest
import asyncio
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.core.security import create_access_token
from app.core.rbac import Role


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def auth_headers():
    """Generate valid JWT headers for a clinician user."""
    token = create_access_token(
        subject="test-user-id",
        extra_claims={"email": "test@test.com", "role": Role.CLINICIAN.value},
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers():
    """Generate valid JWT headers for an admin user."""
    token = create_access_token(
        subject="admin-user-id",
        extra_claims={"email": "admin@test.com", "role": Role.ADMIN.value},
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def mock_model_registry():
    """Mock the ML model registry for all tests."""
    with pytest.MonkeyPatch.context() as mp:
        mock_registry = MagicMock()
        mock_registry.predict = AsyncMock(return_value=(0.65, 0.88, "mock-1.0.0"))
        mock_registry.get_feature_importance = MagicMock(
            return_value={"glucose_level": 0.25, "bmi": 0.18, "age": 0.15}
        )
        mock_registry.get_model = MagicMock(return_value=MagicMock())

        from app.ml import model_registry
        mp.setattr(model_registry.ModelRegistry, "_instance", mock_registry)
        mp.setattr(model_registry.ModelRegistry, "get_instance", lambda: mock_registry)
        yield mock_registry


@pytest.fixture(autouse=True)
def mock_rag_pipeline():
    """Mock the RAG pipeline for all tests."""
    with pytest.MonkeyPatch.context() as mp:
        mock_rag = MagicMock()
        mock_rag.generate_clinical_narrative = AsyncMock(
            return_value="Mock clinical narrative for testing."
        )
        mock_rag.query = AsyncMock(return_value=MagicMock(
            query="test",
            answer="Mock answer",
            sources=[],
            confidence=0.9,
            processing_time_ms=100.0,
        ))

        from app.rag import pipeline
        mp.setattr(pipeline.RAGPipeline, "_instance", mock_rag)
        mp.setattr(pipeline.RAGPipeline, "get_instance", lambda: mock_rag)
        yield mock_rag
