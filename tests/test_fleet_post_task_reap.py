"""Hermetic tests for scripts.fleet.post_task_reap.

Tests exercise the hard guards without touching the real checkout:
- never reap while task status is spawning/running
- never reap a dirty worktree
- never reap without binding task state to a registered dispatch worktree
- never reap ACP runtime-review paths by prefix alone (process must be gone)
- default dry-run; --apply required for deletion
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from scripts.fleet import post_task_reap


@pytest.fixture
def hermetic_reap(monkeypatch, tmp_path):
    """Redirect post_task_reap to a fresh git repo and task directory."""
    repo_root = tmp_path / "repo"
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir(parents=True)

    monkeypatch.setattr(post_task_reap, "ROOT", repo_root)
    monkeypatch.setattr(post_task_reap, "_TASKS_DIR", tasks_dir)
    monkeypatch.setattr(post_task_reap, "_DISPATCH_WORKTREES_ROOT", repo_root / ".worktrees" / "dispatch")
    monkeypatch.setattr(post_task_reap, "_ACP_RUNTIME_ROOT", repo_root / ".worktrees" / "dispatch" / "acp")

    _init_repo(repo_root)

    # Tests control process liveness so we stay independent of lsof availability.
    monkeypatch.setattr(post_task_reap, "_is_path_held_by_process", lambda _path: False)

    return repo_root, tasks_dir


def _run(args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=check,
    )


def _init_repo(repo_root: Path) -> None:
    repo_root.mkdir(parents=True)
    _run(["git", "init"], cwd=repo_root)
    _run(["git", "config", "user.email", "test@example.com"], cwd=repo_root)
    _run(["git", "config", "user.name", "Test User"], cwd=repo_root)
    (repo_root / "README.md").write_text("# test\n", encoding="utf-8")
    _run(["git", "add", "README.md"], cwd=repo_root)
    _run(["git", "commit", "-m", "initial"], cwd=repo_root)


def _add_dispatch_worktree(repo_root: Path, agent: str, task_id: str) -> Path:
    branch = f"{agent}/{task_id}"
    _run(["git", "branch", branch], cwd=repo_root)
    path = repo_root / ".worktrees" / "dispatch" / agent / task_id
    path.parent.mkdir(parents=True, exist_ok=True)
    _run(["git", "worktree", "add", str(path), branch], cwd=repo_root)
    return path


def _add_external_worktree(repo_root: Path, name: str) -> Path:
    branch = f"external/{name}"
    _run(["git", "branch", branch], cwd=repo_root)
    path = repo_root / ".worktrees" / name
    path.mkdir(parents=True, exist_ok=True)
    _run(["git", "worktree", "add", str(path), branch], cwd=repo_root)
    return path


def _add_acp_runtime_worktree(repo_root: Path, task_id: str, locked: bool = False) -> Path:
    label = post_task_reap._safe_label(task_id)
    path = repo_root / ".worktrees" / "dispatch" / "acp" / f"runtime-{label}-deadbeef"
    path.parent.mkdir(parents=True, exist_ok=True)
    _run(
        ["git", "worktree", "add", "--detach", "--no-checkout", str(path), "HEAD"],
        cwd=repo_root,
    )
    if locked:
        _run(
            ["git", "worktree", "lock", "--reason", f"active ACP execution {label}", str(path)],
            cwd=repo_root,
        )
    return path


def _write_task_state(
    tasks_dir: Path,
    task_id: str,
    status: str,
    worktree_path: Path | None,
    agent: str = "kimi",
) -> None:
    state: dict[str, Any] = {
        "task_id": task_id,
        "agent": agent,
        "status": status,
    }
    if worktree_path is not None:
        state["worktree_path"] = str(worktree_path)
    safe = task_id.replace("/", "_").replace("\\", "_")
    (tasks_dir / f"{safe}.json").write_text(json.dumps(state), encoding="utf-8")


def test_no_task_state(hermetic_reap):
    repo_root, tasks_dir = hermetic_reap
    report = post_task_reap.post_task_reap("missing-task", tasks_dir=tasks_dir, repo_root=repo_root)

    assert report["task_status"] is None
    assert report["main_worktree"]["action"] == "retained"
    assert "no task state" in report["main_worktree"]["reason"]


def test_running_skip(hermetic_reap):
    repo_root, tasks_dir = hermetic_reap
    worktree = _add_dispatch_worktree(repo_root, "kimi", "running-task")
    _write_task_state(tasks_dir, "running-task", "running", worktree)

    report = post_task_reap.post_task_reap("running-task", tasks_dir=tasks_dir, repo_root=repo_root)

    assert report["task_status"] == "running"
    assert report["main_worktree"]["action"] == "retained"
    assert "still active" in report["main_worktree"]["reason"]
    assert worktree.exists()


def test_spawning_skip(hermetic_reap):
    repo_root, tasks_dir = hermetic_reap
    worktree = _add_dispatch_worktree(repo_root, "kimi", "spawning-task")
    _write_task_state(tasks_dir, "spawning-task", "spawning", worktree)

    report = post_task_reap.post_task_reap("spawning-task", tasks_dir=tasks_dir, repo_root=repo_root)

    assert report["main_worktree"]["action"] == "retained"
    assert "still active" in report["main_worktree"]["reason"]
    assert worktree.exists()


def test_dirty_skip(hermetic_reap):
    repo_root, tasks_dir = hermetic_reap
    worktree = _add_dispatch_worktree(repo_root, "kimi", "dirty-task")
    _write_task_state(tasks_dir, "dirty-task", "done", worktree)
    (worktree / "new_file.txt").write_text("dirty", encoding="utf-8")

    report = post_task_reap.post_task_reap("dirty-task", tasks_dir=tasks_dir, repo_root=repo_root)

    assert report["main_worktree"]["action"] == "retained"
    assert "uncommitted changes" in report["main_worktree"]["reason"]
    assert worktree.exists()


def test_clean_terminal_reap_dry_run(hermetic_reap):
    repo_root, tasks_dir = hermetic_reap
    worktree = _add_dispatch_worktree(repo_root, "kimi", "clean-task")
    _write_task_state(tasks_dir, "clean-task", "done", worktree)

    report = post_task_reap.post_task_reap("clean-task", tasks_dir=tasks_dir, repo_root=repo_root)

    assert report["main_worktree"]["action"] == "would_remove"
    assert "terminal" in report["main_worktree"]["reason"]
    assert worktree.exists()


def test_clean_terminal_reap_apply(hermetic_reap):
    repo_root, tasks_dir = hermetic_reap
    worktree = _add_dispatch_worktree(repo_root, "kimi", "clean-task")
    _write_task_state(tasks_dir, "clean-task", "done", worktree)

    report = post_task_reap.post_task_reap("clean-task", tasks_dir=tasks_dir, repo_root=repo_root, apply=True)

    assert report["main_worktree"]["action"] == "removed"
    assert report["main_worktree"]["error"] is None
    assert not worktree.exists()


def test_terminal_failed_reap_apply(hermetic_reap):
    repo_root, tasks_dir = hermetic_reap
    worktree = _add_dispatch_worktree(repo_root, "kimi", "failed-task")
    _write_task_state(tasks_dir, "failed-task", "failed", worktree)

    report = post_task_reap.post_task_reap("failed-task", tasks_dir=tasks_dir, repo_root=repo_root, apply=True)

    assert report["main_worktree"]["action"] == "removed"
    assert not worktree.exists()


def test_ambiguous_retain_no_state_path(hermetic_reap):
    repo_root, tasks_dir = hermetic_reap
    worktree = _add_dispatch_worktree(repo_root, "kimi", "ambiguous-task")
    _write_task_state(tasks_dir, "ambiguous-task", "done", worktree_path=None)

    report = post_task_reap.post_task_reap("ambiguous-task", tasks_dir=tasks_dir, repo_root=repo_root)

    assert report["main_worktree"]["action"] == "retained"
    assert "unknown ownership" in report["main_worktree"]["reason"]
    assert worktree.exists()


def test_ambiguous_retain_outside_dispatch(hermetic_reap):
    repo_root, tasks_dir = hermetic_reap
    external = _add_external_worktree(repo_root, "external-task")
    _write_task_state(tasks_dir, "external-task", "done", external)

    report = post_task_reap.post_task_reap("external-task", tasks_dir=tasks_dir, repo_root=repo_root)

    assert report["main_worktree"]["action"] == "retained"
    assert "outside .worktrees/dispatch" in report["main_worktree"]["reason"]
    assert external.exists()


def test_ambiguous_retain_unregistered_directory(hermetic_reap):
    repo_root, tasks_dir = hermetic_reap
    bogus = repo_root / ".worktrees" / "dispatch" / "kimi" / "bogus-task"
    bogus.mkdir(parents=True)
    _write_task_state(tasks_dir, "bogus-task", "done", bogus)

    report = post_task_reap.post_task_reap("bogus-task", tasks_dir=tasks_dir, repo_root=repo_root)

    assert report["main_worktree"]["action"] == "retained"
    assert "not a registered git worktree" in report["main_worktree"]["reason"]
    assert bogus.exists()


def test_acp_runtime_reap_when_process_gone(hermetic_reap):
    repo_root, tasks_dir = hermetic_reap
    main_worktree = _add_dispatch_worktree(repo_root, "kimi", "acp-task")
    acp_path = _add_acp_runtime_worktree(repo_root, "acp-task", locked=False)
    _write_task_state(tasks_dir, "acp-task", "done", main_worktree)

    report = post_task_reap.post_task_reap("acp-task", tasks_dir=tasks_dir, repo_root=repo_root, apply=True)

    assert report["main_worktree"]["action"] == "removed"
    assert len(report["acp_runtimes"]) == 1
    assert report["acp_runtimes"][0]["action"] == "removed"
    assert report["acp_runtimes"][0]["path"] == str(acp_path)
    assert not acp_path.exists()


def test_acp_runtime_retain_while_process_alive(hermetic_reap, monkeypatch):
    repo_root, tasks_dir = hermetic_reap
    main_worktree = _add_dispatch_worktree(repo_root, "kimi", "acp-task")
    acp_path = _add_acp_runtime_worktree(repo_root, "acp-task", locked=False)
    _write_task_state(tasks_dir, "acp-task", "done", main_worktree)

    # Simulate a live process holding the ACP runtime path.
    monkeypatch.setattr(post_task_reap, "_is_path_held_by_process", lambda _path: True)

    report = post_task_reap.post_task_reap("acp-task", tasks_dir=tasks_dir, repo_root=repo_root)

    assert report["main_worktree"]["action"] == "would_remove"
    assert len(report["acp_runtimes"]) == 1
    assert report["acp_runtimes"][0]["action"] == "retained"
    assert "live process" in report["acp_runtimes"][0]["reason"]
    assert acp_path.exists()

    # MUTATION-CHECK: disabling the liveness check turns a live ACP runtime
    # path into a would-remove candidate.  The retain assertion above would fail.
    monkeypatch.setattr(post_task_reap, "_is_path_held_by_process", lambda _path: False)
    mutated = post_task_reap.post_task_reap("acp-task", tasks_dir=tasks_dir, repo_root=repo_root)
    assert mutated["acp_runtimes"][0]["action"] == "would_remove"


def test_acp_runtime_retain_while_task_active(hermetic_reap):
    repo_root, tasks_dir = hermetic_reap
    main_worktree = _add_dispatch_worktree(repo_root, "kimi", "acp-active-task")
    acp_path = _add_acp_runtime_worktree(repo_root, "acp-active-task", locked=False)
    _write_task_state(tasks_dir, "acp-active-task", "running", main_worktree)

    report = post_task_reap.post_task_reap("acp-active-task", tasks_dir=tasks_dir, repo_root=repo_root)

    # Main worktree retained because task is active; ACP runtimes are not even
    # evaluated while the task is active.
    assert report["main_worktree"]["action"] == "retained"
    assert report["acp_runtimes"] == []
    assert acp_path.exists()


def test_acp_runtime_retain_unregistered(hermetic_reap):
    repo_root, tasks_dir = hermetic_reap
    main_worktree = _add_dispatch_worktree(repo_root, "kimi", "acp-unreg-task")
    bogus_acp = repo_root / ".worktrees" / "dispatch" / "acp" / "runtime-acp-unreg-task-bogus"
    bogus_acp.mkdir(parents=True)
    _write_task_state(tasks_dir, "acp-unreg-task", "done", main_worktree)

    report = post_task_reap.post_task_reap("acp-unreg-task", tasks_dir=tasks_dir, repo_root=repo_root, apply=True)

    assert report["main_worktree"]["action"] == "removed"
    assert len(report["acp_runtimes"]) == 1
    assert report["acp_runtimes"][0]["action"] == "retained"
    assert "not a registered git worktree" in report["acp_runtimes"][0]["reason"]
    assert bogus_acp.exists()


def test_cli_dry_run_default(hermetic_reap, capsys):
    repo_root, tasks_dir = hermetic_reap
    worktree = _add_dispatch_worktree(repo_root, "kimi", "cli-task")
    _write_task_state(tasks_dir, "cli-task", "done", worktree)

    code = post_task_reap.main(["--task-id", "cli-task", "--tasks-dir", str(tasks_dir), "--repo-root", str(repo_root)])
    captured = capsys.readouterr()

    assert code == 0
    report = json.loads(captured.out)
    assert report["main_worktree"]["action"] == "would_remove"
    assert worktree.exists()


def test_cli_apply_flag(hermetic_reap, capsys):
    repo_root, tasks_dir = hermetic_reap
    worktree = _add_dispatch_worktree(repo_root, "kimi", "cli-apply-task")
    _write_task_state(tasks_dir, "cli-apply-task", "done", worktree)

    code = post_task_reap.main(
        [
            "--task-id",
            "cli-apply-task",
            "--tasks-dir",
            str(tasks_dir),
            "--repo-root",
            str(repo_root),
            "--apply",
        ]
    )
    captured = capsys.readouterr()

    assert code == 0
    report = json.loads(captured.out)
    assert report["main_worktree"]["action"] == "removed"
    assert not worktree.exists()


def test_cli_no_acp_runtime(hermetic_reap, capsys):
    repo_root, tasks_dir = hermetic_reap
    main_worktree = _add_dispatch_worktree(repo_root, "kimi", "no-acp-task")
    acp_path = _add_acp_runtime_worktree(repo_root, "no-acp-task", locked=False)
    _write_task_state(tasks_dir, "no-acp-task", "done", main_worktree)

    code = post_task_reap.main(
        [
            "--task-id",
            "no-acp-task",
            "--tasks-dir",
            str(tasks_dir),
            "--repo-root",
            str(repo_root),
            "--apply",
            "--no-include-acp-runtime",
        ]
    )
    captured = capsys.readouterr()

    assert code == 0
    report = json.loads(captured.out)
    assert report["main_worktree"]["action"] == "removed"
    assert report["acp_runtimes"] == []
    assert acp_path.exists()
