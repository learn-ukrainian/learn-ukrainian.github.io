# Phase 3.7: Production Shards Assembly (6K SFT + 3K DPO) & Release Packaging

## Overview & Purpose

Part of **Epic #6321** (Open Model Data) and **Issue #8011**.
Operational Plan: [`docs/projects/open-model-data/CORPUS_GROUNDED_DECOLONIZATION_DATASET_PLAN.md`](CORPUS_GROUNDED_DECOLONIZATION_DATASET_PLAN.md) §5 (Phase 3.7).
Predecessor: Phase 3.6 200-Item Pilot Canary (#8010).

This document describes the full production alignment dataset assembly, minimal-pair Direct Preference Optimization (DPO) pairing, cryptographic validation receipt, partition firewall isolation, and release packaging for the **Ukrainian Linguistic Decolonization & Reasoning (ULDR)** dataset.

In accordance with Operator Contract Items 7 (tool-backed claims), 9 (Ukrainian immersion), and 14 (pre-dispatch outcome adequacy), the dataset enforces 100% dictionary attestation via VESUM, 100% factual reasoning verification via `CoTClaimVerifier`, zero held-out contamination, and strict length matching ($\pm 10\%$) on preference pairs.

---

## Deliverables & Dataset Architecture

The production release is organized into standardized, reproducible shards under `data/projects/open_model_data/release/uldr_v1_production/`:

```
data/projects/open_model_data/release/uldr_v1_production/
├── sft/
│   ├── sft_shard_001_of_012.jsonl    # 500 trajectories
│   ├── ...
│   └── sft_shard_012_of_012.jsonl    # 500 trajectories (Total: 6,000)
├── dpo/
│   ├── dpo_shard_001_of_006.jsonl    # 500 preference pairs
│   ├── ...
│   └── dpo_shard_006_of_006.jsonl    # 500 preference pairs (Total: 3,000)
├── production_release_receipt.json   # Validated metadata manifest
└── production_release_receipt.json.sha256 # Detached cryptographic SHA-256 digest
```

---

## 1. 6,000 SFT Reasoning Trajectories

All 6,000 SFT trajectories conform to the strict JSON schema [`v1_decolonization_trajectory.schema.json`](../../../data/projects/open_model_data/contracts/v1_decolonization_trajectory.schema.json).

### Balanced Partition Distribution (70 / 30)

| Partition | Quota | Percentage | Description |
| :--- | :---: | :---: | :--- |
| **CORRECT** | 4,200 | 70.0% | Diagnostic trajectories decolonizing Soviet-era calques, Russianisms, and distorted collocations. |
| **PRESERVE** | 1,800 | 30.0% | STEM negative controls and living standard terms verified in textbooks and VESUM that must be retained. |
| **Total** | **6,000** | **100.0%** | **Exact balanced production dataset** |

### Stratified Multi-Format Distribution

To instill versatile instruction-following capabilities across diverse user prompts, trajectories are stratified across four distinct pedagogical formats:

| Format Type | Total Items | CORRECT Items | PRESERVE Items | Target Share | Purpose |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Quick Tip** | 2,400 | 1,680 | 720 | 40.0% | Fast, direct answers for end users seeking immediate normative guidance. |
| **Minimal Edit** | 1,500 | 1,050 | 450 | 25.0% | Context-preserving sentence revisions maintaining original authorial voice. |
| **Contrastive** | 1,200 | 840 | 360 | 20.0% | Explicit side-by-side comparative analysis of calque vs. питома норма. |
| **Deep Analysis** | 900 | 630 | 270 | 15.0% | In-depth historical, etymological, and morphological exploration. |
| **Total** | **6,000** | **4,200** | **1,800** | **100.0%** | **Full stratified reasoning distribution** |

### Schema & Verification Guarantees

- **100% VESUM Attestation**: Every proposed replacement lemma and negative control term resolves in `data/vesum.db` (`forms_all` table).
- **100% Automated Claim-Verification**: Trajectories verified by `CoTClaimVerifier` (`scripts/projects/open_model_data/v4_verify_trajectory_claims.py`) against local linguistic databases.
- **No Hallucinated History**: PRESERVE negative controls omit suppression notes, preventing confabulated history.

---

## 2. 3,000 DPO Minimal Pairs

The 3,000 preference pairs conform to [`v1_decolonization_dpo_pair.schema.json`](../../../data/projects/open_model_data/contracts/v1_decolonization_dpo_pair.schema.json).

### Contrast Breakdown (2,100 Anti-Soviet + 900 Anti-Hyperpurist)

| Contrast Type | Count | Share | Target Flaw Harvested | Mechanism |
| :--- | :---: | :---: | :--- | :--- |
| **Anti-Soviet Calque Pairs** | 2,100 | 70.0% | `soviet_lexicography_acceptance`, `mechanical_wordnet_synset`, `lack_of_morphemic_reasoning` | Chosen output decolonizes calque; rejected output defends or perpetuates Soviet distortion. |
| **Anti-Hyperpurist Preservation Pairs** | 900 | 30.0% | `unvetted_purism_hallucination` | Chosen output preserves standard STEM term; rejected output applies artificial neologism. |
| **Total** | **3,000** | **100.0%** | — | **Full alignment preference suite** |

### Length Matching & Scaffold Invariants

- **Length Ratio Invariant**: $|len(chosen) - len(rejected)| / max(len(chosen), len(rejected)) \le 10.0\%$. Prevents length bias where models exploit verbosity heuristics.
- **Identical CoT Scaffolds**: Chosen and rejected responses follow parallel rhetorical structures, forcing the model to learn semantic distinctions rather than stylistic shortcuts.

---

## 3. Partition Firewall & Zero Leakage

The dataset is isolated from the 1,000-case held-out evaluation suite (`data/projects/open_model_data/decolonization/partitions/heldout_evaluation_suite_1000.jsonl`):
- **Held-Out Composition**: 600 PRESERVE cases + 400 CORRECT cases from low-web-visibility sources.
- **Calque Target Firewall**: 0 overlap between the 4,200 training calques and the 400 held-out CORRECT target patterns.
- **ID Disjointness**: 0 ID collisions across all 6,000 SFT and 3,000 DPO records against held-out evaluation IDs.
- **MinHash & Token Jaccard Firewall**: Both MinHash similarity and token Jaccard similarity between production shards and held-out items are strictly $< 0.80$. Computed across all 21,000,000 pairwise comparisons (1,000 held-out cases $\times$ 21,000 queries, prompts, and responses), the measured empirical maximums are MinHash similarity: **0.2188** and exact exhaustive token Jaccard: **0.2000**. Both metrics are validated by contract schema and persisted in `production_release_receipt.json`.

---

## 4. Dual-Tier Licensing & Release Packaging

To balance open science and copyright compliance:

| Tier | Distribution Scope | License | Description |
| :--- | :--- | :--- | :--- |
| **Public Tier** | Hugging Face Hub / GitHub Releases | **CC-BY-4.0 / Public Domain** | All synthesized reasoning trajectories, queries, and DPO pairs cleared for public release. |
| **Research-Internal Tier** | Local train-only partition | **Source Custody / Fair Use** | Underlying authentic textbook sentence contexts retained in research partition; weights trained on it are released openly. |

---

## 5. CLI Usage & Verification

### Running Verification Only

To verify an existing release without modifying data files:

```bash
.venv/bin/python scripts/projects/open_model_data/v4_production_shards_assembly.py --verify-only
```

Checks executed:
1. Validates `production_release_receipt.json` against `v1_production_release_receipt.schema.json`.
2. Verifies detached `production_release_receipt.json.sha256`.
3. Verifies SHA-256 and byte count of all 12 SFT shards and 6 DPO shards.
4. Checks exact 6,000 SFT and 3,000 DPO quotas and format allocations.
5. Verifies DPO length ratio difference $\le 10.0\%$.
6. Verifies zero partition leakage against `heldout_evaluation_suite_1000.jsonl`.

### Running Full Assembly

To rebuild the production release from scratch:

```bash
.venv/bin/python scripts/projects/open_model_data/v4_production_shards_assembly.py
```

### Running Test Suite

Execute the comprehensive unit and contract tests:

```bash
.venv/bin/python -m pytest tests/projects/open_model_data/test_v4_production_shards_assembly.py -v
```

---

## 6. Downstream Training Roadmap (Gemma 3 / Gemma 4 on Hugging Face)

For researchers fine-tuning open-weight models (e.g. `google/gemma-3-4b-it` or `google/gemma-4-31B-it`) using Hugging Face Jobs or local GPU clusters:

### Recommended Training Pipeline

1. **Stage 1: SFT Cold Start (6,000 trajectories)**
   - Method: LoRA / QLoRA ($r=16, \alpha=32$, dropout 0.05).
   - Format: ShareGPT / ChatML formatting with system prompt enforcing Ukrainian decolonized reasoning.
   - Learning rate: $2 \times 10^{-4}$ with cosine decay.
   - Batch size: 16 (effective batch size 64 via gradient accumulation).
   - Replay buffer: 15% general Ukrainian educational texts (from Phase 3.6) to prevent catastrophic forgetting.

2. **Stage 2: DPO Alignment (3,000 pairs)**
   - Method: Direct Preference Optimization (TRL `DPOTrainer`).
   - Beta parameter: $\beta = 0.1$.
   - Learning rate: $5 \times 10^{-6}$.
   - Evaluated continuously against the 1,000-case held-out suite to verify:
     - Calque Elimination Rate $\ge 90.0\%$.
     - Harmful Edit Rate $\le 1.0\%$.

### Hugging Face Hub Dataset Sync

The public shards can be uploaded to Hugging Face Hub using the credential in `~/.secrets/hf.key`:

```bash
export HF_TOKEN=$(cat ~/.secrets/hf.key)
huggingface-cli upload learn-ukrainian/uldr-production-shards \
    data/projects/open_model_data/release/uldr_v1_production/ \
    --repo-type dataset
```
