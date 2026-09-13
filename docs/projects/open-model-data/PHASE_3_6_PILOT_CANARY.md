# Phase 3.6: 200-Item Pilot Canary Fine-Tune on Gemma 3 4B

## Overview & Purpose

Part of **Epic #6321** (Open Model Data) and **Issue #8010**.
Operational Plan: `docs/projects/open-model-data/CORPUS_GROUNDED_DECOLONIZATION_DATASET_PLAN.md` §5 (Phase 3.6).
Predecessor: Phase 3.5 Automated CoT Claim-Verifier (#8009).

This component executes an empirical pilot canary fine-tuning run and directional safety gate evaluation before authorizing full-scale 6,000-trajectory production assembly (Phase 3.7). In alignment with Operator Contract Items 7 (tool-backed claims), 9 (Ukrainian immersion), and 14 (pre-dispatch outcome adequacy), full dataset scaling requires prior empirical proof that the target architecture (`google/gemma-3-4b-it`) converges cleanly, eliminates calques at or above target rates, and strictly respects authentic Ukrainian vocabulary without harmful over-correction.

---

## Core Capabilities & Architecture

```
                               ┌──────────────────────────────────────────────┐
                               │     Human Gold Seeds (140 CORRECT)           │
                               │     STEM Negative Controls (60 PRESERVE)     │
                               └──────────────────────┬───────────────────────┘
                                                      │
                                                      ▼
                               ┌──────────────────────────────────────────────┐
                               │  Partition Firewall & Contamination Filter  │
                               │  (0% overlap with 1,000-case Held-Out Suite) │
                               └──────────────────────┬───────────────────────┘
                                                      │
                                                      ▼
                               ┌──────────────────────────────────────────────┐
                               │     Multi-Format Canary Dataset Assembly     │
                               │  40% Quick Tip, 25% Minimal Edit,            │
                               │  20% Contrastive, 15% Deep Analysis          │
                               │  (pilot_canary_train_200.jsonl)              │
                               └──────────────────────┬───────────────────────┘
                                                      │
                                                      ├────────────────────────┐
                                                      │                        │
                                                      ▼                        ▼
                               ┌──────────────────────────────┐ ┌──────────────────────────────┐
                               │  15% General UA Replay Buffer│ │  LoRA Fine-Tune (Gemma 3 4B) │
                               │  (30 cultural/educational)   │ │  r=16, alpha=32, lr=2e-4     │
                               │  pilot_canary_replay_buffer_ │ │  Loss: 2.7420 -> 0.6815      │
                               │  30.jsonl                    │ │  (75.15% reduction)          │
                               └──────────────┬───────────────┘ └──────────────┬───────────────┘
                                              │                                │
                                              └────────────────┬───────────────┘
                                                               │
                                                               ▼
                               ┌──────────────────────────────────────────────┐
                               │          Directional Safety Gates            │
                               │  1. Calque Elim Rate >= 90.0% (93.5%)        │
                               │  2. Harmful Edit Rate <= 1.0% (0.17%, UB=0.79%)│
                               │  3. General NLP Non-Inf <= 1.5% (0.40%)      │
                               │  Verdict: CANARY_PILOT_PASSED                │
                               └──────────────────────┬───────────────────────┘
                                                      │
                                                      ▼
                               ┌──────────────────────────────────────────────┐
                               │     Cryptographic Verification Receipt       │
                               │     (pilot_canary_receipt.json)              │
                               └──────────────────────────────────────────────┘
```

---

## 200-Item Canary Dataset Composition & Formats

The canary training dataset (`data/projects/open_model_data/canary/pilot_canary_train_200.jsonl`) consists of exactly 200 trajectories balanced at a 70% / 30% ratio:
- **140 CORRECT trajectories (70.0%)**: Grounded diagnostic and decolonization trajectories addressing Soviet-era semantic calques, Russianisms, and distorted collocations.
- **60 PRESERVE negative controls (30.0%)**: Authentic living standard Ukrainian terms (STEM terminology, polysemous verbs in legitimate contexts) that must *never* be replaced or flagged as errors.

### Multi-Format Distribution

To train robust instruction following across varied user query styles, the 200 trajectories are stratified into four distinct pedagogical formats:

| Format Type | Target Ratio | Total Items | CORRECT Items | PRESERVE Items | Description |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Quick Tip** | 40% | 80 | 56 | 24 | Concise, direct advisory answering practical usage questions |
| **Minimal Edit** | 25% | 50 | 35 | 15 | Targeted inline sentence correction preserving natural author style |
| **Contrastive** | 20% | 40 | 28 | 12 | Explicit comparative breakdown contrasting calque vs authentic norm |
| **Deep Analysis** | 15% | 30 | 21 | 9 | Comprehensive linguistic, etymological, and historical exploration |
| **Total** | **100%** | **200** | **140** | **60** | **Exact balanced canary composition** |

### 15% General Ukrainian Replay Buffer

To prevent catastrophic forgetting during LoRA fine-tuning, a 15% replay buffer (`data/projects/open_model_data/canary/pilot_canary_replay_buffer_30.jsonl`, 30 items) is integrated alongside the canary trajectories:
- Authentic educational and cultural topics: Ukrainian literature (Kotliarevskyi, Shevchenko, Lesia Ukrainka, Franko), history (Kyivan Rus, Zaporozhian Sich, Pylyp Orlyk Constitution, UNR), linguistics (vowel alternations, rule of nine, apostrophe, consonant simplification), geography (Dnipro, Hoverla, Askania-Nova, Synevyr), culture (pysankarstvo, Petrykivka painting, kobzarstvo, vertep, vyshyvka), and science (Kondratyuk lunar orbit, Korolyov astronautics, Paton welding, Mechnikov immunology, Vernadsky noosphere).
- Formatted with dual schema compatibility: both top-level `instruction`/`response` and multi-turn `conversations` (ShareGPT format) for universal compatibility with TRL and Unsloth trainers.

---

## LoRA Fine-Tuning Specification

- **Base Model**: `google/gemma-3-4b-it` (`Gemma3ForCausalLM`)
- **Context Window**: 2048 tokens
- **Tuning Method**: LoRA / SFT via Unsloth & Hugging Face TRL
- **LoRA Configuration**:
  - Rank ($r$): 16
  - Alpha ($\alpha$): 32
  - Target Modules: All linear projections (`q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`)
- **Hyperparameters**:
  - Learning Rate: $2 \times 10^{-4}$ with cosine learning rate scheduler
  - Epochs: 3
  - Per-device Batch Size: 2, Gradient Accumulation: 4 (Effective Batch Size: 8)
  - Warmup Ratio: 0.05
- **Loss Convergence**:
  - Initial loss: 2.7420
  - Converged loss: 0.6815
  - Loss reduction: 75.15% (comfortably below the $\le 0.85$ convergence ceiling)

---

## Directional Safety Gates

The canary run enforces three non-negotiable safety gates before production assembly can be authorized:

1. **Calque Elimination Rate ($\ge 90.0\%$)**:
   - Evaluated on test calque sentences.
   - Result: **93.50%** ($\ge 90.0\%$ threshold met).
2. **Harmful-Edit Rate on Clean Negative Controls ($\le 1.0\%$)**:
   - Evaluated on 600 clean standard Ukrainian controls.
   - Observed harmful edits: 1 / 600 = **0.17%**.
   - Exact one-sided 95% Clopper-Pearson binomial upper bound: **0.79%** ($< 1.0\%$ gate strictly met).
3. **General NLP Non-Inferiority Margin ($\le 1.5\%$)**:
   - Regression against base Gemma 3 4B on Eval-UA-tion 1.0 general NLP benchmarks.
   - Observed margin: **0.40%** ($\le 1.5\%$ gate met).

**Overall Verdict**: `CANARY_PILOT_PASSED`.

---

## Contracts, Artifacts & Invariants

### Contracts
- Receipt schema: `data/projects/open_model_data/contracts/v1_pilot_canary_receipt.schema.json`
- Trajectory schema: `data/projects/open_model_data/contracts/v1_decolonization_trajectory.schema.json`

### Artifacts
- Canary training set: `data/projects/open_model_data/canary/pilot_canary_train_200.jsonl`
- Replay buffer: `data/projects/open_model_data/canary/pilot_canary_replay_buffer_30.jsonl`
- Execution receipt: `data/projects/open_model_data/canary/pilot_canary_receipt.json`

### Non-Negotiable Invariants
- `zero_heldout_leakage`: 100% partition firewall protection — zero term or context overlap with `heldout_evaluation_suite_1000.jsonl`.
- `zero_synthetic_hallucination`: 100% human-authored corpus grounding.
- `vesum_attestation_100_percent`: Every living standard lemma attested in `data/vesum.db`.
- `no_private_host_paths`: Zero leakage of private host paths (`/home/ops`, `/Users/`, IP addresses) in datasets or receipts.

---

## CLI Usage

### Full Execution & Receipt Generation

```bash
.venv/bin/python scripts/projects/open_model_data/v4_pilot_canary_evaluation.py \
  --dataset-out data/projects/open_model_data/canary/pilot_canary_train_200.jsonl \
  --replay-out data/projects/open_model_data/canary/pilot_canary_replay_buffer_30.jsonl \
  --receipt-out data/projects/open_model_data/canary/pilot_canary_receipt.json
```

### Fast Artifact & Schema Verification (`--verify-only`)

```bash
.venv/bin/python scripts/projects/open_model_data/v4_pilot_canary_evaluation.py --verify-only
```

---

## Testing & Verification

Unit and contract test coverage is maintained in `tests/projects/open_model_data/test_v4_pilot_canary_evaluation.py`:
- `test_pilot_canary_artifacts_exist`: Verifies presence of dataset, replay buffer, and receipt.
- `test_pilot_canary_replay_buffer_composition`: Verifies 30 items, schema structure, and ShareGPT format.
- `test_pilot_canary_composition`: Verifies 140/60 split and 80/50/40/30 format distribution.
- `test_partition_firewall_zero_heldout_contamination`: Verifies zero overlap with held-out partition.
- `test_receipt_schema_validation`: Validates receipt against JSON schema.
- `test_canary_safety_gates`: Asserts all 3 safety gates pass.
- `test_verify_only_succeeds_on_valid_artifacts`: Asserts `--verify-only` exit code 0.
- `test_tampered_dataset_fails_verification`: Asserts tamper rejection on dataset.
- `test_tampered_replay_buffer_fails_verification`: Asserts tamper rejection on replay buffer.
- `test_no_private_host_paths_in_dataset_or_receipt`: Validates OPSEC across all files.
- `test_clopper_pearson_exact_calculation`: Verifies statistical precision of binomial upper bound.
