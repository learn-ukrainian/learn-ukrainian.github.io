"""Timeout contracts for the remaining #7213 slice 18 subprocess sites."""

from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from scripts.generate_mdx import core as mdx_core
from scripts.generate_mdx import generate_plan_markdown
from scripts.hooks import hook_timing, measure_hook_stack
from scripts.lib import session_record
from scripts.review import snapshot


def _raise_timeout(calls: list[dict[str, Any]]):
    def fake_run(*args: object, **kwargs: Any) -> Any:
        calls.append({"args": args, **kwargs})
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])

    return fake_run


def test_mdx_validation_timeout_exits_nonzero(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(subprocess, "run", _raise_timeout(calls))
    monkeypatch.setattr(mdx_core, "get_modules_from_manifest", lambda *_args: [])
    monkeypatch.setattr(sys, "argv", ["generate_mdx.py", "--validate"])

    with pytest.raises(SystemExit) as raised:
        mdx_core.main()

    assert raised.value.code == 124
    assert calls[0]["timeout"] == mdx_core._VALIDATE_TIMEOUT_SECONDS == 60
    assert "MDX validation timed out after 60s" in capsys.readouterr().err


def test_plan_diff_timeout_exits_nonzero(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    base_path = tmp_path / "project"
    archive = base_path / "docs" / "l2-uk-en" / "_archive" / "HIST-CURRICULUM-PLAN.md"
    archive.parent.mkdir(parents=True)
    archive.write_text("old\n", encoding="utf-8")
    fake_file = base_path / "scripts" / "generate_plan_markdown.py"
    monkeypatch.setattr(generate_plan_markdown, "__file__", str(fake_file))
    monkeypatch.setattr(generate_plan_markdown, "generate_plan_markdown", lambda *_args: "new\n")
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(generate_plan_markdown.subprocess, "run", _raise_timeout(calls))
    monkeypatch.setattr(sys, "argv", ["generate_plan_markdown.py", "hist", "--diff"])

    with pytest.raises(SystemExit) as raised:
        generate_plan_markdown.main()

    assert raised.value.code == 124
    assert calls[0]["timeout"] == generate_plan_markdown._DIFF_TIMEOUT_SECONDS == 30
    assert "diff timed out after 30s" in capsys.readouterr().err
    assert not Path(calls[0]["args"][0][-1]).exists()


def test_hook_timing_timeout_returns_124_and_logs(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(hook_timing.subprocess, "run", _raise_timeout(calls))
    log_path = tmp_path / "hook-timing.jsonl"
    monkeypatch.setenv("HOOK_TIMING", "1")
    monkeypatch.setenv("HOOK_TIMING_LOG", str(log_path))
    monkeypatch.setattr(hook_timing.sys, "stdin", SimpleNamespace(buffer=io.BytesIO()))

    rc = hook_timing.run_wrapped(["fake-hook"])

    assert rc == 124
    assert calls[0]["timeout"] == hook_timing._HOOK_TIMEOUT_SECONDS == 60
    assert "hook command timed out after 60s" in capsys.readouterr().err
    row = json.loads(log_path.read_text(encoding="utf-8"))
    assert row["rc"] == 124


def test_measure_hook_stack_timeout_records_nonzero_rc(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(measure_hook_stack.subprocess, "run", _raise_timeout(calls))

    row = measure_hook_stack._time_one("fake-hook", ["fake-hook"], None, {}, repeats=1)

    assert row["rc"] == 124
    assert len(row["samples"]) == 1
    assert calls[0]["timeout"] == measure_hook_stack._HOOK_TIMEOUT_SECONDS == 60


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


def test_session_root_git_timeout_uses_existing_error_shape(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(session_record.subprocess, "run", _raise_timeout(calls))

    with pytest.raises(session_record.SessionRecordError, match="TimeoutExpired after 30s"):
        session_record.canonical_state_root(tmp_path)

    assert calls[0]["timeout"] == session_record._GIT_TIMEOUT_SECONDS == 30
