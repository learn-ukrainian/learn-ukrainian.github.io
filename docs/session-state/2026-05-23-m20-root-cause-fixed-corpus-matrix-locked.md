---
date: 2026-05-23
session: "m20 root cause fixed (promote + learner_state); per-level corpus matrix locked via user interview; word atlas designed as separate top-level section; writer-prompt rebuild dispatched to Codex"
status: green-progress-blocked-on-writer-prompt-rebuild-pr
main_sha: edcb872323
main_green: clean (review/review advisory persists)
working_tree_dirty: pre-existing carry-overs only (.agents/mcp_config.json, audit/2026-05-21-flash-3.5-ua-quality/, curriculum/l2-uk-en/_orchestration/, docs/dispatch-briefs/2026-05-21-agy-mcp-telemetry-shim-codex.md)
prs_merged_this_session:
  - "#2211 fix(learner_state): planned-vocab fallback for not-yet-built modules — unblocks student-aware immersion"
  - "#2212 fix(promote_module): read MDX from build's curriculum tree, not stale starlight tree"
prs_wip_unmerged:
  - "#2213 docs(v7-design): word atlas design + HTML PoC + session dispatch briefs"
active_dispatches:
  - "writer-prompt-rebuild-2026-05-23 (Codex gpt-5.5 xhigh, branch codex/writer-prompt-rebuild-2026-05-23, brief in docs/dispatch-briefs/2026-05-23-writer-prompt-rebuild-codex.md, fired ~14:26Z)"
active_builds: []
builds_completed_this_session: []
headline_finding: "The original m20 handoff DOUBLE-misdiagnosed the broken module: (a) the 'Tab 3 fallback eaten by transforms' and 'format_resources_for_mdx not reading canonical resources.yaml' framings were both wrong — the assembler is correct end-to-end; the real bug is `promote_module._source_rel_for_mdx` reads MDX from `starlight/src/content/docs/` in the build branch (a stale Phase 4 exemplar from commit c91ae3bbe1), not from `curriculum/.../{slug}.mdx` where `assemble_mdx` actually writes. Fixed in PR #2212. (b) The student-aware immersion 'verify ULP-derived' check exposed that `_load_vocab` reads from built `vocabulary.yaml` artifacts, so for any module built before its predecessors exist, `cumulative_vocabulary = 0` → `compute_immersion_band` always picked the m01-03 band regardless of module number. Fixed in PR #2211 (planned-vocab fallback). Both fixes merged; m20 now sees 295 lemmas + band a1-m07-14. Also: locked per-level corpus-access matrix via user interview covering A1→A2→B1→B2→C1→C2→seminars. Writer-prompt rebuild brief authored + dispatched to Codex (in flight). Word atlas (Лексикон) designed as separate top-level site section + HTML PoC committed."
next_session_first_item: "Poll/review the writer-prompt rebuild Codex dispatch (writer-prompt-rebuild-2026-05-23). If PR opened: review against the brief, merge if green, then refire a1/my-morning build using the new prompt + already-merged promote/learner_state fixes. Validate the rebuilt MDX shows Tab 3 with workbook activities (4-6 inline + 6-9 workbook split respected) and Tab 4 cites canonical G1 resources. If validation passes, promote m20 as the first complete V7 module. Then sequential a1/m1, a1/m2, ..., a1/m7 per user's queue order. Concurrently: review + merge PR #2213 (session docs)."
---

# 2026-05-23 m20 root cause fixed + per-level corpus matrix locked + word atlas designed + writer-prompt rebuild in flight

## TL;DR — what changed in this session

| # | Action | State |
|---|---|---|
| 1 | Diagnosed real m20 root cause: TWO separate bugs (`promote_module` MDX path + `learner_state` vocab source) | both fixed |
| 2 | PR #2211 (learner_state planned-vocab fallback) | merged @ `c75d1694a6` — verified m20 now sees 295 lemmas + band `a1-m07-14` |
| 3 | PR #2212 (promote_module reads MDX from curriculum tree, not stale starlight tree) | merged @ `edcb872323` |
| 4 | Ran user interview locking per-level RAG/corpus access matrix (A1-C2 + seminars) | matrix encoded in writer-prompt rebuild brief |
| 5 | Designed Word Atlas (Лексикон) as separate top-level site section | design doc + HTML PoC committed; PR #2213 open |
| 6 | Authored + dispatched writer-prompt rebuild brief to Codex | in flight (~5 min in at session close) |
| 7 | Verified user clarification: INLINE 4-6 / WORKBOOK 6-9 split is intentional pedagogy, NOT a P2 dual-rendering bug | brief explicitly forbids changing the assembler or implementing P2 dual-render |

## Why the m20 revert handoff was wrong

The 2026-05-23 morning handoff (`docs/session-state/2026-05-23-v7-design-alignment-m20-reverted.md`) framed the broken m20 MDX as containing TWO assembler bugs + ONE design gap:

- "Tab 3 emit logic — fallback message eaten by `_apply_shared_transforms` or downstream pass"
- "Tab 4 `format_resources_for_mdx()` not reading canonical resources.yaml"
- "P2 inline-and-aggregate cross-reference not implemented"

**All three are misdiagnoses.** Diagnostic trace (reproducible from `.worktrees/builds/a1-my-morning-20260522-063200/`):

1. The build's `assemble_mdx` step ran correctly and committed a fresh MDX to `curriculum/l2-uk-en/a1/my-morning/my-morning.mdx` (commit `c78c8e38d4` inside the build worktree, 244 lines added). That MDX has:
   - Tab 1 with 8 inline activity components (ErrorCorrection, FillIn, MatchUp, TrueFalse, Translate)
   - Tab 3 with the proper fallback message: `*No workbook activities for this module; see the Lesson tab.*` ← assembler IS emitting it
   - Tab 4 citing canonical Захарійчук Grade 1 p.24 + p.52 ← assembler IS reading canonical resources.yaml

2. **But** `scripts/sync/promote_module.py` had `_source_rel_for_mdx(level, slug) → DOCS_ROOT / level / f"{slug}.mdx"` — i.e., `starlight/src/content/docs/{level}/{slug}.mdx`. That path in the build branch held a Phase 4 exemplar from commit `c91ae3bbe1` (pre-V7, from initial pipeline setup, no inline activities, stale G4/G10 resources). The promote read the wrong path → diff against main was empty → promote committed the stale exemplar's source files but NOT the MDX.

3. Net result: the served Starlight MDX was the OLD exemplar, not the build's fresh output. Both "Tab 3 empty" and "Tab 4 stale" stem from this single deploy-sync bug.

4. P2 inline-and-aggregate as I had drafted it (dual-render the same activity in Tab 1 + Tab 3) is also a misread. The user clarified mid-session that INLINE 4-6 (light theory-time checks) + WORKBOOK 6-9 (substantive after-lesson drill) are **DIFFERENT activities written for different contexts**, exactly as `ACTIVITY_CONFIGS["a1"]` encodes. The m20 build's writer violated this by emitting 10 inline + 0 workbook; the assembler correctly emitted the "No workbook activities" fallback as the signal the contract was broken. **The fix is in the writer prompt's inline/workbook clarity, NOT in the assembler.**

PR #2212 fixes the promote path. Future m20 promote will sync the actual build MDX into Starlight.

## Why student-aware immersion was load-bearing in name only

`scripts/pipeline/learner_state.py::_load_vocab` reads from `curriculum/l2-uk-en/{track}/{slug}/vocabulary.yaml` — i.e., **built-module artifacts**. For m20 (the only A1 module ever built), `_load_vocab` returned `[]` for m1, m2, ..., m19 because those slug directories don't exist yet — they haven't been built. Hence:

```
build_learner_state('a1', 20) →
  cumulative_vocabulary len: 0          ← BROKEN
  known_grammar len: 95                 ← OK (loaded from plans)
compute_immersion_band('a1', 20, learner_state=ls) →
  band key: a1-m01-03                   ← always the first-3-modules band
```

`_load_grammar` reads from `curriculum/l2-uk-en/plans/{track}/{slug}.yaml` (the plans), which exist for all A1 modules. That asymmetry between grammar (works) and vocab (empty) was the load-bearing diagnostic.

Fix (PR #2211): add `_load_planned_vocab(track, slug)` that reads `vocabulary_hints.required + vocabulary_hints.recommended` from the plan, and modify `_load_vocab` to try built-first, plan-fallback. Codex implemented + tested (5 new unit tests). After merge, verified:

```
build_learner_state('a1', 20) →
  cumulative_vocabulary len: 295        ← FIXED
  known_grammar len: 95
  first 5 lemmas: ['звук', 'літера', 'голосний', 'приголосний', 'привіт']
compute_immersion_band(...) →
  band key: a1-m07-14                   ← appropriate for 295-lemma exposure
```

Note: `a1-m07-14` is named by module-range from when bands were tied to module#, but selection is now vocab-count-driven per the 2026-05-13 ULP design. Whether 295 lemmas at m20 is the right exposure target is a plan-allocation question (do m1-m19 plans collectively teach enough?) — flagged as F7 below but not the next blocker.

## The locked per-level corpus-access matrix

User interview (questions Q1-Q14 in main session) produced this binding matrix. The writer-prompt rebuild brief (`docs/dispatch-briefs/2026-05-23-writer-prompt-rebuild-codex.md`) implements it verbatim in `scripts/build/phases/linear-write.md`.

| Level | Posture | Textbooks | Literary | External | Vocab source | Grammar/style |
|---|---|---|---|---|---|---|
| **a1** | scaffold-grounded | G1-4 (prefer G1-2) | curated subset (children's lit, folk songs, iconic phrases) | ULP (`ulp_blogs` + `ulp_youtube`) + `pohribnyi_pronunciation` | PULS A1 → freq top-1000 → ULP S1-S2 (stacked) | Pravopys + Antonenko (writer-side); UA-GEC + heritage + russian_shadow (reviewer-side) |
| **a2** | (same) | G1-5 | widened curated subset | (same as a1) | PULS A1+A2 → top-2000 → ULP S1-S4 | (same) |
| **b1** | (same) | G1-11 (full) | FULL `search_literary` corpus | All 8 collections | PULS A1+A2+B1 → top-5000 → ULP S1-S6 | (same) |
| **b2** | (same) + new content modes | (same) | (same) | (same) | (same) | (same) — adds literary commentary, cultural-analysis, historical narrative as content types |
| **c1** | **hybrid** (facts pre-cited, prose flow free) + academic ingestion required | (same) | (same) | (same) + peer-reviewed UA scholarship (post-ingestion) | (same, extend PULS to C1) | (same) |
| **c2** | (same as c1) | (same) | (same) | (same) | (same) | (same) |
| **seminar — hist/oes/ruth/istorio** | strict-2-source citation rule | full | full + ingested OES manuscripts + Ruthenian Baroque | full + ingested academic UA scholarship | (n/a — not vocab-driven) | (same) |
| **seminar — lit/bio + sub-tracks** | hybrid | full | full | full + ingested academic UA scholarship | (n/a) | (same) |

The interview also clarified decolonization sourcing for seminar modules: a **dedicated decolonization corpus** (Plokhy *Lost Kingdom*, Snyder *Reconstruction of Nations*, Magocsi, Subtelny, Hrycak, Kappeler) must be ingested as a tagged source category before any seminar fires. The myth-buster boxes pair imperial-narrative claims with named UA primary + secondary sources.

## Word Atlas (Лексикон) — design committed (PR #2213 open)

Per user direction mid-session: build a SEPARATE top-level site section (parallel to A1-C2 and Seminars in the nav) that renders per-lemma dictionary pages from existing `sources.db` + `vesum.db` + ESUM vols 1-6 jsonl + 8 external-article collections. NOT embedded into lessons; lessons cross-link into it.

The editorial moat over slovnyk.me is the decolonization layer:
- **Sovietization warning** (red `.myth-box` style) for any СУМ-11 entry with `sovietization_risk ≥ 1`
- **Heritage-defense badge** (green `.myth-box` style) when `search_heritage` returns `is_russianism=false` + pre-Soviet attestation
- **Calque warning** (yellow `.rule-box` style) for Antonenko-Davydovych hits
- **Russian morphological shadow** (red pill) for `check_russian_shadow=true`
- **Course cross-links** ("Used in HIST M23, OES M44") — none of slovnyk.me's competitors have curriculum back-links

Visual proof: `docs/poc/poc-word-atlas-design.html` shows three contrasting words (`князь` rich data clean; `прапор` sovietization warning visible; `файний` heritage-defense badge for galicianism). All visual primitives reused from `poc-lesson-design.html` — same CSS tokens, same `.myth-box`/`.rule-box`/`.source-box`/`.ety-stage` patterns. Distinguishing teal-yellow hero gradient marks the atlas as the third top-level section.

Design doc covers data model, page contract (15 sections in flow, omit-if-empty), V7 pipeline integration (writer deeplinks to atlas; reviewer audits against atlas as ground truth), deterministic quality gates (all 7), v0→v5 phasing, scope exclusions, and 5 open questions for user (naming, URL scheme, pre-build vs on-demand rendering, cross-link integrity gate, editorial overrides).

## Writer-prompt rebuild dispatch (in flight)

Brief at `docs/dispatch-briefs/2026-05-23-writer-prompt-rebuild-codex.md`. Modifies ONE file: `scripts/build/phases/linear-write.md` (currently 707 lines; target +120-180 lines after rebuild). Five targeted changes:

1. **NEW §"Corpus Access (level-gated)"** — encodes the matrix above as a writer-readable table + sub-sections §1.1-§1.5 covering literary filter intent, stacked vocab check, content modes at B2+, posture shifts at C1+, strict-2-source for seminar history
2. **REPLACE §"Activity Types"** — explains INLINE (light, theory-time) vs WORKBOOK (substantive, after-lesson) split with per-level numerical targets and a design principle directive
3. **NEW pre-emit `<activity_split_audit>`** — parallel to existing `<implementation_map_audit>` and `<bad_form_audit>`; verifies `inline_n ∈ [4,6]` and `workbook_n ∈ [6,9]` at A1 (per-level ranges)
4. **STRENGTHEN §"Learner State"** — 5 binding rules of engagement with prior learning (don't re-explain, vocab containment + foreshadowing, frequency/CEFR awareness, build on cumulative grammar)
5. **NEW additional MCP tools section** + REPLACE pre-emit verification checklist — surfaces `search_literary`, `search_idioms`, `search_definitions` (with sovietization caveat), `search_grinchenko_1907`, `search_esum`, `search_synonyms`, `translate_en_uk`, `query_pravopys`, `query_cefr_level`

9 deterministic acceptance criteria (grep counts + wc -l range + placeholder integrity). Codex must quote raw outputs in PR body.

Not in scope: assembler, pipeline, lesson-contract.md, reviewer prompt (separate dispatch), the curated literary tag layer (F1), the ingestions (F2-F5), the deterministic post-build gate for activity-split.

## What's still in the queue (user-stated order: m20 → m1-m7 → rest of A1)

1. **a1/my-morning (m20)** — blocked on writer-prompt rebuild PR landing. Then refire build using new prompt + already-merged promote/learner_state fixes. Hand-verify the resulting MDX shows 4-6 inline + 6-9 workbook activities and Tab 4 cites G1 canonical resources. Promote if validation passes.
2. **a1/m1-m7** — sequential builds: sounds-letters-and-hello, reading-ukrainian, special-signs, stress-and-melody, plus the next 3 in curriculum.yaml order. Each ~25-30 min on the V7 pipeline.
3. **rest of A1 (m8-m54)** — same loop.

Each build will now produce: (a) correct cumulative_vocab from planned-vocab fallback; (b) correct MDX promote path; (c) once writer rebuild lands, correct INLINE/WORKBOOK split + full corpus surface.

## Follow-ups captured for future sessions

| # | Item | Blocks |
|---|---|---|
| F1 | Build curated-literary filter layer (`tag:a1-curated`, `tag:a2-curated`) on `search_literary` — children's lit, folk songs, fairy-tale openings, iconic phrases | A1+A2 builds (advisory until built; writer prompt references it as future scope) |
| F2 | Ingest peer-reviewed UA academic scholarship (Hrushevsky, Plokhy, Yakovenko, etc.) | C1+ builds + all seminar builds |
| F3 | Ingest Ruthenian Baroque corpus (Прокопович, Туптало sermons + religious treatises) | All seminar builds |
| F4 | Ingest OES manuscripts (Реймське Євангеліє, Остромирове, Києво-Печерський патерик manuscripts) | All seminar builds |
| F5 | Ingest dedicated decolonization corpus (Plokhy *Lost Kingdom*, Snyder *Reconstruction of Nations*, Magocsi, Subtelny, Hrycak, Kappeler) | All seminar builds |
| F6 | Reviewer-prompt rebuild dispatch — mirror the per-level matrix on the audit side; cross-reference atlas pages as ground truth for sovietization/heritage badges | Quality bar for any rebuilt module |
| F7 | Plan-allocation review — verify A1 plans m1-m19 collectively teach enough planned vocab to land m20 in a later band than `a1-m07-14`; may indicate plans are under-allocating vocab targets | Quality refinement; not next-blocker |
| F8 | Word Atlas v1 implementation — render m20 + m1 + m08 vocabulary lemmas via Astro dynamic route (~80 lemmas) | First user-visible payoff from PR #2213 design |
| F9 | Deterministic post-build gate for `activity_split_valid` — parallel to existing wiki_coverage_gate; checks inline ∈ [4,6] + workbook ∈ [6,9] | Defense-in-depth for future writers |

## Active state at handoff

- **Active dispatches**: 1 (`writer-prompt-rebuild-2026-05-23` Codex, branch `codex/writer-prompt-rebuild-2026-05-23`, fired 2026-05-22T14:26:01Z UTC, ETA 20-40 min)
- **Active builds**: 0
- **Open PRs**: 1 (`#2213` session docs)
- **Origin/main**: `edcb872323` (PR #2212 merge head)
- **Build worktrees preserved per #M-10**: all a1-my-morning timestamps still intact
- **Starlight dev server**: up at http://localhost:4321 (still serving the reverted m20 page)
- **Monitor API**: up at localhost:8765
- **Sources MCP**: up at localhost:8766
- **Inbox**: empty
- **Wakeup scheduled**: 2026-05-22T16:51Z to poll the writer-prompt dispatch — but handoff supersedes this (next session re-orients via Monitor API)

## Lessons from this session (autopsy notes)

### What was wrong in how I read the prior handoff
- I took the prior handoff's framing ("Tab 3 fallback eaten by transforms") at face value and started tracing transforms instead of tracing the actual file path from build write → promote read. Reading the build's git log + `git show --stat` on the promote commit would have surfaced the path mismatch in ~5 minutes; instead I burned ~30 minutes chasing the wrong layer.
- The diagnose-the-right-layer principle: when a build artifact looks wrong on main, check ALL the layers (writer → assembler → promote → deploy). The bug is often in a layer that the prior session ASSUMED worked.

### What was wrong in how I conducted the interview
- Mid-session the user explicitly told me "you can bring up several options, that won't change how i want it. i am just getting annoyed from these options. how many time i told you this and you just dont care." This violates #M-1 (direct order obedience: stop alternative paths, do the thing) and #0A (frustrated user: brief actions only — no menus, no "two options").
- Pattern that triggered the frustration: presenting AskUserQuestion blocks AFTER the user had already given a clear direction. Interview mode is for OPEN questions, not for confirming directions the user has already stated.
- Specific case: the user described the inline-vs-workbook split clearly ("we have some activities during the theory parts since every book is like that, much more activities in the workbook part"). I then proposed 4 P2 rendering options when the user had already implicitly answered. Cost: a frustrated message + a wasted decision card.

### What's working
- The interview matrix itself is a strong artifact — A1-C2 + seminars captured in one binding table that drives the writer-prompt rebuild brief verbatim.
- Codex dispatch for the learner_state fix landed clean (5 new tests, all 9 acceptance criteria green, all blocking CI passed). Inline PR review + merge took ~5 min.
- The promote_module fix was a clean root-cause find: traced through the m20 worktree's git log to the promote commit, identified the path mismatch, fixed with one function rename + one new function + 3-line policy change + a new regression test that pollutes the stale starlight path and asserts the fresh curriculum path is what lands.

## How next-session orchestrator should open

1. Read this handoff (you're doing it now)
2. Verify state matches: `git log --oneline -5 origin/main` should show `edcb872323` (promote_module fix) on top
3. Poll `/api/delegate/active` for `writer-prompt-rebuild-2026-05-23` outcome. If `status=done`, find the PR via `gh pr list --state open --search "writer-prompt-rebuild"`. If still running, ScheduleWakeup.
4. When writer-prompt PR is up: review against the brief's 9 acceptance criteria, merge if green
5. Refire `a1/my-morning` build with the new prompt: `.venv/bin/python scripts/build/v7_build.py a1 my-morning --worktree` and Monitor JSONL events
6. Hand-verify the rebuilt MDX against `docs/poc/poc-lesson-design.html`:
   - Tab 1: dialogue + rule boxes + 4-6 inline activities anchored to teaching prose
   - Tab 2: vocab table + flashcards
   - Tab 3: 6-9 workbook activities (NOT "no workbook activities" fallback)
   - Tab 4: cites Захарійчук G1 p.24 + p.52 + any external materials the writer pulled
7. If validation passes: `scripts/sync/promote_module.py --build-branch <branch>` and verify the served MDX matches the build's output
8. Then fire `a1/sounds-letters-and-hello` (m1) build, same loop
9. Concurrently: review + merge PR #2213 (session docs — low-risk, mergeable as-is)

**Do not promote any module until the rebuild MDX has been visually verified against the PoC.** The m20 revert + double-misdiagnosis pattern shows that gates + LLM-9.5/10 + green CI are necessary but not sufficient. Eyes-on verification before promote stays mandatory.
