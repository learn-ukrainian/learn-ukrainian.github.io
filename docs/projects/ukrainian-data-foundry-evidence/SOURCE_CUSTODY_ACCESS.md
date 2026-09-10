# Source custody access and non-OCR lineage verification (#7884, ACCESS-1..ACCESS-4)

`v4_source_custody_access` resolves storage/custody arrangements and verifies
non-OCR extraction lineage for selected human-authored Ukrainian sources under
epic #7423 (operator decision 2026-09-10).

The September 2026 inspection located the retained archive through the existing
storage resolver but did not establish access from the execution host to every
selected original. Missing resolver access is not missing collection evidence.
This module establishes a bounded, reproducible path and proof for the first
eligible source/cohort without requiring clearing the entire collection before
#7430 starts.

## Requirements and Implementation

- **ACCESS-1 — Storage/Custody Resolution:** Resolves selected native digital
  sources through established storage arrangements (`data/sources.db` read-only
  tables `literary_texts` and `textbooks`, and `data/textbook_chunks`). Records
  a text-free access result with row/byte counts and deterministic stream hashes.
- **ACCESS-2 — Non-OCR Lineage Confirmation:** Confirms each selected input is
  native digital text (`literary-non-ocr` cohort from established literary
  archives) or has a verified native PDF text layer (`public-textbooks` cohort
  with `native_pdf_text` / `native_text` extraction mode). OCR-derived hidden
  text layers (`apple_vision_ocr`, scans, orphan OCR) are strictly excluded;
  unknown extraction lineage fails closed and is never silently called native.
- **ACCESS-3 — Bounded Executable Read Path:** Implements `BoundedCustodyReader`
  which executes streaming queries in bounded memory (`PRAGMA query_only = ON`),
  computing text-free integrity digests without broad recollection, without
  creating new storage infrastructure, and without copying protected corpus text
  to the coordinator or into logs.
- **ACCESS-4 — Missing Inputs & Disjoint Progression:** Documents unmounted
  host archive paths (e.g. raw GDrive PDFs on VPS) in a structured missing
  report assigned to `"existing custody/source-access owner"`. Permits the first
  eligible cohort (`literary-non-ocr`, 229/229 sources accessible) and ready
  native textbooks to proceed immediately into #7885 and #7430.

## Usage

Build custody artifacts from local databases and chunk files:

```bash
.venv/bin/python -m scripts.projects.open_model_data.v4_source_custody_access build \
  --config data/projects/open_model_data/custody/v4_source_custody_access_config_v1.json \
  --input-root . --output-root .
```

Verify committed artifacts against contracts and invariants:

```bash
.venv/bin/python -m scripts.projects.open_model_data.v4_source_custody_access verify \
  --config data/projects/open_model_data/custody/v4_source_custody_access_config_v1.json \
  --input-root . --output-root .
```

Execute a bounded text-free stream read:

```bash
.venv/bin/python -m scripts.projects.open_model_data.v4_source_custody_access read \
  --database data/sources.db --table literary_texts --source-file ukrlib-andiyevska
```

## Committed Artifacts

1. `data/projects/open_model_data/contracts/v4_source_custody_access_*.schema.json`:
   JSON schemas enforcing strict structure for config, items, missing report, and receipt.
2. `data/projects/open_model_data/custody/v4_source_custody_access_config_v1.json`:
   Declared operator decision, input paths, and cohort resolver mappings.
3. `data/projects/open_model_data/custody/v4_source_custody_access_index_v1.jsonl`:
   Per-source resolved custody access record, text-free stream hash, and permission status.
4. `data/projects/open_model_data/custody/v4_source_custody_missing_report_v1.json`:
   Accounting of unmounted host paths with explicit owner and non-blocking verdict.
5. `data/projects/open_model_data/custody/v4_source_custody_access_receipt_v1.json`:
   Receipt binding artifact hashes, summary metrics, safety assertions, and verdict.
