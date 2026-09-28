# QUARANTINE NOTICE: uldr_v04a_kyivan_rus

> **DO NOT USE FOR MODEL TRAINING OR UNIFIED DATASET PACKAGING**
> **Quarantine Order:** Issue #8343 (Parent Epic #6321), Operator Decision 2026-09-20.

## Rationale for Quarantine

The generated dataset files in this directory (`kyivan_rus_epigraphic_eval.jsonl` and `sft/sft_shard_*.jsonl`, originally produced under #8103) have been withdrawn from the release tier and quarantined.

### Measured Deficiencies:
1. **Dating and Attribution Contradictions:**
   467 Kyivan Rus records are labelled "XI–XIII century" while their own first reasoning step cites a date range starting between 1400 and 1999 (e.g. late Latin-script graffiti erroneously described as 11th–13th-century living vernacular speech).
2. **Linguistic Admixtures:**
   The texts are deeply mixed with Church Slavonic, chancery language, Polish, and Latin. Properly disentangling vernacular Old Ukrainian from liturgical Church Slavonic and foreign chancery admixtures requires a professional historical linguist.
3. **Template Monotony:**
   Five synthetic question patterns cover 94% of lines in the generated trajectories.

## Scope & Preservation Policy

1. **Not for Training:**
   No training or fine-tuning pipelines or dataset packaging scripts may consume files from this directory.
2. **Raw Sources Preserved:**
   All primary historical texts in `data/sources.db` (epigraphy, chronicles) remain intact and untouched.
3. **Protective Test Questions Preserved:**
   Protective evaluation criteria ensuring modern models do not erroneously "correct" historical quotations into contemporary Ukrainian remain active in `tests/projects/open_model_data/test_v5_dialect_historical_protection.py`.
4. **Future Re-opening Terms:**
   This dataset may only be reopened when an expert historical linguist is available to specify canonical, high-fidelity criteria for authentic records, producing a small, expert-checked benchmark rather than large-scale synthetic generation.
