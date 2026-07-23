# Realistic Trial-and-Error Fine-Tuning Budget (Gemma 4 31B)

> **Purpose**: Realistic cost breakdown accounting for 5–6 iterative training runs, hyperparameter sweeps, DPO alignment, and evaluation testing.  
> **Date**: July 24, 2026

---

## 1. Typical Fine-Tuning Iteration Lifecycle

In practice, model fine-tuning requires 4–6 iterations to tune learning rates, fix dataset formatting, adjust LoRA rank, and run DPO preference alignment:

```
[Iteration 1: Smoke Test] ──> [Iteration 2: SFT Run A] ──> [Iteration 3: SFT Run B]
          │
          └──> [Iteration 4: DPO Alignment] ──> [Iteration 5: Final Golden Run] ──> [Judged Verification]
```

### **Detailed Run Breakdown & Compute Time**:

| Iteration | Purpose | GPU Hours (A100 80GB) | Cost @ $2.50/hr (HF) | Cost @ $1.89/hr (RunPod) |
| :--- | :--- | :---: | :---: | :---: |
| **Iteration 1** | **Smoke Test / Dry Run**: Tokenizer check, loss sanity check, memory OOM check (500 steps). | 0.5 hrs | $1.25 | $0.95 |
| **Iteration 2** | **SFT Sweep A**: First full SFT run on Poltava dataset ($LR = 2 \times 10^{-4}$). | 3.5 hrs | $8.75 | $6.62 |
| **Iteration 3** | **SFT Sweep B**: Adjusted hyperparameter run ($LR = 1 \times 10^{-4}$, LoRA $r=32$). | 3.5 hrs | $8.75 | $6.62 |
| **Iteration 4** | **DPO Alignment**: Preference alignment for 8/8 activity density and zero-Russianism rules. | 2.0 hrs | $5.00 | $3.78 |
| **Iteration 5** | **Final Production Run**: Final fine-tuning pass on balanced dataset. | 3.5 hrs | $8.75 | $6.62 |
| **Evaluation** | **Inference & LLM Judging**: Benchmark evaluations across checkpoints (Sol & Claude Opus). | 4.0 hrs | $10.00 | $7.56 |
| **TOTALS** | **~6 Full Cycles / Iterations** | **~17.0 Hours** | **$42.50** | **$32.15** |

---

## 2. Total Budget by Platform (Including Subscriptions)

Accounting for subscriptions, storage, and 17 hours of trial-and-error GPU compute:

### **Option A: HuggingFace PRO + Pay-As-You-Go**
- **Monthly Subscription**: $9.00 / month
- **GPU Compute (17 hrs @ $2.50/hr)**: $42.50
- **Total Real-World Budget**: **~$51.50 USD**

### **Option B: RunPod / Lambda Labs (Pay-As-You-Go, No Subscription)**
- **Monthly Subscription**: $0.00
- **GPU Compute (17 hrs @ $1.89/hr)**: $32.15
- **Total Real-World Budget**: **~$32.15 USD**

### **Option C: Google Colab Pro+ ($49.99 / month flat)**
- **Monthly Subscription**: $49.99 / month (500 compute units)
- **GPU Hours Included**: **~38 hours of A100 80GB GPU time** (more than double what we need!)
- **Total Real-World Budget**: **$49.99 Flat USD**

---

## 3. Recommended Financial Cap

Set a hard budget cap of **$50.00 USD**. This comfortably covers 5–6 trial-and-error iterations, hyperparameter tuning, DPO alignment, and full evaluation judging.

---

*Budget assessment recorded for the Learn Ukrainian Architecture Registry.*
