# Monitor API App Factory + Typed Root/Store Context — Design Doc

> **Version:** v9 (revised after eight rounds of cross-family review)
> **Status:** APPROVED (operator, 2026-08-25) — hardening, not new architecture; proceeds without
> further sign-off. Rollout is incremental and gated per family below. **Not yet re-reviewed** — v9
> needs a ninth cross-family pass before step 0 is dispatched (see § 10).
> **Author:** Claude (monitor-epic driver), formalizing the operator's sketch, then revising per
> eight rounds of codex review below.
> **Issue:** #7269 (parent epic #7177, milestone M5 hardening).
> **Refs:** #7182 (OPSEC sweep design r2/r3 critique, task `critique-7182-design-r2-codex`, GPT-seat
> critic origin of the proposal).
> **Changelog:** v1→v8 each got a cross-family REJECT and fixed the prior round's findings — see §10
> for the full eight-round record. Round 8 confirmed the core-router-last ordering and the explicit
> exception-handler registration both actually work, but found three more issues: the v8 lifespan
> test entered a `TestClient` block cleanly with no positive assertion, which proves nothing (a bare
> `FastAPI()` with no lifespan at all also enters cleanly); this doc's own inline-route count was
> wrong *again* (v7/v8 said 18, the real count re-verified against the tree is 15); and two of those
> 15 route bodies (`health_check`, `get_config`) read the module-global `app.version` directly, which
> would silently point every `create_app()`-built instance at the same global rather than the
> instance actually serving the request. v9 (this version) fixes all three — the lifespan test now
> requires a mandatory spy assertion (not an optional one), the route count is corrected to 15
> throughout, and both handlers switch to `request.app.version` — see §10's v8 entry.

---

## 1. Problem

The Monitor API (`scripts/api/`) is a module-global FastAPI `app` with an attached `_lifespan`
(`scripts/api/main.py`). Roots and stores are import-bound module globals:

- `scripts/api/config.py`: `PROJECT_ROOT`, `LIVE_REPO_ROOT`, `MESSAGE_DB`, dashboard/batch roots.
- Per-router `_repo_root` / `_db_path` / `_store` globals, each router owning its own copy.
- Global in-memory presence and report stores.

This makes every router's data access implicit and process-global: tests and tools cannot build a
fully isolated instance of the API without monkeypatching module attributes, and nothing stops a
route from reaching a *real* store by accident — the exact shape of leak the #7182 OPSEC sweep
(`tests/api/opsec_sweep/`) exists to catch, but today it catches it with per-seam monkeypatches
rather than a structural guarantee.

## 2. Goals

1. One typed, app-scoped context object (`MonitorContext`) that owns every root and store handle the
   API touches.
2. A `create_app(context, *, lifespan=None)` factory so tests and tools can construct a fully
   isolated app instance — no monkeypatching, no shared process state.
3. Routers read the context via `Depends(get_ctx)` instead of module globals; no route can reach a
   real store except through the context it was constructed with.
4. The #7284 deny-connect-outside-root guard becomes a **property of the context** (enforced at
   construction) rather than a test-only monkeypatch seam.
5. Zero behavior change to any route's response shape or status codes during the migration.
6. The OPSEC sweep (`tests/api/opsec_sweep/`) is the regression net for every step and its seam list
   **shrinks monotonically** as each family migrates — that shrinkage is the visible proof of
   progress.

## 3. Non-goals

- No endpoint behavior change. Response shapes stay exactly as the #7182 burn-down left them.
- No new leak-table rows; the OPSEC sweep denominator stays SHA-pinned per step.
- Not touching `.github/workflows/*`, `scripts/ci/*`, or `opsec_scan.py` (fenced — CI/lint
  infrastructure is out of scope for this refactor).
- Not a big-bang rewrite. Each router family migrates in its own PR with its own CF review.

## 4. Design

### 4.1 `MonitorContext` (frozen dataclass)

One object holding every root and store handle the API needs, opened lazily:

- **`roots`** — `project_root`, `live_repo_root`, `dashboards_dir`, `batch_state_dir`,
  `curriculum_root`, `plans_root`, `backup_dir`, `logs_dir`, `queue_dir`, `pid_dir`, the docs
  `EFFECTIVE_ROOTS` table, image roots, …
- **`stores`** — `sources_db`, `message_db` (comms plane), `presence_store`, `report_store`,
  `session_streams_store`, `epics_store`, …

Two constructors:

- **`production_context()`** — builds the context from today's `config.py` resolution logic
  (identical values to what module globals resolve to today; this is a pure refactor of *where* the
  values live, not *what* they resolve to).
- **`fixture_context(root)`** — builds a context entirely rooted under one temp directory.

**How the outside-root guard actually becomes structural (not just "paths are scoped, trust it").**
Verified against today's mechanism: the #7284/#7182 guard is currently one process-wide monkeypatch,
`monkeypatch.setattr(sqlite3, "connect", _deny_real_database_connect(root, sqlite3.connect))` in
`tests/api/opsec_sweep/test_opsec_route_sweep.py`, plus a per-router `monkeypatch.setattr(router_mod,
"SOME_DIR", root / …)` for every module-global root the sweep knows about. Both are *test-side*
patches — nothing stops a route from calling `sqlite3.connect(<real path>)` directly; the sweep only
catches it because the test happens to intercept the interpreter-global function.

**v2 named a single `_open_db` choke point and claimed it was "the only call site anywhere in
`scripts/api/` permitted to call `sqlite3.connect`." Verified against the actual tree (2026-08-25),
this is false: DB access today goes through at least three distinct patterns, not one —**

- **Direct `sqlite3.connect(` calls** in `fleet_router.py`, `agent_monitor_router.py`,
  `delegate_router.py`, `fleet_workers_collect.py`, `hramatka_cache.py`, `comms_router.py`,
  `resilience.py`, `runtime_router.py`, `agents_extensions/shared/session_streams/db.py` (9 files).
- **`connect_sqlite()`**, an existing wrapper **defined** in `scripts/api/resilience.py:262` and
  **called from 10 other files**: `admin_router.py`, `discussions_router.py`, `state_helpers.py`,
  `gold_router.py`, `wiki_router.py`, `telemetry_router.py`, `dashboard_comms.py`,
  `hramatka_router.py`, `comms_router.py`, `telemetry/legacy_comms.py` — this is already the closest
  thing to an existing choke point; the design below builds on it rather than replacing it. (A plain
  `grep -l "connect_sqlite("` returns 11 files because the definition line itself matches the search
  string; the design-relevant count is the 10 callers.)
- **`SessionStreamDatabase.connect()`**, a method on the class in
  `agents_extensions/shared/session_streams/db.py:97`, used by `occupancy_local.py`,
  `epics_router.py`, `session_streams_router.py` (3 files).

`MonitorContext` replaces this with an in-code choke point that accounts for all three:

1. `MonitorContext.stores` holds **already-open handles** (`sqlite3.Connection` / a
   `SessionStreamDatabase` instance / equivalent), not raw `Path` values. Nothing downstream of the
   context receives a bare path it could open itself.
2. Internally, `MonitorContext` builds every handle by calling the *existing* `connect_sqlite()` (for
   plain sqlite stores) or constructing a `SessionStreamDatabase` (for the session-streams store) —
   it does not invent a fourth mechanism. What changes is that **only** `MonitorContext`'s
   construction code is allowed to call `connect_sqlite()` / `sqlite3.connect()` /
   `SessionStreamDatabase(...)` directly; every router gets a ready handle via `Depends(get_ctx)`.
3. For a `fixture_context` specifically, the context resolves the target path with `Path.resolve()`
   (canonical, symlink-following) before asserting `resolved_path.is_relative_to(self.root.resolve())`
   — plain `is_relative_to` on unresolved paths permits a symlink escape, which v2 missed.
   `production_context()` has no such root restriction; the guarantee is "a fixture-built app cannot
   reach outside its temp root," which is what #7284 needs.
4. Step 0 adds a grep-based lint check enumerating **all three** patterns above (not just
   `sqlite3.connect(`), wired into the OPSEC sweep or a standalone test, that fails if any of them
   appears outside `monitor_context.py` (or `resilience.py`/`session_streams/db.py` themselves, which
   `MonitorContext` calls into) and any *not-yet-migrated* file listed in an explicit allowlist. The
   §5.2 inventory step populates this allowlist's initial contents from the three lists above — 22
   real call sites (9 direct `sqlite3.connect` + 10 `connect_sqlite()` callers, excluding its own
   definition file + 3 `SessionStreamDatabase` users) across **21 unique files**
   (`comms_router.py` appears in both the direct-call and `connect_sqlite()`-caller lists;
   `resilience.py` is the direct-call site *and* the `connect_sqlite()` definition, counted once) —
   that is the real, checked starting count, not a placeholder.
5. The existing `monkeypatch.setattr(sqlite3, "connect", …)` global backstop in the OPSEC sweep
   **stays** through the whole migration as defense-in-depth — it becomes redundant for migrated
   routers (they can only reach handles the context already validated) but keeps catching
   not-yet-migrated routers and any future non-context code path.

### 4.2 `create_app(context, *, lifespan=None) -> FastAPI`

Builds a fresh `FastAPI` app, stashes `context` at `app.state.ctx`, registers routers and middleware.
`main.py`'s bottom becomes:

```python
app = create_app(production_context())
```

One line. The ASGI target stays `scripts.api.main:app` and all existing imports of `main.app` are
unchanged — this is the seam that keeps the migration invisible to every external caller (uvicorn
invocation, `TestClient(app)` call sites, deploy scripts) during the rollout.

### 4.3 Routers depend on context, not globals

Each router reads `Depends(get_ctx)` for the roots/stores it needs. The
`BACKUP_DIR = PROJECT_ROOT / …`-shaped module-level constants are deleted **per family**, as that
family migrates — not all at once.

## 5. Incremental rollout — one router family per PR, never big-bang

Each family PR: migrate its routers to `ctx`, delete the now-redundant sweep monkeypatch seam(s) for
that family, confirm the sweep stays green with **fewer** seams than before, run the full
`tests/api -n 4`, get an independent cross-family review of record.

**v1 named families by concept ("session-streams / orient / authority") without checking them
against the actual router set — codex's review caught that this is not filing-ready. v2 then
undercounted the router set itself (said 33; the actual count, re-verified by grepping every
`app.include_router(...)` call in `main.py`, is 44 — see the exact list below) and silently dropped
`build_events_router` from the step table. Both errors are fixed here; the count below is generated
from `grep -oE 'app\.include_router\(\s*\n?\s*[a-zA-Z_]+' scripts/api/main.py`, not hand-counted, so
any future reader can re-derive it. `main.py` makes 47 `include_router` calls mounting **44 unique
router modules** (`cost_router`, `docs_router`, and `sources_router` are each mounted at two
prefixes — one module, two routes-tables-worth of paths); 6 of those 44 are the largest and mix
several concerns internally (`fleet_router.py` 2,637 lines, `state_router.py` 2,433,
`comms_router.py` 1,898, `runtime_router.py` 1,729, `route_contracts.py` 1,356, `dashboard_router.py`
996 — together roughly half of all router code by line count). Naming one of these a "family"
by itself is not precise enough to file a bounded sub-issue from, and lumping several together is
worse. Guessing a finer split without reading what's actually inside those six files would just move
the same ambiguity to a smaller-looking table.**

### 5.1 Step 0 — Core (revised after the v2 through v8 reviews — see §10)

`MonitorContext` + `create_app` + `production_context`/`fixture_context` per §4. **No behavior
change to any of the 44 separately-defined routers** — every router still reads its own module
globals directly, exactly as today; none of their route/handler code moves or changes. **This claim
does not cover 15 routes and 3 exception handlers that today live inline, decorated directly on the
module-level `app` object inside `main.py` itself** (not in any of the 44 router files) — see point 5
below, a real structural change step 0 cannot avoid. This matters for what step 0 can and cannot
claim:

- **What step 0 does NOT claim.** v2 asserted a "fixture-isolation test" at step 0 — two apps built
  from two different temp roots must not observe each other's writes. The v2 reviewer correctly
  rejected this: since no router reads from `ctx` yet, a `fixture_context`-built app's routers still
  hit the *same real module globals* as every other app in the process. There is nothing to isolate
  until a router actually depends on the context. That guarantee becomes true, and testable,
  **incrementally, per family, starting at step 1** — not at step 0. Claiming it earlier was wrong;
  dropped.
- **What step 0 does claim, concretely, reusing existing infrastructure instead of inventing a new
  comparison harness** (this replaces v2's custom byte-identical-body test, which the reviewer
  correctly flagged as unspecified — no legacy-app builder, a wrong description of the sweep's
  denominator as "GET/HEAD" when it is actually 280 HTTP operations across
  `{DELETE, GET, PATCH, POST, PUT}` plus 1 WebSocket route with read/read-side-effect/mutation/stream
  classes and isolated/skip fixture kinds — see `tests/api/opsec_sweep/registry.py` — and no
  normalization plan for non-deterministic fields like UUIDs/timestamps in real responses):
  1. `main.py`'s bottom becomes `app = create_app(production_context())`. Since no router changed,
     every existing test that imports `scripts.api.main.app` (the bulk of `tests/api/`) exercises the
     factory-built app already — **the existing `tests/api -n 4` suite passing, unchanged, is itself
     the primary behavioral-equivalence proof**, because the routers it calls are byte-identical
     Python functions before and after this step.
  2. The OPSEC sweep's frozen-denominator check (`FROZEN_HTTP_OPERATION_COUNT`,
     `FROZEN_WEBSOCKET_ROUTE_COUNT`, `FROZEN_DENOMINATOR_SHA256` in `registry.py`, asserted at
     `test_opsec_route_sweep.py:677`) already exists specifically to catch a route table that grew,
     shrank, or changed shape. Re-run this exact check against `create_app(production_context())`'s
     route table and require the identical count and digest — this is the concrete, already-built
     mechanism that proves `create_app()` wires up the identical route set as the hand-built app,
     with no new comparison logic to design or trust.
  3. **Route digest + passing tests prove routes are unchanged; they do not prove app-level wiring is
     unchanged** — `main.py` also configures a lifespan context manager, exception handlers, CORS and
     resilience middleware, and app metadata that a route-count digest cannot see and that existing
     route tests may not each individually exercise. **v4 proposed diffing `legacy_app` against
     `factory_app` directly (`legacy_app.user_middleware == factory_app.user_middleware`), which the
     reviewer correctly rejected**: Starlette's `Middleware` entries compare by identity, so two
     independently-built (even structurally identical) apps never compare equal that way, and no
     `legacy_app` object exists to build once `main.py`'s bottom is rewritten to
     `app = create_app(production_context())` — there is nothing left to diff against.
     **Fixed, against the real current wiring** (`scripts/api/main.py:148-168`, read directly rather
     than assumed): `FastAPI(title="Playground API", version="2.0.0", description=..., lifespan=
     _lifespan)`, then `app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
     allow_methods=["*"], allow_headers=["*"])`, then `app.middleware("http")(resilience_middleware)`,
     then three `@app.exception_handler(...)` registrations for `StarletteHTTPException`,
     `RequestValidationError`, and `Exception`. Step 0 hardcodes this as an **expected snapshot** —
     not a second live app to diff against — and asserts `create_app(production_context())`'s app
     matches it:
     Every field below was independently confirmed by importing the real `scripts.api.main.app` and
     inspecting `app.user_middleware` / `app.exception_handlers` directly (2026-08-25), not guessed:
     - Extract each `app.user_middleware` entry's `.cls`, `.args`, `.kwargs` (these are the real
       `starlette.middleware.Middleware` attribute names, confirmed live — `args` is always `()` for
       both entries below) and compare against:
       - `CORSMiddleware` with `kwargs == {"allow_origins": ["*"], "allow_credentials": True,
         "allow_methods": ["*"], "allow_headers": ["*"]}`.
       - `BaseHTTPMiddleware` with `kwargs["dispatch"] is resilience_middleware` (the function-based
         middleware `app.middleware("http")(resilience_middleware)` wraps into this shape — confirmed
         live; do **not** compare `repr()` as a fallback, since Starlette's middleware `repr()`
         embeds the function's memory address and is not stable across runs).
     - Expected exception-handler key set is **four** entries, not three — a bare `FastAPI()` app
       already registers `starlette.exceptions.HTTPException`, `fastapi.exceptions.
       RequestValidationError`, and `fastapi.exceptions.WebSocketRequestValidationError` by default;
       `main.py`'s three `@app.exception_handler(...)` calls override two of those three and add
       `Exception` as a new fourth key. Confirmed live: `app.exception_handlers` has exactly these 4
       keys, each resolving to the handler stated: `StarletteHTTPException` → `main.py`'s custom
       handler (overridden), `RequestValidationError` → `main.py`'s custom handler (overridden),
       `WebSocketRequestValidationError` → **FastAPI's own default** (the one key `main.py` does
       *not* touch), `Exception` → `main.py`'s custom handler (added, not a default). An
       exact-three-key assertion would fail against the real app; the test must assert all four keys
       by name against this exact per-key origin, not a positional "first N vs. last one" shorthand
       (a v6 draft of this same bullet stated the origins positionally and got them backwards — fixed
       here by naming each key's origin explicitly instead).
     - **Expected lifespan: do NOT compare `app.router.lifespan_context` for identity or structural
       equality against `_lifespan`.** Verified live: `app.router.lifespan_context` is
       `<function _merge_lifespan_context.<locals>.merged_lifespan at 0x...>` — FastAPI wraps
       whatever `lifespan=` value it receives in a fresh closure on every app construction, so it is
       never `_lifespan` itself (`is` returns `False`), and two independently-built apps' wrapped
       closures are two different objects with nothing meaningful to structurally compare — the same
       independent-construction trap as the middleware finding above, just one layer deeper.
       **v7 proposed calling `_lifespan(factory_app)` directly (the pattern
       `tests/api/test_epics_registry_seed.py:380-384` already uses), which the reviewer correctly
       rejected**: `_lifespan`'s parameter is named `_app` and the function never reads it (verified
       against `scripts/api/main.py:120`), so calling it directly proves the function itself runs, not
       that `create_app()` actually *wired it in* as the app's lifespan — the test would pass even if
       `create_app()` registered no lifespan at all. **v8 then proposed `with TestClient(factory_app)
       as client: ...` with an optional spy assertion, which the reviewer also correctly rejected**:
       entering a `TestClient` context block cleanly is *not itself* evidence anything ran — a bare
       `FastAPI()` with no `lifespan=` argument at all enters and exits a `TestClient` block just as
       cleanly, since there is nothing to fail. Making the positive assertion "additional, for
       stronger evidence" left the test able to pass on a factory that wired no lifespan whatsoever.
       **Fixed: the positive assertion is mandatory, not optional.** Patch one of `_lifespan`'s own
       side-effecting calls (e.g. `scripts.api.main.start_periodic_refresh`, or
       `ensure_broker_db_ready`) with a `Mock`/spy *before* constructing `factory_app`, enter
       `with TestClient(factory_app) as client:`, and assert the spy **was called** — only a call
       recorded on the specific function `_lifespan` invokes proves `create_app()` actually wired
       `_lifespan` in as the app's lifespan; "the block didn't raise" proves nothing on its own and
       must not be the test's only assertion.
     This sidesteps identity-equality entirely (comparing hardcoded values against real structures,
     not two live objects against each other) and needs no second app construction.
  4. Add a narrow, new unit test scoped to `MonitorContext`/`fixture_context` **in isolation** (not
     through a running app): `fixture_context(tmp_path)` resolves every configured root/store path
     under `tmp_path`, and a path crafted to escape via a symlink is rejected (§4.1 point 3). This is
     testable today, standalone, without any router depending on the context yet.
  5. **New in v8: `main.py` has 15 routes and 3 exception handlers that are not part of any of the 44
     routers — they are decorated directly on the module-level `app` object, inside `main.py` itself**
     (verified live, `grep -n '^@app\.\(get\|post\|put\|delete\|patch\|websocket\|exception_handler\)'
     scripts/api/main.py`): `@app.exception_handler(...)` ×3 at lines 226/238/253, and `@app.get`/
     `@app.post`/`@app.websocket` ×15 at lines 1437–1916, including a catch-all `@app.get("/{path:path}")`
     at line 1916 that must stay registered *last* (route order determines match precedence — this
     catch-all currently is last because it is physically the last thing in the file, after all the
     `include_router` calls). **This breaks the "bottom of `main.py` becomes
     `app = create_app(production_context())`" claim as literally stated**: a decorator like
     `@app.get(...)` needs `app` to already exist at the point in the file where it executes, and
     Python evaluates a module top-to-bottom — if `app` is only constructed at the *bottom* of the
     file, every decorator physically *above* that point (which is all of them, today) has no `app`
     to bind to. **Fixed:** convert these into a proper router, exactly like the other 44 — add
     `core_router = APIRouter()` near the top of `main.py` (after imports, before any route
     definitions), change `@app.get(...)` / `@app.post(...)` / `@app.websocket(...)` to
     `@core_router.get(...)` / etc. for the 15 routes (same functions, same paths, same bodies — no
     behavior change), and have `create_app()` call `app.include_router(core_router)` as the **last**
     router registration (after all 44 others), preserving today's route-matching order for the
     catch-all. For the 3 exception handlers: drop the `@app.exception_handler(...)` decorator syntax
     (same `app`-must-exist-first problem) and keep `http_exception_handler`,
     `request_validation_exception_handler`, and `global_exception_handler` as plain module-level
     functions; `create_app()` calls `app.add_exception_handler(StarletteHTTPException,
     http_exception_handler)` (and the other two) explicitly — `@app.exception_handler(X)` is
     documented FastAPI sugar for exactly this call, so this is a syntax change with no behavior
     change. This is a genuine, unavoidable structural change inside `main.py` for step 0 — the
     amendment to the "no behavior change" claim above reflects that: no *behavior* changes (same
     routes, same handlers, same responses), but this specific file's code, unlike the 44 router
     files, cannot stay untouched.

     **Two of the 15 route bodies reference the module-global `app` variable directly, not just via
     the decorator** — verified live: `health_check` (`main.py:1450`) returns `"version": app.version`
     and `get_config` (`main.py:1759`) returns `"api_version": app.version`. A bare
     `@core_router.get(...)` rename does not fix this: both functions would still close over
     whichever object the name `app` resolves to in `main.py`'s module scope, which is fine for the
     single production instance today but breaks the moment two different `create_app()`-built
     instances need to exist (a `fixture_context` app and a `production_context` app, or two test
     fixtures) — both handlers would report the *same* global `app.version` regardless of which
     instance actually served the request. **Fixed:** both handlers gain a `request: Request`
     parameter and read `request.app.version` instead of the module-global `app.version` — this is
     FastAPI's documented, standard way for a handler to reach the specific app instance serving the
     current request, not a new mechanism invented for this migration. Because `main.py` currently has
     15 inline routes reviewed one-by-one for this migration, this is the only such reference found;
     §5.2's inventory step should still grep the other 44 router files for any bare `app.` reference
     (as opposed to `request.app.` or a context-supplied value) before assuming none exist there
     either.
- The grep-based call-site lint from §4.1 point 4 (all three DB-access patterns, not just
  `sqlite3.connect(`) also lands in step 0, with its initial allowlist populated by the 21 unique
  files enumerated in §4.1 plus `main.py` itself for its own direct store access, if any (checked as
  part of §5.2's inventory, not assumed here).

### 5.2 Step 0.5 — Router dependency & seam inventory (NEW; fixes the v1 P1a "ambiguous families" and P1b "no seam manifest" findings with one mechanism)

A small, mechanical, single-PR deliverable that must land and get reviewed **before any family
sub-issue is filed**: for every router module `main.py` mounts, record in
`docs/design/monitor-api-router-inventory.md` (or a JSON manifest the doc renders as a table):

1. Module path, mount prefix(es), route count, line count (data above is the seed; confirm live).
2. Every module-global root/store it reads from `scripts/api/config.py` or its own file (the exact
   set `MonitorContext.stores`/`roots` in §4.1 must cover).
3. Every OPSEC sweep seam (`monkeypatch.setattr(...)` call in `tests/api/opsec_sweep/`) that exists
   *because of* this router — this becomes the seam-count baseline. The sweep's shrinkage claim in
   §7 is checked against this baseline, not vibes: each family step's PR must delete the exact seams
   its inventory row lists, and the sweep's remaining-seam count (a single assertable number, e.g. a
   test asserting `len(KNOWN_SEAMS) == N`) must equal `baseline - migrated_seams`.
4. A proposed step grouping, derived from (2) — routers that share a store/root cluster group
   together; a module over roughly 800–1,000 lines gets its **own** step rather than folding
   into a batch, specifically so `fleet_router.py`, `state_router.py`, `comms_router.py`,
   `runtime_router.py`, `route_contracts.py`, and `dashboard_router.py` each get individually
   reviewed at a size where a reviewer can actually hold the whole diff in mind; each of those six
   additionally gets an internal route-group breakdown in its own inventory row (a 2,000+ line router
   may itself need to migrate in more than one PR — the inventory should say so explicitly rather
   than assume one PR fits).

Provisional shape (grounded in the live `main.py` mount list above; **the inventory in this step is
the source of truth that confirms or corrects this, not this doc**):

| Step | Scope (module file(s), by mount concern) | Size class |
| --- | --- | --- |
| 1 | `session_streams_router.py`, `rollover_router.py`, `session_router.py`, `rules_router.py` | small batch |
| 2 | `state_router.py` (own step — orient/authority/governance-adjacent endpoints live here; inventory decides if it splits into 2a/2b) | large, own step |
| 3 | `agent_router.py`, `agent_monitor_router.py`, `occupancy.py`, `observer_presence.py`, `fleet_workers_router.py`, `project_state_router.py` | small/medium batch |
| 4 | `fleet_router.py` (own step; inventory decides if it splits) | large, own step |
| 5 | `comms_router.py` (own step; inventory decides if it splits) | large, own step |
| 6 | `runtime_router.py` (own step; inventory decides if it splits) | large, own step |
| 7 | `docs_router.py`, `artifacts_router.py`, `images_router.py` | small/medium batch |
| 8 | `admin_router.py`, `ops_router.py`, `git_hygiene_router.py` | small/medium batch |
| 9 | `dashboard_router.py` (own step; inventory decides if it splits) | large, own step |
| 10 | `rag_router.py` (mounted as `/api/sources` + deprecated `/api/rag`) | small — folds the #7284 connect-deny guard into the context per §4.1 |
| 11 | `route_contracts.py` (own step; inventory decides if it splits) | large, own step |
| 12 | Everything else the inventory has not yet placed: `atlas_jobs_router.py`, `blue_router.py`, `build_events_router.py`, `epics_router.py`, `coordination_router.py`, `consultation_router.py`, `cost_router.py`, `decisions_router.py`, `delegate_router.py`, `discussions_router.py`, `gold_router.py`, `governance_router.py`, `hermes_cron_router.py`, `issues_router.py`, `knowledge_router.py`, `reviewer_ghosts_router.py`, `site_router.py`, `telemetry_router.py`, `wiki_router.py`, `worktrees_router.py`, `work_router.py` (21 modules) — the inventory step batches these by shared store/root, capped at roughly 5 files or 1,500 lines per resulting step, and files that many sub-issues (12a, 12b, …) rather than one. | batched by inventory |

Full accounting: step 1 (4) + step 2 (1) + step 3 (6) + step 4 (1) + step 5 (1) + step 6 (1) +
step 7 (3) + step 8 (3) + step 9 (1) + step 10 (1) + step 11 (1) + step 12 (21) = **44 modules**,
matching the live count above with none dropped.

Sub-issues under #7269 are filed **from the inventory's actual output**, not from the provisional
table above — if the inventory contradicts a row here, the inventory wins and this doc gets a new
§10 entry.

## 6. Constraints (binding for every step)

- No endpoint behavior change; response shapes stay as the #7182 burn-down left them.
- No new leak-table rows; the OPSEC sweep denominator stays SHA-pinned.
- Fenced paths: `.github/workflows/*`, `scripts/ci/*`, `opsec_scan.py`.
- Reviews of record stay cross-family on trusted seats (codex / agy / claude) — **not** ox-alpha
  (ox-alpha may implement; it does not review its own or anyone else's work here).

## 7. Regression net

`tests/api/opsec_sweep/` is the standing regression net for the whole migration. Each step:

1. Runs the full sweep (serial) — zero new leaks, same SHA-pinned denominator.
2. Runs `tests/api -n 4` — full suite green.
3. Deletes the monkeypatch seam(s) the migrated family no longer needs, per its inventory row from
   §5.2 — the sweep's known-seam count must equal `baseline - Σ(seams migrated so far)` exactly. This
   is a single assertable number (e.g. `test_known_seam_count_matches_migration_progress`), not an
   eyeballed "looks smaller" check — that is the fix for the v1 review's P1b finding.
4. Step 0's no-op proof (§5.1: unchanged `tests/api` + route-table digest match + the app-structure
   equality check below) and the standalone `MonitorContext`/`fixture_context` unit test stay in the
   suite through every later step. **Neither is an app-level isolation test** — no router depends on
   `ctx` until it migrates, so there is nothing for an app-level isolation test to check until steps
   1+ add one per family, scoped to exactly the routers that family migrated. This is a correction to
   a v2 wording carried over into this section that this section itself failed to update — see §10
   v3 entry.

## 8. Sequencing

1. Formalize this doc (done, v1, PR #7296).
2. Cross-family design review (codex). **Done eight times — v1 REJECT (3 P1 + 1 P2), v2 REJECT
   (4 further findings, incl. a router-count error), v3 REJECT (a doc-consistency bug, a real
   app-wiring proof gap, and several precision nits), v4 REJECT (v4's fixes for §7/router-count/
   connect_sqlite-count/line-counts all held; the middleware-equality mechanism itself was flawed),
   v5 REJECT (the fixed mechanism was sound but its exception-handler snapshot was incomplete — 3
   keys claimed, 4 actual — and its `repr()` fallback was unstable), v6 REJECT (the 4-key set and
   middleware attribute names were both confirmed correct; a self-contradictory closing sentence and
   an underspecified lifespan check remained), v7 REJECT (the lifespan test didn't test anything, and
   — the largest finding of the whole review — routes + handlers live inline on `main.py`'s
   module-level `app`, breaking the "bottom of the file becomes `create_app(...)`" claim as stated),
   v8 REJECT (the core-router-last ordering and explicit handler registration both actually work; the
   lifespan test's positive assertion was optional instead of mandatory, the inline-route count was
   wrong again — 18 claimed, 15 real — and two route bodies read the module-global `app.version`
   directly). v9 (this version) addresses all eight rounds (§10).**
3. One more cross-family design review on this v9 revision before implementation starts. **Next
   step.**
4. Implement step 0 (§5.1) — the dependency for every later step and the step most likely to reveal a
   wrong assumption in this doc before anything else builds on it.
5. Implement step 0.5 (§5.2) — the router dependency & seam inventory. Its output either confirms or
   corrects the provisional step table; file the per-family sub-issues under #7269 from its actual
   output once it lands and is reviewed.
6. Implement the resulting steps in order, one PR at a time, each gated on the previous step's
   sweep+tests staying green, each with its own independent cross-family review of record.

## 9. Open questions / risks

- **`fixture_context` root discipline**: every store/root the context opens must resolve strictly
  under the given root with no fallback to a module-level default — this is the entire point of §4.1;
  step 0's review should specifically check for any lazy-open path that could silently fall back to a
  production path when a fixture value is unset.
- **Ordering within a family**: some routers in the same batch may share a store handle — batch PRs
  should migrate all routers sharing a store together to avoid a half-migrated state where the same
  store is reached through two different paths (module global + context) simultaneously. The §5.2
  inventory's "group by shared store" rule is meant to prevent this by construction; this stays an
  open risk only for whatever the inventory misses.

## 10. Cross-family review record

- **v1 (PR #7296 initial commit), reviewer: codex, verdict: REJECT.** Findings and their v2
  disposition:
  1. **P1 — rollout families ambiguous** (step 1 named concepts, not exact routers; "the rest" was a
     10+ router catch-all). **Fixed:** §5 now cites the live 33-router `include_router` list with
     real line counts, gives every 1,000+ line router its own step, and defers the exact family
     boundaries for the remaining routers to a new mechanical inventory step (§5.2) rather than a
     second guess.
  2. **P1 — OPSEC sweep does not enforce seam shrinkage** (no seam inventory, baseline, or
     strict-decrease assertion). **Fixed:** §5.2 makes the seam inventory a per-router baseline
     recorded before migration starts; §7 point 3 makes the sweep assert the exact expected count
     after each step, not just "fewer."
  3. **P1 — `fixture_context` described as a structural guard but a frozen `Path`-holding object
     cannot itself prevent an arbitrary `sqlite3.connect`.** **Fixed:** §4.1 now specifies that
     `MonitorContext` holds open handles (not paths), routes every store open through one internal
     `_open_db` choke point that validates the root for fixture contexts, and adds a grep-based lint
     so no other call site can call `sqlite3.connect` once a router has migrated — with the existing
     process-wide monkeypatch kept as defense-in-depth, not replaced.
  4. **P2 — step 0's "byte-identical outcome" had no executable definition.** **Fixed:** §5.1 defines
     the exact test: legacy `main.app` vs. `create_app(production_context())`, same route list (the
     OPSEC sweep's existing denominator), same request, same assertion (status + body), kept
     permanently as the regression net for every later step; plus a fixture-isolation test.
  - The reviewer also noted it could not independently check v1 against the #7269 issue comment
    (GitHub network access was unavailable in that sandbox) — this is a harness limitation of that
    run, not a finding; the source-of-record comment is quoted in full in this repo's PR #7296
    description for any reviewer without live `gh` access.

- **v2 (commit 5d3a6c4), reviewer: codex, verdict: REJECT.** Findings and their v3 disposition:
  1. **P1 — step 0 was internally contradictory**: §5.1 asserted a fixture-isolation test, but
     routers still read module globals directly at step 0, so there was nothing for
     `fixture_context` to isolate yet. **Fixed:** §5.1 now explicitly states what step 0 does *not*
     claim (isolation — deferred to step 1+, per-family, as each router actually starts depending on
     `ctx`) and replaces the fixture-isolation app-level test with a narrow unit test of
     `MonitorContext`/`fixture_context` alone (path resolution + symlink-escape rejection), which is
     genuinely testable without any router migrated.
  2. **P1 — the byte-identical test was not executable**: no legacy-app builder was defined; the
     OPSEC sweep denominator was mischaracterized as "GET/HEAD" when it is actually 280 HTTP
     operations across 5 methods plus 1 WebSocket route with mutation/read/stream classes
     (`tests/api/opsec_sweep/registry.py`); real responses contain UUIDs/timestamps that break a
     byte-comparison with no normalization plan. **Fixed:** §5.1 drops the custom body-diff harness
     entirely and instead (a) relies on the existing, unchanged `tests/api -n 4` suite passing
     against the factory-built app — valid specifically because step 0 changes no router code — and
     (b) re-runs the sweep's existing frozen-denominator count+digest check
     (`test_opsec_route_sweep.py:677`) against `create_app(production_context())`'s route table.
     Both mechanisms already exist; nothing new to design or trust.
  3. **P1 — the `_open_db` choke point was bypassable**: v2 claimed one call site, but real DB access
     goes through `sqlite3.connect()` directly (9 files), the existing `connect_sqlite()` wrapper (10
     caller files, plus its own definition file), and `SessionStreamDatabase.connect()` (3 files);
     root validation used unresolved paths, permitting a symlink escape. **Fixed:** §4.1 now names
     all three real patterns by file (22 call sites across 21 unique files, grepped live and
     re-verified after this same section briefly mis-stated the connect_sqlite caller count in this
     round — see the v3 entry below), has `MonitorContext` build handles by calling the *existing*
     `connect_sqlite()`/`SessionStreamDatabase(...)` rather than inventing a fourth mechanism, and
     resolves paths canonically (`Path.resolve()`) before the root-containment check.
  4. **P2 — §5.2 was not dispatch-ready and had false inventory evidence**: the claimed 33-router
     count was wrong (real count: 44, re-grepped live); `build_events_router` and `reviewer_ghosts_router`
     were named as omitted — `reviewer_ghosts_router` was in fact present in v2's step 12, but
     `build_events_router` really was missing. **Fixed:** the router count and full step table are
     corrected (§5), with an explicit per-step module tally that sums to 44 with none dropped, and the
     count is now derived from a reproducible grep command stated in the doc rather than asserted from
     memory.
  - This reviewer run also could not reach `gh` for the #7269 issue comment (same harness limitation
    as the v1 run) — grounded its review in the checked-out tree instead, which is why it caught the
    router-count error directly rather than trusting the doc's stated figure.

- **v3 (commit 074b9b4), reviewer: codex, verdict: REJECT.** Findings, independently re-verified
  before disposition (one did not hold up — see below), and their v4 fix:
  1. **§7 still described the fixture-isolation test that §5.1 had already dropped** — a real
     doc-consistency bug: I edited §5.1's scope in the v2→v3 pass but missed updating §7's summary of
     what stays in the regression net. **Fixed:** §7 point 4 rewritten to match §5.1 exactly — no
     app-level isolation claim at step 0, isolation tests arrive per family starting step 1.
  2. **Route digest + passing tests don't prove app-level wiring (middleware, exception handlers,
     lifespan) is unchanged** — a real, previously-unaddressed gap: nothing in step 0 checked that
     `create_app()` actually carries over CORS/resilience middleware, exception handlers, and the
     lifespan context manager from the hand-built app. **Fixed:** §5.1 adds a direct structural-
     equality assertion (`user_middleware`, `exception_handlers`, `lifespan_context` compared between
     the legacy and factory-built app objects) as new point 3, distinct from the route-digest check.
  3. **Router-count precision**: claimed "44 router modules" without distinguishing that from the 47
     actual `include_router` calls (3 modules mounted twice). **Fixed:** §5 now states both numbers
     and names the 3 double-mounted modules (`cost_router`, `docs_router`, `sources_router`).
     *However*, the reviewer's specific sub-claim that "the stated grep returns 46 because it misses
     the multiline `reviewer_ghosts_router` call" **did not hold up under independent re-verification**
     — running the exact grep command stated in the doc returns 44 and does catch
     `reviewer_ghosts_router` (confirmed directly against `main.py`). Noted here rather than silently
     accepted, per this project's own rule against treating an unverified claim — including a
     reviewer's — as fact.
  4. **`connect_sqlite()` file-count was internally inconsistent**: v3 said "(11 files)" but listed
     only 10 filenames, because the 11th (`resilience.py`) is the function's own definition site, not
     a caller — a real transcription slip between the raw grep output and the doc's prose list.
     **Fixed:** §4.1 now separates "defined in resilience.py" from "called from 10 other files" and
     explains why a plain `grep -l` returns 11. The downstream "23 raw call sites / 21 unique files"
     figure is corrected to 22 real call sites (9 + 10 + 3) / 21 unique files — the unique-file count
     was already right; only the raw-match arithmetic needed the same correction.
  5. **"6 routers are 1,000+ lines" was imprecise** for `dashboard_router.py` at 996 (already stated
     correctly elsewhere in the same doc). **Fixed:** §5's framing no longer uses a round-number
     bracket; it lists the six actual line counts, 996 included honestly.
  - Verification note from this reviewer run: its own focused pytest could not start (no usable temp
    directory in that sandbox) — an environment limitation of that run, not a product result.

- **v4 (commit b0361e1), reviewer: codex, verdict: REJECT.** This round independently re-verified
  every round-3 fix rather than trusting the doc, and confirmed four of them held: §7 no longer
  claims step-0 app isolation; the router count (44 unique / 47 mounts, 3 double-mounted) checked out
  against `main.py`; the `connect_sqlite()` count (10 callers + 1 definition) checked out; the six
  line counts, including `dashboard_router.py` at 996, checked out. One finding remained:
  1. **The middleware/exception-handler/lifespan structural-equality check itself was flawed** — it
     proposed `legacy_app.user_middleware == factory_app.user_middleware`, but Starlette's
     `Middleware` entries compare by identity, so two independently-built apps — even with identical
     configuration — never compare equal that way; and no `legacy_app` object exists to build once
     `main.py`'s bottom is rewritten to call the factory, so there was nothing concrete to diff
     against in the first place. **Fixed:** §5.1 point 3 replaces the two-live-apps diff with a
     hardcoded expected-snapshot comparison, grounded directly in `main.py`'s actual current
     construction (`FastAPI(title=..., lifespan=_lifespan)`, the CORS `add_middleware` call with its
     four kwargs, the `resilience_middleware` function-based middleware, and the three
     `@app.exception_handler` registrations — read from the file, not assumed) — the factory-built
     app is checked against these hardcoded values, not against a second live app, which sidesteps
     the identity-equality problem entirely. The exact Starlette-internal field names for extracting
     `(cls, args, kwargs)` from a `Middleware` entry are explicitly left to the step-0 implementation
     PR (with a version-tolerant `repr()`-comparison fallback named), rather than guessed here and
     risking a fifth round on a wrong private attribute name.

- **v5 (commit 62ca873), reviewer: codex, verdict: REJECT.** Confirmed the fixed mechanism itself
  sound — "distinct, same-valued `Middleware` wrappers compare unequal, while comparing their
  extracted class/kwargs and the dispatch callable directly works" — and confirmed the
  CORS/resilience/lifespan/handler wiring otherwise matched `main.py`. Two findings:
  1. **Blocking: the exception-handler snapshot was incomplete.** v5 claimed exactly 3 keys
     (`StarletteHTTPException`, `RequestValidationError`, `Exception`). The real app has 4: a bare
     `FastAPI()` already registers `WebSocketRequestValidationError` as a default handler, and
     `main.py` never overrides it — an exact-3-key assertion would fail against the real app; a
     subset assertion wouldn't verify complete wiring. **Fixed:** independently re-confirmed by
     importing `scripts.api.main.app` directly and inspecting `app.exception_handlers` (4 keys,
     exactly as the reviewer described); §5.1 point 3 now specifies all 4 explicitly, with the origin
     of each (3 from `main.py`'s custom handlers, 1 from FastAPI's own default).
  2. **The proposed `repr()` fallback was not stable** — Starlette's middleware `repr()` embeds a
     function memory address, so it changes across runs/processes and can't be hardcoded as an
     expected value. **Fixed:** the fallback is dropped. Independently confirmed live (importing the
     real app and inspecting `app.user_middleware`) that `entry.cls` / `entry.args` / `entry.kwargs`
     are the real, correct Starlette attribute names — §5.1 point 3 now specifies these directly with
     no hedge, since they are now verified rather than assumed.
  - Also noted: `git diff --check` passed; full app import was unavailable in that sandbox (no usable
    temp directory, an environment limitation), but isolated FastAPI/Starlette probes completed —
    this session's own follow-up verification used the real `scripts.api.main.app` import directly and
    got the same 4-key, 2-middleware-entry result the reviewer described from its isolated probes.

- **v6 (commit 5e9f595), reviewer: codex, verdict: REJECT.** Confirmed the 4-key exception-handler set
  and the `.cls`/`.args`/`.kwargs` middleware attributes were both correct. Two findings:
  1. **v6's closing sentence contradicted its own preceding list.** The bullet correctly listed each
     key's origin (`StarletteHTTPException` overridden, `RequestValidationError` overridden,
     `WebSocketRequestValidationError` FastAPI default, `Exception` added), then closed with "the
     first three... custom handlers, the fourth... FastAPI's own default" — which is backwards: the
     3rd listed key is the default, and the 4th is custom. **Fixed:** §5.1 point 3 now states each
     key's origin explicitly next to the key name (no positional "first N / last one" shorthand that
     can drift out of sync with the list above it).
  2. **The lifespan check was underspecified and, as stated, would fail.** "Compare the same
     `_lifespan` function passed to `create_app`" implied an identity or structural check against
     `app.router.lifespan_context` — independently confirmed live that this is
     `_merge_lifespan_context.<locals>.merged_lifespan`, a fresh FastAPI-generated closure per app
     construction, never `_lifespan` itself (`is` returns `False`). **Fixed:** §5.1 point 3 now
     explicitly says not to touch `app.router.lifespan_context`, and instead reuses an existing
     pattern already in this codebase (`tests/api/test_epics_registry_seed.py:380-384`, which calls
     `api_main._lifespan(api_main.app)` directly as an async context manager) — the same call against
     the factory-built app, testing the actual function's behavior rather than an opaque wrapper's
     identity.

- **v7 (commit f361012), reviewer: codex, verdict: REJECT.** Confirmed the exception-handler origin
  fix held. Two findings, one of them the largest across all seven rounds:
  1. **The v7 lifespan test didn't test anything.** `_lifespan(factory_app)` calls the function
     directly, but `_lifespan`'s parameter is named `_app` and the body never reads it — the test
     could pass even if `create_app()` wired no lifespan at all. **Fixed:** §5.1 point 3 replaces the
     direct call with `with TestClient(factory_app) as client: ...`, which triggers Starlette's real
     ASGI lifespan protocol — an existing pattern in this codebase
     (`tests/api/test_import_pinning.py:227`) — so the test actually exercises the wiring, not just
     the function's callability.
  2. **Blocking, largest finding of the review: `main.py` has route decorators and exception handlers
     decorated directly on the module-level `app` object** (`scripts/api/main.py:226-254` and
     `:1437-1916`), not inside any of the 44 router files the design otherwise covers. (v8 itself had
     miscounted this as 18 routes; independently re-verified via `grep -c` against the checked-out
     tree, the real count is **15** route decorators + 3 exception handlers — this doc's own count was
     wrong twice in a row here, corrected below.) The design's "`main.py`'s bottom becomes
     `app = create_app(production_context())`" claim cannot work as stated: those decorators need a
     real `app` object at the point in the file where they execute, and Python evaluates top-to-bottom,
     so if `app` is only constructed at the bottom, none of them have anything to bind to. **Fixed:**
     §5.1 gains a new point 5 — convert the 15 routes into a
     `core_router = APIRouter()` (same pattern as every other router, `create_app()` includes it
     *last* to preserve the existing catch-all's route-matching order) and the 3 handlers into
     explicit `app.add_exception_handler(...)` calls inside `create_app()` (the documented equivalent
     of the `@app.exception_handler(...)` decorator they replace). The "no behavior change" claim at
     the top of §5.1 is corrected to be precise about what it does and doesn't cover — same routes,
     same handlers, same responses, but `main.py` itself (unlike the 44 router files) cannot stay
     byte-for-byte untouched for step 0 to be possible at all.

- **v8 (commit 92d401d), reviewer: codex, verdict: REJECT.** Confirmed the core-router-last ordering
  actually preserves the catch-all's precedence and the explicit exception-handler registration
  actually resolves the construction-order problem ("No additional `@app` route or exception
  decorators were found"). Three findings:
  1. **The lifespan test's positive assertion was optional, not mandatory** — "the client enters
     without raising... a mocked/spied piece can *additionally* assert" let the test pass with only
     the negative check, which a plain `FastAPI()` with no lifespan at all would also pass. **Fixed:**
     §5.1 point 3 now requires the spy assertion — patch one of `_lifespan`'s own calls before
     construction and assert it was called; "didn't raise" is explicitly stated as insufficient on its
     own.
  2. **The inline-route count was wrong again.** v7/v8 said 18; independently re-verified via
     `grep -c` against the checked-out tree, the real count is **15** route decorators + 3 exception
     handlers. **Fixed:** every "18" in the doc referring to this count is corrected to 15, with a
     note that the count was wrong in two consecutive versions here — this doc's own repeated
     miscounting is itself now part of the review record (§10 keeps it rather than quietly erasing
     it, consistent with how earlier rounds' arithmetic errors were handled).
  3. **Two of the 15 route bodies read the module-global `app.version` directly** — `health_check`
     (`main.py:1450`) and `get_config` (`main.py:1759`), verified live. A bare
     `@core_router.get(...)` rename doesn't fix this: both functions would still close over whichever
     object `main.py`'s module-level `app` name resolves to, so two different `create_app()`-built
     instances would both report the *same* global version rather than their own. **Fixed:** §5.1
     point 5 gains a new paragraph — both handlers add a `request: Request` parameter and read
     `request.app.version` instead, FastAPI's standard mechanism for a handler to reach the specific
     app instance serving the current request. §5.2's inventory step is also asked to grep the other
     44 router files for the same bare-`app.` pattern rather than assume these were the only two.
