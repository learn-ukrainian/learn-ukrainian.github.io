---
date: 2026-05-11
session: "Two-tier handoffs shipped (epic #1865 item #1) — meta-deliverable session"
status: ok
detail: 2026-05-11-two-tier-handoffs-shipped.html
main_sha: 9860cdb92a
main_green: true
open_prs: 9                                   # all dependabot — none mine
active_dispatches: 0
merged_today: [1876]
rejected_today: []
filed_today: [1875]
closed_today: [1875]
in_flight: []
blocked: []
next_p0: "#1657 (MCP verification-layer Phase 1) FIRST, then #1577 (V7 vertical slice) — user-stated 2026-05-11. Background-dispatch in parallel: #1787 (4 small Codex PRs). Tracked but no action: #1782 (kept active per user)."
agents: [claude]
---

# Brief — 2026-05-11 (two-tier handoffs shipped)

> Machine-readable companion to `2026-05-11-two-tier-handoffs-shipped.html`.
> **First brief produced under its own spec.** Self-referential proof-of-concept: this brief was generated using the format it ships.

## TL;DR

- Single-PR session. PR #1876 merged: two-tier handoff format (brief.md + .html). Closes epic #1865 item #1 of 6.
- Compound benefit: every future cold-start now ramps at ~4KB instead of ~22KB on the handoff tier (−81%).
- 9 dependabot PRs (#1866-#1874) arrived mid-session — not touched, queued for next session.
- **User direction for next session: focus #1657 first, then #1577.**

## What shipped

| PR / Issue | Title | Source |
|---|---|---|
| #1876 | docs(handoff): two-tier handoffs (brief.md + .html) — #1865 item #1 | inline, worktree `claude-1875-two-tier-handoffs` (now cleaned) |
| #1875 | Sub-issue for epic #1865 item #1 (closed by #1876) | inline filing |

## What's now in the codebase

- `claude_extensions/rules/workflow.md` § "Two-tier handoffs": frontmatter schema (required fields listed), body shape, pair-authoring rule, backfill policy.
- `docs/session-state/2026-05-10-evening-codeql-cleanup-and-context-budget-brief.md`: PoC brief paired with yesterday's evening HTML.
- `docs/session-state/current.md`: top row format updated to link both Brief + Detail with explicit labels; cold-start protocol steps 2 + 5 updated.
- `.claude/` + `.agent/` + `.codex/` all deployed.

## Carry-over queue (priority order)

### User-directed for next session — orchestrator attention queue

1. **Epic #1657** — MCP verification-layer improvements (3-phase plan). Phase 1 quick wins: rename `search_etymology` → `search_grinchenko_1907`, add `sovietization_risk` column to СУМ-11 entries, add quote-verification + source-attribution primitives. **Foundation that V7 reviewer/writer work depends on.**
2. **Epic #1577** — Curriculum reboot via 3-agent contract design (A1+A2+B1 vertical slice). V7 linear pipeline replaces V6 convergence loop. 6 phases. Benefits from #1657's primitives.

### Background parallel-dispatch (does not compete with orchestrator focus)

2.5. **Epic #1787** — Build orchestration guardrails. 4 small sub-tasks, each ~30-40 LOC and independent:
  - 1.1 Brief linter (rejects `.venv/bin/python` outside main checkout without `cd <main>` prefix)
  - 1.3 Status-verification CLI helper (`delegate.py status-or-fail TASKID`)
  - 1.4 Anti-menu regex check
  - + handoff-verifier
  Each is ideal Codex dispatch fodder — fire all 4 in parallel from any session, no orchestrator attention required while they run. **Sub-task 1.1 is most directly relevant to this session's deliverable** (briefs are now being generated per session).

### Tracked but no action this session (user-managed)

2.7. **Epic #1782** — Persistent agent listeners. `decision-pending` label. Architecturally depends on Multi-UI ADR ACCEPTED. Per that ADR's "Empirical findings — 2026-05-09" section, **Codex Desktop Automations supersedes Tier-3 daemon** for the autonomous-orchestrator strand; Tier-2 warm-cache already shipped. Premise partially obsolete. **User explicitly chose to keep this active and triage themselves later** — orchestrator should NOT close or rescope this issue.

### From yesterday's brief (still open)

3. Cleanup plan #1863 Phase 1 — build `scripts/audit/find_dead_code.py`.
4. PR #1864 minor scope: Codex added `.json` to `_ALLOWED_EXT` — user decision: keep or revert.
5. PR-C router job for `gemini-dispatch.yml` — re-evaluate now that 4 baseline PRs observed.
6. Pytest matrix split — need more warm-cache data.
7. V7 writer bakeoff — stale 9+ shifts, user-runs.
8. v5/v6 file deletion decision (currently OBSOLETE-banner'd per #1853).
9. User-action: `/graphify docs/` rebuild via Gemini CLI.

### New today

10. **9 dependabot PRs** (#1866-#1874) arrived mid-session — all mechanical bumps in `starlight/` + pip packages. Need triage: which ones to merge after CI verifies, which need careful review (e.g. astro 6.2.1→6.3.1 minor, mcp-memory-service 10.29.1→10.54.0 multi-minor jump). Recommended: batch-review on the cold-start next session, merge greens, defer non-trivial.

### Epic #1865 remaining items (this session's epic, not done)

11. Item #3 — In-tool cost telemetry (hook-injected footer with ctx/turn/tier).
12. Item #5 — MEMORY rule inversion at high context (≥150K main switches to subagent-prefer).
13. Item #2 — Lazy orient (touches /api/orient contract).
14. Item #4 — Rate-tracking warnings (depends on #3).
15. Item #6 — Cost-aware handoff trigger heuristic (depends on #3+#4).

## Decisions encoded

- Two-tier handoff format is now mandatory for new sessions (per `workflow.md` § "Two-tier handoffs"). Pair must ship in a single orchestrator turn. Older HTML-only rows in `current.md` stay as-is — cold-start fallback handles them.
- Frontmatter schema is fixed (required fields enumerated); optional fields allowed but the required block must be parseable.
- `next_p0` for the next session reflects user statement: #1657 → #1577 ordering.

## Pending decisions (still PROPOSED — not blocking next P0)

- `docs/decisions/pending/2026-05-09-decision-graph-view.md` — channels.html UI toggle. Out of scope for #1657/#1577.
- `docs/decisions/pending/2026-05-06-multi-ui-channel-participation.md` — agent bridge multi-surface identity. Out of scope.

## Cold-start orientation for next agent

If you are the next session:

1. **Read this brief, not the .html companion.** That IS the protocol you should follow now.
2. **First priority: #1657.** Read the issue body. Phase 1 quick wins are listed there. Likely small-PR sized — good warm-up.
3. **After #1657 lands (or substantial progress): #1577.** Larger epic. Re-read its body fully + last 2-3 sessions of V7-related session-state to absorb the V6→V7 reboot context.
4. Dependabot wave (#1866-#1874): use the batch-review approach. Don't merge blindly. Don't ignore — they go stale fast.
5. **Repo state:** clean. main at `9860cdb92a`. 0 active dispatches. 0 open PRs of mine. Phantom-edits stash at `stash@{0}` (preserved, do not touch — see prior handoffs for context).
6. **Self-test of the new format:** measure your own cold-start KB after reading this brief. Should be ~61KB total (manifest + rules + session + orient + inbox + brief), down from ~79KB if you had read the .html instead. Report the number in your first reply so we can validate the savings empirically across sessions.

---

*Format spec: `claude_extensions/rules/workflow.md` § "Two-tier handoffs". Epic: #1865. Sub-issue (this work): #1875. PR: #1876.*
