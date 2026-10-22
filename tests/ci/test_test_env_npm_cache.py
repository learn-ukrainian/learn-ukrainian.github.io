"""Behavior tests for the npm task in scripts/ci/test_env.sh (#11393).

Defect classes covered, named in each test:
  - registry outage hangs the install past the deadline
  - no cache preference revalidates against the registry
  - unbounded retry exceeds the deadline
"""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "ci" / "test_env.sh"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


def _fake_npm(tmp_path: Path) -> tuple[Path, Path]:
    """Install a fake `npm` that records its arguments and follows NPM_SHIM_MODE."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    args_log = tmp_path / "npm-args.log"
    state = tmp_path / "npm-state"
    npm = bin_dir / "npm"
    npm.write_text(
        "#!/bin/sh\n"
        f'printf "%s\\n" "$*" >> "{args_log}"\n'
        'case "${NPM_SHIM_MODE:-ok}" in\n'
        "  ok) exit 0 ;;\n"
        "  fail)\n"
        '    echo "npm error code EAI_AGAIN" >&2\n'
        "    exit 1\n"
        "    ;;\n"
        "  fail-once)\n"
        f'    if [ -e "{state}" ]; then exit 0; fi\n'
        f'    : > "{state}"\n'
        '    echo "npm error code EAI_AGAIN" >&2\n'
        "    exit 1\n"
        "    ;;\n"
        "  hang) exec sleep 600 ;;\n"
        "  term-resistant)\n"
        f"    trap 'echo TERM > \"{state}.term\"' TERM\n"
        "    while :; do sleep 1; done\n"
        "    ;;\n"
        "esac\n"
    )
    npm.chmod(0o755)
    return bin_dir, args_log


def _run_npm_task(
    tmp_path: Path, bin_dir: Path, mode: str, limit: int | None
) -> tuple[subprocess.CompletedProcess[str], float]:
    env = {
        **os.environ,
        "RUNNER_TEMP": str(tmp_path),
        "NPM_SHIM_MODE": mode,
        "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
    }
    env.pop("TEST_ENV_WAIT_TIMEOUT_S", None)
    if limit is not None:
        env["TEST_ENV_WAIT_TIMEOUT_S"] = str(limit)
    started = subprocess.run(
        ["bash", str(SCRIPT), "start", "npm"],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert started.returncode == 0, started.stderr
    began = time.monotonic()
    result = subprocess.run(
        ["bash", str(SCRIPT), "wait"],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    return result, time.monotonic() - began


def test_warm_cache_installs_from_cache_without_audit_registry_calls(tmp_path: Path) -> None:
    """Defect class: no cache preference revalidates against the registry."""
    bin_dir, args_log = _fake_npm(tmp_path)
    result, _ = _run_npm_task(tmp_path, bin_dir, "ok", limit=20)
    assert result.returncode == 0, result.stdout + result.stderr
    calls = args_log.read_text().splitlines()
    assert len(calls) == 1, calls
    args = calls[0].split()
    assert args[:2] == ["ci", "--ignore-scripts"]
    assert "--prefer-offline" in args
    assert "--no-audit" in args
    assert "--no-fund" in args
    assert "--fetch-retries=0" in args
    assert any(arg.startswith("--fetch-timeout=") for arg in args)
    assert "::group::npm setup (exit 0)" in result.stdout


def test_transient_registry_failure_is_retried_then_succeeds(tmp_path: Path) -> None:
    """Defect class: a transient registry failure is not retried."""
    bin_dir, args_log = _fake_npm(tmp_path)
    result, _ = _run_npm_task(tmp_path, bin_dir, "fail-once", limit=20)
    assert result.returncode == 0, result.stdout + result.stderr
    calls = args_log.read_text().splitlines()
    assert len(calls) == 2, calls
    assert "npm ci attempt 1/3 failed (exit 1); retrying in 1s" in result.stdout
    assert "::group::npm setup (exit 0)" in result.stdout


def test_cold_cache_with_unreachable_registry_fails_fast_and_clearly(tmp_path: Path) -> None:
    """Defect class: registry outage hangs the install past the deadline."""
    bin_dir, args_log = _fake_npm(tmp_path)
    result, elapsed = _run_npm_task(tmp_path, bin_dir, "fail", limit=10)
    assert result.returncode == 1
    assert elapsed < 10
    assert len(args_log.read_text().splitlines()) == 3
    assert "npm ci failed after 3 attempt(s) within the 8s install budget" in result.stdout
    assert "shared wait deadline 10s" in result.stdout
    assert "::error::npm setup failed (exit 1)" in result.stdout
    assert "did not finish" not in result.stdout


def test_hung_registry_is_cut_off_before_the_shared_deadline(tmp_path: Path) -> None:
    """Defect class: unbounded retry exceeds the deadline."""
    bin_dir, args_log = _fake_npm(tmp_path)
    result, elapsed = _run_npm_task(tmp_path, bin_dir, "hang", limit=10)
    assert result.returncode == 1
    assert elapsed < 15
    assert "did not finish" not in result.stdout
    assert "::error::npm setup failed (exit 1)" in result.stdout
    assert "npm ci failed after" in result.stdout
    assert "within the 8s install budget" in result.stdout
    assert len(args_log.read_text().splitlines()) >= 1


@pytest.mark.parametrize("limit", [4, 2, 10])
def test_term_resistant_npm_cannot_outlive_the_shared_deadline(tmp_path: Path, limit: int) -> None:
    """Defect class: termination grace outlives the shared deadline.

    A TERM-resistant npm must be SIGKILLed, and the failure marker written,
    strictly before `wait` reports. With no reserve the kill grace runs past a
    short deadline, so `wait` prints "did not finish" and the marker lands
    afterwards.
    """
    bin_dir, args_log = _fake_npm(tmp_path)
    result, elapsed = _run_npm_task(tmp_path, bin_dir, "term-resistant", limit=limit)
    marker = tmp_path / "test-env" / "npm.rc"
    assert result.returncode == 1, result.stdout + result.stderr
    # `wait` prints a group only after it has read a whole exit code, so a
    # typed group below proves the marker was published before the report.
    assert "::group::npm setup (exit 1)" in result.stdout
    assert "::error::npm setup failed (exit 1)" in result.stdout
    assert "did not finish" not in result.stdout
    assert marker.read_text().strip() == "1"
    assert (
        f"within the {limit}s shared wait deadline" in result.stdout
        or f"shared wait deadline {limit}s" in result.stdout
    ), result.stdout
    assert elapsed < limit + 2, elapsed
    if limit > 2:
        assert "install budget" in result.stdout
        # The shim trapped TERM and kept running until the kill grace ended it.
        assert (tmp_path / "npm-state.term").exists()
        assert len(args_log.read_text().splitlines()) == 1
    else:
        assert f"cannot start within the {limit}s shared wait deadline" in result.stdout
        assert not (tmp_path / "npm-state.term").exists()


@pytest.mark.parametrize("limit", [1, 2, 3, 5])
def test_every_accepted_short_deadline_fails_typed_within_the_deadline(tmp_path: Path, limit: int) -> None:
    """Defect class: termination grace outlives the shared deadline."""
    bin_dir, _ = _fake_npm(tmp_path)
    result, elapsed = _run_npm_task(tmp_path, bin_dir, "fail", limit=limit)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "did not finish" not in result.stdout
    assert (
        f"within the {limit}s shared wait deadline" in result.stdout
        or f"shared wait deadline {limit}s" in result.stdout
    ), result.stdout
    assert (tmp_path / "test-env" / "npm.rc").read_text().strip() == "1"
    assert elapsed < limit + 2, elapsed


def test_default_deadline_budget_reserves_termination_and_reporting(
    tmp_path: Path,
) -> None:
    """Defect class: termination grace outlives the shared deadline.

    Assert the computed default budget arithmetically instead of sleeping for
    240 s: 240 minus the 1 s kill grace and 1 s reporting margin is 238 s.
    """
    bin_dir, _ = _fake_npm(tmp_path)
    result, elapsed = _run_npm_task(tmp_path, bin_dir, "fail", limit=None)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "within the 238s install budget" in result.stdout
    assert "shared wait deadline 240s" in result.stdout
    assert elapsed < 40


def test_pull_request_npm_ci_steps_prefer_the_cache() -> None:
    """Defect class: no cache preference revalidates against the registry."""
    workflow = yaml.safe_load(CI_WORKFLOW.read_text())
    commands = [
        line.strip()
        for job in workflow["jobs"].values()
        for step in job.get("steps", [])
        for line in str(step.get("run", "")).splitlines()
        if line.strip().startswith("npm ci")
    ]
    assert len(commands) == 2, commands
    for command in commands:
        assert "--prefer-offline" in command, command
        assert "--no-audit" in command, command
        assert "--no-fund" in command, command
