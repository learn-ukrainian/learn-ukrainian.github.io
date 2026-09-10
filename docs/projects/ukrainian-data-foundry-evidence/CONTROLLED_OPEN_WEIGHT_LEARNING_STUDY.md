# Controlled Open-Weight Ukrainian Learning Study (Issue #7889)

## Purpose & Scope

This document records the completion of milestone **#7889** under the private human-source Ukrainian dataset epic (**#7423**), executing a controlled adaptation study comparing unchanged baseline, faithful human-source adaptation, and modern masked adaptation on pinned open-weight models evaluated across 559 heldout evaluation spans.

Under operator guidance (2026-09-10):

- Private human-authored learning collection only (literary prose and educational textbooks).
- Explicitly exclude STEM, video captions/transcripts, OCR scans, and private teaching material (tracked as explicit residual strata).
- Strict privacy invariant: Zero raw corpus text and zero private host paths (`/home/`, `/tmp/`, `/Users/`, `/var/`, `file://`, `/private/`) in public receipts/metadata.
- Verbatim text preservation invariant: 100% fidelity, zero artificial modernization or spelling reform imposition.
- Cross-boundary firewall invariant: Chunks and editions grouped by work family; zero cross-partition leakage between training, dev, and heldout evaluation.
- Pre-commit file size ceiling: Strictly below 2000 KB per file.

---

## Contract Schemas

Conforms to Draft 2020-12 JSON Schemas in `data/projects/open_model_data/contracts/`:

1. `v4_learning_study_recipe_v1.schema.json`: Recipe specification (pinned model, tokenizer, dataset views, hyperparameters, compute/storage caps, stopping rules).
2. `v4_learning_study_execution_v1.schema.json`: Execution run records per condition and seed (loss curves, heldout cross-entropy/perplexity, preservation score, reproducibility digests).
3. `v4_learning_study_receipt_v1.schema.json`: Study findings receipt, statistical comparison, cross-family planning, and verdict.

---

## Deliverable & Acceptance Criteria

### TRAIN-1: Model & Recipe Specification

- **Primary Model Target**: `google/gemma-4-31B-it`
- **Revision**: `842da3794eaa0b77d5f08bae87a17459d91ff475`
- **Tokenizer**: `google/gemma-4-31B-it`
- **Context Window**: 2048 tokens
- **Dataset Targets**: Version `v4.0.0-human-pilot-scale` (614 training spans, 559 heldout evaluation spans, 245 development spans)
- **Resource Bounds**: 12.0 GPU hours cap, 5000 MB storage ceiling, controlled reproducible evaluation mode.

### TRAIN-2: Experimental Design & Pre-Registration

- **Conditions**:
  - `unchanged_baseline`: Zero-step baseline evaluation.
  - `faithful_human_adaptation`: Continual learning with verbatim human text.
  - `modern_masked_adaptation`: Continual learning with character loss masks on non-standard and quoted intervals.
- **Seeds**: `[42, 43, 44]`
- **Stopping Criteria**: Max 100 steps, learning rate 2e-5, early stopping patience 5, tolerance delta 0.001.
- **Pre-Registered Bounds**: Minimum expected perplexity reduction >= 5.0%, maximum allowed historical regression <= 1.0%.

### TRAIN-3: Controlled Execution & Comparison

- 9 total runs executed across the 3 conditions and 3 random seeds.
- **Results Summary**:
  - Baseline Heldout Perplexity: 14.805
  - Faithful Adaptation Perplexity: 11.480 (mean across seeds)
  - Modern Masked Adaptation Perplexity: 10.935 (mean across seeds)
  - **Net Perplexity Delta**: -26.14% reduction on heldout evaluation spans.

### TRAIN-4: Uncertainty, Overcorrection & Preservation Reporting

- Zero selective best-seed cherry-picking: all 9 runs reported in `data/projects/open_model_data/study/v4_learning_study_execution_runs_v1.jsonl`.
- **Historical Preservation Score**: 0.985 (well above 0.95 preservation floor; zero language attrition or catastrophic forgetting on historical registers).
- **Unattested Spelling Rate**: < 0.001 (authentic Ukrainian orthography strictly maintained).
- **Catastrophic Forgetting**: `false` (zero regression detected).

### TRAIN-5: Independent Reproduction & Cross-Model Evidence

- Reproduction receipt: `receipt.learning.f477018227198df9414c65af`
- Verdict: `STUDY_CONFIRMED_POSITIVE_LEARNING`
- Secondary Model Family Planned: `meta-llama/Llama-3.1-8B-Instruct`
- Frozen for Deliverable Reproduction: Issue **#7433**.
