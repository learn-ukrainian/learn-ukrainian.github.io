# Monitor API Reference

Base URL: `http://localhost:8765`

FastAPI auto-docs: `http://localhost:8765/docs` (Swagger UI)

**Definition authority for the public surface**: `GET /api/contracts/routes` (returns the full `route_contracts` + `page_contracts` registry with `purpose`, `source_of_truth`, `freshness`, `consumers`, `overlap`, `stale_risk`, `recommendation`, `mutates`, `replacement` for every endpoint family and every `dashboards/*.html` page).

This (plus the live `meta` objects returned by many endpoints) is the enforced, machine-readable definition of the declared API surface. The running code in `scripts/api/*.py` is the ultimate behavioral authority. `docs/MONITOR-API.md` is the human narrative. Dashboards are consumers/visualizers that should (and increasingly do) derive from the contracts. See `scripts/api/route_contracts.py` and `tests/test_monitor_route_contracts.py`. The 2026-06-07 Monitor API/UI Audit (#2794) is the origin of this registry.

---

## Optional Context Telemetry Footer

Set `LEARN_UKRAINIAN_TELEMETRY_FOOTER=1` on the Monitor API process to
include live context-window telemetry in cold-start responses. Dispatched
subprocesses set `AGENT_NO_TELEMETRY_FOOTER=1`, which suppresses the
footer even if the parent process has the opt-in variable set.

Token usage comes from the exact transcript path recorded from the official
SessionStart payload. Monitor parses assistant `message.usage` records and sums
`input_tokens`, `cache_read_input_tokens`, and
`cache_creation_input_tokens` from the latest assistant turn; output tokens are
not current-context usage. The previous assistant usage record supplies the
per-turn delta, and the assistant usage record count supplies the monotonic turn
number. Capacity, profile, trust, and mismatch metadata come from the canonical
private per-session record. An official statusline
`context_window.context_window_size` observation wins over the declared launcher
profile. Unknown capacity remains `null`; Monitor never fabricates a 1M or
auto-compaction denominator.

Text responses append a tail footer:

```text
[ctx: 187K (+22K this turn), tier: base, 13K to premium, turn: 47]
```

JSON responses add a top-level `_telemetry` object instead of changing
the response text. Pass `?session=<uuid>` or header `X-Session-Id`
(query wins) on telemetry-bearing endpoints (`/api/orient`, `/api/rules`,
`/api/session/current`, `/api/state/manifest`).

- Session hit → `_telemetry.ctx` reflects that session's transcript;
  `caller_match: true`.
- No session param → `_telemetry.ctx` is `null`; `_telemetry.newest_transcript`
  is a compatibility diagnostic only and must never be treated as the caller's
  context state.
- Session miss → `reason: "session-transcript-not-found"`.

`LEARN_UKRAINIAN_TRANSCRIPT_PATH` / `CLAUDE_TRANSCRIPT_PATH` remain a
server-global test hook for the no-session newest-transcript path only.

```json
{
  "_telemetry": {
    "ctx": 187000,
    "prev_ctx": 165000,
    "delta": 22000,
    "tier": "base",
    "distance_tokens": 13000,
    "distance_label": "to premium",
    "turn": 47,
    "source": "transcript-jsonl",
    "declared_model": "gpt-5.6-sol",
    "observed_model": "gpt-5.6-sol",
    "declared_context_limit": 372000,
    "actual_context_limit": 360000,
    "selected_profile": "sol_lead",
    "percentage": 51.94,
    "provenance": "statusline.context_window.context_window_size",
    "mismatch": true,
    "profile_trusted": true,
    "profile_resolution_reason": "explicit-profile"
  }
}
```

When telemetry is enabled, `/api/rules` and `/api/session/current`
continue to expose `X-Rules-Hash` / `X-Session-Hash` for the underlying
stable markdown, but dynamic telemetry responses do not use `304 Not
Modified` or strong `ETag` headers. With telemetry disabled, existing
ETag and cache semantics are unchanged.

---

## Agent Quick Start

**Recommended cold-start sequence (profile-aware):**

```bash
# SessionStart writes the official id into CLAUDE_ENV_FILE for later Bash calls.
# If it is unavailable, telemetry must stay caller-unmatched; never guess from the newest transcript.
S="${LEARN_UKRAINIAN_SESSION_ID:-}"

# 1. Tiny session-bound index: hashes, identity, and trusted context telemetry.
curl -s "http://localhost:8765/api/state/manifest?session=$S"

# 2. Follow the SessionStart capsule's Orientation URL.
# Compact profiles use lean=true; certified full profiles omit it.
if [ "${LEARN_UKRAINIAN_COLD_START_PROFILE:-compact}" = "compact" ]; then
  curl -s "http://localhost:8765/api/orient?lean=true&session=$S"
else
  curl -s "http://localhost:8765/api/orient?session=$S"
fi

# 3. Pull live operational signals used by the lane.
curl -s "http://localhost:8765/api/delegate/active"
curl -s "http://localhost:8765/api/worktrees"
curl -s "http://localhost:8765/api/comms/inbox?agent=claude-infra"

# 4. Do NOT fetch the full rules payload at cold start. Fetch it on demand before
# the first dispatch, and again only when the manifest rules hash changes.
```

Agents should keep a small on-disk cache keyed by manifest hash
(`.agent/cache/monitor/*.body`). When the manifest's hash matches
what you cached, skip the payload fetch entirely — the bytes are
still authoritative. A ready-to-use helper lives at
``scripts/ai_agent_bridge/_monitor_cache.py``; the client SDK
(``scripts/ai_agent_bridge/monitor_client.py``) will wrap this in P3.

---

### Custom log formatters

Access log formats that reference uvicorn-only fields like
`%(client_addr)s`, `%(request_line)s`, or `%(status_code)s` must declare
`"()": "uvicorn.logging.AccessFormatter"` in `scripts/api/logging.json`.
Python's default `logging.Formatter` does not populate those fields and
will raise during response logging. See uvicorn's
[`AccessFormatter`](https://github.com/encode/uvicorn/blob/master/uvicorn/logging.py)
implementation for the field mapping.

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
  "pipeline": {"summary": {"totals": {"total": 1778}}},
  "runtime": {"agents": ["claude", "gemini", "codex"]},
  "delegate": {"active_count": 2},
  "wiki": {"by_track": {"hist": {"compiled": 15, "total": 140, "pct": 10.7}}},
  "health": {"api": true, "mcp_rag": false, "sources_db": true, "message_broker": true}
}
```

For live agent progress from the channel bridge, Monitor can consume the event stream directly: `Monitor(command=".venv/bin/python scripts/ai_agent_bridge/__main__.py channel watch <thread_id> --follow --event-stream", ...)`. The watch command replays historical events first, then keeps streaming line-buffered JSONL for `reply_started`, `heartbeat`, `reply_complete`, and delivery outcome events as the inbox worker updates the thread.

Related MCP source lookup: `mcp__sources__search_external` searches the chunked external articles corpus with channel/register/decolonization filters and optional track-aware reranking.

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

Freshness:
- Cached for 60 seconds.
- Pass `?fresh=true` to bypass the state-summary cache.
- `meta.generated_at`, `meta.source`, `meta.cache`, and
  `meta.stale_after_s` describe the snapshot. `cache: "hit"` means the
  payload is still within the TTL; clients should still surface
  `audit_stale` when present because that is source-artifact staleness,
  not API-cache staleness.

Returns per-track counts:
- `total` — module catalog count from `curriculum.yaml`, falling back to
  `plans/{track}/*.yaml` when the manifest has no module list
- `module_source` — `curriculum.yaml` or `plans-fallback`
- `research_done` — modules with research complete in pipeline state or
  a discovered research/dossier file
- `dossier_done` — discovered dossier/research files, including
  `docs/research/{track}/{slug}.md` seminar dossiers
- `dossier_docs` / `dossier_curriculum` — split by dossier source
- `content_done` — modules with lesson content complete in pipeline state
- `generated_md` — generated curriculum markdown exists on disk
- `published_mdx` — Starlight MDX exists under
  `starlight/src/content/docs/{track}/{slug}.mdx`
- `audit_passing` — `status/*.json` overall == "pass"
- `audit_stale` — status cache exists but is older than the module source
- `final_review_done` — `review/*-final-review.md` exists
- `prompt_reviewed` — `/prompt-review` done (`audit/*-prompt-review.md` exists)
- `content_reviewed` — `/content-review` done (`audit/*-content-review.md` exists)
- `profile` — "core" | "seminar" | "pro"
- `is_seminar` — true for tracks listed in `SEMINAR_TRACK_IDS`

Sample response:
```json
{
  "generated_at": "2026-02-19T15:30:06Z",
  "meta": {
    "generated_at": "2026-02-19T15:30:06Z",
    "source": "fs:plans+orchestration+artifacts+research",
    "cache": "miss",
    "stale_after_s": 60,
    "stale": false
  },
  "tracks": {
    "istorio": {
      "total": 136, "profile": "seminar", "is_seminar": true,
      "module_source": "curriculum.yaml",
      "research_done": 26, "dossier_done": 26,
      "generated_md": 0, "published_mdx": 136,
      "content_done": 0, "audit_passing": 0, "final_review_done": 0
    },
    "hist": {
      "total": 140, "profile": "seminar",
      "research_done": 140, "content_done": 5,
      "audit_passing": 4, "final_review_done": 4
    }
  },
  "totals": { "total": 1778, "research_done": 400, "published_mdx": 220, ... }
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
  "track": "a1",
  "profile": "core",
  "is_seminar": false,
  "meta": {"source": "fs:orchestration+audit+research", "cache": "miss", "stale_after_s": 60},
  "modules": [
    {
      "num": 1, "slug": "sounds-letters-and-hello",
      "pipeline_version": "v6",
      "phases": {
        "check": {"status": "complete", "ts": "2026-03-20T14:00:00Z"},
        "research": {"status": "complete", "ts": "2026-03-20T14:01:00Z"},
        "write": {"status": "complete", "ts": "2026-03-20T14:05:00Z"},
        "publish": {"status": "pending"}
      },
      "audit": "pass",
      "words": 1500,
      "word_target": 1200,
      "research_score": null,
      "generated_md": true,
      "published_mdx": true,
      "dossier": {"exists": false, "source": null}
    }
  ]
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

### `GET /api/state/module-range/{track}`

Deterministic committed-file status for a module number range. Use this for
questions like "what is left for B2 M32-M41?" without spending model context on
manual repo scans.

With `MONITOR_API_BASE` set to the monitor host:

```bash
curl -s "${MONITOR_API_BASE}/api/state/module-range/b2?start=32&end=41" | .venv/bin/python -m json.tool
```

The endpoint checks committed source files, generated MDX, and durable score
docs. It intentionally does not depend on `status/*.json`, `audit/*-review.md`,
or local orchestration artifacts because those are runtime state and are not
committed.

Returns:
```json
{
  "track": "b2",
  "range": {"start": 32, "end": 41},
  "total": 10,
  "complete": 10,
  "content_complete": 10,
  "score_persisted": 10,
  "incomplete": 0,
  "remaining": [],
  "modules": [
    {
      "num": 32,
      "slug": "phonetic-stylistic-devices",
      "status": "complete",
      "complete": true,
      "content_complete": true,
      "score_persisted": true,
      "files": {"module": true, "activities": true, "vocabulary": true, "mdx": true},
      "missing_files": [],
      "missing": []
    }
  ],
  "deterministic": true,
  "source": "fs:plans+content+mdx+score-docs"
}
```

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
- `enriched` — whether the plan records versioned changes in `plan_fixes`
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

Which plans are enriched per track. Checks for a non-empty `plan_fixes` list in the plan YAML; tracked `.yaml.bak` files are legacy artifacts and no longer count.

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

### `GET /api/state/scores/{track}` and `GET /api/state/scores/{track}/{slug}`

Per-module **status + LLM-QG quality scores** — the live view for watching the
seminar quality-gate prototype converge to ≥8
(`docs/folk-epic/seminar-quality-gate-design.md`). Source of truth:
`curriculum/l2-uk-en/<track>/<slug>/llm_qg.json` (`.aggregate` + `.dimensions`)
plus the audit status cache. Always fresh (small reads, no TTL cache) so polling
during a build reflects the latest correction round.

```bash
curl -s http://localhost:8765/api/state/scores/folk | python3 -m json.tool
curl -s http://localhost:8765/api/state/scores/folk/kalendarna-obriadovist-zvychai | python3 -m json.tool
```

Track response: `{track, count, scored, modules[], meta}`. Each module:

```json
{
  "track": "folk", "num": 4, "slug": "kalendarna-obriadovist-zvychai",
  "status": "not_run", "word_count": null, "word_target": null,
  "scored": true,
  "aggregate": {
    "verdict": "REVISE", "terminal_verdict": "PASS",
    "min_score": 7.0, "min_dim": "pedagogical",
    "failing_dims": ["pedagogical", "engagement", "tone"], "warning_dims": [...]
  },
  "dimensions": {"pedagogical": 7.0, "naturalness": 10.0, "decolonization": 10.0,
                 "engagement": 7.0, "tone": 7.5}
}
```

- A module not yet QG-scored returns `scored: false`, `aggregate: null`, `dimensions: {}`.
- `dimensions` is read generically, so a newly-added dim (e.g. `beauty` once the
  seminar gate Phase A lands) appears automatically with no endpoint change.
- Unknown track or slug → `404`.

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

**Canonical path (P1+P3 since #1309).** One manifest call + only the
components whose hash changed:

```bash
# 1. Index of hashes. Tiny.
curl -s http://localhost:8765/api/state/manifest

# 2. Core context. Only fetch if manifest hash differs from local cache.
curl -s http://localhost:8765/api/rules?format=markdown
curl -s 'http://localhost:8765/api/session/current?agent=claude'

# 3. Fresh project state.
curl -s http://localhost:8765/api/orient

# 4. Unread messages for this agent.
curl -s "http://localhost:8765/api/comms/inbox?agent=claude"
```

Python agents use the SDK (caching + ETag round-trip built in):

```python
from ai_agent_bridge.monitor_client import MonitorClient
boot = MonitorClient().bootstrap()
# boot["rules"].body   — ready to drop into a system prompt
# boot["session"].body — current-task summary
# boot[...].source     — "cache" | "not-modified" | "network"
```

Both `/api/rules` and `/api/session/current` honour
`If-None-Match: "<hash>"` and reply `304 Not Modified` when the hash
matches — repeat cold-starts with an up-to-date local cache pay
near-zero bytes for these payloads.

### Deep-dive queries (run as needed, not on every boot)

```bash
# Ship-ready modules across every track.
curl -s http://localhost:8765/api/artifacts/ship-ready | python3 -m json.tool

# Public site reachability + freshness.
curl -s http://localhost:8765/api/site/health | python3 -m json.tool

# What's ready to build next (Phase A done, B not started)
curl -s http://localhost:8765/api/state/ready-to-build

# Critical issues to fix
curl -s "http://localhost:8765/api/state/issues?severity=critical"
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
    {"name": "claude", "binary": "claude"},
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

### `GET /api/runtime/headroom?agent=codex&model=gpt-5.5`

Quota gate for one `(agent, model)` pair.

```json
{
  "agent": "codex",
  "model": "gpt-5.5",
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

## Tool Timing Telemetry — `/api/telemetry/`

### `POST /api/telemetry/tool-timings`

Ingests one Claude Code `PostToolUse` or `PostToolUseFailure` timing event.
The local hook sends these events asynchronously, so Monitor API outages do
not block tool execution.

```bash
curl -s -X POST http://localhost:8765/api/telemetry/tool-timings \
  -H 'Content-Type: application/json' \
  -d '{
    "ts": "2026-04-25T00:12:34.567Z",
    "tool_name": "Bash",
    "duration_ms": 142,
    "tool_use_id": "toolu_123",
    "session_id": "sess-1",
    "failed": false
  }'
```

Response:
```json
{"ok": true}
```

Validation notes:
- `duration_ms` must be `>= 0`
- `tool_name`, `duration_ms`, and `ts` are required
- malformed payloads return FastAPI/Pydantic `422`

### `GET /api/telemetry/tool-timings?window=1h&tool=Bash`

Returns per-tool counts, latency percentiles, mean duration, and failure
counts for a bounded time window. Supported windows: `5m`, `15m`, `1h`,
`6h`, `24h`, `7d`. Results are sorted by `count` descending.

```bash
curl -s 'http://localhost:8765/api/telemetry/tool-timings?window=1h' | jq
curl -s 'http://localhost:8765/api/telemetry/tool-timings?window=24h&tool=Bash' | jq
```

Response:
```json
[
  {
    "tool_name": "Bash",
    "count": 124,
    "p50_ms": 85,
    "p95_ms": 412,
    "p99_ms": 1850,
    "mean_ms": 142,
    "failure_count": 3
  }
]
```

## Module Build Token Telemetry — `/api/telemetry/module-builds`

Persists module-build token telemetry as local runtime state. This is the
canonical place to record whether a build used a swarm or ran solo. The data
is stored in `data/telemetry/module_builds.db`; the database is ignored by git
and must not be included in content/code PRs.

### `POST /api/telemetry/module-builds`

Upserts one build-run telemetry record. `swarm_used`, `swarm_note`, `level`,
`slug`, and `source` are required. Re-posting the same `run_id` updates the
run and replaces its participant rows.

```bash
curl -s -X POST http://localhost:8765/api/telemetry/module-builds \
  -H 'Content-Type: application/json' \
  -d '{
    "run_id": "b1-m13-pr3148",
    "level": "b1",
    "slug": "alternation-consonants-verbs",
    "branch": "codex/b1-m13-alternation-verbs",
    "commit_sha": "7066d5f506",
    "pr_number": 3148,
    "status": "merged",
    "swarm_used": true,
    "swarm_label": "thin",
    "swarm_note": "Used bounded reviewers and validation runner.",
    "wall_clock_minutes": 30.5,
    "source": "codex-final",
    "participants": [
      {
        "role": "main",
        "agent": "codex",
        "model": "gpt-5.5",
        "effort": "xhigh",
        "prompt_tokens": 120000,
        "response_tokens": 18000,
        "token_source": "estimated"
      }
    ]
  }'
```

Response:
```json
{"ok": true, "run_id": "b1-m13-pr3148"}
```

### `GET /api/telemetry/module-builds`

Returns recent build-run telemetry. Supported filters: `level`, `slug`,
`swarm_used`, and `limit`.

```bash
curl -s 'http://localhost:8765/api/telemetry/module-builds?level=b1&swarm_used=true'
```

Response:
```json
{
  "generated_at": "2026-06-14T12:34:56Z",
  "records_total": 1,
  "totals": {
    "runs": 1,
    "swarm_runs": 1,
    "solo_runs": 0,
    "participants": 1,
    "prompt_tokens": 120000,
    "response_tokens": 18000,
    "total_tokens": 138000,
    "cost_usd_est": 0.0
  },
  "runs": [
    {
      "run_id": "b1-m13-pr3148",
      "level": "b1",
      "slug": "alternation-consonants-verbs",
      "swarm_used": true,
      "swarm_note": "Used bounded reviewers and validation runner.",
      "participants": [
        {
          "role": "main",
          "agent": "codex",
          "model": "gpt-5.5",
          "effort": "xhigh",
          "prompt_tokens": 120000,
          "response_tokens": 18000,
          "total_tokens": 138000,
          "token_source": "estimated"
        }
      ]
    }
  ]
}
```

### `GET /api/telemetry/module-builds/{level}/{slug}`

Returns telemetry for one module, with `latest` set to the newest matching
run or `null` when no record exists.

```bash
curl -s 'http://localhost:8765/api/telemetry/module-builds/b1/alternation-consonants-verbs'
```

## Delegation — `/api/delegate/`

### `GET /api/delegate/tasks?status=&limit=50`

List delegate task state files with derived age and zombie detection.
Delegate task status only becomes `rate_limited` when the runtime adapter sees
an actual provider rate-limit failure signal; for Claude's text-mode runtime
that means a failed call with a rate-limit phrase on `stderr`, not a successful
response whose body happens to mention rate limits.

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

### `GET /api/delegate/active`

List delegate tasks that are currently running or spawning with a live PID.
Use this, or `delegate.py status-or-fail <task-id>`, before reporting async
task state.

```json
{
  "total": 1,
  "tasks": [
    {"task_id": "issue-1166", "agent": "codex", "status": "running", "age_s": 45.0}
  ]
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

## Research registry — `/api/knowledge` (ADR-011)

Bounded, task-scoped discovery of the Project Research Registry
(`docs/references/research-registry.yaml`). Gated behind the default-off
`research_registry` kill switch; while disabled every surface below reproduces
exact pre-registry behavior. **Pointers are automatic; record bodies are strictly
on demand** — no cold-start, orient, bootstrap, dispatch, or pipeline path ever
fetches a digest body automatically.

### `GET /api/knowledge/manifest`

Filtered, pointer-only projection for a task context. Pure **AND** matcher over
`role`, `task_family`, `track`, and repeatable `owned_path` (every dimension a
record specifies must match; a task missing a required dimension does not match).
Disabled → `{"enabled":false,"records":[]}`. Carries its own strong context-scoped
`ETag`; `If-None-Match` gives a bodyless `304`. Top-5 / ≤1.5 KB; no digest bodies.

### `GET /api/knowledge/cold-start?role=<role>`

Role-only pointer projection from the opt-in `cold_start_roles` announce list —
**never** the AND matcher above. A bare role has no `task_family`/`track`/
`owned_path`, so the AND matcher would fail closed on those missing dimensions
even for a record that explicitly opted in via `cold_start_roles`; this endpoint
exists precisely so cold start/bootstrap has a role-only path that doesn't hit
that trap. Same shape, caps, and ETag/304 semantics as `/manifest`.

### `GET /api/knowledge/record/{id}`

One validated compact digest body as `text/markdown` with an honest per-record
`ETag` (its `content_hash`). Generic `404` for disabled/unknown/malformed/traversal
id, an invalid/drifted/`private-local` record, or an over-budget body.

- `task=<task-id>` — **optional** consumption attribution. A served `200` or a
  cache-backed `304` fetched under a validated, still-active delegate task emits
  one privacy-safe consumption telemetry event. Attribution is **response-invariant**:
  a missing/malformed/unknown/finished task changes nothing an unattributed caller
  sees and never reveals whether a task exists — it simply emits no event. A `404`
  is never a consumption. A `304` only counts when the same task already has
  evidence of a matching prior `200` for that record, persisted into the task's own
  delegate state (no third store) — a caller can't manufacture a consumption event
  by replaying the record's public `content_hash` as `If-None-Match` without ever
  having fetched the body.

### `GET /api/knowledge/monitor?window_days=30` (ADR-011 P4)

Registry observability — makes silent rot visible. **Ungated by the discovery kill
switch**: governance must survive a serving disable, so this endpoint answers even
when `research_registry.enabled` is false (it reports `discovery_enabled` so the
caller knows the serving state). Deterministic (identical registry + telemetry +
membership cache + wall-clock → identical metrics); **no ETag / conditional
caching**. `window_days` is `1..365` (default 30); out-of-range → `422`.

Built from the **raw registry and P1 per-record helpers** — never
`load_runtime_safe()`, which returns nothing on any semantic error and would hide
the very records rot makes invalid. Sections:

- `lifecycle` — `status`, `eligible_total` (non-superseded), raw state `counts`
  (proposed/adopted/deferred/superseded/invalid/total), and id lists `stale`
  (hash-drift), `orphaned` (structurally un-owned), `ownership_unverified` (plausible
  owner not confirmable against a fresh issue-stream cache — never falsely orphaned),
  `deferred`, `superseded`. `ownership_cache` ∈ `fresh`/`missing`.
- `adoption` — `adopted`, `effective_adopted` (adopted + current hash + resolvable
  consumer), `eligible_total`, and `rate` (`adopted ÷ eligible_total`, **null** on a
  zero denominator).
- `dead_consumers` — `dead` (a deterministic typed resolver proves the consumer
  dangles) vs `unverified` (`issue`/`corpus` consumers, which have no offline
  resolver) — issue/corpus is never falsely reported dead.
- `consumption` — from the P3 telemetry JSONL (`batch_state/telemetry/events/
  YYYY-MM-DD.jsonl`; no new store), bounded file/byte scan, fail-soft. Counts raw
  events and **distinct `(task_id, research_id)` pairs** (deduped across 200/304),
  `surfaced_never_consumed` (first surface in window, no consumption at/after it, past
  a 1-hour grace — newer pairs are `pending`), and a per-record aggregate. Unknown
  research ids get aggregate counts only (their strings are never echoed).
  `malformed_lines`/`unreadable_files`/`bytes_scanned`/`partial` report scan health.

**Privacy allowlist:** only registry ids and counts — never task ids, run/session/
source, role, track, owned paths, titles, summaries, source urls, prompts, or digest
bodies. Broken registry/cache/event lines degrade a section, never `500`.

**Strict adoption gate (CLI, separate from serving):**
`.venv/bin/python scripts/audit/check_research_registry.py --strict-adoption
[--max-age 3600]` re-validates ownership + issue consumers against a **fresh,
offline** `issue_stream_audit.json` membership cache (produced by a separate live
auditor run — the gate never touches the network). Missing/stale/unreadable cache
**fails closed** (exit 2). The default `--check` is unchanged: offline, non-network,
and never reads the membership cache.

### Cold start / bootstrap

- `GET /api/orient?role=<role>` — pointer-only `research` section from the role's
  opt-in `cold_start_roles` announcements (never the AND matcher, never a body).
  No top-level `fetch` field — the fetch endpoint is the documented, well-known
  `GET /api/knowledge/record/{id}` above, and omitting it keeps the whole envelope
  inside the same ≤1.5 KB budget the selector already caps pointers to.
- Monitor client SDK: `MonitorClient.bootstrap()` is unchanged (`rules` + `session`
  only). `bootstrap(role=...)` with **no** other context dimension routes through
  `MonitorClient.cold_start(role=..., consumer=...)` — the role-only
  `/api/knowledge/cold-start` path, never the AND manifest. `bootstrap(role=...,
  task_family=...)` (or `track=`/`owned_paths=`) routes through
  `MonitorClient.research(role=…, task_family=…, track=…, owned_paths=…,
  consumer=…)` — the full AND-matched `/api/knowledge/manifest` path. Both cache
  under a fingerprint over the bounded `consumer` plus the canonical context (one
  full, untruncated SHA-256; never a raw path/role/consumer string in the cache
  filename) and return **only the added/changed pointers** since the last call for
  that key — the on-disk cache still stores the complete latest projection so the
  diff has something to compare against. cold (nothing cached) → the first `200`
  returns everything; warm+unchanged → `304` returns a valid empty projection
  (zero changed); warm+changed → the new `200` is diffed against the cached
  snapshot by canonical pointer content (id/state/content_hash/routing) and only
  the changed/new records come back. Both methods fail soft to an empty component
  on any transport or cache read/write failure — an optional boundary that must
  never crash `bootstrap()`.

### Dispatch injection

`delegate.py dispatch` accepts explicit, namespaced context flags — never inferred
from the prompt, agent, provider, or branch: `--research-role`,
`--research-task-family`, `--research-track`, and repeatable `--research-owned-path`.
When set (and the registry is enabled) the dispatch prompt gains a bounded,
pointer-only block plus an on-demand fetch instruction, and the task state persists
**only** the pointer ids, filtered ETag, dropped ids, and context fingerprint (never
raw owned paths, digest/source/prompt text, role, or task family).

### Consumption telemetry (privacy contract)

Two distinct central-emitter events (`scripts/telemetry/emit.py`; no new store):
`research_pointer_surfaced` (a pointer was shown) and `research_record_consumed`
(a body was actually fetched under a validated active task). Surfaced ≠ consumed.
Payload allowlist is exactly `{task_id, research_id, surface, status}` on top of the
emitter envelope — never a digest body, title, summary, source URL, prompt, role,
task family, track, owned paths, or context fingerprint.

## Rollover Registry — `/api/rollovers`

### `GET /api/rollovers`

Read-only fleet audit of versioned rollover records. The response classifies
valid and corrupt packets, reports live-pending counts, and includes exact IDs,
human-readable task titles, age, last successful boundary, reconciliation
state, blocking or terminal reason, and the next safe action. HTTP never
exposes a mutation path.

Optional query parameters are `agent`, `source_thread_id`,
`replacement_thread_id`, `lineage_id`, `rollover_id`, and `stale_hours`.
Supplying any exact selector switches to one-record projection mode. Multiple
selectors are ANDed; no match returns `404`, and an ambiguous match returns
`409` with candidates instead of selecting one.

```bash
curl -s "${MONITOR_API_BASE}/api/rollovers" | jq .
curl -s "${MONITOR_API_BASE}/api/rollovers?agent=codex&lineage_id=<lineage-id>&rollover_id=<rollover-id>" | jq .
```

The `rollovers` section in `/api/orient` is the compact cold-start projection:
counts plus live pending or confirmed-but-incompletely-cleaned entries. Use this
endpoint for complete evidence and registry validation errors. Use
`scripts/orchestration/rollover_registry_cli.py` for evidence-gated exact
reconciliation or maintenance.

## Orientation — `/api/orient`

### `GET /api/orient`

One-call agent orientation: git, issues, pipeline, runtime, delegate, rollovers,
wiki, health, and session hints.

Query params:

- `fresh=true` — invalidate orient-layer caches before gathering (see below).
- `sections=git,runtime` — comma-separated subset of section keys to
  collect. Valid keys: `git`, `issues`, `pipeline`, `runtime`,
  `delegate`, `bridge_pending`, `rollovers`, `wiki`, `governance`, `health`,
  `session_hints`. Unknown keys return `400`. Omitted = full payload
  (back-compat). Skipped sections are not collected and are omitted
  from both the top-level payload and `meta`.
- `role=<role>` — **opt-in** ADR-011 P3 cold-start research (see
  *Research registry* below). Absent → the response is byte-identical to
  the pre-P3 orient (no `research` key). Present + registry enabled → a
  pointer-only `research` section (≤5 records / ≤1.5 KB; bodies fetched
  on demand, never here). Computed fresh per request and never stored in
  the shared `orient_*` cache, so two roles cannot contaminate each other.
- `session=<uuid>` or header `X-Session-Id` — per-session context
  telemetry when `LEARN_UKRAINIAN_TELEMETRY_FOOTER=1` (query wins).

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

When `LEARN_UKRAINIAN_TELEMETRY_FOOTER=1`, the JSON response includes
top-level `_telemetry` with the same context-window fields documented
above.

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
| `rollovers` | 15 | `fs` | compact fleet rollover counts plus actionable pending or incompletely cleaned entries |
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
| `issues` | 5 s `_run_command` subprocess timeout | hardened |
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

If the `issues` collector returns `issues_error` or the GitHub
subsection times out, run
`.venv/bin/python scripts/orchestration/issue_stream_audit.py --json`
to refresh the issue-stream hygiene cache instead of retrying the full
orient bundle blindly.

---

## Bounded Research Discovery — `/api/knowledge/*` (ADR-011 P2 #4982, P3 #4992)

Task-scoped, pointer-only, hash-addressed access to the Project Research
Registry (`docs/references/research-registry.yaml` + the compact digests
under `docs/references/research-digests/`). Reuses the P1 validator
primitives (`scripts/audit/check_research_registry.py`) for the schema,
canonical digest projection/hash, drift, and path safety — it does not
re-implement any of them. **P2 exposed the bare `/manifest` + `/record/{id}`
surface with no automatic caller. P3 (this doc's *Research registry* section
above) wired it into real task discovery: `GET /api/orient?role=`,
`MonitorClient.bootstrap()`/`cold_start()`/`research()`, and
`delegate.py dispatch --research-*` all surface pointers automatically now —
record bodies remain strictly on-demand throughout.**

### Kill switch (default OFF, instant rollback)

The whole surface is gated by `research_registry.enabled`, resolved
**dynamically per request**, most-specific layer wins:

1. env `LEARN_UK_RESEARCH_REGISTRY_ENABLED` — strict `true/false`, `1/0`,
   `yes/no`, `on/off` (case-insensitive);
2. live gitignored file `<LIVE_REPO_ROOT>/.runtime/api/research-registry.json`
   with shape `{"research_registry":{"enabled":false}}`;
3. compiled default `false`.

An invalid higher-precedence value (bad env spelling, malformed/unreadable
live file) logs a warning and resolves to `false` — it never falls through
to a lower, possibly-enabled layer. Flipping the live file is an immediate,
in-place enable/disable — no revert PR, no redeploy. Loading is **fail-open**:
while disabled the registry is never parsed; enabled with a missing/malformed/
invalid registry yields an empty surface and a logged warning, never a 500. A
drifted or provenance-broken record is excluded individually; healthy records
keep routing.

### `GET /api/knowledge/manifest?role=&task_family=&track=&owned_path=`

Filtered, task-scoped **pointers** for the given context (no digest bodies).
Query context: single `role`, `task_family`, `track`, and repeated
`owned_path`. Matching is a strict **AND** across every dimension the record
declares — a dimension omitted from the record is a wildcard; a dimension the
record requires but the request lacks fails the match (so a `core`-track
record scoped to `difficulty-gate` will **not** surface for a `core`-track
`module-build` task). `owned_path` intersects the record's globs by
deterministic case-sensitive glob. **No task context → zero records** (never
"show all"). Repeated/duplicate/reordered query values are normalized so
semantically identical contexts produce byte-identical output and ETag.

- Disabled → HTTP 200 `{"enabled":false,"records":[]}` (loader never invoked).
- Enabled → `{"enabled":true,"records":[…]}`, each record an allowlisted
  pointer `{"id","state","content_hash","routing"}` — never summary, digest
  path/body, source URL, ownership, timestamps, the global hash, or telemetry.
- Bounded: **top 5 records** (sorted by record id) and **≤ 1536 serialized
  UTF-8 bytes**. If the byte cap drops records, every dropped id is logged —
  never a silent truncation.
- Strong **ETag** over the exact response bytes for this context (not the
  global hash, not `generated_at`). This is what keeps an unrelated warm
  client at zero research tokens even while the global manifest hash churns:
  after any record edit flips the global hash, a context whose filtered set is
  unchanged still gets a bodyless `304` on `If-None-Match`, while a context
  routing to the edited record gets `200` and a new ETag. Honors strong/weak/
  `*`/comma-list `If-None-Match` (shared `_matches_etag` semantics).
- Request caps: ≤ 64 `owned_path` values, each ≤ 512 chars; `role`/
  `task_family`/`track` ≤ 128 chars. Excess → `422`.

### `GET /api/knowledge/record/{record_id}`

The one validated compact digest **body** as `text/markdown; charset=utf-8`,
capped at **4096 serialized UTF-8 bytes**. The P1 `content_hash` is the ETag
for the exact normalized body (an honest ETag: if the returned bytes ever
differed from the hashed projection, the ETag is computed over the response
bytes instead). Unchanged `If-None-Match` → bodyless `304`; a
changed/reconciled digest → `200` with a new ETag.

Lookup resolves only through validated registry ids — never a direct path
join. A generic **404** covers a disabled feature, an unknown/malformed/
traversal id, an invalid/drifted/`private-local` record, an unsafe digest
path, or an over-budget body (Starlette answers encoded traversal with `403`
before the route). No status or message leaks which of these applied.

### Budgets (normative = serialized UTF-8 bytes; tokens = `ceil(bytes/2)`)

| Surface | Budget |
|---|---|
| Total `/api/state/manifest` | < 2048 bytes |
| `research` manifest component | ≤ 512 bytes |
| `/api/knowledge/manifest` filtered projection | ≤ 5 records and ≤ 1536 bytes |
| `/api/knowledge/cold-start` role-only projection | ≤ 5 records and ≤ 1536 bytes |
| `GET /api/orient?role=` `research` envelope (final emitted bytes) | ≤ 1536 bytes |
| One `/api/knowledge/record/{id}` body | ≤ 4096 bytes |
| Automatic selected-body fetch (P3 consumer) | ≤ 8192 bytes total |

Any runtime budget drop logs the affected record ids, never digest bodies.

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
  "session": {"hash": "def...", "url": "/api/session/current?agent=orchestrator&format=markdown"},
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
- `research` — **optional, ADR-011 P2.** Present only when the research
  registry kill switch is on *and* the registry is exposable; a compact
  `{"hash": "<64-hex>", "url": "/api/knowledge/manifest"}` (≤ 512 bytes,
  no summary/note/timestamp). `hash` is a single global hash over the
  routing-relevant projection of the whole registry (states, content
  hashes, per-record validity, and routing metadata — never digest
  bodies or YAML formatting). Any record edit flips it for all clients.
  With the switch off or on a missing/malformed registry the key is
  **absent**, so pre-P2 clients are byte-for-byte unaffected. See
  *Bounded Research Discovery* below.
- When `LEARN_UKRAINIAN_TELEMETRY_FOOTER=1`, this JSON response also
  includes top-level `_telemetry` derived from transcript JSONL. It
  never appends text to the manifest body.

### `GET /api/rules?format={markdown,json}`

Condensed rule text from `claude_extensions/rules/` (critical +
non-negotiable + workflow, in that order). Source of truth is the
checked-in files so a fresh clone or worktree that hasn't deployed
to `.claude/rules/` still gets correct content.

- `format=markdown` (default) → `text/markdown; charset=utf-8` with
  an `X-Rules-Hash` header. Drop-in for a system prompt. With telemetry
  enabled, a context footer is appended after the markdown body.
- `format=json` → `{hash, bytes, sources[], markdown}`. Use this when
  an SDK needs to reconcile the hash against its on-disk cache. With
  telemetry enabled, the response also includes top-level `_telemetry`.

### `GET /api/session/current?agent={name}&format={markdown,json}`

Agent-specific session handoff plus a short list of recent handoff
filenames (newest first). The default agent is `orchestrator`; use
`agent=codex`, `agent=claude`, or `agent=gemini` to read that agent's
mapped handoff file. The Codex orchestrator handoff lives at
`docs/session-state/codex-orchestrator-handoff.md`; other durable agent
handoffs normally use `docs/session-state/current.<agent>.md`. Codex UI
rollovers read `docs/session-state/current.orchestrator.md`, which is a
thin pointer to the durable orchestrator handoff above. Pass
`agent=router` only when you need the small compatibility router at
`docs/session-state/current.md`.

Kept intentionally small — the endpoint answers "what do I need to know RIGHT
NOW to keep working", not "give me the full history".

With telemetry enabled, `format=markdown` appends the context footer and
`format=json` adds top-level `_telemetry`.

### `GET /api/comms/inbox?agent={claude,gemini,codex}&limit=10`

Per-agent READ-ONLY view of unread channel deliveries (oldest first).
Replaces the rejected `agent_view=…` param on `/api/orient`. Payload
is compact — one entry per delivery with a 160-char body preview and
provenance (channel, from_agent, dispatched_at, attempt_count).

To actually drain messages, use `ai_agent_bridge` CLI as usual; this
endpoint is for "do I have work waiting?" checks during cold-start.

### Agent-side cache + SDK (P3)

`scripts/ai_agent_bridge/_monitor_cache.py` — small, pure-stdlib
on-disk cache under `.agent/cache/monitor/`. Low-level API for
callers that want fine-grained control:

```python
from scripts.ai_agent_bridge import _monitor_cache as cache

body = cache.get("rules", expected_hash="...")
# ... fetch if None ...
cache.put("rules", body, body_hash="...", url="/api/rules?format=markdown")
```

For most callers, **use the SDK**: `scripts/ai_agent_bridge/monitor_client.py`.

```python
# Requires ``scripts/`` on sys.path. Tests + any caller launched via
# ``.venv/bin/python`` from the repo root already have it (see
# tests/conftest.py). Standalone scripts should add it at the top:
#     import sys; from pathlib import Path
#     sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from ai_agent_bridge.monitor_client import MonitorClient

client = MonitorClient()  # defaults to http://localhost:8765
boot = client.bootstrap()

rules_md = boot["rules"].body       # ready to drop into a system prompt
session_md = boot["session"].body   # current-task summary

# Role-only cold start: routes through cold_start_roles, never the AND matcher.
boot = client.bootstrap(role="quality")
research_body = boot["research"].body   # changed/new pointers only (see below)

# boot[...].source tells you why you have these bytes:
#   "cache"         — no network call; local hash matched
#   "not-modified"  — server replied 304; research bodies are a valid EMPTY
#                      pointer projection (zero changed), other components reuse
#                      the cached body verbatim
#   "network"       — first fetch or new ETag, body downloaded
#   "error:*"       — degraded (transport/cache failure, disabled, or 4xx/5xx);
#                      body is empty, never raises
```

Use `bootstrap(role="...")` only when the session already has a known assigned
functional role. `bootstrap()` remains the generic or genuinely role-unknown
startup path and deliberately has no hidden default role, so it remains
pointer-free.

`MonitorClient.cold_start(role=...)` and `MonitorClient.research(role=..., task_family=..., track=..., owned_paths=...)`
are also callable directly (`bootstrap()` picks between them based on which
dimensions are given — see *Cold start / bootstrap* above).

The SDK handles:

- Fetching `/api/state/manifest` once.
- Checking the local cache against the manifest's content hash.
- Sending `If-None-Match` on cache-miss so the server can return
  `304 Not Modified` (empty body, reuse cache).
- Storing the fresh body + ETag on 200.

### ETag support on cachable endpoints

Both `/api/rules` and `/api/session/current` honour
`If-None-Match: "<hash>"`. A matching hash returns `304 Not Modified`
with no body — the SDK skips a multi-KB download in that case.
Also accepts `W/"<hash>"` (weak ETag) and `*`. The ETag value is the
same sha256 advertised in the manifest, so the manifest hash IS the
If-None-Match token.

Override the cache directory with `MONITOR_CACHE_DIR=...` for tests
or alternate checkouts.

### Deprecated endpoints (P3)

These keep working but carry `X-Deprecated: true` + `X-Deprecated-Use`
+ `Warning: 299` response headers. Migrate to the canonical endpoints
noted in the header; the deprecated handlers will be removed in a
future cleanup.

| Deprecated | Replacement |
|---|---|
| `GET /api/blue/live-status` | `GET /api/state/build-status` |
| `GET /api/comms/live-activity` | `GET /api/state/build-status` + `GET /api/build/events` stream |

The deprecated routes still work for existing dashboards and scripts
that haven't been updated — the contract is "log a warning and
migrate", not "break suddenly".

---

## Content-Delivery-to-Production — `/api/artifacts/*`, `/api/site/*` (#1309)

Two routers with an **explicit boundary**:

- `/api/artifacts/*` answers "are the internal artifacts ready to
  ship?" — MDX exists, frontmatter valid, word target met, audit
  passes, final review approved, plan not changed after build.
- `/api/site/*` answers "is the public site actually up?" —
  reachability, freshness, recent GH Pages deploys.

Codex flagged in review that mixing these would muddy the contract;
the split keeps each router's purpose obvious.

### `GET /api/artifacts/{track}/{slug}`

Per-module gate snapshot. Returns `ship_ready` (bool — true iff every
named gate is green) plus the individual gates so clients can surface
exactly which check failed.

```json
{
  "track": "a1", "slug": "hello-who-are-you",
  "gates": {
    "content_exists":    true,
    "frontmatter_valid": true,
    "word_target_met":   true,
    "audit_pass":        true,
    "final_review_pass": true,
    "plan_fresh":        true
  },
  "ship_ready": true,
  "legacy_shippable": true,
  "audit": {"status": "pass", "word_count": 1230, "word_target": 1200, ...},
  "review": {"score": 9.4, "verdict": "PASS"},
  "final_review": {"exists": true, "verdict": "PASS", ...}
}
```

`legacy_shippable` is the older audit+review combined check (still
used by existing dashboards). `ship_ready` is the strict new check
that also covers frontmatter + final review + plan freshness.

### `GET /api/artifacts/ship-ready[?track=a1]`

Aggregate list — walks every plan and returns the modules whose
every gate is green. Narrow to one track with `?track=`.

```json
{
  "tracks_scanned": ["a1", "a2", "b1"],
  "modules_inspected": 155,
  "ship_ready_count": 27,
  "ship_ready": [
    {"track": "a1", "slug": "hello-who-are-you", "review_score": 9.4,
     "word_count": 1230, "word_target": 1200}
  ]
}
```

### `GET /api/site/health`

Public-site reachability + freshness. Every field degrades gracefully
— if the network is down or `gh` isn't available, the response still
returns 200 with per-field `error` strings rather than failing the
whole check.

```json
{
  "public_url": "https://learn-ukrainian.github.io/",
  "reachable": true,
  "canaries": [{"url": ".../", "status": 200, "elapsed_ms": 42}],
  "last_astro_build": {"built": true, "last_build_at": "...", "age_seconds": 3600},
  "last_deploy_commit": {"sha": "abc123", "committed_at": "..."},
  "sitemap": {"exists": true, "age_seconds": 3650}
}
```

Override the target URL with `LEARN_UK_SITE_URL=<url>` for preview
deployments.

### `GET /api/site/deployments[?limit=5]`

Recent `pages-build-deployment` workflow runs via `gh run list`.
Returns `{runs: [...], error?: "..."}`. An empty `runs` list with
an `error` string means the CLI call failed (not authenticated, not
installed, etc.) — check the string and retry, don't retry blindly.

---

## Codex-Requested Follow-ups (#1313)

After the P0-P3 work shipped, Codex asked for ten deterministic
scoped views. Nine of those ten landed as follow-up commits on the
same PR (#10 agent_help was already covered by P1 manifest + rules
+ session). All follow below under their final URLs.

### Range status — `GET /api/state/range/{track}?start=N&end=M`

Compact per-module table for one slice. One call replaces N
``/api/state/pipeline`` reads plus cross-referencing. Ideal for
overnight batch runs.

```json
{
  "track": "a1", "start": 1, "end": 5, "count": 5,
  "modules": [
    {"num": 1, "slug": "hello", "phase": "review", "phase_status": "in_progress",
     "worker": "claude", "audit": "pass", "review_score": 9.4,
     "words": 1300, "word_target": 1200, "blocker": null,
     "pipeline_version": "v6", "needs_rebuild": false}
  ]
}
```

`blocker` is derived on the server from the module's state:

| Value | Meaning |
|---|---|
| `"failed:<phase>"` | a phase status is `"failed"` in state.json |
| `"audit_fail"` | audit verdict is `"fail"` but no failed phase |
| `"gate:<name>"` | audit has `blocking_issues` and the first names a gate |
| `"audit_issue"` | audit has `blocking_issues` but no specific gate |
| `null` | nothing known to be blocking |

### Worktree registry — `GET /api/worktrees`

Every active git worktree with branch, dirty/clean, change-type
summary, last commit. All subprocesses bounded at 2 s and wrapped to
never 500.

```json
{
  "count": 2,
  "worktrees": [
    {"path": "/.../learn-ukrainian", "branch": "main", "head": "abc1234",
     "is_primary": true, "dirty": false, "change_types": [],
     "last_commit": {"sha": "abc1234", "committed_at": "...", "subject": "..."}}
  ]
}
```

### Git hygiene — `GET /api/git/hygiene`

Classifies current working-tree dirty files into actionable cleanup
buckets. Exemption paths are loaded from
`docs/best-practices/git-hygiene.md`; exempt files do not count toward
`dirty_total`.

| Endpoint | Purpose |
|---|---|
| `GET /api/git/hygiene` | Dirty-file taxonomy, remediation hints, and hygiene health |

```bash
curl -s http://localhost:8765/api/git/hygiene | python3 -m json.tool
```

Response:

```json
{
  "generated_at": "2026-04-24T06:50:00Z",
  "dirty_total": 6,
  "exempt": {"wiki": 1, "draft_tickets": 1, "gitignored": 0, "other": 0, "total": 2},
  "buckets": {
    "stale_behind_main": {"count": 1, "files": ["stale.py"]},
    "real_wip": {"count": 1, "files": ["wip.py"]},
    "untracked_unexempted": {"count": 1, "files": ["scratch/todo.txt"]},
    "intentional_deletions": {
      "count": 3,
      "files": ["feature/remove/a.txt", "feature/remove/b.txt", "feature/remove/c.txt"],
      "pattern": "feature/remove/*"
    }
  },
  "suggestions": [
    {
      "action": "restore_to_head",
      "rationale": "pre-merge content; main moved past these files",
      "files": ["stale.py"],
      "command": "git checkout HEAD -- stale.py"
    },
    {
      "action": "stash_wip",
      "rationale": "local definitions or decorators need a stash or commit, not restore",
      "files": ["wip.py"],
      "command": "git stash push -m git-hygiene-wip -- wip.py"
    },
    {
      "action": "gitignore_pattern",
      "pattern": "scratch/",
      "rationale": "untracked files are neither ignored nor policy-exempt",
      "files": ["scratch/todo.txt"]
    },
    {
      "action": "commit_deletions",
      "rationale": "coherent deletion cluster with no modified or untracked files in the same subtree",
      "pattern": "feature/remove/*",
      "files": ["feature/remove/a.txt", "feature/remove/b.txt", "feature/remove/c.txt"]
    }
  ],
  "health": "dirty",
  "performance_ms": 42.5
}
```

### Git cleanup (`GET /api/git/cleanup`)

Read-only git rot report for stale local branches and worktrees that are
safe candidates for manual removal. The endpoint only classifies state;
it never runs `git branch -d`, `git worktree remove`, `rm`, or any other
destructive cleanup command.

```bash
curl -s http://localhost:8765/api/git/cleanup | python3 -m json.tool
```

Response:

```json
{
  "stale_branches": [
    {
      "name": "codex/1234-old-branch",
      "upstream_gone": true,
      "fully_merged_to_main": false,
      "last_commit_sha": "abc1234",
      "last_commit_date": "2026-04-12T14:22:00Z",
      "committer": "Codex Worker"
    }
  ],
  "removable_worktrees": [
    {
      "path": ".worktrees/dispatch/codex/foo",
      "branch": "codex/foo",
      "clean": true,
      "upstream_gone": true,
      "fully_merged_to_main": false,
      "disk_bytes": 240000000,
      "reason": "upstream gone, working tree clean"
    }
  ],
  "protected_worktrees": [
    {
      "path": "/Users/you/projects/learn-ukrainian",
      "branch": "main",
      "reason": "primary checkout"
    },
    {
      "path": ".worktrees/codex-interactive",
      "branch": "(detached HEAD)",
      "reason": "interactive session (contains 'interactive' in path)"
    }
  ],
  "total_reclaimable_bytes": 1234567890,
  "computed_at": "2026-04-25T00:15:30Z",
  "performance_ms": 342.5
}
```

Branch classification:

- A local branch is stale when its upstream tracking branch is gone, or
  when all commits are already present on `main`.
- `main`, `origin/*`, and branches currently checked out in any worktree
  are never returned in `stale_branches`.

Worktree classification:

- A worktree is removable only when its branch is merged to `main` or
  has a gone upstream, `git status --porcelain` is empty in that
  worktree, and no protection rule applies.
- Protected worktrees are the primary checkout, paths containing
  `interactive`, and active dispatch worktrees under
  `.worktrees/dispatch/**` whose `batch_state/tasks/*.json` state has
  `status: "running"`.
- `disk_bytes` comes from portable `du -sk` output. If `du` cannot read
  a worktree, `disk_bytes` is `null` and the total ignores that entry.

### Force-preview — `GET /api/artifacts/{track}/{slug}/force-preview`

Exact list of files `v7_build.py {track} {slug} --worktree --force` would delete,
classified by category. **Never** deletes anything.

```json
{
  "track": "a1", "slug": "hello",
  "count": 12, "total_bytes": 234567,
  "would_remove": [
    {"path": "curriculum/l2-uk-en/a1/hello.md", "category": "content",
     "is_dir": false, "size_bytes": 8432, "reason": "module markdown"}
  ],
  "preserved": ["plans/a1/hello.yaml",
                "curriculum/l2-uk-en/a1/orchestration/hello/index.md",
                "curriculum/l2-uk-en/a1/orchestration/hello/friction.yaml"]
}
```

Categories: `content` / `activities` / `vocabulary` / `review` /
`audit` / `status` / `research` / `orchestration` / `published`.

### Slug-keyed module state — `GET /api/state/module/{track}/slug/{slug}`

Slug-keyed compact alias of `/api/state/module/{track}/{num}`. Default
response omits the verbose `phases` dict; pass `?verbose=true` for the
full payload.

```json
{
  "track": "a1", "slug": "hello", "num": 1,
  "phase": "review", "last_successful": "write",
  "pipeline_version": "v6", "needs_rebuild": false,
  "audit": {"status": "pass", "word_count": 1300, "word_target": 1200},
  "review": {"score": 9.4, "verdict": "PASS"},
  "final_review": {"exists": true, "verdict": "PASS"},
  "shippable": true, "blocking_issues": [],
  "retry_count": 0, "worker": "claude"
}
```

### Classified file manifest — `GET /api/artifacts/{track}/{slug}/files`

Four buckets: `source_of_truth`, `generated`, `published`, `stale`.
An artifact lands in `stale` when its mtime predates the plan YAML —
source has moved on, rebuild recommended. Complements `force-preview`
(destructive) with the read-only classification view.

### Review snapshot — `GET /api/artifacts/{track}/{slug}/review-snapshot`

Main review + style review + per-file `empty_findings_flag` (high
score with zero findings — the reviewer-gaming pattern). Also an
`any_empty_findings_flag` at the top level for batch filtering.

### Drift check — `GET /api/artifacts/{track}/{slug}/drift`

Cross-checks `state.json`, audit status, final-review verdict, content
file on disk, published MDX on disk. Reports named `drift` kinds:
`publish_mdx_missing`, `mdx_without_state`,
`audit_passes_without_content`, `final_review_without_content`,
`content_without_audit`, `state_unreadable`. Returns `in_sync: true`
when everything agrees.

### Issues map — `GET /api/issues/map?limit=50`

Open issues grouped by label category. Extracts `superseded-by: #N`
and `merged-in: PR #N` references from issue bodies so queue
management stops being manual. Categories:
`infrastructure` / `pipeline` / `content` / `wiki` / `agent` /
`priority:high` / `other`.

### Runtime auth snapshot — `GET /api/runtime/auth`

Per-agent auth mode. For Gemini: resolved `auto` / `subscription` /
`api` mode + `auth_mode_raw_valid` (did `GEMINI_AUTH_MODE` hold one
of the accepted values?) + `auth_mode_raw_length` (length only) +
whether `GEMINI_API_KEY` / `GOOGLE_API_KEY` is set + whether
`~/.gemini/oauth_creds.json` exists. For Claude / Codex: which env
var would provide the key (if any).

**Never echoes env-var values** — only presence booleans, source env
name, and the resolved enum. A test pins this contract so a future
change can't accidentally leak a value through the raw passthrough
that used to exist here (the `auth_mode_raw` string from an earlier
revision of this endpoint was removed per reviewer BLOCKER on
#1312 pre-merge).

---

## UI Pages

| Page | URL | Data source |
|------|-----|-------------|
| Home | `/` | `/api/dashboard/overview`, `/api/state/summary?fresh=true`, `/api/comms/batch-progress` |
| Audit Dashboard | `/audit-dashboard.html` | `/api/dashboard/overview`, `/api/dashboard/track/{id}` |
| Progress | `/progress.html` | `/api/state/summary?fresh=true`, `/api/state/pipeline-versions?fresh=true`, `/api/state/pipeline/{track}?fresh=true` |
| Agent Comms | `/comms.html` | `/api/build/events/active`, `/api/build/events/recent`, `/api/comms/batch-progress`, `/api/comms/zombies`, `/api/comms/messages`, `/api/comms/stats` |
| Quality | `/quality.html` | `/api/state/research-coverage`, `/api/state/review-coverage`, `/api/state/issues`, `/api/state/weak-points` |
| Track Health | `/track-health.html` | `/api/state/track-health/{track}`, `/api/state/build-status`, `/api/state/enrichment-status` |
| Curriculum | `/curriculum-dashboard.html` | `/api/dashboard/overview` |
| Consultation | `/consultation.html` | `/api/consultation/queue`, `/api/consultation/history`, `/api/consultation/metrics` |
| API Docs | `/docs` | FastAPI auto-generated |

Dashboard consolidation status:
- `/progress.html` is the canonical fast visual overview for current
  track/module state. It surfaces cache freshness, dossier coverage,
  generated/published state, stale audit warnings, and next-action hints.
- `/audit-dashboard.html` remains because it drills into QA gate
  breakdowns through `/api/dashboard/track/{id}`.
- `/quality.html` remains because it is a fix queue over research,
  reviews, issues, and weak-point endpoints rather than a status overview.
- `/track-health.html` remains because it uses build-status and
  enrichment endpoints that are not shown in the progress overview.
- `/curriculum-dashboard.html` remains for plan/meta inspection. It is
  overlapping, but deleting it would remove a distinct module-inspection
  workflow.
- No page is removed in this slice; the safe consolidation is to make
  `/progress.html` trustworthy and leave the specialized pages explicit.

---

## Build Event Stream (#1180)

`scripts/build/v7_build.py` now emits monitor-friendly JSON lines to `stdout` alongside the existing human-readable logs. Each event is exactly one line, includes `event` and `ts`, and is flushed immediately with `print(..., flush=True)`.

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
  command: .venv/bin/python scripts/build/v7_build.py a2 m01-bridge --worktree --resume
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

### V7 Linear JSONL Events

The V7 linear pipeline emits additive prompt-adherence telemetry to the same
JSONL stream. Existing V6 event shapes stay unchanged.

- `writer_cot_emit`: one event per contracted section. Includes `writer`,
  `module`, `section`, `block_present`, `block_chars`, and `fields_filled`.
- `writer_tool_call`: one event per bounded writer MCP tool call. Includes
  `writer`, `module`, `section`, `tool`, `args_summary`, `result_summary`,
  and `duration_ms`.
- `writer_end_gate`: one event per writer phase. Includes `writer`, `module`,
  `gate_present`, `gate_actions`, and `removed_count`.
- `phase_writer_summary`: writer roll-up. Includes `writer`, `module`,
  `sections_total`, `sections_with_cot`, `tool_calls_total`,
  `verify_words_calls`, `end_gate_fired`, and `removed_via_gate`.
- `reviewer_dim_evidence`: one event per reviewer dimension. Includes
  `reviewer`, `module`, `writer_under_review`, `dim`, `evidence_quotes`,
  `rubric_mapping`, and `score`.
- `reviewer_audit_call`: one event per reviewer Tier-1 audit call. Includes
  `reviewer`, `module`, `writer_under_review`, `dim`, `audit_type`, `tool`,
  `items_checked`, `items_failed`, and `flags_raised`.
- `phase_review_summary`: reviewer roll-up. Includes `reviewer`, `module`,
  `writer_under_review`, `dims_scored`, `dims_with_evidence`,
  `audit_calls_total`, `flags_raised_total`, `min_dim_score`, and
  `weighted_score`.

V7 payloads are intentionally bounded: evidence quote arrays are capped at
five entries, `rubric_mapping` is capped at 500 characters, and tool events
store summaries rather than full arguments or raw tool results.

- `reviewer_override` (#1321) fires once per deterministic-dimension override applied during a review round. Includes `level`, `slug`, `dim` (int), `name`, `claim` (one of `word_count_below_target`, `activity_count_undercounted`), `reviewer_value` (what the reviewer claimed), `deterministic_value` (what the pipeline measured), and `delta_score` (points added to that dim).
- `reviewer_saved_by_override` (#1321) fires at most once per review round, only when the cumulative override(s) lifted the module from `passed=False` to `passed=True`. Includes `level`, `slug`, `old_score`, `new_score`.
- `review_regression_prevented` (#1320) fires when the review-heal loop detects that a post-pass round dropped below the snapshotted score by more than `_REGRESSION_BAND` (0.2) and reverts to the snapshot. Includes `level`, `slug`, `regressed_round`, `regressed_score`, `best_round`, `best_score`.

---

## Documentation Artifacts — `/artifacts/` (#1814)

> **Mounted prefix:** `/artifacts` (NOT `/api/artifacts` and NOT `/files`).
> Browser-friendly: `localhost:8765/artifacts/docs/session-state/2026-05-09-late-night-gemini-tools-cwd-fix.html` renders the HTML directly. The `/api/` prefix is reserved for JSON endpoints.

Local API serving for project documentation, reports, and session state. Supports
both directory listings and raw file serving (HTML, MD, assets).

### `GET /artifacts/`

List all approved documentation roots. Returns a list of root IDs and their
filesystem status.

```json
{
  "roots": [
    {"id": "audit", "path": "audit", "exists": true},
    {"id": "docs/session-state", "path": "docs/session-state", "exists": true},
    ...
  ]
}
```

### `GET /artifacts/{path:path}`

Serve a documentation artifact or list a subdirectory.

- **Directory listing**: If the path resolves to a directory, returns a JSON
  object with root metadata and a list of items (name, size, mtime).
- **File serving**: If the path resolves to a file, serves the raw content with
  appropriate MIME type and `Cache-Control: max-age=300`.

**Approved Roots:**
- `audit/`
- `docs/session-state/`
- `docs/handoffs/`
- `docs/reports/`
- `docs/architecture/`
- `docs/best-practices/`
- `docs/decisions/`
- `docs/references/external/`

**Supported Extensions:**
- `.html`, `.md`, `.txt`
- `.png`, `.jpg`, `.jpeg`, `.svg`, `.webp`
- `.pdf`

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

---

## Startup Import Pinning & Correctness Guarantee

To prevent runtime crashes and version skew caused by git mutations (e.g., switching branches or pulling changes on the primary checkout while the API server is running), the Monitor API enforces **startup import pinning**.

### Pinning Guarantee & Scope
- **Post-Successful-Startup Guarantee:** Upon startup, the FastAPI lifespan (`preload_all()`) eagerly imports the entire static import closure of the API, along with all dynamic adapter modules (walked from `scripts/agent_runtime/adapters/`) and dynamic migration scripts. This ensures that all required Python modules are resident in `sys.modules` from the start.
- **Parent Process Only:** The import pinning guarantee is strictly scoped to the parent API process.
- **Subprocess Design Intent:** Subprocess children spawned by the API (such as git, gh, or agent dispatches) execute code from the current working tree by design, using standard loose text/JSON contracts.
- **Guard Rails:** The guarantee is continuously verified via an AST-walking guard test (`tests/api/test_import_pinning.py`). The test asserts that all nested imports inside `scripts/api/` are registered in the preload lists (`PRELOAD_MODULES` or `OPTIONAL_MODULES`) or marked with an explicit inline comment: `# lazy-ok: <reason>`. Any unregistered dynamic imports or unregistered dynamic loaders will cause the test suite to fail.

### PR-B Symlink & Snapshot Follow-Up
In the follow-up PR-B release, this guarantee is reinforced by serving the API from immutable, release-dir code snapshots (with staging→rename symlink promotion), ensuring complete separation between running code and the live repository data.
