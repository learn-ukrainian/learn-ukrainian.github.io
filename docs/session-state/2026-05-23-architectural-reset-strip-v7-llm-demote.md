---
date: 2026-05-23
session: "Architectural reset agreed: strip V7 writer prompt + demote LLM subjective dims to warning + decolonization stays terminal + A1 focus with claude-tools as anchor + writer specialization by track + manual review as final gate. Encodes empirical learnings from V6 + V7 across 4 weeks of build attempts."
status: green-architecture-decided-PRs-pending
main_sha: a9f1f86f23
main_green: clean (review/review advisory persists per F7 — needs GEMINI_API_KEY in repo secrets)
working_tree_dirty: pre-existing carry-overs (no new on top)
prs_merged_this_session: []  # this is the planning handoff; tactical PRs landed in predecessor 2026-05-23-overnight-two-pipeline-fixes-but-no-anchor.md (#2237, #2238)
prs_wip_unmerged: []
active_dispatches: []
active_builds: []
builds_completed_this_session: []  # 6 build attempts captured in 2026-05-23-overnight-two-pipeline-fixes-but-no-anchor.md
headline_finding: "After 6 V7 build attempts produced zero shipped anchor and identified that V7 is structurally over-engineered (268KB writer prompt, 23 deterministic gates, brittle ADR-008 auto-correction with 3/7 unparseable rate, multiple correction LLM round trips fighting each other), user + I agreed an architectural reset: strip V7 in-place (no parallel V8 fork), demote 4 LLM subjective dims (pedagogical / naturalness / engagement / tone) from terminal to warning while decolonization stays terminal, A1 focus with claude-tools as anchor writer (gemini → wiki + content, codex → seminars post-#2239 fix), writer prompt budget ≤40KB rendered, --resume aggressive use, manual human review as final promote gate (user + orchestrator). Concrete PR sequence A→B→C→D (~580 LOC + 1 validation build) takes ship-velocity to 3-5 A1 modules per week if the strip+demote holds."
next_session_first_item: "1) **PR-A (~30 LOC)**: demote pedagogical/naturalness/engagement/tone from terminal to warning in `scripts/build/linear_pipeline.py` `LLM_QG_TERMINAL_DIMS`. Decolonization stays terminal. Build continues regardless of subjective verdicts; reviewer output preserved for human review. 3 tests. 2) **PR-B (~50 LOC)**: widen word_count ±5% → ±8% and engagement_floor:callout_min 2 → 1 in `scripts/audit/config.py` + `scripts/build/linear_pipeline.py`. Tests. 3) **PR-C (~500 LOC)**: writer-prompt strip pass 1 on `scripts/build/phases/linear-write.md`. Target 268KB → 40KB rendered. Drop 2 of 3 pre-emit audit lines (keep implementation_map_audit only), state each rule once with strong language not 4× redundant phrasings, move activity-type component-props + corpus catalog to fetchable appendix files, drop placeholders that always substitute to the same value. Add `scripts/audit/check_writer_prompt_size.py` enforcing 40KB ceiling. 4) **Validation build**: claude-tools on a1/my-morning with PR-A+B+C in place. Expected: complete MDX artifact, LLM warnings logged but build continues, visual verify-before-promote, promote. 5) If validation passes: same shape applies to a1/m21 + rest of A1 cumulatively. 6) If validation fails on a new class: PR-D writer-prompt strip pass 2."
---

# 2026-05-23 — V7 architectural reset agreed

## Decision summary

After tonight's 6-build evidence + back-and-forth on V7's structural fitness, we agreed:

| # | Decision | Rationale |
|---|---|---|
| 1 | **Strip V7 in place, no parallel V8 fork** | A parallel V8 means two pipelines to maintain. Conceptual change doesn't need schema changes — module.md / activities.yaml / vocabulary.yaml / resources.yaml stay. If the strip+demote works, we can rename to V8 at the end as a clarity gesture. |
| 2 | **Demote 4 LLM dims from terminal → warning** | pedagogical, naturalness, engagement, tone are subjective. The reviewer output stays and informs human review, but doesn't kill the build. |
| 3 | **Decolonization STAYS terminal** | Political safety. "Russian framing leaked in" is not subjective — it's a hard rule. |
| 4 | **A1 focus; claude-tools as A1 anchor writer** | Lowest immersion, simplest grammar scope, best plan coverage. Claude is best instruction-follower at xhigh (m20 pedagogical 7.5 post-#2238). Ship A1 → use shape for A2 and beyond. |
| 5 | **Writer specialization by track** | claude → A1 core. gemini → wiki + content writer (existing role). codex-tools → seminars (post-#2239 fix; only writer that invokes query_ulif + query_pravopys + search_heritage). |
| 6 | **Writer prompt size budget ≤40KB rendered** | Current 268KB is at the edge of any LLM's reliable following. Strip via redundancy elimination + appendix-able heavy reference material + terse examples replacing prose explanation. Enforced via `scripts/audit/check_writer_prompt_size.py`. |
| 7 | **Manual human review as final promote gate** | Pipeline does corpus grounding + structural checks + assembly. User + orchestrator (me) do final pedagogical + tone review before `scripts/sync/promote_module.py` runs. Shifts load off the algorithm onto humans where humans have leverage. |
| 8 | **--resume aggressive default** | When a build dies on a fixable phase, next invocation resumes from that phase unless `--no-resume`. Saves the 5-20 min writer phase replay we burned 6× tonight. |

## Why this shape and not the alternatives

**Not V6:** V6 had its own complexity (9-dim weighted LLM review with self-correction) and shipped modules but lost the corpus-grounding rigor V7 added (wiki obligations manifest, implementation_map seeding, MCP-tool verification). The strip+demote keeps V7's quality scaffolding (deterministic gates for things we CAN check in code) while dropping V7's hubris (LLM gating subjective dims it can't reliably enforce).

**Not V6.5:** User explicitly rejected hybrid framing. The shape is V7-restructured, not V6-with-V7-toppings.

**Not full re-architecture (V8 parallel build):** Two pipelines = double maintenance cost during the months it'd take to stabilize V8. We have all 1700+ plans already on V7 contracts. Strip-in-place is faster and lower-risk.

## What V7 got right that we keep

Per evidence from 2026-05-22 + tonight:
- Wiki obligations manifest (18 substance checks per module) — load-bearing for "no hallucinated treatment"
- Implementation map seeding — load-bearing for writer accountability
- MCP-tool verification (38-48 sources calls per build observed) — load-bearing for corpus grounding
- VESUM gate (russianisms_strict, calques_clean, surzhyk_clean) — load-bearing for Ukrainian linguistic safety
- Activity-split bands (#2238 fixed the correction-side bug, the band concept stays)
- python_qg deterministic gates for things code CAN check (word_count, activity_schema, formatting_standards, citations_resolve, textbook_grounding, etc.)

## What V7 got wrong that we strip / demote

- **Writer prompt sediment**: 4+ redundant statements of the same rule across the 268KB body. Each rule landed because of a past empirical failure but nothing was ever removed when adding.
- **Three pre-emit audit lines** (implementation_map_audit + bad_form_audit + activity_split_audit): the writer is asked to self-audit 3 times before emitting. Deterministic gates catch all three post-emission anyway. Keep ONE (the one with HARD-REJECT teeth) and drop two.
- **LLM dims as terminal**: subjective judgment dims (tone, pedagogical, etc.) terminating builds means stochastic non-convergence. Warnings + human review = predictable.
- **ADR-008 auto-correction** has high `writer_correction_unparseable` rate (3 of 7 builds tonight). Don't auto-correct on subjective dims at all; let them fall to human.
- **Auto-promote `_apply_activity_id_inserts`** (FIXED tonight in PR #2238): pipeline mutated writer's correct split to anti-pattern.

## Concrete PR sequence — A → D

Next-session orchestrator opens with this plan.

### PR-A (~30 LOC) — LLM dim demote

**File:** `scripts/build/linear_pipeline.py`

```python
# Currently: ALL llm_qg dim verdicts in {REJECT} kill the build
# Change: only specific dims terminate; others warn

LLM_QG_TERMINAL_DIMS = frozenset({"decolonization"})
LLM_QG_WARNING_DIMS = frozenset({"pedagogical", "naturalness", "engagement", "tone"})
```

Build continues regardless of warning-dim verdict. The reviewer's critique + evidence quotes still get persisted to `llm_qg.json` for human review. Failure-class telemetry emits `llm_qg_warning` events for observability, not `module_failed`.

**Tests:**
- `test_llm_qg_demoted_dims_do_not_terminate` — module continues past llm_qg with REJECT on tone
- `test_llm_qg_decolonization_still_terminal` — decolonization REJECT still kills build
- `test_llm_qg_warning_dims_logged_to_telemetry` — warning telemetry event emitted with critique

### PR-B (~50 LOC) — Floor gate widening

**Files:** `scripts/audit/config.py` + `scripts/build/linear_pipeline.py`

- `word_count`: ±5% → ±8% (1104 ≤ count ≤ 1296 for A1's 1200 target). Empirically all of gemini 1031, deepseek 1197, deepseek 1212 (earlier in week) cluster within ±15% of target. ±8% catches the 1197 case while still rejecting the 1031.
- `engagement_floor:callout_min`: 2 → 1. Writers consistently emit 1 callout. The "minimum 2" was aspirational not empirical.

**Tests:** band-edge unit tests + 1 regression test.

### PR-C (~500 LOC) — Writer prompt strip pass 1

**File:** `scripts/build/phases/linear-write.md`

Target: 268KB → 40KB rendered.

Concrete moves:
1. **Drop 2 of 3 pre-emit self-audit lines**. Keep `<implementation_map_audit>` (the one with HARD-REJECT teeth). Drop `<bad_form_audit>` + `<activity_split_audit>` — deterministic gates catch both.
2. **State each rule ONCE.** Search/grep for repeated phrasings ("address the learner directly" appears 4+ times, "do not fabricate" appears 3+ times) and consolidate.
3. **Move heavy reference material to appendix.** Activity-type component-props schemas + full corpus catalog → `docs/best-practices/activity-component-props.md` + `docs/best-practices/v7-design-and-corpus.md` references. Writer fetches via @-path on demand.
4. **Drop placeholders that always substitute to fixed values.** {INLINE_ALLOWED_TYPES} expands to the same list every A1 module — bake it in or move it to the appendix.
5. **Replace prose explanations with terse examples.** One good / one bad per rule. Cut transition paragraphs.

**New file:** `scripts/audit/check_writer_prompt_size.py` — pytest fixture that fails CI if a rendered prompt exceeds 40KB for any level/module fixture. Forces discipline.

**Validation:** lint-only on this PR. Real validation comes from the next-step build.

### Validation build

After PR-A + B + C land:

```bash
.venv/bin/python scripts/build/v7_build.py a1 my-morning --writer claude-tools --effort xhigh --worktree
```

Expected behavior:
1. Writer runs against stripped prompt (~40KB)
2. python_qg: passes (widened bands) or auto-corrects on the few WRITER_CORRECTION_GATES
3. wiki_coverage: passes (PR #2237 + #2238 already in)
4. llm_qg: runs, emits per-dim verdicts. Decolonization PASS or terminal. Other 4 dims = warnings logged.
5. mdx_assemble: produces complete artifact
6. Build "passes" (no `module_failed` event) — reviewer output stays in `llm_qg.json` for human review

Then:
1. User + orchestrator read `llm_qg.json` warning critiques + visually verify rendered MDX at `http://localhost:4321/a1/my-morning/`
2. Hand-edit specific issues (tone slips, missing callouts, etc.)
3. Run verify-before-promote 10-check (`docs/best-practices/v7-design-and-corpus.md` §4)
4. `scripts/sync/promote_module.py a1 my-morning`

If validation fails on a new class of issue: PR-D writer-prompt strip pass 2 OR diagnostic. Don't keep blind-firing.

### PR-D (contingency)

Reserved for writer-prompt strip pass 2 (additional cuts) OR a separate gate adjustment surfaced by the validation build. Specifics defined after validation runs.

## Open risks + tradeoffs (HONEST)

1. **Human review bottleneck.** Demote means YOU (+me) become the gatekeeper for subjective quality. If you don't have ~30-60 min per module for review, modules ship that LLM would have caught. Mitigation: budget review time explicitly per module; treat review as the work, not as overhead.

2. **Writer prompt strip risk.** Cutting rules risks losing safety floors. Mitigation: each cut should be justified by "this rule fired N times in the last 6 months of builds; if N=0 the rule is dead weight; if N>3 the rule stays." Track via empirical evidence not by gut.

3. **40KB might be the wrong number.** Could be 30KB or 60KB. Mitigation: pick 40KB as the working target; revisit after PR-C empirical results.

4. **Specialization assumes codex regression fixed.** Issue #2239 blocks codex-tools entirely. Until fixed, codex can't take seminars. Mitigation: Issue #2239 is P1 for next-or-next-next session.

5. **A1 focus deprioritizes B1+.** While A1 ships, B1/B2/C1/C2/seminar tracks stall. Mitigation: explicit decision — A1 first, others wait. Don't fragment attention.

6. **The strip might not be enough.** Writer reliability is also a function of model capability + prompt clarity + corpus complexity, not just prompt size. Mitigation: validation build is the falsifier. If claude m20 still fails post-PR-C, the answer isn't "strip more" — it's "claude isn't reliable enough at A1 even with clean prompt; we need different shape entirely."

## What's NOT changing

- All four writer artifacts (module.md / activities.yaml / vocabulary.yaml / resources.yaml) — schemas unchanged
- Wiki obligations manifest format — unchanged
- Implementation map schema — unchanged
- python_qg deterministic gates — unchanged in shape, 2 band values widened
- MCP sources tools — unchanged
- VESUM verification — unchanged
- Module promote machinery — unchanged
- Module manifest (`curriculum/l2-uk-en/curriculum.yaml`) — unchanged
- Plan format — unchanged

## Open follow-ups (cumulative — only delta from 2026-05-22 + this overnight handoff)

| # | Item | Priority | Notes |
|---|---|---|---|
| **A1-2026-05-23** | **PR-A: demote 4 LLM dims to warning** | **P0** | Next-session first action |
| **B1-2026-05-23** | **PR-B: widen word_count + engagement_floor bands** | **P0** | After A |
| **C1-2026-05-23** | **PR-C: writer prompt strip pass 1 (target 40KB)** | **P0** | After B |
| **V1-2026-05-23** | **Validation build: claude m20 with stripped prompt + demoted LLM** | **P0** | After C |
| **P1-2026-05-23** | **Promote a1/my-morning if validation passes** | **P0** | After V |

Carry-over from 2026-05-23 overnight handoff:
| # | Item | Priority | Notes |
|---|---|---|---|
| F2-2026-05-23 | Codex adapter post-#2233 regression (Issue #2239) | **P1** | Unblocks codex-tools entirely |
| F3-2026-05-23 | Validate #2238 on a non-my-morning module | P1 | Confirm fix general |
| F4-2026-05-23 | Writer-bench v0 (now unblocked structurally) | P2 | Reset priority — wait until A1 anchor ships + new shape stabilizes |

All F5-F17 carry-overs from 2026-05-22 handoff Section 8 unchanged but deprioritized P3 until A1 anchor lands.

## Session-handoff discipline (added 2026-05-23)

Future session-state handoffs should explicitly capture **architectural decisions** as ADRs at `docs/decisions/YYYY-MM-DD-{slug}.md` in addition to the session-state file. The session-state file is narrative-shaped (what happened + why + next); the ADR is decision-shaped (option taken, options rejected, reversal triggers). They serve different consumers.

For this session: ADR candidate = `docs/decisions/2026-05-23-v7-architectural-reset-strip-and-demote.md`. Drafting deferred to PR-A (the first PR that encodes the decision in code).

## Honest assessment for the user

We didn't ship a module tonight. We did identify and fix two structural pipeline bugs (#2237 + #2238) that were blocking every V7 build since 2026-05-12. The m20 root cause is closed. The 6 builds gave us the empirical evidence needed to make the architectural call you proposed — and you proposed the RIGHT call. The strip + demote + human-review shape is what V7 should have been from the start; the auto-everything ambition was overreach.

Concrete velocity estimate going forward (under the new shape):
- ~5 days to PR-A, PR-B, PR-C, validation build, first promote
- ~3-5 A1 modules per week after that if the shape holds
- ~6-8 weeks to A1 complete (55 modules)
- A2-C2 + seminars follow once A1 cadence is steady-state

That's slower than the original V7 ambition. It's faster than the current zero-ship pace.

If the validation build (post-PR-C) doesn't pass, we have a harder conversation: the model + prompt combo isn't reliable enough even with the strip. At that point options narrow to (a) different writer, (b) human-writes-skeleton + LLM-fills-details, (c) pause project. We cross that bridge if we reach it.

## Section: How next-session orchestrator should open

1. Read this handoff end-to-end.
2. Read the predecessor handoff (`docs/session-state/2026-05-23-overnight-two-pipeline-fixes-but-no-anchor.md`) for tactical evidence.
3. Verify state: `git log --oneline -3 origin/main` shows `a9f1f86f23` (handoff #2240) on top.
4. Poll: `curl -s http://localhost:8765/api/delegate/active` — should be empty.
5. **Start PR-A immediately.** Don't re-litigate decisions; they're settled per this handoff.
6. Open PR-A → CI green → merge → PR-B → CI green → merge → PR-C → CI green → merge → validation build.
7. Report progress + checkpoints to user at PR-merge boundaries.
8. After validation build runs, decide: promote OR PR-D OR escalate (per "What if validation fails" section).
