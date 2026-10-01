"""Behavior tests for scripts/ci/test_env.sh (#9450)."""

from __future__ import annotations

import os
import re
import subprocess
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "ci" / "test_env.sh"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


def _seed(tmp_path: Path, tasks: dict[str, tuple[str | None, str]]) -> Path:
    """Create the state `start` leaves behind: tasks, logs and optional rc files."""
    env_dir = tmp_path / "test-env"
    env_dir.mkdir()
    (env_dir / "tasks").write_text("".join(f"{name}\n" for name in tasks))
    for name, (rc, log) in tasks.items():
        (env_dir / f"{name}.log").write_text(log)
        if rc is not None:
            (env_dir / f"{name}.rc").write_text(f"{rc}\n")
    return env_dir


def _wait(tmp_path: Path, limit: str | None) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "RUNNER_TEMP": str(tmp_path)}
    env.pop("TEST_ENV_WAIT_TIMEOUT_S", None)
    if limit is not None:
        env["TEST_ENV_WAIT_TIMEOUT_S"] = limit
    return subprocess.run(
        ["bash", str(SCRIPT), "wait"],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


def test_missing_marker_fails_within_limit_and_names_task(tmp_path: Path) -> None:
    _seed(tmp_path, {"postgres": (None, "starting postgres\n")})
    started = time.monotonic()
    result = _wait(tmp_path, "2")
    elapsed = time.monotonic() - started
    assert result.returncode == 1
    assert elapsed < 10
    assert "::error::postgres setup did not finish within 2s" in result.stdout
    assert "starting postgres" in result.stdout


def test_huge_log_cannot_hold_step_past_deadline_and_error_comes_first(tmp_path: Path) -> None:
    env_dir = _seed(tmp_path, {"postgres": (None, "")})
    with (env_dir / "postgres.log").open("wb") as handle:
        handle.write(b"x" * (50 * 1024 * 1024))
    started = time.monotonic()
    result = _wait(tmp_path, "2")
    elapsed = time.monotonic() - started
    assert result.returncode == 1
    assert elapsed < 6
    assert result.stdout.startswith("::error::postgres setup did not finish within 2s\n")
    assert len(result.stdout) < 70_000


def test_finished_huge_log_is_bounded_to_last_200_lines(tmp_path: Path) -> None:
    log = "".join(f"line {i}\n" for i in range(5000))
    _seed(tmp_path, {"npm": ("0", log)})
    result = _wait(tmp_path, None)
    assert result.returncode == 0
    assert "line 4999\n" in result.stdout
    assert "line 4800\n" in result.stdout
    assert "line 4799\n" not in result.stdout


def test_missing_log_still_names_task(tmp_path: Path) -> None:
    env_dir = _seed(tmp_path, {"postgres": (None, "")})
    (env_dir / "postgres.log").unlink()
    result = _wait(tmp_path, "2")
    assert result.returncode == 1
    assert "::error::postgres setup did not finish within 2s" in result.stdout
    assert "(no log)" in result.stdout


def test_empty_marker_is_not_finished_yet(tmp_path: Path) -> None:
    env_dir = _seed(tmp_path, {"postgres": (None, "pg log\n")})
    (env_dir / "postgres.rc").write_text("")
    result = _wait(tmp_path, "2")
    assert result.returncode == 1
    assert "exit )" not in result.stdout
    assert "::error::postgres setup did not finish within 2s" in result.stdout


def test_start_publishes_marker_atomically(tmp_path: Path) -> None:
    env = {**os.environ, "RUNNER_TEMP": str(tmp_path)}
    started = subprocess.run(
        ["bash", str(SCRIPT), "start", "bogus"],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert started.returncode == 0
    result = _wait(tmp_path, "20")
    assert result.returncode == 1
    assert "::group::bogus setup (exit 2)" in result.stdout
    assert "unknown task: bogus" in result.stdout
    assert not (tmp_path / "test-env" / "bogus.rc.tmp").exists()


def test_one_deadline_covers_all_tasks_and_finished_ones_still_report(tmp_path: Path) -> None:
    _seed(
        tmp_path,
        {
            "postgres": (None, "pg log\n"),
            "npm": ("0", "npm log\n"),
            "extra": (None, "extra log\n"),
        },
    )
    started = time.monotonic()
    result = _wait(tmp_path, "2")
    elapsed = time.monotonic() - started
    assert result.returncode == 1
    # Two stalled tasks share one 2s deadline instead of waiting 2s each.
    assert elapsed < 4
    assert "::error::postgres setup did not finish within 2s" in result.stdout
    assert "::error::extra setup did not finish within 2s" in result.stdout
    assert "::group::npm setup (exit 0)" in result.stdout
    assert "npm log" in result.stdout


def test_finished_tasks_success_unchanged(tmp_path: Path) -> None:
    _seed(tmp_path, {"postgres": ("0", "pg ok\n"), "npm": ("0", "npm ok\n")})
    result = _wait(tmp_path, None)
    assert result.returncode == 0
    assert "::group::postgres setup (exit 0)\npg ok\n::endgroup::" in result.stdout
    assert "::group::npm setup (exit 0)\nnpm ok\n::endgroup::" in result.stdout
    assert "::error::" not in result.stdout


def test_finished_task_failure_unchanged(tmp_path: Path) -> None:
    _seed(tmp_path, {"postgres": ("0", "pg ok\n"), "npm": ("1", "npm boom\n")})
    result = _wait(tmp_path, None)
    assert result.returncode == 1
    assert "::group::npm setup (exit 1)\nnpm boom\n::endgroup::" in result.stdout
    assert "::error::npm setup failed (exit 1); see its log group above" in result.stdout
    assert "did not finish" not in result.stdout


def test_invalid_limit_exits_2(tmp_path: Path) -> None:
    _seed(tmp_path, {"postgres": ("0", "pg ok\n")})
    for bad in ("abc", "0", "-5", "1.5", "007"):
        result = _wait(tmp_path, bad)
        assert result.returncode == 2, bad
        assert "TEST_ENV_WAIT_TIMEOUT_S must be a positive integer" in result.stderr, bad


def test_empty_limit_uses_default(tmp_path: Path) -> None:
    _seed(tmp_path, {"postgres": ("0", "pg ok\n")})
    assert _wait(tmp_path, "").returncode == 0


def test_default_bound_is_below_workflow_step_timeout() -> None:
    match = re.search(r"TEST_ENV_WAIT_TIMEOUT_S:-(\d+)\}", SCRIPT.read_text())
    assert match, "default of TEST_ENV_WAIT_TIMEOUT_S not found in test_env.sh"
    default_s = int(match.group(1))

    workflow = yaml.safe_load(CI_WORKFLOW.read_text())
    steps = [
        step
        for job in workflow["jobs"].values()
        for step in job.get("steps", [])
        if str(step.get("run", "")).strip() == "bash scripts/ci/test_env.sh wait"
    ]
    assert steps, "no `bash scripts/ci/test_env.sh wait` step in ci.yml"
    for step in steps:
        assert "timeout-minutes" in step, "wait step has no timeout-minutes"
        assert step["timeout-minutes"] * 60 > default_s
