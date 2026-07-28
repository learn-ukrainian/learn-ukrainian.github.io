"""Contract tests for start-codex-driver.sh (sustained driver vs --governor mode)."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_LAUNCHER = _REPO_ROOT / "start-codex-driver.sh"


def _clean_environ() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def _run_driver(
    *arguments: str,
    env_override: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = _clean_environ()
    env["CODEX_DRIVER_DRY_RUN"] = "1"
    if env_override:
        env.update(env_override)
    return subprocess.run(
        ["bash", str(_LAUNCHER), *arguments],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )


def _runtime_launcher(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    launcher = root / "start-codex-driver.sh"
    handoff = root / "scripts" / "lib" / "handoff_identity.sh"
    python_stub = root / ".venv" / "bin" / "python"
    start_codex = root / "start-codex.sh"
    handoff.parent.mkdir(parents=True)
    python_stub.parent.mkdir(parents=True)
    shutil.copy2(_LAUNCHER, launcher)
    shutil.copy2(_REPO_ROOT / "scripts/lib/handoff_identity.sh", handoff)
    python_stub.write_text(
        """#!/bin/bash
if [ "${PROBE_STUB_EXIT:-0}" = "0" ]; then
  echo '{"status":"healthy","fresh":true}'
else
  echo '{"status":"degraded","fresh":true,"failure_class":"test"}'
fi
exit "${PROBE_STUB_EXIT:-0}"
""",
        encoding="utf-8",
    )
    start_codex.write_text(
        """#!/bin/bash
printf 'START_CODEX_CALLED %s\\n' "$*"
""",
        encoding="utf-8",
    )
    python_stub.chmod(0o755)
    start_codex.chmod(0o755)
    return launcher


def _run_runtime_launcher(
    launcher: Path,
    *,
    probe_exit: int,
) -> subprocess.CompletedProcess[str]:
    env = _clean_environ()
    env.pop("CODEX_DRIVER_DRY_RUN", None)
    env["PROBE_STUB_EXIT"] = str(probe_exit)
    return subprocess.run(
        ["bash", str(launcher), "--governor", "AUTO"],
        cwd=launcher.parent,
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )


def test_default_mode_forwards_epic_without_model_pin() -> None:
    res = _run_driver("devops")
    assert res.returncode == 0, res.stderr
    assert "would exec" in res.stdout
    assert "--epic devops" in res.stdout
    assert "--model" not in res.stdout


def test_default_mode_forwards_extra_flags() -> None:
    res = _run_driver("atlas", "--verbose", "--foo=bar")
    assert res.returncode == 0, res.stderr
    assert "--epic atlas" in res.stdout
    assert "--verbose --foo=bar" in res.stdout


def test_governor_mode_pins_model_unsets_epic_and_passes_prompt() -> None:
    res = _run_driver("--governor", "devops", env_override={"SESSION_EPIC": "should_be_unset"})
    assert res.returncode == 0, res.stderr
    assert "would exec" in res.stdout
    assert "--model gpt-5.6-sol" in res.stdout
    assert "--epic" not in res.stdout
    assert "dynamic-area-epic-fleet-governor.md" in res.stdout
    assert "TARGET=devops GOAL=AUTO" in res.stdout
    assert "would probe" in res.stdout
    assert "scripts.orchestration.codex_transport_health probe" in res.stdout
    assert "--model gpt-5.6-sol --effort low" in res.stdout
    assert "CODEX_FRESH_TRANSPORT" not in res.stdout
    # Load-bearing guard: an ambient SESSION_EPIC must be UNSET before exec so the
    # governor never claims the epic-driver lease. The dry-run echoes the resolved
    # value precisely so removing the `unset` line fails this assertion.
    assert "SESSION_EPIC=<unset>" in res.stdout
    assert "should_be_unset" not in res.stdout


def test_governor_help_flag_after_governor_shows_usage() -> None:
    res = _run_driver("--governor", "--help")
    assert res.returncode == 0, res.stderr
    assert "Usage:" in res.stdout


def test_bare_help_flag_shows_usage() -> None:
    res = _run_driver("--help")
    assert res.returncode == 0, res.stderr
    assert "Usage:" in res.stdout


def test_governor_mode_auto_selector_bypasses_validation() -> None:
    res = _run_driver("--governor", "AUTO")
    assert res.returncode == 0, res.stderr
    assert "--model gpt-5.6-sol" in res.stdout
    assert "TARGET=AUTO GOAL=AUTO" in res.stdout


def test_governor_mode_missing_selector_exits_2() -> None:
    res = _run_driver("--governor")
    assert res.returncode == 2
    assert "Usage:" in res.stderr


def test_unknown_selector_fails_in_default_and_governor_modes() -> None:
    res_def = _run_driver("unknown_selector_xyz")
    assert res_def.returncode == 2
    assert "Error: unknown lane selector 'unknown_selector_xyz'." in res_def.stderr

    res_gov = _run_driver("--governor", "unknown_selector_xyz")
    assert res_gov.returncode == 2
    assert "Error: unknown lane selector 'unknown_selector_xyz'." in res_gov.stderr


def test_governor_runtime_gate_refuses_degraded_transport(tmp_path) -> None:
    result = _run_runtime_launcher(_runtime_launcher(tmp_path), probe_exit=3)

    assert result.returncode == 3
    assert "fresh Codex transport is not healthy" in result.stderr
    assert '"status":"degraded"' in result.stderr
    assert "do not retry Codex" in result.stderr
    assert "START_CODEX_CALLED" not in result.stdout


def test_governor_runtime_gate_execs_sol_after_healthy_probe(tmp_path) -> None:
    result = _run_runtime_launcher(_runtime_launcher(tmp_path), probe_exit=0)

    assert result.returncode == 0, result.stderr
    assert "START_CODEX_CALLED --model gpt-5.6-sol" in result.stdout
    assert "dynamic-area-epic-fleet-governor.md" in result.stdout
    assert "CODEX_FRESH_TRANSPORT" not in result.stdout
