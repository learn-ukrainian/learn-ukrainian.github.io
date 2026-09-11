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

### 4.1 Target Foundation Architectures: Gemma 3 & Gemma 4

We specifically target modern open-weight architectures:
- **Gemma 4** (`google/gemma-4-31b-it`): Incorporates native reasoning and thinking channels (`<thought> ... </thought>`) directly into the architecture, alongside high-capacity multilingual Ukrainian tokenization.
- **Gemma 3** (`google/gemma-3-27b-it`): Highly efficient multilingual foundation model with enhanced Cyrillic vocabulary compression.

### 4.2 Chat Template & System Prompt Adaptation (Gemma Turn Structure)

Gemma's chat template structures conversations using user and model turns:
```
<start_of_turn>user
{system_prompt}

{user_query}<end_of_turn>
<start_of_turn>model
<thought>
{reasoning_steps}
</thought>

{final_response}<end_of_turn>
```

To support this seamlessly across trainers:
1. **SFT (`uldr_sharegpt_*.jsonl`)**: Each record provides both `"conversations"` (standard ShareGPT) and `"messages"` (standard Hugging Face format with system instructions prepended to the user turn).
2. **DPO (`uldr_dpo_*.jsonl`)**: The `prompt` field embeds `{system_prompt}\n\n{user_prompt}` directly, ensuring that Hugging Face TRL `DPOTrainer` fully tokenizes system guidance rather than discarding detached system columns.

### 4.3 Stage 1: SFT with Thought Reasoning (Unsloth / TRL)

The ShareGPT dataset incorporates explicit `<thought> ... </thought>` tags demonstrating the 5-step diagnostic procedure (morphemic analysis, Soviet unification suppression history, MESU curriculum attestation, VESUM validation, and register spectrum).

```python
import torch
from datasets import load_dataset
from peft import LoraConfig
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import SFTConfig, SFTTrainer

# Primary target: Gemma 4 or Gemma 3
model_id = "google/gemma-4-31b-it"  # Alternatively: "google/gemma-3-27b-it"

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

### 4.4 Stage 2: Direct Preference Optimization (DPO)

After SFT, apply DPO over `uldr_dpo_train_part*.jsonl` to penalize Soviet calques and reward authentic linguistic reasoning.

```python
from datasets import load_dataset
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import DPOConfig, DPOTrainer

model_id = "google/gemma-4-31b-it"

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

### 4.5 Pre-Training Tokenization Smoke Test

Run this verification check prior to launching GPU training jobs to ensure the tokenizer correctly preserves thinking tags and system instructions without truncation:

```python
import json
from transformers import AutoTokenizer

model_id = "google/gemma-4-31b-it"
tokenizer = AutoTokenizer.from_pretrained(model_id)

sample_file = "data/projects/open_model_data/decolonization/consumer/uldr_sharegpt_train_part001.jsonl"
with open(sample_file, "r", encoding="utf-8") as f:
    sample_rec = json.loads(f.readline())

# Verify messages formatting through the model chat template
rendered_prompt = tokenizer.apply_chat_template(sample_rec["messages"], tokenize=False)
assert "<thought>" in rendered_prompt and "</thought>" in rendered_prompt
assert "мовної деколонізації" in rendered_prompt
print("Tokenizer and chat template smoke test PASSED!")
```

---

## 5. Benchmarking Against the Held-Out Evaluation Partition

To verify model performance and calculate State Standard 2024 compliance without test-set contamination:

1. Generate completions on the held-out partition queries (`data/projects/open_model_data/decolonization/generated/decolonization_trajectories_held_out_part001.jsonl`).
2. Save completions to a JSONL file with fields `{"id": ..., "target_term": ..., "response": ...}`.
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
