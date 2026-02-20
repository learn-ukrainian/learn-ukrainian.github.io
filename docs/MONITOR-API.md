# Monitor API Reference

Base URL: `http://localhost:8765`

FastAPI auto-docs: `http://localhost:8765/docs`

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
    "c1-hist": {
      "total": 136, "profile": "seminar",
      "research_done": 26, "content_done": 0,
      "audit_passing": 0, "final_review_done": 0
    },
    "b2-hist": {
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
curl -s http://localhost:8765/api/state/pipeline/c1-hist | python3 -m json.tool
curl -s http://localhost:8765/api/state/pipeline/b2-hist | python3 -m json.tool
```

Returns:
```json
{
  "track": "b2-hist",
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

### `GET /api/state/ready-to-build[?track=x]`

Modules where Phase A is complete but Phase B hasn't started. **The build queue.**

```bash
# All tracks
curl -s http://localhost:8765/api/state/ready-to-build | python3 -m json.tool

# Specific track
curl -s "http://localhost:8765/api/state/ready-to-build?track=b2-hist" | python3 -m json.tool
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
curl -s "http://localhost:8765/api/state/issues?track=b2-hist" | python3 -m json.tool
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
curl -s http://localhost:8765/api/dashboard/track/b2-hist

# Deep module inspection (plan + meta + gates + orchestration)
curl -s http://localhost:8765/api/gold/inspect/b2-hist/trypillian-civilization

# Research coverage (detailed per-module scores)
curl -s http://localhost:8765/api/dashboard/research
```

### Communications
```bash
# Message broker status + recent messages
curl -s http://localhost:8765/api/dashboard/comms
```

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
| Home | `/` | `/api/dashboard/overview`, `/api/state/summary` |
| Audit Dashboard | `/audit-dashboard.html` | `/api/blue/live-status`, `/api/dashboard/track/{id}` |
| Progress | `/progress.html` | `/api/state/summary`, `/api/state/pipeline/{track}` |
| Quality | `/quality.html` | `/api/state/research-coverage`, `/api/state/review-coverage`, `/api/state/issues`, `/api/state/weak-points` |
| Curriculum | `/curriculum-dashboard.html` | `/api/dashboard/overview` |
| API Docs | `/docs` | FastAPI auto-generated |
