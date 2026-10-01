"""Behavior tests for scripts/ci/test_env.sh (#9450)."""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "ci" / "test_env.sh"


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
