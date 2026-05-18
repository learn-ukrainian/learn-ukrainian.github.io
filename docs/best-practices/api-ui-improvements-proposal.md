# API + UI improvements — proposal for dual agent + human usability

> **Status:** v1 proposal — 2026-05-18 by orchestrator (Claude). Triggered by user 2026-05-18: *"api ui needs improvements and make sure it is usable for both agents and humans."*
> **Scope:** Monitor API on localhost:8765 + `/artifacts/` page + new endpoints surfacing matrix, bakeoffs, dispatch state, tech-debt board.
> **Companion docs:** `docs/best-practices/agent-activity-matrix.md`, `audit/INDEX-bakeoff-evidence.md`, EPIC #1814 (HTML artifact serving + nav UI).

---

## Why this matters

The Monitor API at `localhost:8765` works well for agents (JSON at `/api/state/*`, `/api/orient`, `/api/rules`, `/api/delegate/active`). It works poorly for humans:

- The only HTML surface is `/artifacts/` (kubedojo-layout, kubedojo-adoption PR landed 2026-05-18).
- There is no human-facing view of: active dispatches, recent bakeoff results, the agent activity matrix, the PR queue, the tech-debt board, build queue health.
- There is no agent-facing endpoint for the activity matrix in JSON form (the file at `docs/best-practices/agent-activity-matrix.md` is the source of truth but agents would have to file-read it, not query it).

The principle (per MEMORY #M-2): **format depends on the flow.** Agents read JSON; humans read HTML; the *same data* should be available in both projections.

---

## What's already in place (don't duplicate)

| Surface | Path | Format | Audience | Status |
|---|---|---|---|---|
| Orient | `/api/orient` | JSON | Agents | Live — cached, per-section TTL |
| Rules | `/api/rules?format=markdown` | Markdown | Agents | Live — ETag-cached |
| Session current | `/api/session/current?format=markdown` | Markdown | Agents | Live |
| Track health | `/api/state/track-health/{level}` | JSON | Agents | Live |
| Failing modules | `/api/state/failing?track=X` | JSON | Agents | Live |
| Build status | `/api/state/build-status/{level}` | JSON | Agents | Live |
| Routing budget | `/api/state/routing-budget` | JSON | Agents | Live — per-agent spend + recommendation |
| Delegate active | `/api/delegate/active` | JSON | Agents | Live |
| Inbox (agent comms) | `/api/comms/inbox?agent=X` | JSON | Agents | Live |
| Manifest | `/api/state/manifest` | JSON | Agents | Live — hashes + URLs of warm-cache reads |
| Artifacts page | `/artifacts/` | HTML | Humans | Live — kubedojo-style (PR #2120-ish era) |
| Healthz | `/healthz` | JSON | Both | Live — TTL cache (PR #2121) |

The **gap** is that humans have to read JSON or terminal commands to know:
1. What dispatches are currently running and what they're doing.
2. Which agents are best at which tasks (matrix).
3. What bakeoffs we've run and what they showed.
4. What's blocking m20 / m1-m7 / etc.
5. What tech debts cascade across the curriculum vs what's bounded.

---

## Proposed deliverables

### Deliverable 1 — `/api/activity-matrix` endpoint

**Both formats from one source.** Backed by `docs/best-practices/agent-activity-matrix.md` (parsed YAML-style headers + tables) + `audit/INDEX-bakeoff-evidence.md` (joined on `last_verified` dates).

| Path | Format | Use |
|---|---|---|
| `/api/activity-matrix?format=json` | JSON | Agents: routing decisions, fallback selection. Schema: `{task_types: [{id, name, primary, runners_up: [{agent, score, last_verified, evidence_path}], known_weaknesses, known_strengths}]}` |
| `/api/activity-matrix?format=html` | HTML | Humans: at-a-glance cell view + drill-down into evidence index per cell |
| `/api/activity-matrix/agent/{agent}` | JSON | Per-agent rollup: every cell where this agent is primary/runner-up/absent + per-cell eval scores |
| `/api/activity-matrix/cell/{cell_id}` | JSON | Per-cell rollup: bakeoff history for this task type + all agents' scores + last_verified |

**Implementation sketch:**
- New file `scripts/api/activity_matrix.py` — parser for the markdown matrix + the bakeoff index + the routing-budget endpoint output.
- New tests `tests/api/test_activity_matrix.py` — parse each table, verify round-trip JSON shape, verify all cells have `last_verified` date, verify cells reference valid evidence paths.

**Estimated effort:** 1 Codex dispatch (~45-60 min).

---

### Deliverable 2 — `/dashboard` unified HTML view

One page, four panels, refresh-on-load. Kubedojo aesthetic (already in repo per `/artifacts/`).

```
+----------------------------------------+
| DASHBOARD — Ukrainian curriculum       |
| 2026-05-18 09:15 CEST · main 4aeaa0a611 |
+--------+--------+--------+-------------+
| ACTIVE | RECENT | OPEN   | MATRIX      |
| DISPS  | PRs    | ISSUES | QUICK VIEW  |
| · 2128 | #2130  | #2128  | writing:    |
|        | #2129  | #2127  |  Claude     |
|        |        | #2126  | reviewing:  |
|        |        |   ...  |  Codex      |
+--------+--------+--------+-------------+
| BUILD QUEUE          | TECH DEBT       |
| a1: 0/55 built       | HIGH cascade: 3 |
| a2: 0/69 built       | MED cascade: 8  |
| folk: 1/27           | LOW cascade: 11 |
+----------------------+-----------------+
| BAKEOFF EVIDENCE                       |
| 2026-05-12 night: claude-tools wins    |
| 2026-05-15 russianism: opus-4-7 wins   |
| 2026-05-17 h2: gemini-3.1-pro wins     |
+----------------------------------------+
```

**Data sources:** all existing endpoints + the new `/api/activity-matrix` + a thin index over `audit/INDEX-bakeoff-evidence.md`. No new state — pure projection.

**Estimated effort:** 1 Codex dispatch (~60-90 min: HTML + minimal JS + tests on the data joining).

---

### Deliverable 3 — Per-agent activity page

`/api/agent/{agent}` → JSON + HTML projection.

Shows for one agent (claude / codex / gemini / deepseek / grok):
- Their primary cells (where they own the routing)
- Their runner-up cells (where they're documented fallback)
- Recent dispatches (last 24 hours / 7 days): task_id, duration, status, PR if any
- Cost burn (from `/api/state/routing-budget`)
- Open promote-protocol challenges they have outstanding

**Use case (agent-facing):** when orchestrator routes work, it can check the per-agent page for current load + known weaknesses before firing.

**Use case (human-facing):** when human reviewer is auditing the curriculum, they can see "what did Gemini do last week" at a glance.

**Estimated effort:** 0.5 Codex dispatch (~30 min, extends `/api/activity-matrix` and `/api/delegate/active` joins).

---

### Deliverable 4 — Bakeoff search + browser

`/api/bakeoff` → list/search.
`/api/bakeoff/{name}` → one bakeoff record.

Surfaces from `audit/INDEX-bakeoff-evidence.md`:
- All bakeoff dirs catalogued
- Per-bakeoff metadata: date, agents tested, task type, winner, score metric, decision-card delta
- Drill-down: open `REPORT.md` or per-agent `*.jsonl` inline (text rendering, not raw JSON dump)

**Use case (agent):** when promote-protocol challenge fires, agent can read prior bakeoff data to build a calibrated proposal.

**Use case (human):** when auditing routing decisions, human can see the evidence trail without grep.

**Estimated effort:** 0.5 Codex dispatch (~30 min).

---

### Deliverable 5 — Promote-protocol response inspection

Fix for issue #2131 (filed this session): the bridge auto-ack appears to delete messages, so promote-protocol responses are non-retrievable.

**Two fixes:**

1. **Bridge layer fix** (out of API/UI scope — but blocks promote-protocol). Issue #2131 should land before promote-protocol v2.
2. **API surface fix** (in this proposal's scope):
   - `/api/promote-protocol/challenges?status=open` — list outstanding challenges per agent
   - `/api/promote-protocol/responses?challenge_id=X` — read response after agent replies
   - `/api/promote-protocol/aggregate` — ACCEPT/DECLINE rollup across all open challenges

**Estimated effort:** 0.5 Codex dispatch (~30 min) — DEPENDS on issue #2131 landing first.

---

### Deliverable 6 — Tech-debt board

`/api/tech-debt` → JSON + HTML.

Joins:
- `docs/session-state/2026-05-18-cascade-risk-orchestration-handoff.md` cascade categorisation
- `gh issue list --state open --json` for live status
- `docs/best-practices/agent-activity-matrix.md` for which agent could resolve each item

Returns:
```json
{
  "high_cascade": [{"issue": 2127, "title": "...", "blocks_m20": true, "recommended_agent": "codex"}],
  "medium_cascade": [...],
  "low_cascade": [...],
  "epics": [...]
}
```

**Use case (orchestrator-self):** when I (Claude) wake from a handoff, this is my P0 query: what's the next HIGH-cascade fix?

**Use case (human):** what's blocking m20? what's the tech-debt budget for this week?

**Estimated effort:** 1 Codex dispatch (~45 min).

---

## Implementation sequencing

Phase 1 — foundation (2-3 days):
1. Deliverable 1 — `/api/activity-matrix` endpoint (json+html parser over the matrix file).
2. Deliverable 4 — Bakeoff search (depends on D1 evidence-index parsing).

Phase 2 — dashboards (2-3 days):
3. Deliverable 2 — `/dashboard` HTML.
4. Deliverable 3 — Per-agent page.

Phase 3 — orchestration loops (1-2 days):
5. Deliverable 6 — Tech-debt board.

Phase 4 — promote-protocol (blocked):
6. Deliverable 5 — Promote-protocol API (blocked on #2131 bridge fix).

All phases plug into EPIC #1814 (HTML artifact serving + nav UI). The `/dashboard` is the navigation hub.

---

## Design principles

1. **Same data, two formats.** Every new endpoint serves both `?format=json` (agents) AND `?format=html` (humans). No format-by-route splits.
2. **No new state — only projections.** New endpoints read from existing files (matrix.md, INDEX-bakeoff-evidence.md, /api/state/*, gh issue list). No new DB tables, no new write paths.
3. **Cache-friendly.** Existing endpoints use TTL caching (per-section). New endpoints follow same pattern.
4. **Kubedojo aesthetic** for HTML — already adopted, consistent.
5. **Agents read first, humans read second.** When designing a new endpoint, write the JSON shape FIRST (because agent routing depends on it), then derive the HTML view.
6. **No interactive forms in v1.** Read-only views only. Bakeoff firings, promote-protocol acceptances, etc. happen via CLI (`delegate.py`, `ab discuss`) — the dashboard *shows* state but doesn't *change* it.

---

## Out of scope (file as follow-ups if needed)

- **Auth.** API is localhost-only; no auth proposed in v1.
- **Real-time updates** (SSE / WebSockets). Page-load refresh is sufficient for v1; agents poll on schedule.
- **Mobile UI.** Desktop-first.
- **Multi-user / multi-orchestrator state** (this is a single-user / single-orchestrator project).
- **Replacing the Monitor tool** (it's the right tool for stdout-event-stream use cases; the dashboard surfaces *state*, not streams).

---

## Risk callouts

1. **The matrix v1 markdown isn't yet machine-parseable.** Deliverable 1 needs either (a) re-author the markdown into a parseable YAML+narrative hybrid OR (b) write a custom parser. Pick (a) before Deliverable 1 starts — re-authoring the matrix file with a deterministic header convention is cheaper than a brittle parser.
2. **Bakeoff REPORTs have inconsistent shape.** Deliverable 4 needs at least minimal normalization — INDEX-bakeoff-evidence.md (just landed) is the starting point.
3. **#1814 EPIC scope is large.** Don't try to ship everything in one PR — Deliverable 1 alone is a complete shippable unit.

---

## Provenance

- v1: 2026-05-18 by orchestrator (Claude inline) per user direction "api ui needs improvements and make sure it is usable for both agents and humans."
- Companions: `docs/best-practices/agent-activity-matrix.md`, `audit/INDEX-bakeoff-evidence.md`.
- EPIC: #1814.
