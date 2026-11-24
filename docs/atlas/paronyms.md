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
     `Запам’ятайте значення паронімічних прикметників`, `Розрізняйте пароніми`), dash/slash pair
     lists, parenthesized gloss pairs, inline definitions, semicolon-separated comma groups, and
     paronym-choice exercises.
   - A textbook chunk is read as a paronym lesson only from the segment that itself opens with a
     dedicated paronym heading (`§ 9. Пароніми`, `Пароніми`, `2.1. Явище паронімії`, …); text
     above that heading in the same chunk is never in lesson mode. Dictionary headings
     (`Словничок паронімів`, `Короткий словник паронімів`) count only as a standalone line, and
     their scan starts at that line; a prose reference to such a dictionary ("У додатку є
     Словничок паронімів") is a passing mention, not a cue. A choice exercise whose own prompt
     sends the learner to a paronym dictionary ("Скористайтеся словничком паронімів") is a
     paronym exercise. After a summary table of lexical groups (`ГРУПИ ЛЕКСИКИ`) only its
     Пароніми row is taken, and later text is read only from an explicit section heading
     (`§ 9. Пароніми`); the table's own bare `Пароніми` label never opens a lesson. Two-line
     definition pairs need a paronym cue above them that is neither a passing mention nor a
     disclaimer (`не є паронімічними`). A МійКлас page is a paronym page as a whole. Outside
     lesson mode a segment needs its own local paronym cue.
   - Fails closed on mixed-topic switches (`антоніми`, `синоніми`, `омоніми`, numbered
     non-paronym exercises), multiple-choice distractor items (`А/Б/В/Г` or `а)/б)/в)`), mixed
     euphony quizzes, and explicit non-paronym disclaimers (`не є паронімічними`, `від паронімів
     слід відрізняти`).
   - Records every pair with `source_file`, `chunk_id`, `locator`, extraction `pattern`, exact
     `attested_forms`, verbatim `quoted_line` (sliced directly from raw source text via
     offset-mapped spans with whitespace folding only), and any short meaning or example stated
     by the source. Zero pairs come from model memory.
   - A source gloss shown to learners loses separators left by the split (a trailing comma, a
     sentence period; `та ін.` keeps its period). A gloss with a source comma error right after
     its opening relative pronoun (`який, викликає`) or a definition line cut off by the page
     layout (no terminal punctuation while its partner line has it) is withheld. The
     `quoted_line` always stays verbatim.
2. **VESUM verification (`scripts/atlas/paronyms/build.py`)**
   - Batch-verifies every single-token member against VESUM (`verify_words`) and re-gates any
     lemmatized canonical pair against pass-2 canonical lookup results before admission.
   - Inflected forms from choice exercises (e.g. `(громадською, громадянською)`) resolve to
     VESUM lemmas only when both forms share a POS with unique distinct lemmas; pairs whose
     paronymy holds only on specific inflected forms across different POS (`греби` / `гриби`)
     stay marked `surface_form_pair: true`. Every other pattern keeps the words exactly as the
     source cites them (`в'язи` / `м'язи`). For a surface-form pair VESUM attests the cited forms,
     but the registry asserts no lexeme for them (`vesum_lemmas` and `vesum_pos` are empty unless
     the form is its own lemma), because VESUM can tie such a form only to an unrelated homonym
     (`в'язи` "nape" appears only as a form of `в'яз` "elm").
   - **Antonymic and synonymic paronyms stay.** Ukrainian lexicology classes semantic relations
     between paronyms as antonymic, synonymic, ideographic and morphological-semantic:
     «Семантичні відношення між паронімами охоплюють такі вияви: 1) антонімічні зв’язки:
     еволюція − революція; прогрес − регрес; еміграція − імміграція; 2) синонімічні зв’язки:
     говорити − гомоніти; вивільняти − визволяти − звільняти; хиткий − хибкий; 3) ідеографічні
     зв’язки … м’язи − в’язи» (Філон, Хомик 2010, `uni-ukrmova-lexicology-filon-khomik-2010_s0173`,
     p. 160). A source-taught paronym pair is therefore admitted whatever that relation is.
   - **Same-meaning variants are withheld** (`same_meaning_variant`). When the primary meaning
     (first sense of the first homonym) of one member's СУМ-20 article opens with a direct
     reference to the other member, `див.` or `Те саме, що`, preceded only by the headword and its
     grammar and usage labels (`ПЛАСКИ́Й див. пло́ский`; `КРОПІТКИ́Й, а́, е́, рідко. Те саме, що
     копітки́й`). A reference inside a definition, an example, `(…)` or `[…]` does not count. The two words do not
     contrast in meaning, so the pair moves to `"unverified"` with that excerpt as `evidence`.
     The lookup reads the local СУМ-20 mirror (`sum20_mirror_articles` in `data/sources.db`,
     read-only). A reference in a later, rare or obsolete sense (`людний` / `людяний`) does not
     withhold a pair.
   - A meaning gloss is shown only when VESUM attests every Ukrainian word in it, a
     sentence-initial capital included (each part of a hyphenated compound); a gloss with a
     source typo or a VESUM `bad` form (`оспівний`, `прийомів`) is withheld. A gloss headed by a
     verb infinitive is withheld for a member that VESUM analyses only as a non-verb, because it
     defines an action rather than the member (`мимохідь`, an adverb, glossed by МійКлас as
     `проходити мимо по дорозі, побіжно`; СУМ-20 defines it as `Проходячи мимо кого-, чого-небудь`).
     The source's `quoted_line` stays verbatim.
   - Any pair with an unattested or multiword member is routed to `"unverified"` with an
     explicit reason (`not_attested_in_vesum` or `multiword_not_in_vesum`), never into
     `"pairs"`.
3. **МійКлас acquisition and corpus-recipe note (`scripts/atlas/paronyms/miyklas.py`)**
   - All 5 public МійКлас paronym pages (5-klas «Короткий словник паронімів» plus 5/6/10/11-klas
     theory pages) returned HTTP 200 on 2026-11-23 and are stored with full provenance
     (canonical URL, HTTP status, UTC fetch timestamp, raw HTML SHA-256, extracted text SHA-256)
     in [`registry/miyklas/paronyms-raw-v1.json`](../../registry/miyklas/paronyms-raw-v1.json).
   - Live `data/sources.db` was intentionally left untouched (CTO decision 2026-11-23):
     adding content via `docs/corpus-inventory.md`’s «Safe recipe to ADD literary content»
     requires a mounted bulk corpus root and primary-checkout generation publication into the
     read-only `data/sources.db` store, which remain separate from this worker task.

### One-shot build tool and corpus pin

The extractor is a **one-shot build tool, not a reusable parser**. Its heuristics were reviewed
against one corpus only: the 117 textbook chunks the `паронім*` query returns from
`data/sources.db` and the 5-page МійКлас snapshot. It is not certified for any other text.

The registry records that corpus in `sources_corpus.corpus_fingerprint`:

| Field | Meaning |
| --- | --- |
| `textbooks_fts_query`, `textbooks_result_rows` | The pinned query and the number of rows it returned |
| `textbooks_result_sha256` | SHA-256 of the ordered result set (`chunk_id`, `source_file`, `title`, `grade`, `author`, `text`) as loaded |
| `miyklas_pages`, `miyklas_snapshot_sha256` | Page count and SHA-256 of the loaded МійКлас snapshot (canonical JSON) |

Before any extraction, both the build and `--check` compute the live fingerprint and compare it
with the one recorded in the registry at `--output`; each field is compared as canonical JSON, so
a missing or extra key (even one set to `null`) and a value of another type (`5.0` for `5`)
differ. When they differ, or when the registry is missing or records no fingerprint, the build
refuses with `CorpusFingerprintError`. Every step from reading the first input to the final
comparison (the pin gate, the rebuild and, under `--check`, the byte comparison) runs inside one
fail-closed boundary: any failure there, whatever its type, is also a refusal. The three JSON
inputs (the registry at `--output`, the МійКлас snapshot and the A1 inventory) are parsed in full
as I-JSON (RFC 7493 section 2), so any of these anywhere in the file refuses, even where the
build would not read the value: a duplicate member name; a `NaN` or `Infinity` constant; a number
beyond a double's magnitude (`1e400`); a number whose value needs more significant digits than its
double holds (`3.141592653589793238462643383279`, or `1e-400`, which underflows to zero), while a
value its double reproduces when rounded to the digits the value needs is valid however it is
written (`0.1`, `0.10000000000000000`, `999999999999999.875`; trailing zeros add no digits);
an integer value outside ±(2^53 − 1) however it is written (`9007199254740992`,
`9007199254740992.0`, `9.007199254740992e15`): every number these files carry is an integer count,
and every double of that size is an integer, so no number of magnitude 2^53 or more is accepted; a
surrogate (an escape such as `\ud800`) or a noncharacter (such as U+FDD0) in a string or member
name. The boundary also covers an unreadable or non-UTF-8 file, wrong
JSON types, missing keys, nesting deep enough to exhaust the stack, an oversize value, a МійКлас
page whose text no longer matches its `text_sha256`, a broken A1 inventory and an unreadable
`sources.db`. A refusal prints `REFUSED:` and the reason: a
`CorpusFingerprintError` gives its own reason, and any other failure is prefixed with its exception
type. The whole reason is at most 2,000 characters; a longer one is cut and ends in
`... (truncated)`. A refusal writes nothing and exits 2. A new corpus (a new `sources.db` textbook
generation that changes these rows, or a re-fetched МійКлас snapshot) is a new certification: a
reviewed change that judges the extractor's output on that corpus and re-pins the fingerprint.
VESUM, the СУМ-20 mirror and the A1 inventory are not part of the pin; a valid change there that
alters the output shows as `DRIFT` under `--check` (exit 1).

### Deterministic replay

```bash
.venv/bin/python -m scripts.atlas.paronyms.build --check
```

Exit 0 means the pinned corpus reproduces the committed registry byte for byte (the file's raw
bytes are compared, so a line-ending change is `DRIFT`); exit 1 is `DRIFT`; exit 2 is a refusal
(see above).

## Counts

### Overall

| Metric | Count |
| --- | ---: |
| Textbook chunks scanned (`textbooks_fts MATCH 'паронім*'`) | 117 |
| Textbook chunks yielding at least one pair | 43 |
| Textbook source files yielding verified pairs | 14 |
| МійКлас pages acquired and parsed | 5 |
| **Verified unique paronym pairs (`pairs`)** | **173** |
| Verified pairs with at least one source-quoted meaning | 68 |
| Total verified source attestations | 298 |
| Distinct VESUM-verified member words | 311 |
| Unverified pairs routed to `unverified` | 19 |

### Verified pairs by source overlap

| Source coverage | Unique verified pairs |
| --- | ---: |
| Textbooks only | 111 |
| МійКлас only | 33 |
| Both textbooks and МійКлас | 29 |
| **Total unique verified pairs** | **173** |

### Verified pairs per source file

| Source file | Type | Verified pairs |
| --- | --- | ---: |
| `miyklas-5-klas-slovnyk-paronimiv` | miyklas | 44 |
| `10-klas-ukrajinska-mova-avramenko-2018` | textbook | 38 |
| `uni-ukrmova-lexicology-filon-khomik-2010` | textbook | 24 |
| `10-klas-ukrmova-glazova-2018` | textbook | 20 |
| `5-klas-ukrmova-golub-2022` | textbook | 19 |
| `7-klas-ukrmova-avramenko-2024` | textbook | 18 |
| `11-klas-ukrajinska-mova-glazova-2019` | textbook | 16 |
| `5-klas-ukrmova-avramenko-2022` | textbook | 16 |
| `6-klas-ukrmova-avramenko-2023` | textbook | 14 |
| `5-klas-ukrmova-zabolotnyi-2023` | textbook | 12 |
| `10-klas-ukrmova-karaman-2018` | textbook | 11 |
| `6-klas-ukrmova-litvinova-2023` | textbook | 8 |
| `miyklas-10-klas-paronimy` | miyklas | 8 |
| `11-klas-ukrajinska-mova-avramenko-2019` | textbook | 7 |
| `miyklas-5-klas-paronimy` | miyklas | 6 |
| `miyklas-6-klas-paronimy` | miyklas | 6 |
| `miyklas-11-klas-paronimy` | miyklas | 5 |
| `uni-ukrmova-sulm-attestation-vspu-2021` | textbook | 3 |
| `8-klas-ukrmova-avramenko-2025` | textbook | 1 |

## A1 word-card coverage

Measured only against [`registry/atlas/a1-v1-inventory.json`](../../registry/atlas/a1-v1-inventory.json).
The builder opens that file directly and stops with `A1InventoryError`, naming the file, when it
is missing or unreadable, is not JSON, or has a row without a unique non-empty `id`, a valid
`mapping` or a string `key`. Slice allocation manifests are not read: their validation belongs
to the canonical Atlas slice loaders, not to this registry.

| A1 denominator | Total | With ≥ 1 verified paronym |
| --- | ---: | ---: |
| A1 inventory resolved lemmas (`mapping.lemma`) | 714 | **13** (1.8%) |
| A1 inventory single-token vocabulary keys | 1,112 | **14** (1.3%) |

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
2. **Meanings present on 68 / 173 pairs:** Dictionary blocks (`miyklas-5-klas-slovnyk-paronimiv`,
   `5-klas-ukrmova-zabolotnyi-2023`, `6-klas-ukrmova-avramenko-2023`,
   `7-klas-ukrmova-avramenko-2024`) provide short meanings and examples for both members;
   exercise lists (`10-klas-ukrajinska-mova-avramenko-2018`,
   `11-klas-ukrajinska-mova-glazova-2019`) attest the pair without inline glosses, so the
   word-card builder will fall back to each card's own СУМ-20 / ВТС definition for the remaining
   105 pairs.
3. **19 unverified pairs withheld from `pairs`:**
   - 1 multiword expression (`на протязі | протягом`, `multiword_not_in_vesum`).
   - 1 textbook PDF typo (`мимохіть | михохідь` in `10-klas-ukrmova-glazova-2018`, caught by
     VESUM as `not_attested_in_vesum`).
   - 8 pairs containing a member marked `bad` / nonstandard or absent in VESUM clean forms
     (`бережливий`, `вимисел`, `вникати`, `віла`, `дерзати`/`терзати`, `криштальний`,
     `путати`/`путає`).
   - 9 same-meaning variants by СУМ-20 (`same_meaning_variant`): `будівельник | будівник`,
     `геройський | героїчний`, `копіткий | кропіткий`, `листопад | падолист`,
     `музикальний | музичний`, `плаский | плоский`, `повідь | повінь`,
     `програмний | програмовий`, `слизняк | слимак`.
   - Residual: the direct-reference rule misses variants whose СУМ-20 article defines one member
     through a third word or with a bare synonym (`клопіткий`, `раяти` "Радити",
     `принадливий` "Те саме, що принадний") or that have no mirror article (`капля`). These
     stay in `pairs` until a rule that follows such chains is approved.
4. **Continuation chunks without `паронім*`:** The textbook query scans only chunks matching
   `textbooks_fts MATCH 'паронім*'`. Multi-chunk discussions where an exercise continues onto a
   later chunk without repeating the stem `паронім*` (e.g. `uni-ukrmova-prof-haluzynska-2006_s0038`)
   are intentionally excluded by the single-query scope.
5. **Extractor tool residuals (owner: the `scripts/atlas/paronyms` owner, `claude-opus-5-5`).**
   Review of the predecessor PRs found four classes of held-out synthetic input that the
   extractor mishandles. None of them occurs in the pinned corpus, so none reaches a published
   record; the corpus pin above keeps the tool from running on any input where they could.
   They must be fixed before the extractor is certified on another corpus:
   - a bare or numbered heading after a parsed `ГРУПИ ЛЕКСИКИ` table is dropped
     (`extractor.py`, table-tail handling);
   - instruction cues: a prohibition, or an instruction aimed at the next exercise, still
     activates a paronym cue (`extractor.py`, cue matching);
   - the СУМ-20 header-token test is too lax (`Знак.`) and too strict (`тільки одн.`,
     `у́ється, недок.`) (`build.py`, `_is_sum20_header_token`);
   - gloss names: a capitalised proper name (`Шевченка`) is lower-cased to an unattested key,
     and a hyphenated place name (`Івано-Франківська`) is cut (`build.py`, `_gloss_words`).
6. **Live `sources.db` indexing:** `registry/miyklas/paronyms-raw-v1.json` is not yet indexed in
   `data/sources.db`; indexing it into a new `sources.db` generation remains a separate
   primary-checkout driver action if full-text MCP search over МійКлас is wanted later.
