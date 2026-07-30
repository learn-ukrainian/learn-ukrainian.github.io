# Literary Poltava candidate audit

## Observed facts

- Frozen JSONL SHA-256: `06923700a0f5a6bbb077221325b8b7cc2b5e0a094100569494af32acd52c3424`.
- Source database SHA-256: `8cb9e113ba85c9a99341cfb05ad9dfa7db390526481c7824f331e7d1ec0ef3ac`.
- Records: 5000; unique IDs: 5000; joined database rows: 5000.
- Missing database rows: 0; all records lack recorded rights evidence.
- Missing rights/provenance fields: {"acquisition_source":5000,"copyright_status":5000,"edition_or_editor":5000,"external_source_or_catalog_id":5000,"license":5000,"model_training_permission":5000,"redistribution_permission":5000,"region":5000,"register":5000,"translation_origin":5000}.
- Anomaly signals (heuristic only): {"low_cyrillic_ratio_signal":59,"ocr_or_layout_noise_signal":752,"repetition_signal":1,"russian_only_letter_signal":1496}.
- Exact duplicate clusters: 87; near-duplicate clusters: 1.
- Evaluation overlaps: {}.

## Inferences

- **Verdict: rebuild_required** — No record has evidence for license, copyright, redistribution, or model-training permission; those unknowns fail closed.
- The top author concentrations are recorded in the machine-readable receipt: [["Колектив",750],["Грушевський М.",696],["Невідомий",443],["Нестор",198],["Франко І.",138]].

## Unknowns and limits

- Heuristic anomaly flags are signals, not linguistic or legal adjudications.
- No record-level external catalog, license, publisher, estate, or government/legal citation was supplied; this audit makes no external rights assertion.
- The labels pure, native, decolonized, and Poltava standard are unestablished by this audit.

## Recommendations

- Rebuild from sources with per-work external catalog identifiers, acquisition receipts, edition/editor, license, copyright, redistribution, and explicit model-training permissions.
- Exclude every record marked as evaluation overlap from any future training view; have Ukrainian linguistic experts review all anomaly signals and any regional/standard claim.

## Stale-claim inventory

| Path | Lines | Claim | Support status | Action |
| --- | --- | --- | --- | --- |
| scripts/dataset/export_literary_poltava_dataset.py | 1-5, 40, 52-82 | The random export is pristine, authentic Poltava-Kyiv data ready to fine-tune open models. | `unsupported_and_unsafe_to_regenerate` | Do not run against the committed candidate; replace only after a rights-cleared rebuild. |
| docs/architecture/ADR_013_LITERARY_POLTAVA_ALIGNMENT.md | 19, 23-47 | The corpus is pristine, decolonized, hand-verified, release-ready, and approved for fine-tuning. | `contradicted_by_fail_closed_audit` | Supersede in a separately scoped documentation correction; do not use as current authority. |
| docs/guides/HUGGINGFACE_GEMMA_FINETUNING_GUIDE.md | 3, 8-25 | The candidate is a clean pre-packaged dataset that can be uploaded publicly. | `contradicted_by_unknown_rights_and_provenance` | Do not upload or train; retire or gate the guide in a separate documentation change. |
| docs/research/DATASET_UNIQUENESS_AND_UNLP_GAP_ANALYSIS.md | 23-59 | The project is releasing a unique decolonized dataset with zero machine translation or calques. | `unestablished` | Retain only as historical research after adding a clear supersession notice. |
| docs/research/UNLP_DATASET_SURVEY_AND_EVALUATION.md | 35-71 | The candidate should be used for Poltava alignment and decolonized fine-tuning. | `contradicted_by_rebuild_required_verdict` | Do not use as a training recommendation; supersede separately. |
| docs/strategy/STRATEGY_MAKING_GOOGLE_NOTICE_OUR_BENCHMARKS.md | 3-8, 21-55 | Purity, publication readiness, and visibility probabilities support public release. | `already_disclaimed_in_document_header` | No audit-PR edit; preserve the existing historical-context warning. |
