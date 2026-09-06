# Grade-4 textbook glossaries (#7551)

Per-book domain/headword glossaries re-extracted from local
`data/textbook_chunks/grade-04/*.jsonl` — **not** the oneshot function-word
mine (`data/lexicon/source-inventory/oneshot/textbook-jsonl-curated-2026-07-19-bulk.yaml`,
explicitly excluded per #7551) and not a Grade-4-wide single dump. The four
`ukrmova` textbooks (Kravtsova, Ponomarova, Savchenko, Zaharijchuk) are
treated as separate books, each with its own glossary. Books processed:

| Book | Subject | JSONL | Skip reason |
| --- | --- | --- | --- |
| Воронцова, Пономаренко, Хомич, Лаврентьєва, «Інформатика», підручник для 4 класу ЗЗСО (НУШ), 2021 | informatyka | `4-klas-informatyka-vorontsova-2021.jsonl` | — |
| Істер, «Математика», підручник для 4 класу ЗЗСО (у 2-х частинах), 2021 (2 parts) | matematyka | `4-klas-matematyka-ister-2021-{1,2}.jsonl` | — |
| Рубля, Мед, Щеглова, «Мистецтво», підручник для 4 класу ЗЗСО (НУШ), 2021 | mystetstvo | `4-klas-mystetstvo-rublia-2021.jsonl` | — |
| Кравцова Н. М., «Українська мова», 4 клас, частина 1, «Підручники і посібники», 2021 | ukrmova | `4-klas-ukrayinska-mova-kravtsova-2021-1.jsonl` (частина 2 not on disk) | — |
| Пономарьова, Гайова, «Українська мова та читання», підручник для 4 класу ЗЗСО, частина 1, 2021 | ukrmova | `4-klas-ukrayinska-mova-ponomarova-2021-1.jsonl` (частина 2 not on disk) | — |
| Савченко О. Я., «Українська мова та читання», 4 клас, частина 2, «Освіта», 2021 | ukrmova | `4-klas-ukrayinska-mova-savchenko-2021-2.jsonl` (частина 1 not on disk) | — |
| Захарійчук, Мовчун, «Українська мова та читання», підручник для 4 класу ЗЗСО, частина 1, 2021 | ukrmova | `4-klas-ukrayinska-mova-zaharijchuk-2021-1.jsonl` (частина 2 not on disk) | — |
| Жаркова, Мечник, Роговська, «Я досліджую світ», підручник для 4 класу ЗЗСО (у 2-х частинах), 2021 (2 parts) | ya-doslidzhuiu-svit | `4-klas-ya-doslidzhuiu-svit-zharkova-2021-{1,2}.jsonl` | — |
| Губарєва, «Англійська мова», 2021 | — | `4-klas-angliiska-mova-hubarieva-2021.jsonl` | English textbook, not a UK-headword source |

Author surnames are sourced from `data/sources.db` (`textbooks.author_uk`)
and cross-checked against the pidruchnyk.com.ua catalog pages linked from
`docs/l2-uk-direct/textbook-selection.yaml`; those pages do not print
author initials, so none are invented here (Kravtsova and Savchenko carry
full initials because those two citations are already recorded verbatim in
`docs/l2-uk-direct/textbook-reading-notes/grade-4-kravtsova-savchenko-2021.md`).

## Pipeline

Same two-stage pipeline as grade 1/2/3 (`data/lexicon/source-inventory/grade-01/README.md`,
`.../grade-02/README.md`, `.../grade-03/README.md`), scripts unchanged:

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
   with the same selection rule as grade 1/2/3; the derivation itself is a
   throwaway step (no new committed script), matching precedent.

   Both dictionary lookups reuse the shared cache
   `data/lexicon/slovnyk_cache/<lemma>.json` (schema v4, tens of thousands of
   files already built by the grade-1/2/3 passes), so this run's slovnyk.me
   fetches were mostly cache hits.

## Counts (this run)

| Book | VESUM content candidates | Attempted (top 300 by freq) | Admitted | Richness | Residual (not yet attempted) |
| --- | ---: | ---: | ---: | ---: | ---: |
| informatyka-vorontsova | 1,350 | 300 | 272 | 90.7% | 1,050 |
| matematyka-ister | 1,326 | 300 | 268 | 89.3% | 1,026 |
| mystetstvo-rublia | 1,751 | 300 | 286 | 95.3% | 1,451 |
| ukrmova-kravtsova | 2,850 | 300 | 280 | 93.3% | 2,550 |
| ukrmova-ponomarova | 2,814 | 300 | 281 | 93.7% | 2,514 |
| ukrmova-savchenko | 3,439 | 300 | 283 | 94.3% | 3,139 |
| ukrmova-zaharijchuk | 2,733 | 300 | 272 | 90.7% | 2,433 |
| ya-doslidzhuiu-svit-zharkova | 3,508 | 300 | 286 | 95.3% | 3,208 |
| **Total** | **19,771** | **2,400** | **2,228** | **92.8%** | **17,371** |

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
- Not grade 5+. Next grade in the #7551 queue is grade 5.
