---
session: "Fleet-comms #5512 — operator cutovers are NEXT SESSION primary targets (binding)"
date: 2026-07-22
epic: 5512
stream: 4707
status: open
priority: P0-next-cold-start
---

# 2026-07-22 — Fleet-comms cutover handoff (binding for next cold-start)

**Do not wait for the operator to restate targets.** On cold-start, orient then **execute** the queue below.

## NEXT SESSION — PRIMARY TARGETS (binding)

**Epic:** [#5512](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/5512) Fleet Communications System v1  
**Stream:** [#4707](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/4707) infra-harness

### Item 2 — Operator cutovers (DO THESE FIRST)

1. **Message-plane dual_write cutover after parity**
   - Check: `.venv/bin/python -m scripts.fleet_comms plane-status`
   - Expect: was `mode: off` / dual_write not default — cutover only after parity receipt
   - Streams: `session_streams dual-write-status` / `inventory --register` (17/17 ok, drift=0 previously)
   - **No silent flip** — record parity evidence, then operator/advisor-approved enable

2. **Retention Gate 5 — daily dry-run × ≥7 days before scheduled apply**
   - Command: `.venv/bin/python scripts/hygiene/retention_engine.py plan` (dry-run only)
   - **7d = observation window**, not data TTL (`stale_hours` default 72; apply still OFF)
   - Confirm plans stable; no active/leased work in `would_reap`
   - Only then enable scheduled **apply** (never arm example plist blindly)
   - API: `curl -s http://localhost:8765/api/ops/v1/retention/latest`

3. **Cold-start smoke — Claude + Grok + Codex + AGY**
   - Prove launchers/streams without manual folklore
   - AGY: `./start-gemini.sh --epic harness` (default `gemini-3.6-flash-high`; Pro escalate)
   - Claude infra: `./start-claude.sh --epic harness` / `--agent infra-orchestrator`
   - Grok / Codex: project start scripts + stream lease for epic 4707

### Parallel (do not block cutovers)

**Isolation fan-out** under #5555–#5557 — design spikes first, then wire, then enable:

| Family | Parent | Design | Wire | Enable |
| --- | --- | --- | --- | --- |
| AGY | #5555 | #5614 | #5615 | #5616 |
| Kimi | #5556 | #5617 | #5618 | #5619 |
| Grok | #5557 | #5620 | #5621 | #5622 |

**Hard rule:** do **not** flip `formal_review_eligible` without wire green + cross-family CF on enablement PR.  
Until flip: formal CF = `review-pr` codex|claude|glm (Terra/Sonnet5/GLM @ high; Sol/Fable escalate for hard only).

## Already on main (do not re-litigate)

| Ship | PR / note |
| --- | --- |
| Practical formal CF pins + Laguna S/XS/M.1 + AGY orchestrator seat | #5602 |
| Escalate: Sol / Fable / Pro parallel to AGY Pro | #5611 |
| Sealed CF line_mismatch relocate | #5613 |
| Metrics / backlog / dead-letters / github-metrics | #5584 PR-M |
| Retention plan/apply engine (apply default OFF) | #5585 PR-L |
| Sol phases 0–5 thin review program | #5484 closed |

## Orient at cold-start

```bash
cd ~/projects/learn-ukrainian
git fetch origin main --prune && git status -sb
git pull --ff-only origin main
curl -sS --max-time 2 "http://127.0.0.1:8765/api/orient?lean=true" || true
.venv/bin/python -m scripts.fleet_comms plane-status
.venv/bin/python -m agents_extensions.shared.session_streams dual-write-status
.venv/bin/python scripts/hygiene/retention_engine.py plan
gh issue view 5512
# This brief is authoritative for next actions:
# docs/session-state/2026-07-22-fleet-comms-cutover-handoff.md
```

## Operating rules (unchanged)

- Implementation only under `.worktrees/dispatch/<agent>/<task>/`
- `X-Agent` trailer on every commit
- Cross-family `review-pr` before merge; arm auto-merge after gate
- No architecture cutover without present-tense operator/advisor approval when required by Gate C/A

## Out of scope for this handoff queue

- Atlas/practice product epics unless cutovers are green and capacity remains
- Isolation enablement before design+wire complete
- Inventing a competing fleet-comms design

## Done when (cutover slice)

- [ ] Plane dual_write: parity receipt + approved cutover state (or explicit deferred with owner)
- [ ] Retention: ≥1 plan run recorded this session + 7d plan log started/continued; apply still OFF until day 7
- [ ] Cold-start smoke: evidence comment on #5512 for Claude + Grok + Codex + AGY
- [ ] Isolation: at least design spikes moving or dispatched (#5614/#5617/#5620) without blocking cutovers
