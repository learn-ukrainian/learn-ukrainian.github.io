# Work control plane API (unified browser projection)

Read-only projection of work for the local Monitor. GitHub Issues/PRs remain the
source of truth. There is no Linear source of truth.

Completion vocabulary:

- Public foundation (server + schema): **`FOUNDATION_COMPLETE`**
- Browser-local dual-source product slice: **`UNIFIED_COMPLETE`** means dual-source
  fetch/validation/merge in the browser, public-safe saved views, independent
  degradation, docs, deterministic unit and headless-browser proofs, ready PR,
  exact-head cross-family approval, and green repository checks. It does **not**
  mean mutation, hosted deployment, or private proxying.

Base URL (public Monitor): `http://127.0.0.1:8765` (prefer loopback IP).

## Endpoints (public server)

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/work/v1/projection` | Normalized attention list, work items, source envelopes, denominator, cache age |
| `GET` | `/api/work/v1/next` | Stream-scoped actionable pick list for orchestrators (#6880) |
| `GET` | `/api/work/v1/capabilities` | Schema digest, budgets, class-4 endpoint freeze, private-source seam |
| `GET` | `/api/work/v1/health` | Cheap Work surface liveness |

### `GET /api/work/v1/next` (next-queue, #6880)

Machine contract for "what should this lane do next" — a driver never needs the
586-row projection dump. Params: `stream=<stream key>` (required; keys from
`scripts/config/issue_streams.yaml`, unknown keys 400 with `valid_streams`) and
`limit` (default 7, max 25). Unambiguous fleet-taxonomy area aliases are
accepted and echoed (`?stream=infra` → `stream: "infra-harness"` +
`requested_stream: "infra"`, via the same `fleet_taxonomy.yaml` resolver the
session hooks use); ambiguous or unknown selectors still fail closed (#6984).

- **Pick list is stream-scoped** (operator addendum on #6880): only actionable
  rows whose `projections.stream.streams` membership includes the requested
  stream. Body-homed `pending_native` tickets keep that honest status but DO
  carry their epic-body-derived membership, so they are pick items for the
  lane that owns them while native sub-issue migration lags (#6984). Items
  with no stream membership (orphans, PRs, tasks, pending-native with no
  derivable lane) are NEVER pick items — they appear as
  `digest.unscoped_actionable_count`, and pending-native ones are additionally
  named with a reason in `digest.excluded_pending_native`.
- **Actionable** is the server-side SSOT `scripts/work/attention.py::is_actionable`
  (OFF_TRACK/AT_RISK always; otherwise `safe_next_action.code` outside the
  `INSPECT_UNKNOWN`/`OPEN_GITHUB`/`NONE` deny list). `dashboards/work.html`
  mirrors it in JS under a parity contract test.
- **Digest, never a queue**: `other_streams.actionable_counts_by_stream`
  (counts only), `other_streams.top_blockers` (≤3 repo-wide OFF_TRACK
  pointers), `unscoped_actionable_count`, `excluded_pending_native`
  (`count` + ≤25 items with `streams` and `reason`).
- **Warm cache only**: serves strictly from the unfiltered projection cache
  (single-flight, #6861). Cold → wire body
  `503 {"error": "building", "retry_after_s": 3}` (no FastAPI `detail`
  wrapper — machine-consumable as documented) and never triggers a build;
  expired-but-present entries are served with an honest `cache_age_s` while
  the shared background refresh runs, until age exceeds `max_stale_s` (300s)
  → `503 {"error": "stale", "cache_age_s", "max_stale_s", "retry_after_s"}`.
  The background build is bounded (`NEXT_BUILD_TIMEOUT_S`, 20s) so a hung
  collector frees the single-flight slot and the next caller's refresh can
  succeed instead of wedging the lane at 503 stale (#6984).
  An unreadable `issue_streams.yaml` registry →
  `503 {"error": "registry_unavailable", "retry_after_s"}` (fail closed —
  never 200 + empty queue for a stream typo). Warm calls measure ~1ms
  locally.
- **Stream-name allowlist**: derive-time membership and any pre-set
  `open_stream_membership` are re-validated against registry keys before they
  enter the public projection (#6890).
- **Deterministic**: rank is the projection's `attention_rank` with a
  `work_id` tie-break; two calls over an unchanged projection return identical
  order.

UI: [`/work.html`](../../dashboards/work.html) — Evidence rail attention list
(Monitor paper language).

## Browser-local private adapter boundary

Only browser JavaScript in `dashboards/work.html` may fetch the fixed constant:

`http://127.0.0.1:8769/v1/projection`

Invariants:

1. The public server never imports, reads, proxies, configures, or logs the
   private adapter. The public capability seam remains
   `available: false` / `not_configured` until the **browser** admits a private
   document.
2. The private endpoint is not configurable: no query parameter, input,
   environment, local/session storage, cookie, fragment, or server setting. It
   never enters the page URL, saved views, HTML links, DOM status text as a raw
   URL, errors, or telemetry.
3. Both browser requests are GET-only with `Accept: application/json`,
   `credentials: "omit"`, `cache: "no-store"`, and `referrerPolicy: "no-referrer"`.
   The private request has an exact 5-second `AbortController` budget and no
   query string (including on Refresh). Public Refresh may use `fresh=true`.
   User filters are applied **locally after merge** and are never sent to the
   private adapter.
4. Sources settle independently (`Promise.allSettled`). Private availability is
   never a prerequisite for public rendering or vice versa. Raw
   fetch/parse/validation exception text is never displayed or logged.
5. Private admission is closed-world against `work-projection.v1` plus the frozen
   schema digest `89fb9c1eec41baaa00a328d456340111163c1e3ab899cd7baa15e284fff65bde`
   and public schema commit `f522c8dba5a68d86fe29d1a36bd8cfeb8c3acb9d`. Any
   violation rejects the entire private payload as `schema_mismatch` (no partial
   item admission, no payload echo). Work-id collisions with public items reject
   the private payload as `identity_collision` without overwriting public data.
6. Mutation remains false everywhere. No POST/PUT/PATCH/DELETE, dispatch, merge,
   issue-edit, proxy, websocket, or hosted-resource behavior.

### Private-source status vocabulary (closed)

Rendered only in `#source-private-meta`:

| Condition | Text |
| --- | --- |
| Admitted private source | `status=<ok\|degraded\|unavailable\|permission_denied\|timeout\|truncated>` |
| AbortError / budget exceeded | `unavailable · timeout` |
| Fetch / non-2xx | `unavailable · unreachable` |
| Parse / shape failure | `unavailable · schema_mismatch` |
| Work-id collision | `unavailable · identity_collision` |

When the public document fails but private remains usable,
`#source-public-meta` is `status=unavailable` (transport) or
`status=schema_mismatch` (parse/shape). If both fail, the error banner is exactly:

`Work projection unavailable · public=<unreachable|schema_mismatch> · private=<timeout|unreachable|schema_mismatch|identity_collision>`

and the list is exactly: `No source projection is available. Retry refresh.`

### Merge (browser)

On dual admission success the browser:

- replaces only the public `sources[]` member with `source_id=private-local-adapter`
- concatenates admitted items
- sums issue/PR denominators, ANDs `streams_complete`, preserves public class-4
- removes only `{class:"private_adapter",reason:"not_configured"}` from public
  denominator omissions and appends private omissions
- installs the validated private `capabilities.private_source`
- sets `cache_age_s = max(public, private)`
- emits one dense attention list ordered by health
  (`OFF_TRACK`, `AT_RISK`, `UNKNOWN`, `ON_TRACK`), then original
  `attention_rank`, then `source_id`, then `work_id`, rewritten to `0..N-1`

### Saved views

Shareable state is **URL query only** (never fragment, storage, cookie, or other
encoding). Allowlisted keys: `health`, `kind`, `lifecycle`, `orphan`,
`repository_id`, `source_id`.

Stricter shareable rules than in-memory filters:

- enums only for health / kind / lifecycle / orphan
- `repository_id` only when it equals the public singleton
  `learn-ukrainian/learn-ukrainian.github.io`
- `source_id` only when it is `public-monitor`

Selecting a private repository or `private-local-adapter` filters the current
in-memory view only and strips those keys from the URL. Repository choices say
**All repositories** and include public/private slugs only after they appear in
an admitted payload.

### Live CORS (private adapter contract)

The private adapter admits exactly Monitor origins
`http://127.0.0.1:8765` and `http://localhost:8765`. A simple GET returns matching
`Access-Control-Allow-Origin` plus `Vary: Origin`, no credentials, and needs no
preflight because `Accept` is CORS-safelisted. Fixture proofs cover real
cross-origin browser smoke on those fixed loopback ports in addition to request
interception tests.

### Local service lifecycle

Run `./services.sh start` from the public checkout to start Sources (`8766`),
Monitor (`8765`), Astro (`4321`), and the sibling private Work adapter (`8769`).
The sibling checkout is discovered as `../learn-ukrainian-infra-private`; a
nonstandard layout may set `LEARN_UKRAINIAN_INFRA_PRIVATE_ROOT` to its root.
The browser endpoint and loopback bind remain fixed.

Use `./services.sh status work`, `./services.sh restart work`,
`./services.sh stop work`, and `./services.sh logs work` for the adapter. Status
reports `unavailable` with a typed reason when the checkout, virtualenv, or
module is missing, and `blocked` when a foreign process owns `127.0.0.1:8769`.
An unavailable adapter does not prevent the public services from starting.
Adapter logs remain in the private checkout at `logs/work-projection.log`; the
public tree never stores private adapter output.

The local port allocation also preserves the optional OpenAI-compatible bridge
on `8767` and is collision-free with KubeDojo: its API and Astro development
server remain on `8768` and `4333`, respectively.

## Denominator (public server)

At a query instant the public projection represents exactly once (or counts in a
typed omission):

1. Open public issues — one `gh issue list` enumeration, cap **1000**,
   `truncated=true` when incomplete.
2. Open public PRs — one `gh pr list` enumeration, same cap. No per-item
   detail/comment/check fan-out on refresh.
3. Complete public `GET /api/issues/streams` response (private cache keys stripped).
4. Class-4 summaries only:
   - `GET /api/delegate/active`
   - `GET /api/delegate/tasks?status=all&limit<=500`
   - `GET /api/fleet/reviews`

   Never delegate task detail bodies or sealed review blobs.

## Identity

`work_id = wp1:{source_id}:{repository_id}:{resource_kind}:{remote_id}`

`source_id`: `public-monitor` | `private-local-adapter`

## Budgets

- Warm response target: **≤2s** (warm cache ~30s).
- Optional/failing section → typed degraded/unknown within **≤5s** without hiding
  healthy sources.
- Private browser fetch budget: **5s** hard abort.
- `cache_age_s` is always present on admitted projections.

## Privacy

- Public server **never** fetches, proxies, persists, or renders private-repository
  data.
- Public capability seam returns `available: false`,
  `reason_if_unavailable: not_configured`, `endpoint: null` until the browser
  admits a private document.
- Mutation is always `false`.

## Example

```bash
curl -sS 'http://127.0.0.1:8765/api/work/v1/capabilities' | .venv/bin/python -m json.tool
curl -sS 'http://127.0.0.1:8765/api/work/v1/projection?fresh=true' | .venv/bin/python -m json.tool | head
# Private adapter (loopback only; never via public Monitor):
curl -sS -H 'Accept: application/json' -H 'Origin: http://127.0.0.1:8765' \
  'http://127.0.0.1:8769/v1/projection' | .venv/bin/python -m json.tool | head
```

See also: [ADR-019](../decisions/ADR-019-work-control-plane.md).
