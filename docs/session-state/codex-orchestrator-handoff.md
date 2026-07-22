# Current - Codex / Grok Orchestrator Handoff (2026-07-22)

Latest-Brief: docs/session-state/2026-07-22-fleet-comms-cutover-handoff.md

## Role

Orchestrator seat (Codex / Grok / Claude-infra as assigned): drive the product and
infra queue, keep main clean, open PRs from worktrees only, require cross-family
`review-pr` before merge, arm auto-merge after the gate, clean worktrees after merge.
Do not babysit idle green PRs; do not leave draft limbo.

Do not use `docs/session-state/current.md` as scratch space. Durable state lives in
the Latest-Brief above and this file. Thread rollover packets live under
`.agent/<agent>-thread-handoff.md` (machine-local).

---

## NEXT SESSION — START HERE (binding)

**Do not ask the operator what to work on.** Read the Latest-Brief and **execute**.

### Primary — Fleet-comms #5512 operator cutovers (item 2)

1. **Message-plane dual_write cutover after parity**
2. **Retention Gate 5** — daily `retention_engine.py plan` dry-run (7d observation before apply)
3. **Cold-start smoke** — Claude + Grok + Codex + AGY

### Parallel — Isolation fan-out (does not block cutovers)

- #5555 AGY → #5614 design → #5615 wire → #5616 enable  
- #5556 Kimi → #5617 design → #5618 wire → #5619 enable  
- #5557 Grok → #5620 design → #5621 wire → #5622 enable  

**Hard rule:** do **not** flip `formal_review_eligible` without wire green + cross-family CF.

Full commands and acceptance: **Latest-Brief** above.

---

## Current State (session close 2026-07-22)

Fleet-comms code/pins largely landed on main (`#5602`, `#5611`, `#5613`, PR-M/L).  
**Operator cutovers and multi-family isolation enablement remain.**

### Shipped (recent)

- Practical formal CF pins + Laguna S 2.1 / XS 2.1 / M.1 + AGY orchestrator: **#5602**
- Orchestrator escalate Sol / Fable / Pro: **#5611**
- Sealed CF line_mismatch relocate: **#5613**
- Metrics / retention engine (apply default OFF): **#5584**, **#5585**
- Isolation fan-out tickets: **#5614–#5622** (parents #5555–#5557 reopened)

### Explicit non-goals for next cold-start

- Do not re-litigate Sol phases 0–5 (#5484 closed)
- Do not invent a competing fleet-comms architecture
- Do not enable retention **apply** until ≥7 days of dry-run plans are clean
- Do not flip formal_review_eligible on agy/kimi/grok without isolation wire + CF

## Operating Rules

- Implementation only under `.worktrees/dispatch/<agent>/<task>/`
- Every commit: `X-Agent` trailer
- Use `.venv/bin/python`, never `sys.executable`
- Never touch `.python-version`, `.yamllint`, `.markdownlint.json`
- No status/audit/review artifact dumps in code PRs
- CF review gate = independent cross-family `review-pr` (discuss ≠ review)

## Startup Checks

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin main --prune
git status --short --branch
git pull --ff-only origin main
gh pr list --state open --limit 20
curl -sS --max-time 2 "http://127.0.0.1:8765/api/orient?lean=true" || true
# BINDING next targets:
# docs/session-state/2026-07-22-fleet-comms-cutover-handoff.md
.venv/bin/python -m scripts.fleet_comms plane-status
.venv/bin/python scripts/hygiene/retention_engine.py plan
```

## Next Focus (priority order)

1. **#5512 cutovers** (dual_write · retention Gate 5 · cold-start smoke) — THIS SESSION
2. Isolation design spikes in parallel if capacity: #5614 / #5617 / #5620
3. Only after cutovers green: other #4707 backlog / product streams
