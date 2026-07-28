"""Codex driver regression coverage, including the lease-free governor guard."""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.test_launcher_contract import REPO, run_launcher


def _would_exec_argv(result: subprocess.CompletedProcess[str]) -> list[str]:
    """Return the redacted, exact CLI argv emitted by a launcher dry run."""
    return shlex.split(result.stdout.split("would exec ", maxsplit=1)[1].strip())


def _clean_environ() -> dict[str, str]:
    return {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}


def _runtime_launcher(tmp_path: Path) -> tuple[Path, Path]:
    """Build the minimal shared-launcher surface with observable probe and CLI stubs."""
    root = tmp_path / "repo"
    for relative in (
        "start-codex-driver.sh",
        "scripts/config/context_profiles.yaml",
        "scripts/lib/context_profiles.py",
        "scripts/lib/deploy_extensions.sh",
        "scripts/lib/launcher_core.sh",
        "scripts/lib/handoff_identity.sh",
        "scripts/lib/profile_resolver.sh",
        "scripts/lib/thread_rollover_link.sh",
        "scripts/launchers/codex.sh",
    ):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / relative, target)

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
exec {os.fspath(REPO / ".venv" / "bin" / "python")!r} "$@"
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


def test_sustained_driver_probes_then_claims_lease_then_binds_drive_epic() -> None:
    result = run_launcher(
        "start-codex-driver.sh", "--epic", "devops", "--model", "gpt-5.6-sol"
    )
    assert result.returncode == 0, result.stderr
    assert "would probe" in result.stdout
    assert result.stdout.index("would probe") < result.stdout.index("would claim lease")
    assert result.stdout.index("would claim lease") < result.stdout.index("would mint and bootstrap")
    assert result.stdout.index("would mint and bootstrap") < result.stdout.index("would bind drive-epic")


def test_governor_pins_sol_and_is_mutation_guarded_against_lease_claim() -> None:
    result = run_launcher(
        "start-codex-driver.sh",
        "--governor",
        "AUTO",
        env={"SESSION_EPIC": "foreign-lease-must-not-survive"},
    )
    assert result.returncode == 0, result.stderr
    argv = _would_exec_argv(result)
    model_index = argv.index("--model")
    assert argv[model_index + 1] == "gpt-5.6-sol"
    # Mutation guard: removing this seed leaves the bounded Sol invocation
    # without the operator-ordered supervision instruction.
    assert argv[model_index + 2] == (
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
    result = run_launcher(
        "start-codex-driver.sh", "devops", "--model", "gpt-5.6-sol", "--verbose", "--foo=bar"
    )
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


def test_governor_execs_sol_after_healthy_transport_probe(tmp_path: Path) -> None:
    launcher, executable_dir = _runtime_launcher(tmp_path)
    result = _run_runtime_governor(launcher, executable_dir, probe_exit=0)

    assert result.returncode == 0, result.stderr
    assert '{"status":"healthy","fresh":true}' in result.stdout
    assert "CODEX_EXEC" in result.stdout
    assert "--model gpt-5.6-sol" in result.stdout
    assert "dynamic-area-epic-fleet-governor.md" in result.stdout


def test_sustained_codex_driver_revalidates_certification() -> None:
    rejected = run_launcher("start-codex-driver.sh", "--epic", "devops", "--model", "gpt-unknown")
    sol = run_launcher("start-codex-driver.sh", "--epic", "devops", "--model", "gpt-5.6-sol")
    assert rejected.returncode == 4
    assert sol.returncode == 0, sol.stderr
    assert "--model gpt-5.6-sol" in sol.stdout
