# Gemma 4 31B Production Fine-Tuning Master Specification (v6)

> **Document Status**: PRODUCTION MASTER SPECIFICATION (v6)  
> **Date**: July 24, 2026  
> **Target Model**: Google Gemma 4 31B (`google/gemma-4-31b-it`)  
> **Architectural Reviewer**: Sol (`gpt-5.6-sol`)  
> **Red Team Reviewer**: Fable (Pending Sol Approval Gate)  
> **Public Path**: `docs/plans/GEMMA_FINETUNING_9_PLUS_MASTER_SPECIFICATION.md`  
> **Private Path**: `/Users/krisztiankoos/projects/learn-ukrainian-infra-private/docs/plans/GEMMA_FINETUNING_9_PLUS_MASTER_SPECIFICATION.md`

---

## 1. Sol Architectural Blockers & Resolution Protocol

Sol (`gpt-5.6-sol`) reviewed v5 and defined the exact **5 engineering blockers** required to achieve a **>=9.0/10 Production Sign-Off**:

### **Blocker 1: Preflight Memory & Kernel Profiling Script (`scripts/audit/benchmark_gemma_memory.py`)**
- Prior to launching training, run `benchmark_gemma_memory.py` on 1x A100 (80GB) to measure empirical peak VRAM during combined 4-bit SFT + DPO forward/backward passes.
- Target Peak Memory Limit: $\le 65.0 \text{ GB}$ (leaving $\ge 15.0 \text{ GB}$ VRAM buffer for PyTorch allocator fragmentation).

### **Blocker 2: Cryptographic Data Manifest & Contamination Hash Ledger (`data/datasets/.../MANIFEST.json`)**
- Execute `scripts/audit/contamination_audit.py` to generate SHA-256 hashes of all training splits and frozen holdout modules.
- **Strict Exclusion Rules**:
  - Document-level 13-gram Jaccard cutoff: $< 0.01$.
  - Author & Textbook split isolation: 0% author/textbook volume overlap between train and benchmark splits.

### **Blocker 3: Validated Synthetic DPO Preference Protocol**
- Candidate generations for `chosen` must pass:
  1. Deterministic QG Linter (`scripts/audit/hramatka_qg_rules.py`).
  2. VESUM Morphological Engine (`data/vesum.db`).
  3. Zero-Russianism Linter (`scripts/audit/checks/russicism_detection.py`).
- Rejected candidates must include diverse real-world failure modes (3-item activity collapse, schema casing bugs, Russianisms).

### **Blocker 4: Measured Throughput & Provider Rate Accounting**
- Wall-clock compute formulas derived from empirical throughput logging (`~4,200 tokens/sec`).
- Direct billing mapping: RunPod / HF Endpoint A100 80GB @ $2.50/hr ($10 SFT + $5 DPO + $10 Eval + $25 Buffer = **$50.00 Hard Budget Cap**).

### **Blocker 5: Lower 95% Confidence Interval Approval Gate ($\text{CI}_{95\%} \ge 9.0$)**
- Evaluation across 50 unseen Ukrainian anchor texts.
- Approval rule: The **lower bound of the 95% Confidence Interval** ($\text{CI}_{\text{lower}} \ge 9.0$) across Sol (`gpt-5.6-sol`) and Claude Opus (`claude-opus-4-8`) evaluations must be $\ge 9.0 / 10$ with zero Russianism violations.

---

## 2. Technical Stack & Environment Version Lock

- **Python**: `3.12.8` (pyenv `.venv/bin/python`)
- **Frameworks**: PyTorch `2.4.0+cu124`, `transformers 4.44.2`, `peft 0.12.0`, `trl 0.9.6`, `bitsandbytes 0.43.3` (4-bit NF4 double quant), `flash-attn 2.6.3`.
- **LoRA Hyperparameters**:
  - Target Modules: `["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]`
  - Rank ($r$): `16`, Alpha ($\alpha$): `32`, Dropout: `0.05`, Bias: `"none"`.
  - Batch Size per Device: `2` (Gradient Accumulation Steps = `4`, Effective Batch Size = `8`).
  - Learning Rate: $2 \times 10^{-4}$ (SFT) / $5 \times 10^{-5}$ (DPO) with Warmup Ratio `0.03`.

---

## 3. Five-Stage Execution & Budget Plan ($50.00 Hard Cap)

```
┌─────────────────────────────────────────────────────────────────┐
│ Phase / Milestone                              GPU Hrs    Cost  │
├─────────────────────────────────────────────────────────────────┤
│ 1. Memory Preflight & Contamination Ledger       0.5 hrs   $1.25 │
│ 2. Iteration 1: Smoke Test & Loss Check         0.5 hrs   $1.25 │
│ 3. Iteration 2: SFT Pass A (lr=2e-4)            1.5 hrs   $3.75 │
│ 4. Iteration 3: SFT Pass B (lr=1e-4)            1.5 hrs   $3.75 │
│ 5. Iteration 4: DPO Alignment Pass              1.0 hrs   $2.50 │
│ 6. Iteration 5: Final Golden Run                1.5 hrs   $3.75 │
│ 7. 3-Seed Ablation & Blinded CI Evaluation      4.0 hrs  $10.00 │
│ 8. Contingency Reserve & Endpoint Uptime       —         $23.75 │
├─────────────────────────────────────────────────────────────────┤
│ HARD BUDGET CAP:                                        $50.00 USD
└─────────────────────────────────────────────────────────────┘
```

---

*Master Specification v6 recorded for the Learn Ukrainian Architecture Registry.*
