"""
Groq LLM Inference — Free Llama 3 via Groq API
Replaces local model inference for free-tier deployment.
Groq free tier: 14,400 req/day, ~330 tokens/sec on Llama 3 70B.
"""
import asyncio
import os
import json
import urllib.request
import urllib.error
import structlog
from typing import Optional

logger = structlog.get_logger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_PROMPT = (
    "You are a clinical AI assistant specialising in disease risk assessment. "
    "Provide clear, evidence-based, empathetic explanations in plain language. "
    "Always recommend consulting a qualified healthcare professional."
)


class GroqInferenceEngine:
    """
    Calls Groq's free API for Llama 3 inference.
    Falls back to a rule-based response if API key is missing.
    """

    _instance: Optional["GroqInferenceEngine"] = None

    def __init__(self):
        from app.config import settings
        self._api_key = settings.GROQ_API_KEY or ""
        self._model   = settings.GROQ_MODEL
        self._ready   = bool(self._api_key)
        if self._ready:
            logger.info("Groq LLM engine ready", model=self._model)
        else:
            logger.warning("GROQ_API_KEY not set — LLM running in mock mode")

    @classmethod
    def get_instance(cls) -> "GroqInferenceEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    async def initialize(cls) -> "GroqInferenceEngine":
        cls._instance = cls()
        return cls._instance

    async def generate(self, prompt: str, max_tokens: int = 512) -> str:
        if not self._ready:
            return self._mock_response(prompt)
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._call_groq, prompt, max_tokens)

    def _call_groq(self, prompt: str, max_tokens: int) -> str:
        payload = json.dumps({
            "model": self._model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": 0.3,
        }).encode("utf-8")

        req = urllib.request.Request(
            GROQ_API_URL,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
                return data["choices"][0]["message"]["content"].strip()
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            logger.error("Groq API error", status=e.code, body=body)
            return self._mock_response(prompt)
        except Exception as e:
            logger.error("Groq call failed", error=str(e))
            return self._mock_response(prompt)

    @staticmethod
    def _mock_response(prompt: str) -> str:
        return (
            "Based on the clinical data provided, this patient shows risk factors "
            "that warrant medical attention. Key contributors include metabolic "
            "indicators and lifestyle factors identified by the AI model.\n\n"
            "**Recommended actions:**\n"
            "- Schedule a follow-up with a primary care physician\n"
            "- Review lifestyle modification options (diet, exercise)\n"
            "- Repeat laboratory testing in 3–6 months\n\n"
            "*Set GROQ_API_KEY environment variable for full AI-generated narratives.*"
        )
