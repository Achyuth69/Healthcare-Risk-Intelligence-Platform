"""
Local Fine-Tuned Model Inference
Only used when a GPU is available and FINE_TUNED_MODEL_PATH/merged exists.
Requires: torch, transformers, peft (install from requirements.txt GPU section).
"""
from typing import Optional
import asyncio
import structlog

logger = structlog.get_logger(__name__)


class LocalInferenceEngine:
    """Loads a locally fine-tuned Llama 3 model for inference."""

    _instance: Optional["LocalInferenceEngine"] = None

    def __init__(self):
        self._pipeline = None
        self._tokenizer = None
        self._ready = False

    @classmethod
    async def initialize(cls) -> "LocalInferenceEngine":
        if cls._instance is None:
            cls._instance = cls()
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, cls._instance._load)
        return cls._instance

    def _load(self):
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline, BitsAndBytesConfig
            from app.config import settings
            from pathlib import Path

            model_path = str(Path(settings.FINE_TUNED_MODEL_PATH) / "merged")
            logger.info("Loading local fine-tuned model", path=model_path)

            bnb = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
            )
            self._tokenizer = AutoTokenizer.from_pretrained(model_path)
            self._tokenizer.pad_token = self._tokenizer.eos_token

            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                quantization_config=bnb,
                device_map="auto",
                torch_dtype=torch.float16,
            )
            self._pipeline = pipeline(
                "text-generation", model=model, tokenizer=self._tokenizer,
                max_new_tokens=512, temperature=0.3, top_p=0.9,
                repetition_penalty=1.1, do_sample=True,
            )
            self._ready = True
            logger.info("Local model loaded successfully")
        except Exception as e:
            logger.error("Local model load failed", error=str(e))
            self._ready = False

    async def generate(self, prompt: str, max_tokens: int = 512) -> str:
        if not self._ready:
            return "Local model not available. Set GROQ_API_KEY for AI narratives."
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._run, prompt, max_tokens)

    def _run(self, prompt: str, max_tokens: int) -> str:
        from app.ml.llm.groq_inference import GroqInferenceEngine
        messages = [
            {"role": "system", "content": "You are a clinical AI assistant."},
            {"role": "user", "content": prompt},
        ]
        formatted = self._tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        out = self._pipeline(formatted, max_new_tokens=max_tokens,
                             pad_token_id=self._tokenizer.eos_token_id)
        generated = out[0]["generated_text"]
        return generated[len(formatted):].strip()
