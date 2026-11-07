"""Launcher tests and provider children must not inherit another seat's defaults."""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

from tests.helpers import machinery_package
from tests.launcher_sandbox import launcher_environment, tracked_launcher_wrappers

# Freeze the audited consumers. Never include this file: its subprocess runs pytest.
LAUNCHER_TEST_FILES = (
    "tests/test_handoff_slot_registry.py",
    "tests/test_launcher_contract.py",
    "tests/test_launcher_helper_root.py",
    "tests/test_launcher_interactive_scope.py",
    "tests/test_rules_core_loading.py",
    "tests/test_start_codex_driver.py",
    "tests/test_start_cto_wrappers.py",
    "tests/test_start_cursor_launcher.py",
    "tests/test_start_gemini_launcher.py",
    "tests/test_start_grok_launcher.py",
    "tests/test_start_muse_driver.py",
    "tests/test_start_codex_profiles.py",
    "tests/test_launcher_driver_scope.py",
    "tests/orchestration/test_thread_restart_e2e.py",
    "tests/test_fleet_comms_launcher_awareness.py",
    "tests/test_fleet_taxonomy_aliases.py",
    "tests/test_git_identity.py",
    "tests/test_handoff_identity.py",
    "tests/test_launcher_canary_honesty.py",
    "tests/test_launcher_remote_renew.py",
    "tests/test_session_supervisor.py",
    "tests/test_session_supervisor_shell.py",
    "tests/test_claude_cap_guard.py",
    "tests/test_start_claude_profiles.py",
    "tests/test_start_claude_supervisor.py",
    "tests/test_start_codex_claude_code.py",
    "tests/test_start_codex_launcher.py",
    "tests/test_start_glm_launcher.py",
    "tests/test_start_kimi_claude_code.py",
    "tests/test_start_kimi_launcher.py",
    "tests/test_launcher_sandbox_closure.py",
    "tests/test_secret_redaction.py",
)

# One fixed regression list, mapped to the audited builders and consumers.
POLLUTED_PARENT_TESTS = {
    "tests/test_handoff_slot_registry.py::test_practice_launcher_dry_run_uses_the_dedicated_stream": "inline wrapper environments; original cross-provider reproduction",
    "tests/test_handoff_slot_registry.py::test_open_model_data_selector_mints_registered_slot": "shared _bash and handoff-slot gate",
    "tests/test_handoff_slot_registry.py::test_real_launch_of_unregistered_selector_never_execs_the_provider": "shared _launcher and intentional fake PATH",
    "tests/test_handoff_slot_registry.py::test_kube_dojo_wrapper_dry_run_binds_its_claude_lane": "direct kube-dojo wrapper environment",
    "tests/test_launcher_contract.py::test_codex_launchers_pin_roles_and_preserve_explicit_effort": "shared run_launcher dry-run environment",
    "tests/test_launcher_contract.py::test_canary_failure_closes_lease_and_refuses_driver_launch": "direct lifecycle environment",
    "tests/test_launcher_helper_root.py::test_ambient_git_dir_does_not_redirect_any_site": "shared _clean_env and intentional hostile Git inputs",
    "tests/test_launcher_interactive_scope.py::test_every_wrapper_enters_one_verified_scope_then_reaches_its_provider_once": "tracked-wrapper sandbox, scope re-entry and actual children across families",
    "tests/test_rules_core_loading.py::test_launcher_row_carries_the_core": "rules-core _launch environment across provider families",
    "tests/test_rules_core_loading.py::test_the_old_env_override_has_no_effect": "explicit hostile rules override",
    "tests/test_rules_core_loading.py::test_content_seat_launcher_needs_the_addendum_but_a_core_seat_does_not": "explicit fixture product root and absent-addendum refusal",
    "tests/test_start_codex_driver.py::test_driver_canaries_use_canonical_stream_then_exec_provider": "runtime Codex _clean_environ and fake provider",
    "tests/test_start_codex_profiles.py::test_launcher_targets_canonical_main_without_creating_worktree": "profile _run and _launch builders",
    "tests/test_start_cto_wrappers.py::test_scope_reentry_preserves_cto_defaults_and_explicit_opus": "CTO runtime checkout environment",
    "tests/test_start_cto_wrappers.py::test_supervisor_successor_reenters_cto_wrapper": "successor launcher_env capture and replay",
    "tests/test_start_cursor_launcher.py::test_cursor_interactive_defaults_to_the_concrete_pin": "Cursor _run_interactive launch_env builder",
    "tests/test_start_gemini_launcher.py::test_gemini_driver_default_respects_launcher_model": "Gemini shared launcher consumer",
    "tests/test_start_gemini_launcher.py::test_gemini_exec_hook_gate_precedes_provider_spawn": "Gemini direct exec seam environment",
    "tests/test_start_grok_launcher.py::test_grok_interactive_defaults_to_native_harness_and_rejects_epic": "Grok shared launcher consumer",
    "tests/test_start_muse_driver.py::test_shared_lease_claim_exec_close_order": "Muse muse_env, lifecycle fixture, actual provider child and process guard",
    "tests/test_start_muse_driver.py::test_dry_run_argv_and_capsule_binding": "Muse launch builder and public-route fakes",
    "tests/test_launcher_driver_scope.py::test_forwarder_finishes_close_and_reaps_children_after_repeated_signal": "direct forwarder environment and process cleanup",
    "tests/orchestration/test_thread_restart_e2e.py::test_real_codex_devops_launcher_injects_board_and_binds_exact_fresh_rollover": "restart run helper and direct launcher environment",
    "tests/orchestration/test_thread_restart_e2e.py::test_real_grok_driver_recovers_expired_app_thread_holder_via_remote_ttl": "provider_environment builder and local Monitor stub",
    "tests/test_fleet_comms_launcher_awareness.py::test_cold_clause_resolves_live_mode_when_env_unset": "Fleet clause and fallback shell consumers",
    "tests/test_fleet_taxonomy_aliases.py::test_hermetic_launcher_unknown_selector_fails_closed_contract": "direct wrapper and clean_env builder",
    "tests/test_git_identity.py::test_launcher_export_git_identity": "launcher identity environment with intentional parent identity",
    "tests/test_handoff_identity.py::test_new_registry_stream_resolves_without_shell_edit": "selector shell environment with explicit registry fixture",
    "tests/test_launcher_canary_honesty.py::test_main_clears_inherited_canary_execution_report": "canary probe environment with intentional hostile report",
    "tests/test_launcher_remote_renew.py::test_driver_renew_loop_409_stops_provider_with_lease_lost": "implicit lifecycle shell consumer now isolated",
    "tests/test_session_supervisor.py::test_successor_preflight_resolves_executable_with_stripped_pane_path": "successor environment and executable fixtures",
    "tests/test_session_supervisor_shell.py::test_claim_exports_all_session_stream_variables_and_writes_capsule": "supervisor _clean_environ builder",
    "tests/test_claude_cap_guard.py::test_cto_epics_explicit_cli_opus_is_admitted": "cap fixture and shared launcher consumer",
    "tests/test_start_claude_profiles.py::test_claude_interactive_preserves_advisor_switch": "Claude fake-binary PATH and intentional advisor settings",
    "tests/test_start_claude_supervisor.py::test_claude_driver_claims_before_canary_and_drive_epic": "Claude supervisor shared launcher consumer",
    "tests/test_start_codex_claude_code.py::test_codex_claude_code_clears_foreign_ambient_auth_before_exec": "Codex proxy explicit fake PATH and hostile auth",
    "tests/test_start_codex_launcher.py::test_codex_native_harness_is_default_and_forwards_arguments_after_separator": "Codex interactive shared launcher consumer",
    "tests/test_start_glm_launcher.py::test_glm_retirement_precedes_profile_export": "retired GLM wrapper and explicit fake PATH",
    "tests/test_start_glm_launcher.py::test_claude_route_guard_checks_primary_checkout_settings_for_linked_worktree": "GLM Git fixture and direct route-guard environments",
    "tests/test_start_kimi_claude_code.py::test_kimicc_interactive_dry_run_refuses_retired_pins": "retired Kimi Claude-Code shared launcher consumer",
    "tests/test_start_kimi_launcher.py::test_kimi_native_is_default_and_interactive_rejects_epic": "retired native Kimi shared launcher consumer",
    "tests/test_launcher_sandbox_closure.py::test_slot_registry_closure_includes_fleet_comms_contracts_shim": "shared measured sandbox import closure",
    "tests/test_secret_redaction.py::test_launcher_preserves_parent_api_key_and_fails_closed": "credential helper parent-preservation and fail-closed shell environments",
    "tests/test_secret_redaction.py::test_interactive_launcher_child_uses_dispatcher_credential_policy": "explicit synthetic credential environments across active and retired adapters",
    "tests/test_secret_redaction.py::test_round4_exec_restores_signal_defaults": "shared _round4_launcher_probe environment builder",
}

SEAT_CONTAMINATION = {
    "LAUNCHER_MODEL": "claude-sonnet-5-5",
    "LAUNCHER_EFFORT": "medium",
    "LAUNCHER_DRY_RUN": "0",
    "LAUNCHER_SEAT_SENTINEL": "polluted-parent",
    "LU_DRIVER_SCOPE_ACTIVE": "1",
    "LU_DRIVER_SCOPE_UNIT": "foreign-seat.scope",
    "LU_DRIVER_MEMORY_MAX": "1",
    "CLAUDE_CODE_DISABLE_ADVISOR_TOOL": "1",
    "CLAUDE_CODE_MAX_CONTEXT_TOKENS": "123",
    "LEARN_UKRAINIAN_DISPATCH_TASK_ID": "foreign-seat-task",
    "LEARN_UKRAINIAN_MAIN_MODEL_ID": "claude-opus-5-5",
    "SESSION_HANDOFF_AGENT": "foreign-seat",
    "SESSION_EPIC": "foreign-seat",
    "LC_SUPERVISORY_PREDECESSOR_GENERATION": "999",
}


@pytest.mark.timeout(330)
def test_launcher_tests_pass_with_a_polluted_parent(tmp_path: Path) -> None:
    """Exercise the same fixed test list from a seat carrying foreign defaults."""
    assert {node.split("::")[0] for node in POLLUTED_PARENT_TESTS} == set(LAUNCHER_TEST_FILES)
    assert Path(__file__).name not in {Path(node.split("::")[0]).name for node in POLLUTED_PARENT_TESTS}
    log = tmp_path / "polluted-parent-pytest.log"
    print(f"Polluted-parent pytest log: {log}", flush=True)
    with log.open("w", encoding="utf-8") as output:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-n", "2", "--dist=worksteal", "--tb=short", *POLLUTED_PARENT_TESTS],
            cwd=Path(__file__).resolve().parents[1],
            # Deliberately inherit and pollute pytest itself. The tested launcher
            # environment builders, rather than this caller, must isolate children.
            env={**os.environ, **SEAT_CONTAMINATION},
            stdout=output,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=300,
        )
    report = log.read_text(encoding="utf-8")
    print(report)
    assert result.returncode == 0, report


def _child_environment(path: Path) -> dict[str, str]:
    return dict(entry.split("=", 1) for entry in path.read_text().split("\0") if entry)


def test_environment_builder_isolates_seat_state_and_preserves_explicit_inputs(monkeypatch) -> None:
    for name, value in SEAT_CONTAMINATION.items():
        monkeypatch.setenv(name, value)
    first = launcher_environment()
    second = launcher_environment({"LAUNCHER_MODEL": "intentional", "GIT_DIR": "/hostile"})
    assert not set(first).intersection(SEAT_CONTAMINATION)
    assert first["HOME"] != second["HOME"]
    assert Path(first["HOME"]).is_dir()
    assert Path(first["TMPDIR"]).is_dir()
    assert first["LU_MONITOR_LOOPBACK"] == "http://127.0.0.1:1"
    assert second["LAUNCHER_MODEL"] == "intentional"
    assert second["GIT_DIR"] == "/hostile"


@pytest.mark.parametrize(
    ("wrapper", "default_model", "override_model", "cli_model", "args"),
    (
        ("start-claude-cto.sh", "claude-sonnet-5-5", "claude-sonnet-5-5", "claude-opus-5-5", ()),
        ("start-codex-cto.sh", "gpt-6.1-sol", "gpt-6.1-sol", "gpt-6.1-sol", ()),
        (
            f"{machinery_package()}/start-kube-dojo-driver.sh",
            "claude-sonnet-5-5",
            "claude-sonnet-5-5",
            "claude-sonnet-5-5",
            (),
        ),
        ("start-codex.sh", "gpt-6.1-sol", "gpt-6.1-sol", "gpt-6.1-sol", ()),
        ("start-codex-driver.sh", "gpt-6.1-sol", "gpt-6.1-sol", "gpt-6.1-sol", ("--epic", "devops")),
    ),
)
@pytest.mark.parametrize("selection", ("default", "environment", "cli"))
def test_provider_child_drops_launcher_controls_after_scope_reentry(
    tmp_path: Path,
    wrapper: str,
    default_model: str,
    override_model: str,
    cli_model: str,
    args: tuple[str, ...],
    selection: str,
) -> None:
    from tests.test_launcher_interactive_scope import _checkout, _identity, _launch, _lines

    root, env = _checkout(tmp_path)
    extra = {"LAUNCHER_SEAT_SENTINEL": "must-not-reach-provider"}
    expected_model, expected_effort = default_model, "high"
    if selection != "default":
        extra.update(LAUNCHER_MODEL=override_model, LAUNCHER_EFFORT="medium")
        expected_model, expected_effort = override_model, "medium"
    if selection == "cli":
        extra["LAUNCHER_MODEL"] = "not-certified"
        args = (*args, "--model", cli_model, "--effort", "high")
        expected_model, expected_effort = cli_model, "high"
    result = _launch(root, env, wrapper, *args, **extra)
    assert result.returncode == 42, result.stdout + result.stderr
    identity = _identity(env)
    assert (identity["model"], identity["effort"]) == (expected_model, expected_effort)
    assert _lines(env["FAKE_STARTS"]) == ["start"]
    assert result.stderr.count("DRIVER_SCOPE_VERIFIED") == 2
    child = _child_environment(Path(env["TEST_PROVIDER_ENV"]))
    assert not [name for name in child if name.startswith("LAUNCHER_")]
    assert child["LU_DRIVER_SCOPE_UNIT"] == identity["unit"]
    if identity["mode"] == "driver":
        assert child["SESSION_HANDOFF_AGENT"]


def test_direct_exec_without_credential_helper_still_drops_launcher_controls(tmp_path: Path) -> None:
    core = Path(__file__).resolve().parents[1] / machinery_package() / "lib/launcher_core.sh"
    capture = tmp_path / "child-env"
    script = f"""
set -euo pipefail
source {shlex.quote(str(core))}
LC_MODE=interactive LC_PROVIDER=claude LC_DURABLE_HELPER_ROOT=''
launcher_exec_command /bin/sh -c 'env -0 > "$TEST_CHILD_ENV"'
"""
    result = subprocess.run(
        ["bash", "-c", script],
        env=launcher_environment(
            LAUNCHER_MODEL="claude-sonnet-5-5",
            LAUNCHER_EFFORT="medium",
            LAUNCHER_UNKNOWN="sentinel",
            TEST_CHILD_ENV=str(capture),
        ),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    child = _child_environment(capture)
    assert not [name for name in child if name.startswith("LAUNCHER_")]


@pytest.mark.parametrize(
    "wrapper",
    ("start-codex-cto.sh", f"{machinery_package()}/start-kube-dojo-driver.sh", "start-codex-driver.sh"),
)
def test_successor_replay_keeps_supervisor_defaults_but_cleans_both_provider_children(
    tmp_path: Path,
    wrapper: str,
) -> None:
    from tests.test_launcher_interactive_scope import _checkout, _identity, _launch, _lines

    root, env = _checkout(tmp_path)
    provider = Path(env["TEST_PROVIDER"])
    provider.write_text("""#!/usr/bin/env bash
if [ -z "${SESSION_SUPERVISOR_WAKE_DELIVERY:-}" ]; then
  env -0 > "$TEST_FIRST_ENV"
  trap 'exit 0' TERM
  touch "$TEST_FIRST_READY"
  while :; do sleep 0.01; done
else
  env -0 > "$TEST_SECOND_ENV"
  exit 42
fi
""")
    watcher = root / machinery_package() / "ai_agent_bridge/inbox_watch.sh"
    watcher.write_text("""#!/usr/bin/env bash
if [ "${2:-}" = --launch-plan ]; then
  printf '%s\\n' '{"session_id":"session-test","generation":1}'
  exit 0
fi
if [ -n "${SESSION_SUPERVISOR_WAKE_DELIVERY:-}" ]; then exec sleep 300; fi
while [ ! -f "$TEST_FIRST_READY" ]; do sleep 0.01; done
printf 'fixture-delivery\\n'
# The production loop also observes watcher exit without a notification.
exit 75
""")
    first, second = tmp_path / "first-env", tmp_path / "second-env"
    model = "gpt-6.1-sol" if "codex" in wrapper else "claude-sonnet-5-5"
    args = ("--epic", "devops") if wrapper == "start-codex-driver.sh" else ()
    result = _launch(
        root,
        env,
        wrapper,
        *args,
        LAUNCHER_MODEL=model,
        LAUNCHER_EFFORT="medium",
        LAUNCHER_UNKNOWN="sentinel",
        TEST_FIRST_ENV=str(first),
        TEST_SECOND_ENV=str(second),
        TEST_FIRST_READY=str(tmp_path / "first-ready"),
    )
    assert result.returncode == 42, result.stdout + result.stderr
    assert _identity(env)["model"] == model
    assert _identity(env)["effort"] == "medium"
    assert _lines(env["FAKE_STARTS"]) == ["start"]
    for capture in (first, second):
        child = _child_environment(capture)
        assert not [name for name in child if name.startswith("LAUNCHER_")]
        assert child["SESSION_HANDOFF_AGENT"]


def test_tracked_wrapper_coverage_cannot_silently_shrink() -> None:
    from tests.test_launcher_interactive_scope import DRIVERS, INTERACTIVE

    retired = {"start-kimi.sh", "start-kimicc.sh"}
    public_only = {"start-muse-driver.sh"}
    assert set(tracked_launcher_wrappers()) == set(DRIVERS) | set(INTERACTIVE) | retired | public_only
