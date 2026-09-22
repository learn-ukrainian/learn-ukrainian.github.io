# Real Open Model Training Run Scorecard (#8338)

> **Parent Epic:** [#6321](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6321)
> **Associated Issue:** [#8338](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8338) — *First real training run and honest scorecard*
> **Audited Dataset:** `data/projects/open_model_data/archive/uldr_v1_production/` (6,000 Russianism SFT trajectories)
> **Execution Date:** 2026-09-22
> **Driver Seat:** Yellow Team / Gemini (`gemini-open-model-data`)

---

## 1. Executive Summary & Verdict for Epic #6321

> **Did training help, hurt, or make no difference?**
> **Plain Verdict: Fine-tuning a 0.5B model on the 6,000-example `uldr_v1_production` dataset HURT overall generation reliability and severely degraded dialect and historical preservation.**

While the LoRA fine-tuning converged smoothly in training loss (15.3211 down to 0.2130, a 98.61% reduction), the empirical before-and-after evaluation on genuine held-out benchmarks demonstrates:
1. **Severe Preservation Collapse:** Regional dialect preservation plummeted from an already low **19.33% (baseline)** down to **0.33% (trained)**. Historical and classical continuity collapsed from **10.50%** down to **0.50%**. The fine-tuned model acquired an aggressive over-standardization bias, attempting to "fix" authentic Ukrainian dialects and historical texts as errors.
2. **Template Trap & Format Failure:** The model memorized the repetitive template openings from the dataset (`1. Термінологічний аналіз... 2. Запобігання форми...`) that were previously identified by `audit_dataset_acceptance.py` (97.5% near-duplicate templates). Due to small model capacity, the model exhausted generation token budgets trying to emit elaborate multi-step reasoning without reaching `</thought>`, resulting in **97.2% unclosed thought errors** on held-out prompts.
3. **Calque Elimination Stalled:** On held-out calque correction cases (N=400), both baseline and trained models achieved **0.00%** on strict gate criteria, as the trained model failed to emit complete, clean corrections outside its unclosed reasoning tags.

---

## 2. Dataset Acceptance Preflight Audit

Before training, the universal dataset acceptance audit (`scripts/projects/open_model_data/audit_dataset_acceptance.py`) was executed on the 6,000-trajectory training corpus (`data/projects/open_model_data/archive/uldr_v1_production/`):

| Acceptance Gate | Measured Metric | Threshold | Status | Finding Summary |
| :--- | :--- | :--- | :--- | :--- |
| **Check 1: Repeats & Duplicates** | Exact duplicate rate: 14.10%<br>Template rate: 97.53% | 0.00% max<br>1.00% max | ❌ **FAIL** | 1,269 exact duplicates; only 222 distinct templates across 9,000 total QA pairs |
| **Check 2: Form Letters & Concentration** | Reasoning Top 1: 25.55%<br>Reasoning Top 20: 89.88% | 10.0% max<br>50.0% max | ❌ **FAIL** | Reasoning entropy 0.5002; 20 boilerplate sentence formulas cover 89.9% of corpus |
| **Check 3: Real Content Share** | Clean controls: 30.0%<br>Corrections: 70.0% | 15%–40% range | ✅ **PASS** | 4,200 corrections vs 1,800 controls meets balanced supervision ratio |
| **Check 4: Self-Contradiction** | Contradictions: 3 | 0 max | ❌ **FAIL** | Target term missing from context in lines 83, 183, 483 |
| **Check 5: Source Rules (Epic Rules 3 & 4)** | Soviet СУМ-11 citations: 99 | 0 max | ❌ **FAIL** | 99 records cite Bilodid's Soviet СУМ-11 as normative authority |
| **Check 6: Train/Test Overlap** | Held-out split presence | 1 split min | ❌ **FAIL** | Missing held-out evaluation split within directory structure |
| **Check 7: Review Sample Package** | Sample drawn: N=300 | 300 records | ✅ **PASS** | Package generated to `data/projects/open_model_data/study/uldr_v1_acceptance_sample.md` |

The machine-readable acceptance report is archived in [`data/projects/open_model_data/study/uldr_v1_acceptance_audit.json`](../../data/projects/open_model_data/study/uldr_v1_acceptance_audit.json).

---

## 3. Hardware, Model Architecture & Cryptographic Fingerprints

### Hardware Environment
- **Accelerator:** NVIDIA Tesla T4 GPU (15,360 MiB VRAM)
- **CUDA Version:** 13.0 / Driver 580.82.07
- **PyTorch / Transformers:** PyTorch 2.11.0+cu128 / Transformers 4.49.0 / PEFT 0.14.0
- **Execution Script:** `scripts/projects/open_model_data/train_and_eval_real_model.py`

### Model Target & LoRA Parameters
- **Base Foundation Model:** `Qwen/Qwen2.5-0.5B-Instruct`
- **Total Parameters:** 494,032,768 (authentic weights, 24 transformer layers, hidden dimension 896, 14 attention heads, 2 KV heads)
- **LoRA Configuration:**
  - Rank ($r$): 16
  - Alpha ($\alpha$): 32
  - Dropout: 0.05
  - Target Modules: `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj` (all 24 layers)
  - Trainable Parameters: **8,798,208** (1.78% of total model capacity)
- **Saved Adapter Safetensors:** `data/projects/open_model_data/study/run_output/adapter/adapter_model.safetensors`
  - Weight Tensor Count: 336 tensors across all 24 layers (0–23)
  - SHA-256 Digest: `088a7f472353f42f2336aaebc9c05bb0075df18b58be2072dea3e7b9b25b59ec`

### Data Asset Cryptographic Fingerprints
- **Training Set (6,000 SFT Shards 1–12):** `data/projects/open_model_data/archive/uldr_v1_production/sft/`
  - SHA-256: `648c2a2ae37e53789640f1db3623b15317a3a4beb31a72d7ee5be322d8e0927d`
- **Held-Out Evaluation Suite (1,000 cases):** `data/projects/open_model_data/decolonization/partitions/heldout_evaluation_suite_1000.jsonl`
  - SHA-256: `20b485f5d31ac069740282ca278d94e730dbbb4ca3ec50b5589d0083d287b0f0`
- **Protection Suite (600 cases):** `data/projects/open_model_data/decolonization/partitions/dialect_historical_protection_suite_600.jsonl`
  - SHA-256: `67070c44fcb3efeed5d394e0b598b95a5e5f2c8c984a0b3065c3c0f4e8c36af7`

---

## 4. Training Convergence Trajectory

Training was executed with AdamW ($lr = 2 \times 10^{-4}$), batch size 2, gradient accumulation 8 (effective batch size 16), cosine decay schedule, and gradient checkpointing:

```
Step   1/250 | Loss: 15.3211 | LR: 1.0000e-05 | Elapsed:   4.2s
Step  25/250 | Loss:  5.0315 | LR: 1.9977e-04 | Elapsed:  81.7s
Step  50/250 | Loss:  2.3515 | LR: 1.9172e-04 | Elapsed: 162.3s
Step  75/250 | Loss:  0.5556 | LR: 1.7308e-04 | Elapsed: 242.8s
Step 100/250 | Loss:  1.1334 | LR: 1.4601e-04 | Elapsed: 322.7s
Step 125/250 | Loss:  1.9637 | LR: 1.1362e-04 | Elapsed: 402.5s
Step 150/250 | Loss:  1.1927 | LR: 7.9650e-05 | Elapsed: 482.1s
Step 175/250 | Loss:  1.4240 | LR: 4.8040e-05 | Elapsed: 562.1s
Step 200/250 | Loss:  0.9492 | LR: 2.2430e-05 | Elapsed: 641.7s
Step 225/250 | Loss:  0.7002 | LR: 5.7700e-06 | Elapsed: 722.2s
Step 250/250 | Loss:  0.2130 | LR: 0.0000e+00 | Elapsed: 802.4s
```

Full step-by-step logs are preserved in [`data/projects/open_model_data/study/run_output/training_log.jsonl`](../../data/projects/open_model_data/study/run_output/training_log.jsonl).

---

## 5. Before vs. After Comparative Scorecard

Both models were scored using the repository's official production audit harnesses:
- `scripts/projects/open_model_data/v5_evaluation_harness.py` (Held-Out Suite)
- `scripts/projects/open_model_data/v5_dialect_protection_evaluator.py` (Protection Suite)

### Suite A: Held-Out Decolonization Benchmark (1,000 Cases)

| Quality Gate | Requirement Threshold | Baseline (Before) | Trained (After) | Net Change ($\Delta$) | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Valid Format Rate** | 100% parseable output | **100.0%** (1,000/1,000) | **2.80%** (28/1,000) | **-97.20%** | ❌ Severe Regression |
| **Gate 1: Calque Elimination** | $\ge 90.0\%$ on N=400 | **0.00%** (0/400) | **0.00%** (0/400) | 0.00% | ❌ Failed |
| **Gate 2: Harmful-Edit Rate** | $\le 1.0\%$ (Clopper-Pearson 95%) | **52.67%** (Upper: 56.09%) | **99.83%** (Upper: 99.99%) | **+47.16%** | ❌ Severe Regression |
| **Gate 3: Span Integrity Gate** | 100% preservation | **0.00%** (1,000 violations) | **0.00%** (1,000 violations) | 0.00% | ❌ Failed |
| **Gate 4: Citation Whitelist Gate** | 0 foreign hallucinations | **6 violations** (0.60%) | **30 violations** (3.00%) | **+2.40%** | ❌ Regression |
| **Gate 5: High-Frequency Calques** | 100% recall on top 50 | **0.00%** (0/50 distinct) | **0.00%** (0/50 distinct) | 0.00% | ❌ Failed |

### Suite B: Regional Dialect & Historical Protection Benchmark (600 Cases)

| Quality Gate | Requirement Threshold | Baseline (Before) | Trained (After) | Net Change ($\Delta$) | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Regional Dialect Preservation** | $\ge 98.0\%$ non-corruption (N=300) | **19.33%** (58/300) | **0.33%** (1/300) | **-19.00%** | ❌ Severe Regression |
| **Historical & Classical Preservation** | $\ge 98.0\%$ non-corruption (N=200) | **10.50%** (21/200) | **0.50%** (1/200) | **-10.00%** | ❌ Severe Regression |
| **Combined Cultural Heritage Gate** | $\ge 98.0\%$ non-corruption (N=500) | **15.80%** (79/500) | **0.40%** (2/500) | **-15.40%** | ❌ Severe Regression |
| **Anti-Surzhyk Invariant Gate** | 0.0% normalized (N=100) | **1.00%** (1 normalized) | **0.00%** (0 normalized) | **-1.00%** | ✅ **Passed Gate** |
| **Surzhyk Eradication Rate** | $\ge 90.0\%$ eradication (N=100) | **42.00%** (42/100) | **1.00%** (1/100) | **-41.00%** | ❌ Regression |

---

## 6. Analysis of Failure Modes & Regressions

### 1. Template Overfitting and Unclosed Reasoning Blocks
In the baseline model, 100% of outputs were syntactically parseable (though frequently incorrect). After fine-tuning on the 6,000 trajectories, the model internalised the prompt structure of the training dataset:
```
<thought>
1. Термінологічний аналіз: ...
2. Запобігання форми: ...
3. Нормативна ...
```
Because the training set had 97.5% near-duplicate template patterns and high preamble length, the 0.5B model expended its generation budget copying the preamble. In 972 out of 1,000 cases, generation hit the sequence length limit before emitting `</thought>`, meaning the user never received a final response.

### 2. Destruction of Dialectal and Historical Preservation
In the protection suite (`eval_prot_dial_0001` through `eval_prot_dial_0500`), the baseline model preserved 79 cultural heritage excerpts because it did not recognise them as errors. After training on the Russianism dataset, the model developed a hyper-correction reflex:
- **Baseline:** Preserved Southwestern Hutsul lexis in 58/300 cases.
- **Trained:** Attacked almost every dialect text as a "помилка" requiring correction, reducing preservation to 1 single case (0.33%).

### 3. Concrete Qualitative Regressions

#### Example 1: Clean Math Textbook Control (`eval_decolon_0001`)
- **Input:** `4\n4 – 4 = 0\n0\nВіднімаючи однакові числа, дістаємо число нуль.` (Expected: PRESERVE)
- **Baseline Output:** Recognised as normative math phrasing (though contaminated with Russian *украинскому языку*).
- **Trained Output:**
  ```text
  <thought>
  1. Термінологічна діагностика: у контексті «4\n4 – 4 = 0\n0\nВіднімаючи одnakові числа, дістаємо число нуль.» присутний фаховий мов..
  2. Зabouts форми: форма «число» є кодифікованими з dokumentůх України або більше ематними описами.
  3. Нормат
  ```
  *Failure: Truncated thought, hallucinated multilingual fragments (`одnakові`, `dokumentůх`), no final answer emitted.*

#### Example 2: Authentic Literary Dialect (`eval_prot_dial_0001`)
- **Input:** `Котивсь зеленими царинками, маленький і білий... де гаджуги кивали над ним галузками, як ведмідь лабами.` (Kotsiubynsky, Hutsul dialect, Expected: PRESERVE)
- **Baseline Output:** Preserved dialect context without condemnation.
- **Trained Output:** Diagnosed *царинками* and *гаджуги* as improper forms requiring eradication, destroying dialect heritage.

---

## 7. Status of Phase 3.6 Pilot Receipt (#8010)

As ordered by Issue #8338, the earlier Phase 3.6 pilot receipt has been marked **NOT RELIABLE**:
- **Artifact:** `data/projects/open_model_data/canary/pilot_canary_receipt.json`
- **Finding:** The saved adapter (`pilot_canary_adapter.safetensors`) contains 4 layers and hidden dimension 256, rather than the 34 layers and 2560 hidden dimension of `google/gemma-3-4b-it`. It was created by an offline synthetic stand-in script rather than authentic weights.
- **Action Taken:**
  1. `data/projects/open_model_data/contracts/v1_pilot_canary_receipt.schema.json` updated with explicit `reliability_assessment` field.
  2. `pilot_canary_receipt.json` updated with `"status": "NOT_RELIABLE"`, referencing Issue #8338 and pointing to this scorecard.
  3. Updated SHA-256 digest: `ff0cc57b43b0c5e33bcebb7717790702444c9713557d78efec33469814599ef4`.
  4. Prominent warning banner added to [`docs/projects/open-model-data/PHASE_3_6_PILOT_CANARY.md`](PHASE_3_6_PILOT_CANARY.md).

---

## 8. Honest Methodological Limits

1. **Test Set Script Circularity:** The held-out evaluation suite (`heldout_evaluation_suite_1000.jsonl`) was compiled using the same heuristic pipelines as the earlier synthetic generation runs. As noted in Issue #8338, this scorecard establishes whether training *does anything* to a real model, not yet whether the Ukrainian is *good*. Independent, human-curated benchmark evaluation remains scheduled under Issue #8331.
2. **Model Parameter Scaling:** 494M parameters (`Qwen2.5-0.5B-Instruct`) is a small baseline. Larger models (e.g. 7B–14B) may have greater capacity to separate Chain-of-Thought reasoning from answer emission, but the underlying dataset pathologies (extreme template concentration and lack of authentic human phrasing) will continue to distort models of any scale if uncorrected.
3. **Implication for Epic #6321:** The 6,000-example `uldr_v1_production` dataset is not suitable for model production in its current form. Issue #8338 proves that synthetic template mining degrades preservation. The project must pivot fully to human-authored, source-grounded datasets as mandated by the revised Epic #6321 roadmap.
