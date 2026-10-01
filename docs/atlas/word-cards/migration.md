# Word cards C0 — migration outline from today's `atlas.db` (r2; not implementation)

- **Scope:** the path from the spelling-keyed `atlas.db` (manifest `0.1`, 2026-09-11) to the card store of [`schema.md`](schema.md), gated by a **small pilot inventory**, then the A1–B1 vertical slice, then an independently adjudicated golden set before full scale. Implementation is C1/C2 (#8981 pilot first); this doc only fixes the order, the mappings and the gates. Every step is parameterised by the selected pilot inventory (Astra): nothing below runs at full scale before Gate 1 passes on the pilot.
- **Non-goals:** re-harvesting ULIF (#8400), the URL scheme (#8334 AC-02, Q10), the practice rules themselves (#8983).

## 1. Today's tables → card store

| today (`atlas.db`, measured 2026-09-28) | becomes | note |
| --- | --- | --- |
| `articles` (27,128; `slug` PK = spelling; `entry_type`, `pos`, `gloss`, `cefr`, `heritage_classification`, `review_state`, `visibility`) | identity-registry entries + `card_keys` (`atlas0:slug:<slug>`), `english_gloss`/`cefr`/`heritage_status` assertions with `source_id` from the payload's `source_provenance`, `visibility` kept on the card | one article may become several cards by a `split` event (2,811 lemma articles have several checked ULIF homonyms); the article's id is kept as a `split` card (`examples/zamok-legacy-split.json`) |
| `article_provenance` (27,241; `source_family`, `source_locator`, `extraction_mode`) | `source_keys` on the card and `licence_ref` on the migrated assertions | families: `textbook` 16,251 rows, `built_vocabulary` 3,405, `content_lexicon_grow` 2,829, `ulp` 1,793, `teacher_lesson` 2,169, `ohoiko` 718, … |
| `enrichment` (193,530; one row per `(slug, section)`, `payload_json`, `source`, `phase`) | one assertion per value inside the payload, `snapshot_id = atlas0@manifest-0.1/2026-09-11`, `extraction_version = atlas0-migration`, `extraction_confidence = medium` | sections: `heritage_status` 27,128, `morphology` 25,631 (VESUM), `literary_attestation` 24,220, `stress` 19,143, `translation` ~22,000 across 10 labels, `definition_cards` 12,468 (ВТС), `cefr` 7,903, `synonyms` ~4,400, `idioms` ~4,000, `form_notes` ~5,700, … |
| `aliases` (28,295; `transliteration` 27,128, `canonical` 821, `inflected_form` 344) | `aliases` kept, `target_slug` → `card_id` (several targets allowed) | spelling → card disambiguation |
| `related_entries` (3,690, all `synonym`, `provenance verified/unverified`) | `links` of type `synonym` with the verdict as a curator assertion | sense-less today; attach to `unsplit` senses until mapped |
| `article_payloads` (27,471; rendered JSON per route) | generated export (`export_runtime_shards.py` reads cards) | no longer a store |
| `manifest_metadata` | `build_manifest` | |
| `site/src/lib/lexicon/curated-heteronyms.ts` (420 lemmas) | overlay `split` entries + `atlas0:heteronym:<spelling>/<stressed>` keys + curator assertions (`gloss`, `short_label`) | retires the side file (#8334 in-scope item 3) |

## 2. Steps (pilot-parameterised; order per the design read)

- **M0 Freeze and measure.** Record content hashes of every input (`schema.md` §13): the `atlas0` file sha (`fcf802bd…`), the ULIF checked-row digest (`fe9f52cb…`), the VESUM sha, the register sha (`eb286a61…`), `rules`/`normaliser` versions. Land the register entries the schema needs (ВТС, Караванський, orthographic dictionaries, ukrainian-word-stress lineage; #8979 `open_questions`) and the lineage fields (`schema.md` §9.1). Freeze the **pilot inventory** (a manifest of source keys, ~150 lexemes spanning A1–B1 with ordinary controls and negative eligibility cases) and the sealed held-out expectations (§4).
- **M1 Identity registry bootstrap (the first `allocate` step).** One `wc_` id per existing article in `registry/atlas/identity/registry.json` (Q11, adopted: tracked `registry/`, generated stores stay under `data/`), with `atlas0:slug:<slug>` keys; MWE articles (639) as `mwe` cards; one `sr_` source-record id per source row the pilot reads, with its aliases (`schema.md` §12.1); `mint` / `source_record_mint` events. Ids are minted once, committed and reviewed, before any split; from here on the registry is a frozen build input and `build` refuses ids it does not allocate (`schema.md` §13).
- **M2 Overlay bootstrap (before identity resolution).** Existing curation becomes overlay batches at `registry/atlas/overlay/<batch>.yaml` with author/lane/date/evidence: the 420 curated heteronyms as `split` entries + `atlas0:heteronym:<spelling>/<stressed>` keys, `related_entries` verdicts, existing CEFR overrides, known conflict resolutions. Cross-family review of the batches. (Round 1 consumed this at M3 before introducing it at M6; fixed.)
- **M3 Re-extract, do not copy.** Assertions come from `sources.db`/`vesum.db` directly for every source we hold locally (ULIF, VESUM, PULS, `frazeolohichnyi`, Wiktionary, Грінченко, textbooks, teacher tables), each with its `source_record_key`. `atlas0` payload values are migrated only for sources we do not hold locally (kaikki, ВТС, slovnyk.me caches, Караванський) at `medium`, to be superseded when re-extracted. Correctness fixes already queued (#8729 homographs, #8715 meanings) land as extractor fixes here, not later.
- **M4 Identity pass (pilot inventory first).** Run the matching of `identity.md` §4 over the pilot's VESUM entries × ULIF checked rows with the M2 overlay applied; allocate successors through a committed registry step, then build against the frozen registry; attach ULIF rows at their confidence and basis; preserve each source's homonym partition and fill the holding area with `unresolved` rows for ВТС units whose correspondence to ULIF is not established, under the operator decision recorded 2026-09-29 (`schema.md` §16.3 item 1). The policy decision is settled; adjudicate each uncertain correspondence in the language lane before any merge or meaning practice. Mark ambiguous spelling-keyed rows. Produce the split-candidate list (10,570 ULIF multi-homonym spellings ∪ 18,935 VESUM multi-entry lemmas ∪ 68 VESUM doublets ∪ 2,828 ULIF double-accent single tokens) for the language lane — as a list, not as full-scale work.
- **M5 Senses.** Seed senses from the recorded seed source (`schema.md` §6); everything unaligned is `unsplit`.
- **M6 MWE cards (pilot's MWEs only).** From ULIF phraseology, `frazeolohichnyi` and the multiword articles the pilot needs, with component links via ULIF anchors; full expansion (8,131 sections, 24,683 rows) is a later coverage obligation.
- **M7 Build, exporters, derivations.** `build` produces `atlas.db` from `(S, V, I, O, R)`; `export_runtime_shards.py`, `generate_search_index.py`, `generate_practice_deck.py`, `generate_daily_pool.py`, `practice_deck/publish.py` and the dataset exporter read cards, honour `mapping_evidenced`, and write `derivations` with output identity and card versions. Two consecutive builds must be identical (CI check).
- **M8 Withdrawal, reimport and rollback rehearsal.** Planted-source test (#8980): suppress by `source`, `source_record` and `assertion_content` selector, rebuild, verify transitive invalidation through a generated assertion (`schema.md` §12.2), recomputed tombstoned public projections (the withdrawn value absent from the whole output), the report, and release retirement; load a **changed snapshot** (edited `content_sha256`, renumbered homonym, a corrected empty header) and confirm the selector still applies through the registry's correspondence, including an **ambiguous hold** where two rows match only on the weak key (both must be suppressed); change the normaliser version and confirm the content selector still matches; roll back to the previous inputs and confirm the suppression still applies (`schema.md` §12.1).
- **M9 Redirect and split checks.** Merge two pilot cards and split one; verify consumers resolve `merged_into`/`split_into`, learner-progress fixtures transfer only on item evidence and otherwise flag reassessment (`identity.md` §7.3).
- **M10 Gates.** Gate 1 on the pilot inventory (§3), then the independent golden-set gate (§4), then expand to the full PULS A1–B1 slice, then full scale.

## 3. Gate 1 — pilot inventory, then the A1–B1 vertical slice (before C1 touches the full store)

### Foundation preparation (#9293)

Use the shared project interpreter with `-m scripts.atlas.word_card_foundation`.
The public operations remain `freeze`, `allocate`, and `verify`; all paths and versions are explicit. `freeze` requires one sibling
`*source-admission-receipt.json` binding selection bytes and the independent
source report. Selection JSON is UTF-8, two-space indented, newline ended; retain its field order.
`verify --manifest registry/atlas/pilot/pilot-v1.json --registry
registry/atlas/identity/registry.json` reads committed inputs without writes.
The initial inventory keeps 150 source-local units, 272 verbatim selected rows,
114 legacy allocation metadata projections and 140 legacy aliases separately.
Legacy full literal-row hashes label omitted-row integrity; metadata hashes protect the projection. Unused legacy glosses are excluded. Source-backed POS
metadata preserves reviewed anchor/VESUM provenance without promoting identity.
The 22 source-only card mappings and supplementary correspondence stay unresolved.
Main-file and WAL digests are separate file provenance; selected-row digests identify literal captures, not logical whole-DB snapshots. DBs open read-only.
The whole permissions-register pin remains binding: a register change requires re-admission and re-freeze; reuse then refuses pending approved correspondence.
Locators contain local row IDs only. ULIF aliases use `ulif:register:`, actual
`ulif:content:` digests, and `ulif:record:<query>#<headword>#<label>`; PULS uses
`puls:record:<word>/<pos>/<level>`; phraseology uses `frazeolohichnyi:record:<word>`.
The approved bounded tuple clarification adds `table_row` evidence keys:
`ukrainian_word_stress:record:stress:v1:sha256:<digest>` hashes exactly parsed
`{form,source}`; source must agree with the outer stress row.
`ulif:record:paradigm:v1:sha256:<digest>` hashes `{parent,kind,payload}`. The parent
contains its literal content digest, query, headword, grammatical label and
homonym index, joined through an admitted parent locator. Paradigm payload keeps
exactly rows, raw HTML, response reference, group discriminator and source order.
Tuple JSON is UTF-8, sorted, compact, without newline or string normalization.
Local IDs/timestamps are excluded; accents, case, spaces and raw HTML remain.
Duplicate tuples/digest collisions refuse; null source content stays null.
Weak alias collisions are evidence, never lexical equivalence. Replay conserves
IDs, aliases and history byte-for-byte; changed/new inputs require correspondence.
Immutable output conflicts and source/WAL mutation refuse before writing.
Optional membership is `{"heldout":["source:key"],"replay":[]}`. Keys must resolve;
conservative unit/locator/card/alias closure must remain disjoint from replay.
Expected/adjudicated answers are excluded from all inputs even without membership.
Absent real membership, isolation remains unverified. `--for-evaluation` refuses
until authenticated operator authority and thresholds have an approved contract.
Exit 0 proves foundation preparation only, never full pilot or 220-case certification.

- **Denominator, first pilot:** the frozen pilot manifest (~150 lexemes with their MWEs and aspect pairs, including ordinary controls and cards that must stay ineligible). **Later coverage obligation, not a first-pilot gate:** all 4,512 PULS A1–B1 rows (962 + 1,386 + 2,164 in `puls_cefr`; 3,274 of today's articles carry a PULS A1–B1 level). VESUM accounting (Q-I5): every VESUM entry in scope is reported as *covered by a card*, *merged variant*, or *unresolved mapping*; source entries and cards are many-to-many and are counted separately.
- **Pass criteria:** every pilot card renders; **every applicable mode works and every ineligible combination stays excluded** (not "every card produces practice in every live mode"): an ineligible field never yields an item, an ambiguous spelling-level assertion never satisfies a level rule (`mapping_evidenced`), a `medium`-identity card never feeds meaning practice; each exercise records `card_version` and generator version; withdrawal, changed-snapshot reimport and rollback (M8) behave as specified with current suppressions enforced; redirect/split checks (M9) pass; rebuild is byte-identical; language-lane sample review of generated items passes; zero model-written Ukrainian.
- **Cut from the first pilot (kept as later obligations):** the full PULS slice before the first end-to-end proof; full proper-name/MWE expansion; dependencies on unrelated feature completion. **Not cut:** withdrawal, rollback, redirect/progress checks, semantic review, held-out evaluation.

## 4. Gate 2 — the golden set, with an independent held-out evaluation (before full scale; gates C2)

Round 1 supplied the expected identities as overlay `identity` entries and then checked the build against them, which proves overlay replay, not matching accuracy (Astra gap 7). The set is now two disjoint pools with an exact, frozen manifest.

- **Units.** The manifest lists **cases** (a spelling or source key under test), the **pairs/triples** each expands to, and the **cards** expected, so the count is unambiguous: the composition below totals **220 cases** before expansion — 200 hard cases plus 20 ordinary controls; overlap between categories is resolved at freeze time by listing each case once. The manifest's SHA-256 is recorded in the build manifest and in the gate report.
- **Composition (targets, drawn from the measured candidate lists):** 40 homograph cases from the 2,811 Atlas lemma articles with several ULIF homonyms (must include `замок`, `коса`, `варення`, `броня`, `виносити`); 20 stress doublets (`помилка`, `визволення`, VESUM's 68 declared doublets, ULIF double-accent tokens); 20 proper-name/common-noun pairs; 20 aspect pairs and 5 aspect homographs (`вибігати`); 20 MWEs listed under several headwords; 20 multi-sense words with unsplit senses (`ключ`); 20 stress disagreements from the 78 (both genuine, `вряди-годи`, and identity artefacts); 10 cards whose only source is tier 3; 10 cards with ULIF header damage; 15 with a `russification_exposed` pair (#8982); **plus 20 ordinary controls** (one VESUM entry, one ULIF homonym, agreeing stress) so the matcher is scored on abstention and coverage as well as on hard cases.
- **Replay pool (≈ 60 % of cases).** Expected identities are recorded as overlay `identity`/`split`/`merge` entries; the build must reproduce them exactly. This tests overlay replay and regression, and it is re-run on every rules, normaliser or extractor change.
- **Held-out pool (≈ 40 % of cases, disjoint).** Adjudicated **blind and independently**: each adjudicator (two lanes outside the author's family — recommendation: Gemini via AGY and GPT via Codex; disagreements to a third; `schema.md` §16.3 item 4) receives only the raw source rows (VESUM entries, ULIF checked rows, ВТС/СУМ-20 text) for the case, never the matcher's output or the replay pool's overlay, and records the expected mapping: which source rows form which card(s), expected `variant`/`conflict`, expected abstentions (`unresolved`). The expectations are **sealed**: stored outside every build input path (`tests/golden/heldout/<manifest-sha>/expected.json`, never under `registry/atlas/overlay/` or `registry/atlas/identity/`), and the build's overlay loader **refuses** any overlay entry that touches a held-out source key while the evaluation build runs (a test asserts this). The operator signs the sealed manifest.
- **Metrics (reported separately, never one number):** correct matches / expected matches (coverage), wrong matches (identity errors: a merge that should be a split, a split that should be a merge, a wrong partner), correct abstentions / expected abstentions, false abstentions, `variant`-vs-`conflict` accuracy, and the confusion by category. A held-out failure is fixed in the rules or extractors, never by adding the case to the overlay; once a held-out case has been used to fix a rule it moves to the replay pool and is replaced.
- **Pass criteria:** replay pool reproduced exactly; held-out identity errors = 0 on ordinary controls and ≤ the threshold the operator sets per category (recommendation: 0 wrong merges, ≤ 2 wrong splits, false abstentions ≤ 5 %); zero model-written Ukrainian; every assertion has a locator that resolves in the read-only databases; removal of any single source recomputes states as the rules say.

## 5. Ordering and dependencies
#8979 register entries for the unregistered Atlas sources and the lineage fields → M0. `schema.md` §16.3 decision 1 (settled by the operator on 2026-09-29; uncertain cross-source correspondences remain unresolved pending language-lane adjudication) → M4/M5, decision 2 → M5; decision 3 is adopted (M1/M2 paths). #8334 full identity/URL sign-off remains outstanding → M4. #8400 harvest completion (19 rows in #9123) → M3 for ULIF fields; the pilot can start on VESUM + PULS + textbooks + teacher content without it. #8980 takedown design → M8. #8983 rules (reading `mapping_evidenced`) → Gate 1. Decision 4 (held-out lanes) → Gate 2.

## 6. Consumer inventory (from `git grep -l "atlas\.db"`), change needed

| consumer | change |
| --- | --- |
| `scripts/atlas/atlas_db.py` (writer: `migrate_manifest`, alias validation) | becomes the `build` entry point reading `(S, V, I, O, R)`; manifest migration retired after M3 |
| `scripts/atlas/export_runtime_shards.py`, `site/src/lib/lexicon/atlasDb.ts`, `sqlite-atlas-data-source.ts`, `word-atlas-article-model.ts`, `atlas-static-paths.ts` | read cards + resolutions; spelling routes resolve to one or several cards; per-field citations from assertions |
| `scripts/atlas/fill_local.py`, `scripts/lexicon/enrich_heteronyms.py`, `curated_heteronyms_batch*.py`, `sync_curated_heteronyms_ts.py`, `heritage_calque_wave.py`, `reconcile_calque_clusters.py`, `ohoiko_paired_headword_split.py`, `admit_*` | fillers become extractors that emit assertions; heteronym scripts retired into overlay |
| `scripts/audit/generate_practice_deck.py`, `generate_daily_pool.py`, `generate_search_index.py`, `paronym_residual_audit.py`, `relation_residual_audit.py`, `scripts/practice/author_densified_pairs.py`, `scripts/practice_deck/publish.py` | read eligibility + resolutions (`mapping_evidenced`); write `derivations` with output identity and `card_version`; key items by card/sense id; learner-progress store resolves `merged_into`/`split_into` per `identity.md` §7.3 |
| `scripts/backup-data.sh`, `scripts/benchmarks/generate_synthetic_atlas.py`, `tests/fixtures/atlas/build_runtime_shards_fixture.py` | new tables in backups and fixtures |
| `site/src/lexicon/WordAtlasArticle.tsx` (reads `curated-heteronyms`), `scripts/deploy/auto_deploy_eligibility.py`, `tests/test_sum11_source_guard.py` | side file removed; СУМ-11 guard reads tier 0 / `russification_exposed` only |
| tests (`tests/test_atlas_db.py`, `test_export_runtime_shards.py`, `test_generate_*`, `site/tests/unit/atlas-*.test.ts`) | fixtures on cards; add determinism, takedown/reimport/rollback, split/redirect, replay-pool and sealed held-out tests |

## 7. Risks
- Re-extraction changes shown values on live pages (e.g. `за́мок`-only stress becomes two cards); mitigated by the slice and by keeping `atlas0` as a comparison snapshot.
- Register gaps (ВТС, Караванський, orthographic dictionaries) block `licence_ref` for ~20,000 assertions; must land in M0.
- Unknown lineage of `ukrainian-word-stress` (18,448 stress rows) decides whether most stress fields are `verified` or `single-source`; resolve in the register before Gate 1.
- 687 PULS A1–B1 rows are spelling-ambiguous across ULIF homonyms (`schema.md` §4); until they are mapped (guideword, overlay), those cards fail the level-band rule and the pilot's eligible set is smaller than the slice. This is by design (ambiguous evidence is not eligibility), but it must be budgeted in the language lane's overlay work.
