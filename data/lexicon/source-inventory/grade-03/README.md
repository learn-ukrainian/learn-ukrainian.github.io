# Grade-3 textbook glossaries (#7551)

Per-book domain/headword glossaries re-extracted from local
`data/textbook_chunks/grade-03/*.jsonl` — **not** the oneshot function-word
mine (`data/lexicon/source-inventory/oneshot/textbook-jsonl-curated-2026-07-19-bulk.yaml`,
explicitly excluded per #7551) and not a Grade-3-wide single dump. Books
processed:

| Book | Subject | JSONL | Skip reason |
| --- | --- | --- | --- |
| Морзе Н. В., Барна О. В., «Я досліджую світ» (Інформатика. Дизайн і технології), підручник для 3 класу ЗЗСО (у 2-х частинах), частина 2, 2025 | informatyka | `3-klas-informatyka-morze-2025.jsonl` | — |
| Листопад Н. П., «Математика», підруч. для 3 кл. ЗЗСО (у 2-х частинах), 2020 (2 parts) | matematyka | `3-klas-matematyka-lystopad-2020-{1,2}.jsonl` | — |
| Аристова Л. С., Фролова-Чередняк К. О., «Мистецтво», підручник інтегрованого курсу для 3 класу ЗЗСО, 2025 | mystetstvo | `3-klas-mystetstvo-arystova-2025.jsonl` | — |
| Савченко О. Я., «Українська мова та читання», підручник для 3 класу ЗЗСО (у 2-х частинах), частина 2, 2020 | ukrmova | `3-klas-ukrainska-mova-savchenko-2020-2.jsonl` (частина 1 not on disk) | — |
| Жаркова І. В., Мечник Л. А., Роговська Л. І., Пономарьова Л. А., Антонов О. В., «Я досліджую світ», підручник для 3 класу ЗЗСО (у 2-х частинах), 2020 (2 parts) | ya-doslidzhuiu-svit | `3-klas-ya-doslidzhuiu-svit-zharkova-2020-{1,2}.jsonl` | — |
| Карпюк О. Д., «Англійська мова», 2020 | — | `3-klas-angliiska-mova-karpiuk-2020.jsonl` | English textbook, not a UK-headword source |

## Pipeline

Same two-stage pipeline as grade 1/2 (`data/lexicon/source-inventory/grade-01/README.md`,
`data/lexicon/source-inventory/grade-02/README.md`), scripts unchanged:

1. **`scripts/lexicon/extract_textbook_chunk_headword_inventory.py`** — tokenizes
   each book's chunk text and batch-verifies every unique form against local
   VESUM (`data/vesum.db`, `scripts.verification.vesum.verify_words`). Output:
   `*-headwords.yaml` — every VESUM-attested (lemma, pos) with occurrence
   count and page locators, still an unfiltered candidate pool (no gloss, no
   admission decision).
2. **`scripts/lexicon/admit_textbook_book_glossary.py`** — admits a candidate
   from this round's capped attempt list only when **both** gates clear with
   a real, cited source (invents nothing):
   - a public Ukrainian definition from **СУМ-20** (`newsum`) or **ВТС**
     (`vts`) — never СУМ-11;
   - a learner English gloss from **dmklinger** (UK→EN, Wiktionary-derived),
     falling back to slovnyk.me's **ukreng**.

   The capped attempt list (top 300 by frequency, content words only —
   conj/prep/pron/part/intj POS, ambiguous forms, and proper-noun candidates
   dropped before ranking) was derived from each book's `*-headwords.yaml`
   with the same selection rule as grade 1/2; the derivation itself is a
   throwaway step (no new committed script), matching the grade-1/2
   precedent of a `/tmp` candidate file per book.

   Both dictionary lookups reuse the shared cache
   `data/lexicon/slovnyk_cache/<lemma>.json` (schema v4, tens of thousands of
   files already built by the grade-1/2 passes), so this run's slovnyk.me
   fetches were mostly cache hits.

## Counts (this run)

| Book | VESUM content candidates | Attempted (top 300 by freq) | Admitted | Richness | Residual (not yet attempted) |
| --- | ---: | ---: | ---: | ---: | ---: |
| informatyka-morze | 1,703 | 300 | 263 | 87.7% | 1,403 |
| matematyka-lystopad | 1,484 | 300 | 266 | 88.7% | 1,184 |
| mystetstvo-arystova | 1,589 | 300 | 280 | 93.3% | 1,289 |
| ukrmova-savchenko | 3,052 | 300 | 282 | 94.0% | 2,752 |
| ya-doslidzhuiu-svit-zharkova | 3,107 | 300 | 276 | 92.0% | 2,807 |
| **Total** | **10,935** | **1,500** | **1,367** | **91.1%** | **9,435** |

Richness floor for this program is 40% (`--allow-richness-regression` not
used, not needed). "Residual (not yet attempted)" is real, VESUM-verified
vocabulary outside this round's per-book frequency cap — a further pass over
the same `*-headwords.yaml` files can raise the cap and re-run
`admit_textbook_book_glossary.py`; the slovnyk cache already built means that
pass is mostly free. "Residual (this batch)" — an attempted candidate that
failed one or both gates — is recorded per book in the `residual:` block of
its glossary YAML with the specific reason(s) (`no_uk_definition` /
`no_en_gloss`).

## What this is not

- Not the Atlas manifest. Nothing here has been promoted into
  `site/src/data/lexicon-manifest.json`; that is a separate, explicitly
  authorized publish step (`scripts/lexicon/publish_manifest.py`) out of
  scope for this pass.
- Not a re-run or extension of the 2026-07-19 oneshot bulk mine.
- Not grade 4+. Next grade in the #7551 queue is grade 4.
