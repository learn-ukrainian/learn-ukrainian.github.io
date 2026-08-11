from __future__ import annotations

import json
import os
import signal
import subprocess
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.ai_agent_bridge._review_worktree import _hardened_review_signal_handler
from scripts.orchestration import reap_worktrees, scheduled_worktree_cleanup
from scripts.review import isolation
from scripts.review.isolation import (
    REVIEW_TEMP_ROOT_MANIFEST_NAME,
    REVIEW_TEMP_ROOT_MARKER_NAME,
    create_review_temp_root,
    sweep_review_temp_orphans,
)


def test_sweep_reaps_dead_owner_root_immediately(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Guard 1 (Live Owner Fencing / ESRCH): Dead PID root reaped immediately within 60s grace."""
    monkeypatch.setenv("LU_RUNTIME_TMP_BASE_ROOT", str(tmp_path))
    now = 1000.0

    root = create_review_temp_root(prefix="lu-review-snap-", dir=tmp_path)
    manifest_path = root / REVIEW_TEMP_ROOT_MANIFEST_NAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["owner_pid"] = 999999
    manifest["created_at_epoch"] = now - 5.0
    manifest_path.chmod(0o600)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    res = sweep_review_temp_orphans(now=now, min_free_gb=10.0)
    assert res["roots_reaped"] == 1
    assert not root.exists()


def test_sweep_preserves_live_owner_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Guard 1 (Live Owner Fencing): Active owner process root preserved even if age > 48h."""
    monkeypatch.setenv("LU_RUNTIME_TMP_BASE_ROOT", str(tmp_path))
    now = 1000000.0

    root = create_review_temp_root(prefix="lu-review-snap-", dir=tmp_path)
    manifest_path = root / REVIEW_TEMP_ROOT_MANIFEST_NAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["created_at_epoch"] = now - (100 * 3600)  # 100 hours old
    manifest_path.chmod(0o600)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    res = sweep_review_temp_orphans(now=now, min_free_gb=10.0)
    assert res["roots_reaped"] == 0
    assert root.exists()


def test_sweep_reaps_recycled_pid_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Guard 2 (PID Start-Time Match): Recycled PID with mismatched start time is reaped."""
    monkeypatch.setenv("LU_RUNTIME_TMP_BASE_ROOT", str(tmp_path))
    now = 1000.0

    root = create_review_temp_root(prefix="lu-review-snap-", dir=tmp_path)
    manifest_path = root / REVIEW_TEMP_ROOT_MANIFEST_NAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["owner_pid"] = os.getpid()
    manifest["owner_pid_started_at"] = 1.0  # Mismatched start time
    manifest["created_at_epoch"] = now - 100.0
    manifest_path.chmod(0o600)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    res = sweep_review_temp_orphans(now=now, min_free_gb=10.0)
    assert res["roots_reaped"] == 1
    assert not root.exists()


def test_disk_pressure_escalates_sweeper(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Guard 4 (Disk Pressure Escalation): Free space < 10GB lowers unmanifested cutoff to 1h."""
    monkeypatch.setenv("LU_RUNTIME_TMP_BASE_ROOT", str(tmp_path))
    now = 10000.0

    # Unmanifested root (legacy marker only), age 2h
    root = tmp_path / "lu-review-snap-legacy"
    root.mkdir()
    marker = root / REVIEW_TEMP_ROOT_MARKER_NAME
    marker.write_bytes(f"lu-review-root-v1:{'0'*64}\n".encode("ascii"))
    os.utime(root, (now - 7200.0, now - 7200.0))  # 2 hours old

    # Mock free space = 1GB (< 10GB threshold)
    monkeypatch.setattr(isolation, "_is_disk_pressure_active", lambda *args, **kwargs: True)

    res = sweep_review_temp_orphans(now=now, min_free_gb=10.0)
    assert res["disk_pressure"] is True
    assert res["roots_reaped"] == 1
    assert not root.exists()


def test_signal_handler_cleanup(tmp_path: Path) -> None:
    """Guard 5 (Signal Handler Cleanup): Signal handler cleans up registered review roots on SIGTERM."""
    state_mock = MagicMock()
    state_mock.root = tmp_path / "state_root"
    state_mock.root.mkdir()

    root_mock = tmp_path / "lu-review-exec-test"
    root_mock.mkdir()

    cleanup_called = False

    def fake_cleanup(state, roots):
        nonlocal cleanup_called
        cleanup_called = True

    def get_cleanup_args():
        return state_mock, (root_mock,)

    with patch("scripts.ai_agent_bridge._review_worktree._cleanup_review_resources", side_effect=fake_cleanup):
        with pytest.raises(SystemExit) as exc_info:
            with _hardened_review_signal_handler(get_cleanup_args):
                handler = signal.getsignal(signal.SIGTERM)
                handler(signal.SIGTERM, None)

        assert exc_info.value.code == 128 + signal.SIGTERM
        assert cleanup_called is True


def test_fetch_failure_degrades_gracefully(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Guard 6 (Fetch Timeout Degradation): Fetch error degrades to local cleanup without early return."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()

    fake_fetch_proc = subprocess.CompletedProcess(
        args=["git", "fetch"], returncode=128, stdout="", stderr="fatal: fetch timeout"
    )
    monkeypatch.setattr(scheduled_worktree_cleanup, "_run_git", lambda r, *a: fake_fetch_proc)
    monkeypatch.setattr(scheduled_worktree_cleanup, "_worktree_prune", lambda r, apply: {"ok": True})
    monkeypatch.setattr(reap_worktrees, "_live_cwd_paths", lambda r: set())
    monkeypatch.setattr(reap_worktrees, "reap_worktrees", lambda **kw: [])
    monkeypatch.setattr(
        reap_worktrees,
        "adopt_dispatch_worktrees",
        lambda r: (_ for _ in ()).throw(RuntimeError("adoption probe failed")),
    )
    monkeypatch.setattr(reap_worktrees, "find_needs_finalize_worktrees", lambda r: [])
    monkeypatch.setattr(scheduled_worktree_cleanup, "cleanup_gone_local_branches", lambda r, apply: [])
    monkeypatch.setattr(scheduled_worktree_cleanup, "find_orphaned_worktree_directories", lambda r: [])
    monkeypatch.setattr(scheduled_worktree_cleanup, "_git_maintenance", lambda r, apply: {"ok": True})
    monkeypatch.setattr(scheduled_worktree_cleanup, "sweep_review_temp_orphans", lambda: {"roots_reaped": 0})
    monkeypatch.setattr(scheduled_worktree_cleanup, "sweep_tmp_leaks", lambda apply=False: {"roots_reaped": 0, "bytes_freed": 0, "errors": 0, "candidates": 0, "skipped_live": 0})

    res = scheduled_worktree_cleanup._repo_result_unlocked(repo, apply=False)
    assert any("fetch failed" in err for err in res["errors"])
    assert res["adopted"] == []
    assert "adoption skipped: adoption probe failed" in res["errors"]
    assert res["worktree_prune"] is not None
    assert res["maintenance"] is not None


def test_terminal_task_reaped_immediately(tmp_path: Path) -> None:
    """Guard 7 (Terminal Task Reaper): Detached worktree with terminal task status is reaped immediately."""
    repo = tmp_path / "repo"
    repo.mkdir()
    tasks_dir = repo / "batch_state" / "tasks"
    tasks_dir.mkdir(parents=True)

    task_id = "task-123"
    (tasks_dir / f"{task_id}.json").write_text(
        json.dumps({"task_id": task_id, "status": "done"}), encoding="utf-8"
    )

    wt = repo / ".worktrees" / "dispatch" / "lane-1" / "task-123"
    wt.mkdir(parents=True)

    info = reap_worktrees.WorktreeInfo(
        path=wt,
        head="1234567890abcdef1234567890abcdef12345678",
        branch=None,
        detached=True,
    )

    with (
        patch.object(reap_worktrees, "_worktree_clean", return_value=True),
        patch.object(reap_worktrees, "_is_ancestor_of_origin_main", return_value=False),
    ):
        reason = reap_worktrees._qualifying_reason(
            repo_root=repo,
            info=info,
            pr_state=None,
            build_age_hours=24.0,
            now=time.time(),
            active_ids=set(),
            safe_only=False,
            merged_pr_only=False,
        )

    assert reason is not None
    assert "settled dispatch task-id=task-123" in reason


def test_needs_finalize_log_visibility(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Guard 8 (needs_finalize Log): needs_finalize worktrees surfaced in summary receipt."""
    repo = tmp_path / "repo"
    repo.mkdir()

    wt_item = {"path": str(repo / ".worktrees" / "wt-1"), "task_id": "task-456", "branch": None}
    fake_repo_result = {
        "repo_root": str(repo),
        "fetch": {"ok": True},
        "worktree_prune": {"ok": True},
        "activity_probe": {"available": True},
        "results": [],
        "branches": [],
        "maintenance": {"ok": True},
        "orphans": [],
        "errors": [],
        "needs_finalize_worktrees": [wt_item],
    }
    monkeypatch.setattr(scheduled_worktree_cleanup, "_repo_result", lambda path, apply: fake_repo_result)

    receipt = scheduled_worktree_cleanup.build_receipt([repo], apply=False)
    assert "needs_finalize_worktrees" in receipt["summary"]
    assert receipt["summary"]["needs_finalize_worktrees"] == [wt_item]


def test_sweep_preserves_non_esrch_dead_owner_during_grace_window(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Guard 3 / F1 (60s Grace Window for non-ESRCH): Fresh root (<60s) with recycled PID owner is preserved."""
    monkeypatch.setenv("LU_RUNTIME_TMP_BASE_ROOT", str(tmp_path))
    now = 1000.0

    root = create_review_temp_root(prefix="lu-review-snap-", dir=tmp_path)
    manifest_path = root / REVIEW_TEMP_ROOT_MANIFEST_NAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["owner_pid"] = os.getpid()
    manifest["owner_pid_started_at"] = 1.0  # Mismatched start time -> dead, reason=recycled_pid
    manifest["created_at_epoch"] = now - 5.0  # Age = 5.0s < 60.0s grace window
    manifest_path.chmod(0o600)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    # In normal mode (not disk pressure), non-ESRCH dead owner under 60s grace is preserved
    monkeypatch.setattr(isolation, "_is_disk_pressure_active", lambda *args, **kwargs: False)
    res = sweep_review_temp_orphans(now=now, min_free_gb=10.0)
    assert res["roots_reaped"] == 0
    assert root.exists()

    # Under disk pressure, grace is bypassed for all dead owners
    monkeypatch.setattr(isolation, "_is_disk_pressure_active", lambda *args, **kwargs: True)
    res_pressure = sweep_review_temp_orphans(now=now, min_free_gb=10.0)
    assert res_pressure["roots_reaped"] == 1
    assert not root.exists()


def test_sweep_toctou_recheck_skips_on_uncheckable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Guard / F2 (TOCTOU re-check): Sweeper skips if TOCTOU recheck becomes uncheckable."""
    monkeypatch.setenv("LU_RUNTIME_TMP_BASE_ROOT", str(tmp_path))
    now = 1000.0

    root = create_review_temp_root(prefix="lu-review-snap-", dir=tmp_path)
    manifest_path = root / REVIEW_TEMP_ROOT_MANIFEST_NAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["owner_pid"] = 999999
    manifest["created_at_epoch"] = now - 100.0
    manifest_path.chmod(0o600)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    calls = 0

    def mock_eval(man):
        nonlocal calls
        calls += 1
        if calls == 1:
            return "dead", "ESRCH"
        return "uncheckable", "foreign_machine"

    monkeypatch.setattr(isolation, "_evaluate_root_owner_liveness", mock_eval)

    res = sweep_review_temp_orphans(now=now, min_free_gb=10.0)
    assert res["roots_reaped"] == 0
    assert root.exists()


def test_disk_pressure_threshold_reads_yaml_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Guard / F3 (Disk Pressure YAML Config): YAML config threshold is respected."""
    monkeypatch.setattr(
        isolation,
        "_load_hygiene_yaml_min_free_gb",
        lambda: 15.0,
    )

    mock_usage = MagicMock()
    mock_usage.free = 12 * (1024 ** 3)
    monkeypatch.setattr(isolation.shutil, "disk_usage", lambda p: mock_usage)

    assert isolation._is_disk_pressure_active(tmp_path) is True


def test_review_resource_cleanup_is_idempotent(tmp_path: Path) -> None:
    """Guard / F4 (Cleanup Idempotency): Double cleanup invocation raises no error."""
    state_root = create_review_temp_root(prefix="lu-review-snap-", dir=tmp_path)
    state_mock = MagicMock()
    state_mock.root = state_root
    state_mock.cleaned = False

    def fake_cleanup_state(s):
        if not s.cleaned:
            if s.root.exists():
                isolation.remove_review_temp_tree(s.root)
            s.cleaned = True

    root_mock = create_review_temp_root(prefix="lu-review-exec-", dir=tmp_path)

    with patch("scripts.ai_agent_bridge._review_worktree.cleanup_snapshot_state", side_effect=fake_cleanup_state):
        from scripts.ai_agent_bridge._review_worktree import _cleanup_review_resources

        _cleanup_review_resources(state=state_mock, roots=(root_mock,))
        assert not root_mock.exists()
        assert not state_root.exists()

        # Second invocation must be silent and raise no exception
        _cleanup_review_resources(state=state_mock, roots=(root_mock,))


def test_terminal_task_reaped_with_none_active_ids(tmp_path: Path) -> None:
    """Guard / F5 (active_ids=None): Detached worktree with terminal task status reaped when active_ids is None."""
    repo = tmp_path / "repo"
    repo.mkdir()
    tasks_dir = repo / "batch_state" / "tasks"
    tasks_dir.mkdir(parents=True)

    task_id = "task-789"
    (tasks_dir / f"{task_id}.json").write_text(
        json.dumps({"task_id": task_id, "status": "done"}), encoding="utf-8"
    )

    wt = repo / ".worktrees" / "dispatch" / "lane-1" / "task-789"
    wt.mkdir(parents=True)

    info = reap_worktrees.WorktreeInfo(
        path=wt,
        head="1234567890abcdef1234567890abcdef12345678",
        branch=None,
        detached=True,
    )

    with (
        patch.object(reap_worktrees, "_worktree_clean", return_value=True),
        patch.object(reap_worktrees, "_is_ancestor_of_origin_main", return_value=False),
    ):
        reason = reap_worktrees._qualifying_reason(
            repo_root=repo,
            info=info,
            pr_state=None,
            build_age_hours=24.0,
            now=time.time(),
            active_ids=None,
            safe_only=False,
            merged_pr_only=False,
        )

    assert reason is not None
    assert "settled dispatch task-id=task-789" in reason
