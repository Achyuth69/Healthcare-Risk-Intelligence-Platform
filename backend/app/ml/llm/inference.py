"""
LLM Inference Engine — Auto-selects backend:
  1. Groq API (free, Llama 3 70B) — if GROQ_API_KEY is set
  2. Local fine-tuned model       — if FINE_TUNED_MODEL_PATH exists + GPU available
  3. Mock fallback                — always works, no dependencies
"""
import os
from typing import Optional
import structlog

logger = structlog.get_logger(__name__)


class LLMInferenceEngine:
    """Unified LLM engine — delegates to the best available backend."""

    _instance: Optional["LLMInferenceEngine"] = None

    def __init__(self):
        self._backend = None
        self._backend_name = "mock"

    @classmethod
    async def initialize(cls) -> "LLMInferenceEngine":
        if cls._instance is None:
            cls._instance = cls()
            await cls._instance._select_backend()
        return cls._instance

    @classmethod
    def get_instance(cls) -> "LLMInferenceEngine":
        if cls._instance is None:
            cls._instance = cls()
            # Sync init — pick Groq if key present, else mock
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Schedule async init
                    loop.create_task(cls._instance._select_backend())
                else:
                    loop.run_until_complete(cls._instance._select_backend())
            except Exception:
                cls._instance._use_mock()
        return cls._instance

    async def _select_backend(self):
        # Priority 1: Groq API (free, no GPU needed)
        if os.getenv("GROQ_API_KEY"):
            try:
                from app.ml.llm.groq_inference import GroqInferenceEngine
                self._backend = await GroqInferenceEngine.initialize()
                self._backend_name = "groq"
                logger.info("LLM backend: Groq (Llama 3 70B)")
                return
            except Exception as e:
                logger.warning("Groq init failed", error=str(e))

        # Priority 2: Local fine-tuned model (needs GPU + transformers)
        try:
            import torch
            from pathlib import Path
            from app.config import settings
            model_path = Path(settings.FINE_TUNED_MODEL_PATH) / "merged"
            if model_path.exists() and torch.cuda.is_available():
                from app.ml.llm._local_inference import LocalInferenceEngine
                self._backend = await LocalInferenceEngine.initialize()
                self._backend_name = "local"
                logger.info("LLM backend: Local fine-tuned model")
                return
        except Exception as e:
            logger.warning("Local model init failed", error=str(e))

        # Priority 3: Mock fallback
        self._use_mock()

    def _use_mock(self):
        from app.ml.llm.groq_inference import GroqInferenceEngine
        self._backend = GroqInferenceEngine()  # works in mock mode without key
        self._backend_name = "mock"
        logger.info("LLM backend: mock (set GROQ_API_KEY for real responses)")

    async def generate(self, prompt: str, max_tokens: int = 512) -> str:
        if self._backend is None:
            self._use_mock()
        return await self._backend.generate(prompt, max_tokens)
