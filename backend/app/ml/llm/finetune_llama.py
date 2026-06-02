"""
Llama 3 Fine-Tuning Pipeline — QLoRA + PEFT + SFTTrainer
Trains the model on clinical risk explanation data.

Usage:
    python -m app.ml.llm.finetune_llama \
        --model  meta-llama/Meta-Llama-3-8B-Instruct \
        --output ./models/llama3-healthcare \
        --epochs 3 \
        --hf-token YOUR_TOKEN
"""
import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import torch
import structlog

logger = structlog.get_logger(__name__)


# ── Configuration ─────────────────────────────────────────────

@dataclass
class FineTuneConfig:
    # Model
    base_model: str = "meta-llama/Meta-Llama-3-8B-Instruct"
    output_dir: str = "./models/llama3-healthcare"
    hf_token: Optional[str] = None

    # QLoRA quantisation
    use_4bit: bool = True
    bnb_4bit_compute_dtype: str = "float16"
    bnb_4bit_quant_type: str = "nf4"
    use_nested_quant: bool = True

    # LoRA
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    lora_target_modules: list = field(default_factory=lambda: [
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ])

    # Training
    num_epochs: int = 3
    per_device_train_batch_size: int = 4
    gradient_accumulation_steps: int = 4
    learning_rate: float = 2e-4
    max_seq_length: int = 2048
    warmup_ratio: float = 0.03
    lr_scheduler_type: str = "cosine"
    weight_decay: float = 0.001
    fp16: bool = True
    bf16: bool = False
    logging_steps: int = 10
    save_steps: int = 100
    eval_steps: int = 100


# ── Training examples ─────────────────────────────────────────

SYSTEM_PROMPT = (
    "You are a clinical AI assistant specialising in disease risk assessment. "
    "You provide clear, evidence-based explanations of patient risk factors in plain "
    "language that both clinicians and patients can understand. Always be accurate, "
    "empathetic, and recommend consulting healthcare professionals for medical decisions."
)


def _training_examples() -> list[dict]:
    """
    Curated clinical risk explanation examples.
    In production replace with real de-identified clinical narratives.
    """
    return [
        {
            "instruction": (
                "Explain the diabetes risk for a 52-year-old male with BMI 32, "
                "fasting glucose 118 mg/dL, HbA1c 6.1 %, and family history of diabetes."
            ),
            "response": (
                "Based on the clinical data, this patient has a **moderate-to-high risk** "
                "of developing Type 2 Diabetes (estimated ~68 %).\n\n"
                "**Key risk factors:**\n"
                "1. **Elevated fasting glucose (118 mg/dL)** — pre-diabetic range (100–125). "
                "Strongest predictor in this profile.\n"
                "2. **HbA1c 6.1 %** — also pre-diabetic (5.7–6.4 %), confirming sustained "
                "elevated blood sugar over 3 months.\n"
                "3. **Obesity (BMI 32)** — visceral fat drives insulin resistance. "
                "Even a 5–7 % weight reduction significantly lowers risk.\n"
                "4. **Family history** — first-degree relatives increase genetic susceptibility ~40 %.\n"
                "5. **Age 52** — risk rises substantially after 45.\n\n"
                "**Recommended actions:**\n"
                "- 150 min/week moderate exercise + Mediterranean diet\n"
                "- Target 5–10 % body weight reduction\n"
                "- Repeat HbA1c in 3–6 months\n"
                "- Discuss metformin with physician if lifestyle changes are insufficient\n\n"
                "*This assessment is for informational purposes. "
                "Please consult your healthcare provider for personalised advice.*"
            ),
        },
        {
            "instruction": (
                "A 65-year-old female has LDL 175 mg/dL, BP 148/92 mmHg, "
                "is a former smoker, and has a family history of heart disease. "
                "What is her cardiovascular risk?"
            ),
            "response": (
                "This patient presents with **high cardiovascular risk** "
                "(estimated ~72 % 10-year risk of a major cardiac event).\n\n"
                "**Risk factor analysis:**\n"
                "1. **Elevated LDL (175 mg/dL)** — well above the <100 mg/dL target for "
                "high-risk patients. LDL is the primary driver of atherosclerotic plaque.\n"
                "2. **Stage 2 hypertension (148/92)** — damages arterial walls; "
                "major independent risk factor for MI and stroke.\n"
                "3. **Former smoker** — residual elevated risk persists 10–15 years post-cessation.\n"
                "4. **Post-menopausal female** — loss of oestrogen's cardioprotective effect.\n"
                "5. **Family history** — premature CAD in first-degree relatives signals "
                "genetic predisposition.\n\n"
                "**Clinical recommendations:**\n"
                "- High-intensity statin therapy (target LDL <70 mg/dL)\n"
                "- Antihypertensive: ACE inhibitor or ARB + thiazide diuretic\n"
                "- Aspirin: discuss risk/benefit with cardiologist\n"
                "- Annual cardiovascular monitoring\n\n"
                "*Please consult a cardiologist for comprehensive evaluation.*"
            ),
        },
        {
            "instruction": (
                "Explain what SHAP values mean for a patient's diabetes prediction "
                "where glucose_level has SHAP value +0.23 and physical_activity has SHAP value -0.15."
            ),
            "response": (
                "**Understanding your risk explanation (SHAP analysis)**\n\n"
                "SHAP values show how much each factor *pushed* your risk score up or down "
                "from the population average.\n\n"
                "📈 **Glucose level (+0.23)** — Your fasting glucose is *increasing* your "
                "diabetes risk by 23 percentage points above baseline. "
                "This is the strongest risk-elevating factor in your profile.\n\n"
                "📉 **Physical activity (−0.15)** — Your activity level is *reducing* your "
                "risk by 15 percentage points. Regular exercise improves insulin sensitivity "
                "and is a meaningful protective factor.\n\n"
                "**How to read SHAP values:**\n"
                "- Positive (↑) = factor increases your risk\n"
                "- Negative (↓) = factor decreases your risk\n"
                "- Larger absolute value = stronger influence\n\n"
                "**What this means for you:** Focus on dietary changes to lower glucose "
                "while maintaining your exercise routine — it is already working in your favour.\n\n"
                "*Always discuss these results with your healthcare provider.*"
            ),
        },
    ]


def _format_prompt(example: dict, tokenizer) -> str:
    messages = [
        {"role": "system",    "content": SYSTEM_PROMPT},
        {"role": "user",      "content": example["instruction"]},
        {"role": "assistant", "content": example["response"]},
    ]
    return tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=False
    )


def _prepare_dataset(tokenizer, n_synthetic: int = 1000):
    from datasets import Dataset

    base = _training_examples()
    formatted = [{"text": _format_prompt(ex, tokenizer)} for ex in base]

    # Repeat to reach n_synthetic (replace with real data in production)
    augmented = (formatted * (n_synthetic // len(formatted) + 1))[:n_synthetic]

    ds = Dataset.from_list(augmented).train_test_split(test_size=0.1, seed=42)
    logger.info("Dataset ready", train=len(ds["train"]), eval=len(ds["test"]))
    return ds


# ── Fine-tuning pipeline ──────────────────────────────────────

def finetune(config: FineTuneConfig):
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
        TrainingArguments,
    )
    from peft import LoraConfig, TaskType, get_peft_model, prepare_model_for_kbit_training
    from trl import SFTTrainer

    logger.info("Starting Llama 3 fine-tuning", model=config.base_model)

    # 1. Quantisation config (QLoRA)
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=config.use_4bit,
        bnb_4bit_quant_type=config.bnb_4bit_quant_type,
        bnb_4bit_compute_dtype=getattr(torch, config.bnb_4bit_compute_dtype),
        bnb_4bit_use_double_quant=config.use_nested_quant,
    )

    # 2. Load base model
    logger.info("Loading base model with 4-bit quantisation")
    model = AutoModelForCausalLM.from_pretrained(
        config.base_model,
        quantization_config=bnb_config,
        device_map="auto",
        token=config.hf_token,
        trust_remote_code=True,
    )
    model.config.use_cache = False
    model.config.pretraining_tp = 1

    # 3. Tokeniser
    tokenizer = AutoTokenizer.from_pretrained(
        config.base_model, token=config.hf_token, trust_remote_code=True
    )
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    # 4. Prepare for k-bit training
    model = prepare_model_for_kbit_training(model)

    # 5. LoRA config
    lora_config = LoraConfig(
        r=config.lora_r,
        lora_alpha=config.lora_alpha,
        target_modules=config.lora_target_modules,
        lora_dropout=config.lora_dropout,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # 6. Dataset
    dataset = _prepare_dataset(tokenizer)

    # 7. Training arguments
    training_args = TrainingArguments(
        output_dir=config.output_dir,
        num_train_epochs=config.num_epochs,
        per_device_train_batch_size=config.per_device_train_batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        optim="paged_adamw_32bit",
        save_steps=config.save_steps,
        logging_steps=config.logging_steps,
        learning_rate=config.learning_rate,
        weight_decay=config.weight_decay,
        fp16=config.fp16,
        bf16=config.bf16,
        max_grad_norm=0.3,
        warmup_ratio=config.warmup_ratio,
        group_by_length=True,
        lr_scheduler_type=config.lr_scheduler_type,
        report_to="tensorboard",
        evaluation_strategy="steps",
        eval_steps=config.eval_steps,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
    )

    # 8. SFT Trainer
    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset["train"],
        eval_dataset=dataset["test"],
        peft_config=lora_config,
        dataset_text_field="text",
        max_seq_length=config.max_seq_length,
        tokenizer=tokenizer,
        args=training_args,
        packing=False,
    )

    # 9. Train
    logger.info("Training started")
    trainer.train()

    # 10. Save adapter + merged model
    out = Path(config.output_dir)
    trainer.model.save_pretrained(out / "lora_adapter")
    tokenizer.save_pretrained(out / "lora_adapter")

    logger.info("Merging LoRA weights into base model")
    merged = trainer.model.merge_and_unload()
    merged.save_pretrained(out / "merged")
    tokenizer.save_pretrained(out / "merged")

    logger.info("Fine-tuning complete", output=str(out))


# ── CLI ───────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fine-tune Llama 3 for healthcare")
    parser.add_argument("--model",      default="meta-llama/Meta-Llama-3-8B-Instruct")
    parser.add_argument("--output",     default="./models/llama3-healthcare")
    parser.add_argument("--epochs",     type=int, default=3)
    parser.add_argument("--hf-token",   default=None)
    parser.add_argument("--lora-r",     type=int, default=16)
    parser.add_argument("--batch-size", type=int, default=4)
    args = parser.parse_args()

    cfg = FineTuneConfig(
        base_model=args.model,
        output_dir=args.output,
        num_epochs=args.epochs,
        hf_token=args.hf_token,
        lora_r=args.lora_r,
        per_device_train_batch_size=args.batch_size,
    )
    finetune(cfg)
