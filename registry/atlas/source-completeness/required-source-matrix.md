# Required word-card source matrix

Issue: #10512. Programme: #8977. Census obligations: #9401.
Accountable owner: the existing open-model-data driver in stream #6321.

Status: UNFROZEN. This authored requirements matrix preserves WC-S01 through
WC-S10. It is not a complete-data receipt or approval of a smaller denominator.
Hashing this file freezes its bytes only. AC-01 also requires the source editions,
published ranges, applicable fields, lexical universe, and individual units.
Those inputs remain unresolved wherever listed below.

## Denominator and source units

The denominator is every required unit in the approved source editions and
published ranges, across the approved lexical universe. A populated local table,
pilot, current cache, or current Atlas catalogue cannot define that denominator.
An independently enumerated source index must establish ordered unit membership.

The matrix IDs below identify source requirements, not individual dictionary
entries. Every source unit still needs its own source-visible key, edition or
snapshot, locator, and content digest. Local database row IDs locate a snapshot;
they do not establish persistent cross-snapshot lexical identity. Preserve
homonyms and senses separately, following the existing word-card identity rules.

The lexical-universe manifest, its digest, and its approval locator are unresolved
under gap G-UNIVERSE. No pilot or consumer list substitutes for that manifest.
The original #9401 membership manifest for all 123 legacy cases is unresolved
under G-LEGACY. Retain the obligation at 123; do not invent member identities,
sample it, or substitute a reconstruction from a different consumer version.

## Required source and field coverage

Repository locators below are discovery paths. They establish where to inspect
local material, not that acquisition, raw custody, or completeness has passed.
Every unresolved boundary has owner open-model-data unless a specialist owner is
identified in the linked source-gap issue. All boundaries require G-UNIVERSE.

| Matrix ID | Roles | Required source and applicable fields | Unit and local discovery locator | Edition, range, or evidence gap |
| --- | --- | --- | --- | --- |
| SRC-ULIF | WC-S01, WC-S07, WC-S09, WC-S10 | ULIF identity, morphology, stress variants, synonym and antonym groups, phraseology, source-visible labels and citations | Register position plus homonym; `data/sources.db:ulif_dictua_entries`, `ulif_dictua_sections`; raw references in `data/lexicon/cache/ulif_raw.sqlite` | G-ULIF: independently freeze the published register and reconcile every raw reference and section; retain parser failures. Dependencies #8400, #8428, #9401. |
| SRC-VESUM | WC-S01, WC-S09, WC-S10 | Lexical identity, morphology, form variants, markers; stress is not applicable | Source lexeme and form record; `data/vesum.db:forms_all`, `form_markers`; `scripts/config/vesum_source.lock.json` | G-VESUM: bind the installed form store to its source lock and enumerate the required source records. Exact linking only. #9401. |
| SRC-SUM20 | WC-S01, WC-S07, WC-S09, WC-S10 | Modern definitions, senses, labels, attested headword stress, citations | Published article and sense; `data/sources.db:sum20_articles`, `sum20_senses`, `sum20_citations`, `sum20_crawl_outcomes` | G-SUM20: establish the current published edition/range independently of the cache; preserve quarantine and acquisition/parser gaps. #8579, #9401. |
| SRC-VTS | WC-S01, WC-S09, WC-S10 | Modern definitions, numbered senses, labels, citations | Dictionary article and numbered sense; `data/sources.db:slovnyk_me_entries`, selector `dictionary_slug='vts'` | G-VTS: edition, required article range, source register binding, complete captures, and sense parsing remain to be established. #9401. |
| SRC-GRAC | WC-S02, WC-S09, WC-S10 | Literal examples, collocations, descriptive frequency, corpus version, filters, denominator, period, genre, region where available | Concordance occurrence or frequency query; Sources MCP `query_grac`; `https://www.uacorpus.org/` | G-GRAC: freeze corpus snapshot, required queries and filters, denominator, and retained result locators. Accessible query results do not prove corpus completeness. #9401. |
| SRC-LITERARY | WC-S02, WC-S06, WC-S10 | Authentic examples and citations with work, passage, and applicable context | Work and ordered passage; `data/sources.db:literary_texts` | G-LITERARY: enumerate required works, editions, passage boundaries, and complete raw custody. #9401. |
| SRC-TEXTBOOK | WC-S02, WC-S06, WC-S10 | Authentic examples, learner selection and construction evidence | Book, edition, section, and passage; `data/sources.db:textbooks`, `textbook_sections`; `registry/lexicon/source-inventory/` | G-TEXTBOOK: reconcile required book editions and ordered passages against authentic originals. A chunk count is not a page or book count. #9401. |
| SRC-PRAVOPYS | WC-S03, WC-S09, WC-S10 | Orthographic rule, edition, paragraph/page, source spelling variants and status | Edition and paragraph; `data/sources.db:pravopys_sources`, `pravopys_sections`, `pravopys_paragraphs`; Sources MCP `query_pravopys` | G-PRAVOPYS: validate edition bytes and the ordered published paragraph inventory independently of the parsed store. Local edition metadata alone does not discharge this gap. #9401. |
| SRC-ANTONENKO | WC-S04, WC-S09, WC-S10 | Condemned expression, correction direction, applicable sense and register, source passage | Discussion and full-book passage; `data/sources.db:style_guide`; `textbooks` with `source_file='antonenko-davydovych-yak-my-hovorymo'` | G-ANTONENKO: freeze edition and full-book boundaries; reconcile both structured discussions and prose. The structured index cannot replace the book. #9401. |
| SRC-KARAVANSKY | WC-S04, WC-S05, WC-S09, WC-S10 | Cited usage/correction, historical or specialist evidence within the named dictionary's role | Edition, dictionary entry, and sense; Sources MCP `search_slovnyk_me`; existing Atlas lineage is a consumer locator only | G-KARAVANSKY: identify the required books, editions, source unit inventories, and authentic captures. Do not merge different books into one source role. #8791, #9401. |
| SRC-UAGEC | WC-S04, WC-S09, WC-S10 | Human-annotated correction spans, direction, context and annotation metadata | Document and correction span; `data/sources.db:ua_gec_errors`; Sources MCP `search_ua_gec_errors` | G-UAGEC: bind upstream release and required document/span inventory; preserve phrase scope. Corrections are not unsupported whole-word labels. #9401. |
| SRC-ESUM | WC-S05, WC-S10 | Etymology, volume, page, source entry, historical layers | Volume, page, and entry; `data/sources.db:esum_etymology`, `esum_etymology_meta` | G-ESUM: freeze required volumes/edition and reconcile page and entry coverage against authentic source bytes. Preserve damaged/OCR and parser gaps. #9401. |
| SRC-HRINCHENKO | WC-S05, WC-S10 | Historical attestation and historical meaning in its evidential role | Edition, volume, page, and entry; `data/sources.db:grinchenko`; Sources MCP `search_grinchenko_1907` | G-HRINCHENKO: bind edition, source entry inventory, locators, and captures; historical attestation is not modern recommendation. #9401. |
| SRC-PHRASEOLOGY | WC-S05, WC-S09, WC-S10 | Expression, definition, ordered groups, labels, literal citations | Dictionary edition, expression, and sense/group; `data/sources.db:frazeolohichnyi`; ULIF remains SRC-ULIF | G-PHRASEOLOGY: bind dictionary edition and published entry range; reconcile groups and citations without clipping. #9401. |
| SRC-SPECIALIST | WC-S05, WC-S09, WC-S10 | Qualified regional, specialist, and other dictionary evidence in each source's role | Separate dictionary, edition, entry, sense, and passage; existing source inventory and Sources MCP `search_slovnyk_me` | G-SPECIALIST: enumerate required dictionaries first; this row is an unresolved requirement family, not a claim that one source contains all fields. Retain #9401's inherited #6460 layers. |
| SRC-PULS | WC-S06, WC-S09, WC-S10 | Cited learner selection, level, guideword and construction where supplied | Source row with applicable subject; `data/sources.db:puls_cefr`; Sources MCP `query_cefr_level` | G-PULS: freeze source snapshot and required lexical coverage; an unresolved sense-to-level mapping stays unresolved. #9401. |
| SRC-CURRICULUM | WC-S06, WC-S10 | Cited textbook/curriculum selection for an applicable sense or construction | Versioned curriculum or source-inventory record and its authentic source passage; `curriculum/`, `registry/lexicon/source-inventory/` | G-CURRICULUM: freeze applicable inventory and cited source locators. Model-written examples are prohibited. #9401. |
| SRC-STRESS | WC-S07, WC-S09, WC-S10 | Attested stress alternatives bound to lexeme, POS/sense and inflected form | Qualified source entry/form and snapshot; Sources MCP `verify_stress`; `scripts/verification/stress.py`, `scripts/data/stress_overrides.yaml` | G-STRESS: establish each qualified stress source's version, required form range, provenance and homonym bindings; retain conflicts. No human audio denominator. #9401. |
| SRC-SUM11 | WC-S08, WC-S09, WC-S10 | `soviet_colonization_context`, source-located contrasts, substantiated distortion labels, risk and keywords | Historical entry plus independent modern or pre-Soviet comparison locator; `data/sources.db:sum11` | G-SUM11: freeze edition and historical range; reconcile contrast evidence independently. Never supplies modern meaning, norm, stress, standalone examples, or practice answers. #9401. |
| SRC-LEGACY123 | WC-S01, WC-S09, WC-S10 | All original legacy not_found cases, exact ULIF and VESUM linkage, consumer version and provenance | Original #8337 membership and #9401 AC-03; membership locator unresolved | G-LEGACY: recover the original 123-case manifest and source/consumer version before per-case reconciliation. The obligation remains 123 even if membership is unavailable. |

WC-S09 and WC-S10 apply across the matrix. They are binding and provenance
requirements, not additional physical corpora. For each applicable assertion,
retain its source subject, sense/POS, homonym, edition, snapshot, exact locator,
quality state, alternatives, disagreements, removal dependencies, and consuming
Atlas, Practice, or dataset projection. Aspect, government, preposition/case, and
common combinations need their own cited grammatical evidence.

G-SPECIALIST retains the inherited #6460 obligations separately: `newsum`,
`proverbs`, `linguistic_norm`, `khreshchatyk`, `orthography`, `holoskevych`,
`orthoepy`, `slang_lviv`, `voloschak`, and `foreign_shtepa`. These are historical
discovery keys, not authenticated edition identities. The inherited `vts`,
`synonyms`, `phraseology`, `davydov`, and `hrinchenko` layers also remain required;
their edition and source-record correspondences to matrix rows require evidence.
None disappears because its acquisition or current consumer coverage is unknown.
The authority-book acquisition dependency #8791 separately retains Пономарів,
Городенська, and a paronym dictionary. Exact book and edition selection follows
the existing acquisition issue; this matrix does not invent titles or editions.

## Required accounting

Account separately for acquisition, authentic raw custody, parsing, assertion
admission, and each consumer projection. A field being absent from a parsed
record establishes none of the preceding stages. Use the required range states:

- `verified-complete` requires the independently established source denominator,
  ordered unit coverage, authentic bytes and digest checks, and usable applicable
  fields. Lower-stage counts alone cannot establish it.
- `missing` records an identified required unit missing at a named stage.
- `corrupt` records a damaged capture or digest failure with its evidence.
- `quarantined` records retained material and the explicit reason it cannot be
  used. Quarantine is not absence or admission.
- `genuinely_absent` requires positive source evidence within a verified required
  range. Missing acquisition, damaged capture, and parser loss never qualify.

An unknown range stays explicitly unpartitioned with its gap and owner; do not
invent units or silently put it in one of the five partitions. A `not_applicable`
field needs a source-role reason and is accounted outside genuine absence.
Required unresolved fields keep their named source gap and owner.

## Acceptance evidence and current blocking inputs

| Criterion | Required evidence | Blocking input |
| --- | --- | --- |
| AC-01 | Approved edition/range and lexical-universe freeze, matrix hash, ordered per-unit manifest and locators | G-UNIVERSE, source-specific boundary gaps, G-LEGACY |
| AC-02 | Exhaustive nonoverlapping range partitions and separate five-stage accounting | Independently enumerated source units and raw/capture/parser lineage |
| AC-03 | Authentic usable applicable material, gaps and owners, source-backed absence and not-applicable evidence | Unresolved acquisition, capture, parser, admission and subject-binding gaps |
| AC-04 | Outside-author reconciliation against authentic evidence, ordered counts, duplicate/missing checks and digests | Independent enumerator/reviewer and source-side manifests; assembler output is insufficient |
| AC-05 | Complete-data receipt linked to every criterion and exact inputs under `batch_state/reports/` | AC-01 through AC-04; an incomplete diagnostic receipt cannot pass Phase 1 |

All five criteria remain unmet until their evidence is supplied and independently
reconciled. Phase 4 gold and Phase 5 certification remain blocked. Local tests
provide regression evidence only. No public deployment or cutover is authorized.

Generated inventories, diagnostics, and reconciliation receipts remain ignored
under `batch_state/reports/`; do not commit them as authored registry inputs.

## Structural accounting procedure

Use the [ordered manifest contract](manifest-contract.md) and
`scripts.projects.open_model_data.source_completeness_manifest` to bind supplied
source-side indexes and account independently for stages and consumer projections.
Unknown whole ranges and the unavailable original 123-case membership remain
explicit diagnostic obligations. The producer's structural receipt does not freeze
this matrix's unresolved choices, establish authentic source completeness or
satisfy any of the five acceptance criteria without their independent evidence.
