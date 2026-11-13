"""Shared pieces of the bootstrapped launcher sandboxes used by subprocess tests.

Launcher tests run the real ``start-*.sh`` entry points inside a throwaway git
repo that holds only the files the launcher needs.  Every driver launch passes
``launcher_require_registered_slot`` (#8303), which runs
``python -m scripts.orchestration.handoff_slot_registry`` from the sandbox root
and reads the fleet roster through ``scripts.ai_agent_bridge._channels``.  A
sandbox without that closure refuses every selector with exit 2 before the
provider starts.

The closure (the bridge package imports most of ``scripts/``) is not written
down here: it is measured once per test process by running the real gate calls
and recording every tracked repo file they import or open, so a new import in
the bridge cannot silently break the launcher sandboxes again.
"""

from __future__ import annotations

import functools
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Mapping
from pathlib import Path

from scripts.common.scratch import ensure_scratch_root
from tests.helpers import machinery_module, machinery_package, product_checkout
from tests.helpers.monitor import UNREACHABLE_MONITOR_URL, UNREACHABLE_TOOL_TIMING_URL

_REPO_ROOT = Path(__file__).resolve().parents[1]

# Audited consumers run as native clean and polluted cases in conftest.
LAUNCHER_TEST_FILES = (
    "tests/test_launcher_env_hermetic.py",
    "tests/test_handoff_slot_registry.py",
    "tests/test_launcher_contract.py",
    "tests/test_launcher_helper_root.py",
    "tests/test_launcher_interactive_scope.py",
    "tests/test_rules_core_loading.py",
    "tests/test_start_codex_driver.py",
    "tests/test_start_cto_wrappers.py",
    "tests/test_start_gemini_launcher.py",
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
    "tests/test_rollover_bundles.py",
    "tests/orchestration/test_codex_driver_rollover_recovery.py",
    "tests/orchestration/test_exited_successor_registry.py",
    "tests/orchestration/test_imported_rollover_detection.py",
)


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

# Preserve the original 49 selectors, plus audited lifecycle and failure coverage.
POLLUTED_PARENT_TESTS = {
    "tests/test_handoff_slot_registry.py::test_practice_launcher_dry_run_uses_the_dedicated_stream": "inline wrapper environments; original cross-provider reproduction",
    "tests/test_handoff_slot_registry.py::test_open_model_data_selector_mints_registered_slot": "shared _bash and handoff-slot gate",
    "tests/test_handoff_slot_registry.py::test_real_launch_of_unregistered_selector_never_execs_the_provider": "shared _launcher and intentional fake PATH",
    "tests/test_handoff_slot_registry.py::test_kube_dojo_wrapper_dry_run_binds_its_claude_lane": "direct kube-dojo wrapper environment",
    "tests/test_handoff_slot_registry.py::test_curriculum_upgrade_is_accepted_on_the_core_slot": "explicit product fixture root for curriculum content seats across provider families",
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
    "tests/test_start_gemini_launcher.py::test_gemini_driver_default_respects_launcher_model": "Gemini shared launcher consumer",
    "tests/test_start_gemini_launcher.py::test_gemini_exec_hook_gate_precedes_provider_spawn": "Gemini direct exec seam environment",
    "tests/test_start_muse_driver.py::test_shared_lease_claim_exec_close_order": "Muse muse_env, lifecycle fixture, actual provider child and process guard",
    "tests/test_start_muse_driver.py::test_dry_run_argv_and_capsule_binding": "Muse launch builder and public-route fakes",
    "tests/test_launcher_driver_scope.py::test_forwarder_finishes_close_and_reaps_children_after_repeated_signal": "direct forwarder environment and process cleanup",
    "tests/orchestration/test_thread_restart_e2e.py::test_real_codex_devops_launcher_injects_board_and_binds_exact_fresh_rollover": "restart run helper and direct launcher environment",
    "tests/orchestration/test_thread_restart_e2e.py::test_real_claude_driver_recovers_expired_app_thread_holder_via_remote_ttl": "provider_environment builder and local Monitor stub",
    "tests/orchestration/test_thread_restart_e2e.py::test_monitor_outage_and_dirty_replacement_never_unlock_cleanup": "private GitHub-cache root preserves clean-checkout and cleanup guards",
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
    "tests/test_start_claude_supervisor.py::test_driver_accepts_canonical_and_legacy_lane_selectors[seminars-folk]": "shared launcher builder supplies the selected product fixture root for a content seat",
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
    "tests/test_secret_redaction.py::test_round5_launcher_preserves_process_paths": "final-agent cleanup preserves explicit PATH, HOME and PWD",
    "tests/test_rollover_bundles.py::test_launcher_import_is_silent_for_the_typed_none_only": "direct launcher-core rollover import shell environment",
    "tests/orchestration/test_codex_driver_rollover_recovery.py::test_live_pending_packet_is_still_bound": "real rollover shell detection and explicit stream environment",
    "tests/orchestration/test_exited_successor_registry.py::test_real_detector_and_shell_cold_start_after_exact_disposition": "shared rollover shell detection consumer",
    "tests/orchestration/test_imported_rollover_detection.py::test_imported_pending_packet_launcher_binding": "shared rollover shell detection after cross-host bundle import",
    "tests/test_start_claude_profiles.py::test_native_claude_clears_foreign_route_and_capacity_overrides": "retained launcher failure from the historical exact-head manifest",
    "tests/test_start_codex_driver.py::test_sustained_driver_probes_then_claims_lease_then_binds_drive_epic": "retained launcher failure from the historical exact-head manifest",
    "tests/test_start_codex_driver.py::test_driver_launch_with_caller_prompt_passes_one_positional_prompt": "retained launcher failure from the historical exact-head manifest",
    "tests/test_start_codex_driver.py::test_default_driver_forwards_epic_binding_and_extra_provider_flags": "retained launcher failure from the historical exact-head manifest",
    "tests/test_start_codex_driver.py::test_sustained_codex_driver_revalidates_certification": "retained launcher failure from the historical exact-head manifest",
    "tests/test_start_codex_driver.py::test_non_model_passthrough_remains_available": "retained launcher failure from the historical exact-head manifest",
    "tests/test_start_codex_driver.py::test_non_driver_workers_are_rejected_for_driver_and_governor": "retained launcher failure from the historical exact-head manifest",
    "tests/test_launcher_contract.py::test_real_launcher_deploy_is_confined_to_temporary_checkout": "retained launcher failure from the historical exact-head manifest",
    "tests/test_launcher_contract.py::test_codex_driver_preserves_transport_probe_and_lease_guard": "retained launcher failure from the historical exact-head manifest",
    "tests/test_launcher_contract.py::test_real_store_driver_close_successor_and_expired_recovery": "retained launcher failure from the historical exact-head manifest",
    "tests/orchestration/test_codex_driver_rollover_recovery.py::test_pending_packet_older_than_lane_handoff_is_not_bound": "audited real rollover-shell helper consumer",
    "tests/orchestration/test_codex_driver_rollover_recovery.py::test_2026_11_02_relaunch_resumes_the_lane_packet_and_mints_ten_anchors": "audited real rollover-shell helper consumer",
}


def launcher_toolchain_path() -> str:
    """Declare executable directories without inheriting provider or seat state.

    npm may be an agent shim. Select its real executable from the toolchain
    PATH instead; its Node shebang then resolves from the same declared input.
    """
    search = os.environ.get("PATH", os.defpath).split(os.pathsep)
    search = [entry for entry in search if not entry.rstrip("/").endswith(
        ("/agent_runtime/shims", "/dispatcher/npm_shims")
    )]
    directories = [str(Path(sys.executable).parent)]
    for name in ("node", "npm", "git"):
        executable = shutil.which(name, path=os.pathsep.join(search))
        if executable is None:
            raise RuntimeError(f"launcher fixture requires declared toolchain executable: {name}")
        # A user-level node/npm symlink must not admit that user's providers.
        known = next((directory for directory in directories if (Path(directory) / name).is_file()
                      and (Path(directory) / name).samefile(executable)), None)
        directory = known or str(Path(executable).resolve().parent if name != "npm" else Path(executable).parent)
        directories.append(directory)
    directories.extend(os.defpath.split(os.pathsep))
    return os.pathsep.join(dict.fromkeys(directories))


def launcher_environment(
    *inputs: Mapping[str, str], tmp_path: Path | None = None, **extra: str
) -> dict[str, str]:
    """Build a fresh launcher environment, then overlay deliberate test inputs.

    Bash and its utilities need PATH and a UTF-8 locale. HOME and temporary
    files belong to this invocation, so credentials, Git config and seat state
    cannot come from the runner. Monitor calls fail locally unless a fixture
    supplies a stub endpoint. Only executable directories are selected from
    the caller's declared toolchain; no seat variable is copied.
    """
    if tmp_path is None:
        if not os.environ.get("LU_SCRATCH_ROOT", "").strip():
            raise RuntimeError("launcher_environment requires pytest scratch setup or an explicit tmp_path")
        tmp_path = ensure_scratch_root()
    root = Path(tempfile.mkdtemp(prefix="launcher-environment-", dir=tmp_path))
    for name in ("home", "tmp", "scratch", "guard-bin"):
        (root / name).mkdir()
    contact = root / "unexpected-manager-call"
    for name in ("systemd-run", "systemctl"):
        binary = root / "guard-bin" / name
        binary.write_text(f'#!/bin/sh\nprintf "%s\\n" "{name} $*" >> "$LU_TEST_REAL_MANAGER_CONTACT"\nexit 97\n')
        binary.chmod(0o755)
    env = {
        "PATH": f"{root / 'guard-bin'}{os.pathsep}{launcher_toolchain_path()}",
        "HOME": str(root / "home"),
        "TMPDIR": str(root / "tmp"),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "TERM": "dumb",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "LU_MONITOR_LOOPBACK": UNREACHABLE_MONITOR_URL,
        "TOOL_TIMING_API_URL": UNREACHABLE_TOOL_TIMING_URL,
        "DELEGATE_MONITOR_API": UNREACHABLE_MONITOR_URL,
        "FLEET_COMMS_ROOT": str(root / "fleet-plane"),
        "LU_TASKS_DIR": str(root / "task-store"),
        "LU_GITHUB_CACHE_DIR": str(root / "github-cache"),
        "LU_MODEL_PAUSE_FILE": str(root / "no-model-pause.json"),
        "LU_SCRATCH_ROOT": str(root / "scratch"),
        "LU_DRIVER_SCOPE_CONFIG": str(root / "no-driver-scope.env"),
        "LU_TEST_REAL_MANAGER_CONTACT": str(contact),
    }
    for values in inputs:
        env.update(values)
    env.update(extra)
    return env


def copy_launcher_sources(root: Path) -> None:
    """Copy the tracked launcher/deploy surface without an interpreter or Git init.

    Copy tracked files, rather than symlinking source directories: shell and
    Python helpers resolve their own physical location to choose deploy roots.
    Runtime mirrors and caches must never link back into the tested checkout.
    """
    root.mkdir(parents=True, exist_ok=True)
    tracked = subprocess.run(
        [
            "git",
            "ls-files",
            "-z",
            "--",
            "start-*.sh",
            "package.json",
            machinery_package(),
            "agents_extensions",
            ".gemini/config.yaml",
            "docs/l2-uk-en",
            "docs/prompts/orchestrators",
            "curriculum/l2-uk-en/curriculum.yaml",
        ],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
        env=launcher_environment(),
    )
    for raw in tracked.stdout.split("\0"):
        if not raw:
            continue
        relative = Path(raw)
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        source = _REPO_ROOT / relative
        if source.is_file():
            shutil.copy2(source, destination)
        else:
            # The real curriculum manifest may be sparse; use its tracked bytes.
            blob = subprocess.run(
                ["git", "show", f"HEAD:{relative.as_posix()}"],
                cwd=_REPO_ROOT,
                capture_output=True,
                check=True,
                timeout=30,
                env=launcher_environment(),
            )
            destination.write_bytes(blob.stdout)


def tracked_launcher_wrappers() -> tuple[str, ...]:
    """Every tracked public wrapper: the product's root ``start-*.sh`` and the machinery package's.

    The root wrappers are product files, listed in the product checkout; the machinery package's
    wrappers are listed here. :func:`launcher_wrapper_source` names the file to copy for each.
    """
    product = subprocess.run(
        ["git", "ls-files", "-z", "--", "start-*.sh"],
        cwd=product_checkout(),
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
        env=launcher_environment(),
    )
    machinery = subprocess.run(
        ["git", "ls-files", "-z", "--", f"{machinery_package()}/start-*.sh"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
        env=launcher_environment(),
    )
    listed = {raw for raw in (product.stdout + machinery.stdout).split("\0") if raw}
    return tuple(sorted(listed))


def launcher_wrapper_source(relative: str) -> Path:
    """The tracked file of the wrapper ``relative``: a product root wrapper or a machinery wrapper."""
    if "/" not in relative:
        return product_checkout() / relative
    return _REPO_ROOT / relative


def copy_interactive_launcher_checkout(root: Path) -> None:
    """Copy real launcher/deploy sources so production's root lookup stays in tmp."""
    copy_launcher_sources(root)
    # This is a temporary standalone fixture, not a dispatch worktree.
    (root / ".venv").symlink_to(Path(sys.prefix))
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True, timeout=30, env=launcher_environment())
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.com",
            "commit",
            "--allow-empty",
            "-q",
            "-m",
            "Initial launcher fixture",
        ],
        cwd=root,
        capture_output=True,
        check=True,
        timeout=30,
        env=launcher_environment(),
    )


# Runs the gate's own calls (a registered slot, an unregistered slot and the
# per-provider listing used in the refusal message) and prints the repo files
# they needed: imported modules plus any data file opened (the roster, catalogs).
# Imports are recorded from the files the import system reads (a module's
# ``.py`` or its cached ``.pyc``), not from ``sys.modules``: compatibility shims
# such as ``scripts/fleet_comms/contracts.py`` replace their own entry there.
# PYTHONPYCACHEPREFIX stores that bytecode beside a mirrored package directory,
# not under ``__pycache__``. Map both layouts back to the source path.
_PROBE = r"""
import importlib.util, json, os, sys
from pathlib import Path

root = Path.cwd().resolve()
sys.path.insert(0, str(root))  # the launcher runs the gate with `-m` from the repo root
opened = set()

def _source_for_bytecode(path):
    parent = os.path.basename(os.path.dirname(path))
    prefix = sys.pycache_prefix
    under_prefix = False
    if prefix:
        prefix = os.path.abspath(prefix)
        under_prefix = os.path.abspath(path).startswith(prefix + os.sep)
    if parent != "__pycache__" and not under_prefix:
        return path
    try:
        return importlib.util.source_from_cache(path)
    except (ValueError, OSError):
        return path

def _record(event, args):
    if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
        path = os.fsdecode(args[0])
        if path.endswith(".pyc"):
            path = _source_for_bytecode(path)
        opened.add(path)

sys.addaudithook(_record)
handoff_slot_registry = importlib.import_module(sys.argv[1])

codes = [
    handoff_slot_registry.main(["--slot", "claude-devops"]),
    handoff_slot_registry.main(["--slot", "claude-unregistered-sandbox-probe"]),
    handoff_slot_registry.main(["--list", "claude"]),
]
if codes != [0, 3, 0]:
    raise SystemExit(f"slot registry probe returned {codes}")
paths = opened | {m.__file__ for m in list(sys.modules.values()) if getattr(m, "__file__", None)}
print(json.dumps(sorted(paths)))
"""


@functools.cache
def slot_registry_sources() -> tuple[Path, ...]:
    """Repo-relative tracked files the launcher's handoff-slot gate needs."""
    probe = subprocess.run(
        [sys.executable, "-c", _PROBE, machinery_module("orchestration.handoff_slot_registry")],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
        timeout=120,
        env=launcher_environment(),
    )
    tracked = set(
        subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
            env=launcher_environment(),
        ).stdout.split("\0")
    )
    sources: set[Path] = set()
    for raw in json.loads(probe.stdout.splitlines()[-1]):
        path = Path(raw)
        if not path.is_absolute():
            path = _REPO_ROOT / path
        try:
            relative = path.resolve().relative_to(_REPO_ROOT)
        except ValueError:
            continue
        if relative.as_posix() in tracked:
            sources.add(relative)
    return tuple(sorted(sources))


def _copy_bytecode(source: Path, destination: Path) -> None:
    """Reuse the repo's compiled module so the sandbox does not recompile it.

    ``copy2`` keeps the source mtime and size, which is what the interpreter
    checks before trusting a cached ``.pyc``; a stale cache is recompiled as
    usual.  Without this every sandbox launch recompiles the bridge closure
    (about half a second per launcher run).
    """
    cached = Path(importlib.util.cache_from_source(source))
    if not cached.is_file():
        return
    target = Path(importlib.util.cache_from_source(destination))
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target.chmod(target.stat().st_mode | 0o200)
    shutil.copy2(cached, target)
    target.chmod(target.stat().st_mode | 0o200)


def copy_slot_registry(root: Path) -> None:
    """Give a launcher sandbox the real handoff-slot registry and its readers.

    Existing sandbox files are left alone so fixtures keep their stubs (for
    example the idle ``scripts/ai_agent_bridge/inbox_watch.sh``).
    """
    for relative in slot_registry_sources():
        destination = root / relative
        if destination.exists():
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(_REPO_ROOT / relative, destination)
        # A read-only canonical mode must not make the sandbox copy unwritable.
        destination.chmod(destination.stat().st_mode | 0o200)
        if relative.suffix == ".py":
            _copy_bytecode(_REPO_ROOT / relative, destination)
