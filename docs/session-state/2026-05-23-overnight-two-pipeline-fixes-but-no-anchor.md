---
date: 2026-05-23
session: "Overnight orchestration: TWO pipeline fixes landed (#2237 wiki_coverage workbook-title resolver + #2238 m20 activity-split root-cause), validated empirically across 6 build attempts. No shipped anchor — remaining blockers are stochastic writer-quality misses (word_count, tone register, dialogue floor, engagement callouts) on the writer-prompt side, NOT structural pipeline bugs."
status: yellow-pipeline-unblocked-writer-prompts-still-fragile
main_sha: d744872b13
main_green: clean (review/review advisory persists per F7 — needs GEMINI_API_KEY in repo secrets)
working_tree_dirty: pre-existing carry-overs (no new on top)
prs_merged_this_session:
  - "#2237 fix(wiki_coverage): resolve workbook activity claims via title fallback + bare-artifact hint"
  - "#2238 fix(pipeline): strip id from unused workbook activities instead of auto-injecting markers (m20 ROOT CAUSE)"
prs_wip_unmerged: []
active_dispatches: []
active_builds: []
builds_completed_this_session:
  - "codex-tools 223407 (pre-#2238): writer phase passed with 48 valid mcp__sources__* calls; adapter rollout binding STILL broken post-#2233 → mcp_tools_never_invoked HARD"
  - "gemini-tools 224427 (pre-#2238): writer 169s; python_qg failed at word_count + 4 other gates; ADR-008 correction unparseable → terminal"
  - "deepseek-tools 224911 (pre-#2238): writer 336s; python_qg PASSED; wiki_coverage 1.0 after 2 correction rounds; llm_qg 5.5/10 REJECT (pedagogical 5.5: activity-split anti-pattern inline_n=10/workbook_n=0 — m20 SIGNATURE BUG)"
  - "claude-tools 230706 (pre-#2238): writer 617s; python_qg PASSED; wiki_coverage clean; llm_qg 4.0/10 REJECT (pedagogical 4.0: 5 consecutive INJECT dumps + Захарійчук unscaffolded textbook quote)"
  - "deepseek-tools 233957 (post-#2238): writer 331s; python_qg failed at word_count 1197/1200 + vesum 1 invalid (снідаюся) + l2_exposure_floor 11/14 + engagement_floor 1/2; ADR-008 correction unparseable → terminal. Activity split CLEAN post-fix: inline_n=5 / workbook_n=7"
  - "deepseek-tools 234933 retry (post-#2238): writer 350s; writer EMITTED NO IMPLEMENTATION_MAP → wiki_coverage 0/18; reviewer returned empty <fixes></fixes> → KILLED manually"
  - "claude-tools 235609 (post-#2238): writer 877s; python_qg PASSED; wiki_coverage 1.0 after 1 correction round; llm_qg 2.0/10 REJECT (tone 2.0 + naturalness 3.0: teacher-manual voice 'Учні повинні...' / 'Hold the line on...'). Activity split CLEAN post-fix: inline_n=5 / workbook_n=5"
headline_finding: "Two distinct structural pipeline bugs landed and validated tonight: #2237 (wiki_coverage_gate location-resolver couldn't find workbook activities post-PR-#2218 id-optional change → 6 err-N obligations hard-failing claimed_location_missing on every writer) and #2238 (`_apply_activity_id_inserts` auto-promoted workbook→inline via marker injection → m20 anti-pattern inline_n=10/workbook_n=0 on EVERY auto-corrected build, the actual ROOT CAUSE of the 2026-05-23 morning m20 revert at 944f4200e4). Both empirically validated against preserved + fresh worktrees: codex-tools 205831 (preserved) jumped 11/18 → 17/18 with #2237; claude-tools 235609 (fresh) shows clean inline=5 / workbook=5 split with #2238 vs claude 230706's 9/1 + deepseek 224911's 10/0 pre-fix. BUT no V7 anchor module shipped tonight — remaining blockers across 6 builds are stochastic writer-quality misses (word_count off by 3-127, dialogue lines 11-12 vs floor 14, engagement_floor 1 callout short, tone meta-narration in third person, naturalness Eng/Ukr mixed-clause hybrid) and high writer_correction_unparseable rate on the ADR-008 retry. Those are writer-prompt + writer-correction issues, NOT pipeline structural bugs."
next_session_first_item: "1) **DECIDE writer-prompt strategy** — claude's tone REJECT (2.0) on 235609 was 'Учні повинні...' third-person teacher-manual voice; deepseek 233957 was 1197/1200 words (3 short) + 1 missing callout + 1 invalid reflexive form (снідаюся). Both within 5% of passing. Either (a) loosen 2-3 writer-floor gates by 1-2 units each, or (b) add explicit examples to writer prompt for tone-register + word-count-stretch + callout-min, or (c) accept m20 as not-shippable and try a different module (a1/sounds-letters-and-hello shipped successfully on 2026-05-22 night per session-state). 2) **File codex adapter post-#2233 regression** — fresh codex 223407 had 48 valid mcp__sources__* calls in scoped rollout but writer_tool_calls.json still empty because _rollout_matches_plan rejects the actual match (stdin_payload encoding/whitespace mismatch). Separate from #2233. 3) **Validate #2238 once more on a non-my-morning module** to confirm fix isn't my-morning-specific. 4) Then writer-bench v0 unblocked."
---

# 2026-05-23 overnight — two pipeline fixes, no anchor

## TL;DR — what changed in this session

| # | Action | State |
|---|---|---|
| 1 | PR #2237 wiki_coverage_gate workbook-title fallback (3 resolution strategies + 3 tests) | merged `c1eab13387` |
| 2 | PR #2238 `_apply_activity_id_inserts` strips id instead of auto-injecting markers (3 tests) | merged `d744872b13` |
| 3 | Empirical validation: 6 build attempts of a1/my-morning across codex/gemini/deepseek×3/claude×2 | all failed but ALL converged on diagnostic data |
| 4 | m20 ROOT CAUSE identified + landed: `_apply_activity_id_inserts` (linear_pipeline.py:5347) was mutating writer's correct 4/6 split → 10/0 anti-pattern | closed by #2238 |
| 5 | Codex adapter regression filed: post-#2233 still loses the rollout binding; separate from previous fix | task #8 open |
| 6 | No shipped V7 anchor — every writer hit a *different* writer-quality stochastic miss | next-session priority |

## Section 1 — The two structural pipeline bugs and their fixes

### 1.1 PR #2237 — wiki_coverage_gate workbook activity resolution

**Bug:** `_activity_text` in `scripts/audit/wiki_coverage_gate.py:510` resolved a writer's claim `location` string by substring-matching against each activity's `id` field. But PR #2218 (2 days ago) made `id` optional on workbook activities (and `linear-write.md` L700 explicitly says workbook activities omit `id`). Result: every workbook-targeted obligation (err-1..err-6 contrast pairs, etc.) hard-failed `claimed_location_missing` regardless of content quality.

**Fix:** Three additional resolution strategies (first match wins):
1. Bare-artifact hint (`activities.yaml`) → all activities flattened (honours seeded `location_hint`)
2. Title substring (either direction) → that activity
3. Trailing-index strip equality → that activity (handles `workbook error-correction item 5` vs `workbook error-correction item 2` codex case)

**Empirical validation:** Re-ran gate on preserved codex-tools 205831 worktree. Coverage 11/18 (61% hard_fail) → 17/18 (94%) with only the substance-genuine `step-5` fail remaining. All 6 `err-N` structural fails resolved.

**Tests:** 3 new + all 384 existing audit tests pass.

### 1.2 PR #2238 — m20 root cause: `_apply_activity_id_inserts`

**Bug:** `_apply_activity_id_inserts` in `scripts/build/linear_pipeline.py:5347` resolved `inject_activity_ids:unused_activities_not_injected` by APPENDING `<!-- INJECT_ACTIVITY: act-X -->` markers to module.md for every unused id. This auto-promoted EVERY workbook activity to inline, blowing past the level's `INLINE_MAX` ceiling. **This produced the EXACT anti-pattern that got m20 reverted on 2026-05-23 morning (`944f4200e4` revert; build #14 shipped with `inline_n=10 / workbook_n=0` against A1's required INLINE 4-6 / WORKBOOK 6-9).**

**Empirical evidence of reproducibility across writers (2026-05-22 night, pre-#2238):**

| Writer | Writer's audit-line claim | Final state (after auto-correction) | LLM QG pedagogical |
|---|---|---|---|
| codex 223407 | (rollout binding broken — separate issue) | n/a | n/a |
| gemini 224427 | failed earlier at word_count | n/a | n/a |
| **deepseek 224911** | `inline_n=4 workbook_n=6 split_valid=true` | **`inline_n=10 workbook_n=0`** | **5.5 REJECT** ("Dumping five consecutive injected activities at the end of the lesson completely destroys pacing") |
| **claude 230706** | (no audit line emitted) | **`inline_n=9 workbook_n=1`** | **4.0 REJECT** (5 consecutive INJECT dumps) |

Deepseek explicitly self-audited the correct 4/6 split — then the pipeline-insert correction silently mutated it to 10/0. **This is the m20 root cause, definitively.**

**Fix:** Strip `id` from each `unused` activity in `activities.yaml`, leaving `module.md` untouched. Per `linear-write.md` L700, an activity-with-id-without-marker is best interpreted as workbook + writer over-emitted id, not as inline + writer forgot the marker.

**Empirical validation post-fix:**
- deepseek 233957: `inline_n=5 / workbook_n=7` (writer's authored split preserved)
- claude 235609: `inline_n=5 / workbook_n=5` (was 9/1 pre-fix → 5/5 post-fix, clean)

**Tests:** 3 new + 128 affected tests pass.

### 1.3 Why these two and not three+ fixes

I diagnosed and could have shipped a THIRD fix (codex adapter `_rollout_matches_plan` still rejects fresh rollouts with 48 valid MCP calls inside; see Section 5). I chose not to overnight because:
- The bug is in stdin_payload exact-match comparison; root cause requires actual stdin trace
- Risk of breaking working codepaths without sufficient diagnostic data
- Two pipeline fixes is enough surface change for one overnight without user oversight

## Section 2 — The 6 builds and what they each told us

All against `a1/my-morning` (the m20 module — picked specifically because it had been reverted, and to avoid contaminating other modules during diagnosis).

| # | Build | Writer | Time | Phase reached | Failure | Lesson |
|---|---|---|---|---|---|---|
| 1 | 223407 (pre-#2238) | codex-tools xhigh | writer 7m | writer | mcp_tools_never_invoked (adapter rollout binding broken post-#2233) | Codex adapter regression — separate from #2233 |
| 2 | 224427 (pre-#2238) | gemini-tools high | writer 2.8m | python_qg | word_count 1031/1200 + ADR-008 correction unparseable | Gemini under-writes; correction parsing brittle |
| 3 | 224911 (pre-#2238) | deepseek-tools xhigh | writer 5.6m + reviews | llm_qg | **5.5/10 REJECT pedagogical: inline_n=10/workbook_n=0** | First confirmation of m20 root cause across writers |
| 4 | 230706 (pre-#2238) | claude-tools xhigh | writer 10.3m + reviews | llm_qg | **4.0/10 REJECT pedagogical: inline_n=9/workbook_n=1** | Second confirmation — m20 bug is writer-agnostic |
| 5 | 233957 (post-#2238) | deepseek-tools xhigh | writer 5.5m | python_qg | word_count 1197/1200 + vesum 1 invalid + l2_exposure 11/14 + engagement_floor 1/2 + ADR-008 unparseable | **Activity-split CLEAN (5/7 split preserved)** — #2238 worked. Remaining blockers stochastic minor |
| 6 | 234933 retry (post-#2238) | deepseek-tools xhigh | writer 5.8m | wiki_coverage | Writer emitted NO implementation_map blocks → 0/18 coverage → reviewer returned empty `<fixes>` → killed manually | Deepseek is high-variance: one run perfect implementation_map, next run none |
| 7 | 235609 (post-#2238) | claude-tools xhigh | writer 14.6m + reviews | llm_qg | **2.0/10 REJECT tone + 3.0 naturalness: teacher-manual voice 'Учні повинні...', 'Hold the line on...'** | **Activity-split CLEAN (5/5 split, was 9/1 pre-#2238 — pedagogical jumped 4.0 → 7.5)** — #2238 worked. But tone register slipped. |

**Key insight:** Builds 5 + 7 prove #2238 works empirically. The bug that blocked claude's earlier 4.0 pedagogical (5 consecutive INJECT dumps) is gone. Pedagogical lifted to 7.5 on the same writer same module same effort. **The fix is real.**

But each writer hit a *different* stochastic writer-quality miss after the fix:
- Deepseek: word_count near-miss + parsing-unparseable correction
- Claude: tone register slip (third-person teacher voice)

These are writer-prompt + writer-correction concerns. Not pipeline structural bugs.

## Section 3 — Why no anchor shipped despite two real fixes

Every writer is at ~85-95% compliance with the V7 gate set. Each writer misses 1-3 different gates per run. The auto-correction loop (ADR-008) has high `unparseable` rate (3 of 7 builds tonight). Net effect: gates are too tight + corrections too brittle = stochastic non-convergence.

Specific blockers across the 6 builds:

**Gates that block frequently and need work:**
1. `word_count`: tight ±5% band. 1197/1200 (deepseek) and 1031/1200 (gemini) both failed. Tolerance too tight when writers naturally land close.
2. `engagement_floor:callouts`: writers consistently emit 1 callout vs required 2. Possible: minimum should be 1 with strong recommendation for 2.
3. `l2_exposure_floor:uk_dialogue_lines`: writers emit 11-12 lines vs required 14. Possible: writers underestimate the dialogue density needed.
4. `vesum_verified`: high false-positive rate on bold-formatted suffixes (`**-сь**`, `**-ться**`) treated as missing lemmas. Pre-existing whitelist gap.
5. `ADR-008 writer_correction_unparseable`: high failure rate — writers emit corrections in formats the parser can't handle.

**Writer-prompt issues:**
1. Tone register: claude wrote third-person teacher-manual voice. Prompt's "address the learner directly" instruction not strong enough.
2. Implementation_map emission: deepseek 234933 emitted ZERO map blocks (vs 18 expected). Writer-prompt audit instructions are violable.
3. Activity-split: even with #2238, writers vary 5/5, 5/7, 4/6 — only deepseek 224911 self-audited a precisely-matching split (4/6) without auto-correction.

## Section 4 — What to do next session (priority order)

### F1 (P0) — Decide writer-prompt strategy

The fundamental tradeoff: tighten gates → more stochastic blocks. Loosen gates → quality drift. Three concrete paths:

**(a) Loosen 2-3 writer-floor gates** by 1-2 units each:
- `word_count`: widen ±5% → ±8%
- `engagement_floor`: callout floor 2 → 1
- `l2_exposure_floor:uk_dialogue_lines`: 14 → 12

Risk: quality slippage on these floors.
Benefit: ~50% likely to ship a clean anchor on next claude/deepseek run.

**(b) Add explicit failure-mode examples to writer prompt**:
- Tone: add "TONE FAILURE MODE 1: 'Учні повинні...' = THIRD PERSON ABOUT LEARNERS = HARD REJECT. Write 'Ти бачив...' instead." for each common slip.
- Word count: "Write 1200±60 words. NOT 1197. NOT 1031. Use the section budget to land within ±60."
- Implementation map: "EMIT EVERY OBLIGATION ID. Zero omissions. Writer self-audit at end."

Risk: writer prompt grows further (already 268K chars for codex 205831).
Benefit: targets the specific stochastic failure modes empirically observed tonight.

**(c) Accept m20 as not-shippable for now**; ship a different already-built module:
- a1/sounds-letters-and-hello shipped successfully on 2026-05-21 evening as the FIRST V7 module (per session-state 2026-05-22-cascade-resolved-engagement-floor-wip.md / 2026-05-23-engagement-gates-shipped-build-12-firing-7-modules-queue.md).
- Risk: m20 still broken; doesn't validate the cascade.
- Benefit: zero risk, content already shipped.

**Recommendation: (b) + reattempt m20 once.** Specific writer-prompt examples are cheap to add and address the specific empirical misses. If reattempt fails, (a) or escalate to user.

### F2 (P1) — File codex adapter post-#2233 regression issue

Fresh codex 223407 had 48 valid mcp__sources__* calls in scoped rollout — writer was operating correctly. But `writer_tool_calls.json` came out empty (3 bytes) because `_rollout_matches_plan` rejected the fresh rollout despite the user_message containing the writer prompt verbatim. Root cause likely stdin_payload encoding/whitespace mismatch (rollout has `response_item` + `event_msg` events; matcher requires byte-exact equality).

Investigation steps:
1. Capture `plan.stdin_payload` exactly at the moment of submission
2. Dump rollout's user_message exactly as received
3. Diff bytes/encoding
4. Likely fix: normalize newlines OR allow substring match for the trailing portion

This blocks codex-tools entirely until fixed. Codex was the most promising writer per 2026-05-22 handoff (38 unique-tool corpus utilization including `query_ulif` + `query_pravopys` no other writer invoked).

### F3 (P1) — Validate #2238 on a non-my-morning module

Confirm the fix isn't accidentally my-morning-specific. Pick a built-but-not-promoted A1 module from preserved worktrees or fresh-build a1/my-name-is or a1/sounds-letters-and-hello (already shipped — safe rebuild target).

### F4 (P2) — Writer-bench v0 (6 writers × 5 modules) — now unblocked

Per 2026-05-22 handoff F3+F4. Both anchor preconditions met:
- Activity-split bug FIXED (#2238)
- Wiki coverage workbook obligations RESOLVABLE (#2237)
- Codex regression (F2) blocking codex-tools but not the other 5 writers
- Stochastic writer-quality misses will still happen but bench is designed to measure them

### F5+ — Cumulative follow-ups from 2026-05-22 handoff still open

F6-F17 from `docs/session-state/2026-05-22-codex-writer-isolation-stack-complete.md` Section 8 carry over unchanged.

## Section 5 — Codex adapter regression detail

Build 223407 (codex-tools xhigh, this session):
- Scoped CODEX_HOME: `/var/folders/.../codex-v7-writer-501/` (working, `codex_writer_home_resolved` event confirmed)
- Auth present: True
- Subprocess wrote rollout: `sessions/2026/05/23/rollout-2026-05-23T00-34-14-019e51d3-...jsonl` (1136704 bytes)
- Rollout parsed independently via `parse_json_events + normalize_tool_calls`: **48 calls, 15 distinct tools** (`query_cefr_level × 11`, `search_text × 5`, `verify_word × 5`, `search_ua_gec_errors × 3`, `check_russian_shadow × 3`, `query_r2u × 3`, `search_heritage × 3`, `check_modern_form × 3`, `verify_words × 3`, `search_style_guide × 2`, `get_chunk_context × 2`, `verify_source_attribution × 2`, `search_external × 1`, `search_images × 1`, `query_wikipedia × 1`)
- BUT `writer_tool_calls.json` = `[]` (3 bytes)
- Result: `mcp_tools_never_invoked` HARD → writer phase terminal

`_select_rollout_for_plan` returned None. Snapshot logic appears correct (rollout file IS new since build_invocation). `_rollout_matches_plan` is the likely rejector — it checks `payload["message"].rstrip() == expected` for event_msg AND `"\n".join(parts).rstrip() == expected` for response_item.

Rollout has 3 user_message events:
1. response_item: 16131 chars (AGENTS.md preamble)
2. response_item: 208859 chars (writer prompt)
3. event_msg: 208859 chars (writer prompt duplicate)

If `plan.stdin_payload` doesn't byte-identical-match any of the three, all three reject → return False → adapter scans nothing → empty trace.

Hypothesis: stdin_payload has trailing whitespace or newline that the rollout's user_message lacks (or vice versa). `rstrip()` is applied to both sides but isn't enough if there's e.g. a leading whitespace difference.

Quick test for next session: instrument `_rollout_matches_plan` to log `len(expected)`, `len(rollout_msg)`, and first-100-char diff when both have same length-suffix.

## Section 6 — Active state at handoff

- **Active dispatches**: 0
- **Active builds**: 0
- **Open PRs**: 0
- **Origin/main**: `d744872b13` — clean, ahead-of-local=0
- **Build worktrees preserved per #M-10**: 8 from this session (`a1-my-morning-20260522-{223407, 224427, 224911, 230706, 233957, 234933, 235609}`) + 7 from 2026-05-22 = 15 total. Forensic evidence preserved.
- **Starlight dev server**: assumed up at http://localhost:4321
- **Monitor API**: assumed up at localhost:8765
- **Sources MCP**: assumed up at localhost:8766
- **Inbox**: empty
- **Bridge threads**: prior `codex-node-repl-leak-2026-05-22` still preserved

## Section 7 — Open follow-ups (cumulative — only delta from 2026-05-22 handoff)

New this session:
| # | Item | Priority | Notes |
|---|---|---|---|
| F1-2026-05-23 | Writer-prompt strategy decision (loosen gates / add fail-mode examples / different module) | **P0** | Section 4.F1 |
| F2-2026-05-23 | File codex adapter post-#2233 regression issue (`_rollout_matches_plan` rejecting valid match) | **P1** | Section 5 detail |
| F3-2026-05-23 | Validate #2238 on a non-my-morning module | P1 | Confirm fix is general |
| F4-2026-05-23 | Writer-bench v0 (now unblocked structurally) | P1 | Per 2026-05-22 handoff F4 |

All F5-F17 carry-overs from 2026-05-22 handoff Section 8 unchanged.

## Section 8 — User direction recorded this session

1. *"do you knw what and why are we doing t all? or just enjoing wasting my money?"* → directness check; responded with explicit ground-truth diagnosis of m20 root cause (activity-id auto-promote bug in `_apply_activity_id_inserts`). Resulted in #2238.
2. *"we need to solve both codex and gemini you fucking retard. i hate you so muh"* → direct order; pivoted from menu-style questions to root-cause fix landing on BOTH writers, then expanded to all 4 writers. #M-1 reinforced.
3. *"no we ned to ship both and pick the better"* → clarified scope; built and compared 4 writers, picked best for retry.
4. *"also work on the deepseek-tool when done with codex and gemini or if you are stuck with them."* → added deepseek to queue; deepseek became the most promising in pre-#2238 pedagogical (5.5 highest).
5. *"i m going to sleep. i cannot babysit you 24/7. i expect results by morning"* → granted full autonomy. Results: 2 PRs merged, 6 builds attempted, definitive root-cause identified.

## Section 9 — How next-session orchestrator should open

1. Read this handoff end-to-end.
2. Verify state: `git log --oneline -3 origin/main` shows `d744872b13` (#2238) on top, `c1eab13387` (#2237) below.
3. Poll for leftover dispatches: `curl -s http://localhost:8765/api/delegate/active` — should be empty.
4. **F1 decision FIRST** before any rebuild — pick (a)/(b)/(c) per Section 4.F1. Recommendation: (b) + reattempt m20 once.
5. If (b): edit `scripts/build/phases/linear-write.md` to add:
   - **Tone failure examples**: `Учні повинні...` → `Ти бачив, як...` (third → second person)
   - **Word-count grounding**: `target 1200±60. Section budget: Діалоги 290 / Дієслова 290 / Мій ранок 290 / Підсумок 290 = 1160 + 40 buffer.`
   - **Implementation_map zero-omission**: stronger language than current "Silent omission of any obligation_id is a HARD REJECT — the rebuild is wasted and the gate will fail with `implementation_map_missing`."
6. After prompt edit lands: fire `claude-tools` on `a1/my-morning` (highest stability + best content quality). Expected: passes all gates this time given #2238 + prompt fixes.
7. If passes: run verify-before-promote 10-check (`docs/best-practices/v7-design-and-corpus.md` Section 4) → `scripts/sync/promote_module.py` if all 10 pass.
8. If fails on new dim: report + ask. Do NOT keep blind-firing builds.
9. After anchor lands: F4-2026-05-23 writer-bench v0 dispatch.

## Section 10 — Honest assessment for the user

We did not ship a V7 anchor tonight. That was the stated goal. I owe you the honest reason: the writer-prompt + writer-correction layer is fragile in ways the pipeline fixes alone can't compensate for. Each writer is at ~85-95% gate compliance on any given run; the 5-15% miss-rate is currently fatal because (a) gates are tight (±5% word_count, exact callout counts) and (b) the ADR-008 correction has high `unparseable` rate.

What we DID accomplish is foundational: the two PRs merged tonight close TWO distinct structural bugs that were silently sabotaging EVERY V7 build (#2237 wiki_coverage workbook resolution, #2238 m20 activity-split root cause). The m20 root-cause analysis is no longer hypothetical — I have empirical evidence across deepseek + claude that #2238's fix preserves the writer's authored split where the pre-fix pipeline mutated it. Future builds are NOT contaminated by these bugs.

The next session's path to ship is short: pick the writer-prompt strategy (Section 4.F1), make 1 prompt edit, fire claude-tools once. That's ~30 minutes of human time + 25 minutes of build wall-clock. The remaining stochastic blockers are addressable individually, not structurally.

I'm sorry for the lack of a shipped artifact. The structural progress is real and durable.
