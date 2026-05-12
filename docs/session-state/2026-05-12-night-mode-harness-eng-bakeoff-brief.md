---
date: 2026-05-12
session: "Night mode — harness engineering doc + bakeoff dispatched + cost-telemetry dispatched"
status: dispatches_in_flight
detail: 2026-05-12-night-mode-harness-eng-bakeoff.html
main_sha: 31957e0521
main_green: true
open_prs: 0
active_dispatches: 2
merged_today: []
rejected_today: []
filed_today: []
closed_today: []
in_flight:
  - "codex/1865-3-cost-telemetry — Codex on EPIC #1865 item #3 (in-tool cost telemetry footer). Hard timeout 5400s, silence 900s, effort high. Expected ETA ~30-90 min. Output: PR opened, no auto-merge."
  - "claude/bakeoff-2026-05-12-night — Claude headless /goal runner doing bakeoff claude-tools vs codex-tools on a1/my-morning. Hard timeout 7200s, silence 1800s, effort xhigh. Includes 2 V7 builds. Output: branch pushed (no PR), audit/bakeoff-2026-05-12-night/REPORT.md with verdict."
blocked: []
next_p0: "On wake: read REPORT.md from bakeoff dispatch + decide ratify/revise writer-selection ADR. Review Codex PR for #1865 item #3. Then decide on autonomous-dispatch decision card (pending/)."
agents: [claude, codex]
worktrees_open: 2
ci_notes: |
  Main pushed `31957e0521` (docs-only — 5 files; 1 CLAUDE.md edit + 4 new docs). Pytest gate bypassed per user account permission as usual; nothing in #M-7's trigger list was touched (no claude_extensions/rules/, scripts/, tests/, curriculum/, .dagger/, no .py edits, no hardcoded-fixture mirror).
incidents: []
---

# Brief — 2026-05-12 night — night-mode entry + harness engineering doc + 2 dispatches

> Machine-readable companion to `2026-05-12-night-mode-harness-eng-bakeoff.html`.

## TL;DR

- **User shared OpenAI's "harness engineering" + Symphony posts** as the next interesting evolution. I read all three sources end-to-end (the two OpenAI blog posts via chrome plugin after WebFetch hit 403; the openai/symphony repo via `gh api`).
- **Synthesized into `docs/best-practices/harness-engineering.md`** (vocabulary doc, ai→ai MD) mapping their patterns to ours + the explicit caveat that the model does NOT port to module content production (we are not in the ship-and-iterate regime for content).
- **Filed Decision Card** `docs/decisions/pending/2026-05-12-autonomous-codex-dispatch-narrow-class.md` proposing a narrow Symphony-style autonomous-dispatch lane for lint/deps/doc-gardening/MEMORY/autopsy work only. 3 options + Option A recommended. Awaiting user signoff.
- **User authorized auto night mode + bakeoff + A1 module overnight.** Explicit override on the *"agents do not invoke v7_build.py themselves"* CLAUDE.md rule for this session ("you are allowed to run build when in auto mode").
- **2 dispatches in flight** (see `in_flight` above). One ships a PR; the other ships a research report + branch.
- **The bakeoff is the resolution gate for #1807** (writer-prompt tool-theatre) — the prompt rewrite `28417cc3cb` (2026-05-11) is now empirically tested. Verdict ratifies or revises `docs/decisions/2026-05-06-writer-selection-codex-gpt55.md`.

## What shipped (direct to main, this session)

| Ref | Title | Source |
|---|---|---|
| `31957e0521` | `docs(night): harness engineering doc + autonomous-dispatch decision card + 2 dispatch briefs` | Inline. 5 files: `docs/best-practices/harness-engineering.md`, `docs/decisions/pending/2026-05-12-autonomous-codex-dispatch-narrow-class.md`, `docs/dispatch-briefs/2026-05-12-1865-3-cost-telemetry.md`, `docs/dispatch-briefs/2026-05-12-bakeoff-claude-vs-codex-night.md`, CLAUDE.md best-practices table entry. |

## What's in flight (awaiting wake-up review)

| Task ID | Agent | What | How to verify on wake |
|---|---|---|---|
| `codex/1865-3-cost-telemetry` | Codex (gpt-5.5, high) | Adds in-tool cost telemetry footer to Monitor API responses (`[ctx: 187K (+22K this turn), tier: base, 13K to premium, turn: 47]`). Unblocks #1865 items #4 (rate-of-change warnings) + #6 (cost-aware handoff trigger). Brief: `docs/dispatch-briefs/2026-05-12-1865-3-cost-telemetry.md`. | `gh pr list --search "1865-3-cost-telemetry"` should show one open PR. CI green required before merge. Review the footer renderer logic + transcript-JSONL parser refactor for correctness. |
| `claude/bakeoff-2026-05-12-night` | Claude-headless /goal (opus-4-7, xhigh) | Runs `v7_build.py a1 my-morning --writer claude-tools` and `--writer codex-tools`, scores both against acceptance criteria from `docs/decisions/2026-05-06-writer-selection-codex-gpt55.md`, writes REPORT.md, declares winner. Brief: `docs/dispatch-briefs/2026-05-12-bakeoff-claude-vs-codex-night.md`. | `cat audit/bakeoff-2026-05-12-night/REPORT.md` on wake. Winner declared per acceptance criteria. If winner=codex-tools → existing ADR RATIFIED. If winner=claude-tools → ADR REVISED, follow-up issue for prompt iteration. If FAIL (both `tool_calls_total=0`) → escalate to Stage 2 (verify→write phase split). |

## Decision Cards in `docs/decisions/pending/` (read on wake)

| File | Status | Scope |
|---|---|---|
| `2026-05-12-autonomous-codex-dispatch-narrow-class.md` | PROPOSED | New decision: should we add Symphony-style autonomous dispatch for narrow class (lint/deps/doc-gardening/MEMORY/autopsy)? 3 options + Option A recommended (2-week hard-capped pilot). |
| `2026-05-09-decision-graph-view.md` | PROPOSED (unchanged from prior) | channels.html UI toggle. |
| `2026-05-06-multi-ui-channel-participation.md` | PROPOSED (unchanged) | Agent bridge multi-surface identity. |

## Pre-existing decisions affected by bakeoff outcome

- **`docs/decisions/2026-05-06-writer-selection-codex-gpt55.md`** — currently ACCEPTED for Codex/gpt-5.5/codex-tools. The 2026-05-12 night bakeoff is the empirical retest after the 2026-05-11 prompt rewrite. Possible outcomes:
  - **RATIFIED** (codex-tools wins or ties): no action; ADR stays ACCEPTED; continue toward A1 batch build using codex-tools.
  - **REVISED** (claude-tools wins on `tool_calls_total > 0` + cleaner gates): ADR flips to claude-tools as V7 writer; file follow-up issue for codex-tools next-stage prompt iteration (Stage 2: verify→write phase split per Codex's 2026-05-08 introspective).
  - **FAIL** (both `tool_calls_total=0`): escalate to Stage 2 immediately; bakeoff doesn't pick a winner, prompt architecture does.

## How to act on wake

1. **Read `audit/bakeoff-2026-05-12-night/REPORT.md`** (created by the /goal runner; check `audit/` dir on wake; if missing, the /goal may have aborted — check dispatch logs).
2. **Decide writer-selection.** Either copy the winning module to `curriculum/l2-uk-en/a1/my-morning/` (replacing the May-2 artifacts) and commit, OR escalate per FAIL path.
3. **Review the Codex PR for #1865 item #3.** Should be a small (~200-400 LOC) telemetry-footer PR. CI must be green before merge. Then unblocks items #4 + #6 of epic #1865.
4. **Decide on autonomous-dispatch decision card.** Read `docs/decisions/pending/2026-05-12-autonomous-codex-dispatch-narrow-class.md`. Pick Option A/B/C/wait.

## Carry-over queue

| # | Item | State |
|---|---|---|
| 1 | **#1865 item #5** — MEMORY rule inversion at high context. | 📋 Next item in epic order after #3 lands. |
| 2 | **#1865 item #2** — Lazy orient (bigger /api/orient refactor). | 📋 Depends on #3 + #5 for telemetry signal. |
| 3 | **Autonomous-dispatch decision** | 📋 Pending Decision Card. |
| 4 | **Dagger Node.js in runner image** | 📋 Deferred per prior brief. |
| 5 | **MEMORY budget tension (151/150)** | 📋 Topic files in `memory/` could absorb more detail. Not urgent. |
| 6 | **Backlog of small follow-ups** | 📋 #1896, #1604, #1634. Low priority. |
| 7 | **#1807 next-stage prompt iteration** | 📋 Triggered only on bakeoff FAIL path. |

## Predecessor brief

`docs/session-state/2026-05-12-orchestrator-shift-and-queue-drain-brief.md` — drained the late-night-2026-05-12 carry-over queue + encoded MEMORY #M-6 (orchestrator-drive) + #M-6a (/goal status lines) + #M-7 (pytest before push).

---

*Format spec: `claude_extensions/rules/workflow.md` § "Two-tier handoffs". Companion HTML: `2026-05-12-night-mode-harness-eng-bakeoff.html`.*
