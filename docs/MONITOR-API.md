# Monitor API Reference

Base URL: `http://localhost:8765`

FastAPI auto-docs: `http://localhost:8765/docs` (Swagger UI)

---

## Agent Quick Start

**Recommended cold-start sequence (GH #1309, since P1):**

```bash
# 1. Tiny index of per-component hashes — decide what to fetch.
curl -s http://localhost:8765/api/state/manifest

# 2. Only fetch components whose hash changed since last session.
curl -s http://localhost:8765/api/rules?format=markdown     # ~1.3 KB
curl -s http://localhost:8765/api/session/current           # ~1-3 KB

# 3. Always-fresh: git, pipeline, runtime, wiki, health, hints — with meta.
curl -s http://localhost:8765/api/orient
# Use ?fresh=true right after you committed or filed an issue.

# 4. Optional: do I have unread channel deliveries?
curl -s "http://localhost:8765/api/comms/inbox?agent=claude"
```

Agents should keep a small on-disk cache keyed by manifest hash
(`.agent/cache/monitor/*.body`). When the manifest's hash matches
what you cached, skip the payload fetch entirely — the bytes are
still authoritative. A ready-to-use helper lives at
``scripts/ai_agent_bridge/_monitor_cache.py``; the client SDK
(``scripts/monitor_client.py``) will wrap this in P3.

---

### One-shot orient (unchanged, still useful)

```bash
curl -s http://localhost:8765/api/orient | python3 -m json.tool
```

Sample response:
```json
{
  "generated_at": "2026-04-11T00:15:00Z",
  "git": {"branch": "main", "head": "cb5f47d19"},
  "issues": [{"number": 1186, "title": "feat(api): refresh monitor API..."}],
  "pipeline": {"summary": {"totals": {"total": 1500}}},
  "runtime": {"agents": ["claude", "gemini", "codex"]},
  "delegate": {"active_count": 2},
  "wiki": {"by_track": {"hist": {"compiled": 15, "total": 140, "pct": 10.7}}},
  "health": {"api": true, "mcp_rag": false, "sources_db": true, "message_broker": true}
}
```

For live agent progress from the channel bridge, Monitor can consume the event stream directly: `Monitor(command=".venv/bin/python scripts/ai_agent_bridge/__main__.py channel watch <thread_id> --follow --event-stream", ...)`. The watch command replays historical events first, then keeps streaming line-buffered JSONL for `reply_started`, `heartbeat`, `reply_complete`, and delivery outcome events as the inbox worker updates the thread.

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
- `research_done` — modules with research complete across current and legacy build flows
- `content_done` — modules with lesson content complete across current and legacy build flows
- `audit_passing` — `status/*.json` overall == "pass"
- `final_review_done` — `review/*-final-review.md` exists
- `prompt_reviewed` — `/prompt-review` done (`audit/*-prompt-review.md` exists)
- `content_reviewed` — `/content-review` done (`audit/*-content-review.md` exists)
- `profile` — "core" | "seminar" | "pro"

Sample response:
```json
{
  "generated_at": "2026-02-19T15:30:06Z",
  "tracks": {
    "istorio": {
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

Per-module phase state for one track. Shows each module's phase progress and generation label.

```bash
curl -s http://localhost:8765/api/state/pipeline/istorio | python3 -m json.tool
curl -s http://localhost:8765/api/state/pipeline/a1 | python3 -m json.tool
```

Returns:
```json
{
  "num": 1, "slug": "sounds-letters-and-hello",
  "pipeline_version": "v6",
  "phases": {
    "check": {"status": "complete", "ts": "2026-03-20T14:00:00Z"},
    "research": {"status": "complete", "ts": "2026-03-20T14:01:00Z"},
    "write": {"status": "complete", "ts": "2026-03-20T14:05:00Z"},
    "exercises": {"status": "complete", "ts": "2026-03-20T14:08:00Z"},
    "annotate": {"status": "complete", "ts": "2026-03-20T14:10:00Z"},
    "enrich": {"status": "complete", "ts": "2026-03-20T14:12:00Z"},
    "verify": {"status": "complete", "ts": "2026-03-20T14:15:00Z"},
    "publish": {"status": "pending"}
  },
  "audit": "pass",
  "words": 1500,
  "word_target": 1200,
  "research_score": null
}
```

All module-level responses include `needs_rebuild: true|false` and a `pipeline_version` label derived from the module's orchestration state.

Current phases: `check`, `research`, `write`, `exercises`, `annotate`, `enrich`, `verify`, `publish`.
Legacy modules expose their recorded phase keys as-is.

Some phase entries include an `executor` object with `type` (llm/script), `agent`, and `model`.

Phase statuses: `"pending"` | `"complete"` | `"failed"` | `"in_progress"`

---

### `GET /api/state/pipeline-versions[?track=x]`

Pipeline generation counts and rebuild pressure. **The single-glance migration dashboard.**

```bash
curl -s http://localhost:8765/api/state/pipeline-versions | python3 -m json.tool
curl -s "http://localhost:8765/api/state/pipeline-versions?track=a1" | python3 -m json.tool
```

Returns:
```json
{
  "total": 64,
  "counts": {"...": "per-generation counts"},
  "pct_built": 66,
  "needs_rebuild": 22,
  "per_track": {"a1": {"...": "per-generation counts"}},
  "generated_at": "2026-04-11T00:15:00Z"
}
```

`needs_rebuild` is the number of modules still on older generations or unbuilt.

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

### `GET /api/state/build-stats/{track}`

V6 build attempt history from `build-stats.jsonl`. Each V6 build appends a line to this file; this endpoint reads and summarizes it.

```bash
curl -s http://localhost:8765/api/state/build-stats/a1 | python3 -m json.tool
```

Returns:
```json
{
  "track": "a1",
  "total_attempts": 12,
  "successes": 8,
  "unique_modules": 5,
  "success_rate": "66.7%",
  "entries": [
    {
      "slug": "sounds-letters-and-hello",
      "attempt": 2,
      "result": "success",
      "timestamp": "2026-03-20T14:15:00Z",
      "duration_seconds": 180
    }
  ]
}
```

`entries` returns the last 50 build attempts (most recent first). Use this to monitor V6 build reliability, identify modules that need multiple attempts, and track overall build success rates.

---

### `GET /api/state/module/{track}/{num}`

Single module deep-dive — **everything about one module in one call**, including related broker messages.

```bash
curl -s http://localhost:8765/api/state/module/a1/9 | python3 -m json.tool
```

Returns:
- `pipeline_version` — current generation label or legacy/unbuilt marker
- `phases` — phase map from the module's recorded orchestration state
- `audit` — status, word_count, word_target, blocking_issues
- `research` — exists, quality score (0-10). Detects both research files and knowledge packets
- `review` — exists, **score** (numeric, e.g. 8.7), **verdict** (PASS/FAIL) *(#971)*
- `friction` — **active** count, **resolved** count, **items** list with id/type/description *(#970/#971)*
- `shippable` — **true/false** (audit PASS + review >= 8.0) *(#971)*
- `stress` — **mismatches** count, **unknown** count, **details** (from D.0 screen cache) *(#971)*
- `prompt_review` — whether `/prompt-review` has been run (bool, checks `audit/{slug}-prompt-review.md`)
- `content_review` — whether `/content-review` has been run (bool, checks `audit/{slug}-content-review.md`)
- `final_review` — verdict (APPROVE/NEEDS_WORK), issue count, issue summaries
- `enriched` — whether plan was enriched (`.yaml.bak` exists)
- `consultations` — list of consultation attempts from `--consult` runs (num, outcome, scope, action, confidence, timestamp)
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

Modules where research is complete but content hasn't started. **The build queue.**

```bash
# All tracks
curl -s http://localhost:8765/api/state/ready-to-build | python3 -m json.tool

# Specific track
curl -s "http://localhost:8765/api/state/ready-to-build?track=hist" | python3 -m json.tool
```

Each entry includes `pipeline_version`. Returns list sorted by track then num.

---

### `GET /api/state/weak-points[?track=x&min_score=7&limit=20]`

Modules with quality issues — **the fire list** for content work.

Criteria:
- `audit_status == "fail"`
- research score < `min_score` (default 7)
- word count < 80% of `word_target`

```bash
curl -s "http://localhost:8765/api/state/weak-points?track=bio" | python3 -m json.tool
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

Each entry includes `pipeline_version`, `failed_phases`, and `blocking_issues`.

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
    "bio": {
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
curl -s http://localhost:8765/api/dashboard/module/a1/my-world-objects

# Deep module inspection (legacy gold)
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
- `in_progress` — modules with recently updated orchestration state (track, slug, phase, status, age)
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

Returns messages grouped by `task_id` (e.g., `reflexive-verbs-phase-a`, `enrich-reflexive-verbs`) plus a flat list. Shows dispatch history, enrichment calls, repair loops — everything communicated about this module.

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

## Consultation Endpoints — `/api/consultation/`

Self-improving template loop: review proposals, approve/reject, track history and patterns.

### `GET /api/consultation/queue`

List all pending consultation proposals.

```bash
curl -s http://localhost:8765/api/consultation/queue | python3 -m json.tool
```

Response:
```json
{
  "pending": [
    {
      "filename": "20260313T184951744734-being-and-becoming.yaml",
      "source_module": "a2/being-and-becoming",
      "track": "a2",
      "slug": "being-and-becoming",
      "confidence": "high",
      "root_cause_summary": "The content template produces insufficient Ukrainian...",
      "change_count": 3,
      "queued_at": "2026-03-13T18:49:51.749342+00:00",
      "target_files": ["claude_extensions/phases/gemini/content.md"]
    }
  ],
  "count": 1
}
```

### `GET /api/consultation/queue/{filename}`

Full proposal detail including all FIND/REPLACE changes.

### `POST /api/consultation/queue/{filename}/approve?confirm=true`

Validate FIND strings exist in templates, apply patches, move YAML to `applied/`. Returns 409 if FIND strings don't match.

### `POST /api/consultation/queue/{filename}/reject?confirm=true&reason=...`

Move YAML to `rejected/`, optionally record reason.

### `GET /api/consultation/history`

All consultations across all modules. Params: `?track=`, `?outcome=`, `?limit=50`, `?offset=0`.

```bash
# All consultations for track a2
curl -s "http://localhost:8765/api/consultation/history?track=a2" | python3 -m json.tool
```

### `GET /api/consultation/history/{track}/{slug}`

Consultation timeline for one module.

### `GET /api/consultation/metrics`

Aggregate stats: total, by outcome/confidence/scope/track, top root cause keywords.

```bash
curl -s http://localhost:8765/api/consultation/metrics | python3 -m json.tool
```

Response:
```json
{
  "total": 4,
  "pending_queue": 2,
  "by_outcome": {"queued": 2, "applied": 1, "no_action": 1},
  "by_confidence": {"high": 3, "medium": 1},
  "by_scope": {"all_modules": 3, "this_module": 1},
  "by_track": {"a2": 4},
  "top_root_causes": [["template", 3], ["ukrainian", 2]]
}
```

---

## Decision Journal — `/api/decisions/`

Exposes the decision journal (`docs/decisions/decisions.yaml`) — architectural and design decisions with expiry tracking.

### `GET /api/decisions[?status=active]`

All decisions, optionally filtered by status (`active`, `superseded`, `expired`, `archived`).

```bash
curl -s http://localhost:8765/api/decisions | python3 -m json.tool
curl -s "http://localhost:8765/api/decisions?status=active" | python3 -m json.tool
```

### `GET /api/decisions/stale`

Active decisions past their expiry date — need re-evaluation. Uses same staleness logic as `scripts/audit/check_decisions.py`.

```bash
curl -s http://localhost:8765/api/decisions/stale | python3 -m json.tool
```

### `GET /api/decisions/budget`

Budget status: active count vs max (50), warning threshold (40).

```bash
curl -s http://localhost:8765/api/decisions/budget | python3 -m json.tool
```

Response:
```json
{
  "active_count": 5,
  "total_count": 5,
  "budget_max": 50,
  "budget_warn": 40,
  "status": "ok"
}
```

### `GET /api/decisions/scope/{scope}`

Filter by scope: `pipeline`, `content`, `architecture`, `tooling`, `pedagogy`.

```bash
curl -s http://localhost:8765/api/decisions/scope/pipeline | python3 -m json.tool
```

### `GET /api/decisions/{dec_id}`

Single decision by ID (e.g., `dec-001`). Includes `is_stale` boolean.

```bash
curl -s http://localhost:8765/api/decisions/dec-001 | python3 -m json.tool
```

---

## Wiki Compilation — `/api/wiki/`

Read-only observability for compiled wiki articles, quality gate results, build logs, and source inventory.

### `GET /api/wiki/status`

Per-track compiled vs total wiki coverage, with progress percentage and total compiled words.

Response:
```json
{
  "tracks": [
    {
      "track": "hist",
      "total": 42,
      "compiled": 18,
      "pct": 42.9,
      "total_words": 31240
    }
  ]
}
```

### `GET /api/wiki/status/{track}`

Per-module wiki status for one track: compile flag, words, timestamp, and source count.

Response:
```json
[
  {
    "slug": "kyivan-rus",
    "compiled": true,
    "word_count": 1820,
    "compiled_at": "2026-04-10T18:45:00+00:00",
    "source_count": 7
  }
]
```

### `GET /api/wiki/article/{track}/{slug}`

Single article metadata with a 500-character preview.

Response:
```json
{
  "track": "hist",
  "slug": "kyivan-rus",
  "compiled": true,
  "path": "/Users/me/projects/learn-ukrainian/wiki/periods/kyivan-rus.md",
  "word_count": 1820,
  "preview": "# Kyivan Rus\\n\\nKyivan Rus was ...",
  "source_count": 7,
  "compiled_at": "2026-04-10T18:45:00+00:00"
}
```

### `GET /api/wiki/quality-gate`

Runs the wiki quality gate for all tracks and returns issues grouped by track.

Response:
```json
{
  "hist": {
    "periods/kyivan-rus.md": [
      "SHORT (900w < 1500)"
    ]
  },
  "folk": {}
}
```

### `GET /api/wiki/quality-gate/{track}`

Runs the wiki quality gate for one track only.

Response:
```json
{
  "hist": {
    "periods/kyivan-rus.md": [
      "SHORT (900w < 1500)"
    ]
  }
}
```

### `GET /api/wiki/build-log[?track=x&limit=50]`

Recent structured build events, optionally filtered to one track.

Response:
```json
{
  "events": [
    {
      "ts": "2026-04-10T18:45:00+00:00",
      "track": "hist",
      "slug": "kyivan-rus",
      "event": "compile"
    }
  ]
}
```

### `GET /api/wiki/sources`

Row counts for the wiki `data/sources.db` tables and a total entry count.

Response:
```json
{
  "tables": [
    {"name": "textbooks", "row_count": 12034},
    {"name": "sum11", "row_count": 127001}
  ],
  "total_entries": 139035
}
```

### `GET /api/wiki/sources/{track}/{slug}`

Source availability for one module from its discovery file.

Response:
```json
{
  "keywords": ["Київська Русь", "князі"],
  "literary_chunks": [],
  "textbook_chunks": [
    {"chunk_id": "abc123_c0001"}
  ],
  "literary_files": []
}
```

---

## Runtime Observability — `/api/runtime/`

### `GET /api/runtime/agents`

Registered runtime adapters with default model and supported modes.

```json
{
  "agents": [
    {"name": "claude", "binary": "npx @anthropic-ai/claude-code@latest"},
    {"name": "gemini", "binary": "gemini"},
    {"name": "codex", "binary": "codex"}
  ]
}
```

### `GET /api/runtime/usage?agent=&entrypoint=&days=7`

Aggregated usage counts from `batch_state/api_usage/usage_*.jsonl`.

```json
{
  "window_days": 7,
  "records_total": 1234,
  "by_agent": {"codex": {"total": 300, "ok": 280, "error": 10}},
  "by_entrypoint": {"dispatch": {"total": 700, "ok": 690}}
}
```

### `GET /api/runtime/headroom?agent=codex&model=gpt-5.4`

Quota gate for one `(agent, model)` pair.

```json
{
  "agent": "codex",
  "model": "gpt-5.4",
  "has_headroom": true,
  "reason": ""
}
```

### `GET /api/runtime/recent?limit=50`

Newest usage records from today's runtime logs, newest first.

```json
{
  "records": [
    {"ts": "2026-04-11T00:10:00Z", "agent": "codex", "entrypoint": "dispatch", "outcome": "ok"},
    {"ts": "2026-04-11T00:09:00Z", "agent": "gemini", "entrypoint": "bridge", "outcome": "timeout"}
  ]
}
```

## Delegation — `/api/delegate/`

### `GET /api/delegate/tasks?status=&limit=50`

List delegate task state files with derived age and zombie detection.

```json
{
  "total": 12,
  "tasks": [
    {"task_id": "issue-1166", "agent": "codex", "status": "running", "age_s": 45.0},
    {"task_id": "issue-1165", "agent": "gemini", "status": "done", "age_s": 280.3}
  ]
}
```

### `GET /api/delegate/tasks/{task_id}`

Single task detail plus optional `.result` content.

```json
{
  "task": {"task_id": "issue-1166", "status": "done"},
  "result": "trimmed result text",
  "result_truncated": false,
  "alive": false
}
```

## Build Events — `/api/build/events/`

### `GET /api/build/events/recent?level=&slug=&limit=100`

Recent synthesized build events from dispatch metadata.

```json
{
  "events": [
    {"ts": "2026-04-10T21:50:27Z", "level": "a2", "slug": "a2-bridge", "phase": "skeleton", "ok": true},
    {"ts": "2026-04-10T21:45:01Z", "level": "a2", "slug": "a2-bridge", "phase": "write", "ok": true}
  ]
}
```

### `GET /api/build/events/active?level=`

Modules with recent dispatch activity and unfinished publish state.

```json
{
  "active": [
    {"level": "a2", "slug": "a2-bridge", "current_phase": "write", "started_at": "2026-04-10T21:50:27Z", "age_s": 240}
  ]
}
```

## Orientation — `/api/orient`

### `GET /api/orient`

One-call agent orientation: git, issues, pipeline, runtime, delegate, wiki, health, and session hints.

```json
{
  "generated_at": "2026-04-11T00:15:00Z",
  "git": {"branch": "main", "head": "cb5f47d19"},
  "issues": [{"number": 1186, "title": "feat(api): refresh monitor API..."}],
  "runtime": {"agents": ["claude", "gemini", "codex"]},
  "health": {"api": true, "mcp_rag": false},
  "meta": {
    "git": {"generated_at": "2026-04-11T00:15:00Z", "stale_after_s": 30, "source": "git", "cache": "miss"},
    "issues": {"generated_at": "2026-04-11T00:14:10Z", "stale_after_s": 120, "source": "gh", "cache": "hit"}
  }
}
```

#### Per-section caching + freshness metadata (#1309)

Each section is computed by an independent collector. Most have a
per-section TTL cache; a repeat call within the window skips the
underlying shellout (`git`, `gh issue list`) or filesystem scan and
returns the cached value. Errors are **not** cached — a transient
failure retries on the next call.

| Section | TTL (s) | Source | Notes |
|---|---:|---|---|
| `git` | 30 | `git` | branch, head, ahead_of_origin, recent_commits |
| `issues` | 120 | `gh` | top 10 open issues; slow API, rare updates |
| `pipeline` | 0 | `fs` | wraps `/api/state/summary`, which carries its **own** 60 s cache. Caching again at the orient layer would stack windows and label up-to-119 s-old data as fresh (#1309 reviewer BLOCKER B2). |
| `runtime` | 60 | `fs` | agent registry + headroom + recent outcomes |
| `delegate` | 30 | `fs` | active delegate/codex tasks |
| `wiki` | 120 | `fs` | per-track wiki compilation coverage |
| `health` | 15 | `probe` | API/DB/MCP port + file readability |
| `session_hints` | 60 | `fs` | recent `docs/session-state/*.md` entries |

Every section is mirrored under `response.meta.<section>` with:

- `generated_at` — ISO timestamp of the underlying collector run (useful
  when `cache: "hit"`: the value may be up to `stale_after_s` old).
- `stale_after_s` — TTL window, so clients know when to refetch. `0`
  means "not cached at the orient layer" — the value is fetched on
  every request, and downstream caching (if any) is documented in the
  source endpoint.
- `source` — origin class (`git` / `gh` / `fs` / `probe`) for quick
  provenance decisions.
- `cache` — `"hit"` or `"miss"` on this specific call. Sections with
  `stale_after_s: 0` always report `"miss"`.
- `error` — present only when the collector raised or timed out; value
  is the richer `"TypeName: msg"` form. (The section payload itself
  keeps the bare `str(exc)` error string for backwards compatibility.)

The top-level `response.generated_at` is the **oldest** `generated_at`
across sections — a fully cached response labels itself with the
oldest piece of data the caller is looking at. (Before #1309 it was
request time, which lied to consumers about freshness.)

#### Cache bypass: `?fresh=true`

Pass `?fresh=true` to invalidate every `orient_*` cache entry before
gathering. Use it right after a write an agent wants to see
immediately — a just-committed change, a just-filed issue — without
waiting for the longest TTL (120 s for `issues` / `wiki`).

```bash
# Normal call — honours each section's TTL.
curl -s http://localhost:8765/api/orient | jq .meta.git

# After running `git commit` and you want the new HEAD reflected now.
curl -s 'http://localhost:8765/api/orient?fresh=true' | jq .git.head
```

The query only clears this router's cache namespace; unrelated
endpoints keep their caches intact.

#### Failure isolation

Each section runs inside `asyncio.wait_for(..., timeout=5 s)`. That
properly cancels hung **async** coroutines — for us, that is only the
`pipeline` collector.

For sync collectors run via `asyncio.to_thread`, the hard timeout is
advisory: Python threads aren't cancellable once they start running.
Real protection is collector-specific:

| Collector | Inner timeout | Notes |
|---|---|---|
| `git` | 2 s `_run_command` subprocess timeout | hardened |
| `issues` | 2 s `_run_command` subprocess timeout | hardened |
| `pipeline` | async — `asyncio.wait_for` works | hardened |
| `runtime` | none — pure Python / filesystem | fast in practice; an NFS stall could wedge a thread past the 5 s ceiling |
| `delegate` | none — filesystem read of a small JSON | same caveat |
| `wiki` | none — enumerates a small number of files | same caveat |
| `health` | 0.2 s socket + fast `os.access` | hardened |
| `session_hints` | none — `glob(...)[:10]` + short `read_text` | same caveat |

The unwrapped sync collectors are cheap enough in practice that
they've never been observed to block, but they are **not** inside a
real timeout. If the underlying filesystem hangs, those threads will
tie up threadpool slots past the 5 s ceiling. See the comment near
`ORIENT_SECTION_TTLS` in `scripts/api/main.py` for the constraint.

If a section fails or times out, its own payload degrades to a
fallback (e.g. `git: {"error": "..."}`) while every other section
still populates. A single wedged collector never takes down the
whole response — this fixed the incident logged in the first entry
of `docs/monitor-api/cold-start-baseline.md`.

---

## Cold-Start Consolidation — `/api/state/manifest`, `/api/rules`, `/api/session/current`, `/api/comms/inbox` (#1309)

Per the Agent Quick Start above, these four endpoints are the
P1 scaffolding for bootstrapping a fresh agent with a single small
round-trip.

### `GET /api/state/manifest`

Tiny JSON index. Target size < 2 KB. An agent checks the per-component
hashes against its local cache and only refetches what changed.

```json
{
  "generated_at": "2026-04-17T10:15:00Z",
  "rules":   {"hash": "abc...", "url": "/api/rules?format=markdown"},
  "session": {"hash": "def...", "url": "/api/session/current?format=markdown"},
  "orient":  {"url": "/api/orient", "fresh_param": "?fresh=true"},
  "inbox":   {"url_template": "/api/comms/inbox?agent={name}"}
}
```

- `rules.hash` / `session.hash` — sha256 of the Markdown blob each
  endpoint would currently return. An empty string means the source
  wasn't readable at manifest time (logged but not fatal).
- `orient` / `inbox` don't need a manifest hash — `/api/orient`
  already carries per-section `meta` with its own `generated_at` +
  `cache` + `source` fields, and `/api/comms/inbox` is always
  point-in-time.

### `GET /api/rules?format={markdown,json}`

Condensed rule text from `claude_extensions/rules/` (critical +
non-negotiable + workflow, in that order). Source of truth is the
checked-in files so a fresh clone or worktree that hasn't deployed
to `.claude/rules/` still gets correct content.

- `format=markdown` (default) → `text/markdown; charset=utf-8` with
  an `X-Rules-Hash` header. Drop-in for a system prompt.
- `format=json` → `{hash, bytes, sources[], markdown}`. Use this when
  an SDK needs to reconcile the hash against its on-disk cache.

### `GET /api/session/current?format={markdown,json}`

`docs/session-state/current.md` plus a short list of recent handoff
filenames (newest first). Kept intentionally small — the endpoint
answers "what do I need to know RIGHT NOW to keep working", not
"give me the full history".

### `GET /api/comms/inbox?agent={claude,gemini,codex}&limit=10`

Per-agent READ-ONLY view of unread channel deliveries (oldest first).
Replaces the rejected `agent_view=…` param on `/api/orient`. Payload
is compact — one entry per delivery with a 160-char body preview and
provenance (channel, from_agent, dispatched_at, attempt_count).

To actually drain messages, use `ai_agent_bridge` CLI as usual; this
endpoint is for "do I have work waiting?" checks during cold-start.

### Agent-side cache

`scripts/ai_agent_bridge/_monitor_cache.py` — small, pure-stdlib
on-disk cache under `.agent/cache/monitor/`. Round-trip:

```python
from scripts.ai_agent_bridge import _monitor_cache as cache

manifest = httpx.get("http://localhost:8765/api/state/manifest").json()
rules = cache.get("rules", expected_hash=manifest["rules"]["hash"])
if rules is None:
    body = httpx.get("http://localhost:8765" + manifest["rules"]["url"]).text
    cache.put(
        "rules", body,
        body_hash=manifest["rules"]["hash"],
        url=manifest["rules"]["url"],
    )
    rules = body
# `rules` is the condensed rule markdown, either cached or fresh.
```

Override the cache directory with `MONITOR_CACHE_DIR=...` for tests
or alternate checkouts.

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
| Consultation | `/consultation.html` | `/api/consultation/queue`, `/api/consultation/history`, `/api/consultation/metrics` |
| API Docs | `/docs` | FastAPI auto-generated |

---

## Build Event Stream (#1180)

`scripts/build/v6_build.py` now emits monitor-friendly JSON lines to `stdout` alongside the existing human-readable logs. Each event is exactly one line, includes `event` and `ts`, and is flushed immediately with `print(..., flush=True)`.

Example stream:

```json
{"event":"batch_start","ts":"2026-04-10T18:12:03.114582+00:00","level":"a2","total":68}
{"event":"module_start","ts":"2026-04-10T18:12:03.337912+00:00","level":"a2","slug":"a2-bridge"}
{"event":"phase_done","ts":"2026-04-10T18:13:35.481992+00:00","level":"a2","slug":"a2-bridge","phase":"write","duration_s":92.1,"ok":true}
{"event":"review_score","ts":"2026-04-10T18:20:14.228901+00:00","level":"a2","slug":"a2-bridge","round":1,"score":9.4}
{"event":"module_done","ts":"2026-04-10T18:22:27.009541+00:00","level":"a2","slug":"a2-bridge","ok":true,"final_score":9.6,"duration_s":624.0}
{"event":"module_failed","ts":"2026-04-10T18:25:11.442001+00:00","level":"a2","slug":"dative-verbs","phase":"review","error":"Score 6.8/10 < 7.0 — HALTING. Module has critical issues."}
{"event":"batch_done","ts":"2026-04-10T19:03:42.773140+00:00","level":"a2","total":68,"succeeded":65,"failed":3}
```

### How to consume

Conceptual Claude Code `Monitor` usage:

```text
Monitor
  command: .venv/bin/python scripts/build/v6_build.py a2 1 --resume
  stream: stdout
  parse: JSONL lines whose objects contain "event"
  ignore: human-readable log lines that are not JSON
```

Practical rule: read `stdout` line-by-line, parse only lines that begin with `{` and contain a top-level `event` field, and leave the existing human logs untouched for interactive debugging.

### Schema Notes

- All events include `event` and `ts` (`datetime.now(UTC).isoformat()` in UTC).
- `module_start` includes `level` and `slug`.
- `phase_done` includes `level`, `slug`, `phase`, `duration_s`, and `ok`.
- `review_score` includes `level`, `slug`, `round`, and `score`.
- `module_done` includes `level`, `slug`, `ok`, `final_score`, and `duration_s`.
- `module_failed` includes `level`, `slug`, `phase`, and `error`. Error strings are truncated to 200 characters.
- `batch_start` includes `level` and `total`.
- `batch_done` includes `level`, `total`, `succeeded`, and `failed`.

---

## Local Agent Deterministic State — `/api/agent/`

Read-only deterministic endpoints for agent coordination and deep debugging. Used to avoid repeated shell polling (e.g., `rg`, `ps`, `git status`).

### `GET /api/agent/module/{level}/{slug}`
Returns current phase/status, audit status, and key paths for a given module.

### `GET /api/agent/orchestration/{level}/{slug}`
Returns latest prompt files, review rounds, recent dispatch logs, and whether `needs_human_review` is set.

### `GET /api/agent/prompt-summary/{level}/{slug}`
Returns prompt manifest metrics (prompt chars, component sizes) from rewrite-block prompt manifests.

### `GET /api/agent/runtime`
Returns active local build/reviewer/writer processes relevant to the repo in a deterministic shape (`pid`, `state`, `command`).

### `GET /api/agent/worktree`
Returns git status, distinguishing source-code changes from generated artifact churn (e.g., orchestration, status jsons, audit files).
