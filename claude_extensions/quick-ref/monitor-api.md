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
curl -s "http://localhost:8765/api/state/ready-to-build?track=b2-hist" | python3 -m json.tool

# Phase-level state for a track
curl -s http://localhost:8765/api/state/pipeline/c1-hist | python3 -m json.tool
```

## After Batch / QA

```bash
# Failing or weak modules
curl -s "http://localhost:8765/api/state/failing?track=b2-hist" | python3 -m json.tool
curl -s "http://localhost:8765/api/state/weak-points?track=c1-bio" | python3 -m json.tool

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
| `/api/state/pipeline/{track}` | Inspect one track's v3 phase progress |
| `/api/state/ready-to-build` | Before `build_module_v3 --all` |
| `/api/state/weak-points` | After batch — find what needs fixing |
| `/api/state/failing` | After batch — find hard failures |
| `/api/state/research-coverage` | Research quality health check |
| `/api/state/review-coverage` | Review coverage health check |
| `/api/state/issues` | Outstanding issues from reviews + audit |

## Other Useful Endpoints

```bash
curl -s http://localhost:8765/api/blue/live-status        # Pass/fail all tracks
curl -s http://localhost:8765/api/dashboard/comms         # Broker messages + watcher
curl -s http://localhost:8765/api/gold/inspect/{t}/{slug} # Deep module inspection
```

Full reference: `docs/MONITOR-API.md`
