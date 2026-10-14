"""Hermetic tests for the worktree GC sweep loop in the Monitor API server."""

from __future__ import annotations

import os
import threading
import time
from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import scripts.api.main as api_main
import scripts.api.state_helpers as state_helpers
from scripts.orchestration.reap_worktrees import ReapResult

client = TestClient(api_main.app, raise_server_exceptions=False)


def _patch_orient_sources(monkeypatch: pytest.MonkeyPatch) -> None:
    # Patch non-runtime sources to keep orient fast and hermetic
    monkeypatch.setattr(api_main, "_collect_git_orient_data", lambda *a, **k: {"branch": "main"})
    monkeypatch.setattr(api_main, "_collect_issues_orient_data", lambda *a, **k: {"issues": []})
    monkeypatch.setattr(api_main, "_collect_idle_prs_orient_data", lambda *a, **k: {"idle_prs": []})

    async def fake_pipeline(*a, **k):
        return {"summary": {}}

    monkeypatch.setattr(api_main, "_collect_pipeline_orient_data", fake_pipeline)
    monkeypatch.setattr(api_main, "_collect_delegate_orient_data", lambda *a, **k: {})
    monkeypatch.setattr(api_main, "_collect_wiki_orient_data", lambda *a, **k: {"by_track": {}})
    monkeypatch.setattr(
        api_main,
        "_collect_governance_orient_data",
        lambda *a, **k: {
            "decisions_total": 0,
            "decisions_stale": 0,
            "decisions_approaching_expiry": 0,
            "adrs_total": 0,
            "adrs_warnings": 0,
            "adrs_errors": 0,
        },
    )
    monkeypatch.setattr(api_main, "_collect_health_orient_data", lambda *a, **k: {"api": True})
    monkeypatch.setattr(api_main, "_collect_session_hints_orient_data", lambda *a, **k: [])

    # Patch runtime API dependencies
    monkeypatch.setattr(api_main.runtime_api, "list_runtime_agents", lambda *a, **k: [])
    monkeypatch.setattr(api_main.runtime_api, "runtime_recent_outcomes_today", lambda *a, **k: [])


@pytest.fixture(autouse=True)
def setup_teardown(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    context = api_main.resolve_context(None)
    context = replace(context, roots=replace(context.roots, batch_state_dir=tmp_path))
    monkeypatch.setattr(api_main, "resolve_context", lambda ctx=None: context)
    # Reset global GC variables
    api_main._last_gc_sweep_summary = None
    api_main._gc_sweep_thread = None
    state_helpers.cache_invalidate("worktree_gc_sweep")

    # Force ONLY the GC sweep thread to run synchronously in tests
    original_start = threading.Thread.start

    def fake_start(self):
        target = getattr(self, "_target", None)
        if target and getattr(target, "__name__", None) == "_run_worktree_gc_sweep":
            self._target(*self._args, **self._kwargs)
        else:
            original_start(self)

    monkeypatch.setattr(threading.Thread, "start", fake_start)

    yield


def test_gc_sweep_disabled_by_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LEARN_UK_WORKTREE_GC", "0")
    _patch_orient_sources(monkeypatch)

    response = client.get("/api/orient?fresh=true")
    assert response.status_code == 200
    data = response.json()
    assert "worktree_gc" not in data.get("runtime", {})
    assert api_main._last_gc_sweep_summary is None


def test_gc_sweep_runs_and_exposes_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LEARN_UK_WORKTREE_GC", "1")
    _patch_orient_sources(monkeypatch)

    # Mock reap_worktrees to return a controlled set of results
    fake_results = [
        ReapResult(path="/wt/1", branch="b1", action="removed", reason="merged", dirty=False),
        ReapResult(path="/wt/2", branch="b2", action="removed", reason="merged", dirty=False),
        ReapResult(path="/wt/3", branch="b3", action="skipped", reason="dirty", dirty=True),
        ReapResult(path="/wt/4", branch="b4", action="error", reason="fail", dirty=False, error="err"),
        ReapResult(
            path="/wt/5",
            branch="b5",
            action="skipped",
            reason="needs_attention: initializing_leftover; ...",
            dirty=None,
            needs_attention={"kind": "initializing_leftover", "command": "verify first: git ...", "evidence": {}},
        ),
    ]

    monkeypatch.setattr(api_main, "reap_worktrees", lambda **kwargs: fake_results)
    monkeypatch.setattr(api_main, "primary_checkout_root", lambda path: Path("/dummy"))

    response = client.get("/api/orient?fresh=true")
    assert response.status_code == 200
    data = response.json()
    runtime = data["runtime"]
    assert "worktree_gc" in runtime
    summary = runtime["worktree_gc"]
    assert summary["removed"] == 2
    assert summary["skipped"] == 2
    assert summary["errors"] == 1
    # #8663: report-only findings reach the Monitor summary with their command.
    assert summary["needs_attention"] == [
        {"path": "/wt/5", "kind": "initializing_leftover", "command": "verify first: git ..."}
    ]
    assert "time" in summary


def test_gc_sweep_respects_ttl(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LEARN_UK_WORKTREE_GC", "1")
    monkeypatch.setenv("LEARN_UK_WORKTREE_GC_INTERVAL_MIN", "60")
    _patch_orient_sources(monkeypatch)

    # First call returns 1 removed
    monkeypatch.setattr(
        api_main,
        "reap_worktrees",
        lambda **kwargs: [ReapResult(path="/wt/1", branch="b1", action="removed", reason="m", dirty=False)],
    )
    monkeypatch.setattr(api_main, "primary_checkout_root", lambda path: Path("/dummy"))

    response = client.get("/api/orient?fresh=true")
    assert response.json()["runtime"]["worktree_gc"]["removed"] == 1

    # Update return value to 5 removed, but sweep shouldn't run again due to TTL cache
    monkeypatch.setattr(
        api_main,
        "reap_worktrees",
        lambda **kwargs: [
            ReapResult(path=f"/wt/{i}", branch=f"b{i}", action="removed", reason="m", dirty=False) for i in range(5)
        ],
    )
    response2 = client.get("/api/orient")
    assert response2.json()["runtime"]["worktree_gc"]["removed"] == 1

    # Expire persistent state as well as the process cache, then run again
    state_helpers.cache_invalidate("worktree_gc_sweep")
    stamp = api_main.resolve_context(None).roots.batch_state_dir / "worktree-gc-sweep.last-run"
    if stamp.exists():
        os.utime(stamp, (time.time() - 3601, time.time() - 3601))
    response3 = client.get("/api/orient?fresh=true")
    assert response3.json()["runtime"]["worktree_gc"]["removed"] == 5


def test_10593_gc_sweep_restart_honours_persisted_ttl(monkeypatch):
    monkeypatch.setenv("LEARN_UK_WORKTREE_GC", "1")
    monkeypatch.setenv("LEARN_UK_WORKTREE_GC_INTERVAL_MIN", "60")
    calls = []
    monkeypatch.setattr(api_main, "reap_worktrees", lambda **kwargs: calls.append(kwargs) or [])
    api_main._maybe_run_worktree_gc_sweep()
    assert len(calls) == 1
    state_helpers.cache_invalidate("worktree_gc_sweep")
    api_main._gc_sweep_thread = None
    api_main._last_gc_sweep_summary = None
    api_main._maybe_run_worktree_gc_sweep()
    assert len(calls) == 1
    stamp = api_main.resolve_context(None).roots.batch_state_dir / "worktree-gc-sweep.last-run"
    assert stamp.is_file()
    old = time.time() - 3601
    os.utime(stamp, (old, old))
    api_main._maybe_run_worktree_gc_sweep()
    assert len(calls) == 2


@pytest.mark.parametrize("operation", ["open", "utime"])
def test_gc_sweep_persistence_error_does_not_reap(monkeypatch, operation):
    monkeypatch.setenv("LEARN_UK_WORKTREE_GC", "1")
    calls = []
    monkeypatch.setattr(api_main, "reap_worktrees", lambda **kwargs: calls.append(kwargs) or [])
    stamp = api_main.resolve_context(None).roots.batch_state_dir / "worktree-gc-sweep.last-run"
    if operation == "open":
        original = api_main.safe_open_below

        def refused(directory, name, *args, **kwargs):
            if name == stamp.name:
                raise PermissionError("fixture state unavailable")
            return original(directory, name, *args, **kwargs)

        monkeypatch.setattr(api_main, "safe_open_below", refused)
    else:
        original = os.utime

        def refused(path, *args, **kwargs):
            if isinstance(path, int):
                raise PermissionError("fixture state unavailable")
            return original(path, *args, **kwargs)

        monkeypatch.setattr(os, "utime", refused)
    api_main._maybe_run_worktree_gc_sweep()
    assert calls == []
    assert api_main._gc_sweep_thread is None


@pytest.mark.parametrize("entry", ["symlink", "fifo", "hardlink", "directory"])
def test_gc_sweep_refuses_unsafe_timestamp_entry(monkeypatch, entry):
    monkeypatch.setenv("LEARN_UK_WORKTREE_GC", "1")
    monkeypatch.setenv("LEARN_UK_WORKTREE_GC_INTERVAL_MIN", "0")
    root = api_main.resolve_context(None).roots.batch_state_dir
    sentinel = root / "sentinel.txt"
    sentinel.write_bytes(b"preserve these bytes\n")
    stamp = root / "worktree-gc-sweep.last-run"
    if entry == "symlink":
        stamp.symlink_to(sentinel)
    elif entry == "fifo":
        os.mkfifo(stamp)
    elif entry == "hardlink":
        os.link(sentinel, stamp)
    else:
        stamp.mkdir()
    inode = stamp.lstat().st_ino
    modified = sentinel.stat().st_mtime_ns
    calls = []
    monkeypatch.setattr(api_main, "reap_worktrees", lambda **kwargs: calls.append(kwargs) or [])
    api_main._maybe_run_worktree_gc_sweep()
    assert calls == []
    assert sentinel.read_bytes() == b"preserve these bytes\n"
    assert sentinel.stat().st_mtime_ns == modified
    assert stamp.lstat().st_ino == inode
