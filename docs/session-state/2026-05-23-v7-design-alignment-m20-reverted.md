---
date: 2026-05-23
session: "V7 design alignment + m20 promote REVERTED — comprehensive corpus + design + gap audit so next session can resume with full context"
status: red-rolled-back-m20 + design-alignment-captured + new-feature-pending-user-description
main_sha: 944f4200e4  # revert of d165868535 a1/my-morning promote
main_green: clean (review/review advisory persists on every PR)
working_tree_dirty: pre-existing carry-overs only (.agents/mcp_config.json, audit/2026-05-21-flash-3.5-ua-quality/, curriculum/l2-uk-en/_orchestration/, docs/dispatch-briefs/2026-05-21-agy-mcp-telemetry-shim-codex.md)
prs_merged_this_session:
  - "#2206 fix(linear_pipeline): plan_sections per-section advisory + vesum hyphenated multi-word fallback"
  - "#2207 fix(wiki_coverage_gate): location-fallback when writer's anchor doesn't resolve"
prs_wip_unmerged: []
active_dispatches: []
active_builds: []
builds_completed_this_session:
  - "#14 build/a1/my-morning-20260522-063200 — promoted as `d165868535` then REVERTED as `944f4200e4` after surfaced design-misalignment: empty Activities tab, stale Resources tab, writer prompt not surfacing full corpus, inline/workbook activity split not communicated"
headline_finding: "m20 (a1/my-morning) was promoted prematurely. The promote commit is reverted on main. The pipeline+gates have shipped fixes (PR #2206 + #2207 land genuine gate-fragility improvements) but the writer prompt + MDX assembler + reviewer prompts are NOT corpus-aware in the way the V7 design demands. Before any more module promotes, the writer and reviewer prompts need to be rebuilt to be aware of (1) the full corpus available via mcp__sources__* + jsonl files, (2) the ULP-derived student-aware immersion model, (3) the activity inline/workbook split per ACTIVITY_CONFIGS, (4) the lesson-contract.md tab requirements + P2 inline-and-aggregate rule. User confirmed alignment on this picture and will describe a new V7 feature next session."
next_session_first_item: "Read this handoff + read `docs/poc/poc-lesson-design.html` for visual layout reference. User has a new V7 feature to describe. After feature description: design the writer + reviewer prompt rebuild that makes both fully corpus-aware AND addresses the new feature. NO MORE BUILDS UNTIL THIS IS DONE. The cascade of gate fixes (#2204→#2206→#2207) was necessary but not sufficient — content quality requires the writer to actually use the corpus, not just satisfy deterministic gates."
---

# 2026-05-23 V7 design alignment — m20 reverted, picture clarified, new feature pending

## TL;DR — what changed in this session

| # | Action | State |
|---|---|---|
| 1 | PR #2206 (plan_sections advisory + VESUM hyphenated fallback) | merged @ `524f4a2ac2` |
| 2 | PR #2207 (wiki_coverage_gate location-fallback) | merged @ `0c55dfe585` |
| 3 | m20 a1/my-morning build #14 (9.5/10 LLM review, 18/18 wiki, python_qg ✅) | **promoted then REVERTED** |
| 4 | Design alignment audit (this handoff) | **complete — load this first next session** |

## Why m20 was reverted

The build passed every deterministic gate AND the LLM dim reviewer at 9.5/10, but **the published MDX is empirically broken** + the production pipeline is **not aware of the full corpus the design assumes it uses**.

Empirical defects in the promoted MDX:
1. **Tab 3 (Activities) completely empty** — `<TabItem label="Activities">\n\n</TabItem>`. Not even the "No workbook activities" fallback message rendered. All 10 activities are inline-injected via `<!-- INJECT_ACTIVITY: act-N -->`. The MDX assembler removes inline-injected from Tab 3 (per `scripts/generate_mdx/core.py:330-347`), then emits nothing — even the fallback string is being eaten by `_apply_shared_transforms` or some downstream pass.
2. **Tab 4 (Resources) has stale legacy content** — shows `Захарійчук Grade 4 p.162 / Караман p.176 / Кравцова p.113`, but canonical `resources.yaml` has `Захарійчук Grade 1 p.24 + p.52`. The assembler's `format_resources_for_mdx()` isn't reading the freshly-promoted resources.yaml.
3. **All 10 activities went inline; 0 to workbook** — violates `ACTIVITY_CONFIGS["a1"]` which prescribes INLINE 4-6 / WORKBOOK 6-9 (10 total). Writer prompt does not communicate the inline/workbook split.
4. **Tab 4 doesn't cite external corpus** — only textbooks. The writer made 1 `query_wikipedia` call (satisfies `resources_search_attempted` gate) but didn't pull from ULP blogs, ULP YouTube subtitles, Pohribnyi pronunciation, Історія мови, Реальна історія, Комік історик, IMTGSH, or other blogs (all available in `data/external_articles/*.jsonl` + indexed in `sources.db` `external_articles` / `external_fts` tables).
5. **Student-aware immersion possibly not ULP-deriving** — `learner_state` is imported + `{LEARNER_STATE}` placeholder is in the prompt + `USE_ULP_IMMERSION_DERIVATION = True` at `config.py:145`. But I haven't verified that `compute_immersion_band` for module 20 with that learner_state actually returns ULP-derived bands (vs falling back to flat-% from static IMMERSION_POLICIES).

## Section 1 — The full V7 design (single source of truth)

### 1.1 Destination

From `docs/north-star.md` (v3.1, signed off by Codex + Gemini in `architecture` channel thread `6de2be4789394536abdb6356cd5bb006`):

> The destination is engaging directly with the Ukrainian intellectual tradition — Shevchenko, Franko, Lesya Ukrainka, Stus, Zabuzhko, Andrukhovych, Pidmohylny, Khvylovy, Zhadan; Hrushevsky and Plokhy on history; Hulak-Artemovsky and the Cossack chronicles; Ruthenian Baroque sermons; Old East Slavic manuscripts. L2 acquisition is the cost of admission, not the finish line.

The MVP is A1+A2+B1 (218 modules) — the L2 escalator that leads to the seminars (1,100+ modules). Five excellent modules beat fifty-five mediocre ones.

### 1.2 Lesson shape (lesson-contract.md v3, panel-confirmed 2026-04-25)

Every module = ONE `.mdx` with FOUR `<TabItem>` children:

| # | EN | UK | Source | Constraints |
|---|---|---|---|---|
| 1 | Lesson | Урок | `module.md` after INJECT_ACTIVITY substitution | Prose narrative; ≥1 inline activity per major section (P3) |
| 2 | Vocabulary | Словник | `vocabulary.yaml` | `<FlashcardDeck>` + `<VocabCard>`; the ONLY sanctioned English at B1+ |
| 3 | Activities | Вправи | `activities.yaml` | Inline-and-aggregate (P2): every activity inline-injected in Tab 1 ALSO appears in Tab 3 aggregate with `(see lesson, §<section>)` cross-reference |
| 4 | Resources | Ресурси | `resources.yaml` + plan `references` | ≥1 entry required (P4); cite ALL used sources from corpus |

### 1.3 Student-aware immersion (the BIG V7 design point)

`docs/decisions/2026-05-13-ulp-derived-student-aware-immersion.md` (ACCEPTED):

- **Anna Ohoiko's ULP S1-S6 is the calibration corpus** (`data/references/private/ULP {1-6}-00 Lesson Notes`, gitignored)
- **Replace flat-% bands** with `compute_immersion_band(track, module_num, learner_state)` at `scripts/config.py:718`
- **Inputs**: cumulative_vocabulary count + plan.targets.new_vocabulary + lemma-frequency map
- **Tell the writer "this learner has seen modules 1..N-1"** — soft scaffolding, not hard caps
- **User direct directive** (2026-05-14 session): *"do not use flat-% immersion; use what we learned from ULP"*

What's wired today (verified):
- `USE_ULP_IMMERSION_DERIVATION = True` at `scripts/config.py:145`
- `compute_immersion_band(track, module_num, learner_state)` at `scripts/config.py:718`
- `build_learner_state` + `format_learner_state` imported at `scripts/build/linear_pipeline.py:52`
- `{LEARNER_STATE}` placeholder in writer prompt at `scripts/build/phases/linear-write.md:456`
- `{IMMERSION_RULE}` injected at `linear-write.md:460` via `get_immersion_rule(level, sequence, learner_state=...)` at `linear_pipeline.py:2656`

**STILL TO VERIFY** before next build:
- `_has_learner_vocab_signal(learner_state)` returns True for module 20 (depends on plan having `targets.new_vocabulary` block — not all A1 plans have been backfilled)
- The `rule` field of the derived band actually carries student-aware scaffolding text, not legacy "stay in 15-25% UK"
- The writer's output for module 20 actually reflects student-aware choices

### 1.4 Activity placement matrix

From `scripts/pipeline/config_tables.py:875-1300+` + `docs/best-practices/activity-pedagogy.md`:

| Level | TOTAL | INLINE | WORKBOOK | ITEMS_MIN | VOCAB_TARGET |
|---|---|---|---|---|---|
| a1 | 10 | 4-6 | 6-9 | 6 | 20 |
| a2 | 12 | 4-6 | 8-11 | 8 | 25 |
| b1-core | 16 | 5-7 | 11-15 | 8 | 30 |
| b2 | 16 | 5-7 | 11-15 | 8 | 30 |
| c1-core | 16 | 5-7 | 11-15 | 8 | 30 |
| c2 | 12 | 4-5 | 8-10 | 6 | 30 |
| HIST/BIO/ISTORIO/LIT/OES/RUTH | 10 | 3-4 | 7-9 | 4 | 25-35 |

Per-type placement:
- `INLINE_ONLY_TYPES = {image-to-letter, letter-grid, watch-and-repeat}`
- `WORKBOOK_ONLY_TYPES = {essay-response, reading, cloze, critical-analysis, source-evaluation, debate, comparative-study, authorial-intent, translation-critique, etymology-trace, paleography-analysis, transcription, dialect-comparison}`
- All other types are BOTH_CONTEXTS — work in either placement.
- `scripts/build/activity_repair.py` deterministically corrects misplacement.

Per-level allowed types are in `ACTIVITY_CONFIGS` (~28 levels × per-type matrix). Writer must NOT emit forbidden types per level.

### 1.5 P-rules (panel-confirmed 2026-04-25, binding policy)

- **P1**: Tab 3 canonical UK label = `Вправи` (not `Зошит`)
- **P2**: Inline-AND-aggregate rendering is INTENTIONAL — activity referenced via INJECT_ACTIVITY in Tab 1 ALSO appears in Tab 3 aggregate with `(see lesson, §<section-title>)` cross-reference. **Current MDX assembler violates this** (removes inline-injected from Tab 3 instead of dual-rendering with cross-reference).
- **P3**: ≥1 inline activity per major Tab 1 section. No max cap; writer discretion.
- **P4**: ≥1 Tab 4 entry required (panel-confirmed; empty Tab 4 fails Python QG)
- **P5**: Out-of-scope MVP components are HARD-rejected at A1+A2+B1
- **P6**: B1+ Latin-character ratio ≤1% in Tab 1/3/4 body; Tab 2 + citation metadata exempt
- **P7**: VocabCard cross-link to dictionary section SUPPRESSED until EPIC #1581 ships

## Section 2 — The corpus (what writer + reviewer should ACTIVELY use)

The user emphasized: *"we have a huge ukrainian corpus plus we gathered external blogs, ulp, youtube channels — all of their video subtitles. we have lots of different dictionaries. they are all in the rag db. but we have them as jsonl as well."*

### 2.1 `data/sources.db` (SQLite + FTS5) — primary store

Tables (verified via `sqlite3 data/sources.db ".tables"`):

| Table | Content | Volume | Tool |
|---|---|---|---|
| textbooks / textbooks_fts | Grades 1-11 textbook content | 23K chunks | `mcp__sources__search_text`, `mcp__sources__search_sources` |
| textbook_sections | Sectioned textbook content | — | (same as above) |
| literary_fts / literary_texts | Primary literary sources — chronicles, poetry, legal | 125K chunks | `mcp__sources__search_literary` |
| external_articles / external_fts | Blogs, podcasts, YouTube subtitles, articles | — | `mcp__sources__search_external` |
| grinchenko | Historical Ukrainian dictionary (1907) | 67K entries | `mcp__sources__search_grinchenko_1907` |
| sum11 | СУМ-11 explanatory (partially Sovietized — #1659) | 127K entries (7,152 flagged) | `mcp__sources__search_definitions` |
| frazeolohichnyi | Ukrainian idioms | 25K entries | `mcp__sources__search_idioms` |
| ua_gec_errors / ua_gec_errors_fts | Human-annotated grammatical error corpus | 8,937 pairs | `mcp__sources__search_ua_gec_errors` |
| balla_en_uk | EN→UK translations | 79K entries | `mcp__sources__translate_en_uk` |
| dmklinger_uk_en | UK→EN translations | — | (companion) |
| esum_etymology / esum_etymology_* | Etymological dictionary (vol. 1) | A-Г | `mcp__sources__search_esum` |
| esum_cognate_forms | Cognate map | — | (companion) |
| paronyms_cache | Paronym warnings | — | (used by checks) |
| puls_cefr | PULS CEFR vocabulary | 5.9K words | `mcp__sources__query_cefr_level` |
| style_guide | Antonenko-Davydovych structured | 342 entries + 169 prose chunks via textbooks | `mcp__sources__search_style_guide` + `search_text source=antonenko-davydovych-yak-my-hovorymo` |

### 2.2 JSONL companions (`data/external_articles/`)

| File | Content |
|---|---|
| `ulp_blogs.jsonl` | ULP (Anna Ohoiko) blog posts |
| `ulp_youtube.jsonl` | ULP YouTube subtitles |
| `pohribnyi_pronunciation.jsonl` | Pohribnyi pronunciation references |
| `istoria_movy.jsonl` | History-of-language blog |
| `realna_istoria.jsonl` | Real-history channel |
| `komik_istoryk.jsonl` | Comic-historian channel |
| `imtgsh.jsonl` | (channel TBD — likely IMTGSH) |
| `other_blogs.jsonl` | Mixed-source blog corpus |

### 2.3 YouTube discovery (`data/youtube_discovery/`)

- `patterns.yaml` — discovery patterns
- `ulp_grammar_guide_backfill.jsonl` — ULP grammar guide subtitles

### 2.4 Other data layers

- `data/processed/esum_vol{1-6}.jsonl` — full ESUM vols 1-6 (only vol 1 indexed in sources.db)
- `data/literary_texts/` — raw literary corpus
- `data/ubertext-freq/` — Ubertext frequency map (for vocabulary sequencing)
- `data/zno/` — ZNO standardized test materials
- `data/translations/` — bilingual translation pairs
- `data/embeddings/modern_literary/` — vector embeddings
- `data/qdrant_db/` — Qdrant vector DB
- `data/references/private/` — ULP S1-S6 transcripts + 1000 Ukrainian Words + 500 Ukrainian Verbs + Ohoiko June book (gitignored, local only)
- `data/vesum.db` — VESUM morphological dictionary (409K lemmas / 6.7M forms)

### 2.5 MCP `mcp__sources__*` tools (30+ tools surfacing the above)

From `.claude/rules/mcp-sources-and-dictionaries.md`:

**Verification** (single-primitive, preferred):
- `verify_word`, `verify_words`, `verify_lemma` — VESUM lookup
- `check_modern_form` — VESUM modernity flags
- `check_russian_shadow` — Russian-morphology detection
- `verify_quote(author, text)` — Ukrainian literary quote attribution
- `verify_source_attribution(source, claim)` — attribution discusses claim

**Search** (compose-pattern, for evidence retrieval):
- `search_sources` — UNIFIED entry point across textbooks/literary/Wikipedia/external/wiki
- `search_text` — textbook-only
- `search_literary` — literary-only
- `search_grinchenko_1907`, `search_esum`, `search_definitions`, `search_idioms`
- `search_style_guide` (Antonenko structured), `search_ua_gec_errors`
- `search_heritage` — merged archaism/historism/dialectism check (Грінченко + ЕСУМ + slovnyk.me + Антоненко-Давидович)
- `search_slovnyk_me` — slovnyk.me single-source
- `search_synonyms` — Ukrajinet WordNet (auto-translated, audit pending #1657)
- `search_external` — blogs/articles/podcasts/YouTube subtitles
- `search_images` — textbook image search (14K images)
- `query_wikipedia` — Ukrainian Wikipedia
- `query_pravopys` — Правопис 2019 rules
- `query_cefr_level` — PULS CEFR

**Translation**:
- `translate_en_uk` — EN→UK (Балла)

### 2.6 What the writer should DO with the corpus (design intent)

When building a module like a1/my-morning:
1. **Topic discovery** — `query_wikipedia("ранкова рутина")` + `search_external("ранкова рутина")` (hits ULP blogs / Pohribnyi pronunciation / Історія мови)
2. **Textbook grounding** — `search_text("Захарійчук одягнутися прогулятися")` to find Захарійчук Grade 1 p.24 ("Мій день" frog story) + p.52 (Євген self-directed morning)
3. **Vocabulary sequencing** — frequency map (data/ubertext-freq) + PULS CEFR to pick A1-appropriate lemmas
4. **Russianism / Surzhyk filter** — `check_russian_shadow` on every UK lemma + `search_style_guide` + `search_ua_gec_errors`
5. **Cultural / decolonization** — Wikipedia + literary corpus for context
6. **Resources tab citations** — list every source actually pulled: textbook chunks + ULP blog posts + ULP YouTube clips + Pohribnyi audio + Wikipedia article URLs

The current writer prompt only surfaces a thin subset of this (see Section 3). The reviewer prompt is even thinner.

## Section 3 — Current V7 state (gaps surfaced this session)

### 3.1 Writer prompt (`scripts/build/phases/linear-write.md`, 707 lines)

**What it KNOWS:**
- `mcp__sources__search_text` for textbook grounding
- `mcp__sources__verify_words` / `verify_word` / `verify_lemma` / `verify_quote` / `verify_source_attribution`
- `mcp__sources__search_heritage` for archaism defense
- `mcp__sources__search_style_guide` + `search_ua_gec_errors`
- `mcp__sources__query_wikipedia` / `search_external` / `search_images` (for resources_search_attempted gate)
- `mcp__sources__check_modern_form` / `check_russian_shadow`
- `{LEARNER_STATE}` injection (cumulative vocab, known grammar)
- `{IMMERSION_RULE}` injection (band rule text)

**What it's MISSING:**
- `search_literary` (125K literary chunks — useful even at A1 for textbook-adjacent literary excerpts)
- `search_idioms` (25K idioms — for natural phrasing)
- `search_definitions` (СУМ-11 with sovietization flag)
- `search_grinchenko_1907` / `search_esum` (handled by search_heritage but not surfaced standalone)
- `search_synonyms` / `translate_en_uk` (vocabulary work)
- `query_cefr_level` (level-appropriateness)
- `query_pravopys` (orthography)
- The 8 external-article collection slugs (ulp_blogs, ulp_youtube, pohribnyi_pronunciation, istoria_movy, realna_istoria, komik_istoryk, imtgsh, other_blogs) — writer doesn't know to specifically query these for Resources tab citations
- Frequency map signal (data/ubertext-freq) — writer doesn't know to prefer high-frequency lemmas
- ZNO test material as exercise model
- The ACTIVITY_CONFIGS inline/workbook split — writer prompt has `{ALLOWED_ACTIVITY_TYPES}`, `{INLINE_ALLOWED_TYPES}`, `{WORKBOOK_ALLOWED_TYPES}`, `{ACTIVITY_COUNT_TARGET}` placeholders but doesn't EXPLAIN the split clearly enough for the writer to follow

### 3.2 Reviewer dim prompt (`scripts/build/phases/linear-review-dim.md`, 138 lines)

**NOT YET AUDITED THIS SESSION.** Open question for next session: does the reviewer surface the same corpus + check the same constraints + understand the same student-aware framing?

### 3.3 MDX assembler (`scripts/generate_mdx/core.py`)

**Bugs surfaced:**

1. **Tab 3 empty even when fallback should render** — line 336-342 emits "No workbook activities for this module; see the Lesson tab" when ALL activities are inline-injected. Build #14 has 10 INJECT_ACTIVITY markers in module.md (all 10 activities); `tab3_activities` becomes empty list. Code path SHOULD hit the `elif yaml_activities and injected_activity_ids` branch and emit the fallback. But MDX shows empty TabItem. Either `_apply_shared_transforms` strips the message OR a downstream pass clears it. **Need to trace and fix.**

2. **Tab 4 not reading canonical resources.yaml** — promoted MDX has `Захарійчук Grade 4 p.162 / Караман p.176 / Кравцова p.113`; resources.yaml has `Захарійчук Grade 1 p.24 + p.52`. The assembler must be falling through to a legacy default or reading the wrong file. **Need to trace `format_resources_for_mdx()` against the build #14 worktree.**

3. **Inline-and-aggregate P2 not implemented** — current code REMOVES inline-injected activities from Tab 3 (`tab3_activities = [a for a in yaml_activities if a.id not in injected_activity_ids]`). Per P2, Tab 3 should contain ALL activities, with cross-reference notes for those already shown inline (`(see lesson, §<section-title>)`).

### 3.4 Writer obligations the prompt under-specifies

- Inline vs workbook activity split (INLINE 4-6 / WORKBOOK 6-9 for A1)
- Citing every search the writer ran into Resources tab (currently the writer can call `query_wikipedia` once and discard the result if not useful, satisfying the gate but not the design)
- The 8 external-article collections — writer should query them specifically for the module topic
- Student-aware framing for prose: "you are not allowed to use vocab the learner hasn't seen, unless you introduce it in vocabulary.yaml AND the introduction is gated by foreshadowing"
- Frequency-sensitive vocab selection (prefer high-frequency from ubertext-freq when introducing new lemmas)

## Section 4 — Confirmed gate fixes that DID land cleanly this session

These don't need redo work:

| PR | Subject | Notes |
|---|---|---|
| #2206 | plan_sections per-section advisory + VESUM hyphenated multi-word fallback | Per-section min/max are advisory (only `missing_headings` halts); `літера-в-літеру`-style compounds verify via constituent fallback |
| #2207 | wiki_coverage_gate location-fallback | When writer's `location` doesn't anchor to a heading + isn't a literal substring, fall back to whole-artifact substance check |

These are correct fixes responding to user clarifications and they hold up. The mistake was treating them as sufficient for production-readiness when the broader design alignment was missing.

## Section 5 — Plan for next session (no builds until 1-3 done)

### P0 — Read + align (~30 min)

1. **Read this handoff** in full (~10 min)
2. **Read `docs/poc/poc-lesson-design.html`** for visual layout reference (~5 min, not yet read in this session)
3. **Read `docs/poc/poc-site-design.html`** for site framing (~5 min)
4. **Read `scripts/build/phases/linear-review-dim.md`** — reviewer prompt audit (~5 min, not yet read)
5. **Read user's new V7 feature description** when provided

### P0 — Audit + design (~1-2 hr, before any code)

1. **Verify student-aware immersion actually wires through for module 20**:
   - Run `_has_learner_vocab_signal(build_learner_state("a1", 20))` → does it return True?
   - If False, check whether `plan.targets.new_vocabulary` is populated for a1/my-morning plan
   - Run `compute_immersion_band("a1", 20, build_learner_state("a1", 20))` → does it return ULP-derived or flat-% fallback?
   - Check what `{IMMERSION_RULE}` text actually gets rendered into the writer prompt for module 20

2. **Trace MDX assembler bugs**:
   - Why is Tab 3 empty when the fallback message should render?
   - Why is Tab 4 not reading canonical resources.yaml?
   - Plan how to implement P2 inline-and-aggregate with cross-reference

3. **Design writer prompt rebuild** to be FULLY corpus-aware:
   - List ALL `mcp__sources__*` tools with one-line descriptions
   - Surface the 8 external-article collections explicitly
   - Make INLINE/WORKBOOK split explicit (with the numerical targets)
   - Make student-aware framing actionable (not just "here's cumulative vocab" but "do X, don't do Y based on it")
   - Frequency-aware vocab selection directive
   - Cite-what-you-found directive for Resources tab

4. **Design reviewer prompt audit + rebuild** to enforce the same:
   - Same corpus awareness
   - Same student-aware checking
   - Same activity-split awareness
   - Same Resources-tab-citation awareness

### P1 — Implement

After design alignment + user's new feature is known:
1. Ship writer prompt rebuild
2. Ship reviewer prompt rebuild
3. Ship MDX assembler fixes (Tab 3 fallback + Tab 4 source + P2 inline-and-aggregate)
4. Fire one A1 module build under the new prompts (NOT my-morning — pick one with cleaner upstream state, e.g. m1 sounds-letters-and-hello which has fresh plan)
5. **Manually inspect rendered MDX** against poc-lesson-design.html before promote
6. Only then consider promote

### P0 — User's new V7 feature

The user signaled they have an additional feature to add. Not yet described. Will be the focal point of the next session once alignment is confirmed.

## Section 6 — Active state at handoff

- **Active dispatches**: 0
- **Active builds**: 0 (m1 build was killed mid-stream after the design-alignment discovery)
- **Open PRs**: 0
- **Origin/main**: `944f4200e4` (m20 revert) — local; needs push
- **Build worktrees preserved per #M-10**: all a1-my-morning + the just-killed a1-sounds-letters-and-hello-20260522-085226
- **Starlight dev server**: up at http://localhost:4321; m20 page now shows the revert (back to manually-assembled build #11 preview)
- **Monitor API**: up at localhost:8765
- **Sources MCP**: up at localhost:8766

## Section 7 — Open follow-ups (renumbered for next session)

| # | Subject | Priority | Notes |
|---|---|---|---|
| 1 | **User describes the new V7 feature** | **P0** | wait-on signal |
| 2 | **Read poc-lesson-design.html + poc-site-design.html** | **P0** | not yet read this session |
| 3 | **Read linear-review-dim.md** | **P0** | reviewer-prompt audit pending |
| 4 | **Verify ULP-derivation produces useful output for module 20** | **P0** | three-command check at scripts/config.py |
| 5 | **Audit MDX assembler Tab 3 fallback bug + Tab 4 stale-resources bug** | **P0** | both observed in promoted m20 MDX |
| 6 | **Rebuild writer prompt for full corpus awareness** | **P0** | adds search_literary, search_idioms, 8 external collections, INLINE/WORKBOOK split clarity, frequency-aware vocab, student-aware framing |
| 7 | **Rebuild reviewer prompt for matching awareness** | **P0** | after #6 |
| 8 | **MDX assembler: implement P2 inline-and-aggregate with cross-reference** | P0 | lesson-contract.md panel-confirmed rule |
| 9 | **Apply M5/M6/M7 plan fixes** | P1 | per pre-revert handoff Section 4 |
| 10 | **Cross-validate gemini-tools + deepseek-tools writers** | P1 | once writer prompt rebuilt |
| 11 | `pedagogical_deviations_from_standard:` plan field convention (CC-1) | P2 | curriculum-wide schema enhancement |
| 12 | codex-tools rollout-flush race | P2 | inherited |
| 13 | PR #2168 amelina stub blocker | low | inherited |
| 14 | `review / review` CI auth broken | P2 | inherited |
| 15 | Writer-prompt directive against буквенного-class Russified adjectives | P2 | observed in build #13 |
| 16 | `claim_metadata` field always empty | P3 | minor diagnostic gap |

## Section 8 — Lessons from this session (autopsy notes)

### What I shipped that was wrong
- Promoted m20 declaring "first complete V7 module on main" when it was empirically broken (empty Activities tab, stale Resources tab).
- Treated python_qg + wiki_coverage + LLM-9.5/10 as sufficient signals for production-readiness.
- Did NOT verify the rendered MDX against `poc-lesson-design.html` before promote.
- Did NOT verify that student-aware immersion was actually deriving ULP-style for module 20.
- Did NOT verify writer/reviewer prompts were corpus-aware in the way the design demands.

### What the gates correctly caught (no false comfort)
- python_qg + wiki_coverage_gate + LLM dim review all PASSED on actually-broken content. These gates are necessary but not sufficient. They check artifact correctness against narrow contracts; they don't check "does the rendered MDX match the design PoC visually" or "did the writer actually USE the corpus the design assumes."

### What the design says that the pipeline doesn't yet enforce
- P2 inline-and-aggregate with cross-reference (Tab 3 should contain ALL activities, not just non-inline)
- INLINE/WORKBOOK split per ACTIVITY_CONFIGS (writer puts all 10 inline; no enforcement that 6+ go to workbook)
- Tab 4 should cite every corpus-pulled source — but the resources_search_attempted gate only counts ONE tool call satisfied
- Writer should query the 8 external-article collections + ULP YouTube subtitles for topic-relevant resources

### What needs to change in how I declare ship-ready

Before promote, manually verify against the design PoC:
1. All 4 tabs render with expected content
2. Activities tab has activities (or correct fallback)
3. Resources tab cites the corpus pulls
4. Inline-and-aggregate cross-references appear
5. Student-aware framing visible in prose
6. INLINE/WORKBOOK split respected

If any of these fail → no promote.

## Section 9 — User's exact words this session (for context preservation)

User clarifications (paraphrased + quoted):

1. "the secion wordcount is a guidance for the writer it is not a reason to drop an error, more is always welcome. the important is that the whole content is a whole and not less than the planned word count" → relaxed plan_sections per-section min to advisory in PR #2206

2. "there are many thesse kind of constructions in the ukrainian language [hyphenated multi-word forms like літера-в-літеру], do not drop error if vesum is not supporting it but we need to be able to check if they are correct with an another tool" → VESUM constituent fallback in PR #2206

3. **"in this state m20 is not ready for production"** → m20 reverted

4. "i remember we checked what v7 did not bring from v6, also please check the design poc how a lesson or module should look like, and config.py should tell how many and what kind of activites go to the prose and how many (most of them should ) go to the worksheet tab. we need to refer to extenral resouces, we have a huge database for external resouces and we should also cite resources we used. on the external tab" → audit V7-vs-V6 gap (this handoff Section 3), read poc-lesson-design.html (Section 5 P0 #2), config.py activity placement (Section 1.4 + 3.4), external resources (Section 2)

5. "We also agreed that we will create the lessons student aware, we try to follow the pattern anna ohoiko used in ulp for immersion dont set hard limits, just tell the writer this is a new student and he already learned the previous n-1 lessons and now he is learning the nth lesson. This way we want to build up ukrainian and converge for then end of A2 where we will pre them for full immerson ffrom b1 onwar." → student-aware immersion via ULP-derived `compute_immersion_band`; A2 end is the transition point; B1+ is full immersion (Section 1.3)

6. "you are aware of this? BE honest, if not you need to make sure ythat you are aware of these and the write and the reviewers are aware of this. This is the BIG THIMNG in v7 and the new design. Are we aligned?" → I was NOT aligned at start of this conversation; I am NOW aligned per this handoff

7. "we have a huge ukrainian corpus plus we gathered external blogs, ulp, , youtubr channles. all of their videos subtitles . we have lots of different dictionaries. they are all in the rag db. but we have them as jsonl as well." → corpus inventory in Section 2

8. "this is not just about correctly placing the activites. it is about you being aware all our resouces our corupus and using them and creating the correct prompt for writers and reviewes" → writer/reviewer prompt rebuild (Section 5 P0 #6 + #7)

9. "i eant to add an additional feature to V7 as well. after we are aligned" → new feature description pending — Section 5 P0 + Section 7 #1

## Section 10 — How next-session orchestrator should open

1. Read this handoff (you're doing it now)
2. Verify the state matches: `git log --oneline -5` should show `944f4200e4 Revert "feat(content): promote a1/my-morning..."` at top
3. Read `docs/poc/poc-lesson-design.html` + `docs/poc/poc-site-design.html`
4. Read `scripts/build/phases/linear-review-dim.md`
5. **Wait for user to describe the new V7 feature** — do not start any work before the feature is on the table
6. After feature description: propose unified design that includes the writer + reviewer prompt rebuild AND the new feature, get sign-off
7. Only then implement

**Do not fire builds. Do not promote modules. Do not declare ship-ready.** Until the writer + reviewer + assembler are fully corpus-aware AND the new feature is integrated AND a hand-verified module renders cleanly against poc-lesson-design.html, the pipeline is in a known-broken state.

The hard part isn't the gates anymore — it's the alignment between the design intent, the corpus available, and the prompts that drive the LLM agents. That's what next session ships.
