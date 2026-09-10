# First Private Human-Source Dataset Pilot & Proof-of-Mechanism (Issue #7430)

## Purpose & Scope
This document records the completion of milestone **#7430** for the private human-source Ukrainian dataset epic (**#7423**), delivering the first concrete 1/1 human-source proof-of-mechanism and the representative pilot dataset across the verified human collection.

Under operator guidance (2026-09-10):
- Excludes STEM material, video captions/transcripts, OCR scans, and private teaching material.
- Reuses established source verification and applicable local-learning approval; requires zero blanket re-verification or public redistribution prerequisites.
- Preserves verbatim Ukrainian text with authentic dialectal, historical, and literary registers intact.
- Enforces strict zero-leakage firewalls between training, development, and held-out evaluation partitions.
- Zero raw corpus text and zero private host paths are emitted into public receipts or metadata.

---

## Contract Schemas
Conforms to Draft 2020-12 JSON Schemas in `data/projects/open_model_data/contracts/`:
1. `v4_human_source_pilot_manifest_v1.schema.json`: Pilot denominator, stratum coverage, and input bindings.
2. `v4_human_source_pilot_record_v1.schema.json`: Emitted pilot records with complete provenance, fidelity, dual-view language masks, and split clearance.
3. `v4_human_source_pilot_receipt_v1.schema.json`: Cryptographic verification receipt, accounting, and 1/1 proof of mechanism.

---

## Deliverable & Acceptance Criteria

### PILOT-1: 1/1 Actual Human-Source Proof of Mechanism
- **Proof Record ID**: `record.human.259e48bf64167e8b0499129a`
- **Work Family**: `work_family.literary.yuriy_andrukhovych_moskoviada`
- **Source ID**: `source.literary.451b33b316e840f953b4e393`
- **Span SHA-256**: `18771bb492efa1435d908096e6e500bc2aafefe82dfad162bee0179f5d5f8f34`
- **Clearance**: `builder_training_cleared: true`, `verbatim_preserved: true`
- **Provenance**: Authentic human-authored literary prose; non-OCR native digital extraction.

### PILOT-2: Stratum Coverage & Denominator
The pilot denominator is drawn from representative non-OCR human holdings:
- **Literary Prose**: Covered (`source.literary.0020599cfcaf15e887bdb73c`, `source.literary.451b33b316e840f953b4e393`).
- **Educational Textbooks**: Covered (`source.public_textbooks.00cebc897bb7feab776c42a8`).
- **Operator-Excluded Residual Strata**: Explicitly tracked as residuals (`stem_technical`, `video_captions`, `ocr_scans`, `private_teaching_material`).

### PILOT-3: Pilot Accounting & Invariant Verification
- **Total Selected Spans**: 1,419
- **Admitted Spans**: 1,418
- **Exported Training Spans**: 614
- **Rejected Quarantine Spans**: 1 (upstream layout repetition anomaly quarantined)
- **Abstained Held-out Evaluation Spans**: 559 (firewalled)
- **Abstained Development Spans**: 245 (firewalled)

### PILOT-4: Exact Local Reproduction
- Deterministic builds reproduce the exact cryptographic digests:
  - `manifest_sha256`: `eab18e358266836f81c9791d3eb2a371f0d1fa88d360056a7d31429263efa8f3`
  - `split_receipt_sha256`: `dc52361567488837e41db9c79c79c78604fe80ee7463c31d256c9de73b1c07b0`
  - `records_sha256`: `98e722ff3f9cf9db2283b2b660bb805a5971f761bf488d09304402f201d9e265`
  - `receipt_id`: `receipt.pilot.702e1b404da41ffda2824da5`

### PILOT-5: Next Work Hand-off
- **Independent Evaluation & Quality Assessment**: Tracked in **#7431**.
- **Full Denominator Dataset Construction**: Tracked in **#7432**.
