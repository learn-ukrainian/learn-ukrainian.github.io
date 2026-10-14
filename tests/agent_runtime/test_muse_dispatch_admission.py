"""Held Muse dispatch refuses before task, worktree or process creation (#10511)."""

import pytest

from scripts import delegate
from scripts.orchestration import job_host_exec


@pytest.fixture
def tasks_dir(tmp_path, monkeypatch):
    tasks = tmp_path / "tasks"
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(tmp_path / "scratch"))
    for name in (
        "_resolve_dirty_primary_checkout_error",
        "_resolve_primary_integrity_error",
    ):
        monkeypatch.setattr(delegate, name, lambda **_kwargs: None)
    for name in (
        "_warn_node_modules_integrity",
        "_warn_venv_integrity",
        "_warn_worktree_cleanup_integrity",
        "_warn_if_monitor_api_unreachable",
    ):
        monkeypatch.setattr(delegate, name, lambda: None)
    monkeypatch.setattr(
        delegate,
        "_sweep_runtime_tmp_orphans",
        lambda: {"leases_reaped": 0, "bytes_freed": 0, "errors": 0, "error_details": []},
    )
    monkeypatch.setattr(job_host_exec, "decide_dispatch_placement", lambda **_kwargs: ("local", "test", None))
    return tasks


@pytest.mark.parametrize("mode", ["read-only", "workspace-write", "danger"])
@pytest.mark.parametrize("model", ["muse-wonder-1.0", "muse-wonder-full-1.0", "gpt-6.1-sol", "claude-opus-5-5"])
def test_held_muse_dispatch_creates_no_worktree_or_task(tasks_dir, tmp_path, monkeypatch, capsys, mode, model):
    from tests.helpers.dispatch_checkout import isolate_dispatch_repo

    repo = isolate_dispatch_repo(monkeypatch, tmp_path, delegate)
    monkeypatch.delenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", raising=False)
    monkeypatch.setattr(delegate, "_check_open_pr_freeze", lambda *_args: None)
    worktree_root = repo / ".worktrees"

    def forbidden(*_args, **_kwargs):
        pytest.fail("held Muse dispatch reached a write or process boundary")

    monkeypatch.setattr(delegate, "_write_state_atomic", forbidden)
    monkeypatch.setattr(delegate, "_ensure_worktree", forbidden)
    monkeypatch.setattr(delegate.subprocess, "Popen", forbidden)
    args = delegate.build_parser().parse_args(
        [
            "dispatch",
            "--agent",
            "muse",
            "--model",
            model,
            "--mode",
            mode,
            "--task-id",
            "held-muse-probe",
            "--initiator",
            "codex",
            "--prompt",
            "no-op",
            "--worktree",
            "--owned-path",
            "scripts/example.py",
        ]
    )
    assert delegate.cmd_dispatch(args) == 2
    assert "MUSE_GUARD_PARITY_UNPROVEN" in capsys.readouterr().err
    assert not worktree_root.exists()
    assert not tasks_dir.exists()
