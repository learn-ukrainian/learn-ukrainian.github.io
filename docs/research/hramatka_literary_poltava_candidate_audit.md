# Literary Poltava candidate audit

## Decision and scope

**Verdict: `rebuild_required`.** No record has evidence for license, copyright, redistribution, or model-training permission; those unknowns fail closed.

This dossier audits the frozen candidate as evidence, not as a releasable dataset. It answers whether the committed JSONL can presently support claims of traceable provenance, known rights, deduplication, evaluation isolation, balanced composition, or linguistically adjudicated quality. It does not train a model, generate benchmark responses, upload data, obtain licenses, or convert heuristic observations into expert judgments. A negative verdict therefore closes this audit while intentionally blocking the candidate from training and publication.

The unit of analysis is one JSONL record joined by its numeric `lit-` identifier to one `literary_texts` row in the operator-supplied SQLite database. The committed receipts preserve a disposition for every record. They are tied to the exact input hashes below, so substituting either input requires a fresh run and a fresh decision.

## Frozen inputs and reproducibility contract

- Frozen JSONL SHA-256: `06923700a0f5a6bbb077221325b8b7cc2b5e0a094100569494af32acd52c3424`.
- Source database SHA-256: `8cb9e113ba85c9a99341cfb05ad9dfa7db390526481c7824f331e7d1ec0ef3ac`.
- Records: 5000; unique IDs: 5000.
- Joined database rows: 5000; missing rows: 0.
- Required JSONL-field missing counts: `{"author":0,"dialect_standard":0,"id":0,"language_period":0,"text":0,"work":0,"year":0}`.

The audit opens SQLite through URI `mode=ro`, selects only the lineage columns recorded in `input_contract.json`, and hashes both inputs before and after reading. It stops if an input changes during the run. The database is gitignored runtime material rather than a repository artifact; its own acquisition history is not established here. Reproduction therefore requires an operator-supplied file with the recorded SHA-256. The committed lineage projection hash and record dispositions allow reviewers to verify what the audit saw without pretending that the database itself has known provenance.

All required JSONL fields are checked for presence. Record IDs are parsed deterministically, and the joined row preserves its chunk, work, source-file, genre, URL, author, work, and year values. A successful join means only that the local rows correspond; it is not evidence that the edition, scanning source, chain of custody, or legal status is known.

## Rights and provenance gate

Every one of the 5000 records is excluded pending rights and provenance evidence. The supplied schemas do not provide an authoritative external catalog identifier, acquisition source, edition or editor, license, copyright status, redistribution permission, model-training permission, translation origin, region, or register. The aggregate missing counts are `{"acquisition_source":5000,"copyright_status":5000,"edition_or_editor":5000,"external_source_or_catalog_id":5000,"license":5000,"model_training_permission":5000,"redistribution_permission":5000,"region":5000,"register":5000,"translation_origin":5000}`.

The audit applies a fail-closed rule: absence of a license or permission is not interpreted as permission, public-domain status, fair use, or an implied right to redistribute or train. It also makes no jurisdiction-specific legal conclusion. A future rebuild must attach record- or work-level evidence that a qualified reviewer can inspect. Assertions in filenames, source URLs, historical dates, or earlier project documents do not substitute for that evidence.

This failure is collection-wide and decisive. Duplicate removal, linguistic cleanup, or a favorable contamination result cannot cure it. The appropriate remediation is a rights-cleared rebuild rather than editing these records in place and retaining an unverifiable lineage.

## Duplicate audit

For exact comparison, text is normalized to Unicode NFC, case-folded, stripped of punctuation through non-word-character replacement, and collapsed to single spaces. Equal normalized strings become one connected cluster. For near comparison, every non-exact pair is evaluated with three-token-shingle Jaccard similarity at a threshold of 0.90. A shingle-cardinality ratio pre-filter is mathematically necessary for a pair to reach that threshold, so it cannot discard a qualifying pair. Connected components, member indexes, and scored edges are written to `duplicate_clusters.json`.

The frozen candidate has 87 exact clusters covering 178 records and 1 near cluster covering 2 records. These counts describe text similarity after the declared normalization; they do not determine which edition is authoritative or whether similar passages are legitimate textual reuse. A rebuild should deduplicate only after provenance is recovered, so a keeper can be selected using source quality and rights evidence rather than arbitrary record order.

## Evaluation-contamination audit

The contamination check expands the compact held-out manifest using its declared item and reference layouts. It inventories source strings and every reference target instead of hashing only the compact outer object. JSONL evaluation material is traversed for source, target, text, and reference fields. Candidate strings and evaluation strings use the same normalization as the exact duplicate pass; non-exact pairs use the same 0.90 three-token shingle threshold.

| Evaluation inventory | SHA-256 | Texts | Unique normalized texts |
| --- | --- | ---: | ---: |
| `data/projects/ua_eval_harness/heldout_manifest_v1.json` | `56eb4fc17a5ed6967c5c13fbdc9fde964d1b8fb08bde7da7f15cf535486735dd` | 1595 | 1481 |
| `data/projects/ua_eval_harness/evalset_v1.jsonl` | `34a47de1a8826a60895898bd8d94c5d794159a9ea291a51a7f85790a3bb7f976` | 156 | 81 |

No candidate overlap was found: `{}`. This result is limited to the exact frozen inventories and algorithms named above. It does not establish absence of overlap with private prompts, prior versions, unlisted test sets, or semantic paraphrases below the threshold. Any future training view must preserve these exclusions and rerun the check against the then-current evaluation inventories.

## Composition and balance observations

The following counts expose composition rather than certify balance. Author and language-period values come from the candidate; genre and source-file proxies come from the joined database. A source-file label is only a grouping proxy and is not an acquisition receipt. Large collective, unknown, scholarly, chronicle, or encyclopedia groups can dominate model behavior even when the raw record count appears large.

| Dimension | Value | Records |
| --- | --- | ---: |
| Author | Колектив | 750 |
| Author | Грушевський М. | 696 |
| Author | Невідомий | 443 |
| Author | Нестор | 198 |
| Author | Франко І. | 138 |
| Author | Чижевський Д. | 103 |
| Author | Антологія | 99 |
| Author | Нечуй-Левицький І. | 85 |
| Author | Гончар О. | 79 |
| Author | Величко С. | 76 |
| Language period | `modern` | 3733 |
| Language period | `middle_ukrainian` | 692 |
| Language period | `old_east_slavic` | 575 |
| Genre | `scholarly` | 1871 |
| Genre | `chronicle` | 941 |
| Genre | `prose` | 665 |
| Genre | `encyclopedia` | 565 |
| Genre | `poetry` | 410 |
| Genre | `polemic` | 109 |
| Genre | `philosophy` | 100 |
| Genre | `biography` | 75 |
| Genre | `anthology` | 36 |
| Genre | `legal` | 29 |
| Source-file proxy | `wave8-ukr-lit-entsyklopediia` | 313 |
| Source-file proxy | `wave4-hrushevsky-iur-t2-3` | 214 |
| Source-file proxy | `wave4-hrushevsky-iur-t7-10` | 198 |
| Source-file proxy | `wave12-ipatskyj-litopys` | 149 |
| Source-file proxy | `ukrlib-franko` | 138 |
| Source-file proxy | `wave7-entsyklopediia-ukrainoznavstva` | 135 |
| Source-file proxy | `wave1-pvl-ipatskyi` | 108 |
| Source-file proxy | `wave10-shevchenkivsky-slovnyk` | 99 |
| Source-file proxy | `wave4-hrushevsky-iur-t1` | 91 |
| Source-file proxy | `ukrlib-nechuy` | 85 |

The concentration table shows that this is not demonstrated to be a balanced Poltava literary sample. Period tags include modern, middle Ukrainian, and old East Slavic material; the audit does not validate those labels or infer a single contemporary regional standard from them. Similarly, author strings such as collective or unknown prevent reliable author-level diversity claims. A rebuild needs a documented sampling frame, explicit targets by period, genre, author, region, and register, and a report of both counts and text volume before a balance claim can be evaluated.

## Heuristic quality signals

The non-adjudicative signal counts are `{"low_cyrillic_ratio_signal":58,"ocr_or_layout_noise_signal":752,"repetition_signal":1,"russian_only_letter_signal":1496}`. The Russian-only-letter signal detects any occurrence of `ы`, `э`, `ъ`, or `ё`; it does not decide whether an occurrence is a quotation, historical orthography, OCR corruption, a proper name, or non-Ukrainian prose. The low Cyrillic-ratio signal marks texts where fewer than half of alphabetic characters match the script test used by the tool. The OCR/layout signal detects replacement characters, surrogate damage, long punctuation runs, or spaced dot runs. The repetition signal identifies a high repeated-token ratio only in texts longer than twelve normalized words.

These flags route records for human review; they are not labels and do not authorize automatic deletion. Ukrainian linguists and textual scholars must review contextual evidence before assigning language, dialect, calque, OCR, or authenticity judgments. In particular, this audit does not establish the earlier descriptions `pure`, `native`, `decolonized`, or `Poltava standard`.

## Record dispositions and evidence artifacts

`record_dispositions.jsonl` contains exactly one line per candidate record in input order. Each line records the candidate ID and line, joined database ID and lineage projection, missing lineage fields, the ten missing rights or metadata fields, heuristic anomaly signals, evaluation-overlap status, and a fail-closed disposition. An evaluation overlap would take the stricter `excluded_evaluation_overlap` disposition; otherwise the current candidate uses `excluded_pending_rights_and_provenance`.

`audit_summary.json` provides aggregate counts and the collection verdict. `input_contract.json` binds the dataset, runtime database, selected lineage projection, and evaluation inventories. `duplicate_clusters.json` contains the normalization and cluster evidence. `evaluation_overlap.json` contains the expanded inventory receipts and matching results. Together these artifacts support review of the decision without converting unknown facts into positive claims.

## Required rebuild controls

A replacement collection should begin from independently identified works, not from the present random export. Before inclusion, each work needs an external catalog or source identifier, acquisition receipt, edition/editor record, and source URL or physical-location citation. It also needs an explicitly reviewed copyright status, license, redistribution permission, and model-training permission. Translation origin, language period, region, register, genre, author, and work identifiers should be reviewable fields rather than inferred marketing descriptions.

After those gates, the rebuild should preserve full sampling receipts, run exact and near deduplication, freeze evaluation inventories, exclude every overlap, and route anomaly signals to Ukrainian experts. It should publish aggregate balance tables and unresolved unknowns. Only a subsequent audit against newly frozen hashes can decide whether release or training is permissible; this dossier supplies no such permission.

## Unknowns and limits

- Heuristic anomaly flags are signals, not linguistic or legal adjudications.
- No record-level external catalog, license, publisher, estate, or government/legal citation was supplied; this audit makes no external rights assertion.
- The labels pure, native, decolonized, and Poltava standard are unestablished by this audit.
- Duplicate normalization treats straight and curly Ukrainian apostrophes as punctuation, so apostrophe placement and encoding are not preserved in token shingles.
- Similarity thresholds do not capture all paraphrase, quotation, or shared-source relationships.
- Counts are record counts, not token-weighted or work-weighted measures of representation.
- Database source-file and URL values are lineage clues, not verified acquisition or rights evidence.
- No external legal, bibliographic, archival, linguistic, or regional adjudication was performed.

## Stale-claim inventory

| Path | Lines | Claim | Support status | Action |
| --- | --- | --- | --- | --- |
| scripts/dataset/export_literary_poltava_dataset.py | 1-5, 40, 52-82 | The random export is pristine, authentic Poltava-Kyiv data ready to fine-tune open models. | `unsupported_and_unsafe_to_regenerate` | Do not run against the committed candidate; replace only after a rights-cleared rebuild. |
| docs/architecture/ADR_013_LITERARY_POLTAVA_ALIGNMENT.md | 19, 23-47 | The corpus is pristine, decolonized, hand-verified, release-ready, and approved for fine-tuning. | `contradicted_by_fail_closed_audit` | Supersede in a separately scoped documentation correction; do not use as current authority. |
| docs/guides/HUGGINGFACE_GEMMA_FINETUNING_GUIDE.md | 3, 8-25 | The candidate is a clean pre-packaged dataset that can be uploaded publicly. | `contradicted_by_unknown_rights_and_provenance` | Do not upload or train; retire or gate the guide in a separate documentation change. |
| docs/research/DATASET_UNIQUENESS_AND_UNLP_GAP_ANALYSIS.md | 23-59 | The project is releasing a unique decolonized dataset with zero machine translation or calques. | `unestablished` | Retain only as historical research after adding a clear supersession notice. |
| docs/research/UNLP_DATASET_SURVEY_AND_EVALUATION.md | 35-71 | The candidate should be used for Poltava alignment and decolonized fine-tuning. | `contradicted_by_rebuild_required_verdict` | Do not use as a training recommendation; supersede separately. |
| docs/strategy/STRATEGY_MAKING_GOOGLE_NOTICE_OUR_BENCHMARKS.md | 3-8, 21-55 | Purity, publication readiness, and visibility probabilities support public release. | `already_disclaimed_in_document_header` | No audit-PR edit; preserve the existing historical-context warning. |
