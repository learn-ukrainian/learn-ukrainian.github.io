from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest

from scripts.sync import promote_module, prune_module_forensics


def _raise_timeout(calls: list[dict[str, Any]]) -> Any:
    def fake_run(*args: object, **kwargs: Any) -> Any:
        calls.append(kwargs)
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])

    return fake_run


def test_promote_run_git_timeout_returns_124_when_check_false(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(promote_module.subprocess, "run", _raise_timeout(calls))

    result = promote_module._run_git(tmp_path, ["status"], check=False)

    assert calls[0]["timeout"] == 30
    assert result.returncode == 124
    assert result.args == ["git", "-C", str(tmp_path), "status"]
    assert result.stderr == b"TimeoutExpired after 30s"


def test_promote_run_git_timeout_raises_called_process_error_when_check_true(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(promote_module.subprocess, "run", _raise_timeout(calls))

    with pytest.raises(subprocess.CalledProcessError) as raised:
        promote_module._run_git(tmp_path, ["status"])

    assert calls[0]["timeout"] == 30
    assert raised.value.returncode == 124


def test_prune_run_git_timeout_returns_124_when_check_false(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(prune_module_forensics.subprocess, "run", _raise_timeout(calls))

    result = prune_module_forensics._run_git(tmp_path, ["status"], check=False)

    assert calls[0]["timeout"] == 30
    assert result.returncode == 124


def test_branch_for_worktree_timeout_returns_none(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(promote_module.subprocess, "run", _raise_timeout(calls))

    assert promote_module._branch_for_worktree(tmp_path) is None
    assert calls[0]["timeout"] == 30


def test_generate_readings_timeout_returns_nonzero_and_prints_error(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(promote_module.subprocess, "run", _raise_timeout(calls))
    source = promote_module.SourceSpec(build_ref="", level="folk", slug="test-module")

    status, written = promote_module._run_generate_readings(tmp_path, source)

    assert status == 124
    assert written == []
    assert calls[0]["timeout"] == 300
    assert "readings generator timed out after 300s" in capsys.readouterr().err
