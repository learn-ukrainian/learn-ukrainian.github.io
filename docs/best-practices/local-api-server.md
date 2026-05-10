# Local API Server

The playground API is a local development service, not a production web
service. It still needs guardrails because the dashboards poll multiple heavy
filesystem and SQLite endpoints from one browser session.

## Process Model

Normal API commands launch uvicorn in dev-reload mode:

```bash
.venv/bin/python -m uvicorn scripts.api.main:app \
  --host 0.0.0.0 \
  --port 8765 \
  --reload \
  --log-config scripts/api/logging.json
```

`npm run api` and `npm run api:bg` use this shape. `npm run api:reload`
is an alias for backward compatibility.

The FastAPI app also installs `scripts/api/resilience.py` middleware:

- `API_REQUEST_TIMEOUT_S` defaults to 10 seconds and returns 504 on timeout.
- `API_MAX_CONCURRENCY` defaults to 16 in-flight requests per worker and
  returns 503 with `Retry-After` when saturated.
- `API_SLOW_REQUEST_MS` defaults to 500 ms and logs slow HTTP requests.
- `API_SLOW_SQL_MS` defaults to 500 ms and logs slow SQLite calls made through
  `connect_sqlite()`.
- `/api/health` exposes in-flight, saturation, timeout, slow-request, and
  slow-SQL telemetry.

## Architecture Overview

Routers are mounted by domain from `scripts/api/main.py`:

- Dashboard state: `state_router.py`, `dashboard_router.py`,
  `dashboard_helpers.py`, `state_*`.
- Agent communication: `comms_router.py`, with legacy broker routes marked
  deprecated and channel routes as the current surface.
- Operational dashboards: `admin_router.py`, `runtime_router.py`,
  `build_events_router.py`, `delegate_router.py`, `cost_router.py`.
- Content tooling: `wiki_router.py`, `images_router.py`, `rag_router.py`,
  `consultation_router.py`, `artifacts_router.py`.
- Agent bootstrap: `rules_router.py`, `session_router.py`, `/api/orient`, and
  `/api/state/manifest`.
- Older team dashboards and compatibility endpoints: `blue_router.py`,
  `gold_router.py`, `agent_router.py`, `reviewer_ghosts_router.py`.

The full route and playground consumer inventory lives in
`docs/api-endpoint-consumer-map-2026-05-06.md`.

## Endpoint Design Rules

- Dashboard polling endpoints must be bounded by `limit`, `tail`, `page`, or a
  short TTL cache.
- SQLite tables used by polling paths need indexes matching their `WHERE` and
  `ORDER BY` clauses.
- Use `connect_sqlite()` from `scripts/api/resilience.py` for SQLite inside
  API code so slow queries are visible in logs and `/api/health`.
- Endpoints that depend on optional local services, such as Qdrant, must fail
  fast when the service is down.
- Filesystem scans that aggregate all tracks should use summary data when the
  UI only needs counts.
- Log readers should read bounded tails unless the endpoint is explicitly an
  export operation.
- Heavy sync work inside async handlers should move to `asyncio.to_thread()` or
  a sync FastAPI handler so it runs in the threadpool.

## Adding An Endpoint

1. Add the route to the domain router that already owns the data. Avoid adding
   new router files unless the endpoint is a new operational domain.
2. Decide whether the endpoint is for polling, user action, or export. Polling
   endpoints need a bound and a smoke-test budget under 500 ms.
3. Use structured parsers and existing helper APIs rather than ad hoc string
   scans.
4. If the endpoint reads SQLite, use `connect_sqlite()` and add an index for the
   query shape before wiring a dashboard to it.
5. Add a focused test for failure behavior and include the endpoint in
   `tests/test_playground_api_stability.py` if a playground loads it.
6. Update `docs/MONITOR-API.md` only after the route is stable enough for
   external agent use.

## Deprecating An Endpoint

1. Prove the endpoint has no active consumer with `rg` across `playgrounds/`,
   `scripts/`, and `docs/`.
2. Mark the FastAPI route `deprecated=True` and add a response header or docs
   pointer to the replacement when compatibility clients still exist.
3. Remove or hide the playground consumer first; do not delete a router section
   while a dashboard still calls it.
4. Add the candidate to the endpoint consumer map with LOC, deletion risk, and
   required user signoff.
5. Delete in a separate PR after the user approves the specific file or route
   group.

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
