# Language Usage Separation & Consumer View Masking Evidence (Issue #7886)

## Purpose & Scope
This document records the design, implementation, and empirical verification for separating modern standard learning usage from legitimate historical period variation, literary registers, and quoted/foreign citations, resolving blocker **#7886** for the private human-source Ukrainian dataset epic (**#7423**).

Under operator guidance (2026-09-10):
- Verbatim text is strictly preserved; historical, regional, and literary spellings/forms are never artificially modernized or mutated (**LANG-3**).
- Non-target registers, historical forms, and citations are isolated with deterministic token-level/character-level loss masks for modern training views while remaining completely intact in the faithful source view (**LANG-2**).
- Zero raw corpus text and zero private host paths are emitted into public receipts or metadata.

---

## Contract Schemas
All data structures conform to Draft 2020-12 JSON Schemas in `data/projects/open_model_data/contracts/`:
1. `v4_language_usage_config_v1.schema.json`: Configuration for separation rules and source receipts.
2. `v4_language_usage_item_v1.schema.json`: Per-span functional role annotations and dual-view loss masks (`faithful_view` and `modern_view`).
3. `v4_language_usage_receipt_v1.schema.json`: Deterministic cryptographic verification receipt.

---

## Language Roles & Separation Rules (LANG-1 & LANG-2)
Each span evaluated from upstream native extraction index (`v4_native_extraction_index_v1.jsonl`) is analyzed deterministically:
1. **Functional Roles**:
   - `modern_standard`: Contemporary educational and non-fiction texts (e.g. textbook prose).
   - `literary_register`: Authentic Ukrainian literary expressions, idioms, and non-standard figurative language.
   - `historical_period`: Texts or passages prior to contemporary standard codifications or exhibiting pre-modern orthography (e.g. Ѣ/ѣ, Ъ/ъ, Ѳ/ѳ).
   - `quoted_metalinguistic`: Embedded citations, dialogue, or grammar example quotes (delimited by `«...»`, `“...”`, `"...` or dashes).
   - `foreign_citation`: Latin/non-Cyrillic scripts or citations within Ukrainian text.
   - `damaged_or_excluded`: Damaged or quarantined spans from upstream extraction.
2. **Dual-View Masking**:
   - **`faithful_view`**: Preserves full source text and eligibility for language modeling and cultural heritage evaluation (training eligible for all undamaged spans; zero masks).
   - **`modern_view`**: Designed for modern standard Ukrainian instruction. Historical period text is marked `training_eligible: false`. Quotations and foreign citations inside modern texts receive character-offset `loss_mask_spans`, preventing non-target idioms or foreign vocabulary from polluting modern production loss.

---

## Verification & Linguistic Quality (LANG-3 & LANG-4)
- **Verbatim Invariant**: Verified across all 1,419 spans (`verbatim_preserved: true`).
- **VESUM Non-Punitive Policy**: Unattested archaic, dialectal, or literary words are treated as valid Ukrainian cultural heritage and are not flagged as errors.
- **Leakage Firewall**: Zero corpus text or private host paths exist in public artifacts.

---

## Execution Summary
- Evaluated Spans: 1,419
- Faithful Training Eligible: 1,418 (1 quarantined upstream excluded)
- Modern Training Eligible: 1,418
- Masked Spans Count: 288 (quotations and foreign citations masked for modern training view)
- Receipt ID: `receipt.language.13f75785dc25f46798a4717d`
- Verdict: `LANGUAGE_USAGE_SEPARATION_CONFIRMED`
