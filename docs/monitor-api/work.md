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
| `GET` | `/api/work/v1/capabilities` | Schema digest, budgets, class-4 endpoint freeze, private-source seam |
| `GET` | `/api/work/v1/health` | Cheap Work surface liveness |

UI: [`/work.html`](../../dashboards/work.html) — Evidence rail attention list
(Monitor paper language).

## Browser-local private adapter boundary

Only browser JavaScript in `dashboards/work.html` may fetch the fixed constant:

`http://127.0.0.1:8766/v1/projection`

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
  'http://127.0.0.1:8766/v1/projection' | .venv/bin/python -m json.tool | head
```

See also: [ADR-019](../decisions/ADR-019-work-control-plane.md).
