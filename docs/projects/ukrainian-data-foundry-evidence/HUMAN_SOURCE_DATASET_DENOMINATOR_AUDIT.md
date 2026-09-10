# Representative Private Human-Source Dataset Denominator & Coverage Audit (Issue #7432)

## Purpose & Scope

This document records the completion of milestone **#7432** for the private human-source Ukrainian dataset epic (**#7423**), establishing the complete representative dataset denominator, accounting for source/work/stratum/view coverage, and freezing dataset release `v4.0.0-human-pilot-scale` for downstream learning studies (**#7889**) and reproduction (**#7433**).

Under operator guidance (2026-09-10):

- Private human-authored learning collection only (literary prose and educational textbooks).
- Explicitly exclude STEM, video captions/transcripts, OCR scans, and private teaching material (tracked as explicit residual strata).
- Strict privacy invariant: Zero raw corpus text and zero private host paths (`/home/`, `/tmp/`, `/Users/`, `/var/`, `file://`, `/private/`) in public receipts/metadata.
- Verbatim text preservation invariant: 100% fidelity, zero artificial modernization or spelling reform imposition.
- Cross-boundary firewall invariant: Chunks and editions grouped by work family; zero cross-partition leakage between training, dev, and heldout evaluation.
- Pre-commit file size ceiling: Strictly below 2000 KB per file.

---

## Contract Schemas

Conforms to Draft 2020-12 JSON Schemas in `data/projects/open_model_data/contracts/`:

1. `v4_human_source_dataset_manifest_v1.schema.json`: Denominator accounting, source selection, and input bindings.
2. `v4_human_source_dataset_record_v1.schema.json`: Emitted dataset records with full provenance, fidelity, dual-view language masks, and split clearance.
3. `v4_human_source_dataset_receipt_v1.schema.json`: Cryptographic verification receipt, deduplication yield, storage limits, and frozen downstream targets.

---

## Deliverable & Acceptance Criteria

### SCALE-1: Denominator Recording & Accounting

- **Total Holdings Sources Available**: 16
- **Total Selected Sources**: 3 (curated non-OCR native human sources)
- **Total Work Families**: 3
- **Total Evaluated Spans**: 1,419
- **Total Admitted Spans**: 1,418
- **Exported Training Spans**: 614
- **Firewalled Heldout Evaluation Spans**: 559
- **Development Spans**: 245
- **Quarantined Spans**: 1
- **Strata Coverage**:
  - `literary_prose`: Covered (`source.literary.0020599cfcaf15e887bdb73c`, `source.literary.451b33b316e840f953b4e393`).
  - `educational_textbook`: Covered (`source.public_textbooks.00cebc897bb7feab776c42a8`).
  - `stem_technical`: Residual (operator excluded).
  - `video_captions`: Residual (operator excluded).
  - `ocr_scans`: Residual (operator excluded).
  - `private_teaching_material`: Residual (operator excluded).

### SCALE-2: Full Reviewed Pipeline Application

- Native digital extraction validation (#7885), language usage classification & dual-view loss masks (#7886), and work family grouping & heldout firewalls (#7887) applied with zero silent drops.
- 1 quarantined span (upstream layout repetition anomaly) tracked explicitly and excluded from training.

### SCALE-3: Register Diversity & Linguistic Validity

- Authentic modern standard, literary register, and historical/quoted language preserved verbatim.
- Zero synthetic distortion, zero unverified spelling modifications, and zero manufactured corrections.
- Dual-view representation:
  - `faithful_view`: Preserves full authentic text for robust representation.
  - `modern_view`: Provides masking intervals for non-standard or foreign citations during modern Ukrainian standard learning.

### SCALE-4: Versioned Consumer Payloads

- Exported records format: `data/projects/open_model_data/dataset/v4_human_source_dataset_records_v1.jsonl`.
- Header + 1,419 records each carrying deterministic `record_id`, complete provenance links, fidelity verification, and firewall clearance.

### SCALE-5: Deduplication Yield & Storage Bounds

- **Unique Spans**: 1,419 (100% deduplication yield).
- **Records File Size**: ~1,853 KB (strictly below 2,000 KB pre-commit ceiling).
- **Zero Host Paths**: Automated verification confirms absence of private local paths.

### SCALE-6: Version Freeze for Downstream Deliverables

- **Dataset Version**: `v4.0.0-human-pilot-scale`
- **Frozen for Learning Study**: Issue **#7889**
- **Frozen for Reproducibility**: Issue **#7433**
