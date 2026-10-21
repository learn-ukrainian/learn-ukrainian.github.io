"""Regression tests for stdin temp-file spawn (#2159).

PTY-wrapped stdout/stderr plus PIPE stdin and a large write() caused Codex
CLI to exit rc=1 in under a second with no stderr. Feeding stdin from a temp
file matches ``cat prompt.txt | codex exec -``.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from agent_runtime.runner import (
    _cleanup_stdin_temp,
    _prepare_stdin_handle,
    _spawn_subprocess,
)
from tests.helpers.python import project_python

_TEST_PYTHON = project_python()


@pytest.fixture
def clean_env(monkeypatch):
    monkeypatch.delenv("DELEGATE_DISABLE_PTY", raising=False)
    yield


def test_large_stdin_reaches_child_via_temp_file_not_pipe_write(
    clean_env, tmp_path, monkeypatch,
):
    monkeypatch.setenv("DELEGATE_DISABLE_PTY", "1")
    payload = "X" * 200_000 + "\n"
    handle, path = _prepare_stdin_handle(payload)
    proc = None
    try:
        proc, _, _ = _spawn_subprocess(
            [
                _TEST_PYTHON,
                "-c",
                "import sys; data=sys.stdin.read(); "
                "print(len(data), data[:1], data[-2:])",
            ],
            cwd=tmp_path,
            env=os.environ.copy(),
            stdin=handle,
        )
        stdout, _stderr = proc.communicate(timeout=10)
        assert proc.returncode == 0, f"child failed: rc={proc.returncode}"
        assert "200001" in stdout
        assert "X" in stdout
    finally:
        if proc is not None and proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5.0)
        _cleanup_stdin_temp(path, handle)
