#!/usr/bin/env python3
"""Synthetic tests for the text-free Cycle-007 evidence compile runner."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load_runner() -> Any:
    path = ROOT / "batch_state" / "phase3-compile-cycle007-evidence-v1.py"
    spec = importlib.util.spec_from_file_location("cycle007_evidence_compile_runner", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RUNNER = _load_runner()


def _private_file(path: Path, value: bytes = b"{}\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    path.write_bytes(value)
    os.chmod(path, 0o600)


def _arguments(package: Path, *, endpoint: str = "http://127.0.0.1:18476/mcp") -> list[str]:
    return [
        "--package",
        str(package),
        "--source-manifest",
        str(package / "manifest.json"),
        "--output",
        str(package / "evidence"),
        "--mcp-endpoint",
        endpoint,
    ]


def _package(tmp_path: Path) -> Path:
    package = tmp_path / "private-package"
    package.mkdir(mode=0o700)
    os.chmod(package, 0o700)
    _private_file(package / "manifest.json")
    return package


def _result(capsys: pytest.CaptureFixture[str]) -> dict[str, Any]:
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 1
    return json.loads(lines[0])


def test_rejects_path_and_mode_drift_without_echoing_private_paths(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    package = _package(tmp_path)
    package.chmod(0o755)
    sentinel = "PRIVATE-PATH-SENTINEL"
    code = RUNNER.main([*_arguments(package), "--ignored", sentinel])
    payload = _result(capsys)
    assert code == 1
    assert payload == {"failure_code": "argument_invalid", "ok": False, "text_free": True}
    assert sentinel not in json.dumps(payload)

    code = RUNNER.main(_arguments(package))
    payload = _result(capsys)
    assert code == 1
    assert payload == {"failure_code": "package_mode_invalid", "ok": False, "text_free": True}

    package.chmod(0o700)
    (package / "manifest.json").chmod(0o644)
    code = RUNNER.main(_arguments(package))
    assert _result(capsys) == {"failure_code": "source_manifest_mode_invalid", "ok": False, "text_free": True}

    (package / "manifest.json").chmod(0o600)
    _private_file(package / "evidence" / "already-there")
    code = RUNNER.main(_arguments(package))
    assert code == 1
    assert _result(capsys) == {"failure_code": "output_exists", "ok": False, "text_free": True}


def test_rejects_nonexact_and_occupied_endpoints_before_starting_server(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    package = _package(tmp_path)
    code = RUNNER.main(_arguments(package, endpoint="http://localhost:18476/mcp"))
    assert code == 1
    assert _result(capsys) == {"failure_code": "endpoint_invalid", "ok": False, "text_free": True}

    monkeypatch.setattr(RUNNER, "_endpoint_is_listening", lambda _host, _port: True)
    code = RUNNER.main(_arguments(package))
    assert code == 1
    assert _result(capsys) == {"failure_code": "endpoint_occupied", "ok": False, "text_free": True}


def test_runtime_python_preserves_lexical_venv_entrypoint(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    venv_entry = tmp_path / "venv" / "bin" / "python"
    venv_entry.parent.mkdir(parents=True)
    venv_entry.symlink_to(Path(sys.executable).resolve())
    monkeypatch.setattr(RUNNER.sys, "executable", str(venv_entry))
    assert RUNNER._runtime_python() == Path(os.path.abspath(venv_entry))
    assert RUNNER._runtime_python() != venv_entry.resolve()


class _Process:
    def __init__(self) -> None:
        self.stopped = False

    def poll(self) -> None:
        return None

    def terminate(self) -> None:
        self.stopped = True

    def wait(self, timeout: float) -> int:
        del timeout
        return 0


class _Client:
    def __enter__(self) -> _Client:
        return self

    def __exit__(self, *exc_info: object) -> None:
        return None


def test_managed_server_cleanup_and_text_free_stdout_on_success_and_compile_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    package = _package(tmp_path)
    started: list[_Process] = []

    def start(_endpoint: str) -> _Process:
        process = _Process()
        started.append(process)
        return process

    monkeypatch.setattr(RUNNER, "_start_reviewed_sources_server", start)
    monkeypatch.setattr(RUNNER.compiler, "LocalMcpSourcesClient", lambda **_kwargs: _Client())
    manifest = {
        "packet_count": 204,
        "row_count": 10159,
        "manifest_sha256": "a" * 64,
        "network_lookups_performed": 0,
    }
    monkeypatch.setattr(RUNNER.compiler, "compile_cycle007_package", lambda *_args, **_kwargs: manifest)

    assert RUNNER.main(_arguments(package)) == 0
    payload = _result(capsys)
    assert payload == {"manifest_sha256": "a" * 64, "network_lookups_performed": 0, "ok": True, "packet_count": 204, "row_count": 10159, "text_free": True}
    assert started[0].stopped is True

    sentinel = "PRIVATE-ROW-SENTINEL"

    def fail_compile(*_args: object, **_kwargs: object) -> dict[str, Any]:
        raise RuntimeError(sentinel)

    monkeypatch.setattr(RUNNER.compiler, "compile_cycle007_package", fail_compile)
    assert RUNNER.main(_arguments(package)) == 1
    payload = _result(capsys)
    assert payload == {"failure_code": "compile_failed", "ok": False, "text_free": True}
    assert sentinel not in json.dumps(payload)
    assert len(started) == 2 and started[1].stopped is True


def test_server_launch_uses_lexical_python_and_managed_process_options(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}
    process = _Process()

    class _Response:
        def __enter__(self) -> _Response:
            return self

        def __exit__(self, *exc_info: object) -> None:
            return None

        def read(self) -> bytes:
            return b'{"status":"ok","commit_sha":"b"}'

    def popen(command: list[str], **kwargs: Any) -> _Process:
        captured["command"] = command
        captured["kwargs"] = kwargs
        return process

    monkeypatch.setattr(RUNNER, "_endpoint_is_listening", lambda _host, _port: False)
    monkeypatch.setattr(RUNNER, "_expected_commit", lambda: "b")
    monkeypatch.setattr(RUNNER, "_runtime_python", lambda: Path("/lexical/venv/bin/python"))
    monkeypatch.setattr(RUNNER.subprocess, "Popen", popen)
    monkeypatch.setattr(RUNNER.urllib.request, "urlopen", lambda *_args, **_kwargs: _Response())
    assert RUNNER._start_reviewed_sources_server("http://127.0.0.1:18476/mcp") is process
    assert captured["command"][0] == "/lexical/venv/bin/python"
    assert captured["command"][1] == str(RUNNER.SERVER_PATH)
    assert captured["kwargs"] == {
        "cwd": RUNNER.ROOT,
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "shell": False,
        "start_new_session": True,
    }
