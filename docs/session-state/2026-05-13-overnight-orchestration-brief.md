---
date: 2026-05-13
session: "OVERNIGHT — Plan A autonomous orchestration toward 'build first 7 A1 modules' goal. **All 5 prep PRs shipped. Build queue HALTED on module 1/7 by a discovered P0 infrastructure bug (#1944): claude-tools writer subprocess is behaving as orchestrator instead of curriculum writer — 0 mcp__sources__* calls, instead made 10 Bash + 3 Read + 1 ScheduleWakeup polling the parent orchestrator's state.**"
status: halted-cleanly
mode: overnight-autonomous
authority:
  - "user-overridden Plan A — 'CLAUDE.md HARD rule on builds suspended for tonight only'"
  - "docs/decisions/2026-05-13-ulp-derived-student-aware-immersion.md (ACCEPTED, merged in #1936)"
---

# Overnight Orchestration Brief — 2026-05-13

> Final handoff. Predecessor: `docs/session-state/2026-05-14-v7-mdx-assembler-shipped-brief.md`.

## TL;DR

**5 of 5 prep PRs shipped. Build queue halted at module 1/7 on a writer-subprocess infrastructure bug — filed as `#1944 BLOCKER`.**

| PR | Branch / Work | State |
|---|---|---|
| #1936 | Decision Card + cleanup | ✅ MERGED 22:13:55Z |
| #1938 | Plan-review audit reports for A1 seq 1-7 | ✅ MERGED 22:53:00Z |
| #1937 | Multimedia resources + HIGH CodeQL urlparse fix | ✅ MERGED 23:00:15Z |
| #1939 | PR1 — learner-state V7 wiring + dict-grammar fix + lazy-import fix | ✅ MERGED 23:06:24Z |
| #1943 | PR2 — ULP-derived immersion + plan.targets + recycle-cadence + 3 plan migrations + schema regen | ✅ MERGED 23:40:04Z |
| **Build queue** | 7 A1 modules sequential | ❌ HALTED 23:46:55Z on module 1/7 (sounds-letters-and-hello) — see #1944 |

**Main at `6cd8e4b830`.** V7 pipeline is now student-aware (PR1) + has plan.targets schema + recycle-cadence WARN gate + ULP-derivation function (flag default OFF). Multimedia resources Tab 4 supports YouTube/blog/video.

## What blocked the build queue (#1944)

`v7_build.py a1 sounds-letters-and-hello` failed in writer phase with HARD gate `MCP_TOOLS_NEVER_INVOKED`. The writer (claude-tools) made **14 tool calls in 5 minutes** — none were `mcp__sources__*`:

| count | tool | what the writer actually did |
|---|---|---|
| 10 | Bash | `curl http://localhost:8765/api/delegate/active`, `git status`, `ps auxww \| grep v7_build`, `gh pr list`, etc. |
| 3 | Read | **the orchestrator's overnight handoff**, `docs/session-state/current.md`, `/tmp/build-queue-a1-first-7.sh` |
| 1 | ScheduleWakeup | reason: *"A1 build queue (7 modules sequential, ~10-15 min/module) needs orchestrator re-check at module-transition cadence — verify queue PID 75993 alive..."* |
| **0** | **mcp__sources__\*** | **(none)** |

The writer **read the orchestrator's handoff**, **polled the Monitor API**, **inspected the build queue script**, and **scheduled itself a wakeup as if it were the orchestrator**. It made zero curriculum-content tool calls. The HARD gate correctly caught this on the post-write check.

**Hypothesis:** The writer subprocess inherits the parent Claude Code session's context / system prompt / tool catalog instead of getting its OWN constrained writer prompt + sources-only tool catalog. When it reads the overnight handoff in the working tree, it identifies as the orchestrator and starts running orchestrator-style tool calls.

**Pre-flight `mcp_config_resolved` was OK** — `.mcp.json` is fine, sources MCP server is running, config string resolution passed. The bug is in the writer-spawn mechanism, not the MCP config.

Full diagnosis + recommended investigation paths in **`#1944`**.

## Build queue sequence (still pending after fix)

1. ❌ `a1/sounds-letters-and-hello` (seq 1) — halted on writer-as-orchestrator bug
2. ⏸ `a1/reading-ukrainian` (seq 2)
3. ⏸ `a1/special-signs` (seq 3)
4. ⏸ `a1/stress-and-melody` (seq 4)
5. ⏸ `a1/who-am-i` (seq 5) — plan-review flagged HIGH (Підсумок section words:0)
6. ⏸ `a1/my-family` (seq 6) — plan-review borderline (муж/чоловік register edge)
7. ⏸ `a1/checkpoint-first-contact` (seq 7) — plan-review flagged HIGH (тато/папа Surzhyk row)

All 7 plans are `lifecycle: locked` from 2026-04-23 review.

## Dispatches fired this session

| Time (UTC) | Task | Agent | Duration | Outcome |
|---|---|---|---|---|
| 22:13 | pr1-learner-state-v7-wiring-2026-05-13 | codex | 85s | ABORTED `scope-boundary` (brief error — wrong wiring file referenced) |
| 22:21 | pr1-learner-state-v7-wiring-2026-05-13-v2 | codex | 720s | DONE → #1939 (after 2 inline fixes by orchestrator: dict-grammar normalization + lazy-import) |
| 22:25 | plan-review-a1-first-7-2026-05-13 | claude xhigh Opus 4.7 | 617s | DONE → #1938 (3 LOCK_NOW / 1 borderline / 3 NEEDS_FIX) |
| 22:25 | multimedia-resources-2026-05-13 | codex | 555s | DONE → #1937 (after inline urlparse security fix for HIGH CodeQL alert) |
| 23:06 | pr2-ulp-immersion-2026-05-13 | codex | 851s | DONE → #1943 (after inline lesson-schema-yaml regen fixup) |

## Inline orchestrator fixes this session

1. **PR1 v2 — pushed past Codex's hold.** Codex held the push citing `test_cache_invalidate_by_prefix` failure. Orchestrator verified test passes in isolation (pre-existing flake, CI deselect already handles it). Safe to push.
2. **#1937 multimedia — urlparse fix.** CodeQL flagged HIGH `py/incomplete-url-substring-sanitization`. 5-LOC fix + 3 regression tests in `scripts/build/phases/wiki_manifest.py` and `tests/test_wiki_manifest.py`. Pushed as `2b5e65b72a`.
3. **PR1 v2 — dict-grammar + lazy-import fixes.** Post-push CI exposed 9 real failures Codex never saw (`-x` early-stop on the cache flake). Two root causes: `_load_grammar` returned mixed string/dict items breaking `format_learner_state`; `audit/checks/learner_state` module-load broke bare-cwd `vocab_progression` CLI smoke. Fixed with `69e5067d70`.
4. **PR2 — lesson-schema-yaml regen.** Codex edited `docs/lesson-contract.md` (added "Plan Targets" section) but didn't run `scripts/build/generate_lesson_schema.py`. One-line SHA refresh as `1b3069e6b1`.

## Plan-review verdicts (#1938 summary — for build-queue resume)

| seq | slug | verdict |
|-----|------|---------|
| 1 | sounds-letters-and-hello | NEEDS_FIX (2 MEDIUM: 1pl imperative `Прочитаймо` out-of-scope; `ирій` too rare for И) |
| 2 | reading-ukrainian | **PASS** |
| 3 | special-signs | **PASS** |
| 4 | stress-and-melody | **PASS** (1 MEDIUM TTS forward-ref) |
| 5 | who-am-i | NEEDS_FIX (1 HIGH: Підсумок section `words: 0`; 3 MEDIUM acc/gen frozen-chunks) |
| 6 | my-family | PASS borderline (1 MEDIUM: `муж/чоловік` register edge) |
| 7 | checkpoint-first-contact | NEEDS_FIX (1 HIGH: `тато/папа` Surzhyk row; 1 MEDIUM checkpoint word_target inconsistency) |

0 CRITICAL, 0 NEEDS_REVISION. Cross-cutting items filed as #1940 + #1941.

## Bugs filed tonight

| # | Title | Priority |
|---|---|---|
| **#1944** | **[BLOCKER][v7_build] claude-tools writer subprocess behaves as orchestrator — 14 tool calls, ZERO mcp__sources__\*, then MCP_TOOLS_NEVER_INVOKED HARD halt** | **P0** |
| #1940 | [curriculum] Add 'pedagogical_deviations_from_standard:' plan field | P1 |
| #1941 | [curriculum] A1-checkpoint word_target inconsistency: 5/7 at 1200 vs 2/7 at 1000 | P2 |
| #1942 | [harness] Dispatch briefs should forbid 'pytest -x' in final pre-push verification | P2 |

## Working-tree state

`git stash@{0}: On main: pre-build-queue-2026-05-13` contains:

- 5 modified files from prior session at `curriculum/l2-uk-en/a1/my-morning/` (V7 source artifacts) + regenerated MDX
- `docs/session-state/current.md` modification (from prior session)
- 5 untracked build artifacts at `curriculum/l2-uk-en/a1/my-morning/` (knowledge_packet, python_qg, etc.)

The build queue's writer ran briefly and wrote `writer_tool_calls.json` with 14 tool calls — primary diagnostic artifact for #1944. **Preserved as `audit/incidents/2026-05-13-1944-writer-tool-calls.json`** (committed in the hygiene PR). The original at `curriculum/l2-uk-en/a1/sounds-letters-and-hello/writer_tool_calls.json` remains untracked in the project dir and can be removed when cleaning up.

**Morning sequence to recover:**
1. Read `#1944` for the writer-subprocess diagnosis.
2. `git stash pop` to restore the pre-build dirty state (V7 artifacts at my-morning, current.md update).
3. Investigate v7_build.py writer-phase spawn mechanism per #1944's recommended paths.
4. After fix lands: resume build queue from `a1/sounds-letters-and-hello`.

## Held / deferred items (morning agenda)

- **#1944 P0** — fix writer-as-orchestrator behavior before any V7 build can succeed
- **Plan re-versions** for the 4 plans with NEEDS_FIX issues (M1, M5, M6, M7) — locked-lifecycle protocol requires version bump + changelog
- **#1873 starlight 0.39** — held: real Frontend (build+vitest) failure, needs investigation
- **#1874 react 19.2.6 (in /starlight)** — held: real Frontend failure
- **Dependabot majors:** #1866 lxml 5→6, #1868 attrs 25→26 — held for conservative evaluation
- **Dependabot minor:** #1871 mcp-memory-service big-minor — held for conservative evaluation
- **52 remaining A1 plans** need `plan.targets` migration (PR2 only did 3 as proof-of-shape per Decision Card)
- **Phase 4 calibration** to flip `USE_ULP_IMMERSION_DERIVATION` from False → True (PR2 left it dormant)
- **CC-2 Surzhyk-drill VESUM-anchored verification** — process improvement, could be added as agent-cooperation note
- **A1/my-morning Phase 5 rebuild** (per Decision Card) — separate from the first-7 build queue. Deferred until after first-7 batch completes (post-#1944 fix).
- **Decision Cards still pending:** `2026-05-06-multi-ui-channel-participation.md`, `2026-05-09-decision-graph-view`, `2026-05-12-autonomous-codex-dispatch-narrow-class.md`, `2026-05-13-writer-split-by-tab.md` — none scope-block A1 work

## What worked well tonight

- **The cascade structure** — 5 PRs in 1.5 hr, each unblocking the next, with inline fixups when CI/scope issues arose.
- **Dispatch-brief discipline.** #1942's recommendation (forbid `pytest -x`) is the one process improvement filed; the rest of the orchestration discipline (worktrees, conventional commits, raw-output evidence) held up well.
- **Inline CI fixups.** 4 minor inline orchestrator fixes (CodeQL urlparse, dict-grammar, lazy-import, schema-regen) kept the cascade moving without dispatching follow-ups. Each was ≤10 LOC and within the inline scope of #M-0 row 1.
- **HARD audit gates working as designed.** `MCP_TOOLS_NEVER_INVOKED` correctly halted the build before producing bad content. The pipeline is doing its job — the bug is upstream.

## What did NOT work

- **The writer subprocess.** This is the entire halt. #1944 captures it.
- **Initial PR1 brief.** v1 had wrong wiring file (prompt_builder.py vs linear_pipeline.py:writer_context), causing a wasted 85s scope-boundary abort. v2 fixed.
- **Codex dispatch brief used `pytest -x`.** Filed as #1942. The 9 hidden failures cost 1 inline-fix cycle that proper full-suite dispatch would have surfaced earlier.

## Predecessor reference

`docs/session-state/2026-05-14-v7-mdx-assembler-shipped-brief.md` — set up the "build first 7 A1 modules" goal context, the ULP-derived student-aware immersion architectural finding, and the open-issue inventory at session start.
