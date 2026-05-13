"""Tests for delegate.py --check-budget pre-dispatch guard."""

from __future__ import annotations

import json
import sys
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import delegate


class _FakeBudgetResponse:
    def __init__(self, recommended: str = "codex"):
        self.recommended = recommended

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc, _tb):
        return False

    def read(self):
        return json.dumps(
            {
                "recommendation": {
                    "primary_agent_for_code": self.recommended,
                    "rationale": "fixture rationale",
                    "warnings": [],
                }
            }
        ).encode("utf-8")


class _FakeStdin:
    def write(self, _data):
        pass

    def close(self):
        pass


class _FakeProc:
    pid = 12345
    stdin = _FakeStdin()


def _dispatch_args(*extra: str):
    return delegate.build_parser().parse_args(
        [
            "dispatch",
            "--agent",
            "claude",
            "--task-id",
            "budget-check-fixture",
            "--prompt",
            "no-op",
            "--mode",
            "read-only",
            *extra,
        ]
    )


def _patch_spawn(monkeypatch, tmp_path):
    monkeypatch.setattr(delegate, "_TASKS_DIR", tmp_path / "tasks")
    monkeypatch.setattr(delegate.subprocess, "Popen", lambda *_args, **_kwargs: _FakeProc())
    telemetry = type(
        "_Telemetry",
        (),
        {"model": "fixture-model", "effort": "high", "cli_version": "fixture"},
    )()
    monkeypatch.setattr(
        "agent_runtime.telemetry.resolve_dispatch_start_telemetry",
        lambda **_kwargs: telemetry,
    )


def test_check_budget_warns_when_agent_mismatch(monkeypatch, tmp_path, capsys):
    _patch_spawn(monkeypatch, tmp_path)
    monkeypatch.setattr(delegate.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(
        delegate.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: _FakeBudgetResponse("codex"),
    )

    rc = delegate.cmd_dispatch(_dispatch_args("--check-budget"))

    assert rc == 0
    captured = capsys.readouterr()
    assert "⚠ ROUTING WARNING: budget recommends --agent codex, you passed --agent claude." in captured.err
    assert "Rationale: fixture rationale" in captured.err


def test_check_budget_skipped_when_force_agent(monkeypatch, tmp_path, capsys):
    _patch_spawn(monkeypatch, tmp_path)

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("urlopen should not be called with --force-agent")

    monkeypatch.setattr(delegate.urllib.request, "urlopen", fail_if_called)

    rc = delegate.cmd_dispatch(_dispatch_args("--check-budget", "--force-agent"))

    assert rc == 0
    assert "ROUTING WARNING" not in capsys.readouterr().err


def test_check_budget_skipped_when_api_down(monkeypatch, tmp_path, capsys):
    _patch_spawn(monkeypatch, tmp_path)
    monkeypatch.setattr(
        delegate.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(urllib.error.URLError("timeout")),
    )

    rc = delegate.cmd_dispatch(_dispatch_args("--check-budget"))

    assert rc == 0
    assert "⚠ ROUTING CHECK SKIPPED: Monitor API unreachable" in capsys.readouterr().err


def test_check_budget_off_by_default(monkeypatch, tmp_path, capsys):
    _patch_spawn(monkeypatch, tmp_path)

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("urlopen should not be called unless --check-budget is passed")

    monkeypatch.setattr(delegate.urllib.request, "urlopen", fail_if_called)

    rc = delegate.cmd_dispatch(_dispatch_args())

    assert rc == 0
    assert "ROUTING" not in capsys.readouterr().err


def test_check_budget_dry_run_does_not_spawn(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(delegate, "_TASKS_DIR", tmp_path / "tasks")
    monkeypatch.setattr(delegate.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(
        delegate.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: _FakeBudgetResponse("codex"),
    )

    def fail_if_spawned(*_args, **_kwargs):
        raise AssertionError("dry-run must not spawn a worker")

    monkeypatch.setattr(delegate.subprocess, "Popen", fail_if_spawned)

    rc = delegate.cmd_dispatch(_dispatch_args("--check-budget", "--dry-run"))

    assert rc == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == "budget-check-fixture"
    assert "ROUTING WARNING" in captured.err
