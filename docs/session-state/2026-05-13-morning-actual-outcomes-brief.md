---
date: 2026-05-13
session: "Morning actual outcomes — both night dispatches landed, ADR REVISED, idle-orchestrator failure encoded as #M-8"
status: ok
detail: 2026-05-13-morning-actual-outcomes.html
main_sha: bf774d7d48
main_green: true
open_prs: 0
active_dispatches: 0
merged_today: [1899]
rejected_today: []
filed_today: [1900, 1901]
closed_today: []
in_flight: []
blocked: []
next_p0: "Decide #1901 path (textbook_grounding corpus_missing): Path B (corpus-aware writer prompt, ~1-2 day ship) is the recommendation. After resolution, re-bakeoff a1/my-morning with claude-tools → green build → copy to curriculum/ → unblock A1 batch build."
agents: [claude, codex]
worktrees_open: 1
ci_notes: |
  PR #1899 merged with all blocking checks green (pytest, ruff, frontend, gitleaks, radon, schema-drift, lesson-schema, plan-validation, prompt-lint, CodeQL ×3). Only Gemini-Dispatch advisory `review / review` failed — non-blocking. Main `bf774d7d48` green.
incidents:
  - "Orchestrator idle for 6.5h while both dispatches sat in finalized state. PR #1899 green at 00:31:52 UTC, sat unmerged. Bakeoff REPORT.md decision-grade at 00:31 UTC, sat unread. User flagged: 'you did not monitor and did nit manage the workflow, just idled all night.' Diagnosis: 'stay online' is not a mechanism. Encoded as MEMORY #M-8: mandatory ScheduleWakeup/Monitor on every dispatch lifecycle; orchestrator MUST be active through finalize → follow-up sweep, not just through dispatch fire."
---

# Brief — 2026-05-13 morning — actual overnight outcomes

> Machine-readable companion to `2026-05-13-morning-actual-outcomes.html`. **Supersedes** `2026-05-12-night-mode-harness-eng-bakeoff-brief.md` which was written from the wrong perspective (orchestrator-passive-during-sleep instead of orchestrator-active).

## TL;DR

- **Both night dispatches finished within 14-17 min of firing** (Codex 836s, Claude 1033s). Both succeeded.
- **PR #1899 merged** (`b9e9f285f3` — cost-telemetry footer, #1865 item #3). Unblocks #1865 items #4 (rate-of-change warnings) + #6 (cost-aware handoff trigger).
- **Writer-selection ADR REVISED** → claude-tools (`bf774d7d48`). Three-bakeoff empirical pattern: codex-tools cannot reliably invoke MCP tools post-prompt-rewrite. `tool_calls_total` still zero. Roles reversed.
- **2 follow-up issues filed:** [#1900](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1900) codex MCP catalog visibility; [#1901](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1901) textbook_grounding corpus_missing.
- **A1 module NOT published.** Claude-tools produced a 1224-word module with vesum-verified passing (159/159 forms, 0 invented `-ся`), but HARD `textbook_grounding=corpus_missing` blocks publication. 2026-04-26 incumbent stays.
- **Failure encoded as MEMORY #M-8:** orchestrator-active through dispatch lifecycle. ScheduleWakeup + Monitor mandatory after any dispatch.

## What shipped (this session)

| Commit | What |
|---|---|
| `31957e0521` (last night) | docs: harness engineering best-practice doc + autonomous-dispatch decision card (pending) + 2 dispatch briefs + CLAUDE.md table edit |
| `f1997da643` (last night) | docs: night-mode handoff (wrong perspective — orchestrator-passive) |
| `b9e9f285f3` | **PR #1899 squash-merged** — cost-telemetry footer for Monitor API responses (#1865 item #3). 17 files, +539/-313. New `scripts/api/telemetry/{footer,response,transcript_tokens}.py` + tests. |
| `bf774d7d48` | ADR REVISED: writer-selection 2026-05-06 — claude-tools as new default. Audit artifacts in `audit/bakeoff-2026-05-12-night/` (REPORT.md + per-writer JSONLs + claude python_qg.json). |

## Bakeoff verdict — claude-tools wins decisively

| Field | claude-tools | codex-tools |
|---|---|---|
| `tool_calls_total` | **4** (verify_words ×2, search_text ×2) | **0** — theatre persists post-rewrite |
| Module produced | yes (1224 words, 10.4 KB) | no — writer phase aborted via `MCP_TOOLS_NEVER_INVOKED` guard |
| `vesum_verified` | passed (159/159 forms, **0 invented -ся**) | n/a |
| python_qg gates | 14 of 18 (1 HARD fail: textbook_grounding) | n/a |
| Writer phase duration | ~6 min | ~2 min (early abort) |
| `writer_tool_theatre` | 2 violations (verify_quote, verify_source_attribution — cited uncalled) | full theatre |

Three bakeoffs in a row (2026-05-06, 2026-05-08, 2026-05-12 night) confirm codex-tools `tool_calls_total=0`. The single-primitive prompt rewrite at `28417cc3cb` — Option A's prompt-iteration premise — did not move the needle. **Empirical pattern wins over hope.**

## Why the A1 module isn't published

Claude-tools build had ONE HARD-severity fail:

```
textbook_grounding: REJECT, HARD, reason=corpus_missing
missing: ["Караман Grade 10, p.176", "Кравцова Grade 4, p.113", "Захарійчук Grade 4, p.162"]
```

The writer cited textbook pages that don't exist in the corpus. Plus a softer `citations_resolve` fail (3 page-label citations in prose don't resolve to references[]) and `correction_terminal` failed after one ADR-008 retry. **Quality is non-negotiable** — module stays unpublished. See #1901 for the three paths forward (Path B recommended: corpus-aware writer prompt that constrains citations to indexed textbooks).

The module *content* is genuinely good (1224 words, 4 Ukrainian dialogues with English glosses, grammar explanation for reflexive `-ся`, proper section structure, all language-quality gates green). Worth reviewing it manually for sanity-check before publishing once #1901 resolves.

## The orchestrator-passivity failure (encoded as MEMORY #M-8)

Both dispatches finalized within 17 min. PR #1899 went green at 00:31:52 UTC. The bakeoff REPORT.md was decision-grade at the same time. **Nothing happened for the next 6.5h** because I treated "fire dispatches + write handoff" as session-end. User flagged: *"you did not monitor and did nit manage the workflow, just idled all night."*

Mechanism failure:
- Background-task notifications fire when the `delegate.py dispatch` launcher exits (~3s), not when the dispatched worker finishes.
- I told myself "I'll be notified" — but I had not set up any monitoring stream.
- "Stay online" is wishful thinking; between turns the orchestrator simply does not exist.

#M-8 (added to MEMORY at 160 lines): after firing ANY dispatch, mandatory ScheduleWakeup at 1200s intervals (or Monitor on JSONL telemetry stream for long-runs). Active monitoring until `total=0` AND outcomes done. Then follow-up sweep (PR merge if green, ADR delta if research, artifact copy if all HARD gates pass, issues filed for blockers).

## Follow-ups filed

| # | Title | Path |
|---|---|---|
| 1900 | codex MCP catalog visibility — bakeoff 3 still shows tool_calls_total=0 post-rewrite | Investigation (rollout JSONL grep for `tools are not exposed in this session`). Blocks any return to codex-tools default. |
| 1901 | textbook_grounding corpus_missing — 3 cited textbook pages absent from corpus | Path B recommended: corpus-aware writer prompt constraining citations to indexed textbooks. Pre-A1-batch-build blocker. |

## Decision Cards in `pending/` (one new from last night, awaiting signoff)

| File | Status | Action needed |
|---|---|---|
| `2026-05-12-autonomous-codex-dispatch-narrow-class.md` | PROPOSED | Pick `go A` (2-week pilot) / `go B` (don't adopt) / `go C` (manual-trigger only) / `wait`. |
| `2026-05-09-decision-graph-view.md` | PROPOSED (unchanged) | channels.html UI toggle. |
| `2026-05-06-multi-ui-channel-participation.md` | PROPOSED (unchanged) | Agent bridge multi-surface identity. |

## Carry-over queue

| # | Item | State |
|---|---|---|
| 1 | **#1901** textbook_grounding corpus_missing | 📋 Pre-A1-batch-build blocker. Path B (~1-2 day ship). |
| 2 | **#1900** codex MCP catalog visibility | 📋 Blocking codex-tools return-to-default. Investigation arc. |
| 3 | **#1865 item #5** MEMORY rule inversion at high context | 📋 Next item in epic order after #3 lands (which just did). |
| 4 | **#1865 item #2** Lazy orient | 📋 Depends on #3 + #5 telemetry signal. |
| 5 | **Autonomous-dispatch decision card** | 📋 Pending Decision Card. |
| 6 | **MEMORY budget** 160/150 (was 151 pre-#M-8) | 📋 Topic file extraction needed soon. |
| 7 | **Worktree cleanup** `.worktrees/dispatch/claude/bakeoff-2026-05-12-night/` | 📋 Branch still exists on remote; user may want to keep the artifacts there for now. |
| 8 | **Backlog of small follow-ups** | 📋 #1604, #1634, #1896. Low priority. |

## Predecessor brief

`docs/session-state/2026-05-12-night-mode-harness-eng-bakeoff-brief.md` — the wrong-perspective handoff from last night. Keep for the trail of evidence; do not delete.

---

*Format spec: `claude_extensions/rules/workflow.md` § "Two-tier handoffs". Companion HTML: `2026-05-13-morning-actual-outcomes.html`.*
