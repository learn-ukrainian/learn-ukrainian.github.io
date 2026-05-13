# Dispatch — Routing-budget observability: `/api/state/routing-budget` + pre-dispatch check

**Issue:** to be filed as part of this dispatch (no GH issue yet). Premise documented in handoff `2026-05-13-m20-build-iteration-4-contract-shipped-brief.md` and user direction 2026-05-13: "we need much smarter routing."

**Agent:** codex / gpt-5.5 / high
**Base:** `main` @ `be9b7cef49` (post-#1966)
**Expected scope:** ~150-280 LOC across 4-5 files. Single bundled PR.
**Why Codex:** mechanical glue work on top of existing primitives — cost_report.py, Result.usage_record, /api/cost/, /api/batch/usage. No new architecture, just wiring + one config file + a recommendation rule. Architectural debate already done in this handoff (above).

---

## #M-4 Deterministic preamble — verifiable claims this work will produce

| Claim | Tool / command | Output format that captures evidence |
|---|---|---|
| "Endpoint returns the documented shape" | `curl -s http://localhost:8765/api/state/routing-budget \| python -m json.tool \| head -40` | Quote raw JSON keys |
| "Burn% is computed from real usage" | `curl -s http://localhost:8765/api/state/routing-budget \| python -c 'import json,sys; d=json.load(sys.stdin); print(d["agents"]["claude"]["burn_pct_7d"])'` | Quote raw float |
| "Budget config loaded" | `cat scripts/config/agent_budgets.yaml` | Quote raw file |
| "Pre-dispatch check warns on hot agent" | `.venv/bin/python scripts/delegate.py dispatch --check-budget --agent claude --task-id test-warn --prompt "no-op" --mode read-only --dry-run` | Quote the WARNING line emitted to stderr |
| "Existing endpoints unbroken" | `curl -s http://localhost:8765/api/cost \| python -c 'import json,sys; json.load(sys.stdin); print("OK")'` and `curl -s http://localhost:8765/api/batch/usage \| python -c 'import json,sys; json.load(sys.stdin); print("OK")'` | Quote `OK` from each |
| "Tests pass" | `.venv/bin/python -m pytest tests/api/ tests/test_delegate*.py tests/analytics/ -v` (NO `-x`) | Quote final `N passed in M.MMs` |
| "Ruff clean" | `.venv/bin/ruff check scripts/api/state_router.py scripts/delegate.py scripts/analytics/ scripts/config/` | Quote `All checks passed!` |
| "PR opened" | `gh pr view --json url` | Quote raw URL |

No "I checked X" prose. Every claim above MUST come back as a raw command output line.

---

## Why this matters (one paragraph)

The orchestrator (Claude in interactive) currently routes dispatches blind to capacity state. Codex weekly quota, Claude headless budget, and Gemini quota are all opaque until a dispatch fails with `rate_limited=True`. From 2026-06-15 Anthropic adds a separate ~$200/mo agentic pool for `claude -p` (the bucket `delegate.py --agent claude` consumes), and from now until 2026-07-13 the Claude Code interactive weekly limit is +50%. We need an observability layer that pre-emptively surfaces "this agent's bucket is getting hot — consider routing elsewhere" so the orchestrator routes from data, not from intuition. The infrastructure to compute this already exists (`batch_state/api_usage/`, `scripts/analytics/cost_report.py`, `/api/cost/`). This dispatch wires a thin routing-recommendation layer on top.

## Scope (4 deliverables)

### 1. New file: `scripts/config/agent_budgets.yaml`

Declarative soft-cap config. Initial values match user's current plan + Anthropic's promo windows. **Use these literal values:**

```yaml
# Agent budget soft-caps used by /api/state/routing-budget for burn% computation.
# These are SOFT caps — the router warns when burn% approaches; it does not block.
# Update when Anthropic announces tier or promo changes.
#
# Effective windows (anchored to user's billing cycle, treated as ISO weeks for now):
#   - claude.interactive: Max 20× = ~$2000/mo API-equivalent. +50% promo until 2026-07-13.
#   - claude.agentic_pool: $200/mo from 2026-06-15 (Anthropic Pro+/Max agentic credit).
#   - codex: ~$1000/wk effective weekly quota (rough; revise from observed cap-hits).
#   - gemini: ~$500/wk effective daily quota aggregated (rough).
#
# All caps are dollar-denominated. Records that lack a cost estimate are excluded
# from burn% (counted in "missing_cost_records" diagnostic).

claude:
  interactive:
    weekly_cap_usd: 460  # $2000/mo ÷ 4.33 weeks; this is the "shared with chat" pool
    promo_through: "2026-07-13"
    promo_weekly_cap_usd: 690  # +50%
  agentic_pool:
    monthly_cap_usd: 200
    starts_on: "2026-06-15"
codex:
  weekly_cap_usd: 1000
gemini:
  weekly_cap_usd: 500
```

Path: `scripts/config/agent_budgets.yaml` (create the `config/` subdir under `scripts/` if it doesn't already exist).

### 2. New endpoint: `GET /api/state/routing-budget`

Live in `scripts/api/state_router.py` (where the other `/api/state/*` endpoints register). Response shape:

```json
{
  "generated_at": "2026-05-13T20:30:00Z",
  "agents": {
    "claude": {
      "interactive": {
        "spent_7d_usd": 412.50,
        "weekly_cap_usd": 690,
        "burn_pct_7d": 59.8,
        "promo_active": true,
        "status": "warm"
      },
      "agentic_pool": {
        "spent_cycle_usd": null,
        "monthly_cap_usd": 200,
        "burn_pct_cycle": null,
        "active": false,
        "starts_on": "2026-06-15",
        "status": "pre_launch"
      }
    },
    "codex": {
      "spent_7d_usd": 234.12,
      "weekly_cap_usd": 1000,
      "burn_pct_7d": 23.4,
      "status": "cool"
    },
    "gemini": {
      "spent_7d_usd": 87.00,
      "weekly_cap_usd": 500,
      "burn_pct_7d": 17.4,
      "status": "cool"
    }
  },
  "in_flight": {
    "claude": 0,
    "codex": 1,
    "gemini": 0
  },
  "recommendation": {
    "primary_agent_for_code": "codex",
    "rationale": "All agents cool or warm; default 3:3:3 split applies. Codex has lowest 7d burn (23.4%). Claude agentic pool pre-launch — interactive pool used for claude headless.",
    "warnings": []
  },
  "diagnostics": {
    "records_loaded": 1842,
    "missing_cost_records": 17,
    "window_start": "2026-05-06T20:30:00Z"
  }
}
```

`status` mapping (deterministic, not heuristic):
- `cool` — burn_pct < 50
- `warm` — burn_pct 50-75
- `hot` — burn_pct 75-90
- `near_cap` — burn_pct > 90
- `pre_launch` — bucket not active yet (agentic_pool before 2026-06-15)

`recommendation.primary_agent_for_code` rule (apply in order, return first match):
1. If any agent is `near_cap` AND another is `cool`/`warm`, recommend the coolest non-`near_cap` agent.
2. If claude.agentic_pool is `active` AND `cool`, recommend `claude` (drain the separate pool first — it refreshes monthly anyway, leaving it unused is wasted capacity).
3. If all agents `cool`/`warm`, recommend `codex` (current default per MEMORY #M0 mechanical-row).
4. If all agents `hot` or `near_cap`, set `primary_agent_for_code: "inline_orchestrator"` and add a warning explaining the pool-exhaustion scenario.

`warnings` list (deterministic, populated only when applicable):
- `"claude.interactive at {burn_pct}% — consider --agent codex for next mechanical fix"` when claude.interactive is `hot`+
- `"agentic_pool launches in N days"` when current date is within 14 days of `starts_on`
- `"promo expires in N days; +50% bonus capacity ends 2026-07-13"` when within 14 days of `promo_through`
- `"all agents near cap — orchestrator inline-mode contingency may be needed soon"` when triggered

### 3. New `scripts/delegate.py` flag: `--check-budget`

Opt-in pre-flight that runs BEFORE the dispatch worker spawns:
- Hits `http://localhost:8765/api/state/routing-budget` (3-second timeout).
- If `recommendation.primary_agent_for_code != --agent` arg, print to stderr:
  ```
  ⚠ ROUTING WARNING: budget recommends --agent {recommended}, you passed --agent {actual}.
  Rationale: {recommendation.rationale}
  Proceed anyway? (use --force-agent to suppress this check, or Ctrl+C to abort.)
  ```
  Then sleep 3s for human cancel-window, then proceed.
- If `--force-agent` is ALSO passed: skip the warning entirely, fire normally.
- If the endpoint is unreachable (Monitor API down): print one-line `⚠ ROUTING CHECK SKIPPED: Monitor API unreachable` and proceed without blocking.
- Default behavior (no `--check-budget` passed): unchanged — preserves all existing dispatch flows.

### 4. MEMORY footnote update

Add one line under `## TOOL SELECTION` (around line 138) to MEMORY.md:
```
- `/api/state/routing-budget` → pre-dispatch capacity check. Add `--check-budget` to delegate.py for warnings. Soft-fail when API down.
```

DO NOT trim other MEMORY entries; user manages those. Adding one bullet is fine even at 150 lines (hard limit 200 per file header).

## Files touched (estimate)

| File | Action | LOC |
|---|---|---|
| `scripts/config/agent_budgets.yaml` | create | ~30 |
| `scripts/api/state_router.py` | add endpoint + helper functions | ~120 |
| `scripts/analytics/cost_report.py` | maybe extend with `compute_burn_pct(records, since, cap)` helper | ~30 |
| `scripts/delegate.py` | add `--check-budget` + `--force-agent` argparse + pre-flight call | ~50 |
| `memory/MEMORY.md` | one-line footnote | ~1 |
| `tests/api/test_routing_budget_endpoint.py` | new file | ~80 |
| `tests/test_delegate_check_budget.py` | new file | ~40 |

## Implementation notes (do not skip — these prevent rework)

- **Existing infrastructure to REUSE, not reinvent:**
  - `scripts/analytics/cost_report.py::load_cost_records()` — already loads usage records, already understands phases/levels/slugs.
  - `scripts/analytics/cost_report.py::build_cost_summary()` — already aggregates over `since` window.
  - The new endpoint should call these, NOT re-walk `batch_state/api_usage/` directly.

- **Per-agent cost extraction:** `load_cost_records()` returns records but does NOT currently filter by agent. You'll need to either: (a) accept that the existing `build_cost_summary` aggregates across agents and add an `agent: str | None` filter, OR (b) iterate records and group by `record["agent"]` in the new helper. Option (a) keeps the analytics layer coherent; do that if `build_cost_summary` is the natural seam. If it's invasive, option (b).

- **`agentic_pool.spent_cycle_usd` before 2026-06-15:** return `null` and set `status: "pre_launch"`. Do NOT estimate or invent. After 2026-06-15 this requires knowing the user's billing-cycle start day — not in scope for this PR; leave `spent_cycle_usd` reading from records but `monthly_cap_usd` is the divisor. A follow-up issue can refine billing-cycle anchoring.

- **`promo_active` flag:** `True` if `current_date <= promo_through`. Compare as ISO dates.

- **`weekly_cap_usd` selection for claude.interactive:** if `promo_active`, use `promo_weekly_cap_usd`; else `weekly_cap_usd`.

- **`in_flight` data source:** read from the existing `/api/orient` delegate section's `recent_outcomes` + `active_count` paths. Don't add a new SQL or filesystem walk; the data is already aggregated.

- **Budget config: YAML, not Python.** Use `yaml.safe_load`; the schema is stable across reads. If `yaml.safe_load` raises, treat as `pre_launch` for all buckets and emit a `warnings` entry.

- **No new dependencies.** Project already has `pyyaml`, `fastapi`, `pytest`. Don't add `pydantic-settings` or similar.

## Tests required

`tests/api/test_routing_budget_endpoint.py`:
1. `test_endpoint_returns_documented_shape` — assert top-level keys `agents`, `in_flight`, `recommendation`, `diagnostics`, `generated_at` exist.
2. `test_status_cool_when_burn_under_50` — feed synthetic records via tmp dir, assert `status == "cool"`.
3. `test_status_hot_when_burn_75_90` — synthetic 80% burn, assert `status == "hot"`.
4. `test_pre_launch_agentic_pool_before_2026_06_15` — assert `agents.claude.agentic_pool.status == "pre_launch"` when `now < starts_on`.
5. `test_recommendation_picks_coolest_when_one_near_cap` — synthetic claude at 92%, codex at 30%, assert `primary_agent_for_code == "codex"`.
6. `test_recommendation_inline_when_all_hot` — all three at 85%+, assert `primary_agent_for_code == "inline_orchestrator"` and warning present.
7. `test_promo_through_uses_promo_cap_until_expiry` — date < 2026-07-13, divisor is 690; date > 2026-07-13, divisor is 460.

`tests/test_delegate_check_budget.py`:
1. `test_check_budget_warns_when_agent_mismatch` — mock endpoint returns `recommended=codex`, dispatch with `--agent claude --check-budget`, assert WARNING printed to stderr.
2. `test_check_budget_skipped_when_force_agent` — same setup but `--force-agent`, assert no warning.
3. `test_check_budget_skipped_when_api_down` — mock endpoint times out, assert "ROUTING CHECK SKIPPED" printed, dispatch proceeds.
4. `test_check_budget_off_by_default` — no `--check-budget` flag, assert no endpoint call attempted.

## Pre-submit checklist (numbered)

1. `git worktree add -b fix/routing-budget-observability ../routing-budget origin/main` — set up isolated worktree from clean `main`.
2. **File-level work** per the 4 deliverables above. Re-use cost_report primitives.
3. **Test suite:** `.venv/bin/python -m pytest tests/api/ tests/test_delegate*.py tests/analytics/ -v` — must show all new tests PASS and existing tests still PASS. **Forbid `pytest -x`** (per #1942). Capture full failure count if any.
4. **Existing-endpoint sanity:** `curl -s http://localhost:8765/api/cost && curl -s http://localhost:8765/api/batch/usage` — both must return parseable JSON.
5. **Ruff:** `.venv/bin/ruff check scripts/api/state_router.py scripts/delegate.py scripts/analytics/ scripts/config/` — "All checks passed!"
6. **Commit:** conventional message `feat(routing-budget): add /api/state/routing-budget + delegate.py --check-budget pre-flight` — body cites the user direction "we need much smarter routing" and notes the agentic-pool launch trigger (2026-06-15).
7. **Push:** `git push -u origin fix/routing-budget-observability`.
8. **PR:** `gh pr create --base main --title "feat(routing-budget): observability for agent capacity state" --body "<template below>"` — DO NOT auto-merge.
9. **No auto-merge.** Report PR URL + final `gh pr checks` raw output in finalize. Orchestrator merges after blocking checks green.

## PR body template

```
## Summary

- New `GET /api/state/routing-budget` endpoint exposing per-agent burn% + recommendation
- New `scripts/config/agent_budgets.yaml` config for soft-cap values
- New `delegate.py dispatch --check-budget` opt-in pre-flight + `--force-agent` override
- MEMORY.md footnote pointing at the new endpoint

## Why

User direction 2026-05-13: "we need much smarter routing." From 2026-06-15 the Anthropic agentic credit pool (~$200/mo, separate bucket) launches; until 2026-07-13 the Claude Code weekly cap is +50%. Without observability into per-agent burn rate, the orchestrator routes blind and can only react to rate-limit failures. This PR wires a routing-recommendation layer onto existing cost telemetry (`scripts/analytics/cost_report.py` + `/api/cost/`).

## Test plan

- [x] New endpoint returns documented JSON shape; status thresholds (cool/warm/hot/near_cap) deterministic
- [x] `pre_launch` status returned for agentic_pool before 2026-06-15
- [x] Promo-window divisor switches on 2026-07-13
- [x] Recommendation picks coolest agent; inline_orchestrator when all hot
- [x] `--check-budget` warns on mismatch, skips on `--force-agent`, soft-fails on API down
- [x] Existing `/api/cost` and `/api/batch/usage` endpoints unbroken
- [x] Ruff clean
```

## Forbidden

- ❌ Adding new Python dependencies (use existing pyyaml / fastapi / pytest).
- ❌ Modifying `scripts/analytics/cost_report.py` beyond adding ONE helper function. If structural changes are needed, STOP and report.
- ❌ Touching `/api/cost/*` endpoints (preserve back-compat).
- ❌ `pytest -x` in pre-push verification (per #1942).
- ❌ Auto-merge on the PR.
- ❌ Hardcoding budget values inline in Python — they MUST live in the YAML config so the user can edit without a code change.
- ❌ Estimating or inventing `agentic_pool.spent_cycle_usd` before 2026-06-15. Return null.

## Halt conditions

- If `load_cost_records()` returns 0 records on a real cwd (not test fixture) → STOP. Telemetry pipeline may be broken; investigate before continuing.
- If `build_cost_summary()` cannot be filtered/grouped by agent without invasive refactor → STOP and report the seam mismatch; orchestrator will scope a separate analytics-layer PR.
- If any existing `tests/analytics/` or `tests/api/` test fails after your changes → STOP; do NOT commit. The implementation broke a primitive.

---

*Companion docs: `claude_extensions/rules/dispatch-brief-checklist` (numbered steps required); `docs/best-practices/deterministic-over-hallucination.md` (#M-4 evidence shape); handoff `2026-05-13-m20-build-iteration-4-contract-shipped-brief.md` (queue context).*
