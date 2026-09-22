#!/usr/bin/env python3
"""Execute real open model training run and before/after evaluation (#8338).

Trains a small open model (Qwen/Qwen2.5-0.5B-Instruct) on authentic Russianism
trajectories from uldr_v1_production, records real step-by-step training logs,
and generates predictions before and after training on both held-out evaluation
suites (heldout_evaluation_suite_1000 and dialect_historical_protection_suite_600).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import torch
from peft import LoraConfig, get_peft_model
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, get_cosine_schedule_with_warmup


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


class SFTDataset(Dataset):
    def __init__(self, records: list[dict[str, Any]], tokenizer: Any, max_length: int = 512):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.samples = []
        for r in records:
            query = r.get("query", "").strip()
            final_resp = r.get("final_response", "").strip()
            reasoning = r.get("reasoning_steps", [])
            if not query or not final_resp:
                continue
            thought_str = "\n".join(reasoning) if isinstance(reasoning, list) else str(reasoning)
            assistant_content = f"<thought>\n{thought_str}\n</thought>\n{final_resp}"
            messages = [
                {"role": "user", "content": query},
                {"role": "assistant", "content": assistant_content},
            ]
            try:
                full_text = tokenizer.apply_chat_template(messages, tokenize=False)
                prompt_text = tokenizer.apply_chat_template(messages[:1], tokenize=False, add_generation_prompt=True)
            except Exception:
                continue

            full_enc = tokenizer(full_text, truncation=True, max_length=max_length)
            prompt_enc = tokenizer(prompt_text, truncation=True, max_length=max_length)

            input_ids = full_enc["input_ids"]
            prompt_len = len(prompt_enc["input_ids"])
            labels = [-100] * prompt_len + input_ids[prompt_len:]
            self.samples.append({
                "input_ids": torch.tensor(input_ids, dtype=torch.long),
                "labels": torch.tensor(labels, dtype=torch.long),
            })

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
        return self.samples[idx]


def collate_sft(batch: list[dict[str, torch.Tensor]], pad_token_id: int) -> dict[str, torch.Tensor]:
    max_len = max(len(b["input_ids"]) for b in batch)
    input_ids = []
    attention_mask = []
    labels = []
    for b in batch:
        cur_len = len(b["input_ids"])
        pad_len = max_len - cur_len
        input_ids.append(torch.cat([b["input_ids"], torch.full((pad_len,), pad_token_id, dtype=torch.long)]))
        attention_mask.append(torch.cat([torch.ones(cur_len, dtype=torch.long), torch.zeros(pad_len, dtype=torch.long)]))
        labels.append(torch.cat([b["labels"], torch.full((pad_len,), -100, dtype=torch.long)]))

    return {
        "input_ids": torch.stack(input_ids),
        "attention_mask": torch.stack(attention_mask),
        "labels": torch.stack(labels),
    }


def make_eval_prompt(case: dict[str, Any]) -> str:
    inp = case.get("input_text", "").strip()
    return (
        f"Проаналізуйте наведений текст: «{inp}». Якщо ви виявили кальку, росіянізм чи суржик, "
        f"виправте на нормативне українське слово та поясніть. Якщо текст автентичний і нормативний "
        f"(включаючи діалекти та історичні пам'ятки), збережіть його без змін."
    )


def generate_predictions_batch(
    model: Any,
    tokenizer: Any,
    cases: list[dict[str, Any]],
    device: str,
    batch_size: int = 16,
    max_new_tokens: int = 120,
) -> list[dict[str, str]]:
    model.eval()
    tokenizer.padding_side = "left"
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    results: list[dict[str, str]] = []
    total = len(cases)
    print(f"Generating predictions for {total} cases (batch_size={batch_size})...")
    t0 = time.time()

    for i in range(0, total, batch_size):
        chunk = cases[i : i + batch_size]
        prompts = [make_eval_prompt(c) for c in chunk]
        chat_texts = [
            tokenizer.apply_chat_template([{"role": "user", "content": p}], tokenize=False, add_generation_prompt=True)
            for p in prompts
        ]
        enc = tokenizer(chat_texts, return_tensors="pt", padding=True, truncation=True, max_length=512).to(device)
        with torch.no_grad():
            gen_ids = model.generate(
                **enc,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id,
            )
        for c, g, in_ids in zip(chunk, gen_ids, enc.input_ids, strict=False):
            out_tokens = g[len(in_ids) :]
            resp = tokenizer.decode(out_tokens, skip_special_tokens=True).strip()
            eid = c.get("eval_id") or c.get("id")
            results.append({"eval_id": eid, "prediction": resp})

        if (i // batch_size + 1) % 10 == 0 or (i + batch_size) >= total:
            elapsed = time.time() - t0
            done = min(i + batch_size, total)
            print(f"  Processed {done}/{total} in {elapsed:.1f}s ({done/elapsed:.1f} seq/s)")

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Real open model training and evaluation (#8338)")
    parser.add_argument("--train-file", type=Path, required=True, help="Path to 6,000-example train JSONL")
    parser.add_argument("--heldout-file", type=Path, required=True, help="Path to 1,000-case held-out suite JSONL")
    parser.add_argument("--protection-file", type=Path, required=True, help="Path to 600-case protection suite JSONL")
    parser.add_argument("--output-dir", type=Path, default=Path("run_output"), help="Output directory")
    parser.add_argument("--model-name", type=str, default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--max-steps", type=int, default=300)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--grad-accum", type=int, default=2)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--lora-r", type=int, default=16)
    parser.add_argument("--lora-alpha", type=int, default=32)
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    device = args.device
    print(f"Using device: {device}")

    # Check fingerprints
    train_sha = sha256_file(args.train_file)
    heldout_sha = sha256_file(args.heldout_file)
    prot_sha = sha256_file(args.protection_file)
    print(f"Train file: {args.train_file} (SHA-256: {train_sha})")
    print(f"Heldout file: {args.heldout_file} (SHA-256: {heldout_sha})")
    print(f"Protection file: {args.protection_file} (SHA-256: {prot_sha})")

    # Load eval cases
    heldout_cases = [json.loads(line) for line in args.heldout_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    prot_cases = [json.loads(line) for line in args.protection_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    print(f"Loaded {len(heldout_cases)} held-out cases and {len(prot_cases)} protection cases.")

    # Load tokenizer and base model
    print(f"Loading base model: {args.model_name}...")
    dtype = torch.float16 if device == "cuda" else torch.float32
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    model = AutoModelForCausalLM.from_pretrained(args.model_name, dtype=dtype, device_map=device)

    num_layers = getattr(model.config, "num_hidden_layers", None)
    hidden_size = getattr(model.config, "hidden_size", None)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"Base model loaded: {num_layers} layers, hidden_size={hidden_size}, total_params={total_params:,}")

    # Step 1: Baseline Inference (Before Training)
    print("\n--- PHASE 1: Baseline Inference (Before Training) ---")
    base_heldout_path = args.output_dir / "preds_baseline_heldout_1000.jsonl"
    base_prot_path = args.output_dir / "preds_baseline_protection_600.jsonl"

    if base_heldout_path.exists() and base_prot_path.exists():
        print(f"Baseline predictions already exist at {base_heldout_path} and {base_prot_path}, skipping generation.")
    else:
        base_heldout_preds = generate_predictions_batch(model, tokenizer, heldout_cases, device, batch_size=16)
        with base_heldout_path.open("w", encoding="utf-8") as f:
            for p in base_heldout_preds:
                f.write(json.dumps(p, ensure_ascii=False) + "\n")

        base_prot_preds = generate_predictions_batch(model, tokenizer, prot_cases, device, batch_size=16)
        with base_prot_path.open("w", encoding="utf-8") as f:
            for p in base_prot_preds:
                f.write(json.dumps(p, ensure_ascii=False) + "\n")

        print(f"Baseline predictions saved to {base_heldout_path} and {base_prot_path}")

    # Step 2: Training Run
    print("\n--- PHASE 2: LoRA Fine-Tuning Run ---")
    train_records = [json.loads(line) for line in args.train_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    print(f"Loaded {len(train_records)} training records.")

    if hasattr(model, "gradient_checkpointing_enable"):
        model.gradient_checkpointing_enable()

    lora_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    )
    lora_model = get_peft_model(model, lora_config)
    trainable_params = sum(p.numel() for p in lora_model.parameters() if p.requires_grad)
    print(f"LoRA attached: {trainable_params:,} trainable params ({trainable_params/total_params*100:.2f}% of model)")

    dataset = SFTDataset(train_records, tokenizer, max_length=384)
    pad_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else 0
    dataloader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=True,
        collate_fn=lambda b: collate_sft(b, pad_id),
    )

    optimizer = torch.optim.AdamW(lora_model.parameters(), lr=args.lr, weight_decay=0.01)
    max_steps = min(args.max_steps, len(dataloader) * args.epochs)
    scheduler = get_cosine_schedule_with_warmup(optimizer, num_warmup_steps=20, num_training_steps=max_steps)

    lora_model.train()
    training_logs: list[dict[str, Any]] = []
    step = 0
    t_train_start = time.time()
    accum_loss = 0.0

    print(f"Starting training for {max_steps} steps (batch_size={args.batch_size}, grad_accum={args.grad_accum})...")
    for epoch in range(args.epochs):
        for b_idx, batch in enumerate(dataloader):
            batch = {k: v.to(device) for k, v in batch.items()}
            outputs = lora_model(**batch)
            loss = outputs.loss / args.grad_accum
            loss.backward()
            accum_loss += loss.item() * args.grad_accum

            if (b_idx + 1) % args.grad_accum == 0 or (b_idx + 1) == len(dataloader):
                torch.nn.utils.clip_grad_norm_(lora_model.parameters(), 1.0)
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()
                step += 1

                step_entry = {
                    "step": step,
                    "epoch": epoch + 1,
                    "loss": round(accum_loss, 4),
                    "lr": round(scheduler.get_last_lr()[0], 8),
                    "elapsed_s": round(time.time() - t_train_start, 2),
                }
                training_logs.append(step_entry)

                if step % 25 == 0 or step == 1 or step == max_steps:
                    print(f"  Step {step}/{max_steps} | Epoch {epoch+1} | Loss: {accum_loss:.4f} | LR: {step_entry['lr']} | Elapsed: {step_entry['elapsed_s']}s")

                accum_loss = 0.0
                if step >= max_steps:
                    break
        if step >= max_steps:
            break

    # Save training log and adapter
    training_log_path = args.output_dir / "training_log.jsonl"
    with training_log_path.open("w", encoding="utf-8") as f:
        for entry in training_logs:
            f.write(json.dumps(entry) + "\n")

    adapter_dir = args.output_dir / "adapter"
    lora_model.save_pretrained(adapter_dir)
    print(f"Adapter saved to {adapter_dir}")

    # Inspect adapter safetensors
    adapter_file = adapter_dir / "adapter_model.safetensors"
    adapter_sha = sha256_file(adapter_file) if adapter_file.exists() else "none"
    print(f"Saved adapter file: {adapter_file} (SHA-256: {adapter_sha})")

    # Step 3: Aligned Inference (After Training)
    print("\n--- PHASE 3: Aligned Inference (After Training) ---")
    trained_heldout_preds = generate_predictions_batch(lora_model, tokenizer, heldout_cases, device, batch_size=16)
    trained_heldout_path = args.output_dir / "preds_trained_heldout_1000.jsonl"
    with trained_heldout_path.open("w", encoding="utf-8") as f:
        for p in trained_heldout_preds:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    trained_prot_preds = generate_predictions_batch(lora_model, tokenizer, prot_cases, device, batch_size=16)
    trained_prot_path = args.output_dir / "preds_trained_protection_600.jsonl"
    with trained_prot_path.open("w", encoding="utf-8") as f:
        for p in trained_prot_preds:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    print(f"Trained predictions saved to {trained_heldout_path} and {trained_prot_path}")

    # Step 4: Write Run Manifest
    manifest = {
        "timestamp": datetime.now(UTC).isoformat(),
        "model_name": args.model_name,
        "device": device,
        "gpu_name": torch.cuda.get_device_name(0) if device == "cuda" else "CPU",
        "num_layers": num_layers,
        "hidden_size": hidden_size,
        "total_parameters": total_params,
        "trainable_parameters": trainable_params,
        "lora_r": args.lora_r,
        "lora_alpha": args.lora_alpha,
        "learning_rate": args.lr,
        "total_steps": step,
        "initial_loss": training_logs[0]["loss"] if training_logs else None,
        "final_loss": training_logs[-1]["loss"] if training_logs else None,
        "loss_reduction_pct": round((1.0 - training_logs[-1]["loss"] / training_logs[0]["loss"]) * 100, 2) if training_logs and training_logs[0]["loss"] > 0 else 0.0,
        "fingerprints": {
            "train_file": str(args.train_file),
            "train_sha256": train_sha,
            "train_records": len(train_records),
            "heldout_file": str(args.heldout_file),
            "heldout_sha256": heldout_sha,
            "heldout_cases": len(heldout_cases),
            "protection_file": str(args.protection_file),
            "protection_sha256": prot_sha,
            "protection_cases": len(prot_cases),
            "adapter_sha256": adapter_sha,
        },
    }
    manifest_path = args.output_dir / "training_run_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Run manifest written to {manifest_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
