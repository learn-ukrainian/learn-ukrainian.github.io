"""Codex driver regression coverage, including the lease-free governor guard."""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tests.launcher_libraries import launcher_library_files
from tests.rules_core_view import (
    install_loader_bypass,
    rules_core_absent_when_marked,  # noqa: F401  (autouse: serves @rules_core_absent)
)
from tests.test_launcher_contract import REPO, run_launcher
from tests.test_launcher_driver_scope import install_scope_sandbox


@pytest.fixture(autouse=True)
def _use_checkout_context_profile(monkeypatch):
    # The launcher resolves the human checkout as canonical; exercise this
    # checkout's profile contract without depending on its deployed version.
    monkeypatch.setenv("CLAUDE_PROFILE_RESOLVER_PY", str(REPO / "scripts/lib/context_profiles.py"))


def _would_exec_argv(result: subprocess.CompletedProcess[str]) -> list[str]:
    """Return the redacted, exact CLI argv emitted by a launcher dry run."""
    return shlex.split(result.stdout.split("would exec ", maxsplit=1)[1].strip())


def _clean_environ() -> dict[str, str]:
    return {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}


def test_launcher_library_inventory_includes_new_tracked_files(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True, timeout=30)
    library = tmp_path / "scripts/lib/new/nested-library.sh"
    library.parent.mkdir(parents=True)
    library.write_text("# Future launcher dependency\n")
    library.with_name("untracked.sh").write_text("# Local scratch\n")
    subprocess.run(["git", "add", "scripts/lib/new/nested-library.sh"], cwd=tmp_path, check=True, timeout=30)
    assert launcher_library_files(tmp_path) == (Path("scripts/lib/new/nested-library.sh"),)
    assert Path("scripts/lib/driver_scope.sh") in launcher_library_files(REPO)


def _runtime_launcher(tmp_path: Path) -> tuple[Path, Path]:
    """Build the minimal shared-launcher surface with observable probe and CLI stubs."""
    root = tmp_path / "repo"
    for relative in (
        "start-codex-driver.sh",
        "scripts/config/context_profiles.yaml",
        "scripts/review/model_catalog.py",
        "scripts/config/model_catalog.yaml",
        "scripts/config/launcher_stream_aliases.tsv",
        "scripts/launchers/codex.sh",
        *launcher_library_files(REPO),
    ):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / relative, target)
    install_scope_sandbox(root)
    install_loader_bypass(root)

    probe = root / ".venv" / "bin" / "python"
    probe.parent.mkdir(parents=True)
    probe.write_text(
        f"""#!/usr/bin/env bash
if [[ "${{1:-}}" == "-m" && "${{2:-}}" == "scripts.orchestration.codex_transport_health" ]]; then
  if [ "${{PROBE_STUB_EXIT:-0}}" = "0" ]; then
    printf '%s\\n' '{{"status":"healthy","fresh":true}}'
  else
    printf '%s\\n' '{{"status":"degraded","fresh":true,"failure_class":"test"}}'
  fi
  exit "${{PROBE_STUB_EXIT:-0}}"
fi
exec {sys.executable!r} "$@"
""",
        encoding="utf-8",
    )
    probe.chmod(0o755)

    executable_dir = tmp_path / "bin"
    executable_dir.mkdir()
    codex = executable_dir / "codex"
    codex.write_text(
        """#!/usr/bin/env bash
printf 'CODEX_EXEC %s\\n' "$*"
""",
        encoding="utf-8",
    )
    codex.chmod(0o755)
    initialized = subprocess.run(
        ["git", "init", "-q", "-b", "main", os.fspath(root)],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert initialized.returncode == 0, initialized.stderr
    return root / "start-codex-driver.sh", executable_dir


def _run_runtime_governor(
    launcher: Path,
    executable_dir: Path,
    *,
    probe_exit: int,
) -> subprocess.CompletedProcess[str]:
    env = _clean_environ()
    env["LAUNCHER_DRY_RUN"] = "0"
    env["PATH"] = f"{executable_dir}:{env.get('PATH', '')}"
    env["PROBE_STUB_EXIT"] = str(probe_exit)
    return subprocess.run(
        ["bash", str(launcher), "--governor", "AUTO"],
        cwd=launcher.parent,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )


def _runtime_driver_launcher(tmp_path: Path) -> tuple[Path, Path]:
    """Keep selector resolution and the Codex adapter real, with local lifecycle stubs."""
    launcher, executable_dir = _runtime_launcher(tmp_path)
    root = launcher.parent
    shutil.copy2(REPO / "scripts/config/issue_streams.yaml", root / "scripts/config/issue_streams.yaml")
    for relative, body in {
        "scripts/lib/thread_rollover_link.sh": """
clear_codex_launcher_rollover_env() { :; }
bootstrap_codex_checkout() { :; }
resolve_codex_pending_rollover() { :; }
""",
        "scripts/lib/deploy_extensions.sh": "deploy_agent_extensions() { :; }\n",
        "scripts/lib/fleet_comms_cold_start.sh": "fleet_comms_cold_clause() { :; }\n",
    }.items():
        (root / relative).write_text(body, encoding="utf-8")
    core = root / "scripts/lib/launcher_core.sh"
    with core.open("a", encoding="utf-8") as output:
        output.write("""
launcher_import_rollover_bundle() { :; }
launcher_claim_driver_lease() {
  launcher_prepare_driver_identity
  printf 'LEASE_STUB %s\\n' "$(launcher_selector_stream "$LC_EPIC")"
}
""")
    probe = root / ".venv/bin/python"
    body = probe.read_text(encoding="utf-8")
    body = body.replace(
        f'exec {sys.executable!r} "$@"',
        f"""if [[ "${{1:-}}" == "-m" && "${{2:-}}" == "scripts.orchestration.handoff_slot_registry" ]]; then
  exit 0
fi
if [[ "${{1:-}}" == "-m" && "${{2:-}}" == "scripts.session_canary.codex_lane" ]]; then
  printf 'CANARY_EXEC '; printf '%q ' "$@"; printf '\\n'
  # A missing/wrong stream must refuse execution, just as real mint does.
  case "${{5:-}}" in
    curriculum-upgrade) expected=epic:7994 ;;
    devops) expected=epic:5703 ;;
    *) exit 91 ;;
  esac
  [[ "$#" == 7 && "$4" == --epic && "$6" == --stream && "$7" == "$expected" ]] || exit 92
  exit 0
fi
# Refuse any unplanned module so this fixture cannot contact live services.
[[ "${{1:-}}" != -m ]] || exit 93
exec {sys.executable!r} "$@"
""",
    )
    probe.write_text(body, encoding="utf-8")
    return launcher, executable_dir


@pytest.mark.parametrize(
    ("selector", "stream"),
    [("curriculum-upgrade", "epic:7994"), ("devops", "epic:5703")],
)
def test_driver_canaries_use_canonical_stream_then_exec_provider(tmp_path: Path, selector: str, stream: str) -> None:
    launcher, executable_dir = _runtime_driver_launcher(tmp_path)
    result = run_launcher(
        launcher.name,
        "--epic",
        selector,
        root=launcher.parent,
        dry_run=False,
        env={
            **_clean_environ(),
            "CODEX_CANONICAL_REPO_ROOT": str(launcher.parent),
            "PATH": f"{executable_dir}:{os.environ.get('PATH', '')}",
        },
    )

    assert result.returncode == 0, result.stderr
    canaries = [
        shlex.split(line.removeprefix("CANARY_EXEC "))
        for line in result.stdout.splitlines()
        if line.startswith("CANARY_EXEC ")
    ]
    assert canaries == [
        ["-m", "scripts.session_canary.codex_lane", operation, "--epic", selector, "--stream", stream]
        for operation in ("mint", "bootstrap")
    ]
    assert f"LEASE_STUB {stream}" in result.stdout
    assert result.stdout.index("LEASE_STUB") < result.stdout.index("CANARY_EXEC")
    assert result.stdout.rindex("CANARY_EXEC") < result.stdout.index("CODEX_EXEC")


def test_runtime_driver_refuses_unknown_selector_before_canary_or_provider(tmp_path: Path) -> None:
    launcher, executable_dir = _runtime_driver_launcher(tmp_path)
    result = run_launcher(
        launcher.name,
        "--epic",
        "unknown-selector",
        root=launcher.parent,
        dry_run=False,
        env={
            **_clean_environ(),
            "CODEX_CANONICAL_REPO_ROOT": str(launcher.parent),
            "PATH": f"{executable_dir}:{os.environ.get('PATH', '')}",
        },
    )

    assert result.returncode == 2, result.stderr
    assert "unknown lane selector 'unknown-selector'" in result.stderr
    assert "LEASE_STUB" not in result.stdout
    assert "CANARY_EXEC" not in result.stdout
    assert "CODEX_EXEC" not in result.stdout


def test_sustained_driver_probes_then_claims_lease_then_binds_drive_epic() -> None:
    result = run_launcher("start-codex-driver.sh", "--epic", "devops", "--model", "gpt-6.1-sol")
    assert result.returncode == 0, result.stderr
    assert "would probe" in result.stdout
    assert result.stdout.index("would probe") < result.stdout.index("would claim lease")
    assert result.stdout.index("would claim lease") < result.stdout.index("would mint and bootstrap")
    assert result.stdout.index("would mint and bootstrap") < result.stdout.index("would bind drive-epic")


@pytest.mark.rules_core_absent
def test_governor_pins_astra_and_is_mutation_guarded_against_lease_claim() -> None:
    result = run_launcher(
        "start-codex-driver.sh",
        "--governor",
        "AUTO",
        env={"SESSION_EPIC": "foreign-lease-must-not-survive"},
    )
    assert result.returncode == 0, result.stderr
    argv = _would_exec_argv(result)
    model_index = argv.index("--model")
    assert argv[model_index + 1] == "gpt-6.1-sol"
    assert argv[model_index + 2 : model_index + 4] == ["-c", "model_reasoning_effort=high"]
    # Mutation guard: removing this seed leaves the bounded Astra invocation
    # without the operator-ordered supervision instruction.
    assert argv[model_index + 4] == (
        "Follow agents_extensions/shared/prompts/dynamic-area-epic-fleet-governor.md "
        "for one bounded supervision cycle. TARGET=AUTO GOAL=AUTO"
    )
    # This is intentionally observable: removing the core's `unset SESSION_EPIC`
    # changes this line and fails the test.
    assert "governor SESSION_EPIC=<unset>" in result.stdout
    assert "foreign-lease-must-not-survive" not in result.stdout
    assert "would claim lease" not in result.stdout


@pytest.mark.parametrize(
    "arguments",
    (("--help",), ("--governor", "--help")),
)
def test_codex_driver_help_succeeds_before_or_after_governor(arguments: tuple[str, ...]) -> None:
    result = run_launcher("start-codex-driver.sh", *arguments)
    assert result.returncode == 0, result.stderr
    assert "Usage:" in result.stdout


def test_governor_missing_selector_exits_usage_error() -> None:
    result = run_launcher("start-codex-driver.sh", "--governor")
    assert result.returncode == 2
    assert "requires a value" in result.stderr


@pytest.mark.parametrize(
    "arguments",
    (("not-a-selector",), ("--governor", "not-a-selector")),
)
def test_codex_driver_rejects_unknown_selector_in_default_and_governor_modes(
    arguments: tuple[str, ...],
) -> None:
    result = run_launcher("start-codex-driver.sh", *arguments)
    assert result.returncode == 2
    assert "unknown lane selector 'not-a-selector'" in result.stderr


def test_default_driver_forwards_epic_binding_and_extra_provider_flags() -> None:
    result = run_launcher("start-codex-driver.sh", "devops", "--model", "gpt-6.1-sol", "--verbose", "--foo=bar")
    assert result.returncode == 0, result.stderr
    assert "would claim lease" in result.stdout
    argv = _would_exec_argv(result)
    assert "--verbose" in argv
    assert "--foo=bar" in argv
    # Mutation guard: dropping the resolved selector from the injected binding
    # would launch a provider process without an auditable epic association.
    assert any("already claimed the devops lease" in argument for argument in argv)


def test_governor_refuses_degraded_transport_before_exec(tmp_path: Path) -> None:
    launcher, executable_dir = _runtime_launcher(tmp_path)
    result = _run_runtime_governor(launcher, executable_dir, probe_exit=1)

    assert result.returncode == 5
    assert "Codex transport is degraded" in result.stderr
    # Mutation guard: if the governor bypasses the adapter probe, this marker
    # appears because the stubbed Codex executable receives the invocation.
    assert "CODEX_EXEC" not in result.stdout


def test_governor_execs_astra_after_healthy_transport_probe(tmp_path: Path) -> None:
    launcher, executable_dir = _runtime_launcher(tmp_path)
    result = _run_runtime_governor(launcher, executable_dir, probe_exit=0)

    assert result.returncode == 0, result.stderr
    assert '{"status":"healthy","fresh":true}' in result.stdout
    assert "CODEX_EXEC" in result.stdout
    assert "--model gpt-6.1-sol" in result.stdout
    assert "model_reasoning_effort=high" in result.stdout
    assert "dynamic-area-epic-fleet-governor.md" in result.stdout


def test_sustained_codex_driver_revalidates_certification() -> None:
    rejected = run_launcher("start-codex-driver.sh", "--epic", "devops", "--model", "gpt-unknown")
    astra = run_launcher("start-codex-driver.sh", "--epic", "devops", "--model", "gpt-6.1-sol")
    assert rejected.returncode == 4
    assert astra.returncode == 0, astra.stderr
    assert "--model gpt-6.1-sol" in astra.stdout


def test_model_guard_rejects_old_codex_model_in_claude_code_harness():
    result = subprocess.run(
        [
            "bash",
            "-c",
            'launcher_error() { echo "$*" >&2; }; source "$1"; LC_HARNESS=claude-code; LC_MODEL=gpt-5.6-sol; launcher_adapter_validate',
            "test",
            str(REPO / "scripts/launchers/codex.sh"),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 2
    assert "approved models are gpt-6-luna, gpt-6.1-sol" in result.stderr


@pytest.mark.parametrize("harness", ["codex", "claude-code"])
@pytest.mark.parametrize(
    "forwarded",
    [
        ["--model", "gpt-5.5"],
        ["--model=gpt-5.5"],
        ["-m", "gpt-5.5"],
        ["-mgpt-5.5"],
        ["-m=gpt-5.5"],
    ],
)
def test_forwarded_model_overrides_rejected_before_preflight(harness, forwarded):
    result = run_launcher("start-codex.sh", "--harness", harness, "--", *forwarded)
    assert result.returncode == 2
    assert "Forwarded model overrides are forbidden" in result.stderr
    assert "would exec" not in result.stdout
    assert "would probe" not in result.stdout
    assert "would require binary" not in result.stdout


@pytest.mark.parametrize("harness", ["codex", "claude-code"])
def test_non_model_passthrough_remains_available(harness):
    result = run_launcher("start-codex.sh", "--harness", harness, "--", "--verbose", "inspect this")
    assert result.returncode == 0, result.stderr
    assert "--model gpt-6.1-sol" in result.stdout
    assert "--verbose" in result.stdout


@pytest.mark.parametrize(
    "forwarded",
    [
        ["--fallback-model", "claude-sonnet-5"],
        ["--fallback-model=claude-sonnet-5"],
        ["--agents", '{"reviewer":{"description":"Review","prompt":"Review","model":"sonnet"}}'],
        ['--agents={"reviewer":{"description":"Review","prompt":"Review","model":"sonnet"}}'],
    ],
)
def test_claude_code_forwarded_agent_and_fallback_models_rejected_before_preflight(forwarded):
    result = run_launcher("start-codex.sh", "--harness", "claude-code", "--", *forwarded)
    assert result.returncode == 2
    assert "Forwarded model overrides are forbidden" in result.stderr
    assert "would exec" not in result.stdout
    assert "would probe" not in result.stdout
    assert "would require binary" not in result.stdout


def test_luna_is_rejected_for_driver_and_governor() -> None:
    driver = run_launcher("start-codex-driver.sh", "--epic", "devops", "--model", "gpt-6-luna")
    assert driver.returncode == 4, driver.stderr
    assert "not certified" in driver.stderr
    governor = run_launcher("start-codex-driver.sh", "--governor", "AUTO", "--model", "gpt-6-luna")
    assert governor.returncode == 4, governor.stderr
    assert "not a governor model" in governor.stderr
    bounded = run_launcher("start-codex.sh", "--model", "gpt-6-luna")
    assert bounded.returncode == 0, bounded.stderr
    assert "--model gpt-6-luna" in bounded.stdout
