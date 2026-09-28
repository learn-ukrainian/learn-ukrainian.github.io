# Word cards C0 — card schema (spec v1, draft for review)

- **Issue:** #8978 (schema) under epic #8977; identity contract for #8334 in [`identity.md`](identity.md); worked examples in [`worked-examples.md`](worked-examples.md); migration outline in [`migration.md`](migration.md).
- **Machine-readable schema:** [`schemas/word-card-v1.schema.json`](../../../schemas/word-card-v1.schema.json) (JSON Schema 2020-12). The ten example cards in [`examples/`](examples/) validate against it; `tests/validate/test_word_card_examples.py` proves that and proves AC-03 (source removal recomputes value and state).
- **Status:** draft, 2026-09-28, author Claude (Fable 5.1). Review of record: Astra (GPT, design) and Gemini (Ukrainian). Open design questions are listed in §16 and are not decided here.
- **Approved inputs:** proposal #8976 (operator go 2026-09-27) with both advisor reads; #8978 advisor requirements; #8983 (practice eligibility) and #8980 (takedown) as constraints; operator decisions of 2026-09-27 on #8979 (content stays, teacher consent, takedown via GitHub issues, no outreach).
- **Evidence rule:** every statement about current data below comes from read-only queries against `data/atlas.db`, `data/sources.db` and `data/vesum.db` run on 2026-09-28; §17 lists them.

## 1. What a card is

A **card** is an assembled view over retained, cited **assertions**. Choosing the value a page or an exercise shows never deletes the alternatives or their sources. Three products read the same cards: Word Atlas pages, practice generators and the open dataset.

- One card per **lexeme** (a word with one paradigm, one stress pattern or declared doublet, one POS and one sense family), per **multiword expression** (MWE) and per **proper name**. Never one card per spelling. Today `atlas.db` has exactly one article per bare spelling: 27,128 articles, 27,128 distinct lemmas, so `замок` is one article with gloss `castle / lock`, stress only `за́мок` and castle-only synonyms.
- **Senses** are rows under a card. Meanings, relations and examples attach to senses, not to the card.
- Cards are **derived**: `atlas.db = build(sources.db, vesum.db, curation overlay, rules)`. Nothing is hand-edited in `atlas.db`; curation lives in the overlay (§12) and is replayed by the build (§13).
- Quality is **several dimensions**, not one flag (§9). Corroboration (how many independent lineages agree) is separate from fitness for practice (#8983).

## 2. Entities

```
source_snapshots ──< assertions >── cards ──< senses
                        │            │  └──< links (typed, to cards or senses)
                        │            └──< card_ids (mapping table, merged_into redirects)
                        └──< derivations (exercises, distractors, glosses, dataset rows, curriculum embeds)
overlay (git) ── replayed by build ── build_manifest (input hashes, rules version)
```

## 3. Source records and snapshots

A **snapshot** is the concrete edition or harvest of a source that an assertion was extracted from. It is recorded once and referenced by id.

| source_id (register) | snapshot_id form | what fixes it | measured on 2026-09-28 |
| --- | --- | --- | --- |
| `ulif` | `ulif@ulif-dictua-v2/2026-09-22..2026-09-27` | `ulif_dictua_entries.parser_version`, `retrieved_at` range, per-entry `content_sha256` and `raw_response_ref` (`sha256:…` into `data/lexicon/cache/ulif_raw.sqlite`) | 262,788 rows `homonym_checked=1`, all `status='ok'`, all `parser_version='ulif-dictua-v2'`, `retrieved_at` 2026-09-22T07:16:23Z … 2026-09-27T23:36:03Z; 6,449 legacy rows `homonym_checked=0` (6,446 `not_found`, 3 `ok`; 6,425 of them from parser `1.0`) are never a source |
| `vesum` | `vesum@53923150073b4fc7` | `vesum_build_metadata.canonical_jsonl_sha256` = `53923150073b4fc7bee419fe7b071acbe17b6a9aba76cfb2d0336c95f5188680`, `schema_version=vesum-reingest-v1`, `marker_policy_version=v1` | 442,458 entries (`entry_id`), 422,656 distinct lemmas, 6,970,759 form rows (`forms_all`), 6,632,807 in the `forms` view (markers `bad`, `obsc`, `subst` hidden) |
| `sum20` | `sum20@wordid` | `sum20_articles.content_sha256`, `fetched_at`, `parser_version` | 100 articles, 168 senses, 699 citations (crawl paused) |
| `atlas0` | `atlas0@manifest-0.1/2026-09-11` | `manifest_metadata` (`version "0.1"`, `generated_at 2026-09-11T10:12:36+00:00`) | the pre-card store: 27,128 articles, 193,530 enrichment rows, 28,295 aliases, 3,690 related entries; used only as a migration snapshot (see `migration.md`) |
| others (`kaikki`, `wiktionary`, `puls`, `frazeolohichnyi`, `grinchenko`, `sum11`, `textbooks`, `teacher_materials`, …) | `<source>@<table or file>/<date or hash>` | table row ids in `sources.db` or file hashes | e.g. `frazeolohichnyi` 24,683 rows; `puls_cefr` 5,939 rows (A1 962, A2 1,386, B1 2,164, B2 1,194, C1 233); `wiktionary` 50,278 rows |

Rules:
- A snapshot never changes. A re-harvest is a new snapshot; assertions from the old one become `superseded` when the new build replaces them, and stay queryable.
- `atlas0` enrichment payloads carry the source label but not the source snapshot (e.g. `enrichment.stress` from `kaikki/Wiktionary (CC BY-SA 3.0)` has no dump date). Assertions migrated from them get `extraction_version = atlas0-migration` and `extraction_confidence = medium` until re-extracted from the source itself.

## 4. Assertions

An assertion is one (subject, field, value) claim by one source at one locator. It is the unit of citation, of suppression and of dependency tracking. JSON shape: `$defs/assertion` in the schema.

| property | meaning |
| --- | --- |
| `assertion_id` | `wa_` + first 24 hex chars of `sha256(canonical JSON of {source_id, snapshot_id, locator, subject, field, value_norm, extraction_version})`. Deterministic: a rebuild from the same inputs mints the same ids (proved by `test_generator_reproduces_committed_examples`). |
| `subject` | `{kind: card|sense|link, id}` |
| `field` | card field (`spelling`, `stress`, `pos`, `grammatical_label`, `gender`, `aspect`, `paradigm`, `cefr`, `frequency`, `heritage_status`, `transliteration`, `english_gloss`, `spelling_variants`, `mwe_form`, `mwe_frame`) or sense field (`definition_uk`, `gloss_en`, `sense_label`, `register`, `synonyms`, `antonyms`, `examples`, `russification_exposed`, `collocations`). This is the field list of the #8976 card table. |
| `value` | as extracted: string, list or object. Never model-written Ukrainian. |
| `value_norm` | comparison form (NFC, combining acute U+0301 kept, lower-cased for common words, whitespace and trailing punctuation normalised). Agreement is decided on `value_norm`. A declared set (a source that itself lists two stresses) is written `a|b`. |
| `source_id` | key into `docs/sources/permissions-register.yaml` (#8979, register `schema_version: 2`, `register_date: 2026-09-28`): `ulif`, `vesum`, `sum20`, `slovnyk_me`, `synonyms_dictionary`, `grinchenko`, `sum11`, `grac`, `ua_gec`, `ukrajinet`, `wiktionary`, `kaikki`, `dmklinger`, `goroh`, `mphdict`, `balla`, `puls`, `ubertext_freq`, `r2u_e2u`, `wikidata`, `ukrainian_word_stress`, `teacher_materials`, `course_authored`, `wikipedia`, `esum`, `textbooks`, `frazeolohichnyi`, `antonenko_style_guide`, `ulp_private`. Sources shown in the Atlas but not yet registered (ВТС, Караванський, orthographic dictionaries, Приповідки, МійКлас, Штепа, Культура слова, literary corpus) are listed in the register's `open_questions` and need entries before C1. |
| `snapshot_id` | §3 |
| `locator` | where in the snapshot. Grammar per source: `ulif:entry:<id>[/section:<id>] [<column or rows[i][j]>]`, `vesum:entry:<entry_id> [<column>]`, `sum20:wordid:<n>/sense:<k>`, `sources.<table>:id:<n> [<column>]`, `atlas0:enrichment:<slug>/<section> [<json path>]`, `textbook:<doc>::<section>` (as today's `article_provenance.source_locator`, e.g. `1-klas-bukvar-bolshakova-2018-1::1-klas-bukvar-bolshakova-2018-1_s0012`). |
| `extraction_version` | parser or transformer version (e.g. `ulif-dictua-v2`, `ulif paradigm-row headword recovery v1`, `atlas0-migration`). |
| `extraction_confidence` | `high` (value read from its dedicated field), `medium` (recovered or split from a compound field), `low` (markup damage). Measured ULIF cases: 12,899 checked entries have `canonical_headword=''` (header not parsed); 12,095 of them have a paradigm section whose first data row carries the stressed lemma (`замо́к` for `ulif:entry:76793`), so the headword is recoverable at `medium`; 27 have no section at all. Phraseology `terms[].text` carries doubled accents from the source markup (`будува́́ти пові́́тря́́ні за́́мки .`), so `mwe_form` from ULIF is `low` with a normalised `value_norm`. |
| `producer` | `{kind: source_extract|generator|teacher|curator|estimator, name, version, produced_at}`. Generated and teacher content is an assertion like any other, with its producer named (advisor requirement). Today's `enrichment.cefr` rows labelled `estimated (GRAC frequency)` (3,862 rows) become `estimator` assertions; `learner_english_gloss` (3,282 translation rows) become `generator` assertions. |
| `review` | `{status: none|sampled|reviewed|rejected, lane, record, date}`: the reviewing lane for generated/teacher/curated content. |
| `licence_ref` | `{register_source_id, register_version, appears_in?}` (§10). |
| `independence_group`, `tier` | copied from the register at build time (§9.1). |
| `mapping` | per-assertion identity confidence: how sure the build is that this source row belongs to this card. Missing means `high`. `low`/`unresolved` assertions are retained but do not vote (§8). Example: PULS rates the spelling `замок` A2 (`puls_cefr.id 4340`); it does not say which замок, so the assertion is mapped to both cards at `medium`. |
| `status` | `active`, `suppressed` (with `suppression_ref`: overlay id or takedown issue URL), `superseded`. |

Suppression is a status, not a deletion: the internal store keeps the row so the takedown report (#8980) can say what was removed and reimport cannot bring it back (the overlay entry outlives the snapshot).

## 5. Cards, opaque ids, the mapping table and redirects

- `card_id`: `wc_` + 12 Crockford base32 characters (`[0-9a-hjkmnp-tv-z]`), random at minting, no semantics, never reused. `sense_id`: `ws_` + 12. Link ids `wl_` and assertion ids `wa_` are content-derived (§4).
- `card_ids` **mapping table** (in `atlas.db`, also exported): `card_id, card_kind, key_at_creation (spelling, stress_patterns, pos, paradigm_key, mwe_key, source_keys), created_in_build, state, merged_into`. The key at creation is *matching evidence*, recorded so a later build can find the same card again; it is not identity. Renaming a spelling (2019 orthography) or correcting a stress does not change the id.
- **Redirects**: a merged card gets `state = redirected`, `merged_into = <surviving card_id>`; its senses get `merged_into` sense ids. Every consumer that holds a card id (learner progress, exercises, dataset rows, curriculum embeds) resolves through `merged_into` before use. A redirected card is never deleted and never re-minted.
- **Spelling aliases**: `slug`/spelling stays an alias (today's `aliases` table: 27,128 `transliteration`, 821 `canonical`, 344 `inflected_form` rows). A spelling with several cards resolves to a disambiguation list; the URL scheme itself is #8334 AC-02 and is an open question (Q10).
- Card-level `state`: `active`, `redirected`, `suppressed`. Field-level states are in §8.

## 6. Senses

- `senses[]`: `{sense_id, order, state: active|redirected|suppressed|unsplit, merged_into, sense_map[], fields{}}`.
- `sense_map` records which **source sense units** feed the sense: `ulif:section:<id>` (a ULIF synonym group is sense-bound: `замок` homonym 3 has three groups, `synonyms:1` = zipper `БЛИ́СКАВКА …`, `synonyms:2` = lock `ЗАМО́К (пристрій для замикання дверей), ЗАПІ́Р рідше, ЗА́ПІРКА рідко; КОЛО́ДКА діал.`, `synonyms:3` = latch `ЗА́ЩІПКА …`), `sum20:wordid:<n>/sense:<k>` (`sum20_senses.sense_order`), `vts:<spelling>#<I|II>/<n>` (numbered senses inside today's `definition_cards` payloads), `ulif:entry:<id> sense_gloss[i]` (ULIF's `sense_gloss` is one parenthesised list: for `ключ` homonym 1 it names six senses separated by `;`).
- Alignment across sources is a curation decision, done automatically only when a source has exactly one unit. Units that cannot be aligned go to one sense with `state = unsplit`; unsplit senses are shown on the page (thin cards are never hidden) and excluded from practice modes that need sense alignment (#8983).
- Sense-level fields (`definition_uk`, `gloss_en`, `synonyms`, `antonyms`, `examples`, `register`, `russification_exposed`, `collocations`) resolve exactly like card fields (§8).

## 7. Multiword expressions and typed links

### 7.1 MWE cards
- `card_kind = mwe`, own key: `mwe_key = <first source locator>|<normalised form>`, e.g. `ulif:entry:76792/section:96932|будувати повітряні замки`. Normalised form: NFC, accents stripped, lower-case, punctuation and slot markers (`кого, чого`, bracketed optional parts) kept as slots in `mwe_frame`.
- One MWE card even when a source lists the idiom under several headwords: ULIF lists «будувати повітряні замки» under `замок` homonym 2 (section 96932) and under `повітряний` (section 218523) with identical text.
- Scale in ULIF: 8,131 phraseology sections; 4,820 distinct heads by the first 60 characters of `text` (an upper bound on cards from ULIF, because variants such as `тримати (держати) за сімома замками` are one section). `sources.frazeolohichnyi` (24,683 rows) and today's `enrichment.idioms` (via slovnyk.me) carry the same dictionary text (§9.1).
- Existing `atlas.db` multiword articles (492 `multiword_term`, 124 `expression`, 23 `phraseologism`) become MWE cards with `atlas0` keys.

### 7.2 Typed links
`links[]`: `{link_id, type, from, to, role, assertion_ids[], state}`. Types: `aspect_pair` (roles `imperfective`/`perfective`; two cards, never one), `component_of` (MWE → component card, role `anchor` or `component`; ULIF anchors carry the target's own id, e.g. `dictua.aspx?uid=47336` = `ЗА́МОК` castle, `uid=47335` = `ЗАМО́К` lock), `stress_variant_of`, `homograph_of`, `synonym`, `antonym` (ULIF antonym rows are `paired_sense` objects with `left`/`right` sides: `БРАТИ` ↔ `ДАВАТИ` in `ulif:entry:28535/section:27648`), `see_also`, `russification_contrast`. Every link cites the assertions that support it; a link with no active supporting assertion is `suppressed` by the build.

## 8. Field resolution and quality states

For each (subject, field) the build computes a **field resolution** `{state, selected, values[], independence_groups_agreeing, resolution_ref}` from the assertions. Rules `rules-v1-draft` (reference implementation: `resolve()` in `examples/build_examples.py`, exercised by the test):

1. Take `active` assertions whose `mapping.confidence` is `high` or `medium`. If none: `suppressed` when any assertion for the field is suppressed, otherwise the field is absent (an `unverified` resolution with no values is emitted only for visibility).
2. Voting assertions are tier 1 and tier 2 (§9.1). If only tier-3 assertions exist (generated, teacher-unreviewed, estimated, curated) the state is **`unverified`** and the first tier-3 value is shown with its producer.
3. Group voting assertions by `value_norm`. Count **distinct independence groups** per value; groups with unknown lineage (marked `?`) never count.
4. One value: ≥2 groups → **`verified`**; 1 group → **`single-source`** (several assertions from one lineage are still single-source: ULIF + slovnyk.me + `frazeolohichnyi` for an idiom).
5. Several values: an overlay `resolve` entry picks the shown value and records `resolution_ref`; the losing values stay in `values[]`. Else, if a tier-1 source itself declares the set (`value_norm` `броня́|бро́ня` from VESUM's comment `xv2 броня́; бро́ня`, or ULIF's headword `по́ми́лка` with two accents) and the set equals the observed values → **`variant`** (both correct, all shown). Else → **`conflict`**: `selected = null`, nothing shown as fact, the field is listed for review and excluded from practice.
6. Card-level: `redirected` (merged_into set) and `suppressed` override every field state in public outputs.

States are therefore: `verified`, `single-source`, `variant`, `conflict`, `unverified`, `suppressed` (field), plus `redirected`, `suppressed` (card). `variant` is distinct from `conflict` on purpose (advisor requirement): `по́ми́лка` is one word with two permitted stresses, `вряди́-годи́` (ULIF) vs `вряди́-го́ди` (ukrainian-word-stress) is a disagreement.

Measured today (Atlas `enrichment.stress` vs ULIF headword, single-homonym spellings, polysyllables, same letters): 14,509 comparable, 14,419 agree, 12 are ULIF doublets containing the Atlas stress (`variant`), 78 differ. Most of the 78 are identity artefacts, not conflicts: `варення` (ULIF has two homonyms, `ва́рення` (дія) and `варе́ння`), `бере` (ULIF `бе́ре`, a noun; Atlas `бере́`, a verb form), `всього` (ULIF adverb `всього́`; Atlas `всьо́го`), `братів` (adjective vs genitive plural). `вряди-годи` is a genuine conflict (one VESUM entry, one ULIF homonym).

## 9. Quality dimensions

### 9.1 Source independence: groups and tiers
Corroboration counts **lineages**, not labels. Provisional table (to be recorded per source, and per field where lineage differs, in the #8979 register; Q3):

| group | sources | tier | evidence / note |
| --- | --- | --- | --- |
| `G-ULIF` | `ulif`, `sum20`, `frazeolohichnyi`, `slovnyk_me` (as a mirror of the same dictionaries) | 1 | ULIF publishes СУМ-20; ULIF phraseology text for «будувати повітряні замки» is identical to `frazeolohichnyi` row 568 and to the slovnyk.me idiom payload (definition and the М. Зарудний citation), so they are one lineage |
| `G-VESUM` | `vesum` | 1 | independent morphological dictionary (dict_uk) |
| `G-WIKI` | `kaikki`, `wiktionary`, `wikipedia`, `wikidata` | 2 | one community lineage |
| `G-PULS` | `puls` | 2 | CEFR list |
| `G-GRAC` | `grac`, `ubertext_freq` | 2 | frequency |
| `G-KARAVANSKY` | Караванський synonyms (via slovnyk.me) | 2 | separate dictionary; needs its own register entry |
| `G-VTS?` | ВТС (`definition_cards`) | 2 | lineage vs СУМ-11 unknown; `?` = does not corroborate until recorded |
| `G-UWS?` | `ukrainian_word_stress` | 2 | lineage unknown (possibly ULIF-derived); `?` until the register records it |
| `G-GRINCHENKO` | `grinchenko` | 2 | 1907; attests heritage, never modern stress or meaning |
| `G-TEACHER` | `teacher_materials`, `ulp_private` | 3 | reviewed teacher content can be promoted to tier 2 per assertion by `review.status = reviewed` (Q5) |
| `G-PROJECT` | `course_authored`, `learner_english_gloss`, `estimated (GRAC frequency)`, curated side files, generators | 3 | never corroborates |
| `G-SUM11` | `sum11` | 0 | not evidence for any modern field (rule #M-6); only the `russification_exposed` field may cite it, always paired with the modern norm (#8982) |

### 9.2 Identity confidence
Per card (`identity.confidence`) and per assertion (`mapping.confidence`): `high`, `medium`, `low`, `unresolved`; rules in `identity.md` §5. `unresolved` cards exist (thin, honest) but no practice item may depend on them.

### 9.3 Extraction confidence
Per assertion (§4). `quality.extraction_confidence_min` summarises the card.

### 9.4 Linguistic review
Per assertion (`review`) and per card (`quality.linguistic_review`): `none`, `sampled`, `reviewed`, `rejected`, with lane and record. Generated, teacher and curated content needs at least `sampled` by a lane outside the producer's family before it reaches A1–B2 practice (#8976 rule).

### 9.5 Practice eligibility
`quality.practice_eligibility[]`: `{mode, eligible, rules_version, reasons[], sense_id?}`, computed by the eligibility rules of #8983 (per mode: CEFR/frequency band, register exclusions, sense alignment, identity confidence, field state ∈ {verified, single-source}). It is an output of the build, versioned by `rules_version`, never edited by hand. Exercises record the card version and generator version they used (#8983).

**English gloss** (`english_gloss`, `gloss_en`) is a scaffold field with a level policy: shown at A1 by design, never raised from A2 (`level_policy` on the resolution; #8983 advisor requirement). It is not card content for immersion purposes.

## 10. Licence and permission reference per assertion

`licence_ref = {register_source_id, register_version, appears_in?}` points into `docs/sources/permissions-register.yaml` (#8979; delivered on `claude/impl-8979-permissions`, register `schema_version: 2`). The register holds, per source, the rights holder, the terms as found, the citation form to show and the removal route. Operator decisions of 2026-09-27 (register `operator_decisions` d1–d4): all current content stays on the site and in exports; the teacher consents; takedown requests arrive as GitHub issues; no outreach. The register is therefore a **citation and provenance record, not a publication gate**. Exporters read `appears_in` only to keep `internal`-only sources (e.g. `ulp_private`) out of public outputs; they do not withhold registered sources.

Every derived item inherits the `licence_ref`s of the assertions it used (§11), so a dataset row can print its full attribution list and a takedown can find it.

## 11. Dependency links from derived items

`derivations`: `{derived_id: wd_<hash>, kind: exercise|distractor|gloss|relation|dataset_row|atlas_page|search_doc|curriculum_embed, generator, generator_version, input_assertion_ids[], input_card_ids[], output_ref, built_in}`. `derived_id` is the hash of `(generator, generator_version, sorted inputs)`.

- Practice items, distractors and generated glosses record the assertions they read (not only the card), so a suppressed assertion invalidates exactly the items that used it and #8983 regenerates them.
- Dataset rows record inputs so a retracted release (#8980) can list affected rows.
- `curriculum_embed` rows are produced by a scan of `curriculum/` for card text or ids at build time, so the takedown report can list modules that embed affected card text (advisor requirement; how the scan keys text is Q9).

## 12. Curation overlay

The overlay is the only hand-written input. It lives in git (proposed `data/atlas/overlay/*.yaml`, Q11), is keyed by `card_id`, and every entry is replayed by the build as a `curator` assertion with `review` and `producer` filled in.

```yaml
- overlay_id: ovl-2026-09-28-0001
  kind: split                       # merge | split | resolve | variant | suppress | level_override | sense_map | link | identity
  card_id: wc_…legacy…              # for split: the card being split; for merge: the card being merged away
  into: [wc_7k3m9q2xw4pd, wc_c2v8n5rt6yhq]
  author: gemini-agy                # lane or human
  lane: language                    # language | design | operator
  date: 2026-09-28
  evidence: "ulif:entry:76792 родовий за́мку vs ulif:entry:76793 родовий замка́; vesum:entry:128973 xp2 vs 128972 xp1"
  record: "#8334 language-lane read"
- overlay_id: ovl-2026-09-28-0002
  kind: resolve
  card_id: wc_x2j5n8sd1vpc
  field: stress
  assertion_id: wa_…                # the value to show; losers stay in values[]
  rationale: "…"
- overlay_id: ovl-2026-09-28-0003
  kind: suppress
  level: entry                      # source | entry | assertion
  target: "ulif:entry:12345"        # or a source_id, or an assertion_id
  issue: https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/NNNN
```

Kinds: `merge`/`split` (identity, §5 and `identity.md` §7), `resolve` (conflict → shown value), `variant` (declare a doublet when no tier-1 source declares it), `suppress` at source / entry / assertion level (#8980, reimport-proof because it is keyed by source locator, not by row id), `level_override` (CEFR for practice; recorded as a tier-3 assertion with lane), `sense_map` (alignment of source sense units), `link` (assert a typed link with evidence), `identity` (confirm or reject a machine match). Suppression entries are honoured by imports too: a suppressed locator is skipped when a new snapshot is loaded.

## 13. Reproducible build contract

```
atlas.db  =  build( sources.db@S , vesum.db@V , overlay@O , rules@R )
```

- **Pure and deterministic.** Same `(S, V, O, R)` → identical cards, identical ids (`wc_` ids are read from the mapping table, minted only for keys that have none), identical field resolutions. Proof in CI: build twice, compare logical dumps.
- **Build manifest** (`build_manifest` table + `docs/atlas/word-cards/builds/<build_id>.json`): `S` = per-table digests (`ulif_dictua_entries`: count of checked rows, `parser_version`, `retrieved_at` range, sha256 over sorted `content_sha256`; `sum20_articles`: sha over `content_sha256`; other tables: row count + sha over row ids), `V` = `vesum.canonical_jsonl_sha256`, `O` = overlay git commit, `R` = rules semver (`rules-v1-draft` today). The example cards embed such a manifest in `build`.
- **Takedown** (#8980) = add a `suppress` overlay entry → rebuild → diff report (cards, fields, derivations, dataset rows, curriculum embeds affected) → republish every output type. Reimport cannot resurrect a suppressed locator. Correctness fixes (#8729, #8715) do not wait for this: they land as overlay entries or extractor fixes against today's tables.
- **Rollback** = rebuild from the previous `(S, V, O, R)`; nothing else to restore.

## 14. Russification exposed (СУМ-11)

`sum11` is tier 0. It appears only in the sense-level field `russification_exposed`, always as a contrastive object `{imposed: <СУМ-11 text with locator>, norm: <modern assertion id>, distortion_type, both citations}` (#8982), never as `definition_uk`, `stress`, `examples` or a practice answer. `sources.sum11` holds 127,069 rows with `sovietization_risk` and `sovietization_keywords` columns; the `замок` row (`id 29322`) has `sovietization_risk 0`.

## 15. Physical schema sketch (SQLite, for C1)

`source_snapshots(snapshot_id PK, source_id, edition, retrieved_from, retrieved_to, content_digest, extraction_version)` · `assertions(assertion_id PK, subject_kind, subject_id, field, value_json, value_norm, source_id, snapshot_id, locator, extraction_version, extraction_confidence, producer_kind, producer_name, producer_version, produced_at, review_status, review_lane, review_record, review_date, register_source_id, register_version, independence_group, tier, mapping_confidence, mapping_note, status, suppression_ref)` with indexes on `(subject_id, field)`, `(source_id, locator)`, `(status)` · `cards(card_id PK, card_kind, state, merged_into, created_in_build, visibility)` · `card_keys(card_id, kind, key)` (the mapping table: `spelling`, `stress`, `pos`, `paradigm_key`, `mwe_key`, `source_key`) · `senses(sense_id PK, card_id, ord, state, merged_into)` · `sense_map(sense_id, source_id, source_sense_key, mapped_by)` · `links(link_id PK, type, from_id, to_id, role, state)` + `link_evidence(link_id, assertion_id)` · `field_resolutions(subject_id, field, state, selected_json, values_json, groups_agreeing, resolution_ref, build_id)` · `quality(subject_id, dimension, value, evidence_json, build_id)` · `derivations(derived_id PK, kind, generator, generator_version, output_ref, built_in)` + `derivation_inputs(derived_id, assertion_id, card_id)` · `build_manifest(build_id PK, inputs_json, rules_version, started_at, finished_at)`. Today's `articles`, `article_payloads`, `enrichment`, `aliases`, `related_entries`, `article_provenance` become generated views/exports (`migration.md`).

## 16. Open design questions (for Astra and Gemini; not decided here)

- **Q1 (design)** Assertion id includes `value_norm`; a normalisation-rule change re-mints ids. Acceptable (ids are content addresses), or should the id exclude the value and version the normaliser separately?
- **Q2 (design)** One id namespace `wc_` for lexemes, MWEs and proper names with `card_kind`, versus separate prefixes. Proposed: one namespace.
- **Q3 (design + register)** Independence groups and tiers are provisional (§9.1); they belong in the #8979 register per source and per field. Who owns them, and do `ukrainian_word_stress` and ВТС get lineage entries before C1?
- **Q4 (language)** Should `variant` require a tier-1 source that declares the doublet (ULIF `по́ми́лка`, VESUM `броня́; бро́ня`), or may two tier-2 sources disagreeing on a known doublet class be declared `variant` by rule?
- **Q5 (design)** Promotion of reviewed teacher/curated assertions from tier 3 to voting tier 2 by `review.status = reviewed`: allowed, and by which lanes?
- **Q6 (language)** Sense inventory authority when several sources give senses (ВТС numbered senses, ULIF `sense_gloss` list, СУМ-20 `sense_order`): which one seeds the sense rows when they disagree in count?
- **Q7 (language + practice)** May `identity_confidence = medium` cards (dictionary homonym split with identical paradigm, e.g. `ключ`) feed meaning practice, or only `high`?
- **Q8 (language)** Aspect-pair evidence: VESUM gives aspect per lemma, not the pairing; ВТС headers name the pair for some verbs; ULIF shared synonym groups are far too broad (91,385 imperfective/perfective lemma pairs share at least one identical synonym-group text). Which source or lane asserts the pair for A1–B1 verbs?
- **Q9 (design)** How `curriculum_embed` derivations are detected (card id in module metadata vs text match).
- **Q10 (design)** URL scheme for spellings with several cards (#8334 AC-02): disambiguation page at `/lexicon/<spelling>/` plus per-card routes, or stress-marked routes.
- **Q11 (design)** Overlay location and format (`data/atlas/overlay/*.yaml` in git, one file per batch) and whether overlay entries need cross-family review like code.
- **Q12 (language)** ULIF rows with an unparsed header and no paradigm (27) and ULIF proper-name homonyms (`Коса́` settlement, `Коса́` river in Russia): create cards or hold?

## 17. Evidence (queries run 2026-09-28, read-only)

All with `/home/ops/learn-ukrainian/.venv/bin/python` and `sqlite3.connect("file:…?mode=ro", uri=True)`.

```sql
-- atlas.db
SELECT count(distinct lemma), count(*) FROM articles;                       -- 27128 | 27128
SELECT entry_type, count(*) FROM articles GROUP BY 1;                       -- expression 124, lemma 26489, multiword_term 492, phraseologism 23
SELECT section, source, phase, count(*) FROM enrichment GROUP BY 1,2,3;     -- stress: ukrainian-word-stress 18448, kaikki 695; cefr: PULS 4041, estimated 3862 …
SELECT * FROM manifest_metadata;                                            -- version "0.1", generated_at 2026-09-11T10:12:36+00:00
-- sources.db
SELECT homonym_checked, status, count(*) FROM ulif_dictua_entries GROUP BY 1,2;  -- (0,not_found,6446) (0,ok,3) (1,ok,262788)
SELECT homonym_index, count(*) FROM ulif_dictua_entries WHERE homonym_checked=1 GROUP BY 1;
   -- 1:250712 2:10570 3:1252 4:200 5:38 6:7 7:3 8:2 9:2 10:1 11:1
SELECT kind, count(*) FROM ulif_dictua_sections GROUP BY 1;                 -- paradigm 250183, synonyms 75952, phraseology 8131, antonyms 2103
SELECT count(*) FROM ulif_dictua_entries WHERE homonym_checked=1 AND canonical_headword='';   -- 12899 (12095 with a paradigm, 27 with no section)
SELECT id, homonym_index, canonical_headword, grammatical_label, sense_gloss FROM ulif_dictua_entries WHERE normalized_query='замок';
   -- 76791 1 За́мок іменник чоловічого роду (населений пункт в Україні) | 76792 2 за́мок … (будівля) | 76793 3 '' '' ''
SELECT json_extract(payload_json,'$.rows[1]') FROM ulif_dictua_sections WHERE id IN (96929, 96933);  -- ["називний","за́мок","за́мки"] | ["називний","замо́к","замки́"]
SELECT level, count(*) FROM puls_cefr GROUP BY 1;                           -- A1 962, A2 1386, B1 2164, B2 1194, C1 233
-- vesum.db
SELECT * FROM vesum_build_metadata;                                         -- canonical_jsonl_sha256 53923150…, schema_version vesum-reingest-v1
SELECT count(distinct entry_id), count(distinct lemma) FROM forms_all;      -- 442458 | 422656
SELECT DISTINCT entry_id, tags, source_comment FROM forms_all WHERE lemma='замок' AND word_form=lemma;
   -- 128972 noun:inanim:m:v_naz:xp1 'замо́к (пристрій)' | 128973 noun:inanim:m:v_naz:xp2 'за́мок (будівля)'
SELECT DISTINCT entry_id, tags, source_comment FROM forms_all WHERE lemma='броня' AND word_form=lemma;   -- 30497 noun:inanim:f:v_naz 'xv2 броня́; бро́ня'
```
The stress-agreement measurement (14,509 / 14,419 / 12 / 78) joins `enrichment.stress` to single-homonym checked ULIF headwords on the spelling, drops monosyllables (ULIF leaves them unmarked: `ключ`) and letter mismatches, and classifies the rest; the script is reproduced in `identity.md` §11.
