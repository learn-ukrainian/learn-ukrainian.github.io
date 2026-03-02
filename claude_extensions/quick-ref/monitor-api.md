# Monitor API Cheat Sheet

Base: `http://localhost:8765` | Docs: `/docs`

## At Session Start

```bash
# Full project snapshot (replaces 5 scripts)
curl -s http://localhost:8765/api/state/summary | python3 -m json.tool

# What's active right now
curl -s http://localhost:8765/api/batch/active
```

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

**Pipeline version**: All module-level responses include `pipeline_version` (`"v4"`, `"v3"`, `"unbuilt"`). V4 modules return named phases (`research`..`mdx`); v3 modules return letter-coded phases (`A`..`D`).

## Other Useful Endpoints

```bash
curl -s http://localhost:8765/api/blue/live-status        # Pass/fail all tracks
curl -s http://localhost:8765/api/dashboard/comms         # Broker messages + watcher
curl -s http://localhost:8765/api/gold/inspect/{t}/{slug} # Deep module inspection
```

Full reference: `docs/MONITOR-API.md`
