# Native extraction validation and damaged span exclusion (#7885, EXTRACT-1..EXTRACT-4)

`v4_native_extraction_validation` enforces deterministic passage extraction,
character offset linkage, encoding integrity, objective layout anomaly
detection, and fail-closed quarantine of damaged or OCR-derived text spans
under epic #7423 (operator decision 2026-09-10).

## Requirements and Implementation

- **EXTRACT-1 — Immutable Original Wording & Span Linkage:** Preserves exact
  original wording without silent omission or reordering. Declares UTF-8 decoding
  and character-level offset boundaries (`start_char`, `end_char`, `char_length`)
  with bit-level SHA-256 digests (`span_sha256`), binding each span deterministically
  to its parent source, table, and chunk ID.
- **EXTRACT-2 — Encoding Damage & Layout Anomaly Detection:** Validates character
  encoding against corruption artifacts:
  - Unicode replacement characters (`\ufffd`) indicating lossy transcodes.
  - Non-standard ASCII control characters (byte codes < 32 excluding `\t`, `\n`, `\r`).
  - Layout anomalies via `detect_native_text_anomalies`: adjacent duplicate line pairs,
    first-character truncation pairs, and intraline duplicate token spans.
  - Legitimate linguistic orthography (apostrophes, archaic Cyrillic letters `ѣ`, `ѵ`, `ъ`)
    is correctly preserved without false classification as damage.
- **EXTRACT-3 — OCR Exclusion & Fail-Closed Quarantine:**
  - Strictly excludes OCR-derived sources (`EXCLUDED_OCR`, `training_eligible: false`).
  - Quarantines passages with structural layout anomalies (`QUARANTINED_ANOMALOUS`).
  - Rejects spans with encoding corruption (`REJECTED_DAMAGED`).
  - Ensures only fully verified native spans (`ACCEPTED_FAITHFUL`) are marked
    `training_eligible: true`.
- **EXTRACT-4 — Deterministic Stream Reconstruction:** Each span maintains a
  monotonically increasing `sequence_order` (0-indexed) and `stream_digest_contribution`.
  The rolling accumulation of chunk records reconstructs the exact `stream_sha256`
  verified in custody access (#7884), proving 100% fidelity and zero silent omissions.

## Usage

Build extraction index, quarantine report, and receipt:

```bash
.venv/bin/python -m scripts.projects.open_model_data.v4_native_extraction_validation build \
  --config data/projects/open_model_data/extraction/v4_native_extraction_config_v1.json \
  --input-root . --output-root .
```

Verify committed extraction artifacts against schemas and fidelity invariants:

```bash
.venv/bin/python -m scripts.projects.open_model_data.v4_native_extraction_validation verify \
  --config data/projects/open_model_data/extraction/v4_native_extraction_config_v1.json \
  --input-root . --output-root .
```

## Committed Artifacts

1. `data/projects/open_model_data/contracts/v4_native_extraction_*.schema.json`:
   JSON schemas enforcing structural validity of config, items, quarantine report, and receipt.
2. `data/projects/open_model_data/extraction/v4_native_extraction_config_v1.json`:
   Declared target cohorts, input paths, extraction rules, and anomaly detection settings.
3. `data/projects/open_model_data/extraction/v4_native_extraction_index_v1.jsonl`:
   Per-span extraction records containing offset locators, fidelity assessments, and reconstruction digests.
4. `data/projects/open_model_data/extraction/v4_native_extraction_quarantine_report_v1.json`:
   Structured accounting of quarantined or rejected spans with granular anomaly classifications.
5. `data/projects/open_model_data/extraction/v4_native_extraction_receipt_v1.json`:
   Cryptographic receipt binding artifact digests, summary counts, safety assertions, and verdict (`EXTRACTION_FIDELITY_CONFIRMED`).
