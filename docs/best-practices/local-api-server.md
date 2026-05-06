# Local API Server

The playground API is a local development service, not a production web
service. It still needs guardrails because the dashboards poll multiple heavy
filesystem and SQLite endpoints from one browser session.

## Current Process Model

`package.json` currently starts uvicorn like this:

```bash
.venv/bin/python -m uvicorn scripts.api.main:app --host 0.0.0.0 --port 8765 --log-config scripts/api/logging.json
```

Findings from the 2026-05-06 stability audit:

- Uvicorn runs with the default single worker.
- No `--limit-concurrency` value is configured.
- No FastAPI middleware-level request concurrency limit is installed.
- `scripts/api/main.py` has a dedicated thread pool only for `/api/orient`
  sync collectors. It does not limit whole-server request concurrency.
- A single blocking request can stall `/api/health` in the current process
  model.

## Recommended Defaults

Do not change the process model without user signoff. The recommended next
configuration to test is:

```bash
.venv/bin/python -m uvicorn scripts.api.main:app \
  --host 127.0.0.1 \
  --port 8765 \
  --workers 2 \
  --limit-concurrency 32 \
  --log-config scripts/api/logging.json
```

Rationale:

- `--workers 2` keeps one dashboard request from monopolizing the only event
  loop process.
- `--limit-concurrency 32` prevents one browser or script from queueing
  unlimited work.
- `127.0.0.1` matches the localhost-only intent in `scripts/api/config.py`.
  Current npm scripts bind to `0.0.0.0`; tighten that separately if remote LAN
  access is not intentionally needed.

Tradeoffs:

- In-memory TTL caches become per-worker, so the first request to each worker
  may pay a cold-cache cost.
- Background mutable operations, especially admin maintenance endpoints, must be
  reviewed before multi-worker is made default.
- `--reload` and `--workers` should not be used together for the normal dev
  workflow.

## Endpoint Design Rules

- Dashboard polling endpoints must be bounded by `limit`, `tail`, `page`, or a
  short TTL cache.
- SQLite tables used by polling paths need indexes matching their `WHERE` and
  `ORDER BY` clauses.
- Endpoints that depend on optional local services, such as Qdrant, must fail
  fast when the service is down.
- Filesystem scans that aggregate all tracks should use summary data when the
  UI only needs counts.
- Log readers should read bounded tails unless the endpoint is explicitly an
  export operation.

## Operational Checks

Use these while exercising dashboards:

```bash
pid=$(pgrep -f 'uvicorn scripts.api.main:app' | head -1)
ps -o rss= -p "$pid"
lsof -p "$pid" | wc -l
curl -s -w '%{time_total}\n' -o /dev/null http://127.0.0.1:8765/api/health
```

Healthy local expectations:

- `/api/health` stays under 200 ms while dashboards are being opened.
- RSS should stabilize after warm caches; it should not climb on every poll.
- File descriptors should remain roughly flat after PDF and SQLite caches warm.
