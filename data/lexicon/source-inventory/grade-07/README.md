# Grade-7 textbook glossaries (#7551)

Per-book domain/headword glossaries re-extracted from local
`data/textbook_chunks/grade-07/*.jsonl` — **not** the oneshot function-word
mine (`data/lexicon/source-inventory/oneshot/textbook-jsonl-curated-2026-07-19-bulk.yaml`,
explicitly excluded per #7551) and not a Grade-7-wide single dump. All 16
Ukrainian-language grade-7 textbooks are processed, each with its own
glossary; the English-language textbook (Коста) is skipped (not a UK-headword
source). `ukrlit-avramenko` and `ukrlit-zabolotnyi` are separate books with
separate authors covering the same subject, as are `istoria-ukr-hlibovska`
and `istoriya-shchupak`. STEM books (algebra, geometry, physics, chemistry,
biology, informatics) are in scope for this pass. Books processed:

| Book | Subject | JSONL | Skip reason |
| --- | --- | --- | --- |
| Мерзляк А. Г., Якір М. С., «Алгебра», підручник для 7 класу ЗЗСО, Харків: «Гімназія», 2024 | algebra | `7-klas-algebra-merzliak-2024.jsonl` | — |
| Соболь В. І., «Біологія», підручник для 7 класу ЗЗСО, Кам'янець-Подільський: Видавництво «Абетка», 2024 | biolohiya | `7-klas-biolohiya-sobol-2024.jsonl` | — |
| Бар'яхтар В. Г., Божинова Ф. Я., Довгий С. О., Кірюхін М. М., Кірюхіна О. О., «Фізика», підручник для 7 класу ЗЗСО, за редакцією Довгого С. О., Київ-Харків: Видавництво «Ранок», 2024 | fizyka | `7-klas-fizyka-bariakhtar-2024.jsonl` | — |
| Довгань Г. Д., «Географія», підручник для 7 класу ЗЗСО, Харків: Видавництво «Ранок», 2024 | heohrafiya | `7-klas-heohrafiya-dovhan-2024.jsonl` | — |
| Мерзляк А. Г., Якір М. С., «Геометрія», підручник для 7 класу ЗЗСО, Харків: «Гімназія», 2024 | heometriya | `7-klas-heometriya-merzliak-2024.jsonl` | — |
| Бондаренко О. О., Ластовецький В. В., Пилипчук О. П., Шестопалов Є. А., «Інформатика», підручник для 7 класу ЗЗСО, Харків: Видавництво «Ранок», 2024 | informatyka | `7-klas-informatyka-bondarenko-2024.jsonl` | — |
| Хлібовська Г. М., Крижановська М. Є., Наумчук О. В., «Історія України», підручник для 7 класу ЗЗСО, Тернопіль: Астон, 2024 | istoriya | `7-klas-istoria-ukr-hlibovska-2024.jsonl` | — |
| Щупак І. Я., Секиринський Д. О., Власова Н. С., Кронгауз В. О., «Історія: Україна і світ», підручник інтегрованого курсу для 7 класу ЗЗСО, 2024 | istoriya | `7-klas-istoriya-shchupak-2024-full.jsonl` | — |
| Григорович О. В., Недоруб О. Ю., «Хімія», підручник для 7 класу ЗЗСО, Харків: Видавництво «Ранок», 2024 | khimiya | `7-klas-khimiya-hryhorovych-2024.jsonl` | — |
| Масол Л. М., Калініченко О. В., «Мистецтво», підручник інтегрованого курсу для 7 класу ЗЗСО, Київ: Видавничий дім «Освіта», 2024 | mystetstvo | `7-klas-mystetstvo-masol-2024.jsonl` | — |
| Біленко О. В., Пелагейченко М. Л., «Технології», підручник для 7 класу ЗЗСО, Тернопіль: Астон, 2024 | tekhnolohiyi | `7-klas-tekhnolohiyi-bilenko-2024.jsonl` | — |
| Авраменко О. М., «Українська література», підручник для 7 класу ЗЗСО, 2024 | ukrlit | `7-klas-ukrlit-avramenko-2024.jsonl` | — |
| Заболотний В. В., Заболотний О. В., Слоньовська О. В., Ярмульська І. В., «Українська література», підручник для 7 класу ЗЗСО, Київ: «Літера ЛТД», 2024 | ukrlit | `7-klas-ukrlit-zabolotnyi-2024.jsonl` | — |
| Авраменко О. М., Тищенко З., «Українська мова», підручник для 7 класу ЗЗСО, 2024 | ukrmova | `7-klas-ukrmova-avramenko-2024.jsonl` | — |
| Ніколенко О. М., Мацевко-Бекерська Л. В., Рудніцька Н. П., Ковальова Л. Л., Туряниця В. Г., Базильська Н. М., Гвоздікова О. В., Лебедь Д. О., «Зарубіжна література», підручник для 7 класу ЗЗСО, Київ: ВЦ «Академія», 2024 | zarubizhna-literatura | `7-klas-zarlit-nikolenko-2024.jsonl` | — |
| Гущина Н. І., Василашко І. П., за редакцією Бойченко Т. Є., «Здоров'я, безпека та добробут», підручник інтегрованого курсу для 7 класу ЗЗСО, Київ: Видавничий дім «Освіта», 2024 | zdorovia | `7-klas-zdorovia-guschyna-2024.jsonl` | — |
| Коста О. С. та ін., «Англійська мова», підручник для 7 класу ЗЗСО, 2024 | foreign_language | `7-klas-angliiska-mova-kosta-2024.jsonl` | English textbook, not a UK-headword source |

`istoriya-shchupak-grade7-2024-headwords.yaml` is split into `-headwords-1.yaml`
and `-headwords-2.yaml` (11,186 headwords split in half by extraction order,
`unknown_forms` kept with part 2) — the unsplit file was 2,946,101 bytes,
over this repo's `check-added-large-files` pre-commit limit (2,048,000
bytes/2000 KB) because the source book is the largest in this grade's queue
(589 pages, 112,754 tokens, `-full` JSONL). No data was dropped or altered;
this is a storage split only, and it does not affect the already-completed
admission run (the glossary was built from the single unsplit inventory
before the split).

Author names and titles are verified against the front-matter/title-page and
colophon (`Навчальне видання` imprint block) text captured in each book's own
JSONL chunks (`data/textbook_chunks/grade-07/*.jsonl`) — full author bylines
with patronymics were found directly in-chunk for every book, including the
four for which `data/sources.db`'s `textbooks` table has no rows
(`biolohiya-sobol`, `heohrafiya-dovhan`, `informatyka-bondarenko`,
`zarlit-nikolenko`; those chunk files were read directly). Nothing here is
invented.

## Pipeline

Same two-stage pipeline as grade 1–6 (`data/lexicon/source-inventory/grade-01/README.md`
… `.../grade-06/README.md`), scripts unchanged:

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
   with the same selection rule as grade 1–6; the derivation itself is a
   throwaway step (no new committed script), matching precedent.

   Both dictionary lookups reuse the shared cache
   `data/lexicon/slovnyk_cache/<lemma>.json` (schema v4, tens of thousands of
   files already built by the grade-1..6 passes), so this run's slovnyk.me
   fetches were mostly cache hits.

## Counts (this run)

| Book | VESUM content candidates | Attempted (top 300 by freq) | Admitted | Richness | Residual (not yet attempted) |
| --- | ---: | ---: | ---: | ---: | ---: |
| algebra-merzliak | 1,891 | 300 | 258 | 86.0% | 1,591 |
| biolohiya-sobol | 5,395 | 300 | 271 | 90.3% | 5,095 |
| fizyka-bariakhtar | 2,896 | 300 | 256 | 85.3% | 2,596 |
| heohrafiya-dovhan | 3,624 | 300 | 274 | 91.3% | 3,324 |
| heometriya-merzliak | 1,558 | 300 | 258 | 86.0% | 1,258 |
| informatyka-bondarenko | 2,297 | 300 | 264 | 88.0% | 1,997 |
| istoria-ukr-hlibovska | 4,119 | 300 | 268 | 89.3% | 3,819 |
| istoriya-shchupak | 6,954 | 300 | 279 | 93.0% | 6,654 |
| khimiya-hryhorovych | 2,276 | 300 | 264 | 88.0% | 1,976 |
| mystetstvo-masol | 4,309 | 300 | 274 | 91.3% | 4,009 |
| tekhnolohiyi-bilenko | 3,009 | 300 | 266 | 88.7% | 2,709 |
| ukrlit-avramenko | 7,695 | 300 | 285 | 95.0% | 7,395 |
| ukrlit-zabolotnyi | 7,662 | 300 | 293 | 97.7% | 7,362 |
| ukrmova-avramenko | 6,114 | 300 | 273 | 91.0% | 5,814 |
| zarlit-nikolenko | 6,031 | 300 | 285 | 95.0% | 5,731 |
| zdorovia-guschyna | 4,139 | 300 | 287 | 95.7% | 3,839 |
| **Total** | **69,969** | **4,800** | **4,355** | **90.7%** | **65,169** |

Richness floor for this program is 40% (`--allow-richness-regression` not
used, not needed — every book cleared 85%+). "Residual (not yet attempted)"
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
- Not grade 8+. Next grade in the #7551 queue is grade 8.
