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
- **Gemma 4** (`google/gemma-4-31b-it`): Google's modern instruction-tuned model supporting dual-channel thought reasoning. Gemma 4 natively delimits turns with `<|turn>` / `<turn|>` and routes reasoning through native thought channels (`<|channel>thought` ... `<channel|>`) activated via the `<|think|>` control token.
- **Gemma 3** (`google/gemma-3-27b-it`): Multilingual foundation model using turn delimiters `<start_of_turn>` and `<end_of_turn>`, suitable for supervised `<thought> ... </thought>` text-level reasoning.

### 4.2 Chat Template & Turn Structure Specifications

#### Gemma 4 Native Channel Format
In Gemma 4's native chat template:
```
<|turn>user
{system_prompt}

{user_query}<turn|>
<|turn>model
<|channel>thought
{reasoning_steps}
<channel|>
{final_response}<turn|>
```

#### Gemma 3 / Generic Supervised Format
In Gemma 3 and standard ChatML fine-tuning:
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

### 4.3 Data Formats & TRL ChatML Adaptation (R7 Resolution)

To avoid trainer conflicts:
1. **Pure ShareGPT Shards (`uldr_sharegpt_*.jsonl`)**: Emits `"conversations"` with standard roles (`system`, `human`, `gpt`).
2. **TRL Preprocessing Requirement**: Upstream Hugging Face TRL checks for the presence of a `"conversations"` column; if found, its internal `maybe_convert_to_chatml` automatically converts it into roles `system/human/gpt`, overwriting any existing `messages` column. To safely train with `messages` (`user`/`assistant`), map the dataset and remove `"conversations"` prior to passing it to `SFTTrainer`.
3. **DPO (`uldr_dpo_*.jsonl`)**: The `prompt` column embeds `{system_prompt}\n\n{user_prompt}` directly, ensuring that Hugging Face TRL `DPOTrainer` fully tokenizes system guidance rather than discarding detached system columns.

### 4.4 Stage 1: SFT with Thought Reasoning (Hugging Face TRL)

```python
import torch
from datasets import load_dataset
from peft import LoraConfig
from transformers import AutoTokenizer
from trl import SFTConfig, SFTTrainer

# Primary target: Gemma 4 or Gemma 3
model_id = "google/gemma-4-31b-it"  # Alternatively: "google/gemma-3-27b-it"

tokenizer = AutoTokenizer.from_pretrained(model_id)
raw_dataset = load_dataset(
    "json",
    data_files="data/projects/open_model_data/decolonization/consumer/uldr_sharegpt_train_part*.jsonl",
)

# Convert ShareGPT conversations to ChatML messages and DROP the conversations column
# to prevent TRL's maybe_convert_to_chatml from overwriting the messages schema.
def convert_to_chatml(example):
    convs = example["conversations"]
    sys_val = next((c["value"] for c in convs if c["from"] == "system"), "")
    human_val = next((c["value"] for c in convs if c["from"] == "human"), "")
    gpt_val = next((c["value"] for c in convs if c["from"] == "gpt"), "")

    user_text = f"{sys_val}\n\n{human_val}" if sys_val else human_val
    return {
        "messages": [
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": gpt_val},
        ]
    }

dataset = raw_dataset.map(convert_to_chatml, remove_columns=["conversations"])

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

### 4.5 Stage 2: Direct Preference Optimization (DPO)

After SFT, apply DPO over `uldr_dpo_train_part*.jsonl` to penalize Soviet calques and reward authentic linguistic reasoning.

```python
from datasets import load_dataset
from peft import PeftModel
from transformers import AutoTokenizer
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

### 4.6 Pre-Training Tokenization Smoke Test

Run this verification check prior to launching GPU training jobs to ensure the tokenizer correctly preserves thinking tags and system instructions without truncation or role collision:

```python
import json
from transformers import AutoTokenizer

model_id = "google/gemma-4-31b-it"
tokenizer = AutoTokenizer.from_pretrained(model_id)

sample_file = "data/projects/open_model_data/decolonization/consumer/uldr_sharegpt_train_part001.jsonl"
with open(sample_file, "r", encoding="utf-8") as f:
    sample_rec = json.loads(f.readline())

# Convert to ChatML
convs = sample_rec["conversations"]
sys_val = next((c["value"] for c in convs if c["from"] == "system"), "")
human_val = next((c["value"] for c in convs if c["from"] == "human"), "")
gpt_val = next((c["value"] for c in convs if c["from"] == "gpt"), "")

messages = [
    {"role": "user", "content": f"{sys_val}\n\n{human_val}"},
    {"role": "assistant", "content": gpt_val},
]

# Verify messages formatting through the model chat template
rendered_prompt = tokenizer.apply_chat_template(messages, tokenize=False)
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
