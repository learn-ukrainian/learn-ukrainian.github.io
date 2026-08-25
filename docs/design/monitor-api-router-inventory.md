# Monitor API Router Dependency & Seam Inventory

> **Parent design:** [`monitor-api-app-factory.md`](monitor-api-app-factory.md) §5.2 (step 0.5)
> **Issue:** #7269
> **Status:** Live inventory — source of truth for filing per-family sub-issues
> **Generated:** 2026-08-25 (post-#7302 step 0; includes `core_router`)

This document records every router module `scripts/api/main.py` mounts via
`create_app()` → `factory_app.include_router(...)`, the module-global roots/stores
each reads, every OPSEC sweep monkeypatch seam attributed to it, and a proposed
migration step grouping per §5.2 point 4 of the parent design.

---

## Evidence preamble (re-run commands)

All counts below were derived from the checked-out worktree at inventory time.
A reviewer can reproduce them with these exact commands.

### Total router-module count — **45**

`main.py` makes **48** `include_router` calls mounting **45 unique** router
modules (`cost_router`, `docs_router`, and `sources_router` are each mounted at
two prefixes; `reviewer_ghosts_router` uses a multiline `include_router` call).

```bash
grep -c 'include_router' scripts/api/main.py
# 48

/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python -c "
import ast
from pathlib import Path
tree = ast.parse(Path('scripts/api/main.py').read_text())
mods = set()
for node in ast.walk(tree):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'include_router':
        if node.args and isinstance(node.args[0], ast.Name):
            mods.add(node.args[0].id)
print(len(mods))
"
# 45
```

The design-doc one-liner
`grep -oE 'app\.include_router\(\s*\n?\s*[a-zA-Z_]+' … | sort -u | wc -l`
returns **44** against the current tree: it truncates names when the opening
parenthesis is immediately followed by a newline (`session_router` →
`ession_router`, etc.) and misses the multiline `reviewer_ghosts_router` mount.
The AST parse above is authoritative.

### Total route-handler count — **269** (OpenAPI operations — **280**)

Per-module counts sum `@router.*` / `@core_router.*` decorators (one handler per
route definition; double-mounted modules are counted once). OpenAPI operation
count includes duplicate prefix mounts and the `/ws/batch` websocket.

```bash
/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python -c "
import re
from pathlib import Path
ROUTER_MAP = { ... }  # see inventory table module paths
total = 0
for var, path in sorted(ROUTER_MAP.items()):
    text = Path(path).read_text()
    pat = r'@core_router\.' if var == 'core_router' else r'@router\.'
    total += len(re.findall(pat + r'(get|post|put|delete|patch|websocket|head|options)\(', text))
print(total)
"
# 269

/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python -c "
import sys; sys.path.insert(0,'.')
from scripts.api.main import app
print(sum(len(v) for v in app.openapi()['paths'].values()))
"
# 280
```

### Total OPSEC seam-count baseline — **166**

**162** seams attributed to router modules below, plus **4** global
infrastructure backstops (`subprocess.run`, `subprocess.Popen`,
`socket.create_connection`, `sqlite3.connect`) that are not owned by any single
router but stay until the migration completes.

```bash
grep -c 'monkeypatch\.setattr' tests/api/opsec_sweep/test_opsec_route_sweep.py
# 61   (static call sites; loops expand to more logical seams at runtime)
```

The **166** baseline counts every logical seam the `isolated_fixture` in
`tests/api/opsec_sweep/test_opsec_route_sweep.py` installs: explicit
`monkeypatch.setattr` targets **plus** one seam per absolute `Path` module-global
repointed by the `scripts.api` scan loop, one per `_run_command` replacement,
one per `default_plane_root` replacement, and external-store loops for
`wiki`/`telemetry`/`ai_agent_bridge` modules consumed by router routes. Per-router
tallies in the table sum to **162**; adding the 4 global backstops yields **166**.

### Per-step module tally — sums to **45**

```
step 1 (4) + step 2 (1) + step 3 (6) + step 4 (1) + step 5 (1) + step 6 (1)
+ step 7 (3) + step 8 (3) + step 9 (1) + step 10 (1) + step 11 (1)
+ step 12a (5) + step 12b (5) + step 12c (5) + step 12d (4) + step 12e (2)
+ step 13 (1) = 45 modules
```

---

## Proposed migration steps

Grouped by shared store/root clusters per §5.2 point 4. Modules over ~800 lines
get their own step. `core_router` is **step 13 (last)** so the catch-all
`/{path:path}` dashboard static handler remains registered after all prefixed
routers (§4.2 core-router-last ordering).

| Step | Modules | Lines (sum) | Rationale |
| --- | --- | ---: | --- |
| **1** | `session_streams_router`, `rollover_router`, `session_router`, `rules_router` | 861 | Session-streams / handoff / rules cluster; shared `LIVE_REPO_ROOT`, session-streams DB |
| **2** | `state_router` | 2,433 | Large; orient/authority/pipeline — see internal route groups |
| **3** | `agent_router`, `agent_monitor_router`, `occupancy_router`, `observer_presence_router`, `fleet_workers_router`, `project_state_router` | 1,563 | Agent monitor DB + occupancy markers + in-memory presence + fleet project-state |
| **4** | `fleet_router` | 2,637 | Large; fleet facade / messages / ACP — see internal route groups |
| **5** | `comms_router` | 1,898 | Large; `MESSAGE_DB` + fleet-comms plane — see internal route groups |
| **6** | `runtime_router` | 1,729 | Large; runtime adapters / ACP / usage telemetry |
| **7** | `docs_router`, `artifacts_router`, `images_router` | 1,949 | Docs `EFFECTIVE_ROOTS` + curriculum artifacts + image/textbook stores |
| **8** | `admin_router`, `ops_router`, `git_hygiene_router` | 1,200 | Admin backup/MCP roots + retention plan dir + git hygiene |
| **9** | `dashboard_router` | 996 | Large; dashboard aggregation over curriculum + comms |
| **10** | `sources_router` (`rag_router.py`) | 139 | Sources DB (`SOURCES_DB_PATH`) + #7284 connect guard |
| **11** | `contracts_router` (`route_contracts.py`) | 1,356 | Large; route-contract registry (1 handler, heavy logic) |
| **12a** | `atlas_jobs_router`, `blue_router`, `build_events_router`, `coordination_router`, `cost_router` | 1,119 | Small curriculum/batch-state cluster |
| **12b** | `consultation_router`, `decisions_router`, `delegate_router`, `discussions_router`, `gold_router` | 1,690 | Consultation queue dirs + delegate tasks + `MESSAGE_DB` discussions |
| **12c** | `governance_router`, `hermes_cron_router`, `issues_router`, `knowledge_router`, `reviewer_ghosts_router` | 812 | Governance/decisions-adjacent reads + issues/gh seam |
| **12d** | `site_router`, `wiki_router`, `worktrees_router`, `telemetry_router` | 1,470 | Site build + wiki `SOURCES_DB_PATH` + worktrees git + telemetry DBs |
| **12e** | `work_router`, `epics_router` | 1,487 | Work projection cache + epics `SessionStreamStore` (both ≥600 lines) |
| **13** | `core_router` (`main.py` inline) | 1,949 | **Last** — health/orient/batch inline routes + catch-all static + websocket; reads broad config roots but no dedicated store of its own |

---

## Per-router inventory

Columns: **Module** · **Mount prefix(es)** · **Routes** · **Lines** ·
**Config imports** (`scripts/api/config.py`) · **Module globals** ·
**OPSEC seams** (count) · **Step**

Seam lists name the patched target as it appears in
`tests/api/opsec_sweep/test_opsec_route_sweep.py`. `path_loop:` entries are
created by the fixture's `scripts.api` absolute-`Path` scan loop.

### Step 1 — session-streams cluster

| Module | Mount prefix(es) | Routes | Lines | Config imports | Module globals | Seams | Step |
| --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `session_streams_router.py` | `/api/session-streams` | 6 | 218 | `LIVE_REPO_ROOT`, `PROJECT_ROOT` | `_repo_root()`, `_db_path()`, `_store()` | 9 | 1 |
| `rollover_router.py` | `/api/rollovers` | 1 | 132 | `LIVE_REPO_ROOT` | — | 1 | 1 |
| `session_router.py` | `/api/session` | 1 | 287 | `PROJECT_ROOT` | `ORCHESTRATOR_HANDOFF_PATH`, `LEGACY_ORCHESTRATOR_HANDOFF_PATH`, `SESSION_ROUTER_PATH` | 1 | 1 |
| `rules_router.py` | `/api/rules` | 1 | 223 | `PROJECT_ROOT` | — | 1 | 1 |

**`session_streams_router` seams (9):** `session_streams_router._repo_root`,
`_db_path`, `_store`, `list_handoff_candidates`, `diagnose_handoff`,
`list_projection_receipts`, `detect_projection_drift`; `path_loop:LIVE_REPO_ROOT`,
`path_loop:PROJECT_ROOT`.

### Step 2 — `state_router` (large)

| Module | Mount prefix(es) | Routes | Lines | Config imports | Module globals | Seams | Step |
| --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `state_router.py` | `/api/state` | 28 | 2,433 | `CURRICULUM_ROOT`, `LEVELS`, `LIVE_REPO_ROOT`, `PROJECT_ROOT` | `BUDGET_CONFIG_PATH`, `TASKS_DIR` | 14 | 2 |

**Internal route groups** (may split 2a/2b if a single PR exceeds review size):

| Group | Routes | Paths (representative) |
| --- | ---: | --- |
| Pipeline / preparation | 8 | `/routing-budget`, `/summary`, `/pipeline/{track_id}`, `/pipeline-versions`, `/preparation`, `/preparation/{track}/{slug}`, `/ready-to-build`, `/weak-points` |
| Research / review quality | 6 | `/failing`, `/scores/{track}`, `/scores/{track}/{slug}`, `/research-coverage`, `/research/{track_id}`, `/review-coverage` |
| Build status / modules | 10 | `/build-status`, `/build-status/{track_id}`, `/module-range/{track_id}`, `/llm-qg/{track_id}`, `/build-stats`, `/build-stats/{track_id}`, `/module/{track_id}/{num}`, `/module/{track_id}/slug/{slug}`, `/final-reviews/{track_id}`, `/enrichment-status` |
| Issues / manifest | 4 | `/track-health/{track_id}`, `/issues`, `/range/{track_id}`, `/manifest` |

**`state_router` seams (14):** `state_helpers._ttl_cache`,
`_content_file_index_cache`, `_curriculum_cache`, `_curriculum_mtime`;
`repository_authority._git`, `classify_repo_path`; `entire_context_router.projection_path`,
`load_provider_status`, `load_provider_capabilities`; `path_loop:CURRICULUM_ROOT`,
`LIVE_REPO_ROOT`, `PROJECT_ROOT`, `BUDGET_CONFIG_PATH`, `TASKS_DIR`.

### Step 3 — agent / occupancy / fleet-workers cluster

| Module | Mount prefix(es) | Routes | Lines | Config imports | Module globals | Seams | Step |
| --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `agent_router.py` | `/api/agent` | 5 | 212 | `LIVE_REPO_ROOT`, `PROJECT_ROOT` | — | 3 | 3 |
| `agent_monitor_router.py` | `/api/agent-monitor` | 6 | 411 | `BATCH_STATE_DIR` | `DB_PATH` | 2 | 3 |
| `occupancy.py` | `/api/occupancy` | 1 | 505 | — | — (reads env + `occupancy_local._MARKERS_REL`) | 0 | 3 |
| `observer_presence.py` | `/api/observer` | 1 | 298 | — | `_STORE`, `_STORE_LOCK` (in-memory presence) | 0 | 3 |
| `fleet_workers_router.py` | `/api/fleet` + router `prefix=/workers/v1` | 1 | 19 | — | — (delegates to `fleet_workers_collect`) | 0 | 3 |
| `project_state_router.py` | `/api/fleet` | 2 | 163 | — | — | 2 | 3 |

**`agent_router` seams (3):** `path_loop:LIVE_REPO_ROOT`, `PROJECT_ROOT`;
`run_command_loop:agent_router._run_command`.

**`project_state_router` seams (2):** `allowed_reporter_host_ids`;
`project_state_collect._git`.

### Step 4 — `fleet_router` (large)

| Module | Mount prefix(es) | Routes | Lines | Config imports | Module globals | Seams | Step |
| --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `fleet_router.py` | `/api/fleet` | 27 | 2,637 | `LIVE_REPO_ROOT`, `PROJECT_ROOT` | — (uses `default_plane_root`, `legacy_comms.MESSAGE_DB` at call time) | 8 | 4 |

**Internal route groups:**

| Group | Routes | Paths (representative) |
| --- | ---: | --- |
| Facade / cold-start | 8 | `/facade`, `/facade/help`, `/facade/status`, `/facade/board`, `/facade/metrics`, `/facade/backlog`, `/facade/dead`, `/facade/broker-report`, `/facade/reap-report` |
| Operations / overview | 5 | `/operations`, `/health`, `/overview`, `/agents`, `/endpoints` |
| Messages / discussions / reviews | 8 | `/requests`, `/messages`, `/messages/{message_id}`, `/discussions`, `/discussions/{conversation_id}`, `/reviews`, `/reviews/{review_id}`, `/dead-letters` |
| Authority / ACP / activity | 6 | `/authority/jobs`, `/migrations`, `/acp/conversations`, `/acp/conversations/{conversation_id}`, `/activity` |

**`fleet_router` seams (8):** `cold_start_board._get_local_git_info`,
`_resolve_session_streams_db`, `_probe_gh_pr_list`, `default_plane_root`;
`fleet_router.build_cold_start_board` (seam-honesty test); `path_loop:LIVE_REPO_ROOT`,
`PROJECT_ROOT`; `default_plane_root_loop:fleet_router`.

### Step 5 — `comms_router` (large)

| Module | Mount prefix(es) | Routes | Lines | Config imports | Module globals | Seams | Step |
| --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `comms_router.py` | `/api/comms` | 26 | 1,898 | `CURRICULUM_ROOT`, `MESSAGE_DB`, `PROJECT_ROOT` | `LOG_DIR`, `PID_DIR` | 7 | 5 |

**Internal route groups:**

| Group | Routes | Paths (representative) |
| --- | ---: | --- |
| Legacy (deprecated) | 5 | `/messages`, `/conversations`, `/conversation/{task_id}`, `/live-activity`, `/send` |
| Health / plane / batch | 6 | `/active-processes`, `/zombies`, `/stats`, `/health`, `/v1/plane-status`, `/batch-progress`, `/batch-progress/{track}` |
| Channels | 7 | `/channels`, `/channels/{name}`, `/channels/{name}/messages`, `/channels/{name}/threads/{thread_id}`, `/channels/{name}/deliveries`, `/channels/{name}/post`, `/cleanup`, `/acknowledge/{message_id}` |
| Inbox / v1 metrics | 8 | `/by-module/{track}/{slug}`, `/agent-activity`, `/inbox`, `/v1/backlog`, `/v1/dead-letters`, `/v1/metrics` |

**`comms_router` seams (7):** `broker_report.main_checkout_root`;
`message_plane.default_plane_root`; `path_loop:CURRICULUM_ROOT`, `MESSAGE_DB`,
`PROJECT_ROOT`, `PID_DIR`, `LOG_DIR`.

### Step 6 — `runtime_router` (large)

| Module | Mount prefix(es) | Routes | Lines | Config imports | Module globals | Seams | Step |
| --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `runtime_router.py` | `/api/runtime` | 11 | 1,729 | `BATCH_STATE_DIR`, `PROJECT_ROOT` | `ADAPTERS_DIR`, `REGISTRY_PATH`, `USAGE_DIR` | 8 | 6 |

**Internal route groups:** agents/usage (`/agents`, `/usage`, `/recent`);
ACP (`/acpx`, `/acp/conversations/*`); routing/transport (`/headroom`,
`/routing-assignments`, `/transport-health`, `/auth`).

**`runtime_router` seams (8):** `path_loop:BATCH_STATE_DIR`, `PROJECT_ROOT`,
`CODEX_TRANSPORT_CONFIG_PATH`, `CODEX_TRANSPORT_RECEIPT_PATH`, `ADAPTERS_DIR`,
`REGISTRY_PATH`, `USAGE_DIR`; `default_plane_root_loop:runtime_router`.

### Step 7 — docs / artifacts / images

| Module | Mount prefix(es) | Routes | Lines | Config imports | Module globals | Seams | Step |
| --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `docs_router.py` | `/artifacts`, `/files` | 2 | 446 | `DASHBOARDS_DIR`, `PROJECT_ROOT` | `ALLOWED_ROOTS`, `DISCOVERY_ROOTS`, `EFFECTIVE_ROOTS` | 7 | 7 |
| `artifacts_router.py` | `/api/artifacts` | 7 | 854 | `CURRICULUM_ROOT`, `LEVELS`, `PROJECT_ROOT` | `PLANS_ROOT` | 3 | 7 |
| `images_router.py` | `/api/images` | 9 | 649 | `PROJECT_ROOT` | `IMAGES_DIR`, `TEXTBOOKS_DIR`, `ANNOTATIONS_FILE`, `_index`, `_pdf_pool`, `_page_cache`, `_pdf_page_count_cache` | 11 | 7 |

**`docs_router` seams (7):** `PROJECT_ROOT`, `ALLOWED_ROOTS`, `DISCOVERY_ROOTS`,
`EFFECTIVE_ROOTS`, `DASHBOARDS_DIR`; `path_loop:DASHBOARDS_DIR`, `PROJECT_ROOT`.

**`images_router` seams (11):** explicit singleton resets for `IMAGES_DIR`,
`TEXTBOOKS_DIR`, `ANNOTATIONS_FILE`, `_index`, `_pdf_pool`, `_page_cache`,
`_pdf_page_count_cache`; matching `path_loop` entries.

### Step 8 — admin / ops / git

| Module | Mount prefix(es) | Routes | Lines | Config imports | Module globals | Seams | Step |
| --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `admin_router.py` | `/api/admin` | 8 | 381 | `MESSAGE_DB`, `PROJECT_ROOT` | `BACKUP_DIR`, `DATA_DIR`, `IMAGE_DIR`, `LOGS_DIR`, `MCP_DIR` | 7 | 8 |
| `ops_router.py` | `/api/ops` | 2 | 70 | `PROJECT_ROOT` | `DEFAULT_PLAN_DIR` | 2 | 8 |
| `git_hygiene_router.py` | `/api/git` | 2 | 749 | `LIVE_REPO_ROOT`, `PROJECT_ROOT` | `POLICY_DOC` | 5 | 8 |

**`git_hygiene_router` seams (5):** `_run_git`; `worktree_containment.primary_checkout_dirty_status`;
`path_loop:LIVE_REPO_ROOT`, `PROJECT_ROOT`, `POLICY_DOC`.

### Step 9 — `dashboard_router` (large)

| Module | Mount prefix(es) | Routes | Lines | Config imports | Module globals | Seams | Step |
| --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `dashboard_router.py` | `/api/dashboard` | 11 | 996 | `CURRICULUM_ROOT`, `LEVELS`, `PROJECT_ROOT`, `SEMINAR_TRACK_IDS` | — | 2 | 9 |

**Internal route groups:** overview/research/track (`/overview`, `/research`,
`/track/*`, `/pipeline`, `/activity-config`); comms embed
(`/comms`, `/comms/message/{message_id}`, `/comms/conversation/{task_id}`,
`/comms/messages`).

### Step 10 — `sources_router` / RAG

| Module | Mount prefix(es) | Routes | Lines | Config imports | Module globals | Seams | Step |
| --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `rag_router.py` (`sources_router`) | `/api/sources`, `/api/rag` (deprecated) | 5 | 139 | `PROJECT_ROOT` | `IMAGE_DIR` | 7 | 10 |

**`sources_router` seams (7):** `sources_db.SOURCES_DB_PATH`, `_conn`, `_get_conn`;
`rag_query.sources_db.SOURCES_DB_PATH`, `_conn`; `path_loop:PROJECT_ROOT`,
`IMAGE_DIR`.

### Step 11 — `contracts_router` / route contracts (large)

| Module | Mount prefix(es) | Routes | Lines | Config imports | Module globals | Seams | Step |
| --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `route_contracts.py` (`contracts_router`) | `/api/contracts` | 1 | 1,356 | `LIVE_REPO_ROOT`, `PROJECT_ROOT` | — | 0 | 11 |

Single route (`/routes`) but ~1.3k lines of contract registry logic — own step.

### Step 12a — curriculum / batch small batch

| Module | Mount prefix(es) | Routes | Lines | Config imports | Module globals | Seams | Step |
| --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `atlas_jobs_router.py` | `/api/atlas-jobs` | 7 | 484 | — | `_HOST_LOAD_CACHE` | 2 | 12a |
| `blue_router.py` | `/api/blue` | 8 | 412 | `BATCH_STATE_DIR`, `CURRICULUM_ROOT`, `LEVELS`, `PROJECT_ROOT` | — | 3 | 12a |
| `build_events_router.py` | `/api/build/events` | 2 | 157 | `CURRICULUM_ROOT` | — | 1 | 12a |
| `coordination_router.py` | `/api/coordination` | 3 | 40 | `PROJECT_ROOT` | — | 1 | 12a |
| `cost_router.py` | `/api/cost`, `/api/analytics/cost` | 3 | 26 | — | — | 0 | 12a |

**`atlas_jobs_router` seams (2):** `atlas_job.registry_dir`, `primary_checkout_root`.

### Step 12b — consultation / delegate / discussions

| Module | Mount prefix(es) | Routes | Lines | Config imports | Module globals | Seams | Step |
| --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `consultation_router.py` | `/api/consultation` | 7 | 495 | `CURRICULUM_ROOT`, `LEVELS`, `PROJECT_ROOT` | `APPLIED_DIR`, `QUEUE_DIR`, `REJECTED_DIR`, `TEMPLATE_DIR` | 6 | 12b |
| `decisions_router.py` | `/api/decisions` | 6 | 168 | `LIVE_REPO_ROOT`, `PROJECT_ROOT` | `DECISIONS_FILE`, `_cache`, `_lineage_cache` | 3 | 12b |
| `delegate_router.py` | `/api/delegate` | 3 | 554 | `BATCH_STATE_DIR` | `TASKS_DIR`, `_LAST_TASKS_DIR_STR`, `_TASK_STATE_CACHE` | 2 | 12b |
| `discussions_router.py` | `/api/discussions` | 1 | 122 | `MESSAGE_DB` | — | 1 | 12b |
| `gold_router.py` | `/api/gold` | 8 | 351 | `CURRICULUM_ROOT`, `PROJECT_ROOT` | — | 2 | 12b |

### Step 12c — governance / issues / knowledge

| Module | Mount prefix(es) | Routes | Lines | Config imports | Module globals | Seams | Step |
| --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `governance_router.py` | `/api/state/governance` | 1 | 162 | `PROJECT_ROOT` | `DECISIONS_FILE` | 3 | 12c |
| `hermes_cron_router.py` | `/api/hermes-cron` | 1 | 44 | `PROJECT_ROOT` | — | 1 | 12c |
| `issues_router.py` | `/api/issues` | 2 | 251 | `PROJECT_ROOT` | — | 2 | 12c |
| `knowledge_router.py` | `/api/knowledge` | 4 | 172 | — | — | 0 | 12c |
| `reviewer_ghosts_router.py` | `/api/state/reviewer-ghosts` | 1 | 183 | `CURRICULUM_ROOT`, `LEVELS` | — | 1 | 12c |

**`issues_router` seams (2):** `_run_gh`; `path_loop:PROJECT_ROOT`.

### Step 12d — site / wiki / worktrees / telemetry

| Module | Mount prefix(es) | Routes | Lines | Config imports | Module globals | Seams | Step |
| --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `site_router.py` | `/api/site` | 2 | 260 | `LIVE_REPO_ROOT`, `PROJECT_ROOT` | `SITE_DIR`, `ASTRO_OUTPUT_DIR` | 5 | 12d |
| `wiki_router.py` | `/api/wiki` | 8 | 436 | `CURRICULUM_ROOT`, `LEVELS` | `PROJECT_ROOT`, `SOURCES_DB_PATH` | 7 | 12d |
| `worktrees_router.py` | `/api/worktrees` | 1 | 221 | `LIVE_REPO_ROOT`, `PROJECT_ROOT` | — | 3 | 12d |
| `telemetry_router.py` | (none — router defines own prefix) | 7 | 553 | `PROJECT_ROOT` | `_DB_PATH`, `_MODULE_BUILD_DB_PATH` | 4 | 12d |

**`wiki_router` seams (7):** `path_loop:CURRICULUM_ROOT`, `PROJECT_ROOT`,
`SOURCES_DB_PATH`; `external_store_loop:wiki.config.WIKI_STATE_DIR`,
`wiki.source_attribution.DEFAULT_DB_PATH`, `wiki.state.WIKI_STATE_DIR`,
`wiki.quality_gate.PROGRESS_DB`.

**`worktrees_router` seams (3):** `_run`; `reap_worktrees._run`;
`path_loop:LIVE_REPO_ROOT`.

### Step 12e — work / epics

| Module | Mount prefix(es) | Routes | Lines | Config imports | Module globals | Seams | Step |
| --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `work_router.py` | `/api/work` | 4 | 633 | — | `_IN_FLIGHT_BUILDS` | 1 | 12e |
| `epics_router.py` | `/api/epics` | 11 | 854 | `LIVE_REPO_ROOT` | `_store()` (`SessionStreamStore`) | 2 | 12e |

**`epics_router` seams (2):** `_store`; `path_loop:LIVE_REPO_ROOT`.

### Step 13 — `core_router` (last)

| Module | Mount prefix(es) | Routes | Lines | Config imports | Module globals | Seams | Step |
| --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `main.py` (`core_router`) | (none — absolute paths) | 15 | 1,949 | `BATCH_STATE_DIR`, `CURRICULUM_ROOT`, `DASHBOARDS_DIR`, `LEVELS`, `LIVE_REPO_ROOT`, `MESSAGE_DB`, `PROJECT_ROOT` | `SOURCES_DB_PATH`, `SESSION_STATE_DIR`, `_IMAGE_DIR` | 12 | 13 |

**Routes:** `/api` (redirect), `/api/health`, `/api/orient`, `/api/config`,
`/api/batch/dispatcher`, `/api/batch/active`, `/api/batch/failures`,
`/api/batch/usage`, `/api/batch/checkpoints`, `/api/batch/dispatcher/running`,
`POST /api/batch/dispatcher/scan`, `/api/batch/dispatcher/logs`,
`WS /ws/batch`, `/images/{path:path}`, `/{path:path}` (dashboard catch-all).

**Why last:** The `/{path:path}` catch-all serves dashboard static files and must
stay registered after all `/api/*` prefixed routers (§4.2). #7302 migrated these
15 inline handlers to `core_router` reading `request.app` / existing `main.py`
helpers; no separate `_repo_root` / `_store` beyond the config imports and
module globals listed above.

**`core_router` seams (12):** `api_main._health_instance_identity`,
`DASHBOARDS_DIR`; `path_loop:BATCH_STATE_DIR`, `CURRICULUM_ROOT`, `DASHBOARDS_DIR`,
`LIVE_REPO_ROOT`, `MESSAGE_DB`, `PROJECT_ROOT`, `SOURCES_DB_PATH`,
`SESSION_STATE_DIR`, `_IMAGE_DIR`; `run_command_loop:main._run_command`.

---

## Global OPSEC seams (not attributed to a single router)

| Seam | Purpose | Count |
| --- | --- | ---: |
| `subprocess.run` / `subprocess.Popen` | Deny subprocess in sweep | 2 |
| `socket.create_connection` | Deny network in sweep | 1 |
| `sqlite3.connect` | #7284 outside-root DB deny backstop | 1 |
| **Global total** | | **4** |

These four stay as defense-in-depth per §4.1 point 5 of the parent design until
all routers read stores through `MonitorContext`.

---

## Summary accounting

| Metric | Value |
| --- | ---: |
| Router modules | 45 |
| Route handlers (decorator sum) | 269 |
| OpenAPI HTTP operations (sweep denominator) | 280 |
| OPSEC seams (router-attributed) | 162 |
| OPSEC seams (global backstops) | 4 |
| **OPSEC seam baseline total** | **166** |

**Full step accounting:**

```
step 1 (4) + step 2 (1) + step 3 (6) + step 4 (1) + step 5 (1) + step 6 (1)
+ step 7 (3) + step 8 (3) + step 9 (1) + step 10 (1) + step 11 (1)
+ step 12a (5) + step 12b (5) + step 12c (5) + step 12d (4) + step 12e (2)
+ step 13 (1) = 45 modules
```

---

## Deviations from parent design provisional table (§5.2)

| Provisional | Inventory correction |
| --- | --- |
| 44 modules (pre-#7302) | **45** — adds `core_router` in `main.py` |
| Step 12 as one 21-module batch | Split into **12a–12e** (≤5 modules / ≤~1,700 lines per sub-step) |
| `core_router` absent | **Step 13 (last)** — catch-all route ordering |
| `rag_router.py` naming | Mounted as `sources_router` import alias; file is `rag_router.py` |

Sub-issues under #7269 should be filed from this inventory, not the provisional
table in the parent design doc.
