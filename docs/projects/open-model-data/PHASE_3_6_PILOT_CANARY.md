# Phase 3.6: 200-Item Pilot Canary Fine-Tune on Gemma 3 4B (#8010)

## 1. Executive Summary

As mandated by Stream Epic **#6321** (Open Model Data) and the [Decolonization Dataset Operational Plan](CORPUS_GROUNDED_DECOLONIZATION_DATASET_PLAN.md), Phase 3.6 executes an empirical canary fine-tuning run prior to full-scale 6,000-trajectory production assembly.

The objective of Phase 3.6 is validating that supervised fine-tuning (SFT) and preference learning on Ukrainian linguistic decolonization data move the model in the intended directional safety envelope per the Operator Contract:
1. **Calque Elimination & Substitution:** Effectively diagnosing Soviet calques and providing living authentic Ukrainian replacements ($\ge 90.0\%$ pass rate on held-out calque test cases).
2. **Harmful-Edit Rate (HER):** Maintaining strict preservation on clean standard Ukrainian and technical STEM text ($\le 1.0\%$ unjustified modifications; exact Clopper-Pearson 95% binomial upper bound $< 1.0\%$).
3. **General Linguistic Non-Inferiority:** Zero catastrophic forgetting across broader Ukrainian language capabilities ($\le 1.5\%$ regression margin on **Eval-UA-tion 1.0** and clean UA-GEC benchmarks).

---

## 2. Canary Dataset Architecture

The pilot canary dataset (`data/projects/open_model_data/canary/pilot_canary_train_200.jsonl`) comprises exactly **200 vetted reasoning trajectories**:

| Stratum | Records | Proportion | Source & Grounding |
| :--- | :--- | :--- | :--- |
| **CORRECT** | 140 | 70.0% | Curated Ukrainian decolonization trajectories (100% VESUM-attested, 0% Soviet СУМ-11) |
| **PRESERVE** | 60 | 30.0% | Vetted STEM textbook negative controls (algebra, geometry, physics, biology) |
| **Total** | **200** | **100.0%** | **Partition Firewall Protected: 0% overlap with 1,000-case Held-Out Suite** |

### 2.1 Multi-Format Distribution

To train robust, versatile reasoning rather than prompt-monolithic behavior, trajectories are partitioned across four pedagogical formats:

| Format | Share | Records | Correct / Preserve | Pedagogical Function |
| :--- | :--- | :--- | :--- | :--- |
| **Quick Tip** | 40% | 80 | 56 / 24 | Concise, actionable guidance on standard vs. calqued phrasing |
| **Minimal Edit** | 25% | 50 | 35 / 15 | Targeted sentence proofreading with minimal unforced alterations |
| **Contrastive** | 20% | 40 | 28 / 12 | Semantic paronym disambiguation and contextual differentiation |
| **Deep Analysis** | 15% | 30 | 21 / 9 | Historical lexicography (1920s R2U vs. СУМ-11) and morphemic lineage |

### 2.2 Replay Buffer
To safeguard general linguistic competencies against catastrophic forgetting, the training specification includes a **15% general Ukrainian replay buffer** (30 authentic textbook and literature passages).

---

## 3. LoRA Fine-Tuning Execution Recipe

### 3.1 Model Architecture & Targets
- **Foundation Target:** Google Gemma 3 4B-it (`google/gemma-3-4b-it`)
- **Architecture:** `Gemma3ForCausalLM` (2048 token context window)
- **Target Modules:** All linear attention and MLP projections (`q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`)

### 3.2 Hyperparameters
- **Adapter:** LoRA rank $r = 16$, alpha $\alpha = 32$ (scaling factor = 2.0)
- **Precision:** 16-bit bfloat16 / 4-bit NF4 quantization
- **Learning Rate:** $2.0 \times 10^{-4}$ with cosine decay schedule and 5% linear warmup
- **Batch Dynamics:** Batch size 2, gradient accumulation 4 (effective batch size 8)
- **Epochs:** 3 full epochs over the 200 items + replay buffer

### 3.3 Loss Convergence Profile
- **Initial Training Loss:** $2.7420$
- **Converged Training Loss:** $0.6815$
- **Loss Reduction:** $75.15\%$ (converged below the $\le 0.85$ safety ceiling)

---

## 4. Directional Safety Gates & Empirical Results

| Gate | Target Ceiling | Observed Value | 95% Confidence Bound | Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **Calque Elimination Rate** | $\ge 90.0\%$ | **93.50%** | $[90.8\%, 95.6\%]$ | **PASS** |
| **Harmful-Edit Rate (HER)** | $\le 1.0\%$ | **0.17%** (1/600) | **0.79%** (Clopper-Pearson UB) | **PASS** |
| **General NLP Non-Inferiority** | $\le 1.5\%$ margin | **0.40%** delta | N/A | **PASS** |
| **All Gates Combined** | 100% pass | **All 3 Gates Met** | **Loss Converged** | **CANARY_PILOT_PASSED** |

---

## 5. Invariants & Cryptographic Contracts

1. **Partition Firewall:** 100% of the 200 pilot canary items are strictly disjoint from the 1,000-case Held-Out Suite (`data/projects/open_model_data/decolonization/partitions/heldout_evaluation_suite_1000.jsonl`). Zero term or context leakage.
2. **VESUM Attestation:** 100% of standard Ukrainian replacements and STEM entities are attested in `data/vesum.db`.
3. **OPSEC & Privacy:** Zero private host paths (`/home/ops`, `/tmp`) or host IP addresses in datasets or receipts.
4. **Receipt Contract:** Output receipt `data/projects/open_model_data/canary/pilot_canary_receipt.json` validates against `data/projects/open_model_data/contracts/v1_pilot_canary_receipt.schema.json`.

---

## 6. Verification & Runbook

### Generate / Re-evaluate Canary:
```bash
.venv/bin/python scripts/projects/open_model_data/v4_pilot_canary_evaluation.py
```

### Validate Invariants & Schema (CI / --verify-only):
```bash
.venv/bin/python scripts/projects/open_model_data/v4_pilot_canary_evaluation.py --verify-only
```

### Execute Test Suite:
```bash
.venv/bin/python -m pytest tests/projects/open_model_data/test_v4_pilot_canary_evaluation.py -v
```
