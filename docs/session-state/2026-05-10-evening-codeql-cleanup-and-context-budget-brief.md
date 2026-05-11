---
date: 2026-05-10
session: "Evening — CodeQL clearance + cleanup plan + context-budget epic"
status: ok
detail: 2026-05-10-evening-codeql-cleanup-and-context-budget.html
main_sha: 99d3844e9
main_green: true
open_prs: 0
active_dispatches: 0
merged_today: [1861, 1863, 1864]
rejected_today: [1862]
filed_today: [1860, 1863, 1865]
closed_today: [1762, 1860]
in_flight: []
blocked: []
next_p0: "Implement #1865 item #1 (two-tier handoffs) — this brief is its proof-of-concept"
agents: [claude, codex, gemini]
---

# Brief — 2026-05-10 evening

> Machine-readable companion to `2026-05-10-evening-codeql-cleanup-and-context-budget.html`.
> Cold-start agents read THIS file. Humans read the `.html` for narrative. Generated under epic #1865 item #1.

## TL;DR

- 3 PRs merged, 1 PR rejected + closed (Gemini cross-file refactor disaster), 18→0 CodeQL alerts cleared, 2 epics filed, main green for first time since `f4bab7125f` (~8h gap).
- Working tree clean, 0 open PRs, 0 active dispatches.
- **P0 next session:** implement epic #1865 item #1 — two-tier handoffs (compound benefit for every future cold-start).

## What shipped

| PR / Issue | Title | Source |
|---|---|---|
| #1861 | codeql suppressions + playgrounds→dashboards + empty-root test skip | inline (closes #1860) |
| #1863 | 2026-Q2 cleanup plan doc + epic anchor | inline strategic doc |
| #1864 | complete playgrounds→dashboards rename across Python + tests | Codex dispatch (replaces #1862) |
| #1865 | EPIC: context-budget optimization | inline (filed end-of-session) |

## What rejected

- **PR #1862** (Gemini centralize-config + dashboards rename): CLOSED, not merged. 10-finding adversarial review caught hallucinated `IMMERSION_POLICIES` + invented track personas in `scripts/config.py`, curriculum vandalism (stripped POS tags + Ukrainian-flag color from A1 module), broken `delegate.py` (path-string → Path object semantics), 60KB stray `.bak` committed, 151 silently-deleted test lines. Re-dispatched to Codex → #1864 (6 files, +36/-35, zero violations). **Lesson encoded:** #M0 "Gemini NOT for cross-file architectural refactor" is a HARD guardrail.

## Carry-over queue (priority order)

1. **#1865 item #1 — two-tier handoffs.** This brief is the PoC. Remaining: update current.md index, update workflow.md cold-start, deploy.
2. Cleanup plan #1863 Phase 1 — build `scripts/audit/find_dead_code.py`.
3. PR #1864 minor scope: Codex added `.json` to `_ALLOWED_EXT` — user decision: keep or revert.
4. PR-C router job for `gemini-dispatch.yml` — re-evaluate now that 4 baseline PRs observed.
5. Pytest matrix split — need more warm-cache data (4:21 vs 4:33 = ~12s, modest).
6. V7 writer bakeoff — stale 8+ shifts, user-runs.
7. v5/v6 file deletion decision (now OBSOLETE-banner'd per #1853).
8. User-action: `/graphify docs/` rebuild via Gemini CLI.

## Decisions encoded

- Gemini is NOT for cross-file architectural refactor / security/concurrency / mass mechanical (empirically verified this session via #1862 outcome).
- Cleanup approach: tooling-first, one-category-per-PR, adversarial-review-mandatory, archive-before-delete (`docs/cleanup-plan-2026-q2.md`).
- Context-budget optimization order: 1→3→5→2→4→6 (user-confirmed).
- Subscription quota burn is the real economic concern, not API $ — informs all context-discipline rules.
- Don't admin-merge pytest failures even for "pre-existing" regressions (#M-0.5 held throughout session).

## Pending decisions (still PROPOSED — not blocking this P0)

- `docs/decisions/pending/2026-05-09-decision-graph-view.md` — channels.html UI toggle.
- `docs/decisions/pending/2026-05-06-multi-ui-channel-participation.md` — agent bridge multi-surface identity.

## Cold-start orientation for next agent

If you are picking up the next session:

1. Implement #1865 item #1 first. Spec is in epic body + this brief is the PoC.
2. Deliverables remaining: spec the brief schema inline in `claude_extensions/rules/workflow.md`, update `current.md` "Latest handoff" table to link both files per row, deploy rules.
3. Read the `.html` companion only if you need narrative context for one of the threads above.

---

*Format spec: see `claude_extensions/rules/workflow.md` § "Two-tier handoffs". Filed under epic #1865, sub-issue #1875.*
