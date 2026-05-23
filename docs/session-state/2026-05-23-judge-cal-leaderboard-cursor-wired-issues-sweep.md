---
date: 2026-05-23
session: "Russianism judge leaderboard fleshed out (qwen3.7-max + deepseek-v4-pro + 3 grok variants + composer-2.5 cal'd against existing 4-model leaderboard), cursor-agent installed + Phase 1 bridge (ab ask-cursor) wired, GH issues sweep proven (one closed, one escalated with audit), 3 carry-over PRs shipped (writer-prompt artifact-fence restore, judge loader, zizmor offline) + the amelina scaffold that triggered them. Validation build for a1/my-morning is at 21/22 gates green — only textbook_grounding (30-words-per-cited-source vs aggregate interpretation) remains to fix in the next session."
status: green-leaderboard-and-cursor-shipped-m20-one-fix-from-promote
main_sha: c6d4345119
main_green: clean (review/review advisory persists per F7 GEMINI_API_KEY)
working_tree_dirty: pre-existing carry-overs + new dispatch-briefs + new audit dirs + new opencode global mcp config + new .cursor/mcp.json + cursor_judge_calibration.py + opencode_judge_calibration.py + docs/architecture/codebase-diagram.html (cursor-IDE-generated, untracked)
prs_merged_this_session: ["#2247 zizmor --offline", "#2248 writer-prompt artifact-fence restore (PR-C regression)", "#2249 judge cal loader prefers working tree", "#2250 amelina-women-looking-at-war plan scaffold", "#2253 amelina seminar-required references + subtitle (followup #2250)", "#2252 cursor-agent bridge Phase 1 (ab ask-cursor) — merged after rebase onto #2253"]
prs_wip_unmerged: []
cursor_ide_question_queued: "Phase 2 + Phase 3 design spec for cursor-agent V7 writer/reviewer wiring — drafted 2026-05-23, awaiting user-relayed response from cursor IDE composer. Covers adapter shape, --trust/--approve-mcps/--yolo security boundary, MCP discipline at writer invocation, SELF_REVIEW_DETECTED gate compatibility for cursor-hosted writer + cursor-hosted reviewer (different model ids), PROMPT_BY_WRITER entry decision (share linear-write.md vs new cursor-specific), and the critical tests-to-touch coverage list to avoid the #2250→#2253 regression class."
issues_closed_this_session: ["#2220 amelina-women-looking-at-war.yaml missing required fields"]
issues_filed_this_session: ["#2251 wiki-ingestion Option B follow-up to #1960 — 158 ext-article-N stubs need backfill (Option A audit by gemini found 0/158 safe-to-strip)"]
active_dispatches: []
active_builds: []
builds_completed_this_session: ["a1/my-morning validation #4 — 21/22 deterministic gates green, textbook_grounding fails on per-source 30-word interpretation, build_dir=.worktrees/builds/a1-my-morning-20260523-184413, NOT promoted"]
headline_finding: "**Russianism judge leaderboard now has 9 calibrated models**, top of which is **grok-4.20-reasoning at F1=86% (tied with claude-opus-4-7), 100% precision, 100% case-accuracy, FREE via xAI subscription**. Deepseek-v4-pro is the cost-quality champion at F1=77% / 100% precision / $0.43/1M-in. Qwen3.7-max disappoints (F1=55%) — not worth its 5.8× price premium over deepseek. Cursor composer-2.5 over-flags clean text (F1=71%, P=67%) but has STRONGER no-fabrication discipline than qwen3.7-max under MCP-tool rejection. **m20 (a1/my-morning)** is now ONE writer-prompt-clarification away from V7-promote-readiness after 4 build attempts this session each surfacing a different layer of regression (writer-output parse → vesum bad-form-marker → textbook_grounding-aggregate-vs-per-source). Cursor-agent installed + Phase 1 bridge merged; Phases 2 (delegate adapter) + 3 (V7 writer/reviewer wiring) queued."
next_session_first_item: "1) **m20 textbook_grounding fix** — 1-line clarification to `scripts/build/phases/linear-write.md` rule #R-TEXTBOOK-30W: change 'paste >=30 contiguous Ukrainian words from that returned text into a blockquote' → '...into a blockquote PER cited textbook (not aggregate across all cited)'. Re-fire validation build #5 on a1/my-morning. If 22/22 → 10-check verify-before-promote per docs/best-practices/v7-design-and-corpus.md §4 → scripts/sync/promote_module.py a1 my-morning. First V7 anchor under new shape. 2) **Cursor Phase 2** (runtime adapter, ~250 LOC, gemini): scripts/agent_runtime/adapters/cursor.py + delegate.py --agent enum + fallback substitutions + tests. Brief at docs/dispatch-briefs/ already has the Phase 1 reference; mirror that pattern. 3) **Cursor Phase 3** (V7 writer/reviewer wiring, ~250 LOC, gemini): PROMPT_BY_WRITER += {cursor-tools: ...} + writer-prompt template + writer-isolation MCP discipline + reviewer exposure + tests. 4) **Consider replacing codex with grok-4.20-reasoning as primary V7 LLM judge** — biggest quality+cost upgrade available. Tied for #1 F1 (86%), highest precision (100%), free via subscription. Writer-isolation gate already enforces no-self-review (codex writes, grok reviews). 5) **GH issues sweep continuation** — #2210 V7 learner-state drift (investigation shape; gemini); #1969 resources_search_attempted=0 regression (writer-prompt analysis; gemini); #2208 / #2209 V7 inline-injection issues (codex if pipeline-deep, gemini if prompt-side). Each is 10-30 min end-to-end."
---

# 2026-05-23 — Russianism judge leaderboard + cursor wired + m20 one fix from promote

## Session arc

User asked early on whether qwen3.7-max had been tested for russianism detection. The honest answer was no — only qwen-3.6, claude-opus-4-7, gemini-3.1-pro, gpt-5.5 had been calibrated against the 12-case Antonenko-grounded gold set on `eval/russianism/calibration-cases.jsonl`. That kicked off a multi-hour judge calibration thread that ran in parallel with multiple other workstreams.

The session split naturally into 5 phases:

1. **Judge calibration build-out** (qwen3.7-max → deepseek-v4-pro → 3 grok variants → composer-2.5)
2. **PR-C writer-prompt regression chase** (validation build #1 hit the artifact-fence rejection landed by PR-C; PR #2248 restored the spec; build #2 advanced to 21/22 gates)
3. **GH issues sweep proof-of-concept** (#2220 closed via PR #2250 in ~10 min end-to-end; #1960 escalated via #2251 with full audit)
4. **Cursor-agent integration Phase 1** (install + .cursor/mcp.json + bridge subcommand `ab ask-cursor` → PR #2252)
5. **Plan-scaffold regression** (my brief omitted the seminar-specific test → main pytest red after #2250 merge → fixed by #2253)

## Behavioral lessons captured this session

1. **Brief-writing bug — tests-not-listed regression cycle.** PR #2250 brief listed `tests/audit/test_validate_plan.py` + `tests/audit/test_plan_invariants.py` as the targeted-test set. Neither file exists. Gemini honestly surfaced this and substituted `tests/audit/test_config_invariants.py` (283 passed). But the SEMINAR-specific check at `tests/curriculum/test_seminar_plan_refs_titles.py` was NEVER on the list — neither in the brief nor in gemini's substitute. Main went red on `Test (pytest)` immediately after merge. Fix shipped as #2253, but the meta-lesson is: **dispatch briefs MUST `grep -rl 'def test_' tests/ | xargs grep -l <YourTargetFile>` to discover which tests touch the file you're editing, not name tests from memory**. Adding this to the brief template would prevent the entire class.

2. **Cal-route choice matters more than I assumed.** Qwen3.7-max scored F1=55% via opencode-openrouter (with ~13K-token coder-agent system prompt). Grok-4.20-reasoning scored F1=86% via the SAME opencode route. Composer-2.5 scored F1=71% via cursor-agent. The opencode-route confound hurts some models (qwen3.7-max) more than others (grok-4.20-reasoning unaffected — F1 ABOVE hermes-route grok-4.3's 69%). Future calibrations should pick the route that matches **deployment shape**, not the route that's apples-to-apples with the historical leaderboard.

3. **Cursor composer-2.5 has stronger no-fabrication discipline than qwen3.7-max** under MCP-tool rejection. When the first MCP probe rejected the verify_words call 3 times, composer-2.5 honestly REFUSED to classify the test words rather than guessing — even with strict "do not guess" prompt instruction. Qwen3.7-max also passed the MCP-use test cleanly but didn't get tested under rejection. The composer behavior is the right discipline for a judge role.

4. **Dispatch worktree wakeup pattern works.** Two gemini dispatches fired this session (#2220 + #1960). Both used `ScheduleWakeup` 20-25min polling `/api/delegate/active` to land. #2220 completed in 4.5min wall, opened PR in <4min, merged ~10min end-to-end. #1960 completed in 14min wall, opened NO PR because gemini's audit found 0/158 safe-to-strip stubs (correctly refused destructive action, drafted the Option-B follow-up issue text). Pattern validated: `delegate.py dispatch --agent gemini --worktree --silence-timeout 1800` + ScheduleWakeup ~20min poll = clean end-to-end.

5. **The "side job" reframe.** Mid-session the user said "this is not your primary job it is a side job. dont focus on only this" — about the russianism calibration thread. The orchestrator-active fallback was to keep parallel work moving (GH issues sweep, cursor wiring) while cal jobs ran in background. This worked: 5 PRs landed + Phase 1 cursor merged-pending while the cal investigation generated 5 new calibrated judges + 2 MCP validations.

6. **User-direct-order overrides any other plan.** "We will swap in grok instead of qwen and test grok 4.20 vs grok 4.3 ok ?" was a direct trim signal even though qwen3.7-max writer-mode wiring was queued. Trimmed it; never resurfaced. Same with "i added cursor, ... test composer 2.5 there" — pivoted immediately.

## What's shipped

| PR | Commit | Scope |
|---|---|---|
| #2247 | `397b9f4bef` | `.github/workflows/zizmor.yml` adds `advanced-args: '--offline'`. Restores Security Analysis workflow that was failing on artipacked-online-verification HTTP 401. |
| #2248 | `c895e8ac15` | `scripts/build/phases/linear-write.md` +2.3KB: restores the artifact-emission spec stripped by PR-C. Writer now knows to fence `activities.yaml`/`vocabulary.yaml`/`resources.yaml` as ```` ```json file=<name> ```` and module.md in a 4-backtick OUTER fence. Validation build #1 was 100% blocked on this. |
| #2249 | `d36221f18d` | `scripts/audit/_judge_eval_lib.py::pull_calibration_cases` defaults to working-tree read, falls back to legacy `origin/pr-2006` ref. Plus regression test. Unblocks all russianism calibration runners (qwen / grok / opencode / cursor sibling scripts). |
| #2250 | `0564da4b57` | `curriculum/l2-uk-en/plans/lit-doc/amelina-women-looking-at-war.yaml` gets `module`, `objectives`, `title`, `version`, `phase`, `vocabulary_hints` added. Closes #2220. |
| #2253 | `69fe2289f8` | Same plan gets `references: [Pending Reference placeholder]` + `subtitle: 'Victoria Amelina: "Looking at Women Looking at War"'`. Followup to #2250 that fixed the pytest red I caused by not listing the seminar-specific test in the dispatch brief. Plan version bumped 1.0.0 → 1.1.0 with `.bak` per immutability rule. |
| **#2252 WIP** | branch `gemini/cursor-phase-1-bridge-2026-05-23` | `scripts/ai_agent_bridge/_cursor.py` + `tests/test_ask_cursor.py` + `_cli.py` registration. Enables `ab ask-cursor` Q&A subcommand routing through cursor-agent (default model `composer-2.5`). CI was red on pytest pre-#2253; re-running now to pick up green main. Should merge cleanly. |

Plus filed: **#2251** wiki-ingestion Option B follow-up to #1960 (158 ext-article-N stubs need backfill from manifest; Option A audit found 0/158 safe-to-strip).

## Russianism judge calibration — full leaderboard (9 models)

All calibrated against same 12-case Antonenko-grounded gold set (`eval/russianism/calibration-cases.jsonl` from PR #2006 / commit 82afad7438).

| Rank | Judge | F1 | P | R | Case acc | $/1M-in | Cal route this session |
|---|---|---:|---:|---:|---:|---|---|
| 1 | claude-opus-4-7 | 86 | 79 | 94 | 100 | $15.00 | prior (2026-05-15) |
| 1 (tie) | **grok-4.20-reasoning** | **86** | **100** | **75** | **100** | **FREE (xAI sub)** | opencode-xAI today |
| 3 | gemini-3.1-pro-preview | 84 | 81 | 87 | 92 | $2.00 | prior (2026-05-15) |
| 4 | gpt-5.5 | 78 | 90 | 69 | 83 | $5.00 | prior (2026-05-15) |
| 5 | deepseek-v4-pro | 77 | 100 | 62 | 92 | $0.43 | opencode-openrouter today |
| 6 | grok-4.3 | 74 | 91 | 63 | 83 | FREE (sub) | opencode-xAI today |
| 7 | composer-2.5 | 71 | 67 | 75 | 67 | FREE (10x promo) | cursor-agent today |
| 8 | qwen-3.6-plus | 69 | 90 | 56 | 92 | $0.33 | prior (2026-05-19, hermes) |
| 9 | qwen-3.7-max | 55 | 100 | 38 | 67 | $2.50 | opencode-openrouter today |
| — | grok-4.20-multi-agent | parse-fail (0) | — | — | 58 | FREE (sub) | opencode-xAI today; verdict-parser couldn't extract; needs ~30min diagnosis |

Artifacts at `audit/2026-05-23-{model}-{route}-judge-calibration/{leaderboard-row.json, REPORT.md, judgments.jsonl}` for each new entry.

**MCP-use validation:** qwen3.7-max + composer-2.5 both call `mcp__sources__verify_words` cleanly (no hallucination, grounded results, correct arg shape). Composer-2.5 stronger on REFUSING to fabricate when tool rejected. Both cleared for MCP-driven writer/reviewer roles.

## What's running at handoff

Nothing in flight. The PR #2252 (cursor Phase 1 bridge) CI re-run was kicked at ~22:55Z; if it greens up I'll merge in the next 5 min, otherwise the handoff is the boundary — next session merges. Check with: `gh pr view 2252 -R learn-ukrainian/learn-ukrainian.github.io --json mergeStateStatus,state` and `gh pr checks 2252 -R learn-ukrainian/learn-ukrainian.github.io`.

## Validation build a1/my-morning — close to ship

4 attempts this session:

| # | Build dir | Phase failed | Reason |
|---|---|---|---|
| 1 | (re-fire from prior session) | writer parse | `activities.yaml must be fenced as json, got activities.yaml` — PR-C stripped fence spec. PR #2248 fixed. |
| 2 | 20260523-181153 | writer output parsing | same — pre-#2248 fix |
| 3 | 20260523-184413 | python_qg (after correction) | `vesum_verified missing=**ться**, користу-юся, користу-ється**` initially → codex correction loop FIXED it; then `textbook_grounding`: 1 of 3 blockquotes ≥30 words, missing 30-word grounding for Захарійчук p.24 and p.52 |
| 4 (logically same as 3) | 20260523-184413 | textbook_grounding | (as above) — 21/22 gates pass, 1 gate fails on per-source 30-word interpretation |

Status: **NOT promoted, in worktree**. Main still has the post-revert skeleton (4 inline activities, no llm_qg.json, no implementation_map.json).

**Fix layer = writer prompt** (NOT gate threshold — non-negotiable rule #1 forbids lowering). One-line clarification to `scripts/build/phases/linear-write.md` rule `#R-TEXTBOOK-30W` at line 180: change "paste >=30 contiguous Ukrainian words from that returned text into a blockquote" → "paste >=30 contiguous Ukrainian words **PER cited textbook page** (not aggregate across all cited)". Then re-fire build #5. If green → 10-check verify-before-promote per `docs/best-practices/v7-design-and-corpus.md §4` → `scripts/sync/promote_module.py a1 my-morning`. First V7 anchor under post-reset shape.

## Cursor-agent integration — Phase 1 of 3

Installed via official one-liner `curl https://cursor.com/install -fsS | bash`. Binaries at `~/.local/bin/{agent,cursor-agent}`. OAuth'd to `krisztian.koos@gmail.com`. 10x usage promotion active (effectively free for our scale).

Composer 2.5 + many other models exposed: composer-2.5, composer-2.5-fast, gpt-5.5-high, claude-opus-4-7-thinking-high, gpt-5.3-codex (low/medium/high/xhigh × fast/non-fast), etc. — ~30 models behind one subscription.

Project-local MCP config at `.cursor/mcp.json` mirrors `.mcp.json` (sources MCP at 127.0.0.1:8766). `agent mcp enable sources` approved. `agent mcp list-tools sources` shows all 34 sources tools accessible.

**Phase 1 (#2252):** bridge subcommand `ab ask-cursor` for Q&A — mirrors PR-D1's `ab ask-opencode` / `ab ask-hermes`. Headless invocation: `agent -p PROMPT --model MODEL --output-format text --trust`. Tests pass (7). Smoke verified: composer-2.5 echoes "OK" through the bridge.

**Phase 2 (queued):** runtime adapter `scripts/agent_runtime/adapters/cursor.py` + delegate.py `--agent cursor` enum + `scripts/config/agent_fallback_substitutions.yaml`. ~250 LOC. Brief shape: mirror `scripts/agent_runtime/adapters/{codex,gemini,opencode}.py`. Gemini dispatch.

**Phase 3 (queued):** V7 writer + reviewer wiring. `PROMPT_BY_WRITER += {cursor-tools: ...}` + writer-prompt template (or share `linear-write.md`) + writer-isolation MCP discipline (cursor needs `--yolo --approve-mcps` for MCP — but `--yolo` also force-approves shell/write tools, security-critical; need to scope carefully) + reviewer exposure. ~250 LOC. Gemini dispatch.

**Phase 4 (test):** writer-bench cell on a1/my-morning with `--writer cursor-tools`; reviewer cross-check on shipped modules vs codex; update `pipeline.md` + `track-architecture.md`.

## Other carry-overs (priority-ordered)

| # | Item | Priority | Notes |
|---|---|---|---|
| **F1-2026-05-23-eve** | m20 textbook_grounding writer-prompt clarification + build #5 → promote | **P0** | First-session action above |
| **F2-2026-05-23-eve** | Cursor Phase 2 (runtime adapter) | **P1** | Brief = mirror existing adapter pattern; gemini |
| **F3-2026-05-23-eve** | Cursor Phase 3 (V7 writer + reviewer wiring) | **P1** | After Phase 2 lands |
| **F4-2026-05-23-eve** | Decide: replace codex with grok-4.20-reasoning as primary V7 LLM judge | **P1** | Tied for #1 F1, highest precision, FREE. Biggest quality+cost upgrade available. Requires writer-isolation gate audit (writer=claude-tools, reviewer=grok-4.20-reasoning, `SELF_REVIEW_DETECTED` enforces). |
| F5-2026-05-23-eve | grok-4.20-multi-agent parse-failure diagnosis | P3 | Multi-agent variant emits different output shape that `parse_json_verdict` can't extract. ~30min if/when needed. |
| F6-2026-05-23-eve | Amelina real-references backfill | P3 | Currently `Pending Reference` placeholder per PR #2168 convention. Under same lineage as #2164. |
| F7-2026-05-23-eve | Composer-2.5 over-flagging precision issue | P3 | Documented in cal results. Pattern: false-positives on disputable forms (`Доброго дня` etc). Could prompt-tune. |
| **F1-prior carryover** | F3 renderer-logic audit (qwen3.7-max insight on `render_writer_prompt` duplicate substitution at L103) | P2 | Documented at `audit/2026-05-23-renderer-logic-audit/FINDINGS.md`. 1-line fix saving ~1.5-2.5KB rendered prompt + clarity. |
| **F2-prior carryover** | DOWNSTREAM_TOKENS guard in prompt-engineering docs (pre-commit lint for `{ALLCAPS}` in prose body) | P3 | Sister of F1; could ship as one PR. |
| **F3-prior carryover** | Writer-prompt-appendix.md is empty stub | P3 | Per PR-C brief, was supposed to contain the LESSON_CONTRACT §3 component inventory. Either populate or remove. |
| **F4-prior carryover** | DISPATCH BRIEF TEMPLATE: add "discover which tests cover the file you're editing" step | **P1 (META)** | THE root-cause fix for the PR #2253 regression. Add to brief template + maybe a `scripts/dispatch/discover_tests.py` helper that takes a file path and outputs the test files that import/reference it. |
| F5-prior carryover | PR-D2: full delegate.py adapter for opencode + hermes | P1 | Filed earlier as P1. Now superseded somewhat by Cursor Phase 2 work (same shape). Could batch. |
| F6-prior carryover | PR-E: verify_before_promote.py automation + /review-module skill | P1 | Post-m20-promote. Lowers per-module human review tax. |
| F7-prior carryover | Codex CLI silence-timeout proper fix | P3 | Workaround at 60min; real fix requires heartbeat or stdout buffering. |

## Honest assessment

**The session went sideways into the judge cal investigation longer than ideal**, but the user pivoted me back via "side job" framing and the back half delivered cleanly: 5 PRs merged, 1 issue closed, 1 escalated with audit, cursor Phase 1 wired, m20 advanced from "writer-output-parse fail" to "21/22 gates green". The user's directness throughout was the orchestrator's most useful signal — when frustrated, they trim scope hard, and trimming serves the project.

**m20 is one writer-prompt clarification from V7-promote-readiness.** The codex correction loop demonstrates real value (fixed VESUM bad-form-marker issue automatically). The remaining `textbook_grounding` failure is a prompt-wording fix, not an architectural one — but per #M-11 (HARD), don't ship m20 without the 10-check verify-before-promote even if gates go 22/22. The artifact-quality check (Activities tab populated, Resources tab fresh, INLINE/WORKBOOK split correct, etc.) is non-negotiable.

**Russianism judge field is now well-mapped.** Grok-4.20-reasoning is the dominant pick by every metric that matters (F1 ties #1, P=100, case-acc=100, $0/cost). The codex→grok-4.20-reasoning replacement decision should land in the next 1-2 sessions if user agrees.

**Cursor integration is a 3-phase ~620-LOC build-out across two more dispatches**, each gemini-shape and ~10-15min wall-clock each per the #2250 pattern. Total ~30min of dispatch time + 5-10min review/merge each → realistically a half-session.

**The PR #2253 regression is the most actionable behavioral learning of the session.** The fix is structural: dispatch brief template should require a "tests-that-reference-this-file" discovery step. Without it, the same class of regression will recur.

## Session-handoff discipline

Per the meta-discipline convention encoded in earlier handoffs: this is narrative + carry-overs. The russianism-leaderboard write-up + composer-2.5 cal results live in `audit/2026-05-23-*/` dirs. The opencode-route + cursor-agent + judge-cal-loader changes (#2247, #2248, #2249, #2250, #2253) are documented in their respective commit bodies + PR descriptions. No ADR needed yet for the cursor integration (Phase 3 wiring is when the architectural commitment lands).

The next session opens with the m20 textbook_grounding fix (one-line) → build #5 → if green → promote. Then Cursor Phase 2 dispatch. Then either Cursor Phase 3 OR the grok-4.20-reasoning judge swap discussion, depending on user direction.
