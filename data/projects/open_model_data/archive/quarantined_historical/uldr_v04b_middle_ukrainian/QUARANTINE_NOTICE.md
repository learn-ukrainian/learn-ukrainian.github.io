# QUARANTINE NOTICE: uldr_v04b_middle_ukrainian

> **DO NOT USE FOR MODEL TRAINING OR UNIFIED DATASET PACKAGING**
> **Quarantine Order:** Issue #8343 (Parent Epic #6321), Operator Decision 2026-09-20.

## Rationale for Quarantine

The generated dataset files in this directory (`middle_ukrainian_eval.jsonl` and `sft/sft_shard_*.jsonl`, originally produced under #8105) have been withdrawn from the release tier and quarantined.

### Measured Deficiencies:
1. **Template Monotony & Lack of Reasoning Diversity:**
   Twenty reasoning patterns cover 99% of the 10,000 records (with five question patterns covering 90% of the dataset), failing to capture the rich syntactic and stylistic variety of Middle Ukrainian.
2. **Unresolved Historical Admixtures:**
   Texts from the 14th–17th centuries exhibit complex stratification across Ruthenian chancery language, Church Slavonic, Polish, and Latin loan mechanisms that require domain-expert philological review.
3. **Unvalidated Linguistic Assertions:**
   Without expert historical philological oversight, automated synthetic generation introduces inaccurate attribution and pseudo-dialectal classifications.

## Scope & Preservation Policy

1. **Not for Training:**
   No training or fine-tuning pipelines or dataset packaging scripts may consume files from this directory.
2. **Raw Sources Preserved:**
   All primary historical texts in `data/sources.db` (chancery acts, Cossack chronicles, polemical literature) remain intact and untouched.
3. **Protective Test Questions Preserved:**
   Protective evaluation criteria ensuring modern models do not erroneously "correct" historical quotations into contemporary Ukrainian remain active in `tests/projects/open_model_data/test_v5_dialect_historical_protection.py`.
4. **Future Re-opening Terms:**
   This dataset may only be reopened when an expert historical linguist is available to specify canonical, high-fidelity criteria for authentic records, producing a small, expert-checked benchmark rather than large-scale synthetic generation.
