"""Regression coverage for intentional background-session detachment."""

from __future__ import annotations

import os
import signal
import time
from pathlib import Path

import pytest

from scripts.tools import detach_session_task


def _wait_for_text(path: Path, expected: str) -> None:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if path.exists() and expected in path.read_text(encoding="utf-8"):
            return
        time.sleep(0.02)
    pytest.fail(f"{path} did not contain {expected!r}")


def _stop_process(pid: int) -> None:
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.02)
    os.kill(pid, signal.SIGKILL)


def test_detach_creates_independent_session_and_redirects_logs(tmp_path: Path, capsys) -> None:
    log_file = tmp_path / "service.log"
    pid_file = tmp_path / "service.pid"
    ready_file = tmp_path / "ready"

    result = detach_session_task.main(
        [
            "--workdir",
            str(tmp_path),
            "--log-file",
            str(log_file),
            "--pid-file",
            str(pid_file),
            "--",
            "/bin/sh",
            "-c",
            f"printf ready > {ready_file}; printf stdout; printf stderr >&2; exec sleep 60",
        ]
    )

    assert result == 0
    pid = int(capsys.readouterr().out.strip())
    try:
        assert int(pid_file.read_text(encoding="ascii").strip()) == pid
        assert os.getsid(pid) != os.getsid(0)
        assert os.getpgid(pid) != os.getpgid(0)
        _wait_for_text(ready_file, "ready")
        _wait_for_text(log_file, "stdout")
        _wait_for_text(log_file, "stderr")
    finally:
        _stop_process(pid)


def test_detach_strips_task_scoped_tmpdir(tmp_path: Path, capsys, monkeypatch) -> None:
    log_file = tmp_path / "service.log"
    pid_file = tmp_path / "service.pid"
    observed = tmp_path / "tmpdir.txt"
    task_tmp = tmp_path / "task-tmp"
    task_tmp.mkdir()
    monkeypatch.setenv("TMPDIR", str(task_tmp))
    monkeypatch.setenv("LU_RUNTIME_TMP_ROOT", str(task_tmp))

    result = detach_session_task.main(
        [
            "--workdir",
            str(tmp_path),
            "--log-file",
            str(log_file),
            "--pid-file",
            str(pid_file),
            "--",
            "/bin/sh",
            "-c",
            f"printf '%s' \"${{TMPDIR-unset}}\" > {observed}; exec sleep 60",
        ]
    )

    assert result == 0
    pid = int(capsys.readouterr().out.strip())
    try:
        _wait_for_text(observed, "unset")
        assert observed.read_text(encoding="utf-8") == "unset"
    finally:
        _stop_process(pid)


def test_detach_refuses_to_replace_a_live_service_pid_file(tmp_path: Path) -> None:
    log_file = tmp_path / "service.log"
    pid_file = tmp_path / "service.pid"
    pid_file.write_text(f"{os.getpid()}\n", encoding="ascii")

    with pytest.raises(SystemExit, match="refusing to replace live service PID file"):
        detach_session_task.main(
            [
                "--workdir",
                str(tmp_path),
                "--log-file",
                str(log_file),
                "--pid-file",
                str(pid_file),
                "--",
                "/bin/sh",
                "-c",
                "exec sleep 60",
            ]
        )
