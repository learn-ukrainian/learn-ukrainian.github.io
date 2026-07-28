from __future__ import annotations

import json
import os
import subprocess
from dataclasses import replace
from pathlib import Path

from scripts.orchestration import scheduled_worktree_cleanup as cleanup


def _git(cwd: Path, *args: str) -> str:
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_")
        and not key.startswith("PRE_COMMIT")
        and key != "AGENT_NO_MERGE"
    }
    proc = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )
    return proc.stdout.strip()


def _repo(tmp_path: Path) -> Path:
    remote = tmp_path / "origin.git"
    repo = tmp_path / "repo"
    _git(tmp_path, "init", "--bare", str(remote))
    _git(tmp_path, "init", "--initial-branch=main", str(repo))
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "Test User")
    (repo / ".gitignore").write_text(".worktrees/\n", encoding="utf-8")
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "base")
    _git(repo, "remote", "add", "origin", str(remote))
    _git(repo, "push", "-u", "origin", "main")
    return repo


def test_apply_fails_closed_without_process_probe(tmp_path: Path, monkeypatch) -> None:
    repo = _repo(tmp_path)
    monkeypatch.setattr(cleanup.reap_worktrees, "_live_cwd_paths", lambda _repo: None)

    result = cleanup._repo_result(repo, apply=True)

    assert result["activity_probe"] == {"available": False, "cwd_count": 0}
    assert result["errors"] == ["process-CWD activity probe unavailable; apply skipped"]
    assert result["results"] == []


def test_orphaned_broken_gitdir_is_reported_not_deleted(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    orphan = repo / ".worktrees" / "dispatch" / "codex" / "orphan"
    orphan.mkdir(parents=True)
    missing = tmp_path / "missing.git" / "worktrees" / "orphan"
    (orphan / ".git").write_text(f"gitdir: {missing}\n", encoding="utf-8")
    (orphan / "recover-me.txt").write_text("local work\n", encoding="utf-8")

    result = cleanup.find_orphaned_worktree_directories(repo)

    assert result == [
        {
            "path": str(orphan.resolve()),
            "reason": "unregistered worktree with missing gitdir",
            "gitdir": str(missing.resolve()),
        }
    ]
    assert (orphan / "recover-me.txt").read_text(encoding="utf-8") == "local work\n"


def test_reaper_error_marks_repository_run_failed(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = _repo(tmp_path)
    worktree = repo / ".worktrees" / "dispatch" / "codex" / "failed"
    row = cleanup.reap_worktrees.ReapResult(
        path=str(worktree),
        branch="codex/failed",
        action="error",
        reason="PR #1 MERGED",
        dirty=False,
        error="worktree removal failed",
    )
    monkeypatch.setattr(
        cleanup.reap_worktrees,
        "_live_cwd_paths",
        lambda _repo: set(),
    )
    monkeypatch.setattr(
        cleanup.reap_worktrees,
        "reap_worktrees",
        lambda **_kwargs: [replace(row)],
    )
    monkeypatch.setattr(
        cleanup,
        "find_orphaned_worktree_directories",
        lambda _repo: [],
    )

    result = cleanup._repo_result(repo, apply=True)

    assert result["errors"] == [f"{worktree}: worktree removal failed"]


def test_lock_contention_marks_repository_run_failed(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = _repo(tmp_path)
    monkeypatch.setattr(
        cleanup.reap_worktrees,
        "_live_cwd_paths",
        lambda _repo: set(),
    )
    monkeypatch.setattr(
        cleanup.reap_worktrees,
        "reap_worktrees",
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("cleanup lock held")),
    )

    result = cleanup._repo_result(repo, apply=True)

    assert result["errors"] == ["cleanup lock held"]


def test_receipt_aggregates_both_repositories(tmp_path: Path, monkeypatch) -> None:
    public = tmp_path / "public"
    private = tmp_path / "private"

    def fake_repo_result(repo_root: Path, *, apply: bool):
        return {
            "repo_root": str(repo_root),
            "fetch": {"ok": True, "detail": None},
            "activity_probe": {"available": True, "cwd_count": 2},
            "results": [
                {
                    "action": "removed" if repo_root == public else "skipped",
                }
            ],
            "orphans": [{"path": "orphan"}] if repo_root == private else [],
            "errors": [],
            "apply": apply,
        }

    monkeypatch.setattr(cleanup, "_repo_result", fake_repo_result)

    receipt = cleanup.build_receipt(
        [public, private],
        apply=True,
        observed_at="2026-07-28T20:00:00Z",
    )

    assert receipt["summary"] == {
        "repositories": 2,
        "removed": 1,
        "orphans_reported": 1,
        "errors": 0,
    }
    assert receipt["mode"] == "apply"


def test_receipt_write_is_atomic_and_private(tmp_path: Path) -> None:
    receipt = {
        "schema_version": cleanup.SCHEMA_VERSION,
        "observed_at": "2026-07-28T20:00:00Z",
        "mode": "dry_run",
        "summary": {"repositories": 0, "removed": 0, "orphans_reported": 0, "errors": 0},
        "repositories": [],
    }

    receipt_dir = tmp_path / "state" / "receipts" / "v1"
    path = cleanup.write_receipt(receipt, receipt_dir)

    assert json.loads(path.read_text(encoding="utf-8")) == receipt
    assert path.stat().st_mode & 0o777 == 0o600
    assert (tmp_path / "state").stat().st_mode & 0o777 == 0o700
    assert (tmp_path / "state" / "receipts").stat().st_mode & 0o777 == 0o700
    assert receipt_dir.stat().st_mode & 0o777 == 0o700
