"""Behavior tests for scripts/ci/test_env.sh (#9450)."""

from __future__ import annotations

import os
import stat
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "ci" / "test_env.sh"
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


def test_marker_is_never_visible_while_its_write_is_in_flight(tmp_path: Path) -> None:
    """Stall the writer between creating the temp file and publishing it."""
    # `mv` is the publish step; a stand-in that sleeps first holds the writer in
    # the window where `.rc.tmp` exists but `.rc` must not.
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    slow_mv = fake_bin / "mv"
    release = tmp_path / "release-mv"
    slow_mv.write_text(
        f'#!/bin/sh\nwhile [ ! -e "{release}" ]; do sleep 0.01; done\nexec /bin/mv "$@"\n'
    )
    slow_mv.chmod(slow_mv.stat().st_mode | stat.S_IXUSR)
    env = {
        **os.environ,
        "RUNNER_TEMP": str(tmp_path),
        "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
    }
    started = subprocess.run(
        ["bash", str(SCRIPT), "start", "bogus"],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert started.returncode == 0
    env_dir = tmp_path / "test-env"
    marker, temp = env_dir / "bogus.rc", env_dir / "bogus.rc.tmp"
    deadline = time.monotonic() + 60
    while not temp.exists() and time.monotonic() < deadline:
        time.sleep(0.05)
    # The writer is now stalled in `mv`: nothing may be published yet.
    try:
        assert temp.exists(), "temp marker was never created"
        assert not marker.exists(), "marker visible before it was published"
    finally:
        release.touch()
    deadline = time.monotonic() + 30
    while not marker.exists() and time.monotonic() < deadline:
        time.sleep(0.1)
    assert marker.read_text().strip() == "2"
    assert not temp.exists()


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
