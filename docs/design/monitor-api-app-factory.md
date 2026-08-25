# Monitor API App Factory + Typed Root/Store Context — Design Doc

> **Version:** v2 (revised after cross-family review)
> **Status:** APPROVED (operator, 2026-08-25) — hardening, not new architecture; proceeds without
> further sign-off. Rollout is incremental and gated per family below.
> **Author:** Claude (monitor-epic driver), formalizing the operator's sketch, then revising v1 per
> the codex review below.
> **Issue:** #7269 (parent epic #7177, milestone M5 hardening).
> **Refs:** #7182 (OPSEC sweep design r2/r3 critique, task `critique-7182-design-r2-codex`, GPT-seat
> critic origin of the proposal).
> **v1 → v2 changelog:** v1 (PR #7296 initial commit) got a cross-family REJECT from codex with 3 P1
> findings + 1 P2. All four are addressed below; see § 10 for the finding-by-finding record.
> `main.py`'s actual 33-router `include_router` list was pulled live (not guessed) to ground the
> rollout plan — see § 5.

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

`MonitorContext` replaces this with an in-code choke point:

1. `MonitorContext.stores` holds **already-open handles** (`sqlite3.Connection` / equivalent), not
   raw `Path` values. Nothing downstream of the context receives a bare path it could open itself.
2. Every handle is produced by exactly one internal method, e.g. `MonitorContext._open_db(name:
   str) -> sqlite3.Connection`, which resolves the configured path, and — for a `fixture_context`
   only — asserts `path.is_relative_to(self.root)` before calling `sqlite3.connect(path)`.
   `production_context()` has no such root restriction (it legitimately opens the real stores); the
   guarantee is specifically "a fixture-built app cannot reach outside its temp root," which is what
   #7284 needs.
3. `_open_db` is the **only** call site anywhere in `scripts/api/` permitted to call `sqlite3.connect`
   once a router family has migrated. Step 0 adds a grep-based lint check (cheap, mechanical, wired
   into the OPSEC sweep or a standalone test) that fails if `sqlite3.connect(` appears outside
   `monitor_context.py` and any *not-yet-migrated* router listed in an explicit allowlist — the
   allowlist shrinks by exactly the routers each family step migrates, so it is machine-checkable
   proof of progress, not a promise.
4. The existing `monkeypatch.setattr(sqlite3, "connect", …)` global backstop in the OPSEC sweep
   **stays** through the whole migration as defense-in-depth — it becomes redundant for migrated
   routers (they can only reach `_open_db`, which already enforces the root) but keeps catching
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
against the actual router set — codex's review caught that this is not filing-ready: `main.py`
mounts 33 router modules today (`app.include_router(...)`, checked live 2026-08-25), 6 of which are
1,000+ lines and mix several concerns internally (`fleet_router.py` 2,637 lines, `state_router.py`
2,433, `comms_router.py` 1,898, `runtime_router.py` 1,729, `route_contracts.py` 1,356,
`dashboard_router.py` 996 — together roughly half of all router code). Naming one of these a "family"
by itself is not precise enough to file a bounded sub-issue from, and lumping several together is
worse. Guessing a finer split without reading what's actually inside those six files would just move
the same ambiguity to a smaller-looking table.**

### 5.1 Step 0 — Core (unchanged from v1)

`MonitorContext` + `create_app` + `production_context`/`fixture_context` per §4. **No router
changes.** Concrete, executable definition of "byte-identical outcome" (this is the fix for the v1
review's P2 finding — v1 asserted this with no test):

- New test, kept permanently (it is cheap and it is exactly the regression net for every later
  step): build `legacy_app = <today's `scripts.api.main.app`>` and `factory_app =
  create_app(production_context())` inside one test process. Enumerate the OPSEC sweep's existing
  route denominator (`tests/api/opsec_sweep/` already has a SHA-pinned list of every GET/HEAD route —
  reuse it, do not build a second one). For every route in that list, call it against both apps via
  `TestClient` with the same inputs and assert identical status code **and** identical JSON body (or
  identical bytes for non-JSON responses). Mutating (POST/PUT/DELETE) routes are exercised for
  status/shape only where the sweep already has a safe fixture for them; routes the sweep has no safe
  fixture for are out of scope for this specific test (already true of the sweep itself).
- Add a fixture-isolation test: `fixture_context(tmp_path)` two separate app instances built from two
  different temp roots must not observe each other's writes (proves `create_app` really is
  side-effect-free per call, not a hidden singleton).
- The grep-based `sqlite3.connect(` call-site lint from §4.1 point 3 also lands in step 0, with its
  initial allowlist populated by every router file that has not migrated yet (i.e., everything —
  step 0 changes no router).

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
| 12 | Everything else the inventory has not yet placed: `atlas_jobs_router.py`, `blue_router.py`, `epics_router.py`, `coordination_router.py`, `consultation_router.py`, `cost_router.py`, `decisions_router.py`, `delegate_router.py`, `discussions_router.py`, `gold_router.py`, `governance_router.py`, `hermes_cron_router.py`, `issues_router.py`, `knowledge_router.py`, `reviewer_ghosts_router.py`, `site_router.py`, `telemetry_router.py`, `wiki_router.py`, `worktrees_router.py`, `work_router.py` — the inventory step batches these by shared store/root, capped at roughly 5 files or 1,500 lines per resulting step, and files that many sub-issues (12a, 12b, …) rather than one. | batched by inventory |

Sub-issues under #7269 are filed **from the inventory's actual output**, not from the provisional
table above — if the inventory contradicts a row here, the inventory wins and this doc gets a v3 note
in §10.

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
4. Step 0's byte-identical-outcome test (§5.1) and fixture-isolation test stay in the suite through
   every later step — they are exactly the check that a family migration changed *where* a route
   reads from, not *what* it returns.

## 8. Sequencing

1. Formalize this doc (done, v1, PR #7296).
2. One cross-family design review (codex seat) on the doc. **Done — v1 got a REJECT with 3 P1 + 1
   P2 finding; this v2 addresses all four (§10).**
3. One more cross-family design review on this v2 revision before implementation starts.
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
