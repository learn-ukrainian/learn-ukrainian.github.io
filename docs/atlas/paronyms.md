# Source-Attested Paronyms (`paronyms-v1`)

Machine-readable source-attested paronym pairs for the Atlas word-card builder
(«не плутати з» / do-not-confuse hints): [`registry/atlas/paronyms-v1.json`](../../registry/atlas/paronyms-v1.json).

## Method

1. **Deterministic extraction (`scripts/atlas/paronyms/extractor.py`)**
   - Scans every `textbooks` chunk in `data/sources.db` matching `textbooks_fts MATCH 'паронім*'`
     (read-only, 117 chunks across 20 textbook source files) plus the 5 public Ukrainian paronym
     pages acquired from МійКлас (`registry/miyklas/paronyms-raw-v1.json`).
   - Extracts **only** explicit paronym presentations: structured paronym dictionaries
     (`СЛОВНИЧОК ПАРОНІМІВ`, `Короткий словник паронімів`, `Запам’ятайте значення паронімів`,
     `Розрізняйте пароніми`), dash/slash pair lists, parenthesized gloss pairs, inline
     definitions, semicolon-separated comma groups, and paronym-choice exercises.
   - Fails closed on mixed-topic switches (`антоніми`, `синоніми`, `омоніми`), multiple-choice
     distractor items (`А/Б/В/Г` or `а)/б)/в)`), mixed euphony quizzes, and explicit
     non-paronym disclaimers (`не є паронімічними`, `від паронімів слід відрізняти`).
   - Records every pair with `source_file`, `chunk_id`, `locator`, extraction `pattern`, exact
     `attested_forms`, verbatim `quoted_line`, and any short meaning or example stated by the
     source. Zero pairs come from model memory.
2. **VESUM verification (`scripts/atlas/paronyms/build.py`)**
   - Batch-verifies every single-token member against VESUM (`verify_words`).
   - Inflected forms from choice exercises (e.g. `(громадською, громадянською)`) resolve to
     VESUM lemmas only when both forms share a POS with unique distinct lemmas; pairs whose
     paronymy holds only on specific inflected forms across different POS (`греби` / `гриби`)
     stay marked `surface_form_pair: true`.
   - Any pair with an unattested or multiword member is routed to `"unverified"` with an
     explicit reason (`not_attested_in_vesum` or `multiword_not_in_vesum`), never into
     `"pairs"`.
3. **МійКлас acquisition and corpus-recipe note (`scripts/atlas/paronyms/miyklas.py`)**
   - All 5 public МійКлас paronym pages (5-klas «Короткий словник паронімів» plus 5/6/10/11-klas
     theory pages) returned HTTP 200 on 2026-11-23 and are stored with full provenance
     (canonical URL, HTTP status, UTC fetch timestamp, raw HTML SHA-256, extracted text SHA-256)
     in [`registry/miyklas/paronyms-raw-v1.json`](../../registry/miyklas/paronyms-raw-v1.json).
   - Live `data/sources.db` was intentionally left untouched (CTO decision 2026-11-23):
     `docs/corpus-inventory.md`’s «Safe recipe to ADD literary content» requires a mounted
     `bulk_root` (`lu_machinery.storage status` reports `bulk_root.available: False`,
     `no_marker_valid_bulk_root`) and live generation publication from the primary checkout
     (`data/sources.db` points to read-only `0444` generation
     `sources.20261030T191244Z-485bfef02834.db`).

### Deterministic replay

```bash
.venv/bin/python -m scripts.atlas.paronyms.build --check
```

## Counts

### Overall

| Metric | Count |
| --- | ---: |
| Textbook chunks scanned (`textbooks_fts MATCH 'паронім*'`) | 117 |
| Textbook chunks yielding at least one pair | 38 |
| Textbook source files yielding verified pairs | 14 |
| МійКлас pages acquired and parsed | 5 |
| **Verified unique paronym pairs (`pairs`)** | **181** |
| Verified pairs with at least one source-quoted meaning | 73 |
| Total verified source attestations | 311 |
| Distinct VESUM-verified member words | 321 |
| Unverified pairs routed to `unverified` | 10 |

### Verified pairs by source overlap

| Source coverage | Unique verified pairs |
| --- | ---: |
| Textbooks only | 115 |
| МійКлас only | 37 |
| Both textbooks and МійКлас | 29 |
| **Total unique verified pairs** | **181** |

### Verified pairs per source file

| Source file | Type | Verified pairs |
| --- | --- | ---: |
| `miyklas-5-klas-slovnyk-paronimiv` | miyklas | 46 |
| `10-klas-ukrajinska-mova-avramenko-2018` | textbook | 37 |
| `uni-ukrmova-lexicology-filon-khomik-2010` | textbook | 24 |
| `11-klas-ukrajinska-mova-glazova-2019` | textbook | 22 |
| `10-klas-ukrmova-glazova-2018` | textbook | 20 |
| `5-klas-ukrmova-avramenko-2022` | textbook | 19 |
| `7-klas-ukrmova-avramenko-2024` | textbook | 19 |
| `5-klas-ukrmova-golub-2022` | textbook | 14 |
| `5-klas-ukrmova-zabolotnyi-2023` | textbook | 13 |
| `6-klas-ukrmova-avramenko-2023` | textbook | 13 |
| `10-klas-ukrmova-karaman-2018` | textbook | 11 |
| `6-klas-ukrmova-litvinova-2023` | textbook | 9 |
| `11-klas-ukrajinska-mova-avramenko-2019` | textbook | 8 |
| `miyklas-10-klas-paronimy` | miyklas | 8 |
| `miyklas-6-klas-paronimy` | miyklas | 7 |
| `miyklas-11-klas-paronimy` | miyklas | 6 |
| `miyklas-5-klas-paronimy` | miyklas | 6 |
| `uni-ukrmova-sulm-attestation-vspu-2021` | textbook | 4 |
| `8-klas-ukrmova-avramenko-2025` | textbook | 1 |

## A1 word-card coverage

Measured against [`registry/atlas/a1-v1-inventory.json`](../../registry/atlas/a1-v1-inventory.json)
(and slices 2–6 card allocations):

| A1 denominator | Total | With ≥ 1 verified paronym |
| --- | ---: | ---: |
| A1 inventory resolved lemmas (`mapping.lemma`) | 714 | **13** (1.8%) |
| A1 inventory single-token vocabulary keys | 1,112 | **15** (1.3%) |
| A1 slices 2–6 allocated card lemmas | 236 | **7** (3.0%) |

The 13 matched A1 inventory lemmas are:
`адреса` (`адрес`, `адресант`, `адресат`), `вода` (`хода`), `відпустка` (`відпуск`),
`газ` (`гас`), `говорити` (`гомоніти`), `гривня` (`гривна`), `кав'ярня` (`кав'яр`),
`коштувати` (`куштувати`), `місто` (`місце`), `місце` (`місто`), `факт` (`фактаж`, `фактор`),
`шукати` (`ошукати`), and `їжа` (`їда`).

## Known gaps

1. **Low A1 coverage (13 / 714 lemmas):** School and university textbooks teach paronyms mostly
   on B1–C1 academic, civic, and derivational vocabulary (`авторитарний/авторитетний`,
   `громадський/громадянський`, `економний/економічний`, `тактичний/тактовний`) rather than
   concrete A1 nouns and verbs. Expanding A1–A2 coverage requires dedicated lexical sources
   (for example, the structured paronym entries in `data/movaua.db`, ZNO/NMT worksheets, or a
   cleared paronym dictionary).
2. **Meanings present on 73 / 181 pairs:** Dictionary blocks (`miyklas-5-klas-slovnyk-paronimiv`,
   `5-klas-ukrmova-zabolotnyi-2023`, `7-klas-ukrmova-avramenko-2024`) provide short meanings and
   examples for both members; exercise lists (`10-klas-ukrajinska-mova-avramenko-2018`,
   `11-klas-ukrajinska-mova-glazova-2019`) attest the pair without inline glosses, so the
   word-card builder will fall back to each card's own СУМ-20 / ВТС definition for the remaining
   108 pairs.
3. **10 unverified pairs withheld from `pairs`:**
   - 1 multiword expression (`на протязі | протягом`, `multiword_not_in_vesum`).
   - 1 textbook PDF typo (`мимохіть | михохідь` in `10-klas-ukrmova-glazova-2018`, caught by
     VESUM as `not_attested_in_vesum`).
   - 8 pairs containing a member marked `bad` / nonstandard or absent in VESUM clean forms
     (`бережливий`, `вимисел`, `вникати`, `віла`, `дерзати`/`терзати`, `криштальний`,
     `путати`/`путає`).
4. **Continuation chunks without `паронім*`:** The textbook query scans only chunks matching
   `textbooks_fts MATCH 'паронім*'`. Multi-chunk discussions where an exercise continues onto a
   later chunk without repeating the stem `паронім*` (e.g. `uni-ukrmova-prof-haluzynska-2006_s0038`)
   are intentionally excluded by the single-query scope.
5. **Live `sources.db` indexing:** `registry/miyklas/paronyms-raw-v1.json` is not yet indexed in
   `data/sources.db`; indexing it into a new `sources.db` generation remains a separate
   primary-checkout driver action if full-text MCP search over МійКлас is wanted later.
