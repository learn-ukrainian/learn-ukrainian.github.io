"""Timeout contracts for the remaining #7213 slice 18 subprocess sites."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest

from scripts.review import snapshot

pytestmark = pytest.mark.reads_content


def _raise_timeout(calls: list[dict[str, Any]]):
    def fake_run(*args: object, **kwargs: Any) -> Any:
        calls.append({"args": args, **kwargs})
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])

    return fake_run


def test_snapshot_git_timeout_returns_rc124_and_fails_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(snapshot.subprocess, "run", _raise_timeout(calls))

    result = snapshot._run_git(Path("/usr/bin/git"), ["status"], cwd=tmp_path, check=False)

    assert result.returncode == 124
    assert result.stderr == "TimeoutExpired after 30s"
    assert calls[0]["timeout"] == snapshot.GIT_EVIDENCE_TIMEOUT_SECONDS == 30

    with pytest.raises(snapshot.ReviewSnapshotError, match="TimeoutExpired after 30s"):
        snapshot._run_git(Path("/usr/bin/git"), ["status"], cwd=tmp_path)
