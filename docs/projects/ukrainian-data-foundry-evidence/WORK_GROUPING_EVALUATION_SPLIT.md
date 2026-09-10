# Work Grouping & Evaluation Split Clearance Evidence (Issue #7887)

## Purpose & Scope
This document records the architecture, contracts, and empirical verification for grouping related source works and enforcing cryptographic train-development-evaluation leakage firewalls, resolving blocker **#7887** for the private human-source Ukrainian dataset epic (**#7423**).

Under operator guidance (2026-09-10):
- Related works, editions, chapters, volumes, and textbook pages are grouped into monolithic **work families** before partition assignment (**SPLIT-1**).
- Exact and near duplicate spans across chunks/editions and prohibited benchmark/exam inputs are screened and excluded from training (**SPLIT-2**).
- Builders receive clean, unambiguous boolean training clearance without exposing held-out evaluation identities, test questions, or benchmark texts (**SPLIT-3**).
- Zero work families cross the training/development/evaluation boundaries; record-ID modulo splitting is strictly prohibited (**SPLIT-4**).
- Zero raw corpus text and zero private host paths are emitted into public receipts or metadata.

---

## Contract Schemas
All split data structures conform to Draft 2020-12 JSON Schemas in `data/projects/open_model_data/contracts/`:
1. `v4_work_grouping_split_config_v1.schema.json`: Configuration specifying grouping levels, target split fractions, and firewall invariants.
2. `v4_work_grouping_split_item_v1.schema.json`: Per-span work family linkages, deduplication records, benchmark screening, and builder clearance flags.
3. `v4_work_grouping_split_receipt_v1.schema.json`: Deterministic cryptographic verification receipt.

---

## Work Families & Boundary Firewalls (SPLIT-1 & SPLIT-4)
Partitioning is strictly enforced at the **work family** level, not at the record or chunk level. Chunks of the same literary novel or pages of the same educational textbook remain co-located within the same split:
- `work_family.literary.hrushevskyy_istoriya_ukrayiny_odnotomnyk` (559 spans) -> `heldout_evaluation`
- `work_family.public_textbooks.masol_mystetstvo_grade_9` (245 spans) -> `development`
- `work_family.literary.yuriy_andrukhovych_moskoviada` (614 spans training, 1 span quarantine excluded) -> `training`

**Firewall Verification**:
- Intersection between Training and Development: 0 work families.
- Intersection between Training and Held-out Evaluation: 0 work families.
- Intersection between Development and Held-out Evaluation: 0 work families.
- Cross-boundary leakage: 0 detected.

---

## Deduplication & Benchmark Screening (SPLIT-2)
- Deduplication tracks exact cryptographic hashes of source spans (`span_sha256`). Any redundant copies across editions or overlapping chunks are flagged as `is_duplicate: true` and excluded from training.
- Evaluation screening verifies that no exam questions, evaluation benchmarks, or excluded test sets enter training sets (`screen_benchmarks_and_exams: true`).

---

## Builder-Safe Clearance (SPLIT-3)
Builders query `builder_clearance.builder_training_cleared` directly. This boolean flag abstracts the evaluation firewall and held-out custody partitions, providing builders with guaranteed safe inputs without requiring them to access or browse held-out evaluation material.

---

## Execution Summary
- Evaluated Spans: 1,419
- Total Work Families: 3
- Work Families by Split: Training (1), Development (1), Held-out Evaluation (1)
- Spans by Split:
  - Training: 614
  - Development: 245
  - Held-out Evaluation: 559
  - Quarantine Excluded: 1
- Cleared Training Spans: 614
- Firewalled Evaluation Spans: 559
- Cross-Boundary Leaks: 0
- Firewall Verdict: `WORK_GROUPING_SPLIT_CONFIRMED`
- Receipt ID: `receipt.split.04dfbbaf8da1a6c50b1367e8`
