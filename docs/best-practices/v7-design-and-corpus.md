# V7 Design + Corpus Reference — load before any module work

> **READ ME FIRST** before designing writer/reviewer prompts, before firing builds, before promoting modules. This doc consolidates the V7 design intent, the corpus available, and the writer/reviewer prompt requirements. Authoritative siblings: [`docs/north-star.md`](../north-star.md) (escalator + audience + voice), [`docs/lesson-contract.md`](../lesson-contract.md) (artifact + tab shape), [`docs/decisions/2026-05-13-ulp-derived-student-aware-immersion.md`](../decisions/2026-05-13-ulp-derived-student-aware-immersion.md) (immersion model).
>
> **Why this doc exists**: 2026-05-23 m20 (a1/my-morning) was promoted then reverted because the orchestrator declared "first complete V7 module shipped" while the rendered MDX had an empty Activities tab, stale Resources tab, all 10 activities placed inline (vs ACTIVITY_CONFIGS INLINE 4-6 / WORKBOOK 6-9), and a writer prompt that didn't surface most of the corpus. The deterministic gates (python_qg + wiki_coverage + LLM 9.5/10) all passed on broken content because they check artifact correctness against narrow contracts, not "does the writer actually use the corpus the design assumes." This doc closes that loop.

---

## 1. V7 design — the destination

### 1.1 What we ship (`docs/north-star.md` v3.1)

A free, source-grounded **L2 escalator from zero-Ukrainian to the Ukrainian intellectual canon**. Three structurally different stages:

1. **A1 + A2 — literacy bootstrap (124 modules).** English carrier ramping out, Ukrainian growing. Immersion ramps progressively via cumulative-vocab derivation. End of A2 is structurally where the learner finishes the transition out of English.
2. **B1 + B2 + C1 — immersion preparation (319 modules).** 100% Ukrainian in every tab EXCEPT Tab 2 (Словник) which keeps English translations for new lemmas + idiom/expression explanations as the ONLY sanctioned English at B1+.
3. **Seminars — the destination (1,100+ modules).** Full-Ukrainian deep dives. Not in EPIC #1577 MVP cut but the gravitational center.

**Audience**: self-driven adult / older teen, peer voice, no AI tells, no "great job!" stickers. Real learners use these modules as their first contact — five excellent modules beat fifty-five mediocre.

### 1.2 The 4-tab module shape (`docs/lesson-contract.md` v3, panel-confirmed 2026-04-25)

Every module = ONE `.mdx` at `starlight/src/content/docs/{level}/{slug}.mdx` with EXACTLY four `<TabItem>` children in this order:

| # | EN | UK | Source artifact | Required content |
|---|---|---|---|---|
| 1 | Lesson | **Урок** | `module.md` after INJECT_ACTIVITY substitution | Prose narrative; ≥1 inline activity per major section (P3) |
| 2 | Vocabulary | **Словник** | `vocabulary.yaml` | `<FlashcardDeck>` + `<VocabCard>` items; carries English translations + idiom explanations (ONLY sanctioned English at B1+) |
| 3 | Activities | **Вправи** (P1) | `activities.yaml` | All activities; inline-and-aggregate per P2 (inline-injected ones ALSO appear here with `(see lesson, §<section>)` cross-reference) |
| 4 | Resources | **Ресурси** | `resources.yaml` + plan `references` | ≥1 entry required (P4); cite every source actually pulled from corpus |

**Panel-confirmed P-rules** (binding policy):
- **P1**: Tab 3 canonical UK label = `Вправи` (not `Зошит`)
- **P2**: Inline-AND-aggregate is INTENTIONAL — activity inline-injected in Tab 1 ALSO appears in Tab 3 aggregate with `(see lesson, §<section-title>)` cross-reference
- **P3**: ≥1 inline activity per major Tab 1 section; no max
- **P4**: ≥1 Tab 4 entry required; empty Tab 4 fails Python QG
- **P5**: Out-of-MVP-scope components are HARD-rejected at A1+A2+B1
- **P6**: B1+ Latin-character ratio ≤1% in Tab 1/3/4 body; Tab 2 + citation metadata exempt
- **P7**: VocabCard cross-link to dictionary SUPPRESSED until EPIC #1581 ships

### 1.3 Student-aware immersion — the BIG V7 design point

> **PRESENTATION PATTERN — READ FIRST** before any A1/A2 build: [`docs/best-practices/ulp-presentation-pattern.md`](ulp-presentation-pattern.md) — extracted Anna Ohoiko presentation moves (UK-first em-dash gloss, side-by-side bilingual, stress marks, UK-only Q&A, named persona) + S1→S6 progression with the DRASTIC S1→S2 step-change at ~A1 m41. The decision card below specifies the ARCHITECTURE (`compute_immersion_band`, gates, schema); the presentation-pattern doc specifies the WRITER EXECUTION moves. Both are required reading.

`docs/decisions/2026-05-13-ulp-derived-student-aware-immersion.md` (ACCEPTED):

- **Anna Ohoiko's ULP S1-S6 is the calibration corpus** (`data/references/private/ULP {1-6}-00`, gitignored)
- `compute_immersion_band(track, module_num, learner_state)` at `scripts/config.py:718` derives band from **cumulative_vocabulary count + plan.targets.new_vocabulary + lemma-frequency map**, NOT flat-%
- `USE_ULP_IMMERSION_DERIVATION = True` at `scripts/config.py:145` (live)
- **User direct directive 2026-05-14**: *"do not use flat-% immersion; use what we learned from ULP"*
- **User direct directive 2026-05-23**: *"we will create the lessons student aware, we try to follow the pattern anna ohoiko used in ulp for immersion, don't set hard limits, just tell the writer this is a new student and he already learned the previous n-1 lessons and now he is learning the nth lesson. This way we want to build up ukrainian and converge for the end of A2 where we will prep them for full immersion from b1 onward"*

What's wired (verified `scripts/build/linear_pipeline.py:52, 2629-2656`):
- `build_learner_state` + `format_learner_state` imported
- `{LEARNER_STATE}` placeholder at `linear-write.md:456`
- `{IMMERSION_RULE}` injected via `get_immersion_rule(level, sequence, learner_state=...)`

What needs verification before any new build (NOT YET DONE):
- `_has_learner_vocab_signal(learner_state)` returns True for the target module (depends on plan having `targets.new_vocabulary` — most A1 plans NOT backfilled)
- `compute_immersion_band` returns ULP-derived band, not flat-% fallback
- The `rule` text carries student-aware scaffolding, not legacy "stay in 15-25% UK"

### 1.4 Activity placement matrix

From `scripts/pipeline/config_tables.py:875-1300` + `docs/best-practices/activity-pedagogy.md`:

| Level | TOTAL | INLINE | WORKBOOK | ITEMS_MIN | VOCAB_TARGET |
|---|---|---|---|---|---|
| a1 | 10 | **4–6** | **6–9** | 6 | 20 |
| a2 | 12 | 4–6 | 8–11 | 8 | 25 |
| b1-core | 16 | 5–7 | 11–15 | 8 | 30 |
| b2 | 16 | 5–7 | 11–15 | 8 | 30 |
| c1-core | 16 | 5–7 | 11–15 | 8 | 30 |
| c2 | 12 | 4–5 | 8–10 | 6 | 30 |
| Seminars | 10 | 3–4 | 7–9 | 4 | 25–35 |

**Most activities go to workbook.** A1 splits 4-6 inline / 6-9 workbook out of 10 total. m20 ship promoted with 10 inline / 0 workbook — that's design violation, not just a tab-rendering bug.

**Hard placement rules**:
- `INLINE_ONLY_TYPES = {image-to-letter, letter-grid, watch-and-repeat}`
- `WORKBOOK_ONLY_TYPES = {essay-response, reading, cloze, critical-analysis, source-evaluation, debate, comparative-study, authorial-intent, translation-critique, etymology-trace, paleography-analysis, transcription, dialect-comparison}`
- All other types are BOTH_CONTEXTS — depends on level-specific config

`scripts/build/activity_repair.py` deterministically corrects misplacement (writer freelance is repaired).

---

## 2. The corpus — what writer + reviewer must actively USE

User direction 2026-05-23: *"we have a huge ukrainian corpus plus we gathered external blogs, ulp, youtube channels — all of their video subtitles. we have lots of different dictionaries. they are all in the rag db. but we have them as jsonl as well."* And: *"this is not just about correctly placing the activities. it is about you being aware all our resources, our corpus, and using them and creating the correct prompt for writers and reviewers."*

### 2.1 `data/sources.db` (SQLite + FTS5) — primary store

> **➡ Full, current, query-verified inventory: [`docs/corpus-inventory.md`](../corpus-inventory.md)**
> — all tables with live counts, the literary breakdown, the local-vs-GoogleDrive build
> architecture (the #1 gotcha), and the safe recipe to add content. The table below is a
> quick reference; keep it in sync with that doc (counts as of 2026-06-15).

| Table | Volume | MCP tool | Use for |
|---|---|---|---|
| `textbooks` / `textbooks_fts` / `textbook_sections` | 25.7K chunks Gr 1-11 | `mcp__sources__search_text`, `search_sources` | Textbook grounding citations — Караман, Захарійчук, Кравцова, Большакова, Заболотний, etc. |
| `literary_fts` / `literary_texts` | 137.7K chunks | `mcp__sources__search_literary` | Primary literary sources, chronicles, poetry, legal — Shevchenko, Franko, Lesya Ukrainka, Stus, Zabuzhko, etc. + folk primaries (35, `ukrlib-narod-dumy`). |
| `external_articles` / `external_fts` | (8 collections) | `mcp__sources__search_external` | Blogs, articles, podcasts, YouTube subtitles |
| `grinchenko` | 67K entries | `mcp__sources__search_grinchenko_1907` | Historical Ukrainian (1907) pre-Soviet attestation |
| `sum11` | 127K entries (7,152 Sovietized — #1659) | `mcp__sources__search_definitions` | Modern explanatory dictionary; check `sovietization_risk` flag |
| `frazeolohichnyi` | 25K entries | `mcp__sources__search_idioms` | Idioms + expressions for natural phrasing |
| `ua_gec_errors` / `ua_gec_errors_fts` | 8,937 pairs | `mcp__sources__search_ua_gec_errors` | Human-annotated error→correction (Grammarly UA team) — calques, case, gender, collocation |
| `balla_en_uk` | 79K entries | `mcp__sources__translate_en_uk` | EN→UK translation |
| `dmklinger_uk_en` | — | (companion) | UK→EN |
| `esum_etymology*` | A-Г | `mcp__sources__search_esum` | Etymological dictionary (vol 1 indexed; vols 2-6 in JSONL) |
| `paronyms_cache` | — | (audit checks) | Paronym warnings |
| `puls_cefr` | 5.9K words | `mcp__sources__query_cefr_level` | PULS CEFR vocabulary (A1-C1 tagged) |
| `style_guide` | 342 structured + 169 prose | `mcp__sources__search_style_guide` + `search_text source=antonenko-davydovych-yak-my-hovorymo` | Antonenko-Davydovych calques + Russianisms |

### 2.2 JSONL companions (`data/external_articles/`)

| File | Content | Search via |
|---|---|---|
| `ulp_blogs.jsonl` | ULP (Anna Ohoiko) blog posts | `search_external` |
| `ulp_youtube.jsonl` | ULP YouTube video subtitles | `search_external` |
| `pohribnyi_pronunciation.jsonl` | Pohribnyi pronunciation references | `search_external` |
| `istoria_movy.jsonl` | History-of-language content | `search_external` |
| `realna_istoria.jsonl` | Real-history channel | `search_external` |
| `komik_istoryk.jsonl` | Comic-historian channel | `search_external` |
| `imtgsh.jsonl` | IMTGSH channel | `search_external` |
| `other_blogs.jsonl` | Mixed-source blog corpus | `search_external` |

### 2.3 YouTube + extended corpus

- `data/youtube_discovery/patterns.yaml` + `ulp_grammar_guide_backfill.jsonl` — discovery + backfill
- `data/processed/esum_vol{1-6}.jsonl` — full ESUM (vol 1 indexed in sources.db; vols 2-6 JSONL-only)
- `data/literary_texts/` — raw literary corpus before FTS indexing
- `data/ubertext-freq/` — Ubertext frequency map (vocabulary sequencing signal)
- `data/zno/` — ZNO standardized test materials (exercise design reference)
- `data/translations/` — bilingual translation pairs
- `data/embeddings/modern_literary/` — vector embeddings
- `data/qdrant_db/` — Qdrant vector DB
- `data/references/private/` — ULP S1-S6 transcripts + 1000 Ukrainian Words + 500 Ukrainian Verbs + Ohoiko June book (gitignored, local only)
- `data/vesum.db` — VESUM morphological dictionary (409K lemmas / 6.7M forms)

### 2.4 MCP `mcp__sources__*` tools — the writer's hand

From `.claude/rules/mcp-sources-and-dictionaries.md`:

**Verification (single-primitive, preferred)**:
- `verify_word`, `verify_words`, `verify_lemma` — VESUM
- `check_modern_form` — VESUM modernity flags
- `check_russian_shadow` — Russian-morphology detection
- `verify_quote(author, text)` — Ukrainian quote attribution
- `verify_source_attribution(source, claim)` — claim-attribution check

**Search (compose-pattern, evidence retrieval)**:
- `search_sources` — UNIFIED entry point (preferred)
- `search_text` — textbook-only
- `search_literary` — literary-only
- `search_external` — blogs/articles/podcasts/YouTube subtitles
- `search_images` — textbook images (14K)
- `search_grinchenko_1907`, `search_esum`, `search_definitions`, `search_idioms`
- `search_style_guide` + `search_ua_gec_errors`
- `search_heritage` — MERGED archaism/historism/dialectism (Грінченко + ЕСУМ + slovnyk.me + Antonenko)
- `search_slovnyk_me` — slovnyk.me single-source
- `search_synonyms` — Ukrajinet WordNet (auto-translated, audit pending #1657)
- `query_wikipedia` — Ukrainian Wikipedia
- `query_pravopys` — Правопис 2019
- `query_cefr_level` — PULS CEFR

**Translation**:
- `translate_en_uk` — EN→UK (Балла)

**Degradable Enhancements**:
Dense rerank (used by `search_sources` unified retrieval) is designed as a degradable enhancement rather than a load-bearing requirement. If the MLX embedding worker refuses to spawn (e.g. on low-RAM machines under 32GB or when explicitly disabled via `SOURCES_MCP_NO_MLX=1`), the retrieval path degrades gracefully to standard SQLite FTS5-only ranking instead of raising an error.

---

## 3. Writer prompt requirements (`scripts/build/phases/linear-write.md`)

### 3.1 What MUST be in the writer prompt

1. **Full corpus surface** — list ALL `mcp__sources__*` tools with one-line descriptions. Writer should not have to guess what's available.
2. **External-collection specifics** — name the 8 external-article collections so writer queries them by slug for Resources tab citations.
3. **Inline vs workbook split** — communicate INLINE_MIN/MAX + WORKBOOK_MIN/MAX explicitly with the rationale "most activities go to workbook; inline activities are sparse interruptions to keep the lesson flowing."
4. **Student-aware framing** — not just "here's cumulative vocab" but actionable: "Do NOT introduce vocabulary the learner hasn't seen unless you also add it to `vocabulary.yaml` AND foreshadow it via context. Do NOT re-explain grammar the learner already knows. Treat the learner as having completed modules 1..N-1."
5. **Frequency-aware vocab selection** — prefer high-frequency lemmas from ubertext-freq when introducing new vocab.
6. **Cite-what-you-found** — every search the writer ran that produced content used in the module MUST be cited in Tab 4 Resources with the URL/chunk_id. The `resources_search_attempted` gate counts ONE call; the design demands citation of ALL pulls.
7. **ULP-derived immersion** — `{IMMERSION_RULE}` should carry student-aware text, not flat-% bands. Writer should know "this learner has seen N lemmas across N-1 modules" framing.

### 3.2 What MUST be in the reviewer prompt (`scripts/build/phases/linear-review-dim.md`)

Same corpus awareness as writer + check:
- Are activities split per ACTIVITY_CONFIGS INLINE/WORKBOOK?
- Does Tab 4 cite the writer's actual search results?
- Does prose respect student-aware framing (no unintroduced vocab, no re-explaining known grammar)?
- Does the module use multiple corpus layers (textbook + literary + external + idioms where appropriate) or only one?
- Is `{IMMERSION_RULE}` actually reflected in the prose, or did the writer ignore it?

---

## 4. Verify-before-promote checklist (MANDATORY)

Before declaring any module ship-ready, manually verify the rendered MDX against this list:

| # | Check | How |
|---|---|---|
| 1 | All 4 tabs render with expected content | Visit `http://localhost:4321/{level}/{slug}/` and click through all 4 tabs |
| 2 | Tab 3 (Activities) has activities (or correct fallback message) | Open MDX → verify `<TabItem label="Activities">` body is non-empty |
| 3 | Tab 4 (Resources) cites the corpus pulls | Cross-check `resources.yaml` URLs against what writer actually searched |
| 4 | Inline-and-aggregate cross-references appear (P2) | Tab 3 includes ALL activities; inline-injected ones carry `(see lesson, §...)` |
| 5 | Student-aware framing visible in prose | No unintroduced vocab; no re-explanation of known grammar; learner addressed as "you've seen X, now we're doing Y" |
| 6 | INLINE/WORKBOOK split respected | A1: ~4-6 inline / ~6-9 workbook. NOT 10 inline / 0 workbook |
| 7 | Activity types per-level allowed | No A2+ types at A1; no seminar types in MVP |
| 8 | Tab 2 (Vocabulary) has FlashcardDeck + VocabCards | Not just a markdown table |
| 9 | Dialogues use `<DialogueBox>` OR `> ` blockquotes | NOT em-dash bare lines |
| 10 | IPA notation present where phonetic_rules obligations require | Surfaces in :::caution blocks per writer prompt |

**If any check fails → no promote.** Deterministic gates passing is necessary but not sufficient.

---

## 5. What's known-broken in current V7 (as of 2026-05-23)

These need fix before next promote:

1. **MDX assembler Tab 3 fallback message not rendering** (`scripts/generate_mdx/core.py:336-342`) — when ALL activities are inline-injected, the "No workbook activities for this module; see the Lesson tab" message is supposed to emit but doesn't. Likely stripped by `_apply_shared_transforms` or downstream pass.
2. **MDX assembler Tab 4 reading stale legacy not canonical resources.yaml** — promoted m20 had Захарійчук Grade 4/Караман/Кравцова instead of Захарійчук Grade 1 p.24+p.52 from resources.yaml. Trace `format_resources_for_mdx()`.
3. **Inline-and-aggregate P2 not implemented in assembler** — current code REMOVES inline-injected from Tab 3 instead of dual-rendering with cross-reference.
4. **Writer prompt under-specifies corpus** — Section 3.1 list of what's missing.
5. **Writer prompt under-specifies INLINE/WORKBOOK split** — has placeholder values for `{INLINE_ALLOWED_TYPES}` + `{WORKBOOK_ALLOWED_TYPES}` but doesn't explain "most go to workbook" intent.
6. **Reviewer prompt not yet audited for corpus + student-aware awareness** (`scripts/build/phases/linear-review-dim.md`).
7. **ULP-derivation actual output for a module not yet verified** — flag is on, function exists, placeholders are wired, but no smoke test confirming the `rule` text + cumulative-vocab signal actually flows through to writer for a real module.
8. **`vesum_verified` false-flags authentic archaisms / dialectisms / poetic forms** — VESUM is the modern-standard dictionary, so authentic Ukrainian that it doesn't enumerate (`другоє` in a verify_quote'd folk song, `ягілки`/`перекличка`, archaic `-оє` poetic endings) is wrongly treated as a bad-form/russianism. Hits folk, lit (poetry), hist (chronicles), oes/ruth (philology). **Design fix = shared Heritage Attestation Engine** — see [`heritage-attestation-engine.md`](heritage-attestation-engine.md). It is the SAME classifier as the Word Atlas §5/§6 decolonization layer (`word-atlas-design.md`, #2882): build once, two consumers (Atlas renders badges; the gate allows authentic / blocks russianisms). `#2899` folk allowlist is the interim stopgap.

---

## 6. Decisions confirmed by user across this work

| Date | Direction | Effect |
|---|---|---|
| 2026-05-14 | "do not use flat-% immersion; use what we learned from ULP" | PR1+PR2 of ULP-derived immersion (decision card 2026-05-13) |
| 2026-05-23 | Per-section word counts are GUIDANCE not error | PR #2206 plan_sections advisory |
| 2026-05-23 | Hyphenated multi-word Ukrainian constructions don't fail just because VESUM has no compound entry | PR #2206 VESUM constituent fallback |
| 2026-05-23 | m20 NOT ready for production with empty Activities tab + stale Resources | m20 revert + this doc |
| 2026-05-23 | Student-aware (n-1 lessons learned), no hard limits, scaffold from A1 to A2 transition where B1+ full immersion starts | this doc Section 1.3 |
| 2026-05-23 | Writer + reviewer must be AWARE of all corpus (sources.db + jsonl + YouTube subs + blogs + dictionaries) | this doc Section 2 + 3 |

---

## 7. How to use this doc

**Before any module work:**
1. Read this doc end-to-end. The corpus + design picture must be loaded before you touch a writer/reviewer prompt OR fire a build.
2. Cross-reference with `docs/north-star.md` + `docs/lesson-contract.md` + `docs/decisions/2026-05-13-ulp-derived-student-aware-immersion.md` if anything here is unclear.
3. Verify ULP-derivation actually works for the target module (Section 1.3 verification steps).

**Before promote:**
1. Run the Section 4 verify-before-promote checklist.
2. ALL 10 checks pass before declaring ship-ready.
3. If any fail → fix root cause, rebuild, re-verify.

**Updating this doc:**
- Whenever the corpus grows (new sources.db tables, new jsonl files, new MCP tools), add the row(s) to Section 2.
- Whenever the design evolves (new P-rules, new tab requirements, new placement matrix entries), update Section 1.
- Whenever a writer/reviewer prompt rebuild lands, audit Section 3 against the new prompts.
- Whenever a verify-before-promote check is added/removed, update Section 4.

This doc is the SSOT for "what the writer + reviewer must know" and "what we verify before shipping." All other docs reference it; it references the authoritative design + decision docs but does not duplicate them.
