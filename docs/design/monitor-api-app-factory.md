# Monitor API App Factory + Typed Root/Store Context — Design Doc

> **Version:** v1 (formalized from the approved sketch)
> **Status:** APPROVED (operator, 2026-08-25) — hardening, not new architecture; proceeds without
> further sign-off. Rollout is incremental and gated per family below.
> **Author:** Claude (monitor-epic driver), formalizing the operator's sketch verbatim.
> **Issue:** #7269 (parent epic #7177, milestone M5 hardening).
> **Refs:** #7182 (OPSEC sweep design r2/r3 critique, task `critique-7182-design-r2-codex`, GPT-seat
> critic origin of the proposal).

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
- **`fixture_context(root)`** — builds a context entirely rooted under one temp directory. This is
  where the #7284 deny-connect-outside-root guard becomes structural: a fixture context simply has no
  path outside `root` to resolve to, instead of relying on a test to patch module globals and hope
  every code path respects the patch.

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

| Step | Family | Notes |
| --- | --- | --- |
| 0 | **Core** | `MonitorContext` + `create_app` + `production_context`/`fixture_context`. `main.py` calls the factory. **No router changes.** Pure no-op — full `tests/api` + the OPSEC sweep must be byte-identical in outcome before/after. This is the step that proves the factory is safe to build on. |
| 1 | session-streams / orient / authority | |
| 2 | comms / fleet / cold-start-board | |
| 3 | docs / artifacts / images | |
| 4 | admin / retention / dashboards | |
| 5 | sources / rag | Folds the #7284 connect-deny guard into the context per §4.1. |
| 6 | the rest | agent / epics / occupancy / delegate / cost / … |

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
3. Deletes the monkeypatch seam(s) the migrated family no longer needs — the shrinking seam count
   *is* the proof this migration is real and not just added abstraction on top of the old globals.

## 8. Sequencing

1. Formalize this doc (this step).
2. One cross-family design review (codex seat) on this doc.
3. File one sub-issue per family (step 0–6 above) under #7269, each scoped to exactly its family's
   router set and its own CF review.
4. Implement step 0 first and only step 0 — it is the dependency for every later step and is the
   step most likely to reveal a wrong assumption in this doc before six more PRs build on it.
5. Implement steps 1–6 in order, one PR at a time, each gated on the previous step's sweep+tests
   staying green.

## 9. Open questions / risks

- **`fixture_context` root discipline**: every store/root the context opens must resolve strictly
  under the given root with no fallback to a module-level default — this is the entire point of §4.1;
  step 0's review should specifically check for any lazy-open path that could silently fall back to a
  production path when a fixture value is unset.
- **Ordering within a family**: some routers in the same family may share a store handle (e.g.
  comms/fleet both touch the message DB) — family PRs should migrate all routers sharing a store
  together to avoid a half-migrated state where the same store is reached through two different paths
  (module global + context) simultaneously.
