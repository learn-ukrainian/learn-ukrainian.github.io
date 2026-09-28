# Word cards C0 — card schema (spec v1 r2, revised per the design panel)

- **Issue:** #8978 (schema) under epic #8977; identity contract for #8334 in [`identity.md`](identity.md); worked examples in [`worked-examples.md`](worked-examples.md); migration outline in [`migration.md`](migration.md).
- **Machine-readable schemas:** [`schemas/word-card-v1.schema.json`](../../../schemas/word-card-v1.schema.json) (the card) plus companions [`word-card-identity-registry-v1`](../../../schemas/word-card-identity-registry-v1.schema.json), [`word-card-overlay-v1`](../../../schemas/word-card-overlay-v1.schema.json), [`word-card-suppression-v1`](../../../schemas/word-card-suppression-v1.schema.json) and [`word-card-derivation-v1`](../../../schemas/word-card-derivation-v1.schema.json) (all JSON Schema 2020-12). The eleven example cards in [`examples/`](examples/) and the four companion instances in [`examples/companion/`](examples/companion/) validate against them; `tests/validate/test_word_card_examples.py` (46 tests) proves that, proves AC-03 (source removal recomputes value and state) and pins the resolver cases the design review reproduced (§8.3).
- **Status:** r2, 2026-09-28, author Claude (Fable 5.1). Round 1 reviews of record: Astra (`gpt-6-astra`, design) **REVISE** with seven blocking gaps; Gemini (language lane) **APPROVE** with inputs on Q-I1–Q-I3, Q-I7/Q-I8. This revision closes the seven gaps (§16.1 maps each to its section) and adopts the panel's recommendations where they agree (§16.2); what remains is listed under *Decisions needed* (§16.3) and is not decided here.
- **Approved inputs:** proposal #8976 (operator go 2026-09-27) with both advisor reads; #8978 advisor requirements; #8983 (practice eligibility) and #8980 (takedown) as constraints; operator decisions of 2026-09-27 on #8979 (content stays, teacher consent, takedown via GitHub issues, no outreach).
- **Evidence rule:** every statement about current data below comes from read-only queries against `data/atlas.db`, `data/sources.db` and `data/vesum.db` run on 2026-09-28; §17 lists them.

## 1. What a card is

A **card** is an assembled view over retained, cited **assertions**. Choosing the value a page or an exercise shows never deletes the alternatives or their sources. Three products read the same cards: Word Atlas pages, practice generators and the open dataset.

- One card per **lexeme** (a word with one paradigm, one stress pattern or declared doublet, one POS and one sense family), per **multiword expression** (MWE) and per **proper name**. Never one card per spelling. Today `atlas.db` has exactly one article per bare spelling: 27,128 articles, 27,128 distinct lemmas, so `замок` is one article with gloss `castle / lock`, stress only `за́мок` and castle-only synonyms.
- **Senses** are rows under a card. Meanings, relations and examples attach to senses, not to the card.
- Cards are **derived**: `atlas.db = build(S sources, V vesum, I identity registry, O overlay, R rules)`. Nothing is hand-edited in `atlas.db`; ids live in the identity registry (§5), curation in the overlay (§12); both are versioned inputs replayed by the build (§13).
- Quality is **several dimensions**, not one flag (§9). Corroboration (how many independent lineages agree) is separate from fitness for practice (#8983).

## 2. Entities

```
source_snapshots ──< source_records ──< assertions >── cards ──< senses
                                            │            └──< links (canonical typed records, endpoints with roles / sense restrictions)
                                            └──< derivations (exercises, distractors, glosses, dataset rows, pages, curriculum embeds)
identity registry (git, versioned) ── ids, keys at creation, split / merge / retire events
overlay (git, reviewed batches) ── replayed by build ── suppression selectors (durable, reharvest- and rollback-proof)
build_manifest ── content hashes of S, V, I, O, R; card versions
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
| `review` | `{status: none|sampled|reviewed|rejected, lane, record, date}`: the reviewing lane for generated/teacher/curated content. `rejected` assertions are retained but **never vote and are never shown as the value** (§8; pinned by `test_rejected_only_assertion_shows_nothing`). Review establishes acceptance, not source independence: it never promotes a tier (Q5). |
| `licence_ref` | `{register_source_id, register_version, appears_in?}` (§10). |
| `independence_group`, `tier` | copied from the register at build time (§9.1). |
| `mapping` | `{confidence, basis, ambiguous?, note}`: how sure the build is that this source row belongs to this card and **on what basis** (`entry` = a homonym-checked source entry, `paradigm`, `stress`, `sense`, `overlay`, `curator`, `spelling`). Missing means `high`/`entry`. `low`/`unresolved` assertions are retained but do not vote (§8). `ambiguous: true` is set by the build when the basis is `spelling` and the spelling has more than one card: the assertion is displayed and counts for the value, but **never satisfies a dependent eligibility rule** (§9.5). Example: PULS rates the spelling `замок` A2 (`puls_cefr.id 4340`, no guideword); it does not say which замок, so the assertion is on both cards at `medium`, `basis: spelling`, `ambiguous: true`. Scale: 870 of 5,939 PULS rows sit on spellings with more than one checked ULIF homonym, 687 of them A1–B1; 505 rows carry a `guideword` that may disambiguate them (§17). |
| `source_record_key` | durable, **content-derived** key of the source record (§12.1), e.g. `ulif:record:замок#замо́к#` (query # stressed headword, canonical or paradigm-recovered # grammatical label), `vesum:record:замок/noun/noun:inanim:m:v_naz:xp1`, `puls:record:замок/іменник/A2`. Never a local row id: `ulif:entry:76793` is a `sources.db` row number and appears only inside `locator`. Suppression selectors and reharvest correspondence key on this. |
| `status` | `active`, `suppressed` (with `suppression_ref`: suppression id or takedown issue URL), `superseded`. |

Suppression is a status, not a deletion: the internal store keeps the row so the takedown report (#8980) can say what was removed and reimport cannot bring it back (the overlay entry outlives the snapshot).

## 5. Cards, opaque ids, the identity registry, splits and redirects

- `card_id`: `wc_` + 12 Crockford base32 characters (`[0-9a-hjkmnp-tv-z]`), random at minting, no semantics, never reused. `sense_id`: `ws_` + 12. Link ids `wl_` and assertion ids `wa_` are content-derived (§4, §7.2). One namespace for lexemes, MWEs and proper names, distinguished by `card_kind` (Q2, adopted).
- **Identity registry** (`I` in §13; schema `word-card-identity-registry-v1`; example `examples/companion/identity-registry.json`): the versioned, committed input that holds every card and sense id ever minted with its `key_at_creation` (spelling, stress patterns, POS, `paradigm_key`, `mwe_key`, `source_keys`), `created_in_build`, `state`, `merged_into` / `split_into`, and the **lineage events** (`mint`, `split`, `merge`, `retire`, `sense_mint`, `sense_merge`, `sense_split`) with their overlay id and evidence. The build reads ids from the registry and mints only for keys that have no entry; a build that mints writes the new allocations back as a registry version bump that is committed with the build. The key at creation is *matching evidence*, recorded so a later build can find the same card again; it is not identity. Renaming a spelling (2019 orthography) or correcting a stress does not change the id.
- **Card states**: `active`; `redirected` (a merge: exactly one `merged_into`); `split` (one-to-many: `split_into` with at least two successors, no `merged_into`); `suppressed`. The JSON schema enforces the state invariants (`allOf`/`if-then`: `redirected` without a target is invalid, `split` with fewer than two successors is invalid, `active` with either pointer is invalid; `test_split_card_is_one_to_many_and_schema_enforces_the_invariants`). Field-level states are in §8.
- **Redirect (merge)**: the losing card gets `state = redirected`, `merged_into = <survivor>`; its senses get `merged_into` sense ids. Consumers that hold the old id resolve through `merged_into` before use.
- **Split**: the old card gets `state = split`, `split_into = [successors]`; nothing is redirected, because the old card mixed two words and no successor "is" the old card. Consumers holding the old id must resolve per successor: see `identity.md` §7 for the rule per consumer (learner progress is transferred only where item-level evidence identifies the successor; otherwise it is preserved as history and flagged for reassessment). Example: `examples/zamok-legacy-split.json` (the atlas0 article `замок` → castle + lock).
- Redirected and split cards are never deleted and never re-minted; the registry keeps their keys so a future harvest cannot mint the old key again.
- **Spelling aliases**: `slug`/spelling stays an alias (today's `aliases` table: 27,128 `transliteration`, 821 `canonical`, 344 `inflected_form` rows). A spelling with several cards resolves to a disambiguation list at `/lexicon/<spelling>/`; cards get stable opaque-id routes with an optional decorative slug, and a stress correction never changes a canonical address (Q10, adopted; the route layout itself is #8334 AC-02).

## 6. Senses

- `senses[]`: `{sense_id, order, state: active|redirected|suppressed|unsplit, merged_into, sense_map[], fields{}}`.
- `sense_map` records which **source sense units** feed the sense: `ulif:section:<id>` (a ULIF synonym group is sense-bound: `замок` homonym 3 has three groups, `synonyms:1` = zipper `БЛИ́СКАВКА …`, `synonyms:2` = lock `ЗАМО́К (пристрій для замикання дверей), ЗАПІ́Р рідше, ЗА́ПІРКА рідко; КОЛО́ДКА діал.`, `synonyms:3` = latch `ЗА́ЩІПКА …`), `sum20:wordid:<n>/sense:<k>` (`sum20_senses.sense_order`), `vts:<spelling>#<I|II>/<n>` (numbered senses inside today's `definition_cards` payloads), `ulif:entry:<id> sense_gloss[i]` (ULIF's `sense_gloss` is one parenthesised list: for `ключ` homonym 1 it names six senses separated by `;`).
- Alignment across sources is a curation decision. It is automatic only when **both** sides have exactly one unit: the card has one active sense and the source has one unit for the card. One unit on the source side alone does not establish cross-source sense equivalence (Astra gap 4): the Караванський synonym row for `замок` is a single unit, but the castle card has three senses, so it is held on the `unsplit` sense until a `sense_map` overlay places it. Units that cannot be aligned go to one sense with `state = unsplit`; unsplit senses are shown on the page (thin cards are never hidden) and excluded from practice modes that need sense alignment (#8983).
- **Sense inventory seed** (Q6): the sense rows of a card are seeded from one explicitly structured modern source, recorded per card as `senses[].seeded_from` (`sum20` when the article is crawled, else ВТС numbered senses, else the ULIF `sense_gloss` list; the order is a *Decision needed*, §16.3). Other inventories are preserved as units in `sense_map`; a different sense count is adjudicated by the language lane through `sense_map`, never matched by ordinal position or auto-merged.
- Sense-level fields (`definition_uk`, `gloss_en`, `synonyms`, `antonyms`, `examples`, `register`, `russification_exposed`, `collocations`) resolve exactly like card fields (§8).

## 7. Multiword expressions and typed links

### 7.1 MWE cards
- `card_kind = mwe`, own key: `mwe_key = <first source locator>|<normalised form>`, e.g. `ulif:entry:76792/section:96932|будувати повітряні замки`. Normalised form: NFC, accents stripped, lower-case, punctuation and slot markers (`кого, чого`, bracketed optional parts) kept as slots in `mwe_frame`.
- One MWE card even when a source lists the idiom under several headwords: ULIF lists «будувати повітряні замки» under `замок` homonym 2 (section 96932) and under `повітряний` (section 218523) with identical text.
- Scale in ULIF: 8,131 phraseology sections; 4,820 distinct heads by the first 60 characters of `text` (an upper bound on cards from ULIF, because variants such as `тримати (держати) за сімома замками` are one section). `sources.frazeolohichnyi` (24,683 rows) and today's `enrichment.idioms` (via slovnyk.me) carry the same dictionary text (§9.1).
- Existing `atlas.db` multiword articles (492 `multiword_term`, 124 `expression`, 23 `phraseologism`) become MWE cards with `atlas0` keys.

### 7.2 Typed links (canonical records)
`links[]` embeds **canonical link records** (`$defs/link`): `{link_id, type, endpoints: [{id, role?, sense_id?}, {id, role?, sense_id?}], basis: asserted|derived, derived_by?, assertion_ids[], state, note?}`. There is exactly one record per link: for symmetric types (`aspect_pair`, `homograph_of`, `stress_variant_of`, `synonym`, `antonym`, `russification_contrast`) the endpoints are ordered by role rank (imperfective before perfective, norm before imposed) and then by id, `link_id = wl_ + sha256(type|endpoints)`, and **both** cards embed the identical record (`test_links_are_canonical_records_with_evidence`: the aspect pair `вибіга́ти ↔ ви́бігти` is one `wl_1ee8b1c64f672f0b68c562e6` on both cards). Directed types (`component_of` with roles `whole` / `anchor` / `component`, `see_also`) keep the given order. `sense_id` on an endpoint restricts the link to that sense (a ULIF synonym group is sense-bound; the flock group `ЛАНЦЮГО́М … КЛЮЧЕ́М` attaches to the flock sense of `ключ`, not to the card).

Evidence: an `asserted` link cites the source or overlay assertions that state it (ULIF anchors carry the target's own id: `dictua.aspx?uid=47336` = `ЗА́МОК` castle, `uid=47335` = `ЗАМО́К` lock; ULIF antonym rows are `paired_sense` objects with `left`/`right` sides: `БРАТИ` ↔ `ДАВАТИ` in `ulif:entry:28535/section:27648`). A `derived` link is computed by a named rule from card keys and cites the assertions the rule read (`homograph_of`: equal `key_at_creation.spelling` ignoring case with distinct identity; evidence = the spelling assertions of both endpoints). **A link with no active supporting assertion is `suppressed` by the build** (`test_link_without_evidence_is_suppressed`); an active link has at least one, enforced by the schema.

Aspect pairs (Q8, adopted): the pairing is asserted by explicit pairing statements in checked СУМ-20/ВТС entries attached to the relevant senses, or by a cited teacher/source assertion adjudicated by an independent language lane; VESUM + checked ULIF verify each member's aspect, never the pairing; shared synonym groups (91,385 lemma pairs share one) and two PULS ratings are not pair evidence.

## 8. Field resolution and quality states

For each (subject, field) the build computes a **field resolution** `{state, selected, values[], independence_groups_agreeing, comparison, proposition, mapping_evidenced, independence_groups_evidenced, non_voting[], resolution_ref?}` from the assertions. Rules `rules-v1-draft` (reference implementation: `resolve()` in `examples/build_examples.py`, pinned by the tests in §8.3).

### 8.1 What is compared: comparison classes and the proposition
Corroboration is counted on an exact proposition, recorded in `proposition`. Each field has a **comparison class** (`comparison`):

| class | fields | proposition | disagreement |
| --- | --- | --- | --- |
| `scalar` | `stress`, `pos`, `gender`, `aspect`, `cefr`, `frequency`, `heritage_status`, `transliteration`, `spelling`, `grammatical_label`, `mwe_form` | `field(subject) = value_norm` | two different `value_norm`s contradict (`conflict`) unless a tier-1 source declares the set (`variant`) |
| `keyed` | `paradigm` | `field(subject)[key] = value` with `value_norm = "<slot>=<form>"`, one proposition per slot | contradiction only inside one slot (`rod.sg=замку` vs `rod.sg=замка`); a slot given by one source only is `single-source` for that slot; ULIF giving fewer slots than VESUM is a compatible subset, not a conflict (`test_keyed_paradigm_conflicts_only_inside_a_slot`). The field state is the worst slot state. |
| `text` | `definition_uk`, `gloss_en`, `english_gloss`, `sense_label`, `examples`, `collocations`, `russification_exposed`, `synonyms`, `antonyms`, `spelling_variants`, `register`, `mwe_frame` | `field(subject) ∋ text` — each source's text is its own proposition | different texts are **parallel**, never a conflict; identical texts corroborate. The shown text is the one with the most independent groups, then the lowest tier, then the lowest assertion id; the others stay in `values[]` (`test_text_fields_are_parallel_propositions_never_conflict`). |

### 8.2 Rules
1. **Who votes.** Take `active` assertions whose `mapping.confidence` is `high` or `medium` and whose `review.status` is not `rejected`. Everything else that is active is listed in `non_voting[]` with its reason (`mapping low`, `mapping unresolved`, `review rejected`) so the page can still show it as evidence. If nothing votes: `suppressed` when any assertion for the field is suppressed, otherwise `unverified` with `selected = null` and no values (a rejected-only field shows nothing as fact: `test_rejected_only_assertion_shows_nothing`).
2. **Tiers.** Voting assertions are tier 1 and tier 2 (§9.1). If only tier-3 assertions exist (generated, teacher-unreviewed, estimated, curated) the state is **`unverified`** and the first tier-3 value is shown with its producer.
3. **Grouping.** Group voting assertions by `value_norm` per the comparison class. Count **distinct independence groups** per value; groups with unknown lineage (marked `?`) never count.
4. **Declared sets (scalar).** A tier-1 assertion whose `value_norm` is a set (`броня́|бро́ня` from VESUM's `xv2 броня́; бро́ня`, `по́милка|поми́лка` from ULIF's `по́ми́лка`) declares a doublet. If every observed single value is a member of the declared set — including when there is **no** observed value (the declaration alone) or only **one** member — the state is **`variant`**, `selected` lists every voting assertion and the declared entry carries `declared_set: true` (`test_declared_doublet_alone_is_variant`, `test_declared_doublet_plus_one_member_is_variant`). A declared set that does not contain an observed value is a **`conflict`**. Variants may also be declared by a reviewed, cited language-lane overlay `variant` entry (Q4, adopted); two disagreeing tier-2 sources never establish a doublet by rule.
5. **One value:** ≥2 groups → **`verified`**; 1 group → **`single-source`** (several assertions from one lineage are still single-source: ULIF + slovnyk.me + `frazeolohichnyi` for an idiom).
6. **Several values (scalar / keyed slot):** an overlay `resolve` entry picks the shown value and records `resolution_ref`; the losing values stay in `values[]`. Else → **`conflict`**: `selected = null`, nothing shown as fact, the field is listed for review and excluded from practice.
7. **Evidence for eligibility.** `mapping_evidenced` is true when at least one voting assertion for the shown value maps to this card on a basis other than an ambiguous spelling; `independence_groups_evidenced` counts independent groups among those assertions only. Eligibility rules (§9.5) read these, never the bare state: castle `cefr` is `single-source` with `mapping_evidenced = false` (PULS is spelling-keyed and `замок` has two lexeme cards), `ключ` stress is `verified` by ULIF + kaikki but `independence_groups_evidenced = 1` because the kaikki row cannot tell the two `ключ` cards apart.
8. **Card-level:** `redirected`, `split` and `suppressed` override every field state in public outputs.

States are therefore: `verified`, `single-source`, `variant`, `conflict`, `unverified`, `suppressed` (field), plus `redirected`, `split`, `suppressed` (card). `variant` is distinct from `conflict` on purpose (advisor requirement): `по́ми́лка` is one word with two permitted stresses, `вряди́-годи́` (ULIF) vs `вряди́-го́ди` (ukrainian-word-stress) is a disagreement. Confidence thresholds and the field-resolution policy are versioned in `R` and replaceable; provisional tiers, dictionary partitions and spelling-level CEFR never enter an id.

### 8.3 Pinned resolver cases (round-1 review reproduced these against the contract)
| case | round 1 gave | contract (r2) | test |
| --- | --- | --- | --- |
| declared doublet alone (`броня́|бро́ня`) | `single-source` | `variant` | `test_declared_doublet_alone_is_variant` |
| declared doublet + one member (`броня́`) | `conflict` | `variant` | `test_declared_doublet_plus_one_member_is_variant` |
| `extraction_confidence_min` over `{high, medium, low}` | `high` | `low` (the worst) | `test_extraction_confidence_min_is_the_worst_confidence` |
| a `rejected` assertion alone | `single-source` | `unverified`, nothing shown, listed in `non_voting` | `test_rejected_only_assertion_shows_nothing` |

Measured today (Atlas `enrichment.stress` vs ULIF headword, single-homonym spellings, polysyllables, same letters): 14,509 comparable, 14,419 agree, 12 are ULIF doublets containing the Atlas stress (`variant`), 78 differ. Most of the 78 are identity artefacts, not conflicts: `варення` (ULIF has two homonyms, `ва́рення` (дія) and `варе́ння`), `бере` (ULIF `бе́ре`, a noun; Atlas `бере́`, a verb form), `всього` (ULIF adverb `всього́`; Atlas `всьо́го`), `братів` (adjective vs genitive plural). `вряди-годи` is a genuine conflict (one VESUM entry, one ULIF homonym). The language lane confirmed the classification of all measured cases (Gemini, 2026-09-28).

## 9. Quality dimensions

### 9.1 Source independence: groups and tiers
Corroboration counts **lineages**, not labels. Provisional table; the merged register (`docs/sources/permissions-register.yaml`, schema 2, sha256 `eb286a61…`) records rights and provenance but **no lineage fields yet**, so the groups below live in `R` until the register gains `independence_group` / `lineage` per source and per field (Q3, adopted: the Atlas driver owns completion, the register maintainer records lineage from reviewed evidence with language/source review and cross-family review; original dictionary, edition and field are modelled separately from delivery mirrors; UWS and ВТС are recorded as explicitly `unknown` before C1 if research cannot establish lineage, and `unknown` never corroborates; a different organisation or website is never inferred to be a different lineage):

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
| `G-TEACHER` | `teacher_materials`, `ulp_private` | 3 | never promoted by review (Q5, adopted): a sanctioned independent language reviewer may *approve an assertion for a specified use* (`review.status = reviewed` + `approved_for: [modes]`), keeping its lineage and tier |
| `G-PROJECT` | `course_authored`, `learner_english_gloss`, `estimated (GRAC frequency)`, curated side files, generators | 3 | never corroborates |
| `G-SUM11` | `sum11` | 0 | not evidence for any modern field (rule #M-6); only the `russification_exposed` field may cite it, always paired with the modern norm (#8982) |

### 9.2 Identity confidence
Per card (`identity.confidence`) and per assertion (`mapping.confidence` + `basis` + `ambiguous`): `high`, `medium`, `low`, `unresolved`; rules in `identity.md` §4–§5. `unresolved` cards exist (thin, honest) but no practice item may depend on them. A confidence label on shared morphology never certifies meaning alignment (Q7, adopted): **meaning practice requires reviewed `high` identity for the specific card and sense** and evidenced supporting assertions; `medium` cards (dictionary-division splits such as `ключ`) are excluded from meaning modes until a language-lane overlay `identity` entry raises them.

### 9.3 Extraction confidence
Per assertion (§4). `quality.extraction_confidence_min` summarises the card.

### 9.4 Linguistic review
Per assertion (`review`) and per card (`quality.linguistic_review`): `none`, `sampled`, `reviewed`, `rejected`, with lane and record. Generated, teacher and curated content needs at least `sampled` by a lane outside the producer's family before it reaches A1–B2 practice (#8976 rule).

### 9.5 Practice eligibility
`quality.practice_eligibility[]`: `{mode, eligible, rules_version, reasons[], sense_id?}`, computed by the eligibility rules of #8983 (per mode: CEFR/frequency band, register exclusions, sense alignment, identity confidence, field state ∈ {verified, single-source, variant}). It is an output of the build, versioned by `rules_version`, never edited by hand. Exercises record the card version (`build.card_version`) and generator version they used (#8983).

**Evidence rule (Astra gap 4).** A field satisfies a dependent eligibility rule only if its resolution has `mapping_evidenced = true`; an ambiguous spelling-level assertion (PULS A2 on `замок`, a GRAC estimate on `вибігати`, a kaikki row on `ключ`) is retained and displayed but never turns into eligibility. Consequently every example card is ineligible in every listed mode today and says why (`test_ambiguous_spelling_level_evidence_never_satisfies_eligibility`): the castle card's stress mode fails on the level band (`cefr` not evidenced), the `ключ` meaning mode fails on identity `medium` and on the level band. The route to eligibility is an overlay `identity`/`sense_map` entry that maps the PULS row (its `guideword`, present on 505 rows, is the first evidence to try) or a source that rates the lexeme, not the spelling.

**English gloss** (`english_gloss`, `gloss_en`) is a scaffold field with a level policy: shown at A1 by design, never raised from A2 (`level_policy` on the resolution; #8983 advisor requirement). It is not card content for immersion purposes.

## 10. Licence and permission reference per assertion

`licence_ref = {register_source_id, register_version, appears_in?}` points into `docs/sources/permissions-register.yaml` (#8979, merged; register `schema_version: 2`, `register_date: 2026-09-28`, file sha256 `eb286a61a5a68ca282482bf747ac27f546022b1becdadb32bfbd707c2bac8873` pinned in `R`). The register holds, per source, the rights holder, the terms as found, the citation form to show and the removal route. Operator decisions of 2026-09-27 (register `operator_decisions` d1–d4): all current content stays on the site and in exports; the teacher consents; takedown requests arrive as GitHub issues; no outreach. The register is therefore a **citation and provenance record, not a publication gate**. Exporters read `appears_in` only to keep `internal`-only sources (e.g. `ulp_private`) out of public outputs; they do not withhold registered sources.

Every derived item inherits the `licence_ref`s of the assertions it used (§11), so a dataset row can print its full attribution list and a takedown can find it.

## 11. Dependency records from derived items

Schema `word-card-derivation-v1`; example `examples/companion/derivations.json`. `derivations[]`: `{derived_id, kind: exercise|distractor|gloss|relation|dataset_row|atlas_page|search_doc|curriculum_embed, generator, generator_version, rules_version, build_id, inputs: {assertion_ids[], card_ids[], card_versions{card_id: cv_…}}, output: {kind, key, content_sha256}, status: active|invalidated, invalidated_by?}`.

- `derived_id = wd_ + sha256(generator, generator_version, inputs, output.kind, output.key)`: the **output identity** is part of the id, so one generator producing several items from the same inputs yields distinct records (Astra gap 6). `output.key` is the route, item key, dataset row key or `release + path`; `content_sha256` pins what was published.
- `inputs.card_versions` pins `build.card_version` (`cv_` + sha256 of the card's public content: identity, senses, links, fields) so a changed card invalidates its derivations even when the input assertion set is unchanged.
- Practice items, distractors and generated glosses record the assertions they read (not only the card), so a suppressed assertion invalidates exactly the items that used it and #8983 regenerates them (§12.2).
- Dataset rows record inputs so a retracted release (#8980) can list affected rows and the releases that carried them.
- `curriculum_embed` (Q9, adopted): new generated embeds record card/sense/assertion ids and versions in module metadata or a dependency manifest; a text scan of `curriculum/` at build time is a legacy discovery aid whose hits are reviewed, never proof of complete coverage.

## 12. Curation overlay and suppression

The overlay is the only hand-written input (`O` in §13; schema `word-card-overlay-v1`; example `examples/companion/overlay.json`). It lives in git as reviewed YAML/JSON batches (proposed `data/atlas/overlay/<batch>.yaml`, Q11 — see §16.3), is keyed by `card_id`, and every entry is replayed by the build as a `curator` assertion with `review` and `producer` filled in. Every entry has `overlay_id` (unique, `ovl-YYYY-MM-DD-NNNN`), `author`, `lane` (`language` | `design` | `operator`), `date`, `evidence` (source locators) and `record`; batches need schema validation, deterministic replay and cross-family review like code, and linguistic entries also need language-lane review (Q11, adopted).

```yaml
- overlay_id: ovl-2026-09-28-0001
  kind: split                       # merge | split | resolve | variant | suppress | level_override | sense_map | link | identity
  card_id: wc_0a1b2c3d4e5f          # for split: the card being split; for merge: the card being merged away
  into: [wc_7k3m9q2xw4pd, wc_c2v8n5rt6yhq]
  author: human
  lane: language
  date: 2026-09-28
  evidence: "ulif:entry:76792 родовий за́мку vs ulif:entry:76793 родовий замка́; vesum:entry:128973 xp2 vs 128972 xp1"
  record: "#8334 curated heteronym side file"
- overlay_id: ovl-2026-09-28-0002
  kind: resolve
  card_id: wc_x2j5n8sd1vpc
  field: stress
  assertion_id: wa_…                # the value to show; losers stay in values[]
  rationale: "…"
```

Kinds: `merge`/`split` (identity, §5 and `identity.md` §7), `resolve` (conflict → shown value), `variant` (declare a doublet when no tier-1 source declares it; reviewed and cited), `suppress` (below), `level_override` (CEFR for practice; recorded as a tier-3 assertion with lane), `sense_map` (alignment of source sense units), `link` (assert a typed link with evidence), `identity` (confirm, raise or reject a machine match; the record the golden set's replay pool uses).

### 12.1 Suppression selectors (persistent across reharvest, remapping and rollback)
Schema `word-card-suppression-v1`; example `examples/companion/suppression-selectors.json`. Assertion ids are content addresses and change when a snapshot, subject, value or extraction version changes, and `locator`s contain local row ids; neither is a durable key. A suppression is therefore a **selector** over durable keys:

| selector kind | matches | survives |
| --- | --- | --- |
| `source` | every assertion from `source_id` | everything |
| `source_record` | every assertion whose `source_record_key` equals the key (`ulif:record:замок#замо́к#`), in any snapshot | reharvest, renumbering, remapping to another card |
| `assertion_content` | `source_id` + `field` + `subject_spelling` (+ `value_norm`) | re-normalisation, re-extraction, a changed assertion id |
| `assertion_id` | one id, with a mandatory `assertion_content` fallback | the id as long as it exists, the content afterwards |

Every entry carries `issue` (the GitHub issue, operator decision d3), `scope` (`site`, `dataset`, `internal`) and `applies_to: {reharvest: true, rollback: true}` (both are schema constants: there is no non-durable suppression). The build keeps a `source_records(source_record_id, source_id, source_record_key, snapshot_id, locator)` correspondence so a key resolves to the right locators in every snapshot; a new snapshot is loaded through the selectors, so a suppressed record is skipped on import. **Rollback applies the current selectors**: `rollback = build(S_prev, V_prev, I_prev, O_prev ∪ suppressions_now, R_prev)` — historical inputs never resurrect withdrawn content.

### 12.2 Transitive invalidation
Suppressing an assertion marks `status = suppressed` on it and then walks the dependency records (§11): every derivation whose `inputs.assertion_ids` contains it is `invalidated` (with `invalidated_by = suppression_id`), and their outputs are regenerated or removed. Links citing only suppressed assertions become `suppressed`; field resolutions recompute (§8; AC-03 test); cards whose every assertion is suppressed become `suppressed`. The takedown report (#8980) lists, per suppression: assertions, cards, fields, links, derivations by kind, dataset rows, curriculum modules, and the hosted releases in §12.3.

### 12.3 Public projections and release retirement
- **Tombstones.** Public projections (site shards, dataset files, search docs) carry a suppressed assertion as `{assertion_id, status: suppressed, suppression_ref}` only (`$defs/assertion_tombstone`); the value, locator and source payload never leave the internal store (`test_public_projection_carries_suppressed_assertions_as_tombstones`). The internal store keeps the full row so the report can say what was removed and reimport cannot bring it back.
- **Retirement.** Rebuilding current files is not enough: every hosted artefact that carried the payload is retired — dataset releases are yanked and re-issued (the retired release id is recorded on the suppression), practice-deck versions are bumped and the old version unpublished, runtime shard bundles are redeployed and CDN caches purged, the search index is rebuilt. Each retired artefact is a `derivation` record with `status = invalidated`, so the report is complete by construction.

## 13. Reproducible build contract

```
atlas.db  =  build( S , V , I , O , R )
S = source snapshots (content hashes)   V = vesum.db (canonical sha)   I = identity registry (version + hash)
O = overlay batches + suppression selectors (git commit)   R = rules + normaliser + register content (versions + hashes)
```

- **Pure and deterministic.** Same `(S, V, I, O, R)` → identical cards, identical ids, identical field resolutions, identical `card_version`s. Ids come from `I`; a build mints only for keys absent from `I` and commits the new registry version with the build. Proof in CI: build twice, compare logical dumps (the examples do this at small scale: `test_generator_reproduces_committed_examples`).
- **Inputs are hashed by content, never by row ids or counts** (Astra gap 1). Measured for the example manifest (§17): `S.sources.ulif_dictua_entries` = sha256 over the sorted `content_sha256` of the 262,788 checked rows = `fe9f52cb26…`; `S.sources.puls_cefr` = sha256 over the canonical JSON of its 5,939 rows = `c2586b0bd4…`; `S.atlas0` = the frozen `data/atlas.db` file (`fcf802bda3…`, manifest 0.1, retained read-only because migrated assertions cite `atlas0@manifest-0.1/2026-09-11`); `V` = `vesum_build_metadata.canonical_jsonl_sha256` `53923150…`; `I` = registry version + file hash; `O` = overlay commit; `R` = `rules-v1-draft`, `norm-v1` (the normaliser is versioned separately from the rules: Q1, adopted — a normaliser change may mint new assertion ids, with `superseded` links to the old ones and stable source-record keys underneath) and the register file sha256 `eb286a61…` (content, not only its schema version). Historical source snapshots referenced by any retained assertion are kept.
- **Build manifest** (`build_manifest` table + `docs/atlas/word-cards/builds/<build_id>.json`) records exactly these; every example card embeds it in `build.inputs.{S,V,I,O,R}` (schema-required keys).
- **Takedown** (#8980) = add a suppression selector → rebuild → transitive invalidation (§12.2) → diff report → republish and retire (§12.3). Correctness fixes (#8729, #8715) do not wait for this: they land as overlay entries or extractor fixes against today's tables.
- **Rollback** = rebuild from the previous `(S, V, I, O, R)` with the current suppression selectors applied (§12.1); nothing else to restore.

## 14. Russification exposed (СУМ-11)

`sum11` is tier 0. It appears only in the sense-level field `russification_exposed`, always as a contrastive object `{imposed: <СУМ-11 text with locator>, norm: <modern assertion id>, distortion_type, both citations}` (#8982), never as `definition_uk`, `stress`, `examples` or a practice answer. `sources.sum11` holds 127,069 rows with `sovietization_risk` and `sovietization_keywords` columns; the `замок` row (`id 29322`) has `sovietization_risk 0`.

## 15. Physical schema sketch (SQLite, for C1) and enforceable invariants

`source_snapshots(snapshot_id PK, source_id, edition, retrieved_from, retrieved_to, content_digest, extraction_version)` · `source_records(source_record_id PK, source_id, source_record_key, snapshot_id, locator)` · `assertions(assertion_id PK, subject_kind, subject_id, field, value_json, value_norm, source_id, snapshot_id, locator, source_record_id, extraction_version, extraction_confidence, producer_kind, producer_name, producer_version, produced_at, review_status, review_lane, review_record, review_date, register_source_id, register_version, independence_group, tier, mapping_confidence, mapping_basis, mapping_ambiguous, mapping_note, status, suppression_ref)` with indexes on `(subject_id, field)`, `(source_record_id)`, `(status)` · `cards(card_id PK, card_kind, state, merged_into, created_in_build, visibility, card_version)` · `card_split_into(card_id, successor_id)` · `card_keys(card_id, kind, key)` · `senses(sense_id PK, card_id, ord, state, merged_into, seeded_from)` · `sense_map(sense_id, source_id, source_sense_key, mapped_by)` · `links(link_id PK, type, basis, derived_by, state)` + `link_endpoints(link_id, position, card_id, role, sense_id)` + `link_evidence(link_id, assertion_id)` · `field_resolutions(subject_id, field, state, comparison, selected_json, values_json, groups_agreeing, groups_evidenced, mapping_evidenced, resolution_ref, build_id)` · `quality(subject_id, dimension, value, evidence_json, build_id)` · `derivations(derived_id PK, kind, generator, generator_version, rules_version, output_kind, output_key, output_sha256, status, invalidated_by, build_id)` + `derivation_inputs(derived_id, assertion_id, card_id, card_version)` · `suppressions(suppression_id PK, issue, date, selector_json, scope, retired_releases_json)` · `identity_events(event_id PK, kind, build_id, overlay_id, from_json, to_json, evidence)` · `build_manifest(build_id PK, inputs_json, rules_version, normaliser_version, register_sha256, identity_registry_version, started_at, finished_at)`. Today's `articles`, `article_payloads`, `enrichment`, `aliases`, `related_entries`, `article_provenance` become generated views/exports (`migration.md`).

**Invariants** (JSON-schema `if/then` on the card today; `CHECK`/trigger or a post-build validator in C1; each is a CI failure, not a warning):
1. `state = redirected` ⇔ `merged_into` is one existing card that is not itself redirected to this card (no cycles); `split_into` null.
2. `state = split` ⇔ `split_into` lists ≥2 distinct existing cards; `merged_into` null. `active`/`suppressed` ⇒ both null.
3. A sense has `merged_into` ⇔ its state is `redirected`; a sense never points outside its card's merge/split successors.
4. A link's two endpoints are existing cards (and, when given, existing senses of those cards); an endpoint that is `suppressed`/`redirected`/`split` suppresses the link until re-derived against successors.
5. `state = active` on a link ⇒ ≥1 active supporting assertion (`basis = asserted`) or a `derived_by` rule plus the assertions it read (`basis = derived`).
6. `field_resolutions.selected` ⊆ the assertion ids in `values[]`; `conflict`/`suppressed` ⇒ `selected` null.
7. Every `assertion.source_id` and `licence_ref.register_source_id` exist in the register at `register_version`; `source_record_id` exists in `source_records`.
8. Every `derivation_inputs.assertion_id` exists; a derivation with any `suppressed` input is `invalidated`.
9. Every id in `cards`/`senses` exists in the identity registry at the build's registry version; the registry never loses an id.
10. No `sum11` assertion on any field other than `russification_exposed` (rule #M-6; `tests/test_sum11_source_guard.py` extends to the card store).

## 16. Panel outcome: gaps closed, recommendations adopted, decisions needed

### 16.1 Astra's seven blocking gaps → where they are closed
| gap | closed in |
| --- | --- |
| 1 rebuild inputs (identity registry, content hashes, atlas0 retention, register content pinned) | §5 registry, §13, companion schema `word-card-identity-registry-v1`, `examples/companion/identity-registry.json`, `build.inputs.{S,V,I,O,R}` |
| 2 split ≠ merge redirect; learner progress | §5 states + schema invariants; `identity.md` §7 (one-to-many successors, progress transfer only on item-level evidence, reassessment otherwise); `examples/zamok-legacy-split.json` |
| 3 durable suppression selectors, transitive invalidation, release retirement, rollback under current policy | §4 `source_record_key`, §12.1–12.3, §13, companion schema `word-card-suppression-v1`, tombstone projection test |
| 4 ambiguous spelling-level evidence must not become eligibility; one source unit ≠ sense equivalence | §4 `mapping.basis/ambiguous`, §6, §8.2 rule 7, §9.2, §9.5 evidence rule; all example eligibility entries recomputed |
| 5 resolver contradicts the contract (3 reproduced cases) | §8.1–8.3, `resolve()` rewritten, four pinned tests |
| 6 canonical relation/dependency records, enforceable invariants | §7.2 canonical link records with endpoints/roles/sense restrictions/basis, §11 output identity + card versions, §15 invariants, schema `if/then`, companion schema `word-card-derivation-v1` |
| 7 circular golden set | `migration.md` §4 (replay pool vs sealed held-out pool, blind adjudication, metrics) |

### 16.2 Recommendations adopted (Astra and Gemini agree, or the question is design-only and Gemini is silent)
Q1 content-addressed assertion ids + separately versioned normaliser + stable source-record keys (§4, §13) · Q2 one `wc_` namespace + `card_kind` (§5) · Q3 lineage ownership and `unknown` never corroborates (§9.1) · Q4 variants only from a declaring source or a reviewed language-lane overlay (§8.2) · Q5 no tier promotion by review; approval for a specified use (§9.1) · Q6 one recorded seed source, adjudicated `sense_map`, no ordinal matching (§6; seed order is a decision below) · Q7 meaning practice needs reviewed `high` identity per card and sense (§9.2, §9.5) · Q8 aspect pairs from explicit dictionary pairing statements or adjudicated teacher/source assertions (§7.2) · Q9 embeds carry ids/versions; text scan is a discovery aid (§11) · Q10 spelling routes for lookup, opaque-id routes for cards (§5) · Q11 reviewed batches with schema validation and cross-family review (§12) · Q12 damaged rows held as unattached evidence; source-supported proper-name cards excluded from the general vocabulary pilot (`identity.md` §6, §1) · Q-I1 two provisional cards for dictionary-distinguished homonyms with identical paradigms (Astra + Gemini) · Q-I2 double accents are candidates only, corroborated by double-marked paradigm rows or an external authority (Astra + Gemini) · Q-I3 `броня` two cards (Gemini confirmed; the overlay `identity` entry recording the read raises the cards from `medium`) · Q-I4 split progress per `identity.md` §7.3 · Q-I5 every VESUM entry accounted for, many-to-many with cards, reported separately (`migration.md` §3) · Q-I6 ULIF `uid` extracted as a namespaced key and tested for stability; snapshot-local locators and correspondence kept · Q-I7/Q-I8 `прізвище`/`власна назва` labels set `card_kind = proper_name` (Gemini) but never establish cross-source identity or distinguish individuals (Astra) (`identity.md` §1).

### 16.3 Decisions needed (operator, or where the panel differs) — one recommendation each
1. **ULIF vs ВТС homonym divisions that differ in count** (Q-I1). Astra: preserve both partitions as separate provisional cards and require language-lane adjudication before any merge or meaning practice. Gemini: keep one shared card with an `unsplit` sense group until an overlay resolves it. *Recommendation:* Gemini's shared card with `unsplit` senses — it never shows a division that no source supports as two identities, and the `unsplit` state already blocks practice; record both partitions in `sense_map` so nothing is lost. Needed before M3.
2. **Sense inventory seed order** (Q6). *Recommendation:* СУМ-20 when the article is crawled (100 today), else ВТС numbered senses (12,468 payloads), else the ULIF `sense_gloss` list (51,182 entries); recorded per card in `seeded_from`. Needs the language lane's agreement that ВТС outranks the ULIF gloss list.
3. **Overlay and registry location** (Q11). *Recommendation:* `data/atlas/overlay/` and `data/atlas/identity/` tracked in git (precedent: `data/datasets/…` and `data/projects/…` are tracked); the registry is small (one row per card, ~30k rows at full scale). Needs operator confirmation that tracked `data/` is the intended home rather than `registry/`.
4. **Held-out adjudication lanes** (`migration.md` §4). *Recommendation:* two lanes outside the author's family adjudicate blind (Gemini via AGY and GPT via Codex), a third breaks ties; the operator signs the sealed manifest. Needs a lane-budget decision.
5. **Meaning practice for `medium`-identity cards** (Q7). Astra: exclude; Gemini approved the `medium` split itself but did not address practice. *Recommendation:* exclude until an overlay `identity` entry from the language lane raises the card to `high` (adopted provisionally in §9.2; confirm).

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
-- r2 additions (sources.db)
SELECT id, word, guideword, level, pos FROM puls_cefr WHERE id=4340;        -- 4340 замок '' A2 іменник
SELECT count(*) FROM puls_cefr p WHERE (SELECT count(*) FROM ulif_dictua_entries u
   WHERE u.homonym_checked=1 AND u.normalized_query=p.word)>1;              -- 870 (687 with level in A1,A2,B1)
SELECT count(*) FROM puls_cefr WHERE guideword!='';                         -- 505
SELECT id, normalized_query, homonym_index, canonical_headword, grammatical_label FROM ulif_dictua_entries
   WHERE id IN (76791,76792,76793,3,98008,29074,29075);                     -- record keys in build_examples.RECORD_KEYS
-- content digests (python, read-only): sha256 over sorted content_sha256 of the 262,788 checked ULIF rows
--   = fe9f52cb261736443f511a85b52e8ee6fe05b51165c56384cfa969b411429b98; sha256 over canonical puls_cefr rows (5,939)
--   = c2586b0bd4830bac7fc08d7bd59e98460d6f5acd468a5f323308668134780d55
-- sha256sum data/atlas.db = fcf802bda35dd4cd99e95317da0f4a1fa9315024befc83e73673c106278ebfca
-- sha256sum docs/sources/permissions-register.yaml = eb286a61a5a68ca282482bf747ac27f546022b1becdadb32bfbd707c2bac8873
```
The stress-agreement measurement (14,509 / 14,419 / 12 / 78) joins `enrichment.stress` to single-homonym checked ULIF headwords on the spelling, drops monosyllables (ULIF leaves them unmarked: `ключ`) and letter mismatches, and classifies the rest; the script is reproduced in `identity.md` §11.
