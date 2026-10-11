# Session streams Monitor API (Sol PR-K)

Read-only Monitor surfaces for epic session streams. **No silent cutover.**

## Fleet Observer (pre-flip)

`/fleet.html` is the consolidated read-only observer for durable fleet-comms
evidence during soak. It does not start work, apply migrations, change process
state, retrieve artifact bodies, or alter cutover authority. File handoffs
remain authoritative in every currently implemented plane mode. Legacy
`/comms.html`, `/channels.html`, `/runtime.html`, and `/acp.html` stay available
until a separately approved retirement.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/fleet/health` | Sanitized mode, health, schema, and pre-flip authority posture |
| GET | `/api/fleet/overview` | Durable requests/messages/reviews/dead-letter/ACP counts |
| GET | `/api/fleet/agents` or `/api/fleet/endpoints` | Configured and durable endpoint metadata; configuration JSON is omitted |
| GET | `/api/fleet/requests`, `/messages`, `/discussions`, `/reviews`, `/dead-letters` | Deterministic, paginated metadata projections with applicable filters |
| GET | `/api/fleet/authority/jobs` | Authority queue metadata with canonical `Source` / `Agent` / `Via`; payload and result artifacts are omitted |
| GET | `/api/fleet/acp/conversations` | Existing body-free ACP conversation and round read model |
| GET | `/api/fleet/activity` | Recent runtime `Source` / `Agent` / `Via` provenance projection |
| GET | `/api/fleet/migrations` | Applied migration metadata only; never applies a migration |

Collection routes accept bounded `limit`/`offset`; applicable routes support
`kind`, `state`, `agent`, `source`, `pr`, `conversation`, `since`, and `until`
filters. Message detail is an explicitly read-only, no-store redacted inline
preview; artifact content is deliberately omitted. Missing databases and
optional tables return deterministic empty availability states, not a write or
bootstrap attempt.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/session-streams/v1/health` | DB reachability / repo identity |
| GET | `/api/session-streams/v1/status/{stream_id}` | Lease/handoff diagnosis (`epic:N`) |
| GET | `/api/session-streams/v1/digest/{stream_id}?limit=20` | Pinned + recent entries |
| GET | `/api/session-streams/v1/dual-write-status` | Handoff file inventory existence |
| GET | `/api/session-streams/v1/drift?dry_run=true` | Projection receipts snapshot (default) |
| GET | `/api/session-streams/v1/plane-continuity` | Bundle board (streams + dual-write + plane pointer) |

Message plane status remains `/api/comms/v1/plane-status`; query it rather than
hard-coding a mode. The default and any authority change remain operator/advisor
gated, and this observer does not perform either action.

Parent: #5512 · stream #4707.

## Relationship Map (/epics-map.html)

`/epics-map.html` is a read-only observer that consumes `GET /api/epics/graph/v1`,
distinct from the `/api/fleet/v1` response envelope (not a fleet-v1 route or new API).
For design context (its historical status header does not reflect current implementation
or deployment status), see [monitor-epics-graph-map.md](../design/monitor-epics-graph-map.md).

### Membership and refresh states

- **Not yet cached:** When an epic membership bucket is missing or the feed has
  `status: "no-cache"` (audit warming or no completed cache), membership displays
  *Not yet cached*.
- **Incomplete membership:** When a membership bucket exists and the feed is not
  no-cache, `membership_complete: false` or nonempty `incomplete_nodes` yields
  explicit incomplete membership (`Open issue membership is incomplete in the cache.`).
- **Unknown membership:** When a bucket exists and no incomplete marker applies,
  missing or null `items` or an invalid, missing, or null `total_open` yields
  explicit unknown membership (`Open issue membership is unknown in the cache.`).
  These states remain distinct from *Not yet cached* rather than sharing identical text.
- **Verified totals:** Complete usable cached membership can display verified zero
  or nonzero totals. Incomplete or unknown membership cannot be interpreted as a zero
  count, and issue counts must not be inferred solely from currently visible rows.
- **Refresh and fetch recovery:** A fetch failure displays the failed-fetch banner
  and "Update failed". A later successful load clears the error and renders refreshed
  data. The existing Refresh button and periodic load can retry (no deployment,
  reconfiguration, or alternate retry policy is implied).
