# Grade-10 textbook glossaries (#7551)

Per-book domain/headword glossaries re-extracted from local
`data/textbook_chunks/grade-10/*.jsonl` — **not** the oneshot function-word
mine (`data/lexicon/source-inventory/oneshot/textbook-jsonl-curated-2026-07-19-bulk.yaml`,
explicitly excluded per #7551) and not a Grade-10-wide single dump. All 19
Ukrainian-language grade-10 textbook JSONL sources are processed, each with its
own glossary. The English textbook (`10-klas-angliiska-mova-burenko-2018.jsonl`)
is explicitly skipped as out-of-scope (foreign language curriculum, not a
Ukrainian headword source).

Same-subject different authors are treated as separate books: three ukrmova
textbooks (`ukrmova-avramenko`, `ukrmova-glazova`, `ukrmova-karaman`). Older 2018
editions are in-scope for complete Atlas coverage; `10-11-klas-tekhnolohiyi-khodzycka-2019`
is processed as a Ukrainian technologies textbook. STEM, social sciences, humanities,
and defence/health textbooks are all included. Books processed:

| Book | Subject | JSONL | Skip reason |
| --- | --- | --- | --- |
| Ходзицька І. Ю., Боринець Н. І., Гащак В. М. та ін., «Технології (рівень стандарту)», підручник для 10 (11) класу закладів загальної середньої освіти, Харків: Вид-во «Ранок», 2019 | tekhnolohiyi | `10-11-klas-tekhnolohiyi-khodzycka-2019.jsonl` | — |
| Істер О. С., Єргіна О. В., «Алгебра і початки аналізу (профільний рівень)», підручник для 10 класу закладів загальної середньої освіти, Київ: «Генеза», 2018 | algebra | `10-klas-algebra-ister-2018.jsonl` | — |
| Задорожний К. М., «Біологія і екологія (рівень стандарту)», підручник для 10 класу закладів загальної середньої освіти, Харків: Вид-во «Ранок», 2018 | biolohiya | `10-klas-biologija-i-ekologija-zadorozhnij-2018-stand.jsonl` | — |
| Крупська Л. П., Тимченко І. Є., Чорна Т. І., «Економіка (профільний рівень)», підручник для 10 класу закладів загальної середньої освіти, Харків: Вид-во «Ранок», 2018 | ekonomika | `10-klas-ekonomika-krupska-2018.jsonl` | — |
| Бар'яхтар В. Г., Довгий С. О., Божинова Ф. Я., Кірюхіна О. О., «Фізика (рівень стандарту)», підручник для 10 класу закладів загальної середньої освіти, за ред. Бар'яхтара В. Г., Довгого С. О., Харків: Вид-во «Ранок», 2018 | fizyka | `10-klas-fizyka-barjakhtar-2018.jsonl` | — |
| Бойко В. М., Брайчевський Ю. С., Яценко Б. П., «Географія (рівень стандарту)», підручник для 10 класу закладів загальної середньої освіти, Ірпінь: ТОВ «Видавництво «Перун», 2018 | heohrafiya | `10-klas-geografija-bojko-2018.jsonl` | — |
| Істер О. С., Єргіна О. В., «Геометрія (профільний рівень)», підручник для 10 класу закладів загальної середньої освіти, Київ: «Генеза», 2018 | heometriya | `10-klas-geometrija-ister-2018.jsonl` | — |
| Григорович О. В., «Хімія (рівень стандарту)», підручник для 10 класу закладів загальної середньої освіти, Харків: Вид-во «Ранок», 2018 | khimiya | `10-klas-himija-grygorovych-2018.jsonl` | — |
| Гісем О. О., Мартинюк О. О., «Громадянська освіта (інтегрований курс, рівень стандарту)», підручник для 10 класу закладів загальної середньої освіти, Харків: Вид-во «Ранок», 2018 | hromadianska-osvita | `10-klas-hromadianska-gisem-2018.jsonl` | — |
| Руденко В. Д., Речич Н. В., Потієнко В. О., «Інформатика (рівень стандарту)», підручник для 10 (11) класу закладів загальної середньої освіти, Харків: Вид-во «Ранок», 2018 | informatyka | `10-klas-informatika-rudenko-2018-stand.jsonl` | — |
| Гісем О. В., Мартинюк О. О., «Історія України (рівень стандарту)», підручник для 10 класу закладів загальної середньої освіти, Харків: Вид-во «Ранок», 2018 | istoriya | `10-klas-istorija-ukrajiny-gisem-2018.jsonl` | — |
| Мерзляк А. Г., Номіровський Д. А., Полонський В. Б., Якір М. С., «Математика: алгебра і початки аналізу та геометрія (рівень стандарту)», підручник для 10 класу закладів загальної середньої освіти, Харків: «Гімназія», 2018 | matematyka | `10-klas-matematika-merzljak-2018.jsonl` | — |
| Авраменко О. М., Пахаренко В. І., «Українська література (рівень стандарту)», підручник для 10 класу закладів загальної середньої освіти, Київ: «Грамота», 2018 | ukrlit | `10-klas-ukrajinska-literatura-avramenko-2018.jsonl` | — |
| Авраменко О. М., «Українська мова (рівень стандарту)», підручник для 10 класу закладів загальної середньої освіти, Київ: «Грамота», 2018 | ukrmova | `10-klas-ukrajinska-mova-avramenko-2018.jsonl` | — |
| Глазова О. П., «Українська мова (рівень стандарту)», підручник для 10 класу закладів загальної середньої освіти, Харків: Вид-во «Ранок», 2018 | ukrmova | `10-klas-ukrmova-glazova-2018.jsonl` | — |
| Караман С. О., Горошкіна О. М., Караман О. В., Попова Л. О., «Українська мова (профільний рівень)», підручник для 10 класу закладів загальної середньої освіти, Харків: Вид-во «Ранок», 2018 | ukrmova | `10-klas-ukrmova-karaman-2018.jsonl` | — |
| Гісем О. В., Мартинюк О. О., «Всесвітня історія (рівень стандарту)», підручник для 10 класу закладів загальної середньої освіти, Харків: Вид-во «Ранок», 2018 | vsesvitnia | `10-klas-vsesvitnia-istoriia-gisem-2018-stand.jsonl` | — |
| Фука М. М., Пашко К. О., Гарасимів І. М., Гудима А. А., Чуткий С. І., Мельник Р. М., Білах Б. І., «Захист України (рівень стандарту)», підручник для 10 класу закладів загальної середньої освіти, Тернопіль: «Астон», 2023 | zakhyst | `10-klas-zakhyst-fuka-2023.jsonl` | — |
| Волощук Є. В., Звиняцьковський В. Я., Філенко О. В., «Зарубіжна література (профільний рівень)», підручник для 10 класу закладів загальної середньої освіти, Київ: «Генеза», 2018 | zarubizhna-literatura | `10-klas-zarubizhna-literatura-voloshhuk-2018.jsonl` | — |
| Буренко В. М., «Англійська мова (10-й рік навчання, профільний рівень)», підручник для 10 класу закладів загальної середньої освіти, Харків: ТОВ Видавництво «Ранок», 2018 | foreign_language | `10-klas-angliiska-mova-burenko-2018.jsonl` | English textbook, not a UK-headword source |

Author names and titles are verified against the front-matter text captured
directly in each book's own JSONL chunks (`data/textbook_chunks/grade-10/*.jsonl`
— colophons and title pages). Nothing here is invented.

## File size handling (large headword inventories)

The following headword inventories exceeded the 2,048,000-byte
`check-added-large-files` pre-commit gate and were split:
- `ukrmova-karaman-grade10-2018`: split into `ukrmova-karaman-grade10-2018-headwords-1.yaml`, `ukrmova-karaman-grade10-2018-headwords-2.yaml`.

Splits follow the established grade-7 `istoriya-shchupak` and grade-9 pattern: headwords split in half
by extraction order, with `unknown_forms` preserved in part 2. No data was dropped or altered.

## Unknown-rate gating

17 of the 19 textbooks passed the default 20% unknown-forms gate (`scripts/lexicon/extract_textbook_chunk_headword_inventory.py`
`validate_result`) cleanly without override.
Two books required scoped unknown-rate overrides due to confirmed upstream PDF text-layer defects (matching the grade-8 `finans-plastun` precedent):

1. **`heometriya-ister-grade10-2018`** (unknown rate 25.34% vs 20% gate): upstream PDF text layer carries split apostrophes (`Розв’ язання`), Latin geometric vertex labels extracted as Cyrillic single-letter tokens (`Ь` for L, `АВС`, `АК`, `ВС`), and high-frequency abbreviated figure labels (`мал.`). Override applied: `--max-unknown-rate 0.30` with mandatory justification.
2. **`ukrlit-avramenko-grade10-2018`** (unknown rate 28.55% vs 20% gate): upstream PDF text layer contains 80,000+ soft-hyphen plus space (`\xad `) artifacts across running text (e.g. `Під\xad руч\xad ник`), splitting Ukrainian words into thousands of isolated syllables (`ли`, `ка`, `ва`, `ло`, `ки`, etc.). Override applied: `--max-unknown-rate 0.35` with mandatory justification.

In both cases, corrupted unknown forms are recorded in `unknown_forms:` and excluded from candidate ranking; admission quality and vocabulary richness are unaffected (both cleared >80% richness).

## Pipeline

Same two-stage pipeline as grades 1–9 (`data/lexicon/source-inventory/grade-01/README.md` … `.../grade-09/README.md`):
1. **`scripts/lexicon/extract_textbook_chunk_headword_inventory.py`** — tokenizes each book's chunk text and batch-verifies every unique form against local VESUM (`data/vesum.db`, `scripts.verification.vesum.verify_words`). Output: `*-headwords.yaml` (or `*-headwords-1.yaml` / `*-headwords-2.yaml` when split).
2. **`scripts/lexicon/admit_textbook_book_glossary.py`** — admits a candidate from this round's capped attempt list only when **both** gates clear with a cited source:
   - a public Ukrainian definition from **СУМ-20** (`newsum`) or **ВТС** (`vts`) — never СУМ-11;
   - a learner English gloss from **dmklinger** (UK→EN, Wiktionary-derived), falling back to slovnyk.me's **ukreng**.

The capped attempt list (top 300 by frequency, content words only — `conj/prep/pron/part/intj` POS, ambiguous forms, and proper-noun candidates dropped before ranking) was derived from each book's headwords with the same selection rule as grades 1–9.
Both dictionary lookups reuse the shared cache `data/lexicon/slovnyk_cache/<lemma>.json` (gitignored).

## Counts (this run)

| Book | VESUM content candidates | Attempted (top 300 by freq) | Admitted | Richness | Residual (not yet attempted) |
| --- | ---: | ---: | ---: | ---: | ---: |
| tekhnolohiyi-khodzycka-grade10-2019 | 5,021 | 300 | 267 | 89.0% | 4,721 |
| algebra-ister-grade10-2018 | 1,806 | 300 | 256 | 85.3% | 1,506 |
| biolohiya-zadorozhnyi-grade10-2018 | 3,323 | 300 | 272 | 90.7% | 3,023 |
| ekonomika-krupska-grade10-2018 | 4,536 | 300 | 272 | 90.7% | 4,236 |
| fizyka-bariakhtar-grade10-2018 | 4,021 | 300 | 256 | 85.3% | 3,721 |
| heohrafiya-boiko-grade10-2018 | 4,173 | 300 | 270 | 90.0% | 3,873 |
| heometriya-ister-grade10-2018 | 1,346 | 300 | 241 | 80.3% | 1,046 |
| khimiya-hryhorovych-grade10-2018 | 3,160 | 300 | 260 | 86.7% | 2,860 |
| hromadianska-osvita-gisem-grade10-2018 | 4,894 | 300 | 286 | 95.3% | 4,594 |
| informatyka-rudenko-grade10-2018 | 2,686 | 300 | 272 | 90.7% | 2,386 |
| istoriya-gisem-grade10-2018 | 4,389 | 300 | 280 | 93.3% | 4,089 |
| matematyka-merzliak-grade10-2018 | 1,193 | 300 | 251 | 83.7% | 893 |
| ukrlit-avramenko-grade10-2018 | 5,038 | 300 | 250 | 83.3% | 4,738 |
| ukrmova-avramenko-grade10-2018 | 7,517 | 300 | 284 | 94.7% | 7,217 |
| ukrmova-glazova-grade10-2018 | 6,816 | 300 | 273 | 91.0% | 6,516 |
| ukrmova-karaman-grade10-2018 | 9,057 | 300 | 284 | 94.7% | 8,757 |
| vsesvitnia-istoriia-gisem-grade10-2018 | 3,597 | 300 | 281 | 93.7% | 3,297 |
| zakhyst-fuka-grade10-2023 | 7,713 | 300 | 269 | 89.7% | 7,413 |
| zarlit-voloshhuk-grade10-2018 | 6,223 | 300 | 290 | 96.7% | 5,923 |
| **Total** | **86,509** | **5,700** | **5,114** | **89.7%** | **80,809** |

Richness floor for this program is 40% (`--allow-richness-regression` not used, not needed — every book cleared 80%+).
"Residual (not yet attempted)" is real, VESUM-verified vocabulary outside this round's per-book frequency cap.
"Residual (this batch)" — attempted candidates that failed one or both gates — is recorded per book in the `residual:` block of its glossary YAML with the specific reason(s).

## What this is not

- Not the Atlas manifest (`site/src/data/lexicon-manifest.json`).
- Not a re-run or extension of the 2026-07-19 oneshot bulk mine.
- Not grade 11+. Next grade in the #7551 queue is grade 11. Issue #7551 remains open.
