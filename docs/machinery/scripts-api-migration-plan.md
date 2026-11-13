# scripts/api migration plan

**Plan only.** Rewriting these imports, or deleting `scripts/api`, needs designated approval (rules core P6: the operator, or `claude-opus-5-5` and `gpt-6.1-sol` agreeing). This file is not that approval. Until it exists, `scripts/api` stays. Issue #12979 AC-02.

Measured `2026-11-13T10:06:01Z` on `dad8aac858056b50f5776dc0e318a40b039cb245`, against `lu-machinery==0.1.11` (`requirements-machinery.lock`).

The census is the issue's command:

```bash
git grep -lE '(from|import) scripts\.api(\.| import)' -- ':!scripts/api' ':!docs' ':!archive'
```

That command lists **59 files: 18 product, 41 tests**. The issue body's "39 test importers" is the earlier count. This tree has 41.

A target is the same module under `lu_machinery.api`. Each imported name on the 57 files below was checked against the 0.1.11 pin and is defined there. Two test files import `scripts.api.fleet_board`, which the pin does not contain.

## Recommendation

Retarget the 57 files by the prefix swap, then prove the opencode provider and the session-supervisor host-id command still work. Do not delete `scripts/api` in that change.

`scripts/api/fleet_board` has no target. `tests/api/test_fleet_board_prs.py` records that 0.1.10 removed the router and the product kept the source until B2b. 0.1.11 still has no `fleet_board` package. Those two tests are retired with the package. They are not pointed at a module the pin will not grow.

The opencode provider (`scripts/dispatcher/providers/opencode.py`) is on the operator keep-list. Execution changes only its import of `lu_machinery.api.subscription_usage`, including `_private_usage`, which 0.1.11 still defines. The provider stays.

Deleting the mirror in one cut, before those retargets, is the worst option: it breaks the provider, the session supervisor, and the launchd wrapper tests while the fleet-board tests still import a removed router.

## Product importers (18)

| Importer | lu_machinery target |
| --- | --- |
| `scripts/ai_agent_bridge/measure_cold_start.py` | `lu_machinery.api.telemetry.transcript_tokens` |
| `scripts/dispatcher/providers/opencode.py` | `lu_machinery.api.subscription_usage` |
| `scripts/fleet/claude_account_lane.py` | `lu_machinery.api.state_router`, `lu_machinery.api.subscription_usage` |
| `scripts/fleet/credit_lane.py` | `lu_machinery.api.subscription_usage` |
| `scripts/fleet/reset_reserve.py` | `lu_machinery.api.subscription_usage` |
| `scripts/fleet/usage.py` | `lu_machinery.api.state_router`, `lu_machinery.api.subscription_usage` |
| `scripts/fleet_comms/fleet_overview.py` | `lu_machinery.api.occupancy_sanitize` |
| `scripts/orchestration/curriculum_coordinator.py` | `lu_machinery.api.state_router` |
| `scripts/orchestration/issue_stream_audit.py` | `lu_machinery.api.config` |
| `scripts/orchestration/observer_heartbeat.py` | `lu_machinery.api.occupancy_local`, `lu_machinery.api.occupancy_sanitize`, `lu_machinery.api.telemetry.transcript_tokens`, `lu_machinery.api.occupancy` |
| `scripts/orchestration/session_markers.py` | `lu_machinery.api.occupancy_sanitize` |
| `scripts/orientation_packet.py` | `lu_machinery.api.session_router` |
| `scripts/research/consumption.py` | `lu_machinery.api.delegate_router` |
| `scripts/research/registry.py` | `lu_machinery.api.config` |
| `scripts/review/bench_health.py` | `lu_machinery.api.state_router` |
| `scripts/session_supervisor/__init__.py` | `lu_machinery.api.occupancy_local` |
| `scripts/tools/check_api_state.py` | `lu_machinery.api.main` |
| `scripts/work/sources_public.py` | `lu_machinery.api.issues_router`, `lu_machinery.api.delegate_router`, `lu_machinery.api.fleet_router` |

Several of these call private names (`_private_usage`, `_assemble_session`, `_read_task_state`, and others). Those names exist on 0.1.11. The retarget keeps the names. A public replacement is a later machinery change, not part of the prefix swap.

## Test importers (41)

| Importer | lu_machinery target |
| --- | --- |
| `tests/_host_path_guard.py` | `lu_machinery.api.occupancy_sanitize` |
| `tests/ai_agent_bridge/test_measure_cold_start.py` | `lu_machinery.api.telemetry.transcript_tokens` |
| `tests/api/opsec_sweep/test_opsec_scan.py` | `lu_machinery.api.opsec_scan` |
| `tests/api/test_acp_routing_budget.py` | `lu_machinery.api.state_router` |
| `tests/api/test_b0_contract_trace.py` | `lu_machinery.api.claude_account_usage`, `lu_machinery.api.fleet_router`, `lu_machinery.api.route_contracts` |
| `tests/api/test_claude_account_probe_ownership.py` | `lu_machinery.api.claude_account_usage`, `lu_machinery.api.subscription_usage` |
| `tests/api/test_claude_account_usage.py` | `lu_machinery.api.claude_account_usage`, `lu_machinery.api.subscription_usage` |
| `tests/api/test_code_worker_recommendation.py` | `lu_machinery.api.state_router` |
| `tests/api/test_fleet_board_prs.py` | none — retire with `scripts/api/fleet_board` |
| `tests/api/test_fleet_workers_sanitize.py` | `lu_machinery.api.fleet_workers_sanitize`, `lu_machinery.api.project_state_sanitize` |
| `tests/api/test_git_no_optional_locks.py` | `lu_machinery.api.project_state_collect` |
| `tests/api/test_lane_health.py` | `lu_machinery.api.codexbar_usage`, `lu_machinery.api.state_helpers`, `lu_machinery.api.state_router`, `lu_machinery.api.lane_health` |
| `tests/api/test_launchd_supervisor.py` | `lu_machinery.api.launchd_supervisor` |
| `tests/api/test_occupancy_local.py` | `lu_machinery.api.occupancy_local` |
| `tests/api/test_preload_closed_fitz_stream.py` | `lu_machinery.api.preload` |
| `tests/api/test_project_state_collect.py` | `lu_machinery.api.project_state_collect`, `lu_machinery.api.project_state_sanitize` |
| `tests/api/test_release_snapshot.py` | `lu_machinery.api.release_snapshot` |
| `tests/api/test_routing_budget.py` | `lu_machinery.api.state_router` |
| `tests/api/test_routing_budget_runtime_diagnostics.py` | `lu_machinery.api.state_router` |
| `tests/dispatcher/test_opencode_provider.py` | `lu_machinery.api.subscription_usage` |
| `tests/fleet/test_capacity_pick.py` | `lu_machinery.api.state_router`, `lu_machinery.api.subscription_usage` |
| `tests/fleet/test_grok_product_usage.py` | `lu_machinery.api.state_router`, `lu_machinery.api.subscription_usage` |
| `tests/fleet/test_quota_history.py` | `lu_machinery.api.state_router` |
| `tests/fleet/test_usage_cli.py` | `lu_machinery.api.subscription_usage`, `lu_machinery.api.state_router`, `lu_machinery.api.state_helpers` |
| `tests/orchestration/test_notebook_observer_heartbeat.py` | `lu_machinery.api.telemetry.transcript_tokens` |
| `tests/test_api_telemetry_footer.py` | `lu_machinery.api.telemetry.transcript_tokens` |
| `tests/test_codexbar_usage.py` | `lu_machinery.api.codexbar_usage`, `lu_machinery.api.state_router`, `lu_machinery.api.subscription_usage`, `lu_machinery.api.state_helpers` |
| `tests/test_comms_router_expiry_sweep.py` | `lu_machinery.api.comms_router`, `lu_machinery.api.monitor_context`, `lu_machinery.api.state_helpers` |
| `tests/test_credit_lane.py` | `lu_machinery.api.subscription_usage` |
| `tests/test_github_graphql_budget.py` | `lu_machinery.api.state_helpers` |
| `tests/test_host_path_guard.py` | `lu_machinery.api.occupancy_sanitize` |
| `tests/test_pace_reserve_routing.py` | `lu_machinery.api.state_router` |
| `tests/test_readonly_sqlite.py` | `lu_machinery.api.resilience` |
| `tests/test_red_team_consumer_trace.py` | none — retire with `scripts/api/fleet_board` |
| `tests/test_routing_amendment_11327.py` | `lu_machinery.api.state_router` |
| `tests/test_routing_consumer_agreement.py` | `lu_machinery.api.state_router` |
| `tests/test_runtime_routing_window.py` | `lu_machinery.api.runtime_router` |
| `tests/test_session_router_path_safety.py` | `lu_machinery.api.config`, `lu_machinery.api.session_router` |
| `tests/test_session_streams_projection.py` | `lu_machinery.api.epics_router` |
| `tests/test_tool_timing_hook.py` | `lu_machinery.api.telemetry_router` |
| `tests/test_transcript_tokens_usage.py` | `lu_machinery.api.telemetry.transcript_tokens` |

`tests/test_readonly_sqlite.py` also embeds the import line inside two string fixtures. Those strings move with the real import.

## Callers the import census misses

A second search for the literal `scripts.api` outside `scripts/api`, `docs`, and `archive` found callers the issue command does not list. Deletion still breaks them.

| Caller | What it does | Target |
| --- | --- | --- |
| `scripts/lib/session_supervisor.sh` | `python -m scripts.api.occupancy_local resolve-host-id` | `python -m lu_machinery.api.occupancy_local` (the pin CLI has `resolve-host-id`) |
| `tests/test_session_supervisor_shell.py` | stubs that command | the same module path |
| `tests/conftest.py` | `_API_STATUS_PACKAGES` still names `scripts.api` | drop `scripts.api` when the package is gone |
| `tests/test_claude_account_bound_snapshot.py` | monkeypatches `scripts.api.state_router.compute_routing_budget` | `lu_machinery.api.state_router.compute_routing_budget` |
| `scripts/api/run_monitor_api_supervisor.sh` | product copy execs `python -m scripts.api.launchd_supervisor` | the pin's copy of this wrapper already execs `python -m lu_machinery.api.launchd_supervisor` |

`tests/api/test_launchd_supervisor.py` is in the census and also opens the product wrapper path. Docs excluded from the census name that path too: `docs/runbooks/launchd-inventory.md`, `docs/best-practices/local-api-server.md`, and `openwiki/monitor-api.md`. Point them at the installed wrapper in the deletion change.

Comment-only mentions, with no runtime import: `scripts/common/repo_root.py`, `scripts/fleet/quota_history.py`, `scripts/github_rest_cache.py`, `scripts/yaml_activities.py`, and the module docstring in `scripts/research/consumption.py` (that file is also an importer). Update them in the same execution change so a later grep is empty.

Negative-path fixtures that use `scripts.api` as a rejected string (`tests/api/test_atlas_jobs_router.py`, `tests/test_api_state.py`, `tests/test_regen_lesson_schema_hook.py`) are not importers.

## Execution order, after approval

1. Retarget the 57 census files whose modules exist, plus the four callers in the table above. Keep the private names those callers already use.
2. Run the existing tests for the opencode provider, the session supervisor, and the retargeted modules. The opencode provider must still run.
3. Stop if a name a caller uses is missing from the pin then in force. This plan was checked against 0.1.11 only.
4. Separately, and only with an approval that names deletion: retire `scripts/api/fleet_board` and its two tests, point the launchd docs and test at the installed wrapper, then delete the rest of `scripts/api`.

Step 4 is not authorized by step 1. Both wait on designated approval. This document does not grant it.
