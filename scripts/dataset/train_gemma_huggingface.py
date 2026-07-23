"""HuggingFace SFT Trainer Script for Fine-Tuning Gemma 4 31B on Literary Ukrainian.

Usage:
    pip install transformers datasets peft trl accelerate bitsandbytes
    python scripts/dataset/train_gemma_huggingface.py \
        --dataset_path data/datasets/hramatka_literary_poltava_v1/hramatka_literary_poltava_v1.jsonl \
        --model_id google/gemma-4-31b-it \
        --output_dir ./gemma-4-31b-uk-poltava-lora
"""

import argparse
import os

import torch
from datasets import load_dataset
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from trl import SFTTrainer


def train():
    parser = argparse.ArgumentParser(description="Fine-tune Gemma 4 31B on Literary Ukrainian")
    parser.add_argument(
        "--dataset_path",
        type=str,
        default="data/datasets/hramatka_literary_poltava_v1/hramatka_literary_poltava_v1.jsonl",
    )
    parser.add_argument("--model_id", type=str, default="google/gemma-4-31b-it")
    parser.add_argument("--output_dir", type=str, default="./gemma-4-31b-uk-poltava-lora")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=2)
    parser.add_argument("--learning_rate", type=float, default=2e-4)
    args = parser.parse_args()

    print(f"Loading dataset from {args.dataset_path}...")
    dataset = load_dataset("json", data_files=args.dataset_path, split="train")

    def formatting_func(example):
        text = example["text"]
        author = example.get("author", "")
        work = example.get("work", "")
        prompt = f"<|im_start|>system\nТи — видатний український письменник і редактор класичної української літератури.<|im_end|>\n<|im_start|>user\nНапиши фрагмент тексту у стилі української літературної класики (автор: {author}, твір: {work}):<|im_end|>\n<|im_start|>assistant\n{text}<|im_end|>"
        return prompt

    print("Configuring 4-bit QLoRA quantization...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    print(f"Loading tokenizer and model {args.model_id}...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_id, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        args.model_id,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )

    model = prepare_model_for_kbit_training(model)

    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )

    training_args = TrainingArguments(
        output_dir=args.output_dir,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=4,
        learning_rate=args.learning_rate,
        logging_steps=10,
        num_train_epochs=args.epochs,
        optim="paged_adamw_8bit",
        fp16=False,
        bf16=True,
        max_grad_norm=0.3,
        warmup_ratio=0.03,
        lr_scheduler_type="constant",
        save_strategy="epoch",
        push_to_hub=False,
    )

    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        peft_config=lora_config,
        formatting_func=formatting_func,
        max_seq_length=1024,
        tokenizer=tokenizer,
        args=training_args,
    )

    print("Starting SFT Fine-Tuning for Gemma 4 31B...")
    trainer.train()

    print(f"Saving fine-tuned LoRA weights to {args.output_dir}...")
    trainer.model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    print("Fine-tuning completed successfully!")


if __name__ == "__main__":
    train()
