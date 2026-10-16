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

These milestone labels establish neither source completeness nor deployment
health, #10667 completion, or independent B6 acceptance. Documentation does not
supply the missing PR ownership/history (D04), posted-blocker/operator-decision
semantics (D05), image search (D10), download aliases (D12), or safe private
destination delivery (D13). Those dependencies need their own evidence.

Base URL (public Monitor): `http://127.0.0.1:8765` (prefer loopback IP).

## Endpoints (public server)

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/work/v1/projection` | Normalized attention list, work items, source envelopes, denominator, cache age |
| `GET` | `/api/work/v1/next` | Stream-scoped actionable pick list for orchestrators (#6880) |
| `GET` | `/api/work/v1/capabilities` | Schema digest, budgets, class-4 endpoint freeze, private-source seam |
| `GET` | `/api/work/v1/health` | Cheap Work surface liveness |

### `GET /api/work/v1/next` (next-queue, #6880)

Machine contract for a lane's next actionable picks. Params:
`stream=<stream key>` (required; keys from
`scripts/config/issue_streams.yaml`, unknown keys 400 with `valid_streams`) and
`limit` (default 7, max 25). Unambiguous fleet-taxonomy area aliases are
accepted and echoed (`?stream=infra` → `stream: "infra-harness"` +
`requested_stream: "infra"`, via the same `fleet_taxonomy.yaml` resolver the
session hooks use); ambiguous or unknown selectors still fail closed (#6984).
`epic:7919` is an invalid selector and returns `400 unknown_stream` with
`valid_streams`, including the canonical `monitor` key.

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
  `INSPECT_UNKNOWN`/`OPEN_GITHUB`/`NONE` deny list). The projection stamps
  that result on `flags.attention`. `dashboards/work.html` reads only that
  flag and treats a missing flag as not actionable. It does not keep a copy
  of the deny list.
- **Unknown stays visible.** Rows whose membership or decision-bearing state
  is unknown remain on `/projection`. `/next` does not put them on the
  requested lane. `digest.unscoped_unknown` is `{count, reason_counts}` for
  those rows, so an empty stream queue does not mean there is no remaining
  work. An unknown row that still names the requested stream is included when
  it is not on the pick list, such as an issue whose source is unqualified.
  `safe_next_action.state` is `ready`, `waiting`, `unknown`, or `none`.
  It qualifies the named action. It does not admit, review, lease, or complete
  anything.
- **Membership.** `denominator.streams_complete` is true only for a current
  complete streams observation (`status: ok`, not stale, not truncated, and
  certified when the payload is an audit). A stale, incomplete, or uncertified
  map sets the issue's current membership to `unknown` with
  `projections.stream.membership_reason`. It does not fall back to homed.
  `authority[].age_s` is the section observation age (`null` when the section
  is missing) and `authority[].stale` follows the section status.
- **Merge advice** is `MERGE_WHEN_READY` only when the latest persisted
  lifecycle receipt matches the repository, PR, and head, its `observed_at`
  is within 900 seconds (`LEDGER_RECEIPT_FRESHNESS_S`) and not further ahead
  than `LEDGER_RECEIPT_FUTURE_TOLERANCE_S` (30 seconds; further ahead is
  `receipt_observed_at_future`), `evaluate` on that
  receipt returns `CI_PASSED` with no hard blockers, and Work's own same-head
  observation is non-draft, merge state neither `DIRTY` nor `UNKNOWN`, with
  no requested changes and CI neither failing nor pending. Anything else is
  `unknown` with a named reason. The refresh does not call the live observer,
  GitHub, `reconcile`, or `write_lifecycle`.
- **Terminal is not delivery.** `done` stays unknown with reason
  `task_done_not_delivered`. Unsuccessful terminals and `needs_finalize`
  stay visible with their own reasons. A running or spawning task whose
  liveness is dead or unknown is not healthy execution. Task runtime age
  comes from `started_at` and is not the delegate section's observation age.
  Current normalization always emits `accountable_owner: "unknown"` and
  `owner_reason: "owner_unknown"`; a lease-backed record does not automatically
  populate the owner. See [Ownership and membership evidence](#ownership-and-membership-evidence).
- **Task association** is `linked_issues` on the delegate summary, copied from
  the DoR-checked `dor_preflight` issues. A task name that merely ends in an
  issue or PR number does not attach.
- **Digest, never a queue**: `other_streams.actionable_counts_by_stream`
  (counts only), `other_streams.top_blockers` (≤3 repo-wide OFF_TRACK
  pointers), `unscoped_actionable_count`, `unscoped_unknown`,
  `excluded_pending_native`
  (`count` + ≤25 items with `streams` and `reason`).
- **Stale projection timeout.** When `/projection` serves a cached payload
  older than its freshness bound because a rebuild timed out, every
  decision-bearing field in that response is `unknown` with reason
  `projection_cache_past_freshness`. Section status becomes stale, counts
  become historical, current issue/PR denominators become null, and class-4
  availability becomes false. The row may remain as history.
- **Warm cache only**: serves strictly from the unfiltered projection cache
  (single-flight, #6861). Cold → wire body
  `503 {"error": "building", "retry_after_s": 3}` (no FastAPI `detail`
  wrapper — machine-consumable as documented) and never triggers a build;
  expired-but-present entries are served with an honest `cache_age_s` while
  the shared background refresh runs, until age reaches `max_stale_s` (300s)
  → `503 {"error": "stale", "cache_age_s", "max_stale_s", "retry_after_s"}`.
  The background build is bounded (`NEXT_BUILD_TIMEOUT_S`, 20s) so a hung
  collector frees the single-flight slot and the next caller's refresh can
  succeed instead of wedging the lane at 503 stale (#6984).
  An unreadable `issue_streams.yaml` registry →
  `503 {"error": "registry_unavailable", "retry_after_s"}` (fail closed —
  never 200 + empty queue for a stream typo). These are source-defined bounds,
  not measured production performance guarantees.
- **Stream-name allowlist**: derive-time membership and any pre-set
  `open_stream_membership` are re-validated against registry keys before they
  enter the public projection (#6890).
- **Deterministic**: rank is the projection's `attention_rank` with a
  `work_id` tie-break; two calls over an unchanged projection return identical
  order.

UI: [`/work.html`](../../dashboards/work.html) — Evidence rail attention list
(Monitor paper language).

## Ownership and membership evidence

In [`normalize.py`](../../scripts/work/normalize.py),
`projections.dispatch.accountable_owner` is always `unknown` with
`owner_reason: owner_unknown`. A lease, caller, model family, GitHub author or
assignee does not establish an accountable-owner association.

PR rows have `projections.stream.status: "n/a"`, no `streams` membership, and
an empty dispatch association. Their branch names and task-name digits do not
attach them to a stream or task. Issue membership comes from the independently
qualified streams observation described above. The optional Fleet PR
`owner_lane` is a recorded lane or a fallback to the first branch segment;
it is distinct from both accountable owner and authoritative stream membership.

## Review, blocker and action evidence

`projections.review.review_decision` is GitHub review state, not a verified
exact-head cross-family verdict. The REST collector never synthesizes
`APPROVED` from individual approvals. `sealed_verdict_available` only reports
availability on matching repository/PR review summaries. That match does not
check the PR head or reviewer independence and does not admit a sealed blob.
Neither field alone clears the independent review gate.

Current PR normalization sets `flags.has_blocker: false` and
`relationships: []`. It does not enumerate posted blocker reports, so `false`
cannot prove that none were posted. Issue blocker flags derive from recognized
`blocked_by` relationships; confirmed closed targets no longer count as live
blockers, while unresolved targets still count. Those flags and
`RESOLVE_BLOCKER` describe derived impediments, not a complete posted-blocker
inventory or a typed pending operator decision.

`safe_next_action`, including `MERGE_WHEN_READY`, is advice derived from
observations. It does not admit, lease, execute, merge, certify, or complete work.
The exact-head independent cross-family review, same-head green CI, driver
enqueue, confirmed merge and closeout gates still apply.

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
- sums known issue/PR denominators, propagates `null` when either count is
  unknown, ANDs `streams_complete`, preserves public class-4
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

1. Open public issues — conditional REST pages (`If-None-Match`) followed to the
   end, cap **1000**. `truncated=true` when that cap or a page ceiling leaves a
   next link. Pull requests mixed into the issues API are dropped and are not
   counted as issues.
2. Open public PRs — same list contract. Check runs, reviews, and mergeability
   are conditional REST reads per open PR. A truncated check or review list stays
   unknown. `reviewDecision` is never synthesized as `APPROVED`: REST cannot see
   the required approval count, so one approval is unknown and Work / idle-PR
   consumers fail closed. A 304 serves the cached body and does not replace it
   with an older response.
3. Complete public `GET /api/issues/streams` response (private cache keys stripped).
4. Class-4 summaries only:
   - `GET /api/delegate/active`: public-repository active delegate tasks
   - `GET /api/delegate/tasks?status=all&limit<=500`: public-repository delegate
     inventory, including ordinary native review dispatches
   - `GET /api/fleet/reviews`: public-repository formal-review jobs only

   Formal-review jobs and ordinary review dispatches are distinct populations.
   An unsupported formal-review component sets `class4.fleet_reviews: false`
   and an unavailable section with its reason. It does not claim zero reviews.
   A supported successful empty read remains `status: ok`, count zero.

   Never delegate task detail bodies or sealed review blobs.

### Freshness, coverage and empty results

`cache_age_s` measures the enclosing projection cache's age. It does not reset
the age of a source observation. Public `sources[].sections` report each
section's `status`, `observed_at`, `age_s`, count, `scope`, `truncated` and
available reason. Failed observations have null count, time and age. Stale
observations retain their historical count and observation time. Aggregate
freshness is unknown if any section's age or observation time is unknown.
Item `authority[]` qualifies the relevant domains independently; missing
sections have `age_s: null` and `stale: true`. The aggregate source status
does not replace section and item qualification. Even `authority[].stale: false`
can accompany a truncated section; completeness needs a separate check.
Section `truncated` flags identify every capped population, even when a stale
or unavailable section determines the aggregate status. The top-level
`sources[].truncation.issues` and `.prs` flags describe only GitHub open
issues and open PRs at the declared GitHub limit. They do not describe delegate
or formal-review coverage. `denominator.omissions` names each truncated class.

A warm projection can contain a stale PR snapshot. The router advances source
ages from their original observation times on reads. Beyond
`PR_SNAPSHOT_FRESHNESS_S` (30 seconds), or if already
stale, PR rows get `gh_pr_snapshot_stale`, unknown health, CI, review decision
and merge evidence, `source_ok: false`, and `INSPECT_UNKNOWN`. Other sections
retain their independent qualification. A small `cache_age_s` therefore does
not prove that the PR's current head is cleared.

A zero count is usable as absence evidence only within a successful, complete,
current observation's scope. Failed, missing or truncated enumeration cannot
establish absence. `denominator.issues_open` and `.prs_open` are `null` for
failed, malformed or stale enumeration. Successful complete empty reads retain
zero. Truncated reads retain the observed count with explicit incomplete
coverage. For example, `gh_issue_list_timeout` produces `issues_open: null`
through both `/projection` and `/next`, even when `queue` is empty. The Work
reader displays unknown counts as `unknown` and capped counts as partial.

Even with complete enumeration, an empty `/next` queue means only that no
observed actionable rows qualify for that stream. Other streams, unscoped
actionable rows, unknown rows and non-actionable issues can remain. The
denominator, omissions and digests above qualify the queue; they do not turn
it into a complete work inventory. The public issue and PR collectors enumerate
open resources. Disappearance from them is not evidence of delivery or merge.

## Identity

`work_id = wp1:{source_id}:{repository_id}:{resource_kind}:{remote_id}`

`source_id`: `public-monitor` | `private-local-adapter`

## Budgets

- Warm response target: **≤2s** (`CACHE_TTL_S`: 30s).
- Projection request budget: **5s**; section timeout: **4.5s**, leaving headroom
  for typed degradation without hiding healthy sources.
- Private browser fetch budget: **5s** hard abort.
- `cache_age_s` is always present on admitted projections.

These values are configured targets and bounds, not current latency measurements
or deployment-health proof.

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
