"""Hermetic tests for ``delegate.py dispatch --preflight-triage`` (#8183)."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import pytest

import scripts.delegate as delegate
from scripts.typesafe import preflight_triage as pt

KEY = "sk-test-secret-key-123"
PATHS = ["scripts/x.py"]


def _fake(choice: str, conf: float, risk: float = 0.1):
    def system_one(state, questions, api_key):
        return {"answers": {"readiness": {"choice": choice, "confidence": conf}, "high_risk": {"noul": risk}}}

    return system_one


def test_broken_diff_fast_fails() -> None:
    res = pt.run_preflight(PATHS, "def f(:\n    # TODO\n", "no log", KEY, system_one=_fake("broken", 0.92))
    assert res.fast_fail
    assert res.label is pt.PreflightLabel.BROKEN_OR_FAILING
    assert "FAST-FAIL" in res.message


def test_high_risk_noul_alone_can_fast_fail_broken() -> None:
    assert pt.run_preflight(PATHS, "d", "l", KEY, system_one=_fake("broken", 0.5, 0.9)).fast_fail


def test_complete_diff_with_passing_log_passes() -> None:
    res = pt.run_preflight(PATHS, "ok", "5 passed", KEY, system_one=_fake("ready", 0.97))
    assert not res.fast_fail
    assert res.label is pt.PreflightLabel.READY_FOR_REVIEW


def test_missing_test_log_is_insufficient_evidence_not_fail() -> None:
    res = pt.run_preflight(PATHS, "d", pt.read_test_log(None), KEY, system_one=_fake("needs_human", 0.9))
    assert not res.fast_fail
    assert res.label is pt.PreflightLabel.INSUFFICIENT_EVIDENCE


def test_low_confidence_broken_does_not_fail() -> None:
    assert not pt.run_preflight(PATHS, "d", "l", KEY, system_one=_fake("broken", 0.6)).fast_fail


def test_missing_key_skips() -> None:
    def boom(*_a):
        raise AssertionError("must not call API")

    assert not pt.run_preflight(PATHS, "d", "l", "", system_one=boom).fast_fail


def test_api_error_skips_and_redacts_key() -> None:
    def failing(*_a):
        raise OSError(f"Authorization: Bearer {KEY}")

    res = pt.run_preflight(PATHS, "d", "l", KEY, system_one=failing)
    assert not res.fast_fail
    assert KEY not in res.message
    assert "OSError" in res.message


def test_malformed_response_skips() -> None:
    assert not pt.run_preflight(PATHS, "d", "l", KEY, system_one=lambda *_a: {"answers": None}).fast_fail


def test_load_api_key_prefers_file_then_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TYPESAFE_API_KEY", "env-key")
    keyfile = tmp_path / "k"
    assert pt.load_api_key(keyfile) == "env-key"
    keyfile.write_text("file-key\n")
    assert pt.load_api_key(keyfile) == "file-key"


def test_test_log_keeps_tail() -> None:
    out = pt.truncate_test_log("a" * 100 + "FAILED", limit=10)
    assert out.endswith("FAILED") and "truncated" in out


def test_record_fast_fail_counts_and_writes(tmp_path: Path) -> None:
    before = pt.FAST_FAIL_COUNT
    res = pt.PreflightResult(True, "m", pt.PreflightLabel.BROKEN_OR_FAILING, 0.9, 0.1)
    ledger = tmp_path / "l.jsonl"
    pt.record_fast_fail("t1", res, ledger)
    assert before + 1 == pt.FAST_FAIL_COUNT
    assert json.loads(ledger.read_text())["task_id"] == "t1"


def _git_repo(tmp_path: Path) -> Path:
    for cmd in (["init", "-q"], ["config", "user.email", "a@b"], ["config", "user.name", "n"]):
        subprocess.run(["git", *cmd], cwd=tmp_path, check=True, timeout=30)
    (tmp_path / "a.py").write_text("x = 1\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, timeout=30)
    subprocess.run(["git", "commit", "-qm", "i"], cwd=tmp_path, check=True, timeout=30)
    (tmp_path / "a.py").write_text("def f(:\n")
    return tmp_path


def _ns(repo: Path, **kw) -> argparse.Namespace:
    return argparse.Namespace(task_id="t-pre", cwd=str(repo), preflight_base="HEAD", preflight_test_log=None, **kw)


def test_hook_fast_fail_returns_distinct_code(tmp_path, monkeypatch) -> None:
    repo = _git_repo(tmp_path)
    monkeypatch.setattr(pt, "load_api_key", lambda: KEY)
    real = pt.run_preflight
    monkeypatch.setattr(pt, "run_preflight", lambda *a: real(*a, system_one=_fake("broken", 0.95)))
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "state" / "tasks"))
    assert delegate._run_preflight_triage(_ns(repo), worktree_arg=None) == pt.FAST_FAIL_EXIT_CODE
    assert (tmp_path / "state" / "preflight_fast_fail.jsonl").exists()


def test_hook_proceeds_without_key(tmp_path, monkeypatch) -> None:
    repo = _git_repo(tmp_path)
    monkeypatch.setattr(pt, "load_api_key", lambda: "")
    assert delegate._run_preflight_triage(_ns(repo), worktree_arg=None) is None


@pytest.mark.skipif(not __import__("os").environ.get("TYPESAFE_LIVE"), reason="TYPESAFE_LIVE not set")
def test_live_smoke() -> None:
    assert pt.load_api_key()
