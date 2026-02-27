# Monitor API Reference

Base URL: `http://localhost:8765`

FastAPI auto-docs: `http://localhost:8765/docs` (Swagger UI)

---

## Health & Config — `/api/`

### `GET /api/health`

Server health check — returns status, version, uptime. Use for monitoring scripts and load balancers.

```bash
curl -s http://localhost:8765/api/health | python3 -m json.tool
```

Response:
```json
{
  "status": "ok",
  "version": "2.0.0",
  "uptime_seconds": 3600,
  "started_at": "2026-02-21T10:00:00+00:00",
  "checked_at": "2026-02-21T11:00:00+00:00"
}
```

### `GET /api/config`

Returns level configuration and API version.

### Error Responses

All endpoints return errors in consistent JSON format:

```json
{
  "error": "internal_server_error",
  "detail": "Description of what went wrong"
}
```

Standard HTTP status codes: `404` for missing resources, `500` for server errors.

---

## State Endpoints — `/api/state/`

These are the primary endpoints for understanding pipeline state. All are read-only GETs.

### `GET /api/state/summary`

Full project snapshot — one call replaces 5 bash scripts at session start.

```bash
curl -s http://localhost:8765/api/state/summary | python3 -m json.tool
```

Returns per-track counts:
- `total` — plan files count (source of truth)
- `research_done` — Phase A complete (`v3-A.status == "complete"`)
- `content_done` — Phase B complete (`v3-B.status == "complete"`)
- `audit_passing` — `status/*.json` overall == "pass"
- `final_review_done` — `review/*-final-review.md` exists
- `profile` — "core" | "seminar" | "pro"

Sample response:
```json
{
  "generated_at": "2026-02-19T15:30:06Z",
  "tracks": {
    "istoriohrafiia": {
      "total": 136, "profile": "seminar",
      "research_done": 26, "content_done": 0,
      "audit_passing": 0, "final_review_done": 0
    },
    "hist": {
      "total": 140, "profile": "seminar",
      "research_done": 140, "content_done": 5,
      "audit_passing": 4, "final_review_done": 4
    }
  },
  "totals": { "total": 1500, "research_done": 400, ... }
}
```

---

### `GET /api/state/pipeline/{track}`

Per-module v3 phase state for one track. Shows each module's phase progress.

```bash
curl -s http://localhost:8765/api/state/pipeline/istoriohrafiia | python3 -m json.tool
curl -s http://localhost:8765/api/state/pipeline/hist | python3 -m json.tool
```

Returns:
```json
{
  "track": "hist",
  "total": 140,
  "modules": [
    {
      "num": 1, "slug": "trypillian-civilization",
      "phases": {
        "A": {"status": "complete", "mode": "meta-only", "ts": "2026-02-19T10:16:32Z"},
        "B": {"status": "complete", "ts": "..."},
        "C": {"status": "pending"},
        "audit": {"status": "complete", "attempts": 2},
        "D": {"status": "complete"}
      },
      "audit": "pass",
      "words": 5240,
      "word_target": 5000,
      "research_score": 9
    }
  ]
}
```

Phase statuses: `"pending"` | `"complete"` | `"failed"` | `"in_progress"`

---

### `GET /api/state/build-status/{track}`

Compact live build progress for one track. **One call tells you: what's building, how many done, recent completions.**

```bash
curl -s http://localhost:8765/api/state/build-status/a1 | python3 -m json.tool
```

Returns:
```json
{
  "track": "a1", "total": 44,
  "done": 11, "building": 1, "queued": 32, "failed": 0,
  "progress": "11/44 (25%)",
  "currently_building": [{"num": 12, "slug": "the-accusative-ii-people", "phase": "B"}],
  "recent_completions": [
    {"num": 11, "slug": "the-accusative-i-things", "phase": "D", "audit": "pass", "words": "2789/2000"}
  ]
}
```

Cache TTL: 15 seconds (designed for live monitoring).

---

### `GET /api/state/build-status`

All-tracks build progress in one call. Shows done/total/building/failed per track.

```bash
curl -s http://localhost:8765/api/state/build-status | python3 -m json.tool
```

Returns only tracks that have activity. Use during overnight builds for a single-glance overview.

---

### `GET /api/state/module/{track}/{num}`

Single module deep-dive — **everything about one module in one call**, including related broker messages.

```bash
curl -s http://localhost:8765/api/state/module/a1/9 | python3 -m json.tool
```

Returns:
- `phases` — A through F with status/timestamps
- `audit` — status, word_count, word_target, blocking_issues
- `research` — exists, quality score (0-10)
- `review` — exists
- `final_review` — verdict (APPROVE/NEEDS_WORK), issue count, issue summaries
- `enriched` — whether plan was enriched (`.yaml.bak` exists)
- `comms` — last 15 broker messages related to this module's slug

---

### `GET /api/state/final-reviews/{track}`

Phase F results aggregated per track. Shows approval rate, issue patterns, rejected modules.

```bash
curl -s http://localhost:8765/api/state/final-reviews/a1 | python3 -m json.tool
```

Returns:
```json
{
  "track": "a1",
  "total_reviewed": 40, "approved": 37, "rejected": 3,
  "pending_review": 0, "approval_rate": "92%",
  "issue_patterns": {"FACTUAL": 2, "MISSING": 1},
  "rejected_modules": [{"num": 27, "slug": "colors-and-clothing", "verdict": "NEEDS_WORK", "issue_count": 10}]
}
```

`issue_patterns` counts keywords (FACTUAL, PLAN COMPLIANCE, ACTIVITY, ANTI-SURZHYK, etc.) across all issues.

---

### `GET /api/state/track-health/{track}`

**One call to know everything about a track.** Build progress, audit, enrichment, final review, word quality, ETA, and attention list — all in one response.

```bash
curl -s http://localhost:8765/api/state/track-health/a1 | python3 -m json.tool
```

Returns:
```json
{
  "track": "a1", "total": 44,
  "build": {"done": 15, "pct": 34},
  "audit": {"passing": 40, "failing": 0, "pct": 91},
  "enrichment": {"done": 44, "pct": 100},
  "final_review": {"reviewed": 40, "approved": 37, "approval_rate": "92%"},
  "words": {"avg_ratio": "1.31x"},
  "eta": {"remaining": 29, "minutes": 142, "display": "~142min (2h22m)"},
  "attention": [{"num": 27, "slug": "colors-and-clothing", "reason": "final_review_NEEDS_WORK", "detail": "10 issues"}]
}
```

ETA is calculated from the rate of recent Phase B completions. Cache TTL: 30 seconds.

---

### `GET /api/state/enrichment-status[?track=x]`

Which plans are enriched per track. Checks for `.yaml.bak` files in `plans/`.

```bash
curl -s http://localhost:8765/api/state/enrichment-status | python3 -m json.tool
curl -s "http://localhost:8765/api/state/enrichment-status?track=a1" | python3 -m json.tool
```

Returns per-track: `total`, `enriched`, `pending`, `pct`, `not_enriched` (first 10 slugs).

---

### `GET /api/state/ready-to-build[?track=x]`

Modules where Phase A is complete but Phase B hasn't started. **The build queue.**

```bash
# All tracks
curl -s http://localhost:8765/api/state/ready-to-build | python3 -m json.tool

# Specific track
curl -s "http://localhost:8765/api/state/ready-to-build?track=hist" | python3 -m json.tool
```

Returns list sorted by track then num. Use before running `build_module_v3.py --all`.

---

### `GET /api/state/weak-points[?track=x&min_score=7&limit=20]`

Modules with quality issues — **the fire list** for content work.

Criteria:
- `audit_status == "fail"`
- research score < `min_score` (default 7)
- word count < 80% of `word_target`

```bash
curl -s "http://localhost:8765/api/state/weak-points?track=c1-bio" | python3 -m json.tool
curl -s "http://localhost:8765/api/state/weak-points?min_score=8&limit=50" | python3 -m json.tool
```

Results sorted worst-first (audit fails > thin research > low words).

---

### `GET /api/state/failing[?track=x]`

All modules with `audit status == "fail"` OR any phase status `== "failed"`.

```bash
curl -s http://localhost:8765/api/state/failing | python3 -m json.tool
curl -s "http://localhost:8765/api/state/failing?track=a1" | python3 -m json.tool
```

Includes `blocking_issues` — failed gate names and messages.

---

### `GET /api/state/research-coverage`

Per-track research completeness and quality distribution.

```bash
curl -s http://localhost:8765/api/state/research-coverage | python3 -m json.tool
```

Returns:
```json
{
  "tracks": {
    "c1-bio": {
      "total_modules": 172,
      "has_research": 104,
      "pct_coverage": 60,
      "quality": {"exemplary": 40, "solid": 30, "adequate": 20, "thin": 10, "stub": 4},
      "avg_score": 7.8,
      "needs_upgrade": 14
    }
  }
}
```

`needs_upgrade` = modules with score < 7.

---

### `GET /api/state/review-coverage`

Per-track review and final-review coverage + quality signal.

```bash
curl -s http://localhost:8765/api/state/review-coverage | python3 -m json.tool
```

Parses `review/*-review.md` to extract `Overall Score: X/10` and `Status: PASS|FAIL`.

---

### `GET /api/state/issues[?track=x&severity=critical]`

Aggregated outstanding issues from review files + audit failures.

```bash
curl -s "http://localhost:8765/api/state/issues?severity=critical" | python3 -m json.tool
curl -s "http://localhost:8765/api/state/issues?track=hist" | python3 -m json.tool
```

Two sources:
1. **Review files** — `### Issue N` blocks from `*-review.md` files. Severity set by keywords (factual error, grammar error → critical; style → warning).
2. **Audit failures** — modules with `overall.status == "fail"` and their failing gates.

---

## Existing Useful Endpoints

### Build state
```bash
# What's building right now (active orchestration dirs, < 15 min old)
curl -s http://localhost:8765/api/batch/active

# Dispatcher state (batch queue)
curl -s http://localhost:8765/api/batch/dispatcher
```

### Audit & quality (existing dashboard router)
```bash
# All tracks pass/fail overview
curl -s http://localhost:8765/api/blue/live-status

# Per-module detail for a track
curl -s http://localhost:8765/api/dashboard/track/hist

# Deep module inspection (plan + meta + gates + orchestration)
curl -s http://localhost:8765/api/gold/inspect/hist/trypillian-civilization

# Research coverage (detailed per-module scores)
curl -s http://localhost:8765/api/dashboard/research
```

### Communications (old)
```bash
# Message broker status + recent messages (legacy)
curl -s http://localhost:8765/api/dashboard/comms
```

---

## Agent Comms Endpoints — `/api/comms/`

Full agent communication monitoring, batch progress tracking, zombie detection, and cleanup.

### `GET /api/comms/live-activity[?minutes=15]`

**What's being built RIGHT NOW** — module-level live feed. The primary endpoint for real-time monitoring.

```bash
curl -s http://localhost:8765/api/comms/live-activity | python3 -m json.tool
```

Returns three feeds:
- `in_progress` — modules with recently updated `state-v3.json` (track, slug, phase, status, age)
- `recent_completions` — research files created in last hour (track, slug, size_kb)
- `recent_dispatches` — last 30 broker messages (from, to, task_id, preview)

### `GET /api/comms/batch-progress`

Track-level batch progress for overnight/background builds. Shows health status per track.

```bash
curl -s http://localhost:8765/api/comms/batch-progress | python3 -m json.tool
```

Returns per-track:
- `health` — `"healthy"` | `"stalled"` | `"dead"` | `"complete"` | `"unknown"`
- `research_done` / `total_expected` / `remaining`
- `throughput_per_hour` — files created in last 30 min, annualized
- `log` — preseed log info (passed/failed counts, last line, age)
- `process` — running PID info (if active)

Health logic: `complete` (log says BATCH COMPLETE) > `healthy` (process running + recent files) > `stalled` (process running but no recent files) > `dead` (no process, stale log).

### `GET /api/comms/batch-progress/{track}`

Detailed progress for one track. Includes a timeline of the 20 most recent research files.

### `GET /api/comms/messages[?agent=x&task_id=x&msg_type=x&unacked_only=true&limit=100]`

All messages with optional filters. Returns `preview` (300 chars), not full content.

### `GET /api/comms/conversations[?limit=50]`

Messages grouped by `task_id` with summary stats (msg_count, unacked, errors, agents involved).

### `GET /api/comms/conversation/{task_id}`

Full thread for one task. Returns all messages in order.

### `GET /api/comms/zombies[?stale_hours=2&pingpong_threshold=5]`

Auto-detect stuck patterns:
- `stale_message` — unacked messages older than `stale_hours`
- `pingpong` — rapid back-and-forth on same task (>threshold msgs in 1h)
- `error_loop` — 3+ consecutive errors on same task
- `orphan_pid` — PID files for dead processes

### `GET /api/comms/stats`

Message rate, error %, per-agent breakdown, queue depth.

### `GET /api/comms/health`

Broker DB health: exists, writable, size, queue depth, alive PID count.

### `GET /api/comms/active-processes`

Live bridge PID files with health status (alive/dead, age, agent, task_id).

### `POST /api/comms/cleanup[?max_age_hours=24]`

Force-ack stale messages and clean orphan PID files. Safe to call anytime.

### `GET /api/comms/by-module/{track}/{slug}`

Full communication trail for a module. All broker messages where `task_id` contains the slug.

```bash
curl -s http://localhost:8765/api/comms/by-module/a1/reflexive-verbs | python3 -m json.tool
```

Returns messages grouped by `task_id` (e.g., `v3-reflexive-verbs-pA`, `enrich-reflexive-verbs`) plus a flat list. Shows dispatch history, enrichment calls, repair loops — everything communicated about this module.

### `POST /api/comms/acknowledge/{id}`

Acknowledge a single message by ID.

---

## Watchdog Script

Self-healing cleanup that runs alongside batch builds:

```bash
# Single pass: check health, clean zombies, log alerts
.venv/bin/python scripts/watchdog.py

# Loop mode: every 5 min (run alongside preseed builds)
.venv/bin/python scripts/watchdog.py --loop

# Dry run: show what would be cleaned
.venv/bin/python scripts/watchdog.py --dry-run
```

Does NOT auto-restart tracks. Cleans stale messages + orphan PIDs, alerts on stalled/dead tracks.
Log: `logs/watchdog.log`.

---

## As an Agent: Session Start Checklist

Run these at the start of each session to orient yourself:

```bash
# 1. Full project state (one call)
curl -s http://localhost:8765/api/state/summary | python3 -m json.tool

# 2. What's building right now
curl -s http://localhost:8765/api/batch/active

# 3. What's ready to build next (Phase A done, B not started)
curl -s http://localhost:8765/api/state/ready-to-build | python3 -m json.tool

# 4. Critical issues to fix
curl -s "http://localhost:8765/api/state/issues?severity=critical" | python3 -m json.tool

# 5. Check Gemini messages
curl -s http://localhost:8765/api/dashboard/comms | python3 -c "
import json,sys; d=json.load(sys.stdin)
print('Unread:', d['stats']['unread'])
for m in d['recent_messages'][:5]:
    print(f\"  [{m['from']} → {m['to']}] {m['content_preview'][:80]}\")"
```

---

## UI Pages

| Page | URL | Data source |
|------|-----|-------------|
| Home | `/` | `/api/dashboard/overview`, `/api/state/summary`, `/api/comms/batch-progress` |
| Audit Dashboard | `/audit-dashboard.html` | `/api/blue/live-status`, `/api/dashboard/track/{id}` |
| Progress | `/progress.html` | `/api/state/summary`, `/api/state/pipeline/{track}` |
| Agent Comms | `/comms.html` | `/api/comms/live-activity`, `/api/comms/batch-progress`, `/api/comms/zombies`, `/api/comms/messages`, `/api/comms/stats` |
| Quality | `/quality.html` | `/api/state/research-coverage`, `/api/state/review-coverage`, `/api/state/issues`, `/api/state/weak-points` |
| Track Health | `/track-health.html` | `/api/state/track-health/{track}`, `/api/state/build-status`, `/api/state/enrichment-status` |
| Curriculum | `/curriculum-dashboard.html` | `/api/dashboard/overview` |
| API Docs | `/docs` | FastAPI auto-generated |
