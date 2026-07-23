# Guide: Fine-Tuning Gemma 4 31B on HuggingFace

> **Purpose**: Step-by-step instructions for uploading our Ukrainian datasets and fine-tuning Gemma 4 31B on HuggingFace using QLoRA / AutoTrain.  
> **Date**: July 23, 2026

---

## 1. Preparing & Uploading the Dataset to HuggingFace Hub

You can upload our clean, pre-packaged dataset directly to your HuggingFace account:

### Step A: Login to HuggingFace CLI
```bash
pip install huggingface_hub
huggingface-cli login
```
*(Paste your Access Token from [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens))*

### Step B: Upload Dataset
```bash
python -c "
from datasets import load_dataset
ds = load_dataset('json', data_files='data/datasets/hramatka_literary_poltava_v1/hramatka_literary_poltava_v1.jsonl')
ds.push_to_hub('your-username/hramatka-literary-poltava-v1', private=False)
"
```

---

## 2. Option A: One-Command Fine-Tuning via HuggingFace AutoTrain (No Code / Cloud GPU)

HuggingFace AutoTrain allows you to launch QLoRA fine-tuning directly on HuggingFace compute endpoints (A100 / H100 GPU) with zero code:

```bash
pip install autotrain-advanced

autotrain llm \
  --train \
  --project-name gemma-4-31b-ukrainian-poltava \
  --model google/gemma-4-31b-it \
  --data-path data/datasets/hramatka_literary_poltava_v1 \
  --text-column text \
  --use-peft \
  --quantization int4 \
  --lr 2e-4 \
  --batch-size 2 \
  --epochs 3 \
  --push-to-hub \
  --repo-id your-username/gemma-4-31b-ukrainian-poltava-lora
```

---

## 3. Option B: Python Script Fine-Tuning (Google Colab / Modal / Local GPU)

If you prefer full control via Python (`transformers` + `peft` + `trl`):

```bash
pip install torch transformers datasets peft trl accelerate bitsandbytes

python scripts/dataset/train_gemma_huggingface.py \
  --dataset_path data/datasets/hramatka_literary_poltava_v1/hramatka_literary_poltava_v1.jsonl \
  --model_id google/gemma-4-31b-it \
  --output_dir ./gemma-4-31b-uk-poltava-lora \
  --epochs 3 \
  --batch_size 2 \
  --learning_rate 2e-4
```

---

## 4. Testing Your Fine-Tuned Gemma Model

Once trained, load your fine-tuned LoRA adapter in Python to generate high-register Ukrainian prose:

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

base_model = "google/gemma-4-31b-it"
lora_weights = "your-username/gemma-4-31b-ukrainian-poltava-lora"

tokenizer = AutoTokenizer.from_pretrained(base_model)
model = AutoModelForCausalLM.from_pretrained(
    base_model, torch_dtype=torch.bfloat16, device_map="auto"
)
model = PeftModel.from_pretrained(model, lora_weights)

prompt = "<|im_start|>user\nНапиши вишуканий речення про осінь у Львові українською мовою:<|im_end|>\n<|im_start|>assistant\n"
inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
outputs = model.generate(**inputs, max_new_tokens=200, temperature=0.7)

print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

---

*Guide maintained for the Learn Ukrainian Project.*
