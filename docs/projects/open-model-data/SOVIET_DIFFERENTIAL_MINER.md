# Phase 3.4: Differential Soviet Candidate Miner & Modern Whitelist Filter

## Overview & Purpose

Part of **Epic #6321** (Open Model Data) and **Issue #8008**.

This tool executes differential lexicographical mining by contrasting Soviet СУМ-11 dictionary entries flagged with `sovietization_risk > 0` against pre-Soviet 1920s Academy dictionaries (R2U) and modern Ukrainian standards (Pravopys 2019 / MESU / VESUM).

Crucially, it enforces two non-negotiable linguistic and structural invariants:
1. **20th-Century Technical Neologism Whitelist**: Modern computing, aviation, and scientific terms coined after 1930 (*програмування*, *комп'ютер*, *авіація*, *транзистор*, *лазер*, *пластмаса*) are inherently absent from 1920s dictionaries. Their absence MUST NOT trigger false calque flags.
2. **Network Timeout vs Absence Disambiguation**: Differentiates `SOURCE_UNAVAILABLE` (network timeouts or HTTP failures) from `NOT_FOUND_WITHIN_VERIFIED_COVERAGE`. Network outages are strictly never logged as missing-word proof or treated as evidence of Sovietization.

---

## Data Architecture & Ingestion

### Source Pool

Ingests from `data/sources.db` table `sum11`:
- Total entries flagged with `sovietization_risk > 0`: **7,152**
  - `sovietization_risk = 1`: 6,397 entries
  - `sovietization_risk = 2`: 755 entries

### Adjudication Categories & Statuses

Every entry is deterministically categorized into:
- `WHITELIST_PRESERVED` (`modern_neologism_technical` / `standard_ukrainian_preserved`): Attested 20th-century technical terms and living standard words.
- `CANDIDATE_ADMITTED` (`lexical_calque` / `syntactic_calque`): Verified Russianisms/Soviet calques with authentic living Ukrainian alternatives (*діючий* -> *чинний*, *співпадати* -> *збігатися*, *приймати участь* -> *брати участь*).
- `IDEOLOGICAL_HISTORICAL_ONLY` (`soviet_realia_ideology`): Historical political realia (*комсомол*, *колгосп*, *партком*, *стахановець*).
- `SKRYPNYKIVKA_ARCHAISM_REJECTED` (`skrypnykivka_archaism`): 1920s obsolete purisms (*рівнобіжник*, *терпуг*, *прямовис*) that must NOT be forced as replacements in modern Ukrainian.

---

## Contracts & Receipts

- **Candidate Contract**: `data/projects/open_model_data/contracts/v1_differential_soviet_candidate.schema.json`
- **Receipt Contract**: `data/projects/open_model_data/contracts/v1_differential_soviet_receipt.schema.json`
- **Artifacts Output**: `data/projects/open_model_data/soviet_candidates/`
  - `differential_soviet_receipt.json`
  - `differential_soviet_manifest.json`
  - `differential_soviet_candidates.jsonl`

---

## CLI Usage

### Run Mining & Adjudication

```bash
.venv/bin/python scripts/projects/open_model_data/v4_differential_soviet_miner.py
```

### Verify Integrity & Hashes (Fast Verification Gate)

```bash
.venv/bin/python scripts/projects/open_model_data/v4_differential_soviet_miner.py --verify-only
```
