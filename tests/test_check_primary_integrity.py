"""Tests for the primary-checkout integrity watchdog.

scripts/audit/check_primary_integrity.py — #5803 follow-up: detection +
CONSERVATIVE repair of primary-checkout drift. The repair gate is the whole
point: repair ONLY when detached + clean + idle + no running dispatch + main
stable; alert and preserve evidence (never touch) otherwise.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from audit.check_primary_integrity import (
    check_primary_integrity,
    main,
    worktree_origin_points_at_remote,
)

_GIT_REDIRECT = frozenset(
    {
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_COMMON_DIR",
        "GIT_PREFIX",
    }
)


def _clean_env() -> dict[str, str]:
    """Drop git redirect env so fixtures are not the outer commit hook repo."""
    return {k: v for k, v in os.environ.items() if k not in _GIT_REDIRECT}


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=check,
        env=_clean_env(),
        timeout=30,
    )


def _init_repo(path: Path) -> Path:
    subprocess.run(
        ["git", "init", "-q", "-b", "main", str(path)],
        check=True,
        env=_clean_env(),
        timeout=30,
    )
    _git(path, "config", "user.email", "watchdog-test@example.com")
    _git(path, "config", "user.name", "watchdog-test")
    (path / "README.md").write_text("fixture\n")
    _git(path, "add", "README.md")
    _git(path, "commit", "-q", "-m", "init")
    return path


def _detach(repo: Path) -> str:
    sha = _git(repo, "rev-parse", "HEAD").stdout.strip()
    _git(repo, "checkout", "-q", "--detach", "HEAD")
    return sha


def _head_symbolic_target(repo: Path) -> str | None:
    proc = _git(repo, "symbolic-ref", "-q", "HEAD", check=False)
    return proc.stdout.strip() if proc.returncode == 0 else None


def _events(state_dir: Path) -> list[dict]:
    path = state_dir / "events.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _check(repo: Path, tmp_path: Path, *, fix: bool = False, tasks_dir: Path | None = None):
    return check_primary_integrity(
        repo,
        fix=fix,
        tasks_dir=tasks_dir if tasks_dir is not None else (tmp_path / "no-tasks"),
        state_dir=tmp_path / "watchdog-state",
    )


# ---------------------------------------------------------------------------
# healthy cases
# ---------------------------------------------------------------------------


def test_ok_when_primary_on_main(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    ok, message = _check(repo, tmp_path)
    assert ok is True
    assert "main" in message


def test_wrong_branch_alerts_without_touching(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    _git(repo, "checkout", "-q", "-b", "feature-x")
    ok, message = _check(repo, tmp_path, fix=True)
    assert ok is False
    assert "feature-x" in message
    # Untouched: still on the wrong branch.
    assert _head_symbolic_target(repo) == "refs/heads/feature-x"


def test_check_from_linked_worktree_targets_primary(tmp_path):
    """Invoked with a linked-worktree path, the watchdog must check the
    PRIMARY — a worktree's .git is a file, not a directory, and must never be
    mistaken for the primary checkout."""
    repo = _init_repo(tmp_path / "repo")
    worktree = tmp_path / "linked"
    _git(repo, "worktree", "add", "-q", "-b", "agent/task-x", str(worktree))

    ok, message = _check(worktree, tmp_path)
    assert ok is True
    assert str(repo) in message  # primary root, not the worktree

    # Detach the PRIMARY; checking via the worktree path must see it.
    _detach(repo)
    ok, _message = _check(worktree, tmp_path, fix=True)
    assert ok is False
    assert _head_symbolic_target(repo) is None


# ---------------------------------------------------------------------------
# repair gate: detached + clean + idle → repaired (after stable-main pass)
# ---------------------------------------------------------------------------


def test_detached_clean_idle_is_repaired(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    _detach(repo)

    # First sighting records the main-movement baseline — no repair yet.
    ok, message = _check(repo, tmp_path, fix=True)
    assert ok is False
    assert "baseline" in message
    assert _head_symbolic_target(repo) is None  # still detached

    # Second pass: main observed stable → conservative repair.
    ok, message = _check(repo, tmp_path, fix=True)
    assert ok is True
    assert "repaired" in message
    assert _head_symbolic_target(repo) == "refs/heads/main"

    # Repair event logged with actor-identification context.
    repaired = [e for e in _events(tmp_path / "watchdog-state") if e["event"] == "primary_drift_repaired"]
    assert repaired, "repair must be logged"
    assert repaired[0]["head_sha"]
    assert repaired[0]["reflog"]


def test_detached_clean_idle_no_fix_reports_repairable(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    _detach(repo)
    _check(repo, tmp_path)  # baseline pass
    ok, message = _check(repo, tmp_path, fix=False)
    assert ok is False
    assert "repairable" in message
    assert _head_symbolic_target(repo) is None


def test_detached_at_older_commit_repaired_via_checkout(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    first_sha = _git(repo, "rev-parse", "HEAD").stdout.strip()
    (repo / "README.md").write_text("fixture v2\n")
    _git(repo, "commit", "-qam", "second")
    _git(repo, "checkout", "-q", first_sha)  # detached at older commit, clean

    _check(repo, tmp_path, fix=True)  # baseline
    ok, _message = _check(repo, tmp_path, fix=True)
    assert ok is True
    assert _head_symbolic_target(repo) == "refs/heads/main"
    # Working tree moved to main's tip without losing anything.
    assert (repo / "README.md").read_text() == "fixture v2\n"


# ---------------------------------------------------------------------------
# alert-only cases: NEVER touched
# ---------------------------------------------------------------------------


def test_detached_dirty_tree_not_touched(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    _detach(repo)
    (repo / "README.md").write_text("human work in progress\n")

    ok, message = _check(repo, tmp_path, fix=True)
    assert ok is False
    assert "DIRTY" in message
    assert _head_symbolic_target(repo) is None  # still detached
    assert (repo / "README.md").read_text() == "human work in progress\n"

    # Evidence preserved: alert event carries the dirty entries + reflog.
    alerts = [e for e in _events(tmp_path / "watchdog-state") if e["event"] == "primary_drift_alert"]
    assert alerts
    assert any("README.md" in entry for entry in alerts[0]["dirty_entries"])
    assert alerts[0]["reflog"]


def test_detached_untracked_file_counts_as_dirty(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    _detach(repo)
    (repo / "stray.txt").write_text("untracked\n")
    ok, _message = _check(repo, tmp_path, fix=True)
    assert ok is False
    assert _head_symbolic_target(repo) is None


def test_operation_in_progress_not_touched(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    _detach(repo)
    (repo / ".git" / "MERGE_HEAD").write_text("deadbeef\n")
    ok, message = _check(repo, tmp_path, fix=True)
    assert ok is False
    assert "MERGE_HEAD" in message
    assert _head_symbolic_target(repo) is None


def test_index_lock_not_touched(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    _detach(repo)
    (repo / ".git" / "index.lock").write_text("")
    ok, message = _check(repo, tmp_path, fix=True)
    assert ok is False
    assert "index.lock" in message
    assert _head_symbolic_target(repo) is None


def test_rebase_state_dir_not_touched(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    _detach(repo)
    (repo / ".git" / "rebase-merge").mkdir()
    ok, _message = _check(repo, tmp_path, fix=True)
    assert ok is False
    assert _head_symbolic_target(repo) is None


def test_main_moved_unexpectedly_not_touched(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    _detach(repo)

    ok, _ = _check(repo, tmp_path, fix=True)  # baseline recorded
    assert ok is False

    # main moves while HEAD is detached — unexpected primary-side activity.
    (repo / "mover.txt").write_text("moved\n")
    _git(repo, "add", "mover.txt")
    _git(repo, "commit", "-qm", "mover commit")  # commits on detached HEAD
    _git(repo, "update-ref", "refs/heads/main", "HEAD")
    _git(repo, "reset", "-q", "--hard", "HEAD~1")  # back to clean detached state

    ok, message = _check(repo, tmp_path, fix=True)
    assert ok is False
    assert "main moved unexpectedly" in message
    assert _head_symbolic_target(repo) is None


# ---------------------------------------------------------------------------
# running-dispatch gate: repair deferred, dispatch never killed
# ---------------------------------------------------------------------------


def test_running_dispatch_defers_repair(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    _detach(repo)
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    (tasks_dir / "codex-live-task.json").write_text(
        json.dumps(
            {
                "task_id": "codex/live-task",
                "agent": "codex",
                "status": "running",
                "pid": os.getpid(),  # this test process is alive
            }
        )
    )

    ok, message = _check(repo, tmp_path, fix=True, tasks_dir=tasks_dir)
    assert ok is False
    assert "deferred" in message
    assert "live-task" in message
    assert _head_symbolic_target(repo) is None  # NOT touched


def test_dead_dispatch_pid_does_not_block_repair(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    _detach(repo)
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    (tasks_dir / "zombie.json").write_text(
        json.dumps({"task_id": "zombie", "status": "running", "pid": 2**22})
    )

    _check(repo, tmp_path, fix=True, tasks_dir=tasks_dir)  # baseline
    ok, message = _check(repo, tmp_path, fix=True, tasks_dir=tasks_dir)
    assert ok is True, message
    assert _head_symbolic_target(repo) == "refs/heads/main"


def test_detection_event_names_running_dispatches(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    _detach(repo)
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    (tasks_dir / "gemini-suspect.json").write_text(
        json.dumps(
            {
                "task_id": "gemini/suspect",
                "agent": "gemini",
                "status": "running",
                "pid": os.getpid(),
            }
        )
    )
    _check(repo, tmp_path, fix=True, tasks_dir=tasks_dir)
    detected = [e for e in _events(tmp_path / "watchdog-state") if e["event"] == "primary_drift_detected"]
    assert detected
    running = detected[0]["running_dispatches"]
    assert any(d["task_id"] == "gemini/suspect" for d in running)


# ---------------------------------------------------------------------------
# worktree origin verification (#5803 root cause: origin must be the REMOTE)
# ---------------------------------------------------------------------------


def test_worktree_origin_points_at_remote(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    _git(repo, "remote", "add", "origin", "git@github.com:learn-ukrainian/learn-ukrainian.github.io.git")
    worktree = tmp_path / "linked"
    _git(repo, "worktree", "add", "-q", "-b", "agent/task", str(worktree))

    ok, message = worktree_origin_points_at_remote(worktree)
    assert ok is True
    assert message == "origin → git@github.com:learn-ukrainian/learn-ukrainian.github.io.git"


def test_worktree_origin_local_path_is_flagged(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    _git(repo, "remote", "add", "origin", str(repo))  # local FS path = the bug
    worktree = tmp_path / "linked"
    _git(repo, "worktree", "add", "-q", "-b", "agent/task2", str(worktree))

    ok, message = worktree_origin_points_at_remote(worktree)
    assert ok is False
    assert "LOCAL path" in message


def test_worktree_origin_missing_is_flagged(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    ok, message = worktree_origin_points_at_remote(repo)
    assert ok is False
    assert "not set" in message


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def test_cli_exit_codes(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    state_dir = tmp_path / "cli-state"
    tasks_dir = tmp_path / "no-tasks"

    assert main(["--repo", str(repo), "--state-dir", str(state_dir), "--tasks-dir", str(tasks_dir)]) == 0

    _detach(repo)
    argv = ["--repo", str(repo), "--state-dir", str(state_dir), "--tasks-dir", str(tasks_dir)]
    assert main(argv) == 1  # drift, no --fix (baseline recorded)
    assert main([*argv, "--fix"]) == 0  # stable-main pass repairs
    assert _head_symbolic_target(repo) == "refs/heads/main"
