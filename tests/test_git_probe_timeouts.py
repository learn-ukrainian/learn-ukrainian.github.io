"""Timeout contracts for the six git-probe subprocess sites (#7213 slice 17).

Every site below previously ran ``subprocess.run`` unbounded and now must:
1. pass ``timeout=30`` to every call, and
2. map ``subprocess.TimeoutExpired`` onto its existing fail-closed /
   non-zero / falsy shape (these run in hooks and CLI lanes, so a raw
   TimeoutExpired traceback must never escape).
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from scripts.hygiene import lane_disk_retention, root_entry_guard
from scripts.pre_commit import check_plan_immutability
from scripts.session_canary import grok_lane


def _raise_timeout(calls: list[dict[str, Any]]) -> Any:
    def fake_run(*args: object, **kwargs: Any) -> Any:
        calls.append(kwargs)
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])

    return fake_run


def _completed_ok(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args[0], 0, stdout="", stderr="")


# --- scripts/pre_commit/check_plan_immutability.py ---------------------------


def test_check_plan_run_git_timeout_raises_runtime_error_when_check_true(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(check_plan_immutability.subprocess, "run", _raise_timeout(calls))

    with pytest.raises(RuntimeError, match="timed out after 30s"):
        check_plan_immutability._run_git(tmp_path, "rev-parse", "--show-toplevel")

    assert calls[0]["timeout"] == 30


def test_check_plan_run_git_timeout_returns_rc124_when_check_false(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(check_plan_immutability.subprocess, "run", _raise_timeout(calls))

    result = check_plan_immutability._run_git(tmp_path, "status", check=False)

    assert calls[0]["timeout"] == 30
    assert result.returncode == 124


def test_check_plan_git_blob_exists_timeout_returns_false(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(check_plan_immutability.subprocess, "run", _raise_timeout(calls))

    assert check_plan_immutability._git_blob_exists(tmp_path, "HEAD:curriculum/a1/plans/x.yaml") is False
    assert calls[0]["timeout"] == 30


def test_check_plan_git_blob_exists_still_reports_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(check_plan_immutability.subprocess, "run", _completed_ok)

    assert check_plan_immutability._git_blob_exists(tmp_path, "HEAD:x") is True


# --- scripts/session_canary/grok_lane.py -------------------------------------


def _mint_args(repo: Path, out_dir: Path, handoff: Path) -> argparse.Namespace:
    return argparse.Namespace(
        repo=repo,
        epic="probe-epic",
        stream="epic:999",
        handoff=str(handoff),
        out_dir=str(out_dir),
        stream_limit=5,
        preferred=None,
    )


def test_grok_lane_cmd_mint_timeout_returns_124(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(grok_lane.subprocess, "run", _raise_timeout(calls))
    monkeypatch.setattr(grok_lane, "_load_stream_entries", lambda *a, **k: [])
    facts = [{"id": f"fact-{i}", "q": f"q{i}?", "a": f"a{i}"} for i in range(grok_lane.N_ANCHORS)]
    monkeypatch.setattr(grok_lane, "_build_facts", lambda **k: facts)
    handoff = tmp_path / "handoff.md"
    handoff.write_text("# Next Drive\n- x\n", encoding="utf-8")
    out_dir = tmp_path / "canary"

    rc = grok_lane.cmd_mint(_mint_args(tmp_path, out_dir, handoff))

    assert rc == 124
    assert calls[0]["timeout"] == grok_lane._CANARY_TIMEOUT_SECONDS == 30
    assert "context_canary mint timed out after 30s" in capsys.readouterr().err


def _score_args(tmp_path: Path, out_dir: Path, answers: Path) -> argparse.Namespace:
    return argparse.Namespace(
        repo=tmp_path,
        epic="probe-epic",
        out_dir=str(out_dir),
        answers=str(answers),
        context_tokens=1234,
        model="test-model",
        pass_ratio=grok_lane.DEFAULT_PASS_RATIO,
        threshold=grok_lane.DEFAULT_SIM_THRESHOLD,
        handoff=None,
        next_drive="",
        pins="",
        open_prs="",
        hands_off="",
        pending_user="",
        worktrees="",
        no_hydrate=True,
        preferred=None,
    )


def test_grok_lane_cmd_score_timeout_maps_to_fail_handoff_and_124(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(grok_lane.subprocess, "run", _raise_timeout(calls))
    out_dir = tmp_path / "canary"
    out_dir.mkdir()
    (out_dir / "probe.json").write_text(json.dumps({"anchors": []}), encoding="utf-8")
    answers = tmp_path / "answers.json"
    answers.write_text("{}", encoding="utf-8")

    rc = grok_lane.cmd_score(_score_args(tmp_path, out_dir, answers))

    assert rc == 124
    assert calls[0]["timeout"] == grok_lane._CANARY_TIMEOUT_SECONDS == 30
    verdict = json.loads((out_dir / "last_verdict.json").read_text(encoding="utf-8"))
    assert verdict["verdict"] == "FAIL-HANDOFF"
    assert verdict["rc"] == 124


# --- scripts/hygiene/lane_disk_retention.py ----------------------------------


def test_lane_disk_retention_git_timeout_returns_empty(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(lane_disk_retention.subprocess, "run", _raise_timeout(calls))

    assert lane_disk_retention._git(["status", "--porcelain"], cwd=tmp_path) == ""
    assert calls[0]["timeout"] == 30


# --- scripts/hygiene/root_entry_guard.py -------------------------------------


def test_root_entry_guard_run_git_timeout_maps_to_rc124(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(root_entry_guard.subprocess, "run", _raise_timeout(calls))

    proc = root_entry_guard._run_git(tmp_path, "ls-files", "-z")

    assert calls[0]["timeout"] == 30
    assert proc.returncode == root_entry_guard._TIMEOUT_RETURN_CODE == 124
    assert "TimeoutExpired after 30s" in proc.stderr


def test_root_entry_guard_tracked_names_fail_closed_on_timeout(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(root_entry_guard.subprocess, "run", _raise_timeout(calls))

    with pytest.raises(RuntimeError, match="TimeoutExpired"):
        root_entry_guard._tracked_top_level_names(tmp_path)
    assert calls[0]["timeout"] == 30
