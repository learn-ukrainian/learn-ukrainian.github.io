"""Regression tests for stdin temp-file spawn (#2159).

PTY-wrapped stdout/stderr plus PIPE stdin and a large write() caused Codex
CLI to exit rc=1 in under a second with no stderr. Feeding stdin from a temp
file matches ``cat prompt.txt | codex exec -``.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from agent_runtime.runner import (
    _STDIN_TEMP_PREFIX,
    _cleanup_stdin_temp,
    _prepare_stdin_handle,
    _spawn_subprocess,
)


def _resolve_test_python() -> str:
    candidate = _REPO_ROOT / ".venv" / "bin" / "python"
    if candidate.exists():
        return str(candidate)
    try:
        common_dir = subprocess.check_output(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=str(_REPO_ROOT),
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        if common_dir:
            main_venv = (Path(common_dir) / ".." / ".venv" / "bin" / "python").resolve()
            if main_venv.exists():
                return str(main_venv)
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        pass
    raise RuntimeError("missing .venv/bin/python")


_TEST_PYTHON = _resolve_test_python()


@pytest.fixture
def clean_env(monkeypatch):
    monkeypatch.delenv("DELEGATE_DISABLE_PTY", raising=False)
    yield


def test_prepare_stdin_handle_writes_payload_to_temp_file():
    handle, path = _prepare_stdin_handle("alpha\nomega")
    try:
        assert path is not None
        assert path.name.startswith(_STDIN_TEMP_PREFIX)
        assert path.read_text(encoding="utf-8") == "alpha\nomega"
    finally:
        _cleanup_stdin_temp(path, handle)


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


def test_initial_response_timeout_kills_silent_child(clean_env, tmp_path, monkeypatch):
    from agent_runtime import runner as runtime_runner
    from agent_runtime.adapters.base import InvocationPlan
    from agent_runtime.errors import AgentStalledError
    from agent_runtime.result import ParseResult
    from agent_runtime.telemetry import InvocationTelemetry

    class SilentAdapter:
        name = "claude"
        default_model = "fixture"
        supported_modes = frozenset({"read-only"})

        def build_invocation(self, **kwargs):
            return InvocationPlan(
                cmd=["/bin/sh", "-c", "sleep 60"],
                cwd=Path(kwargs["cwd"]),
            )

        def parse_response(self, *, returncode: int, **_kwargs):
            return ParseResult(ok=False, response="", stderr_excerpt="")

        def liveness_signal_paths(self, _plan):
            return ()

    monkeypatch.setattr(runtime_runner, "has_headroom", lambda *_a, **_k: (True, ""))
    monkeypatch.setattr(runtime_runner, "write_record", lambda _r: None)
    monkeypatch.setattr(
        runtime_runner,
        "resolve_invocation_telemetry",
        lambda **_k: InvocationTelemetry(
            model="fixture",
            effort="unknown",
            cli_version="fixture",
        ),
    )
    monkeypatch.setitem(runtime_runner._ADAPTER_CACHE, "claude", SilentAdapter())

    started = __import__("time").monotonic()
    with pytest.raises(AgentStalledError) as exc_info:
        runtime_runner.invoke(
            "claude",
            "hi",
            mode="read-only",
            cwd=tmp_path,
            hard_timeout=60,
            initial_response_timeout=2,
            stdout_silence_timeout=None,
        )
    elapsed = __import__("time").monotonic() - started
    assert exc_info.value.kind == "initial_response_timeout"
    assert elapsed < 15
