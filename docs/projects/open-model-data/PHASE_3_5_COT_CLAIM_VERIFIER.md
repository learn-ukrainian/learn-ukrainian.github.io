# Phase 3.5: Automated CoT Claim-Verifier & Schema Reconciliation

## Overview & Purpose

Part of **Epic #6321** (Open Model Data) and **Issue #8009**.

This component implements the automated factual claim-verification engine for Chain-of-Thought (CoT) reasoning trajectories in the Ukrainian Linguistic Decolonization Reasoning dataset. Every trajectory generated for SFT/DPO training undergoes rigorous, multi-authority factual grounding to prevent hallucinated linguistic facts, fabricated dictionary citations, or incorrect inflection counts from entering model training data.

### Core Capabilities

1. **Schema Reconciliation for Negative Controls**:
   - Reconciled `data/projects/open_model_data/contracts/v1_decolonization_trajectory.schema.json` with conditional validation (`allOf` / `if` / `then`).
   - For `CORRECT` candidates (`is_calque_or_russianism == true`), historical suppression fields (`historical_suppression_type` and `historical_source_evidence`) remain strictly required.
   - For `PRESERVE` negative controls (`is_calque_or_russianism == false`), suppression fields are omitted without validation failure, reflecting the authentic living standard status of non-calque Ukrainian words.

2. **Automated CoT Claim-Verifier (`v4_verify_trajectory_claims.py`)**:
   - Parses each reasoning step inside the trajectory's Chain-of-Thought and extracts testable assertions across multiple linguistic facets:
     - **VESUM (`data/vesum.db`)**: Lemma attestation, exact inflected forms count verification (zero-tolerance exact count matching, eliminating hallucinated paradigm sizes), grammatical tags, and living standard attestation.
     - **СУМ-11 (`data/sources.db`)**: Headword presence (including pipe-delimited variants), volume alphabetical spans (Tom 1–11) and publication years (1970–1980), stylistic labels (`заст.`, `розм.`, `рідко`, `діал.`), and Soviet ideological codification risk context.
     - **R2U Pre-Soviet Academy Dictionaries**: Attestation in 1920s lexicographical works (Krymskyi, Yefremov, Holoskevych) via local differential cache (`r2u_differential_cache.json`) with syntax-aware polarity verification (distinguishing asserted presence vs asserted absence and rejecting polarity mismatches).
     - **ULIF (`data/ulif_dump_all.db` & `data/sources.db`)**: Official orthographic register and vocabulary attestation.
     - **Non-Living Register Tiers**: Factual verification of `classical_regional`, `technical_compound`, and `purist_neologism` entries, requiring valid external evidentiary citations (`evidence_source`) and attestation checks.
     - **PRESERVE Negative Controls**: Rejection of false suppression claims for standard vocabulary.
   - Enforces **hard rejection**: Any trajectory containing ungrounded, fabricated, or miscounted claims is immediately routed to `rejected_trajectories.jsonl`.
   - Produces cryptographic verification receipts (`cot_claim_verification_receipt.json`) validated against `v1_cot_claim_verification_receipt.schema.json` with dynamically derived invariants:
     - `pass_rate_100_percent`: All input trajectories passed verification with zero rejections.
     - `zero_unverified_dictionary_claims`: 100% of СУМ-11 and R2U claims verified against authoritative data.
     - `zero_unattested_living_standard_terms`: All living standard lemmas verified in VESUM or ULIF.
     - `zero_network_errors_as_missing_word`: No network timeouts or missing cache entries treated as negative assertions.
     - `no_private_host_paths`: Trajectory-level and receipt-level OPSEC scans pass with zero private paths.

3. **OPSEC & Subprocess Safety**:
   - Zero leakage of private hostnames, IP addresses, or local developer paths (`/home/ops`, `/Users/`) into public artifacts, verified via trajectory-level OPSEC scans on both verified and rejected datasets.
   - All subprocess calls bounded by explicit timeouts (`timeout=30`), audited via AST.

---

## Architecture & Data Flow

```
Input Trajectories (JSONL)
        │
        ▼
┌────────────────────────────────────────────────────────┐
│             v4_verify_trajectory_claims.py            │
│                                                        │
│  1. Schema Validation (conditional JSON Schema)        │
│  2. Claim Parsing (regex + semantic extraction)       │
│  3. Authority Verification:                           │
│     ├─ VESUM (forms_all: lemma, tags, form count)     │
│     ├─ СУМ-11 (headword, volume, definitions)         │
│     ├─ R2U Differential Cache (1920s attestation)     │
│     └─ ULIF (orthography, register labels)            │
│  4. Invariant Auditing (OPSEC, timeouts, pass rate)   │
└───────────────────────┬────────────────────────────────┘
                        │
         ┌──────────────┴──────────────┐
         ▼                             ▼
Verified Trajectories        Rejected Trajectories
(verified_trajectories.jsonl) (rejected_trajectories.jsonl)
         │
         ▼
Verification Receipt & Integrity Manifest
(cot_claim_verification_receipt.json)
```

---

## Contracts & Receipts

- **Trajectory Contract**: `data/projects/open_model_data/contracts/v1_decolonization_trajectory.schema.json`
- **Receipt Contract**: `data/projects/open_model_data/contracts/v1_cot_claim_verification_receipt.schema.json`
- **Generated Artifacts**:
  - `data/projects/open_model_data/trajectories/verified_trajectories.jsonl`
  - `data/projects/open_model_data/trajectories/rejected_trajectories.jsonl`
  - `data/projects/open_model_data/trajectories/cot_claim_verification_receipt.json`

---

## CLI Usage

### Run Full Verification

```bash
.venv/bin/python scripts/projects/open_model_data/v4_verify_trajectory_claims.py \
  --input data/projects/open_model_data/decolonization/seeds/seed_decolonization_trajectories.jsonl \
  --output data/projects/open_model_data/trajectories/verified_trajectories.jsonl \
  --rejected-output data/projects/open_model_data/trajectories/rejected_trajectories.jsonl \
  --receipt data/projects/open_model_data/trajectories/cot_claim_verification_receipt.json
```

### Fast Receipt & Checksum Integrity Verification (`--verify-only`)

```bash
.venv/bin/python scripts/projects/open_model_data/v4_verify_trajectory_claims.py --verify-only
```

---

## Testing & Quality Gates

Run the contract and claim verification test suites:

```bash
.venv/bin/python -m pytest tests/projects/open_model_data/test_v1_decolonization_contracts.py -v
.venv/bin/python -m pytest tests/projects/open_model_data/test_v4_verify_trajectory_claims.py -v
```
