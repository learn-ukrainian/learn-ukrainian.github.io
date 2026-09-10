# Provenance restoration (#7883, PROV-1..PROV-4)

`v4_provenance_restoration` restores source-bound provenance and selection
metadata for the first eligible non-OCR input of the human-source dataset
epic (#7423, operator decision 2026-09-10). It is metadata-only: it never
reads or emits corpus text, never guesses titles or URLs, reacquires no
content, and reopens no existing human-source approval.

Inputs are retained evidence only:

- the committed Phase 1 source/work locator snapshot
  (`source_work_locator_index_v1.compact.jsonl`), expanded strictly;
- `data/sources.db`, read-only, for constant-per-work classification columns
  (`literary_texts.language_period`, `literary_texts.genre`);
- the existing-asset inventory ledger (`inventory/recovery_ledger_v1.jsonl`)
  raw-reconciliation records for acquisition links.

Selection applies the operator scope: the `literary` and non-STEM
`public_textbooks` cohorts are selected; video captions/transcripts
(`external_articles`), Wikipedia (not a selected consumer view), STEM
textbook subjects, the eight private teaching sources, and OCR-derived text
(un-ingested deferred scans and orphan OCR, asserted still un-ingested) are
excluded with their basis recorded in the receipt.

Each emitted row binds the snapshot `locator_id`/`source_id`/`work_id`
(recomputed and compared), restores the canonical URL where retained evidence
holds one, attaches the acquisition reference and edition metadata, and
classifies period/register/domain/original-language/translation status with
explicit `unknown` values and per-field source references. Database group
sets must match the snapshot exactly; conflicting or out-of-vocabulary
classification values fail closed.

Build (requires the local source databases) and verify (works on committed
artifacts):

```bash
.venv/bin/python -m scripts.projects.open_model_data.v4_provenance_restoration build \
  --config data/projects/open_model_data/provenance/v4_provenance_restoration_config_v1.json \
  --input-root . --output-root .

.venv/bin/python -m scripts.projects.open_model_data.v4_provenance_restoration verify \
  --config data/projects/open_model_data/provenance/v4_provenance_restoration_config_v1.json \
  --input-root . --output-root .
```

Outputs are three committed artifacts: the restoration index
(`v4_provenance_restoration_index_v1.jsonl`, header-bound to the snapshot
semantic hash), the separate unresolved-metadata report
(`v4_provenance_restoration_unresolved_v1.json`), and the receipt
(`v4_provenance_restoration_receipt_v1.json`). Validation runs without
waiting for extraction or export; end-to-end provenance propagation is
checked downstream in #7430 PILOT-1/PILOT-4.
