# Monitor API Cheat Sheet

Base: `http://localhost:8765` | Docs: `/docs`

## At Session Start (Cold-Start Sequence — efficient, use manifest first)

```bash
# 1. Tiny hashes (decide what to fetch; ETag/304 friendly)
curl -s http://localhost:8765/api/state/manifest

# 2. Only if hashes changed
curl -s http://localhost:8765/api/rules?format=markdown
curl -s 'http://localhost:8765/api/session/current?agent=orchestrator'

# 3. Full orient snapshot (git + delegate + runtime + health + pipeline)
curl -s http://localhost:8765/api/orient          # or ?fresh=true
curl -s http://localhost:8765/api/state/summary   # tracks overview (published_mdx, audit etc.)
```

## What's active right now

```bash
curl -s http://localhost:8765/api/delegate/active
curl -s http://localhost:8765/api/runtime/agents
```

**Start server:** `npm run api` (or `npm run api:bg`). Serves http://localhost:8765 + all dashboards.

**Usage / limits view (project side; see also external CodexBar.app for 5h/weekly/monthly bars):**
- `.../ai_agent_bridge/__main__.py codex-usage`
- `LU_PRODUCT_ROOT="$PWD" .venv/bin/python -m lu_machinery.telemetry.cost_report --all --markdown`
- Monitor: `/machinery` for workers and usage
- API: /api/health (resilience), /api/runtime/agents

## Fleet note (for context)
Bridge for comms/discuss: `.venv/bin/python -m lu_machinery.ai_agent_bridge ask-*` / `discuss`. Delegate for work: `scripts/dispatch.py dispatch --model <catalog-model> --agent ... --worktree`. See shared/memory/MEMORY.md for full details. (Capacity: `.venv/bin/python -m lu_machinery.fleet.capacity_pick` and `.venv/bin/python -m lu_machinery.fleet.usage show`; `codexbar usage` is retired.)

## Before Building

```bash
# Canonical preparation decision for one module
curl -s http://localhost:8765/api/state/preparation/hist/<slug> | python3 -m json.tool

# Phase-level state for a track
curl -s http://localhost:8765/api/state/pipeline/istorio | python3 -m json.tool
```

## Coverage Checks

```bash
# Review scores per track
curl -s http://localhost:8765/api/state/review-coverage | python3 -m json.tool
```

## State Endpoint Summary

| Endpoint | When to use |
|----------|-------------|
| `/api/state/summary` | Session start — total snapshot |
| `/api/state/pipeline/{track}` | Inspect one track's v3/v4 phase progress (auto-detects per module) |
| `/api/state/preparation/{track}/{slug}` | Before building a module (canonical readiness decision) |
| `/api/state/review-coverage` | Review coverage health check |

**Pipeline version**: All module-level responses include `pipeline_version` (`"v4"`, `"v3"`, `"unbuilt"`) and `needs_rebuild` (`true`/`false`). V4 modules return named phases (`research`..`mdx`); v3 modules return letter-coded phases (`A`..`D`).

## Other Useful Endpoints

```bash
curl -s http://localhost:8765/api/state/build-status/a1    # Build progress for one track
curl -s http://localhost:8765/api/dashboard/comms         # Broker messages + watcher
curl -s http://localhost:8765/api/gold/inspect/{t}/{slug} # Deep module inspection
```

## Retired Endpoints (HTTP 404)

Retired in #7942 (#7945) and #7947; return HTTP 404 without deprecation headers:
- `GET /api/blue/live-status` → use `GET /api/state/build-status/{track}`
- `GET /api/rag/*` → use canonical `GET /api/sources/*`
- `GET /api/state/ready-to-build` → use canonical `GET /api/state/preparation/{track}/{slug}`
- `GET /api/cost/*` → removed with `/api/analytics/cost/*` below

Removed in the 2026-11-12 product page trim (no replacement route; their data was empty):
- `GET /api/analytics/cost/*` → use `LU_PRODUCT_ROOT="$PWD" .venv/bin/python -m lu_machinery.telemetry.cost_report --all --markdown`
- `/api/build/events/*`, `/api/consultation/*`, `/api/images/*`, `/api/admin/*` → removed; use `GET /api/health` for health

Full reference: `docs/MONITOR-API.md`
