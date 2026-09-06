# Grade-6 textbook glossaries (#7551)

Per-book domain/headword glossaries re-extracted from local
`data/textbook_chunks/grade-06/*.jsonl` — **not** the oneshot function-word
mine (`data/lexicon/source-inventory/oneshot/textbook-jsonl-curated-2026-07-19-bulk.yaml`,
explicitly excluded per #7551) and not a Grade-6-wide single dump. All 15
Ukrainian-language grade-6 textbooks are processed, each with its own
glossary; the English-language textbook is skipped (not a UK-headword
source). The two `istoriya`/`istoriia` books (Щупак, Гісем) are separate
books with separate authors covering the same subject, as are the three
`ukrmova` textbooks (Авраменко, Голуб, Літвінова). Books processed:

| Book | Subject | JSONL | Skip reason |
| --- | --- | --- | --- |
| Мартинюк О. О., Гісем О. В., «Етика», підручник (проєкт майбутнього підручника) для 6 класу ЗЗСО, Видавництво «Ранок», 2023 | etyka | `6-klas-etyka-martyniuk-2023.jsonl` | — |
| Запотоцький С. П., Зінкевич М. О., Романишин О. Я., Титар Н. М., Горовий О. В., Миколів І. М., «Географія», підручник для 6 класу ЗЗСО, Тернопіль: Астон, 2023 | heohrafiya | `6-klas-heohrafiya-zapotockyi-2023.jsonl` | — |
| Бондаренко О. О., Ластовецький В. В., Пилипчук О. П., Шестопалов Є. А., «Інформатика», підручник (проєкт підручника) для 6 класу ЗЗСО, Видавництво «Ранок», 2023 | informatyka | `6-klas-informatyka-bondarenko-2023.jsonl` | — |
| Щупак І. Я., Бурлака О. В., Власова Н., Піскарьова І. О., «Історія України. Всесвітня історія», підручник для 6 класу ЗЗСО, Український освітянський видавничий центр «Оріон», 2023 | istoriya | `6-klas-istoriia-shchupak-2023.jsonl` | — |
| Гісем О. О., Гісем О. В., «Історія України. Всесвітня історія», підручник для 6 класу ЗЗСО, Видавництво «Ранок», 2023 | istoriya | `6-klas-istoriya-gisem-2023.jsonl` | — |
| Тарасенкова Н. А., Богатирьова І. М., Коломієць О. М., Сердюк З. О., Рудніцька Ю., «Математика», підручник для 6 класу ЗЗСО (у 2-х частинах), Український освітянський видавничий центр «Оріон», Київ, 2023 | matematyka | `6-klas-matematyka-tarasenkova-2023-1.jsonl` + `-2.jsonl` | — |
| Рубля Т. Є., Щеглова Т. Л., Мед І. Л., «Мистецтво», підручник (проєкт майбутнього підручника) інтегрованого курсу для 6 класу ЗЗСО, Видавництво «Ранок», 2023 | mystetstvo | `6-klas-mystetstvo-rublia-2023.jsonl` | — |
| Коршевнюк Т. В., Ярошенко О. Г., «Пізнаємо природу», підручник інтегрованого курсу для 6 класу ЗЗСО, Київ, 2023 | pryroda | `6-klas-piznaemo-pryrodu-korshevniuk-2023.jsonl` | — |
| Біленко О. В., Пелагейченко М. Л., «Технології», підручник для 6 класу ЗЗСО, Тернопіль: Астон, 2023 | tekhnolohiyi | `6-klas-tekhnolohiyi-bilenko-2023.jsonl` | — |
| Авраменко О. М., «Українська література», підручник для 6 класу ЗЗСО, Київ: «Грамота», 2023 | ukrlit | `6-klas-ukrlit-avramenko-2023.jsonl` | — |
| Авраменко О. М., Тищенко З., «Українська мова», підручник для 6 класу ЗЗСО, 2023 | ukrmova | `6-klas-ukrmova-avramenko-2023.jsonl` | — |
| Голуб Н. Б., Горошкіна О. М., «Українська мова», підручник для 6 класу ЗЗСО, Київ: Видавничий дім «Освіта», 2023 | ukrmova | `6-klas-ukrmova-golub-2023.jsonl` | — |
| Літвінова І. М., «Українська мова», підручник для 6 класу ЗЗСО, 2023 | ukrmova | `6-klas-ukrmova-litvinova-2023.jsonl` | — |
| Волощук Є. М., Слободянюк О., «Зарубіжна література», підручник для 6 класу ЗЗСО, Київ: ТОВ «Генеза», 2023 | zarubizhna-literatura | `6-klas-zarubizhna-literatura-voloshchuk-2023.jsonl` | — |
| Воронцова Т. В., Пономаренко В. С., Лаврентьєва І. В., Хомич О. Л., Андрук Н., «Здоров'я, безпека та добробут», підручник інтегрованого курсу для 6 класу ЗЗСО, Київ: Видавництво «Алатон», 2023 | zdorovia | `6-klas-zdorovia-vorontsova-2023.jsonl` | — |
| Пахомова Т. Г., «Англійська мова», підручник для 6 класу ЗЗСО, 2023 | foreign_language | `6-klas-angliiska-mova-pakhomova-2023.jsonl` | English textbook, not a UK-headword source |

Author names and titles are verified against the front-matter/title-page
text captured in each book's own JSONL chunks (author bylines, cover
titles, and — where present — the full library citation block with ISBN).
Every book's byline was found directly in its own chunk text except
`informatyka-bondarenko`, whose captured pages start after the title page
(no author byline in the OCR'd chunks); for that one book the four-author
byline was confirmed against public catalog entries (pidruchnyk.com.ua,
rule.school) for the same subject/grade/publisher/year already attested
locally (subject `informatyka`, "Проєкт підручника", Видавництво «Ранок»,
2023). Nothing here is invented.

## Pipeline

Same two-stage pipeline as grade 1–5 (`data/lexicon/source-inventory/grade-01/README.md`
… `.../grade-05/README.md`), scripts unchanged:

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
   with the same selection rule as grade 1–5; the derivation itself is a
   throwaway step (no new committed script), matching precedent.

   Both dictionary lookups reuse the shared cache
   `data/lexicon/slovnyk_cache/<lemma>.json` (schema v4, tens of thousands of
   files already built by the grade-1..5 passes), so this run's slovnyk.me
   fetches were mostly cache hits.

## Counts (this run)

| Book | VESUM content candidates | Attempted (top 300 by freq) | Admitted | Richness | Residual (not yet attempted) |
| --- | ---: | ---: | ---: | ---: | ---: |
| etyka-martyniuk | 2,410 | 300 | 279 | 93.0% | 2,110 |
| heohrafiya-zapotockyi | 4,192 | 300 | 276 | 92.0% | 3,892 |
| informatyka-bondarenko | 2,021 | 300 | 272 | 90.7% | 1,721 |
| istoriia-shchupak | 4,142 | 300 | 264 | 88.0% | 3,842 |
| istoriya-gisem | 3,777 | 300 | 283 | 94.3% | 3,477 |
| matematyka-tarasenkova | 1,521 | 300 | 264 | 88.0% | 1,221 |
| mystetstvo-rublia | 2,688 | 300 | 277 | 92.3% | 2,388 |
| piznaemo-pryrodu-korshevniuk | 3,322 | 300 | 274 | 91.3% | 3,022 |
| tekhnolohiyi-bilenko | 3,917 | 300 | 267 | 89.0% | 3,617 |
| ukrlit-avramenko | 6,723 | 300 | 283 | 94.3% | 6,423 |
| ukrmova-avramenko | 6,174 | 300 | 277 | 92.3% | 5,874 |
| ukrmova-golub | 5,718 | 300 | 282 | 94.0% | 5,418 |
| ukrmova-litvinova | 4,669 | 300 | 276 | 92.0% | 4,369 |
| zarubizhna-literatura-voloshchuk | 7,141 | 300 | 286 | 95.3% | 6,841 |
| zdorovia-vorontsova | 2,344 | 300 | 279 | 93.0% | 2,044 |
| **Total** | **60,759** | **4,500** | **4,139** | **92.0%** | **56,259** |

Richness floor for this program is 40% (`--allow-richness-regression` not
used, not needed — every book cleared 88%+). "Residual (not yet attempted)"
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
- Not grade 7+. Next grade in the #7551 queue is grade 7.
