# Ukrainian Linguistic Decolonization & Reasoning (ULDR): Downstream Training & Evaluation Guide

This guide provides reproducible downstream fine-tuning recipes, data formatting specifications, and evaluation procedures for the **Ukrainian Linguistic Decolonization & Reasoning (ULDR)** dataset family.

---

## 1. Project Invariants & Scope Boundary

As mandated by Stream Epic **#6321** and the repository's permanent non-commercial policy:
- **Project Scope**: The repository produces verified, provenance-rich datasets, cryptographic manifests, deterministic evaluation canaries, and consumer reproducibility recipes.
- **Boundary Invariant**: No project-owned model training, inference compute, paid weight production, or external model hosting is executed within this repository. Adoption and fine-tuned checkpoints remain downstream community activities.
- **License**: All prepared datasets and recipes are released under open, non-commercial terms for research and educational advancement of the Ukrainian language.

---

## 2. Dataset Architecture & Partition Firewall

The ULDR dataset consists of **1,200 normative SFT reasoning trajectories** and **1,200 contrastive DPO preference pairs** divided into strict partitions:

| Partition | Share | Records | Shards | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Train** | ~80% | 967 | 3 shards | Supervised fine-tuning (SFT) and preference alignment (DPO) |
| **Held-Out** | ~20% | 233 | 1 shard | Contamination-firewalled evaluation benchmark |

### Partition Isolation Guarantee
Partitioning is keyed on `hashlib.sha256("uldr_partition_v1:" + normalized_target_term)`. All trajectories, contrastive pairs, and alternatives for a given calque exist **exclusively** in either `train` or `held_out`. The manifest explicitly asserts `train_held_out_overlap_count: 0`.

---

## 3. Preparing Consumer Formats

To convert the primary canonical shards into standard training formats (ShareGPT / ChatML with `<thought>` tags, and Hugging Face TRL DPO format), run:

```bash
python scripts/projects/open_model_data/v4_format_decolonization.py \
    --input-dir data/projects/open_model_data/decolonization/generated \
    --out-dir data/projects/open_model_data/decolonization/consumer \
    --records-per-shard 400
```

This generates sharded consumer files adhering to the `< 2,000,000 bytes` repository file limit:
- `uldr_sharegpt_train_part001.jsonl` .. `part003.jsonl` (967 records)
- `uldr_sharegpt_held_out_part001.jsonl` (233 records)
- `uldr_dpo_train_part001.jsonl` .. `part003.jsonl` (967 records)
- `uldr_dpo_held_out_part001.jsonl` (233 records)
- `consumer_formats_manifest.json` (cryptographic record of hashes and byte counts)

---

## 4. Consumer Training Recipes

### 4.1 Stage 1: SFT with Thought Reasoning (Unsloth / TRL)

The ShareGPT dataset incorporates explicit `<thought> ... </thought>` tags demonstrating the 5-step diagnostic procedure (morphemic analysis, Soviet unification suppression history, MESU curriculum attestation, VESUM validation, and register spectrum).

```python
import torch
from datasets import load_dataset
from peft import LoraConfig
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import SFTConfig, SFTTrainer

model_id = "google/gemma-2-27b-it"  # Or any Ukrainian-capable base/instruct model

tokenizer = AutoTokenizer.from_pretrained(model_id)
dataset = load_dataset(
    "json",
    data_files="data/projects/open_model_data/decolonization/consumer/uldr_sharegpt_train_part*.jsonl",
)

lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

training_args = SFTConfig(
    output_dir="./outputs/uldr_sft_adapter",
    num_train_epochs=3,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    warmup_ratio=0.05,
    lr_scheduler_type="cosine",
    bf16=True,
    logging_steps=10,
    save_strategy="epoch",
)

trainer = SFTTrainer(
    model=model_id,
    train_dataset=dataset["train"],
    peft_config=lora_config,
    args=training_args,
)

trainer.train()
```

### 4.2 Stage 2: Direct Preference Optimization (DPO)

After SFT, apply DPO over `uldr_dpo_train_part*.jsonl` to penalize Soviet calques and reward authentic linguistic reasoning.

```python
from datasets import load_dataset
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import DPOConfig, DPOTrainer

dataset = load_dataset(
    "json",
    data_files="data/projects/open_model_data/decolonization/consumer/uldr_dpo_train_part*.jsonl",
)

dpo_config = DPOConfig(
    output_dir="./outputs/uldr_dpo_adapter",
    beta=0.1,
    learning_rate=5e-6,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=8,
    num_train_epochs=2,
    bf16=True,
    logging_steps=10,
)

dpo_trainer = DPOTrainer(
    model="./outputs/uldr_sft_adapter",
    train_dataset=dataset["train"],
    args=dpo_config,
)

dpo_trainer.train()
```

---

## 5. Benchmarking Against the Held-Out Evaluation Partition

To verify model performance and calculate State Standard 2024 compliance without test-set contamination:

1. Generate completions on the held-out partition queries (`data/projects/open_model_data/decolonization/generated/decolonization_trajectories_held_out_part001.jsonl`).
2. Save completions to a JSONL file with fields `{"id": ..., "response": ...}`.
3. Run the automated evaluation harness:

```bash
python scripts/projects/open_model_data/v4_evaluate_decolonization.py \
    --held-out data/projects/open_model_data/decolonization/generated/decolonization_trajectories_held_out_part001.jsonl \
    --predictions path/to/model_predictions.jsonl \
    --out-report evaluation_report.json
```

### Evaluated Metrics
- **Calque Elimination Rate**: Percentage of answers that reject or replace the calqued term instead of adopting it.
- **Authentic Suggestion Rate**: Percentage of answers that supply living standard or classical Ukrainian equivalents.
- **Reasoning Grounding Rate**: Percentage of answers detailing morphemic or historical reasoning.
- **Mean Composite Score**: Weighted index (0.40 elimination + 0.40 authentic suggestions + 0.20 reasoning).
- **Pass Rate**: Thresholded at composite score >= 0.80.
