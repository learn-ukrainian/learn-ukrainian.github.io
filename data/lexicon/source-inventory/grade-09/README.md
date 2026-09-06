# Grade-9 textbook glossaries (#7551)

Per-book domain/headword glossaries re-extracted from local
`data/textbook_chunks/grade-09/*.jsonl` — **not** the oneshot function-word
mine (`data/lexicon/source-inventory/oneshot/textbook-jsonl-curated-2026-07-19-bulk.yaml`,
explicitly excluded per #7551) and not a Grade-9-wide single dump. All 24
grade-9 textbook JSONL sources are processed, each with its own glossary;
there is no English-language textbook in this grade's chunk set to skip
(all 24 are Ukrainian-language textbooks, including зарубіжна література).
Same-subject different authors covering the same subject are treated as separate
books: two algebra (`algebra-merzliak` and `algebra-tarasenkova`), two geometry
(`heometriya-bevz` and `heometriya-merzliak`), two physics (`fizyka-bariakhtar`
and `fizyka-zasiekina`), two chemistry (`khimiya-popel` and `khimiya-yaroshenko`),
two mystetstvo (`mystetstvo-kondratova` and `mystetstvo-masol`), and two ukrlit
(`ukrlit-avramenko` and `ukrlit-zabolotnyi`). STEM, social sciences, humanities,
health, and law books are all in scope. Books processed:

| Book | Subject | JSONL | Skip reason |
| --- | --- | --- | --- |
| Мерзляк А. Г., Полонський В. Б., Якір М. С., «Алгебра», підручник для 9 класу загальноосвітніх навчальних закладів, Харків: «Гімназія», 2017 | algebra | `9-klas-algebra-merzliak-2017.jsonl` | — |
| Тарасенкова Н. А., Акуленко І. А., Данько О. А., Коломієць О. М., Богатирьова І. М., Сердюк З. О., «Алгебра», підручник для 9 класу закладів загальної середньої освіти, Київ: УОВЦ «Оріон», 2026 | algebra | `9-klas-algebra-tarasenkova-2026.jsonl` | — |
| Задорожний К. М., Ягенська Г. В., Додь В. В., «Біологія», підручник для 9 класу закладів загальної середньої освіти, Київ: Видавничий дім «Освіта», 2026 | biolohiya | `9-klas-biolohiya-zadorozhnyi-2026.jsonl` | — |
| Ролік В. В., Войтицька Л. В., Тригуб О. М., «Підприємництво та фінансова грамотність», підручник для 9 класу закладів загальної середньої освіти, Київ: Видавничий дім «Освіта», 2026 | finansova | `9-klas-finansova-rolik-2026.jsonl` | — |
| Бар'яхтар В. Г., Довгий С. О., Божинова Ф. Я., Кірюхіна О. О., «Фізика», підручник для 9 класу закладів загальної середньої освіти, за ред. Бар'яхтара В. Г., Довгого С. О., Харків: Вид-во «Ранок», 2022 | fizyka | `9-klas-fizyka-bariakhtar-2022.jsonl` | — |
| Засєкіна Т. М., Гвоздецький М. В., Сіпій В. В., «Фізика», підручник для 9 класу закладів загальної середньої освіти, Київ: Видавничий дім «Освіта», 2026 | fizyka | `9-klas-fizyka-zasiekina-2026.jsonl` | — |
| Бойко В. М., Барановський М. О., Коваль Ю., Гринюк Т., Атаман Л., «Географія», підручник для 9 класу закладів загальної середньої освіти, Київ: «Літера ЛТД», 2026 | heohrafiya | `9-klas-geografiia-boiko-2026.jsonl` | — |
| Бевз Г. П., Бевз В. Г., Васильєва Д. В., Владімірова Н. Г., «Геометрія», підручник для 9 класу закладів загальної середньої освіти, Київ: Видавничий дім «Освіта», 2026 | heometriya | `9-klas-heometriya-bevz-2026.jsonl` | — |
| Мерзляк А. Г., Полонський В. Б., Якір М. С., «Геометрія», підручник для 9 класу загальноосвітніх навчальних закладів, Харків: «Гімназія», 2017 | heometriya | `9-klas-heometriya-merzliak-2017.jsonl` | — |
| Пометун О. І., Дудар О. В., Кришмарел В. Ю., Ремех Т. О., «Громадянська освіта», підручник для 9 класу закладів загальної середньої освіти, Київ: Видавничий дім «Освіта», 2026 | hromadianska | `9-klas-hromadianska-osvita-pometun-2026.jsonl` | — |
| Морзе Н. В., Барна О. В., «Інформатика», підручник для 9 класу закладів загальної середньої освіти, Київ: УОВЦ «Оріон», 2026 | informatyka | `9-klas-informatyka-morze-2026.jsonl` | — |
| Гісем О. В., Мартинюк О. О., «Історія України», підручник для 9 класу загальноосвітніх навчальних закладів, Харків: Вид-во «Ранок», 2017 | istoriya | `9-klas-istorija-ukrajini-gisem-2017.jsonl` | — |
| Попель П. П., Крикля Л. С., «Хімія», підручник для 9 класу загальноосвітніх навчальних закладів, Київ: ВЦ «Академія», 2017 | khimiya | `9-klas-khimiya-popel-2017.jsonl` | — |
| Ярошенко О. Г., Коршевнюк Т. В., «Хімія», підручник для 9 класу закладів загальної середньої освіти, Київ: УОВЦ «Оріон», 2026 | khimiya | `9-klas-khimiya-yaroshenko-2026.jsonl` | — |
| Кондратова Л. Г., «Мистецтво», підручник інтегрованого курсу для 9 класу закладів загальної середньої освіти, Тернопіль: Навчальна книга — Богдан, 2025 | mystetstvo | `9-klas-mystetstvo-kondratova-2025.jsonl` | — |
| Масол Л. М., «Мистецтво», підручник для 9 класу загальноосвітніх навчальних закладів, Київ: Видавничий дім «Освіта», 2017 | mystetstvo | `9-klas-mystetstvo-masol-2017.jsonl` | — |
| Берендєєв С. О., Сергієнко В. С., «Правознавство», підручник для 9 класу закладів загальної середньої освіти, Харків: Вид-во «Ранок», 2026 | pravoznavstvo | `9-klas-pravoznavstvo-berendieiev-2026.jsonl` | — |
| Біленко О. В., Пелагейченко М. Л., «Технології», підручник для 9 класу закладів загальної середньої освіти, Тернопіль: Астон, 2026 | tekhnolohiyi | `9-klas-tekhnolohiyi-bilenko-2026.jsonl` | — |
| Авраменко О. М., «Українська література», підручник для 9 класу загальноосвітніх навчальних закладів, Київ: «Грамота», 2017 | ukrlit | `9-klas-ukrajinska-literatura-avramenko-2017.jsonl` | — |
| Авраменко О. М., «Українська мова», підручник для 9 класу загальноосвітніх навчальних закладів, Київ: «Грамота», 2017 | ukrmova | `9-klas-ukrajinska-mova-avramenko-2017.jsonl` | — |
| Заболотний В. В., Заболотний О. В., Слоньовська О. В., Ярмульська І. В., «Українська література», підручник для 9 класу закладів загальної середньої освіти, Київ: «Літера ЛТД», 2026 | ukrlit | `9-klas-ukrlit-zabolotnyi-2026.jsonl` | — |
| Пометун О. І., Дудар О. В., «Всесвітня історія», підручник для 9 класу закладів загальної середньої освіти, Київ: Видавничий дім «Освіта», 2026 | vsesvitnia | `9-klas-vsesvitnia-istoriia-pometun-2026.jsonl` | — |
| Ковбасенко Ю. І., Первак О. П., Дячок С. О., «Зарубіжна література», підручник для 9 класу закладів загальної середньої освіти, Київ: «Літера ЛТД», 2026 | zarubizhna-literatura | `9-klas-zarubizhna-literatura-kovbasenko-2026.jsonl` | — |
| Гущина Н. І., Василашко І. П., «Здоров’я, безпека та добробут», підручник інтегрованого курсу для 9 класу закладів загальної середньої освіти, Київ: Видавничий дім «Освіта», 2026 | zdorovia | `9-klas-zdorovia-gushchyna-2026.jsonl` | — |

Author names and titles are verified against the front-matter text captured
directly in each book's own JSONL chunks (`data/textbook_chunks/grade-09/*.jsonl`
— colophons and title pages). Nothing here is invented.

## File size handling (large headword inventories)

Two headword inventories in this grade exceeded the 2,048,000-byte
`check-added-large-files` pre-commit gate due to rich vocabulary breadth in
comprehensive literature textbooks:
- `ukrlit-avramenko-grade9-2017`: split into `ukrlit-avramenko-grade9-2017-headwords-1.yaml` (950 KB) and `ukrlit-avramenko-grade9-2017-headwords-2.yaml` (1.2 MB);
- `zarlit-kovbasenko-grade9-2026`: split into `zarlit-kovbasenko-grade9-2026-headwords-1.yaml` (1.0 MB) and `zarlit-kovbasenko-grade9-2026-headwords-2.yaml` (1.2 MB).

Both splits follow the grade-7 `istoriya-shchupak` pattern: headwords split in half
by extraction order, with `unknown_forms` preserved in part 2. No data was dropped
or altered. All other 22 headword inventories and all 24 glossaries remain single files
well below the 2 MB threshold.

## Unknown-rate gating

All 24 textbooks passed the default 20% unknown-forms gate (`scripts/lexicon/extract_textbook_chunk_headword_inventory.py`
`validate_result`) without requiring any `--max-unknown-rate` override:
- `finansova-rolik-grade9-2026` passed at 12.16% (no glyph-drop defect present in this edition);
- The remaining 23 books cleared the gate cleanly, with unknown rates ranging from 4.62% (`tekhnolohiyi-bilenko`)
  to 19.19% (`heohrafiya-boiko`).

## Pipeline

Same two-stage pipeline as grades 1–8 (`data/lexicon/source-inventory/grade-01/README.md` … `.../grade-08/README.md`):
1. **`scripts/lexicon/extract_textbook_chunk_headword_inventory.py`** — tokenizes each book's chunk text and batch-verifies every unique form against local VESUM (`data/vesum.db`, `scripts.verification.vesum.verify_words`). Output: `*-headwords.yaml` (or `*-headwords-1.yaml` / `*-headwords-2.yaml` when split).
2. **`scripts/lexicon/admit_textbook_book_glossary.py`** — admits a candidate from this round's capped attempt list only when **both** gates clear with a cited source:
   - a public Ukrainian definition from **СУМ-20** (`newsum`) or **ВТС** (`vts`) — never СУМ-11;
   - a learner English gloss from **dmklinger** (UK→EN, Wiktionary-derived), falling back to slovnyk.me's **ukreng**.

The capped attempt list (top 300 by frequency, content words only — `conj/prep/pron/part/intj` POS, ambiguous forms, and proper-noun candidates dropped before ranking) was derived from each book's headwords with the same selection rule as grades 1–8.
Both dictionary lookups reuse the shared cache `data/lexicon/slovnyk_cache/<lemma>.json` (gitignored).

## Counts (this run)

| Book | VESUM content candidates | Attempted (top 300 by freq) | Admitted | Richness | Residual (not yet attempted) |
| --- | ---: | ---: | ---: | ---: | ---: |
| algebra-merzliak-grade9-2017 | 1,877 | 300 | 261 | 87.0% | 1,577 |
| algebra-tarasenkova-grade9-2026 | 2,174 | 300 | 266 | 88.7% | 1,874 |
| biolohiya-zadorozhnyi-grade9-2026 | 3,865 | 300 | 268 | 89.3% | 3,565 |
| finansova-rolik-grade9-2026 | 3,376 | 300 | 282 | 94.0% | 3,076 |
| fizyka-bariakhtar-grade9-2022 | 3,840 | 300 | 262 | 87.3% | 3,540 |
| fizyka-zasiekina-grade9-2026 | 3,762 | 300 | 260 | 86.7% | 3,462 |
| heohrafiya-boiko-grade9-2026 | 5,155 | 300 | 268 | 89.3% | 4,855 |
| heometriya-bevz-grade9-2026 | 1,704 | 300 | 247 | 82.3% | 1,404 |
| heometriya-merzliak-grade9-2017 | 1,188 | 300 | 251 | 83.7% | 888 |
| hromadianska-osvita-pometun-grade9-2026 | 2,571 | 300 | 283 | 94.3% | 2,271 |
| informatyka-morze-grade9-2026 | 3,063 | 300 | 284 | 94.7% | 2,763 |
| istoriya-gisem-grade9-2017 | 5,010 | 300 | 282 | 94.0% | 4,710 |
| khimiya-popel-grade9-2017 | 2,483 | 300 | 262 | 87.3% | 2,183 |
| khimiya-yaroshenko-grade9-2026 | 3,511 | 300 | 258 | 86.0% | 3,211 |
| mystetstvo-kondratova-grade9-2025 | 4,417 | 300 | 273 | 91.0% | 4,117 |
| mystetstvo-masol-grade9-2017 | 4,641 | 300 | 276 | 92.0% | 4,341 |
| pravoznavstvo-berendieiev-grade9-2026 | 2,835 | 300 | 273 | 91.0% | 2,535 |
| tekhnolohiyi-bilenko-grade9-2026 | 4,246 | 300 | 267 | 89.0% | 3,946 |
| ukrlit-avramenko-grade9-2017 | 8,357 | 300 | 287 | 95.7% | 8,057 |
| ukrmova-avramenko-grade9-2017 | 6,121 | 300 | 278 | 92.7% | 5,821 |
| ukrlit-zabolotnyi-grade9-2026 | 7,334 | 300 | 291 | 97.0% | 7,034 |
| vsesvitnia-istoriia-pometun-2026 | 3,825 | 300 | 288 | 96.0% | 3,525 |
| zarlit-kovbasenko-grade9-2026 | 9,925 | 300 | 291 | 97.0% | 9,625 |
| zdorovia-gushchyna-grade9-2026 | 3,375 | 300 | 285 | 95.0% | 3,075 |
| **Total** | **98,655** | **7,200** | **6,543** | **90.9%** | **91,455** |

Richness floor for this program is 40% (`--allow-richness-regression` not used, not needed — every book cleared 82%+).
"Residual (not yet attempted)" is real, VESUM-verified vocabulary outside this round's per-book frequency cap.
"Residual (this batch)" — attempted candidates that failed one or both gates — is recorded per book in the `residual:` block of its glossary YAML with the specific reason(s).

## What this is not

- Not the Atlas manifest (`site/src/data/lexicon-manifest.json`).
- Not a re-run or extension of the 2026-07-19 oneshot bulk mine.
- Not grade 10+. Next grade in the #7551 queue is grade 10. Issue #7551 remains open.
