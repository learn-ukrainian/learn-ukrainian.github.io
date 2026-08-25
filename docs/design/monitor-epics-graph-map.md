# Epics & Areas Relationship Map — Design Doc (v1)

> **Status:** DRAFT — awaiting cross-family design review (not yet implemented).
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
      {"id": "monitor", "title": "Monitor API + UI — fleet & host observability", "epic_count": 1}
      // one per issue_streams.yaml stream key — 13 in the live registry today
    ],
    "epics": [
      {
        "number": 7177, "area_id": "monitor", "title": "...",
        "registry_status": "...", "lease": {...}, "session_state": "...",
        "last_decision": {...}, "last_next_action": {...},   // verbatim from /api/epics/v1 rows
        "open_issue_count": 4, "closed_issue_count": 12
      }
      // one per epics: [...] entry across all 18 streams, keyed by epic number (a stream with
      // 2+ epic numbers, e.g. atlas-practice: [4387, 4700], yields 2 epic nodes under 1 area node)
    ]
  },
  "edges": [
    {"kind": "contains", "from": "area:monitor", "to": "epic:7177"}
    // one per area→epic membership; no issue-level edges in v1 (see §6 non-goals)
  ],
  "issues_by_epic": {
    "7177": [{"number": 7269, "title": "...", "state": "open", "url": "..."}, ...]
    // populated from fetch_epic_membership() open-issue numbers, joined against
    // fetch_open_issues() titles — powers the click-through detail panel
  }
}
```

**Epic-level status fields are pass-through from the existing `/api/epics/v1` row shape** — no new
status vocabulary invented; a stream/epic with no registry row (never claimed by a driver) gets
`registry_status: "unregistered"` (the existing value `remote_epic_list()` already produces for
that case) rather than a new field.

### 4.2 Issue-level relations — scoped down for v1, not the full cross-reference graph

The issue's "relations" language could be read as "full issue↔issue cross-reference graph"
(mentions, `Fixes #N`, etc. across every open issue). That is a materially bigger GitHub API
surface than `issue_stream_audit.py` currently walks (it resolves epic **membership**, not
issue-to-issue **mentions**). **v1 scope: epic→issue membership only** (open + closed counts,
open-issue list for the detail panel) — this satisfies the acceptance criterion ("click-through to
an epic detail panel with its issues") without a new GraphQL surface. A full mention-graph is
explicitly deferred (§6) — flag this scoping choice for the design review; it is the one place
this doc narrows the issue's literal wording and should be confirmed, not assumed correct.

### 4.3 Refresh / caching — reuse the existing worker, do not build a second one

`fetch_epic_membership()` calls `gh api graphql` per epic (18 epic slots) — expensive to run
per-request. `issue_stream_audit.py` already has a **file-locked background refresh worker**
(`schedule_refresh(force=False)`, `_spawn_worker`, `read_refresh_state`) built for exactly this
shape of problem (`/api/state/issues-health` already uses it). The graph endpoint calls
`schedule_refresh()` (cheap, returns immediately if a fresh cache exists or a refresh is already
in flight) and serves `read_refresh_state()`'s cached membership — it does not invoke `gh` inline
on the request path. This is the same pattern `work_router.py`'s `warm_projection_cache` uses for
its own single-flight background build; no third caching mechanism is introduced.

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

1. This doc — cross-family design review (1 round expected; this is materially smaller scope than
   #7269's app-factory refactor, so budget for iteration but not nine rounds).
2. Implement `GET /api/epics/graph/v1` in `epics_router.py` + OPSEC sweep update (§5) — one PR.
3. Implement `dashboards/epics-map.html` — one PR, gated on step 2 merging (needs the live feed to
   render against, not a mock).
4. Verify render end-to-end (not an empty stub) before promoting — per this project's render-
   before-promote gate.

## 8. Open questions for the reviewer

- Is epic→issue membership only (§4.2) an acceptable v1 scope, or does the operator's "relations"
  language require the fuller mention-graph now rather than as a deferred v1.1?
- Confirm the `issues_by_epic` cap — an epic with a very large open-issue count (e.g. a long-lived
  umbrella epic) should probably paginate or cap the inline list rather than ship an unbounded
  array; this doc does not yet specify a limit — reviewer input wanted before implementation.
