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
# Read-only fleet rollover audit: GET /api/rollovers
```

**Start server:** `npm run api` (or `npm run api:bg`). Serves http://localhost:8765 + all dashboards.

**Usage / limits view (project side; see also external CodexBar.app for 5h/weekly/monthly bars):**
- `.../ai_agent_bridge/__main__.py codex-usage`
- `.venv/bin/python scripts/analytics/cost_report.py --all --markdown`
- Dashboards: cost.html, runtime.html
- API: /api/health (resilience), /api/runtime/recent

## Fleet note (for context)
Bridge for comms/discuss: `.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-*` / `discuss`. Delegate for work: `scripts/delegate.py dispatch --agent ... --worktree`. See shared/memory/MEMORY.md for full details. (CodexBar CLI example: `/Applications/CodexBar.app/Contents/Helpers/CodexBarCLI`)

## Before Building

```bash
# Queue: Phase A done, B not started
curl -s "http://localhost:8765/api/state/ready-to-build?track=hist" | python3 -m json.tool

# Phase-level state for a track
curl -s http://localhost:8765/api/state/pipeline/istorio | python3 -m json.tool
```

## After Batch / QA

```bash
# Failing or weak modules
curl -s "http://localhost:8765/api/state/failing?track=hist" | python3 -m json.tool
curl -s "http://localhost:8765/api/state/weak-points?track=bio" | python3 -m json.tool

# Outstanding critical issues
curl -s "http://localhost:8765/api/state/issues?severity=critical" | python3 -m json.tool
```

## Coverage Checks

```bash
# Research quality per track
curl -s http://localhost:8765/api/state/research-coverage | python3 -m json.tool

# Review scores per track
curl -s http://localhost:8765/api/state/review-coverage | python3 -m json.tool
```

## State Endpoint Summary

| Endpoint | When to use |
|----------|-------------|
| `/api/state/summary` | Session start — total snapshot |
| `/api/state/pipeline/{track}` | Inspect one track's v3/v4 phase progress (auto-detects per module) |
| `/api/state/ready-to-build` | Before `build_module --all` |
| `/api/state/weak-points` | After batch — find what needs fixing |
| `/api/state/failing` | After batch — find hard failures (includes `pipeline_version`) |
| `/api/state/research-coverage` | Research quality health check |
| `/api/state/review-coverage` | Review coverage health check |
| `/api/state/issues` | Outstanding issues from reviews + audit |

**Pipeline version**: All module-level responses include `pipeline_version` (`"v4"`, `"v3"`, `"unbuilt"`) and `needs_rebuild` (`true`/`false`). V4 modules return named phases (`research`..`mdx`); v3 modules return letter-coded phases (`A`..`D`).

## V4 Migration Progress

```bash
# How many modules are v4 vs v3?
curl -s http://localhost:8765/api/state/pipeline-versions | python3 -m json.tool

# For one track
curl -s "http://localhost:8765/api/state/pipeline-versions?track=a1" | python3 -m json.tool
```

## Other Useful Endpoints

```bash
curl -s http://localhost:8765/api/blue/live-status        # Pass/fail all tracks
curl -s http://localhost:8765/api/dashboard/comms         # Broker messages + watcher
curl -s http://localhost:8765/api/gold/inspect/{t}/{slug} # Deep module inspection
```

Full reference: `docs/MONITOR-API.md`
