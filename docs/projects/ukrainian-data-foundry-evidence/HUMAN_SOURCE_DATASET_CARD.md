# Dataset Card: Ukrainian Human-Source Learning Collection (v4.0.0-human-pilot-scale)

## Dataset Summary

The Ukrainian Human-Source Learning Collection (`v4.0.0-human-pilot-scale`) is a verified, private human-authored Ukrainian text dataset compiled under epic **#7423** to teach open-weight foundation language models authentic Ukrainian language representations. The dataset is constructed exclusively from human-authored literary prose and educational textbooks, with zero synthetic AI text and zero OCR distortion.

Under operator guidance (2026-09-10):

- Non-commercial, permanent open-source educational mission.
- Private learning collection; zero corpus text and zero private host paths are emitted into public receipts.
- 100% verbatim textual fidelity; authentic dialectal, historical, and literary registers are preserved without modernization.
- Clean work family partition firewalling to prevent data leakage into held-out evaluation benchmarks.

---

## Dataset Structure

### Data Instances

Each record in `v4_human_source_dataset_records_v1.jsonl` contains:

- `record_id`: Deterministic unique identifier (`record.human.<hash>`).
- `provenance`: Author, publication year, genre/domain, historical period, and canonical reference links.
- `source_fidelity`: Verified character length, cryptographic span hash, native text attestation, and verbatim preservation invariant.
- `language_views`:
  - `primary_role`: Linguistic register classification (`modern_standard`, `literary_register`, `historical_period`, `quoted_metalinguistic`, etc.).
  - `faithful_view`: Training clearance for unmasked causal language modeling.
  - `modern_view`: Loss masking intervals for foreign or non-standard quoted occurrences.
- `split_clearance`: Partition assignment (`training`, `development`, `heldout_evaluation`, `quarantine_excluded`) and firewall verification.
- `admission_evidence`: Rights basis and local learning approval confirmation.

### Data Splits

| Partition | Spans | Records % | Primary Purpose |
| --- | --- | --- | --- |
| `training` | 614 | 43.3% | Builder model continual adaptation |
| `heldout_evaluation` | 559 | 39.4% | Strict firewalled evaluation & perplexity assessment |
| `development` | 245 | 17.3% | Hyperparameter tuning and validation |
| `quarantine_excluded` | 1 | 0.07% | Quarantined upstream anomaly (zero training exposure) |

---

## Source Selection & Curation

### Included Strata

1. **Literary Prose**: Verified modern and 20th-century Ukrainian literary works (e.g. Yuriy Andrukhovych's *Moskoviada*, Mykhailo Hrushevskyy's historical scholarship).
2. **Educational Textbooks**: Modern Ukrainian state-curated textbooks (e.g. Masol *Mystetstvo Grade 9*).

### Excluded Residual Strata

- STEM technical and exact sciences (quarantined under #7432).
- Video captions and speech transcripts (transcription noise).
- OCR-derived unverified scans (quarantined under #7885).
- Private teaching material without explicit local clearance.

---

## Licensing & Governance

- Built under local learning rights for educational research.
- Retained within secure local custody; raw texts are not redistributed publicly.
