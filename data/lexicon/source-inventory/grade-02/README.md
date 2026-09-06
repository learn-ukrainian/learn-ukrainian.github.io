# Grade-2 textbook glossaries (#7551)

Per-book domain/headword glossaries re-extracted from local
`data/textbook_chunks/grade-02/*.jsonl` — **not** the oneshot function-word
mine (`data/lexicon/source-inventory/oneshot/textbook-jsonl-curated-2026-07-19-bulk.yaml`,
explicitly excluded per #7551) and not a Grade-2-wide single dump. Books
processed:

| Book | Subject | JSONL | Skip reason |
| --- | --- | --- | --- |
| Істер О. С., «Математика», 2025 | matematyka | `2-klas-matematyka-ister-2025.jsonl` | — |
| Рубля Т. Є., Щеглова Т. Л., Мед І. Л., «Мистецтво», 2024 | mystetstvo | `2-klas-mystetstvo-rublia-2024.jsonl` | — |
| Большакова І. О., Пристінська М. С., «Українська мова та читання», 2019 (2 parts) | ukrmova | `2-klas-ukrmova-bolshakova-2019-{1,2}.jsonl` | — |
| Вашуленко М. С., Дубовик С. Г. (ч. 1) / Вашуленко О. В. (ч. 2), «Українська мова та читання», 2019 (2 parts) | ukrmova | `2-klas-ukrmova-vashulenko-2019-{1,2}.jsonl` | — |
| Грущинська І. В., Хитра З. М., «Я досліджую світ», 2019 (ч. 1) | ya-doslidzhuiu-svit | `2-klas-ya-doslidzhuiu-svit-hrushchynska-2019.jsonl` | — |
| Морзе Н. В., Барна О. В., «Я досліджую світ», 2019 (ч. 2) | ya-doslidzhuiu-svit | `2-klas-ya-doslidzhuiu-svit-morze-2019.jsonl` | — |
| Губарєва С., Павліченко О., Залюбовська Л., «Англійська мова», 2024 | — | `2-klas-angliiska-mova-hubarieva-2024.jsonl` | English textbook, not a UK-headword source |

## Pipeline

Same two-stage pipeline as grade 1 (`data/lexicon/source-inventory/grade-01/README.md`),
scripts unchanged:

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
   with the same selection rule as grade 1; the derivation itself is a
   throwaway step (no new committed script), matching the grade-1 precedent
   of a `/tmp` candidate file per book.

   Both dictionary lookups reuse the shared cache
   `data/lexicon/slovnyk_cache/<lemma>.json` (schema v4, 23k+ files already
   built by the grade-1 pass), so this run's slovnyk.me fetches were mostly
   cache hits.

## Counts (this run)

| Book | VESUM content candidates | Attempted (top 300 by freq) | Admitted | Richness | Residual (not yet attempted) |
| --- | ---: | ---: | ---: | ---: | ---: |
| matematyka-ister | 775 | 300 | 262 | 87.3% | 475 |
| mystetstvo-rublia | 1,227 | 300 | 280 | 93.3% | 927 |
| ukrmova-bolshakova | 2,914 | 300 | 288 | 96.0% | 2,614 |
| ukrmova-vashulenko | 3,322 | 300 | 278 | 92.7% | 3,022 |
| ya-doslidzhuiu-svit-hrushchynska | 2,448 | 300 | 285 | 95.0% | 2,148 |
| ya-doslidzhuiu-svit-morze | 1,476 | 300 | 279 | 93.0% | 1,176 |
| **Total** | **12,162** | **1,800** | **1,672** | **92.9%** | **10,362** |

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
- Not grade 3+. Next grade in the #7551 queue is grade 3.
