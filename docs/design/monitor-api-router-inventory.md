# Monitor API Router Dependency & Seam Inventory

> **Parent design:** [`monitor-api-app-factory.md`](monitor-api-app-factory.md) §5.2 (step 0.5)
> **Issue:** #7269
> **Status:** Live inventory — source of truth for filing per-family sub-issues
> **Generated:** 2026-08-25 (post-#7302 step 0; includes `core_router`)
> **Corrected:** 2026-10-03 (#8522, #9630) — seam tables re-derived from the live fixture; router counts, mount prefixes, route counts and line counts recomputed from `scripts/api/main.py` and the router modules; `batch_router` and `cluster_router` added; `tests/api/test_app_factory_doc_router_count.py` pins them

This document records every router module `scripts/api/main.py` mounts via
`create_app()` → `factory_app.include_router(...)`, the module-global roots/stores
each reads, every OPSEC sweep fixture seam installed on it, and a proposed
migration step grouping per §5.2 point 4 of the parent design.

---

## Evidence preamble (re-run commands)

All counts below were derived from the checked-out worktree at inventory time.
A reviewer can reproduce them with these exact commands.

### Total router-module count — **47** distinct router objects

`main.py` makes **48** `include_router` calls registering **47 distinct router
objects**: 46 imported router modules plus `core_router` (defined inside
`main.py`). Only `docs_router` is registered twice (at `/artifacts` and
`/files`). `reviewer_ghosts_router` uses a multiline `include_router` call.
`telemetry_router`, `batch_router` and `core_router` are mounted without a
prefix.

```bash
grep -c 'include_router' scripts/api/main.py
# 48

.venv/bin/python -c "
import ast
from collections import Counter
from pathlib import Path
tree = ast.parse(Path('scripts/api/main.py').read_text())
calls = Counter(
    ast.unparse(node.args[0])
    for node in ast.walk(tree)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    and node.func.attr == 'include_router' and node.args
)
print(sum(calls.values()), len(calls), [n for n, c in calls.items() if c > 1])
"
# 48 47 ['docs_router']
```

The one-line `grep -oE` form of this count is not authoritative: it breaks on the
multiline `reviewer_ghosts_router` call. The AST parse above is.

### Total route-handler count — **278** decorator sum; **279** OpenAPI HTTP ops + **1** WebSocket

Three separate denominators (do not conflate them):

| Metric | Value | Source |
| --- | ---: | --- |
| Route-handler decorator sum | **278** | `@router.*` (and `@core_router.*` in `main.py`) in each mounted module **once**, plus nested `router.include_router` children (currently only `entire_context_router` inside `ops_router`) |
| OpenAPI HTTP operations | **279** | `FROZEN_HTTP_OPERATION_COUNT` in `tests/api/opsec_sweep/registry.py`; duplicate prefix mounts count twice; **excludes** WebSocket routes |
| WebSocket routes | **1** | `FROZEN_WEBSOCKET_ROUTE_COUNT`; `WS /ws/batch` on `batch_router` — absent from `app.openapi()['paths']` |

Nested mounts (grep `\.include_router(` in `scripts/api/*.py`, excluding
`factory_app.include_router` in `main.py`):

```bash
grep -rn '\.include_router(' scripts/api/*.py | grep -v 'factory_app\.include_router'
# scripts/api/ops_router.py:17:router.include_router(entire_context_router, prefix="/entire-context")
```

Decorator-sum script (complete `ROUTER_MAP`; `NESTED` adds child router files
included via `router.include_router` anywhere under `scripts/api/`):

```bash
.venv/bin/python -c "
import re
from pathlib import Path
ROUTER_MAP = {
    'admin_router': 'scripts/api/admin_router.py',
    'agent_router': 'scripts/api/agent_router.py',
    'agent_monitor_router': 'scripts/api/agent_monitor_router.py',
    'artifacts_router': 'scripts/api/artifacts_router.py',
    'atlas_jobs_router': 'scripts/api/atlas_jobs_router.py',
    'batch_router': 'scripts/api/batch_router.py',
    'blue_router': 'scripts/api/blue_router.py',
    'build_events_router': 'scripts/api/build_events_router.py',
    'cluster_router': 'scripts/api/cluster_router.py',
    'comms_router': 'scripts/api/comms_router.py',
    'contracts_router': 'scripts/api/route_contracts.py',
    'coordination_router': 'scripts/api/coordination_router.py',
    'consultation_router': 'scripts/api/consultation_router.py',
    'cost_router': 'scripts/api/cost_router.py',
    'dashboard_router': 'scripts/api/dashboard_router.py',
    'decisions_router': 'scripts/api/decisions_router.py',
    'delegate_router': 'scripts/api/delegate_router.py',
    'discussions_router': 'scripts/api/discussions_router.py',
    'docs_router': 'scripts/api/docs_router.py',
    'epics_router': 'scripts/api/epics_router.py',
    'fleet_board_router': 'scripts/api/fleet_board/router.py',
    'fleet_router': 'scripts/api/fleet_router.py',
    'fleet_workers_router': 'scripts/api/fleet_workers_router.py',
    'git_hygiene_router': 'scripts/api/git_hygiene_router.py',
    'gold_router': 'scripts/api/gold_router.py',
    'governance_router': 'scripts/api/governance_router.py',
    'images_router': 'scripts/api/images_router.py',
    'issues_router': 'scripts/api/issues_router.py',
    'knowledge_router': 'scripts/api/knowledge_router.py',
    'observer_presence_router': 'scripts/api/observer_presence.py',
    'occupancy_router': 'scripts/api/occupancy.py',
    'ops_router': 'scripts/api/ops_router.py',
    'project_state_router': 'scripts/api/project_state_router.py',
    'reviewer_ghosts_router': 'scripts/api/reviewer_ghosts_router.py',
    'rollover_router': 'scripts/api/rollover_router.py',
    'rules_router': 'scripts/api/rules_router.py',
    'runtime_router': 'scripts/api/runtime_router.py',
    'session_router': 'scripts/api/session_router.py',
    'session_streams_router': 'scripts/api/session_streams_router.py',
    'site_router': 'scripts/api/site_router.py',
    'sources_router': 'scripts/api/sources_router.py',
    'state_router': 'scripts/api/state_router.py',
    'telemetry_router': 'scripts/api/telemetry_router.py',
    'wiki_router': 'scripts/api/wiki_router.py',
    'work_router': 'scripts/api/work_router.py',
    'worktrees_router': 'scripts/api/worktrees_router.py',
    'core_router': 'scripts/api/main.py',
}
NESTED = {
    'ops_router': ['scripts/api/entire_context_router.py'],
}
DECORATOR_PAT = re.compile(
    r'@(router|core_router)\.(get|post|put|delete|patch|websocket|head|options)\('
)
total = 0
for var, path in sorted(ROUTER_MAP.items()):
    text = Path(path).read_text()
    pat = r'@core_router\.' if var == 'core_router' else r'@router\.'
    n = len(re.findall(pat + r'(get|post|put|delete|patch|websocket|head|options)\(', text))
    for nested in NESTED.get(var, []):
        n += len(DECORATOR_PAT.findall(Path(nested).read_text()))
    total += n
print(total)
"
# 278

.venv/bin/python -c "
import sys; sys.path.insert(0,'.')
from scripts.api.main import app
from tests.api.opsec_sweep.registry import FROZEN_HTTP_OPERATION_COUNT, FROZEN_WEBSOCKET_ROUTE_COUNT
print(sum(len(v) for v in app.openapi()['paths'].values()))
print(FROZEN_HTTP_OPERATION_COUNT)
print(FROZEN_WEBSOCKET_ROUTE_COUNT)
"
# 279
# 279
# 1
```

### OPSEC fixture seams — **22** unique `setattr` targets

The seams are what `isolated_fixture` in `tests/api/opsec_sweep/test_opsec_route_sweep.py`
installs today. They were re-derived on 2026-10-03 (#9630) from the live fixture, not from a
copied list: `docs/design/count_opsec_fixture_seams.py` runs the real fixture function against
a recording `pytest.MonkeyPatch` in a fresh interpreter and prints every target. The 2026-08-25
baseline of 198 targets predates the step 5–13 migrations, which deleted the `path_loop`,
`run_command_loop` and `default_plane_root_loop` seams; the per-router sections below record
those deletions.

```bash
.venv/bin/python docs/design/count_opsec_fixture_seams.py          # markdown table
.venv/bin/python docs/design/count_opsec_fixture_seams.py --json   # raw records
```

Counting rules:

1. A **seam** is a unique `(target, attribute)` that the fixture patches with
   `monkeypatch.setattr`, or an environment variable it sets with `monkeypatch.setenv`.
   A target patched twice (a loop and an explicit call) is one seam with two invocations.
2. The recorder covers only the fixture body. Patches that individual tests or mutation
   recipes add (for example `batch_router._run_dispatcher_scan`) are not counted.
3. The fixture's loops walk `sys.modules`, so the result is for a fresh interpreter that has
   imported only the sweep module; a long pytest session can load more modules.
4. A seam is **owned by a router** when its target module is that router's module. That
   is the **Seams** value in each per-router row below. Targets in other modules are totalled
   by category and are not attributed to any single router.

| Target | Kind | Invocations |
| --- | --- | ---: |
| `os.environ.AGENT_NO_TELEMETRY_FOOTER` | env | 1 |
| `os.environ.ATLAS_JOB_REGISTRY` | env | 1 |
| `os.environ.FLEET_COMMS_ROOT` | env | 1 |
| `os.environ.LU_MONITOR_HOST_ID` | env | 1 |
| `os.environ.MONITOR_OCCUPANCY_HOST_IDS` | env | 1 |
| `scripts.api.comms_router.default_plane_root` | setattr | 1 |
| `scripts.api.issues_router._run_gh` | setattr | 1 |
| `scripts.api.main.build_repository_authority` | setattr | 2 |
| `scripts.api.repository_authority.build_repository_authority` | setattr | 1 |
| `scripts.api.state_helpers._ttl_cache` | setattr | 1 |
| `scripts.api.state_router.build_repository_authority` | setattr | 1 |
| `scripts.api.state_router.probe_graphql_budget` | setattr | 1 |
| `scripts.docs.catalogue.git` | setattr | 1 |
| `scripts.orchestration.issue_stream_audit.read_cache` | setattr | 1 |
| `scripts.orchestration.issue_stream_audit.read_refresh_state` | setattr | 1 |
| `scripts.orchestration.issue_stream_audit.schedule_refresh` | setattr | 1 |
| `scripts.orchestration.reap_worktrees._run` | setattr | 1 |
| `scripts.telemetry.legacy_bridge._DB_PATH` | setattr | 1 |
| `socket.create_connection` | setattr | 1 |
| `sqlite3.connect` | setattr | 1 |
| `starlette.datastructures.State.ctx` | setattr | 1 |
| `subprocess.Popen` | setattr | 1 |
| `subprocess.run` | setattr | 1 |
| `wiki.config.WIKI_STATE_DIR` | setattr | 1 |
| `wiki.quality_gate.PROGRESS_DB` | setattr | 1 |
| `wiki.source_attribution.DEFAULT_DB_PATH` | setattr | 1 |
| `wiki.state.WIKI_STATE_DIR` | setattr | 1 |

| Category | Unique targets |
| --- | ---: |
| Router modules (the Seams column below) | 5 |
| Shared API helpers (`scripts.api.*` modules that are not routers) | 2 |
| Other repository modules (`scripts.*` outside `scripts.api`, `wiki.*`) | 10 |
| Application state (`app.state`) | 1 |
| Global backstops (`subprocess`, `socket`, `sqlite3`) | 4 |
| **Unique `setattr` targets** | **22** |
| `setattr` invocations | 23 |
| Environment variables set | 5 |

The four global backstops stay as defense-in-depth per §4.1 point 5 of the parent design
until all routers read stores through `MonitorContext`.

### Per-step module tally — sums to **47**

```
step 1 (4) + step 2 (1) + step 3 (6) + step 4 (1) + step 5 (1) + step 6 (1)
+ step 7 (3) + step 8 (3) + step 9 (1) + step 10 (1) + step 11 (1)
+ step 12a (5) + step 12b (5) + step 12c (5) + step 12d (4) + step 12e (3)
+ step 13 (2) = 47 router objects
```

---

## Proposed migration steps

Grouped by shared store/root clusters per §5.2 point 4. Modules over ~800 lines
get their own step (line sums here are a 2026-10-03 snapshot). `batch_router` and `core_router` are **step 13 (last)** so the catch-all
`/{path:path}` dashboard static handler remains registered after all prefixed
routers (§4.2 core-router-last ordering).

| Step | Modules | Lines (sum) | Rationale |
| --- | --- | ---: | --- |
| **1** | `session_streams_router`, `rollover_router`, `session_router`, `rules_router` | 912 | Session-streams / handoff / rules cluster; shared `LIVE_REPO_ROOT`, session-streams DB |
| **2** | `state_router` | 3,096 | Large; orient/authority/pipeline — see internal route groups |
| **3** | `agent_router`, `agent_monitor_router`, `occupancy_router`, `observer_presence_router`, `fleet_workers_router`, `project_state_router` | 2,207 | Agent monitor DB + occupancy markers + in-memory presence + fleet project-state |
| **4** | `fleet_router` | 2,677 | Large; fleet facade / messages / ACP — see internal route groups |
| **5** | `comms_router` | 2,119 | Large; `MESSAGE_DB` + fleet-comms plane — see internal route groups |
| **6** | `runtime_router` | 1,776 | Large; runtime adapters / ACP / usage telemetry |
| **7** | `docs_router`, `artifacts_router`, `images_router` | 2,082 | Docs `EFFECTIVE_ROOTS` + curriculum artifacts + image/textbook stores |
| **8** | `admin_router`, `ops_router`, `git_hygiene_router` | 1,251 | Admin backup/MCP roots + retention plan dir + git hygiene |
| **9** | `dashboard_router` | 1,061 | Large; dashboard aggregation over curriculum + comms |
| **10** | `sources_router` (`sources_router.py`) | 170 | Sources DB (`SOURCES_DB_PATH`) + #7284 connect guard |
| **11** | `contracts_router` (`route_contracts.py`) | 1,400 | Large; route-contract registry (1 handler, heavy logic) |
| **12a** | `atlas_jobs_router`, `blue_router`, `build_events_router`, `coordination_router`, `cost_router` | 1,121 | Small curriculum/batch-state cluster |
| **12b** | `consultation_router`, `decisions_router`, `delegate_router`, `discussions_router`, `gold_router` | 1,844 | Consultation queue dirs + delegate tasks + `MESSAGE_DB` discussions |
| **12c** | `governance_router`, `issues_router`, `knowledge_router`, `reviewer_ghosts_router`, `cluster_router` | 1,107 | Governance/decisions-adjacent reads + issues/gh seam + cluster readiness probe over the control-plane stores |
| **12d** | `site_router`, `wiki_router`, `worktrees_router`, `telemetry_router` | 1,594 | Site build + wiki `SOURCES_DB_PATH` + worktrees git + telemetry DBs |
| **12e** | `work_router`, `epics_router`, `fleet_board_router` | 2,114 | Work projection cache + epics `SessionStreamStore` (both ≥600 lines) + fleet board v1 |
| **13** | `batch_router`, `core_router` (`main.py` inline) | 2,112 | **Last two mounts, in this order** — batch dispatcher/active/usage routes + `WS /ws/batch` (split out of `main.py`), then health/orient/config routes + catch-all static; read config through `Depends(get_ctx)`, no dedicated store of their own |

---

## Per-router inventory

Columns: **Module** · **Mount prefix(es)** · **Routes** · **Lines** ·
**Config imports** (`scripts/api/config.py`) · **Module globals** ·
**OPSEC seams** (count) · **Step**

The **Seams** value is the number of unique `setattr` targets `isolated_fixture`
installs on that router's module; see *OPSEC fixture seams* above for the rules and the
full target list. The tests in `tests/api/test_router_inventory_seams.py` re-derive it.

### Step 1 — session-streams cluster

| Module | Mount prefix(es) | Routes | Lines | Config imports | Module globals | Seams | Step |
| --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `session_streams_router.py` | `/api/session-streams` | 6 | 213 | — | `_repo_root()`, `_db_path()`, `_store()` | 0 | 1 |
| `rollover_router.py` | `/api/rollovers` | 1 | 136 | — | — | 0 | 1 |
| `session_router.py` | `/api/session` | 1 | 295 | — | `ORCHESTRATOR_HANDOFF_PATH`, `LEGACY_ORCHESTRATOR_HANDOFF_PATH`, `SESSION_ROUTER_PATH` | 0 | 1 |
| `rules_router.py` | `/api/rules` | 1 | 268 | — | — | 0 | 1 |

### Step 2 — `state_router` (large)

| Module | Mount prefix(es) | Routes | Lines | Config imports | Module globals | Seams | Step |
| --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `state_router.py` | `/api/state` | 28 | 3,096 | `LEVELS` | `BUDGET_CONFIG_PATH`, `TASKS_DIR` | 2 | 2 |

**Internal route groups** (may split 2a/2b if a single PR exceeds review size):

| Group | Routes | Paths (representative) |
| --- | ---: | --- |
| Pipeline / preparation | 8 | `/routing-budget`, `/summary`, `/pipeline/{track_id}`, `/pipeline-versions`, `/preparation`, `/preparation/{track}/{slug}`, `/ready-to-build`, `/weak-points` |
| Research / review quality | 6 | `/failing`, `/scores/{track}`, `/scores/{track}/{slug}`, `/research-coverage`, `/research/{track_id}`, `/review-coverage` |
| Build status / modules | 10 | `/build-status`, `/build-status/{track_id}`, `/module-range/{track_id}`, `/llm-qg/{track_id}`, `/build-stats`, `/build-stats/{track_id}`, `/module/{track_id}/{num}`, `/module/{track_id}/slug/{slug}`, `/final-reviews/{track_id}`, `/enrichment-status` |
| Issues / manifest | 4 | `/track-health/{track_id}`, `/issues`, `/range/{track_id}`, `/manifest` |

**`state_router` seams (2):** `build_repository_authority`, `probe_graphql_budget`.

### Step 3 — agent / occupancy / fleet-workers cluster

| Module | Mount prefix(es) | Routes | Lines | Config imports | Module globals | Seams | Step |
| --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `agent_router.py` | `/api/agent` | 5 | 219 | — | — | 0 | 3 |
| `agent_monitor_router.py` | `/api/agent-monitor` | 6 | 419 | — | `DB_PATH` | 0 | 3 |
| `occupancy.py` | `/api/occupancy` | 1 | 836 | — | — (reads env + `occupancy_local._MARKERS_REL`) | 0 | 3 |
| `observer_presence.py` | `/api/observer` | 1 | 331 | — | `_STORE`, `_STORE_LOCK` (in-memory presence) | 0 | 3 |
| `fleet_workers_router.py` | `/api/fleet` + router `prefix=/workers/v1` | 1 | 41 | — | — (delegates to `fleet_workers_collect`) | 0 | 3 |
| `project_state_router.py` | `/api/fleet` | 2 | 361 | — | — | 0 | 3 |

### Step 4 — `fleet_router` (large)

| Module | Mount prefix(es) | Routes | Lines | Config imports | Module globals | Seams | Step |
| --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `fleet_router.py` | `/api/fleet` | 27 | 2,677 | — | — (uses `default_plane_root`, `legacy_comms.MESSAGE_DB` at call time) | 0 | 4 |

**Internal route groups:**

| Group | Routes | Paths (representative) |
| --- | ---: | --- |
| Facade / cold-start | 9 | `/facade`, `/facade/help`, `/facade/status`, `/facade/board`, `/facade/metrics`, `/facade/backlog`, `/facade/dead`, `/facade/broker-report`, `/facade/reap-report` |
| Operations / overview | 5 | `/operations`, `/health`, `/overview`, `/agents`, `/endpoints` |
| Messages / discussions / reviews | 8 | `/requests`, `/messages`, `/messages/{message_id}`, `/discussions`, `/discussions/{conversation_id}`, `/reviews`, `/reviews/{review_id}`, `/dead-letters` |
| Authority / ACP / activity | 5 | `/authority/jobs`, `/migrations`, `/acp/conversations`, `/acp/conversations/{conversation_id}`, `/activity` |

### Step 5 — `comms_router` (large)

| Module | Mount prefix(es) | Routes | Lines | Config imports | Module globals | Seams | Step |
| --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `comms_router.py` | `/api/comms` | 26 | 2,119 | — | `LOG_DIR`, `PID_DIR` | 1 | 5 |

**Internal route groups:**

| Group | Routes | Paths (representative) |
| --- | ---: | --- |
| Legacy (deprecated) | 5 | `/messages`, `/conversations`, `/conversation/{task_id}`, `/live-activity`, `/send` |
| Health / plane / batch | 7 | `/active-processes`, `/zombies`, `/stats`, `/health`, `/v1/plane-status`, `/batch-progress`, `/batch-progress/{track}` |
| Channels | 8 | `/channels`, `/channels/{name}`, `/channels/{name}/messages`, `/channels/{name}/threads/{thread_id}`, `/channels/{name}/deliveries`, `/channels/{name}/post`, `/cleanup`, `/acknowledge/{message_id}` |
| Inbox / v1 metrics | 6 | `/by-module/{track}/{slug}`, `/agent-activity`, `/inbox`, `/v1/backlog`, `/v1/dead-letters`, `/v1/metrics` |

**`comms_router` seams (1):** `default_plane_root`.

### Step 6 — `runtime_router` (large)

| Module | Mount prefix(es) | Routes | Lines | Config imports | Module globals | Seams | Step |
| --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `runtime_router.py` | `/api/runtime` | 11 | 1,776 | — | `ADAPTERS_DIR`, `REGISTRY_PATH`, `USAGE_DIR` | 0 | 6 |

**Internal route groups:** agents/usage (`/agents`, `/usage`, `/recent`);
ACP (`/acpx`, `/acp/conversations/*`); routing/transport (`/headroom`,
`/routing-assignments`, `/transport-health`, `/auth`).

### Step 7 — docs / artifacts / images

| Module | Mount prefix(es) | Routes | Lines | Config imports | Module globals | Seams | Step |
| --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `docs_router.py` | `/artifacts`, `/files` | 2 | 449 | — | `ALLOWED_ROOTS`, `DISCOVERY_ROOTS`, `EFFECTIVE_ROOTS` | 0 | 7 |
| `artifacts_router.py` | `/api/artifacts` | 7 | 879 | `LEVELS` | `PLANS_ROOT` | 0 | 7 |
| `images_router.py` | `/api/images` | 9 | 754 | — | `IMAGES_DIR`, `TEXTBOOKS_DIR`, `ANNOTATIONS_FILE`, `_index`, `_pdf_pool`, `_page_cache`, `_pdf_page_count_cache` | 0 | 7 |

### Step 8 — admin / ops / git

| Module | Mount prefix(es) | Routes | Lines | Config imports | Module globals | Seams | Step |
| --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `admin_router.py` | `/api/admin` | 8 | 402 | — | `BACKUP_DIR`, `DATA_DIR`, `IMAGE_DIR`, `LOGS_DIR`, `MCP_DIR` | 0 | 8 |
| `ops_router.py` | `/api/ops` (+ nested `/entire-context`) | 4 | 74 | — | `DEFAULT_PLAN_DIR` | 0 | 8 |
| `git_hygiene_router.py` | `/api/git` | 2 | 775 | — | `POLICY_DOC` | 0 | 8 |

### Step 9 — `dashboard_router` (large)

| Module | Mount prefix(es) | Routes | Lines | Config imports | Module globals | Seams | Step |
| --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `dashboard_router.py` | `/api/dashboard` | 11 | 1,061 | `LEVELS`, `SEMINAR_TRACK_IDS` | — | 0 | 9 |

**Internal route groups:** overview/research/track (`/overview`, `/research`,
`/track/*`, `/pipeline`, `/activity-config`); comms embed
(`/comms`, `/comms/message/{message_id}`, `/comms/conversation/{task_id}`,
`/comms/messages`).

### Step 10 — `sources_router` / RAG

| Module | Mount prefix(es) | Routes | Lines | Config imports | Module globals | Seams | Step |
| --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `sources_router.py` | `/api/sources` | 4 | 170 | — | — | 0 | 10 |

### Step 11 — `contracts_router` / route contracts (large)

| Module | Mount prefix(es) | Routes | Lines | Config imports | Module globals | Seams | Step |
| --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `route_contracts.py` (`contracts_router`) | `/api/contracts` | 1 | 1,400 | — | — | 0 | 11 |

Single route (`/routes`) but ~1.3k lines of contract registry logic — own step.

### Step 12a — curriculum / batch small batch

| Module | Mount prefix(es) | Routes | Lines | Config imports | Module globals | Seams | Step |
| --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `atlas_jobs_router.py` | `/api/atlas-jobs` | 7 | 530 | — | `_HOST_LOAD_CACHE` | 0 | 12a |
| `blue_router.py` | `/api/blue` | 7 | 331 | — | — | 0 | 12a |
| `build_events_router.py` | `/api/build/events` | 2 | 168 | — | — | 0 | 12a |
| `coordination_router.py` | `/api/coordination` | 3 | 46 | — | — | 0 | 12a |
| `cost_router.py` | `/api/analytics/cost` | 3 | 46 | — | — | 0 | 12a |

**12a migrated (#7330):** path roots now come from `Depends(get_ctx)`. The 7 seams this row listed (`atlas_job.registry_dir`, `atlas_job.primary_checkout_root`, plus the five module-level Path imports on blue / build-events / coordination) are deleted.

### Step 12b — consultation / delegate / discussions

| Module | Mount prefix(es) | Routes | Lines | Config imports | Module globals | Seams | Step |
| --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `consultation_router.py` | `/api/consultation` | 7 | 523 | `LEVELS` | — | 0 | 12b |
| `decisions_router.py` | `/api/decisions` | 6 | 194 | — | `_cache`, `_lineage_cache` | 0 | 12b |
| `delegate_router.py` | `/api/delegate` | 3 | 640 | — | `_LAST_TASKS_DIR_STR`, `_TASK_STATE_CACHE` | 0 | 12b |
| `discussions_router.py` | `/api/discussions` | 1 | 130 | — | — | 0 | 12b |
| `gold_router.py` | `/api/gold` | 8 | 357 | — | — | 0 | 12b |

**12b migrated (#7331):** path roots now come from `Depends(get_ctx)`. The 14 seams this row listed (the path-loop seams on consultation / decisions / delegate / discussions / gold) are deleted.

### Step 12c — governance / issues / knowledge / cluster

| Module | Mount prefix(es) | Routes | Lines | Config imports | Module globals | Seams | Step |
| --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `governance_router.py` | `/api/state/governance` | 1 | 191 | — | — | 0 | 12c |
| `issues_router.py` | `/api/issues` | 2 | 259 | — | — | 1 | 12c |
| `knowledge_router.py` | `/api/knowledge` | 5 | 238 | — | — | 0 | 12c |
| `reviewer_ghosts_router.py` | `/api/state/reviewer-ghosts` | 1 | 187 | `LEVELS` | — | 0 | 12c |
| `cluster_router.py` | `/api/cluster` | 1 | 232 | — | `_ACTIVE_STORES` (constant `StoreId` tuple; stores are probed through `ctx` and the `control_plane.storage` seam) | 0 | 12c |

**12c migrated (#7333 dispatch / inventory step 12c):** path roots now come from
`Depends(get_ctx)`. The 6 Path seams this row listed (`DECISIONS_FILE`,
`path_loop:PROJECT_ROOT` on governance / hermes / issues, `CURRICULUM_ROOT` on
reviewer-ghosts, plus the `collect_adr_governance` fixture stub) are deleted.
`issues_router._run_gh` stays — it is the subprocess deny stub, not a Path
global. `LEVELS` is track-id config, not a filesystem root.

**`cluster_router` seams (0):** added to the inventory by #8522 (mounted at
`/api/cluster`, readiness probe from #7493). `isolated_fixture` installs no target on
`cluster_router`; it reads stores through `Depends(get_ctx)` and `resolve_context` only.

### Step 12d — site / wiki / worktrees / telemetry

| Module | Mount prefix(es) | Routes | Lines | Config imports | Module globals | Seams | Step |
| --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `site_router.py` | `/api/site` | 2 | 304 | — | — | 0 | 12d |
| `wiki_router.py` | `/api/wiki` | 8 | 477 | `LEVELS` | — | 0 | 12d |
| `worktrees_router.py` | `/api/worktrees` | 1 | 231 | — | — | 0 | 12d |
| `telemetry_router.py` | (none — router defines own prefix) | 7 | 582 | — | — | 0 | 12d |

**12d migrated (#7333):** path roots and database handles now come from
`Depends(get_ctx)`. The 15 Path and router-local subprocess seams this row listed
(`site_router` 4 Path globals + `_run` stub, `worktrees_router` 2 Path globals +
`_run` stub, `telemetry_router` 3 Path globals, `wiki_router` 4 router-local Path
globals) are deleted. `reap_worktrees._run`, `scripts.telemetry.legacy_bridge._DB_PATH`,
and `wiki.{config,state}.WIKI_STATE_DIR` (2) remain for external store redirection.
The unused `wiki.sources_db.SOURCES_DB_PATH` and dense rerank defaults (4) are deleted.

### Step 12e — work / epics

| Module | Mount prefix(es) | Routes | Lines | Config imports | Module globals | Seams | Step |
| --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `work_router.py` | `/api/work` | 4 | 790 | — | `_IN_FLIGHT_BUILDS` | 0 | 12e |
| `epics_router.py` | `/api/epics` | 12 | 1,158 | — | — | 0 | 12e |
| `fleet_board.router.py` | `/api/fleet/v1` | 7 | 166 | — | — | 0 | 12e |

**12e migrated (#7334):** stores and live repo root now come from
`Depends(get_ctx)`. The 3 seams this row listed (`work_router._IN_FLIGHT_BUILDS`
fixture setattr, `epics_router._store` fixture setattr, and
`path_loop:LIVE_REPO_ROOT`) are deleted.

### Step 13 — `batch_router` and `core_router` (last)

| Module | Mount prefix(es) | Routes | Lines | Config imports | Module globals | Seams | Step |
| --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `batch_router.py` | (none — absolute paths) | 9 | 182 | — | `DISPATCHER_SCAN_TIMEOUT_S`, `_JSON_LOAD_ERRORS` (constants only) | 0 | 13 |
| `main.py` (`core_router`) | (none — absolute paths) | 6 | 1,930 | `LEVELS` | — | 1 | 13 |

**`batch_router` seams (0):** added to the inventory by #8522. It holds the nine
batch routes that earlier revisions of this document counted under `core_router`.
`isolated_fixture` installs no target on it. A per-recipe patch of
`batch_router._run_dispatcher_scan` exists in
`tests/api/opsec_sweep/mutation_recipes.py`, but that is a mutation-recipe
fixture, not `isolated_fixture`, so it is not counted.

**`core_router` seams (1, module `main`):** `build_repository_authority`.

**13 migrated (#7335) & Residual Cleanup (#7269):** the inline routes and orient collectors read roots from `Depends(get_ctx)`. The `path_loop` rewrites (`scripts.api.config.{BATCH_STATE_DIR, CURRICULUM_ROOT, DASHBOARDS_DIR, LIVE_REPO_ROOT, MESSAGE_DB, PROJECT_ROOT}` and `scripts.api.resilience._REPO_ROOT`), `scripts.fleet_comms.legacy_broker_report.main_checkout_root`, and 4 unused `wiki.*` / RAG defaults are deleted.

**`batch_router` routes (9):** `/api/batch/dispatcher`, `/api/batch/active`,
`/api/batch/failures`, `/api/batch/usage`, `/api/batch/checkpoints`,
`/api/batch/dispatcher/running`, `POST /api/batch/dispatcher/scan`,
`/api/batch/dispatcher/logs`, `WS /ws/batch`.

**`core_router` routes (6):** `/api` (redirect), `/api/health`, `/api/orient`,
`/api/config`, `/images/{path:path}`, `/{path:path}` (dashboard catch-all).

**Why last:** The `/{path:path}` catch-all serves dashboard static files and must
stay registered after all `/api/*` prefixed routers (§4.2). `create_app()` mounts
`batch_router` and then `core_router` as its final two calls. The #7302
migration moved the inline handlers onto `core_router`; the batch routes were
later split into `batch_router`. Neither has a separate `_repo_root` / `_store`
beyond the config imports and module globals listed above.

---

## Summary accounting

| Metric | Value |
| --- | ---: |
| Router registrations (`include_router` calls) | 48 |
| Distinct router objects (46 imported modules + `core_router`) | 47 |
| Routers mounted twice | 1 (`docs_router`) |
| Route handlers (decorator sum, nested included) | 278 |
| OpenAPI HTTP operations (sweep denominator) | 279 |
| WebSocket routes (separate denominator) | 1 |
| OPSEC fixture `setattr` targets (unique; see *OPSEC fixture seams*) | 22 |

**Full step accounting:**

```
step 1 (4) + step 2 (1) + step 3 (6) + step 4 (1) + step 5 (1) + step 6 (1)
+ step 7 (3) + step 8 (3) + step 9 (1) + step 10 (1) + step 11 (1)
+ step 12a (5) + step 12b (5) + step 12c (5) + step 12d (4) + step 12e (3)
+ step 13 (2) = 47 router objects
```

---

## Deviations from parent design provisional table (§5.2)

| Provisional | Inventory correction |
| --- | --- |
| 44 modules (pre-#7302) | **46** distinct router objects — adds `core_router` in `main.py`, `batch_router` and `cluster_router` |
| Step 12 as one 21-module batch | Split into **12a–12e** (≤5 modules per sub-step) |
| `core_router` absent | **Step 13 (last, with `batch_router`)** — catch-all route ordering |
| `rag_router.py` naming | The module is `sources_router.py` (the old `rag_router.py` file no longer exists); it is mounted once, at `/api/sources` |

Sub-issues under #7269 should be filed from this inventory, not the provisional
table in the parent design doc.
