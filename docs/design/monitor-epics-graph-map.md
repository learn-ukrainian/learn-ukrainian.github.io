# Epics & Areas Relationship Map — Design Doc (v1)

> **Status:** APPROVED by cross-family review (agy, 2026-08-25) — see §9. Deltas from the review
> are folded into §4.1/§4.3 below, not left as a separate errata list. Not yet implemented.
> **Author:** Claude (monitor-epic driver).
> **Issue:** #7295 (parent epic #7177, milestone M5).
> **Refs:** #7269 (sibling hardening track — no code overlap; `epics_router.py` is untouched by
> #7269's step 0/0.5, so this can land independently and in parallel).

## 1. Problem

`dashboards/epics.html` is a flat table sourced from `GET /api/epics/v1`: one row per registered
stream, no relationships, no issue-level detail. The operator wants one screen that shows, at a
glance: the areas that exist, which epics sit in each, how epics relate to their issues, each
epic's live status (lease/session/last-decision), and a click-through to the issues themselves.

## 2. Data sources — verified against the live tree, not assumed

The issue names three sources as sufficient for v1. Verifying each against the actual code before
designing on top of it:

1. **`scripts/config/issue_streams.yaml`** — 13 streams, 18 epic slots, **last updated
   2026-08-23** (`cf3553e226`, registered the monitor stream itself). This is the area/stream SSOT
   this design uses (see §2.1 for why the alternative registry is rejected for v1).
2. **`GET /api/epics/v1`** (`scripts/api/epics_router.py:526`) — per-stream rows: `stream_id`,
   registry fields, `lease`, `session_state`, `last_state`/`last_decision`/`last_next_action`.
   Already the exact per-epic status source `dashboards/epics.html` uses today; this design adds
   to the same router rather than inventing a second epic-status path.
3. **GitHub issue graph** — `scripts/orchestration/issue_stream_audit.py` already has
   `fetch_epic_membership(epic)` (native sub-issues via GraphQL + `#N` body-ref fallback) and
   `fetch_open_issues()` (all open issue numbers/titles), plus a **rate-limit-aware refresh state
   machine** (`schedule_refresh` / `read_refresh_state` / file-lock + background worker,
   `issue_stream_audit.py:245-527`) that this design reuses instead of building a second poller —
   see §4.3.

### 2.1 A second area registry exists — `fleet_taxonomy.yaml` — and it is stale; not used for v1

`scripts/config/fleet_taxonomy.yaml` is a **separate**, coarser area registry (`resolve_area()` in
`scripts/orchestration/fleet_taxonomy.py`, consumed by `work_router.py`'s `/api/work/v1/projection`
for per-item area tagging). It groups several `issue_streams.yaml` streams under one "area" id
(e.g. `atlas` area = `atlas-practice` + `atlas-intake` streams). It looked like a plausible reuse
target for "area" grouping — verified live instead of assumed, and rejected:

- **Last touched 2026-07-27** (`7656697b26`), never synced since. It has **no `monitor` area at
  all** — epic #7177, the epic this feature itself belongs to, cannot be resolved through
  `resolve_area()`. A graph map built on this registry would be unable to place its own epic.
- Its `infra` area still lists epic **#4707** (closed) instead of the successor **#6943** that
  `issue_streams.yaml`'s `infra-harness` stream has carried since #6943 replaced it.
- It is also missing an `open-model-data` area (epic #6321) entirely.

**Decision:** v1 uses `issue_streams.yaml` directly as the area layer (matches the issue's own
framing, is current, and includes monitor). `fleet_taxonomy.yaml`'s staleness is a real, separate
bug — filed as a follow-up (#7306) rather than fixed here; fixing it is out of scope for a
graph-map feature and touches `work_router.py`'s live area-tagging behavior, which is its own
change with its own blast radius.

## 3. Goals (v1)

1. One new read-only endpoint, `GET /api/epics/graph/v1`, returning nodes (areas + epics),
   containment edges (area→epic), and per-epic rollups (open/closed issue counts, lease/session
   status) — assembled from the three sources above, no new data source.
2. One new view, `dashboards/epics-map.html`, rendering that feed as a cluster/node graph:
   areas as clusters, epics as nodes colored by status, click-through to an epic detail panel
   listing its issues with GitHub links.
3. The new route passes the OPSEC sweep with zero leaks (§5).
4. Read-only, no mutation, no new write path.

## 4. Design

### 4.1 Endpoint: `GET /api/epics/graph/v1`

Lives in the existing `scripts/api/epics_router.py` (mount prefix `/api/epics`), **not** a new
router module — it shares the same store dependency (`_store()`) as every other `/api/epics/*`
route and needs no root/store the router doesn't already have. This keeps the OPSEC seam count
and #7269's inventory (§5.2 of the app-factory doc, in flight in parallel) unaffected by this
feature — no new router module to add to that inventory.

Response shape:

```jsonc
{
  "schema": "epics-graph.v1",
  "generated_at": "2026-08-25T20:00:00Z",
  "nodes": {
    "areas": [
      {"id": "area:monitor", "stream_id": "monitor", "title": "Monitor API + UI — fleet & host observability", "epic_count": 1}
      // one per issue_streams.yaml stream key — 13 in the live registry today; "id" is the
      // graph-traversal key (matches edge endpoints), "stream_id" is the bare registry key
      // (matches /api/epics/v1's stream_id) — same split as epic nodes' id vs number
    ],
    "epics": [
      {
        "id": "epic:7177", "number": 7177, "area_id": "monitor", "title": "...",
        "registry_status": "...", "lease": {...}, "session_state": "...",
        "last_state": {...}, "last_decision": {...}, "last_next_action": {...},
        "open_issue_count": 4, "closed_issue_count": 12
      }
      // one per epics: [...] entry across all 18 streams, keyed by epic number (a stream with
      // 2+ epic numbers, e.g. atlas-practice: [4387, 4700], yields 2 epic nodes under 1 area node)
    ]
  },
  "edges": [
    {"kind": "contains", "from": "area:monitor", "to": "epic:7177"}
    // one per area→epic membership; no issue-level edges in v1 (see §6 non-goals). Edge
    // endpoints use the same "area:<id>" / "epic:<number>" id strings as node.id, so the
    // dashboard JS can index nodes by id without a second lookup table.
  ],
  "issues_by_epic": {
    "7177": {
      "items": [{"number": 7269, "title": "...", "state": "open", "url": "..."}, ...],
      "total_open": 4,
      "truncated": false
    }
    // capped at 50 items per epic (agy review finding, §9) — an umbrella epic with a large
    // open-issue count gets total_open + truncated:true instead of an unbounded array; the
    // dashboard falls back to a "view all N on GitHub" link when truncated
  }
}
```

**Epic-level status fields are pass-through from the existing `/api/epics/v1` row shape** (now
including `last_state`, not just `last_decision`/`last_next_action` — corrected per §9 finding 4)
— no new status vocabulary invented; a stream/epic with no registry row (never claimed by a
driver) gets `registry_status: "unregistered"` (the existing value `remote_epic_list()` already
produces for that case) rather than a new field.

### 4.2 Issue-level relations — scoped down for v1, not the full cross-reference graph

The issue's "relations" language could be read as "full issue↔issue cross-reference graph"
(mentions, `Fixes #N`, etc. across every open issue). That is a materially bigger GitHub API
surface than `issue_stream_audit.py` currently walks (it resolves epic **membership**, not
issue-to-issue **mentions**). **v1 scope: epic→issue membership only** (open + closed counts,
open-issue list for the detail panel) — this satisfies the acceptance criterion ("click-through to
an epic detail panel with its issues") without a new GraphQL surface. A full mention-graph is
explicitly deferred (§6) — flag this scoping choice for the design review; it is the one place
this doc narrows the issue's literal wording and should be confirmed, not assumed correct.

### 4.3 Refresh / caching — mirror the existing `GET /api/issues/streams` endpoint exactly

`fetch_epic_membership()` calls `gh api graphql` per epic (18 epic slots) — expensive to run
per-request. `issue_stream_audit.py` already has a **file-locked background refresh worker**
(`schedule_refresh(force=False)`, `_spawn_worker`) built for exactly this shape of problem, and a
**live consumer already implements the exact pattern this endpoint needs**:
`GET /api/issues/streams` (`scripts/api/issues_router.py:187-230`, not the more general
`/api/state/issues-health` this doc originally (and incorrectly) pointed at — corrected per §9
finding 2). Its `_load()` does exactly what this endpoint should do, and is the literal
implementation to mirror rather than paraphrase:

1. Read the cache directly — `audit.read_cache(max_age_s=3600)` — **not**
   `read_refresh_state()`, which returns the worker's lifecycle state machine
   (`phase`/`last_outcome`/`retry_after`), not the audit payload. This was wrong in the doc's
   first draft — flagged and fixed per §9.
2. On a cache miss, fall back to a stale read (`read_cache(max_age_s=7*24*3600)`) with a
   `"stale": true` marker rather than blocking on a live audit.
3. Schedule a background refresh (`schedule_refresh(force=fresh)`) only when the cache is
   genuinely absent or the caller passed `?fresh=true` — never inline `gh` work on the request
   path.
4. Run the whole cache/state read off the ASGI event loop via `asyncio.to_thread` (file locks and
   fsync are synchronous OS calls even though no network call happens inline).

The graph endpoint's `_load()` is the same four steps, reading `audit.read_cache(...)`'s
`effective_membership` / `open_issue_numbers` to build `issues_by_epic` instead of
`issues_router.py`'s orphan/multi-homed hygiene report.

**Title-map gap (§9 finding 2) — needs a small, contained addition to `classify()`.** The cached
report (`scripts/orchestration/issue_stream_audit.py:classify()`, ~line 929) already computes
`titles = {i["number"]: i["title"] for i in open_issues}` locally, but only re-embeds it for
`orphans` and `multi_homed` entries in the returned dict — there is no full open-issue title map
in the persisted cache today. Building `issues_by_epic`'s per-issue `title` field without an
inline `gh` call requires `classify()` to persist the full `titles` dict as a new top-level report
key (e.g. `"open_issue_titles": titles`) — a few-line addition to an existing function, not a new
subsystem. This is in scope for the implementation PR, called out explicitly here so it isn't
discovered mid-implementation.

### 4.4 View: `dashboards/epics-map.html`

New file, following the existing `dashboards/epics.html` conventions verified live: vanilla JS
`fetch()` (no framework, no CDN — required by the OPSEC/self-contained-dashboard convention every
other `dashboards/*.html` file already follows), auto-refresh on an interval, theme-aware CSS,
degrades per-field when the feed omits something (e.g. no lease → render "no active driver", not a
blank/broken node). Layout: areas as visually distinct clusters (13 today — small enough for a
simple grid/force-free layout, no graph-layout library needed for this node count), epics as nodes
colored by `registry_status`/lease presence, click opens a detail panel listing `issues_by_epic`
with GitHub links. No mutation controls (read-only dashboard, matches `epics.html`'s existing
footnote convention).

## 5. OPSEC sweep — binding constraint, not optional

`GET /api/epics/graph/v1` is a **new route** and must enter `tests/api/opsec_sweep/registry.py`
before merge. Two frozen values this route changes and the implementer must update **together**,
not separately (a mismatch between the two is exactly the kind of drift the app-factory design
review caught repeatedly on a different route set):

- `FROZEN_HTTP_OPERATION_COUNT` (currently 280) increments by 1.
- `FROZEN_DENOMINATOR_SHA256` (currently
  `4876620305f8035f30103fc6f2d0f0d4f22e43dfb00247f1a7aa32604cbccd20`) changes — re-derive it from
  the sweep's own digest function against the updated route table; do not hand-compute it.

The route also needs an explicit fixture entry (`isolated` — an empty/seeded fixture store has no
real registry rows, matching the existing `"GET /api/epics/v1": "isolated fixture has no seeded
epic registry snapshot"` precedent at `registry.py:63`) — the new route gets the same treatment,
same reason, for the same underlying store.

## 6. Non-goals (v1)

- No mutation, no GitHub write (matches the issue's own non-goals).
- No full issue↔issue cross-reference/mention graph — epic→issue membership only (§4.2).
- No fix to `fleet_taxonomy.yaml`'s staleness (§2.1) — filed as #7306, a separate follow-up.
- Not a generic graph-layout library integration — 13 areas / 18 epics is small enough for a
  hand-rolled cluster layout; revisit only if the node count grows materially.

## 7. Sequencing

1. This doc — cross-family design review. **Done** (agy, APPROVE, one round — §9).
2. Implement `GET /api/epics/graph/v1` in `epics_router.py` + OPSEC sweep update (§5) — one PR.
   **Next.**
3. Implement `dashboards/epics-map.html` — one PR, gated on step 2 merging (needs the live feed to
   render against, not a mock).
4. Verify render end-to-end (not an empty stub) before promoting — per this project's render-
   before-promote gate.

## 8. Open questions — resolved by review (§9)

- **Epic→issue membership only, not the full mention-graph (§4.2):** confirmed as the right v1
  scope. A full cross-issue mention graph would add a materially larger, rate-limit-risky GraphQL
  surface for a click-through detail panel that membership already satisfies; deferred to v1.1.
- **`issues_by_epic` cap:** resolved as a **50-item cap per epic**, with `total_open` and
  `truncated` fields so the UI can show "view all N on GitHub" when truncated (§4.1 response
  shape now reflects this).

## 9. Cross-family review record

- **v1 (PR #7308, commit `c5552d950d`), reviewer: agy (`gemini-3.7-flash-high`), verdict:
  APPROVE.** Verified §2/§2.1's `issue_streams.yaml` vs `fleet_taxonomy.yaml` staleness claims
  directly against both files (confirmed correct). Four findings, all incorporated above rather
  than left as a separate errata list:
  1. §4.3 named `/api/state/issues-health` as the existing consumer of this refresh pattern; the
     concrete, more useful precedent is `GET /api/issues/streams`
     (`scripts/api/issues_router.py:187-230`), which already implements the exact read-cache /
     stale-fallback / schedule-refresh / off-event-loop pattern this endpoint needs. **Fixed:**
     §4.3 now points at and mirrors that handler directly.
  2. §4.3 said the endpoint "serves `read_refresh_state()`'s cached membership" — wrong:
     `read_refresh_state()` returns the background worker's lifecycle state (phase/outcome/retry),
     not the audit payload; the actual cached membership is `audit.read_cache(max_age_s=...)`.
     Also surfaced a real, previously-unnoticed gap: the cached report only retains issue titles
     for orphan/multi-homed entries, not the full open-issue set needed for `issues_by_epic`.
     **Fixed:** §4.3 corrected to the right function and specifies the small `classify()` addition
     (`open_issue_titles`) the implementation PR needs.
  3. The response shape (§4.1) dropped `last_state` while keeping `last_decision` /
     `last_next_action` from the same `/api/epics/v1` row, and used inconsistent id shapes between
     `nodes` (bare `"number"`) and `edges` (`"epic:N"` strings). **Fixed:** §4.1 now includes
     `last_state`, and every node carries an `"id"` field in the same `"area:<id>"` /
     `"epic:<number>"` shape edges use, so the dashboard JS indexes nodes by `id` directly.
  4. Recommended resolutions for both §8 open questions (membership-only scope; a capped
     `issues_by_epic` with truncation metadata). **Fixed:** §8 now records both as decided, and
     §4.1's response shape reflects the 50-item cap.
