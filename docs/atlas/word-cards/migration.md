# Word cards C0 — migration outline from today's `atlas.db` (not implementation)

- **Scope:** the path from the spelling-keyed `atlas.db` (manifest `0.1`, 2026-09-11) to the card store of [`schema.md`](schema.md), gated by an A1–B1 vertical slice and a ~200-card golden set before full scale. Implementation is C1/C2 (#8981 pilot first); this doc only fixes the order, the mappings and the gates.
- **Non-goals:** re-harvesting ULIF (#8400), the URL scheme (#8334 AC-02, Q10), the practice rules themselves (#8983).

## 1. Today's tables → card store

| today (`atlas.db`, measured 2026-09-28) | becomes | note |
| --- | --- | --- |
| `articles` (27,128; `slug` PK = spelling; `entry_type`, `pos`, `gloss`, `cefr`, `heritage_classification`, `review_state`, `visibility`) | `cards` + `card_keys` (`atlas0:slug:<slug>`), `english_gloss`/`cefr`/`heritage_status` assertions with `source_id` from the payload's `source_provenance`, `visibility` kept on the card | one article may become several cards (2,811 lemma articles have several checked ULIF homonyms) |
| `article_provenance` (27,241; `source_family`, `source_locator`, `extraction_mode`) | `source_keys` on the card and `licence_ref` on the migrated assertions | families: `textbook` 16,251 rows, `built_vocabulary` 3,405, `content_lexicon_grow` 2,829, `ulp` 1,793, `teacher_lesson` 2,169, `ohoiko` 718, … |
| `enrichment` (193,530; one row per `(slug, section)`, `payload_json`, `source`, `phase`) | one assertion per value inside the payload, `snapshot_id = atlas0@manifest-0.1/2026-09-11`, `extraction_version = atlas0-migration`, `extraction_confidence = medium` | sections: `heritage_status` 27,128, `morphology` 25,631 (VESUM), `literary_attestation` 24,220, `stress` 19,143, `translation` ~22,000 across 10 labels, `definition_cards` 12,468 (ВТС), `cefr` 7,903, `synonyms` ~4,400, `idioms` ~4,000, `form_notes` ~5,700, … |
| `aliases` (28,295; `transliteration` 27,128, `canonical` 821, `inflected_form` 344) | `aliases` kept, `target_slug` → `card_id` (several targets allowed) | spelling → card disambiguation |
| `related_entries` (3,690, all `synonym`, `provenance verified/unverified`) | `links` of type `synonym` with the verdict as a curator assertion | sense-less today; attach to `unsplit` senses until mapped |
| `article_payloads` (27,471; rendered JSON per route) | generated export (`export_runtime_shards.py` reads cards) | no longer a store |
| `manifest_metadata` | `build_manifest` | |
| `site/src/lib/lexicon/curated-heteronyms.ts` (420 lemmas) | overlay `split` entries + `atlas0:heteronym:<spelling>/<stressed>` keys + curator assertions (`gloss`, `short_label`) | retires the side file (#8334 in-scope item 3) |

## 2. Steps

- **M0 Freeze and measure.** Record the `atlas0` snapshot (manifest hash, table counts), the ULIF snapshot (262,788 checked rows, parser v2, `retrieved_at` range) and the VESUM sha. Land the register entries the schema needs (ВТС, Караванський, orthographic dictionaries, ukrainian-word-stress lineage; #8979 `open_questions`).
- **M1 Mint ids.** One `wc_` id per existing article, mapping table with `atlas0:slug:<slug>` keys; MWE articles (639) as `mwe` cards. Ids are minted once, in a committed table, before any split.
- **M2 Re-extract, do not copy.** Assertions come from `sources.db`/`vesum.db` directly for every source we hold locally (ULIF, VESUM, PULS, `frazeolohichnyi`, Wiktionary, Грінченко, textbooks, teacher tables). `atlas0` payload values are migrated only for sources we do not hold locally (kaikki, ВТС, slovnyk.me caches, Караванський) at `medium`, to be superseded when re-extracted. Correctness fixes already queued (#8729 homographs, #8715 meanings) land as extractor fixes here, not later.
- **M3 Identity pass.** Run the matching of `identity.md` §4 over the VESUM denominator (442,458 entries) × ULIF checked rows; mint cards for every VESUM entry; attach ULIF rows at their confidence; fill the holding area with `unresolved` rows. Apply the 420 curated heteronyms as overlay `split` entries. Produce the split-candidate list (10,570 ULIF multi-homonym spellings ∪ 18,935 VESUM multi-entry lemmas ∪ 68 VESUM doublets ∪ 2,828 ULIF double-accent single tokens) for the language lane.
- **M4 Senses.** Seed senses from source units (§6 of `schema.md`); everything unaligned is `unsplit`.
- **M5 MWE cards.** From ULIF phraseology (8,131 sections), `frazeolohichnyi` (24,683 rows) and the 639 multiword articles, with component links via ULIF anchors.
- **M6 Overlay bootstrap.** Heteronym side file, `related_entries` verdicts, existing CEFR overrides, known conflict resolutions → overlay files, each with author/lane/date/evidence.
- **M7 Build and exporters.** `build` produces `atlas.db` from `(S, V, O, R)`; `export_runtime_shards.py`, `generate_search_index.py`, `generate_practice_deck.py`, `generate_daily_pool.py`, `practice_deck/publish.py` and the dataset exporter read cards and write `derivations`. Two consecutive builds must be identical (CI check).
- **M8 Takedown rehearsal.** Planted-source test (#8980): suppress at source, entry and assertion level, rebuild, verify every output type and the report; attempt a reimport.
- **M9 Rollback.** `atlas.db` is derived; rollback = rebuild from the previous `(S, V, O, R)`; the `atlas0` copy is kept read-only until C2 closes.

## 3. Gate 1 — A1–B1 vertical slice (before C1 touches the full store)

- **Denominator:** the PULS A1–B1 words (962 + 1,386 + 2,164 = 4,512 rows in `puls_cefr`; 3,274 of today's articles carry a PULS A1–B1 level) plus the MWEs and aspect pairs they need. Every one of them goes end to end: assembly → Atlas page → practice items in every live mode → dataset projection → takedown run → rollback.
- **Pass criteria:** every slice card renders; no practice item depends on an `unresolved`/`conflict` field (test: an ineligible field never yields an item, #8983); each exercise records card and generator versions; takedown of a planted source removes it from every output and the report lists affected modules; rebuild is byte-identical; language-lane sample review of generated items passes.

## 4. Gate 2 — the ~200-card golden set (before full scale; gates C2)

- **Composition (targets, drawn from the measured candidate lists):** 40 homograph pairs/triples from the 2,811 Atlas lemma articles with several ULIF homonyms (must include `замок`, `коса`, `варення`, `броня`, `виносити`); 20 stress doublets (`помилка`, `визволення`, VESUM's 68 declared doublets, ULIF double-accent tokens); 20 proper-name/common-noun pairs; 20 aspect pairs and 5 aspect homographs (`вибігати`); 20 MWEs listed under several headwords; 20 multi-sense words with unsplit senses (`ключ`); 20 conflicts from the 78 stress disagreements (both genuine, `вряди-годи`, and identity artefacts); 10 cards whose only source is tier 3; 10 cards with ULIF header damage; 15 with a `russification_exposed` pair (#8982).
- **Adjudication:** a language lane (Gemini via AGY or GPT via Codex, outside the author's family) records the expected identity and states per card as overlay `identity` entries; the operator signs the set.
- **Pass criteria:** the build reproduces the adjudicated identity for every golden card (splits, merges, `variant` vs `conflict`, unresolved rows); zero model-written Ukrainian; every assertion has a locator that resolves in the read-only databases; removal of any single source recomputes states as the rules say; the set is re-run on every rules or extractor change.

## 5. Ordering and dependencies
#8979 register entries for the unregistered Atlas sources → M0. #8334 language-lane read on `identity.md` → M3. #8400 harvest completion (19 rows in #9123) → M2 for ULIF fields; the slice can start on VESUM + PULS + textbooks + teacher content without it. #8980 takedown design → M8. #8983 rules → Gate 1.

## 6. Consumer inventory (from `git grep -l "atlas\.db"`), change needed

| consumer | change |
| --- | --- |
| `scripts/atlas/atlas_db.py` (writer: `migrate_manifest`, alias validation) | becomes the `build` entry point reading `(S, V, O, R)`; manifest migration retired after M2 |
| `scripts/atlas/export_runtime_shards.py`, `site/src/lib/lexicon/atlasDb.ts`, `sqlite-atlas-data-source.ts`, `word-atlas-article-model.ts`, `atlas-static-paths.ts` | read cards + resolutions; spelling routes resolve to one or several cards; per-field citations from assertions |
| `scripts/atlas/fill_local.py`, `scripts/lexicon/enrich_heteronyms.py`, `curated_heteronyms_batch*.py`, `sync_curated_heteronyms_ts.py`, `heritage_calque_wave.py`, `reconcile_calque_clusters.py`, `ohoiko_paired_headword_split.py`, `admit_*` | fillers become extractors that emit assertions; heteronym scripts retired into overlay |
| `scripts/audit/generate_practice_deck.py`, `generate_daily_pool.py`, `generate_search_index.py`, `paronym_residual_audit.py`, `relation_residual_audit.py`, `scripts/practice/author_densified_pairs.py`, `scripts/practice_deck/publish.py` | read eligibility + resolutions; write `derivations`; key items by card/sense id |
| `scripts/backup-data.sh`, `scripts/benchmarks/generate_synthetic_atlas.py`, `tests/fixtures/atlas/build_runtime_shards_fixture.py` | new tables in backups and fixtures |
| `site/src/lexicon/WordAtlasArticle.tsx` (reads `curated-heteronyms`), `scripts/deploy/auto_deploy_eligibility.py`, `tests/test_sum11_source_guard.py` | side file removed; СУМ-11 guard reads tier 0 / `russification_exposed` only |
| tests (`tests/test_atlas_db.py`, `test_export_runtime_shards.py`, `test_generate_*`, `site/tests/unit/atlas-*.test.ts`) | fixtures on cards; add determinism, takedown and golden-set tests |

## 7. Risks
- Re-extraction changes shown values on live pages (e.g. `за́мок`-only stress becomes two cards); mitigated by the slice and by keeping `atlas0` as a comparison snapshot.
- Register gaps (ВТС, Караванський, orthographic dictionaries) block `licence_ref` for ~20,000 assertions; must land in M0.
- Unknown lineage of `ukrainian-word-stress` (18,448 stress rows) decides whether most stress fields are `verified` or `single-source`; resolve in the register before Gate 1.
