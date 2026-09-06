# Grade-11 textbook glossaries (#7551)

Per-book domain/headword glossaries re-extracted from local
`data/textbook_chunks/grade-11/*.jsonl` — **not** the oneshot function-word
mine (`data/lexicon/source-inventory/oneshot/textbook-jsonl-curated-2026-07-19-bulk.yaml`,
explicitly excluded per #7551) and not a Grade-11-wide single dump. All 18
Ukrainian-language grade-11 textbook JSONL sources are processed, each with its
own glossary. The English textbook (`11-klas-angliiska-mova-kuchma-2019.jsonl`)
is explicitly skipped as out-of-scope (foreign language curriculum, not a
Ukrainian headword source).

Same-subject different authors are treated as separate books: two ukrmova
textbooks (`ukrmova-avramenko`, `ukrmova-glazova`) and two istoriya Ukrainy
textbooks (`istoriya-gisem`, `istoriya-hlibovska`). Older 2018–2019 editions
and newer 2024 editions are in-scope for complete Atlas coverage;
`10-11-klas-mystectvo-nazarenko-2018` is processed as a Ukrainian art book.
STEM, social sciences, humanities, law, and defence/health textbooks are all
included. Books processed:

| Book | Subject | JSONL | Skip reason |
| --- | --- | --- | --- |
| Назаренко Н. В., Чєн Н. В., Севастьянова Д. О., «Мистецтво (рівень стандарту, профільний рівень)», підручник для 10 (11) класу закладів загальної середньої освіти, Ірпінь: ТОВ «Видавництво «Перун», 2018 | mystetstvo | `10-11-klas-mystectvo-nazarenko-2018.jsonl` | — |
| Істер О. С., Єргіна О. В., «Алгебра і початки аналізу (профільний рівень)», підручник для 11-го класу закладів загальної середньої освіти, Київ: «Генеза», 2019 | algebra | `11-klas-algebra-ister-2019-prof.jsonl` | — |
| Пришляк М. П., «Астрономія (рівень стандарту)», підручник для 11 класу закладів загальної середньої освіти, Харків: Вид-во «Ранок», 2019 | astronomiya | `11-klas-astronomiya-pryshliak-2019.jsonl` | — |
| Шаламов Р. В., Каліберда М. С., Носов Г. А., «Біологія і екологія (рівень стандарту)», підручник для 11 класу закладів загальної середньої освіти, Харків: «Соняшник», 2019 | biolohiya | `11-klas-biologiia-i-ekologia-shalamov-2019.jsonl` | — |
| Криховець-Хом’як Л. Я., Длугопольський О. В., Вірковська А. А., «Економіка (профільний рівень)», підручник для 11 класу закладів загальної середньої освіти, Тернопіль: «Астон», 2019 | ekonomika | `11-klas-ekonomika-homiak-2019.jsonl` | — |
| Засєкіна Т. М., Засєкін Д. О., «Фізика і астрономія (рівень стандарту)», підручник для 11 класу закладів загальної середньої освіти, Київ: УОВЦ «Оріон», 2019 | fizyka | `11-klas-fizika-astronomiia-zasekina-2019-standart.jsonl` | — |
| Григорович О. В., «Хімія (рівень стандарту)», підручник для 11 класу закладів загальної середньої освіти, Харків: Вид-во «Ранок», 2019 | khimiya | `11-klas-himia-grygorovych-2019.jsonl` | — |
| Руденко В. Д., Речич Н. В., Потієнко В. О., «Інформатика (профільний рівень)», підручник для 11 класу закладів загальної середньої освіти, Харків: Видавництво «Ранок», 2019 | informatyka | `11-klas-informatyka-rudenko-2019.jsonl` | — |
| Гісем О. В., Мартинюк О. О., Сирцова О. М., Галімов А. Е., «Історія України (профільний рівень)», підручник для 11 класу закладів загальної середньої освіти, Харків: Видавництво «Ранок», 2024 | istoriya | `11-klas-istoriya-ukr-gisem-2024.jsonl` | — |
| Хлібовська Г. М., Крижановська М. Є., Наумчук О. В., «Історія України (рівень стандарту)», підручник для 11 класу закладів загальної середньої освіти, Тернопіль: «Астон», 2024 | istoriya | `11-klas-istoriya-ukr-hlibovska-2024.jsonl` | — |
| Щупак І. Я., «Всесвітня історія (рівень стандарту)», підручник для 11 класу закладів загальної середньої освіти, Київ: УОВЦ «Оріон», 2024 | vsesvitnia | `11-klas-istoriya-vsesvit-schupak-2024.jsonl` | — |
| Нелін Є. П., Долгова О. Є., «Математика: алгебра і початки аналізу та геометрія (рівень стандарту)», підручник для 11 класу закладів загальної середньої освіти, Харків: Вид-во «Ранок», 2019 | matematyka | `11-klas-matematyka-nelin-2019.jsonl` | — |
| Наровлянський О. Д., «Правознавство (профільний рівень)», підручник для 11 класу закладів загальної середньої освіти, Київ: «Грамота», 2019 | pravoznavstvo | `11-klas-pravoznavstvo-narovlianskyi-2019.jsonl` | — |
| Авраменко О. М., «Українська література (рівень стандарту)», підручник для 11 класу закладів загальної середньої освіти, Київ: «Грамота», 2019 | ukrlit | `11-klas-ukrajinska-literatura-avramenko-2019.jsonl` | — |
| Авраменко О. М., «Українська мова (рівень стандарту)», підручник для 11 класу закладів загальної середньої освіти, Київ: «Грамота», 2019 | ukrmova | `11-klas-ukrajinska-mova-avramenko-2019.jsonl` | — |
| Глазова О. П., «Українська мова (рівень стандарту)», підручник для 11 класу закладів загальної середньої освіти, Харків: Вид-во «Ранок», 2019 | ukrmova | `11-klas-ukrajinska-mova-glazova-2019.jsonl` | — |
| Гудима А. А., Пашко К. О., Гарасимів І. М., Фука М. М., «Захист Вітчизни: Основи медичних знань (рівень стандарту)», підручник для 11 класу закладів загальної середньої освіти, Тернопіль: «Астон», 2019 | zakhyst | `11-klas-zakhist-vitchizni-gudima-2019-med.jsonl` | — |
| Волощук Є. В., «Зарубіжна література (рівень стандарту)», підручник для 11 класу закладів загальної середньої освіти, Київ: «Генеза», 2019 | zarubizhna-literatura | `11-klas-zarubizhna-literatura-voloshhuk-2019.jsonl` | — |
| Кучма М. О., Заблоцька О. С., «Англійська мова (11-й рік навчання, рівень стандарту)», підручник для 11 класу закладів загальної середньої освіти, Київ: «Генеза», 2019 | foreign_language | `11-klas-angliiska-mova-kuchma-2019.jsonl` | English textbook, not a UK-headword source |

Author names and titles are verified against the front-matter text captured
directly in each book's own JSONL chunks (`data/textbook_chunks/grade-11/*.jsonl`
— colophons and title pages). Nothing here is invented.

## File size handling (large headword inventories)

All 18 headword inventory files and all 18 glossary files are within the 2,048,000-byte
`check-added-large-files` pre-commit gate (the largest file is
`istoriya-hlibovska-grade11-2024-headwords.yaml` at 1,967,320 bytes).
No file splitting was required.

## Unknown-rate gating

All 18 Ukrainian textbooks passed the default 20% unknown-forms gate
(`scripts/lexicon/extract_textbook_chunk_headword_inventory.py` `validate_result`)
cleanly without override (unknown rates range between 6.67% and 15.92%). Zero
overrides were needed.

## Pipeline

Same two-stage pipeline as grades 1–10 (`data/lexicon/source-inventory/grade-01/README.md` … `.../grade-10/README.md`):
1. **`scripts/lexicon/extract_textbook_chunk_headword_inventory.py`** — tokenizes each book's chunk text and batch-verifies every unique form against local VESUM (`data/vesum.db`, `scripts.verification.vesum.verify_words`). Output: `*-headwords.yaml`.
2. **`scripts/lexicon/admit_textbook_book_glossary.py`** — admits a candidate from this round's capped attempt list only when **both** gates clear with a cited source:
   - a public Ukrainian definition from **СУМ-20** (`newsum`) or **ВТС** (`vts`) — never СУМ-11;
   - a learner English gloss from **dmklinger** (UK→EN, Wiktionary-derived), falling back to slovnyk.me's **ukreng**.

The capped attempt list (top 300 by frequency, content words only — `conj/prep/pron/part/intj` POS, ambiguous forms, and proper-noun candidates dropped before ranking) was derived from each book's headwords with the same selection rule as grades 1–10.
Both dictionary lookups reuse the shared cache `data/lexicon/slovnyk_cache/<lemma>.json` (gitignored).

## Counts (this run)

| Book | VESUM content candidates | Attempted (top 300 by freq) | Admitted | Richness | Residual (not yet attempted) |
| --- | ---: | ---: | ---: | ---: | ---: |
| mystetstvo-nazarenko-grade11-2018 | 4,897 | 300 | 279 | 93.0% | 4,597 |
| algebra-ister-grade11-2019 | 2,118 | 300 | 264 | 88.0% | 1,818 |
| astronomiya-pryshliak-grade11-2019 | 2,625 | 300 | 272 | 90.7% | 2,325 |
| biolohiya-shalamov-grade11-2019 | 6,774 | 300 | 271 | 90.3% | 6,474 |
| ekonomika-homiak-grade11-2019 | 4,645 | 300 | 278 | 92.7% | 4,345 |
| fizyka-zasekina-grade11-2019 | 3,680 | 300 | 258 | 86.0% | 3,380 |
| khimiya-hryhorovych-grade11-2019 | 3,148 | 300 | 254 | 84.7% | 2,848 |
| informatyka-rudenko-grade11-2019 | 3,402 | 300 | 266 | 88.7% | 3,102 |
| istoriya-gisem-grade11-2024 | 5,341 | 300 | 279 | 93.0% | 5,041 |
| istoriya-hlibovska-grade11-2024 | 7,250 | 300 | 285 | 95.0% | 6,950 |
| vsesvitnia-istoriia-schupak-grade11-2024 | 6,295 | 300 | 278 | 92.7% | 5,995 |
| matematyka-nelin-grade11-2019 | 2,200 | 300 | 259 | 86.3% | 1,900 |
| pravoznavstvo-narovlianskyi-grade11-2019 | 3,936 | 300 | 262 | 87.3% | 3,636 |
| ukrlit-avramenko-grade11-2019 | 8,361 | 300 | 287 | 95.7% | 8,061 |
| ukrmova-avramenko-grade11-2019 | 7,244 | 300 | 285 | 95.0% | 6,944 |
| ukrmova-glazova-grade11-2019 | 6,322 | 300 | 278 | 92.7% | 6,022 |
| zakhyst-gudima-grade11-2019 | 6,568 | 300 | 279 | 93.0% | 6,268 |
| zarlit-voloshhuk-grade11-2019 | 5,471 | 300 | 288 | 96.0% | 5,171 |
| **Total** | **90,277** | **5,400** | **4,922** | **91.1%** | **84,877** |

Richness floor for this program is 40% (`--allow-richness-regression` not used, not needed — every book cleared 84%+).
"Residual (not yet attempted)" is real, VESUM-verified vocabulary outside this round's per-book frequency cap.
"Residual (this batch)" — attempted candidates that failed one or both gates — is recorded per book in the `residual:` block of its glossary YAML with the specific reason(s).

## What this is not

- Not the Atlas manifest (`site/src/data/lexicon-manifest.json`).
- Not a re-run or extension of the 2026-07-19 oneshot bulk mine.
- Grade 11 is the final grade in the school textbook queue. School curriculum extraction (grades 1–11) is now complete across all 11 grades except Drive-only extras. Issue #7551 remains open for downstream promotion and Atlas manifest integration.
