# Grade-5 textbook glossaries (#7551)

Per-book domain/headword glossaries re-extracted from local
`data/textbook_chunks/grade-05/*.jsonl` — **not** the oneshot function-word
mine (`data/lexicon/source-inventory/oneshot/textbook-jsonl-curated-2026-07-19-bulk.yaml`,
explicitly excluded per #7551) and not a Grade-5-wide single dump. All 13
Ukrainian-language grade-5 textbooks are processed, each with its own
glossary; the English-language textbook is skipped (not a UK-headword
source). The three `ukrmova` textbooks (Avramenko, Golub, Zabolotnyi) are
separate books with separate authors, as are the two `ukrlit`/`zarlit`
literature textbooks (Ukrainian literature vs. world literature in
Ukrainian — both are Ukrainian-language sources). Books processed:

| Book | Subject | JSONL | Skip reason |
| --- | --- | --- | --- |
| Мелещенко Т., Желіба О., Бакка Т., Ашортіа Н., Козіна Н., «Етика», підручник для 5 класу ЗЗСО (НУШ), 2022 | etyka | `5-klas-etyka-meleshchenko-2022.jsonl` | — |
| Морзе Н. В., Барна О. В., «Інформатика», підручник для 5 класу ЗЗСО (НУШ), 2022 | informatyka | `5-klas-informatyka-morze-2022.jsonl` | — |
| Щупак І. Я., Бурлака О. В., Піскарьова І. О., Посунько А. Л., «Вступ до історії України та громадянської освіти», підручник для 5 класу ЗЗСО (НУШ), 2022 | istoriya | `5-klas-istoriya-schupak-2022.jsonl` | — |
| Істер О. С., «Математика», підручник для 5 класу ЗЗСО (НУШ), 2022 | matematyka | `5-klas-matematyka-ister-2022.jsonl` | — |
| Рубля Т. Є., Мед І. Л., Наземнова Т. О., Щеглова Т. Л., «Мистецтво», підручник для 5 класу ЗЗСО (НУШ), 2022 | mystetstvo | `5-klas-mystetstvo-rublia-2022.jsonl` | — |
| Коршевнюк Т. В., Ярошенко О. Г., «Пізнаємо природу», підручник для 5 класу ЗЗСО (НУШ), 2022 | pryroda | `5-klas-piznaiemo-pryrodu-korshevniuk-2022.jsonl` | — |
| Біленко О. В., Пелагейченко М. Л., «Технології», підручник для 5 класу ЗЗСО (НУШ), 2023 | tekhnolohiyi | `5-klas-tekhnolohiyi-bilenko-2023.jsonl` | — |
| Авраменко О., «Українська література», підручник для 5 класу ЗЗСО, 2022 | ukrlit | `5-klas-ukrlit-avramenko-2022.jsonl` | — |
| Авраменко О., «Українська мова», підручник для 5 класу ЗЗСО, 2022 | ukrmova | `5-klas-ukrmova-avramenko-2022.jsonl` | — |
| Голуб Н. Б., Горошкіна О. М., «Українська мова», підручник для 5 класу ЗЗСО (НУШ), 2022 | ukrmova | `5-klas-ukrmova-golub-2022.jsonl` | — |
| Заболотний О. В., Заболотний В. В., «Українська мова», підручник для 5-го класу ЗЗСО, 2023 | ukrmova | `5-klas-ukrmova-zabolotnyi-2023.jsonl` | — |
| Волощук Є. М., «Зарубіжна література», підручник для 5 класу ЗЗСО, 2022 | zarubizhna-literatura | `5-klas-zarubizhna-literatura-voloshchuk-2022.jsonl` | — |
| Воронцова Т. В., Пономаренко В. С., Лаврентьєва І. В., Хомич О. Л., «Здоров'я, безпека та добробут», підручник інтегрованого курсу для 5 класу ЗЗСО (НУШ), 2022 | zdorovia | `5-klas-zdorovia-vorontsova-2022.jsonl` | — |
| Пахомова Т. Г., «Англійська мова», підручник для 5 класу ЗЗСО, 2022 | foreign_language | `5-klas-angliiska-mova-pakhomova-2022.jsonl` | English textbook, not a UK-headword source |

Author names and titles are verified against the front-matter/title-page
text captured in each book's own JSONL chunks (author bylines, cover
titles, and — where present — the full library citation block), plus
`data/sources.db` (`textbooks.author_uk`, `textbooks.subject`) for the
author-surname/subject cross-check. Where a book's chunked text did not
include its library citation block (`Мелещенко`/etyka, `Щупак`/istoriya,
`Рубля`/mystetstvo, `Біленко`/tekhnolohiyi, `Коршевнюк`/pryroda,
`Воронцова`/zdorovia), the full author list and exact title were confirmed
against publicly listed catalog entries (pidruchnyk.com.ua, znayshov.com)
for the same author/subject/grade/year combination already attested in the
local files; nothing here is invented.

## Pipeline

Same two-stage pipeline as grade 1–4 (`data/lexicon/source-inventory/grade-01/README.md`
… `.../grade-04/README.md`), scripts unchanged:

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
   with the same selection rule as grade 1–4; the derivation itself is a
   throwaway step (no new committed script), matching precedent.

   Both dictionary lookups reuse the shared cache
   `data/lexicon/slovnyk_cache/<lemma>.json` (schema v4, tens of thousands of
   files already built by the grade-1..4 passes), so this run's slovnyk.me
   fetches were mostly cache hits.

## Counts (this run)

| Book | VESUM content candidates | Attempted (top 300 by freq) | Admitted | Richness | Residual (not yet attempted) |
| --- | ---: | ---: | ---: | ---: | ---: |
| etyka-meleshchenko | 3,617 | 300 | 288 | 96.0% | 3,317 |
| informatyka-morze | 2,374 | 300 | 270 | 90.0% | 2,074 |
| istoriya-schupak | 3,218 | 300 | 277 | 92.3% | 2,918 |
| matematyka-ister | 1,330 | 300 | 259 | 86.3% | 1,030 |
| mystetstvo-rublia | 3,013 | 300 | 285 | 95.0% | 2,713 |
| piznaiemo-pryrodu-korshevniuk | 3,365 | 300 | 276 | 92.0% | 3,065 |
| tekhnolohiyi-bilenko | 4,170 | 300 | 265 | 88.3% | 3,870 |
| ukrlit-avramenko | 6,425 | 300 | 286 | 95.3% | 6,125 |
| ukrmova-avramenko | 5,507 | 300 | 277 | 92.3% | 5,207 |
| ukrmova-golub | 5,471 | 300 | 283 | 94.3% | 5,171 |
| ukrmova-zabolotnyi | 4,432 | 300 | 275 | 91.7% | 4,132 |
| zarubizhna-literatura-voloshchuk | 6,147 | 300 | 289 | 96.3% | 5,847 |
| zdorovia-vorontsova | 2,281 | 300 | 275 | 91.7% | 1,981 |
| **Total** | **51,350** | **3,900** | **3,605** | **92.4%** | **47,450** |

Richness floor for this program is 40% (`--allow-richness-regression` not
used, not needed — every book cleared 86%+). "Residual (not yet attempted)"
is real, VESUM-verified vocabulary outside this round's per-book frequency
cap — a further pass over the same `*-headwords.yaml` files can raise the
cap and re-run `admit_textbook_book_glossary.py`; the slovnyk cache already
built means that pass is mostly free. "Residual (this batch)" — an
attempted candidate that failed one or both gates — is recorded per book in
the `residual:` block of its glossary YAML with the specific reason(s)
(`no_uk_definition` / `no_en_gloss`).

## What this is not

- Not the Atlas manifest. Nothing here has been promoted into
  `site/src/data/lexicon-manifest.json`; that is a separate, explicitly
  authorized publish step (`scripts/lexicon/publish_manifest.py`) out of
  scope for this pass.
- Not a re-run or extension of the 2026-07-19 oneshot bulk mine.
- Not grade 6+. Next grade in the #7551 queue is grade 6.
