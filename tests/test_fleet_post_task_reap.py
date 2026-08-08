"""Hermetic tests for scripts.fleet.post_task_reap.

Tests exercise the hard guards without touching the real checkout:
- never reap while task status is spawning/running
- never reap a dirty worktree
- never reap without binding task state to a registered dispatch worktree
- never reap ACP runtime paths by name/substring; only ``acp_runtime_paths`` in
  task state authorizes reaping
- liveness probe failure is fail-closed (retain) for both main and ACP paths
- default dry-run; --apply required for deletion
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from scripts.fleet import post_task_reap


def _safe_label(task_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", task_id).strip("-._")[:32]


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
    monkeypatch.setattr(post_task_reap, "_probe_path_liveness", lambda _path: False)
    monkeypatch.setattr(post_task_reap.reap_worktrees, "_live_cwd_paths", lambda _repo: set())

    def merged_pr(_repo: Path, branch: str | None):
        if branch is None:
            return [], None
        proc = _run(["git", "rev-parse", f"refs/heads/{branch}"], cwd=repo_root)
        head = (proc.stdout or "").strip() if proc.returncode == 0 else None
        return [post_task_reap.reap_worktrees.PullRequestState(1, "MERGED", head)], None

    monkeypatch.setattr(post_task_reap.reap_worktrees, "_query_pr_states", merged_pr)

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
    label = _safe_label(task_id)
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
    *,
    agent: str = "kimi",
    acp_runtime_paths: list[Path] | None = None,
    pid: int | None = None,
) -> None:
    state: dict[str, Any] = {
        "task_id": task_id,
        "agent": agent,
        "status": status,
    }
    if worktree_path is not None:
        state["worktree_path"] = str(worktree_path)
    if acp_runtime_paths:
        state["acp_runtime_paths"] = [str(p) for p in acp_runtime_paths]
    if pid is not None:
        state["pid"] = pid
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
    assert report["main_worktree"]["reason"] == "PR #1 MERGED"
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


def test_reap_pending_reservation_refuses_bound_task(hermetic_reap):
    repo_root, tasks_dir = hermetic_reap
    worktree = _add_dispatch_worktree(repo_root, "kimi", "pending-task")
    _write_task_state(tasks_dir, "pending-task", "done", worktree)
    post_task_reap.reaper_lifecycle.mark_reap_pending(
        repo_root,
        worktree_path=worktree,
        branch="kimi/pending-task",
        head=_run(["git", "rev-parse", "HEAD"], cwd=worktree).stdout.strip(),
        task_id="pending-task",
    )

    report = post_task_reap.post_task_reap("pending-task", tasks_dir=tasks_dir, repo_root=repo_root, apply=True)

    assert report["main_worktree"]["action"] == "retained"
    assert report["main_worktree"]["reason"] == "reap-pending reservation blocks a new task bind"
    assert worktree.exists()


def test_main_worktree_retain_when_pid_alive(hermetic_reap, monkeypatch):
    repo_root, tasks_dir = hermetic_reap
    worktree = _add_dispatch_worktree(repo_root, "kimi", "pid-alive-task")
    _write_task_state(tasks_dir, "pid-alive-task", "done", worktree, pid=12345)

    monkeypatch.setattr(post_task_reap, "_pid_alive", lambda _pid: True)

    report = post_task_reap.post_task_reap("pid-alive-task", tasks_dir=tasks_dir, repo_root=repo_root, apply=True)

    assert report["main_worktree"]["action"] == "retained"
    assert "live process" in report["main_worktree"]["reason"]
    assert worktree.exists()


def test_main_worktree_retain_when_pid_liveness_fails(hermetic_reap, monkeypatch):
    repo_root, tasks_dir = hermetic_reap
    worktree = _add_dispatch_worktree(repo_root, "kimi", "pid-error-task")
    _write_task_state(tasks_dir, "pid-error-task", "done", worktree, pid=12345)

    monkeypatch.setattr(post_task_reap, "_pid_alive", lambda _pid: None)

    report = post_task_reap.post_task_reap("pid-error-task", tasks_dir=tasks_dir, repo_root=repo_root, apply=True)

    assert report["main_worktree"]["action"] == "retained"
    assert "liveness probe failed" in report["main_worktree"]["reason"]
    assert worktree.exists()

    # MUTATION-CHECK: if the main-worktree liveness check stopped failing closed,
    # an errored probe would have allowed removal.
    monkeypatch.setattr(post_task_reap, "_pid_alive", lambda _pid: False)
    mutated = post_task_reap.post_task_reap("pid-error-task", tasks_dir=tasks_dir, repo_root=repo_root, apply=True)
    assert mutated["main_worktree"]["action"] == "removed"


def test_acp_runtime_reap_when_process_gone(hermetic_reap):
    repo_root, tasks_dir = hermetic_reap
    main_worktree = _add_dispatch_worktree(repo_root, "kimi", "acp-task")
    acp_path = _add_acp_runtime_worktree(repo_root, "acp-task", locked=False)
    _write_task_state(tasks_dir, "acp-task", "done", main_worktree, acp_runtime_paths=[acp_path])

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
    _write_task_state(tasks_dir, "acp-task", "done", main_worktree, acp_runtime_paths=[acp_path])

    # Simulate a live process holding the ACP runtime path.
    monkeypatch.setattr(post_task_reap, "_probe_path_liveness", lambda _path: True)

    report = post_task_reap.post_task_reap("acp-task", tasks_dir=tasks_dir, repo_root=repo_root)

    assert report["main_worktree"]["action"] == "would_remove"
    assert len(report["acp_runtimes"]) == 1
    assert report["acp_runtimes"][0]["action"] == "retained"
    assert "live process" in report["acp_runtimes"][0]["reason"]
    assert acp_path.exists()

    # MUTATION-CHECK: disabling the liveness check turns a live ACP runtime
    # path into a would-remove candidate.  The retain assertion above would fail.
    monkeypatch.setattr(post_task_reap, "_probe_path_liveness", lambda _path: False)
    mutated = post_task_reap.post_task_reap("acp-task", tasks_dir=tasks_dir, repo_root=repo_root)
    assert mutated["acp_runtimes"][0]["action"] == "would_remove"


def test_acp_runtime_retain_liveness_probe_failed(hermetic_reap, monkeypatch):
    repo_root, tasks_dir = hermetic_reap
    main_worktree = _add_dispatch_worktree(repo_root, "kimi", "acp-error-task")
    acp_path = _add_acp_runtime_worktree(repo_root, "acp-error-task", locked=False)
    _write_task_state(tasks_dir, "acp-error-task", "done", main_worktree, acp_runtime_paths=[acp_path])

    # Simulate a liveness probe that errors out instead of returning a result.
    monkeypatch.setattr(post_task_reap, "_probe_path_liveness", lambda _path: None)

    report = post_task_reap.post_task_reap("acp-error-task", tasks_dir=tasks_dir, repo_root=repo_root)

    assert report["main_worktree"]["action"] == "would_remove"
    assert len(report["acp_runtimes"]) == 1
    assert report["acp_runtimes"][0]["action"] == "retained"
    assert "liveness probe failed" in report["acp_runtimes"][0]["reason"]
    assert acp_path.exists()

    # MUTATION-CHECK: fail-closed means an errored probe must retain the path.
    # If the code treated an errored probe as "process gone", this would remove.
    monkeypatch.setattr(post_task_reap, "_probe_path_liveness", lambda _path: False)
    mutated = post_task_reap.post_task_reap("acp-error-task", tasks_dir=tasks_dir, repo_root=repo_root, apply=True)
    assert mutated["acp_runtimes"][0]["action"] == "removed"


def test_acp_runtime_retain_dirty(hermetic_reap):
    repo_root, tasks_dir = hermetic_reap
    main_worktree = _add_dispatch_worktree(repo_root, "kimi", "acp-dirty-task")
    acp_path = _add_acp_runtime_worktree(repo_root, "acp-dirty-task", locked=False)
    (acp_path / "dirt.txt").write_text("dirt", encoding="utf-8")
    _write_task_state(tasks_dir, "acp-dirty-task", "done", main_worktree, acp_runtime_paths=[acp_path])

    report = post_task_reap.post_task_reap("acp-dirty-task", tasks_dir=tasks_dir, repo_root=repo_root, apply=True)

    assert report["main_worktree"]["action"] == "removed"
    assert len(report["acp_runtimes"]) == 1
    assert report["acp_runtimes"][0]["action"] == "retained"
    assert "uncommitted changes" in report["acp_runtimes"][0]["reason"]
    assert acp_path.exists()


def test_acp_runtime_retain_unbound_name(hermetic_reap):
    """An ACP path whose name happens to contain the task label is not enough."""
    repo_root, tasks_dir = hermetic_reap
    main_worktree = _add_dispatch_worktree(repo_root, "kimi", "acp-unbound-task")
    # Path that the old name-matching logic would have claimed.
    acp_path = repo_root / ".worktrees" / "dispatch" / "acp" / "runtime-review-acp-unbound-task-12345"
    acp_path.parent.mkdir(parents=True, exist_ok=True)
    _run(
        ["git", "worktree", "add", "--detach", "--no-checkout", str(acp_path), "HEAD"],
        cwd=repo_root,
    )
    _write_task_state(tasks_dir, "acp-unbound-task", "done", main_worktree)

    report = post_task_reap.post_task_reap("acp-unbound-task", tasks_dir=tasks_dir, repo_root=repo_root, apply=True)

    assert report["main_worktree"]["action"] == "removed"
    assert report["acp_runtimes"] == []
    assert acp_path.exists()


def test_acp_runtime_retain_unregistered(hermetic_reap):
    repo_root, tasks_dir = hermetic_reap
    main_worktree = _add_dispatch_worktree(repo_root, "kimi", "acp-unreg-task")
    bogus_acp = repo_root / ".worktrees" / "dispatch" / "acp" / "runtime-acp-unreg-task-bogus"
    bogus_acp.mkdir(parents=True)
    _write_task_state(tasks_dir, "acp-unreg-task", "done", main_worktree, acp_runtime_paths=[bogus_acp])

    report = post_task_reap.post_task_reap("acp-unreg-task", tasks_dir=tasks_dir, repo_root=repo_root, apply=True)

    assert report["main_worktree"]["action"] == "removed"
    assert len(report["acp_runtimes"]) == 1
    assert report["acp_runtimes"][0]["action"] == "retained"
    assert "not a registered git worktree" in report["acp_runtimes"][0]["reason"]
    assert bogus_acp.exists()


def test_acp_runtime_retain_while_task_active(hermetic_reap):
    repo_root, tasks_dir = hermetic_reap
    main_worktree = _add_dispatch_worktree(repo_root, "kimi", "acp-active-task")
    acp_path = _add_acp_runtime_worktree(repo_root, "acp-active-task", locked=False)
    _write_task_state(tasks_dir, "acp-active-task", "running", main_worktree, acp_runtime_paths=[acp_path])

    report = post_task_reap.post_task_reap("acp-active-task", tasks_dir=tasks_dir, repo_root=repo_root)

    # Main worktree retained because task is active; ACP runtimes are not even
    # evaluated while the task is active.
    assert report["main_worktree"]["action"] == "retained"
    assert report["acp_runtimes"] == []
    assert acp_path.exists()


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
    _write_task_state(tasks_dir, "no-acp-task", "done", main_worktree, acp_runtime_paths=[acp_path])

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
