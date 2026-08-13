from __future__ import annotations

import json
import os
import shutil
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
        env=env, timeout=30,
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


def test_scheduled_cleanup_enables_terminal_dispatch_class_by_default(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = _repo(tmp_path)
    captured: dict[str, object] = {}
    monkeypatch.setattr(cleanup, "_worktree_prune", lambda _repo, *, apply: {"ok": True})
    monkeypatch.setattr(cleanup.reap_worktrees, "_live_cwd_paths", lambda _repo: set())
    monkeypatch.setattr(
        cleanup.reap_worktrees,
        "reap_worktrees",
        lambda **kwargs: captured.update(kwargs) or [],
    )
    monkeypatch.setattr(cleanup, "cleanup_gone_local_branches", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(cleanup, "find_orphaned_worktree_directories", lambda _repo: [])
    monkeypatch.setattr(cleanup, "_git_maintenance", lambda _repo, *, apply: {"ok": True})
    monkeypatch.setattr(cleanup, "sweep_review_temp_orphans", lambda: {"errors": 0})
    monkeypatch.setattr(cleanup, "sweep_tmp_leaks", lambda apply=False: {"errors": 0, "roots_reaped": 0, "bytes_freed": 0, "candidates": 0, "skipped_live": 0})

    cleanup._repo_result(repo, apply=False)

    assert captured["merged_pr_only"] is True
    assert captured["include_terminal_dispatches"] is True


def test_scheduled_terminal_dispatch_class_can_be_disabled(tmp_path: Path, monkeypatch) -> None:
    repo = _repo(tmp_path)
    captured: dict[str, object] = {}
    monkeypatch.setenv("LU_REAPER_TERMINAL_DISPATCHES", "0")
    monkeypatch.setattr(cleanup, "_worktree_prune", lambda _repo, *, apply: {"ok": True})
    monkeypatch.setattr(cleanup.reap_worktrees, "_live_cwd_paths", lambda _repo: set())
    monkeypatch.setattr(
        cleanup.reap_worktrees,
        "reap_worktrees",
        lambda **kwargs: captured.update(kwargs) or [],
    )
    monkeypatch.setattr(cleanup, "cleanup_gone_local_branches", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(cleanup, "find_orphaned_worktree_directories", lambda _repo: [])
    monkeypatch.setattr(cleanup, "_git_maintenance", lambda _repo, *, apply: {"ok": True})
    monkeypatch.setattr(cleanup, "sweep_review_temp_orphans", lambda: {"errors": 0})
    monkeypatch.setattr(cleanup, "sweep_tmp_leaks", lambda apply=False: {"errors": 0, "roots_reaped": 0, "bytes_freed": 0, "candidates": 0, "skipped_live": 0})

    cleanup._repo_result(repo, apply=False)

    assert captured["include_terminal_dispatches"] is False


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


def test_stale_worktree_registration_is_pruned_before_reaping(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = _repo(tmp_path)
    branch = "codex/stale-registration"
    worktree = repo / ".worktrees" / "dispatch" / "codex" / "stale-registration"
    _git(repo, "worktree", "add", "-b", branch, str(worktree), "main")
    shutil.rmtree(worktree)
    monkeypatch.setattr(
        cleanup.reap_worktrees,
        "_live_cwd_paths",
        lambda _repo: set(),
    )

    result = cleanup._repo_result(repo, apply=True)

    assert result["errors"] == []
    assert result["worktree_prune"]["ok"] is True
    registered = cleanup.reap_worktrees.list_git_worktrees(repo)
    assert all(item.path != worktree for item in registered)


def _gone_branch(repo: Path, branch: str) -> str:
    _git(repo, "branch", branch, "main")
    _git(repo, "push", "origin", branch)
    _git(repo, "branch", "--set-upstream-to", f"origin/{branch}", branch)
    head_sha = _git(repo, "rev-parse", branch)
    _git(repo, "push", "origin", "--delete", branch)
    return head_sha


def test_exact_merged_gone_branch_is_deleted(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = _repo(tmp_path)
    branch = "codex/merged-gone"
    head_sha = _gone_branch(repo, branch)
    monkeypatch.setattr(
        cleanup.reap_worktrees,
        "_query_pr_states",
        lambda _repo, candidate: (
            [
                cleanup.reap_worktrees.PullRequestState(
                    number=42,
                    state="MERGED",
                    head_sha=head_sha,
                )
            ]
            if candidate == branch
            else [],
            None,
        ),
    )

    dry_run = cleanup.cleanup_gone_local_branches(repo, apply=False)
    applied = cleanup.cleanup_gone_local_branches(repo, apply=True)

    assert dry_run == [
        {
            "action": "would_delete",
            "branch": branch,
            "head_sha": head_sha,
            "reason": "upstream gone; exact head of MERGED PR #42",
        }
    ]
    assert applied[0]["action"] == "deleted"
    assert _git(repo, "branch", "--list", branch) == ""


def test_unproven_gone_branch_is_preserved(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = _repo(tmp_path)
    _git(repo, "checkout", "-b", "source-work")
    (repo / "local.txt").write_text("not merged\n", encoding="utf-8")
    _git(repo, "add", "local.txt")
    _git(repo, "commit", "-m", "local only")
    _git(repo, "checkout", "main")
    branch = "codex/unproven-gone"
    _git(repo, "branch", branch, "source-work")
    _git(repo, "push", "origin", branch)
    _git(repo, "branch", "--set-upstream-to", f"origin/{branch}", branch)
    _git(repo, "push", "origin", "--delete", branch)
    monkeypatch.setattr(
        cleanup.reap_worktrees,
        "_query_pr_states",
        lambda _repo, _branch: ([], None),
    )

    result = cleanup.cleanup_gone_local_branches(repo, apply=True)

    row = next(item for item in result if item["branch"] == branch)
    assert row["action"] == "skipped"
    assert "no exact merged-PR" in row["reason"]
    assert _git(repo, "branch", "--list", branch) != ""


def test_pr_query_failure_preserves_branch_and_reports_error(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = _repo(tmp_path)
    branch = "codex/pr-query-failed"
    _gone_branch(repo, branch)
    monkeypatch.setattr(
        cleanup.reap_worktrees,
        "_query_pr_states",
        lambda _repo, _branch: ([], "gh pr list failed: offline"),
    )

    result = cleanup.cleanup_gone_local_branches(repo, apply=True)

    assert result == [
        {
            "action": "error",
            "branch": branch,
            "head_sha": _git(repo, "rev-parse", branch),
            "reason": "upstream gone but PR state could not be verified",
            "error": "gh pr list failed: offline",
        }
    ]
    assert _git(repo, "branch", "--list", branch) != ""


def test_open_pr_preserves_gone_branch(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = _repo(tmp_path)
    branch = "codex/open-pr"
    head_sha = _gone_branch(repo, branch)
    monkeypatch.setattr(
        cleanup.reap_worktrees,
        "_query_pr_states",
        lambda _repo, _branch: (
            [
                cleanup.reap_worktrees.PullRequestState(
                    number=99,
                    state="OPEN",
                    head_sha=head_sha,
                )
            ],
            None,
        ),
    )

    result = cleanup.cleanup_gone_local_branches(repo, apply=True)

    assert result[0]["action"] == "skipped"
    assert result[0]["reason"] == "upstream gone but PR #99 is OPEN"
    assert _git(repo, "branch", "--list", branch) != ""


def test_checked_out_branch_is_not_deleted(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    branch = "codex/checked-out"
    worktree = repo / ".worktrees" / "dispatch" / "codex" / "checked-out"
    _git(repo, "worktree", "add", "-b", branch, str(worktree), "main")
    expected_head = _git(repo, "rev-parse", branch)

    error = cleanup._delete_local_branch(
        repo,
        branch=branch,
        expected_head=expected_head,
    )

    assert error is not None
    assert _git(repo, "branch", "--list", branch) != ""
    assert _git(worktree, "branch", "--show-current") == branch


def test_origin_main_ancestor_with_gone_upstream_is_deleted(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = _repo(tmp_path)
    branch = "codex/ancestor-gone"
    _git(repo, "checkout", "-b", branch)
    (repo / "merged.txt").write_text("merged remotely\n", encoding="utf-8")
    _git(repo, "add", "merged.txt")
    _git(repo, "commit", "-m", "merged branch commit")
    _git(repo, "push", "-u", "origin", branch)
    branch_head = _git(repo, "rev-parse", "HEAD")
    _git(repo, "push", "origin", f"{branch}:main")
    _git(repo, "checkout", "main")
    assert _git(repo, "rev-parse", "HEAD") != branch_head
    _git(repo, "push", "origin", "--delete", branch)
    monkeypatch.setattr(
        cleanup.reap_worktrees,
        "_query_pr_states",
        lambda _repo, _branch: ([], None),
    )

    result = cleanup.cleanup_gone_local_branches(repo, apply=True)

    assert result[0]["action"] == "deleted"
    assert "ancestor of origin/main" in result[0]["reason"]
    assert _git(repo, "branch", "--list", branch) == ""


def test_repository_run_fails_closed_when_hygiene_lock_is_held(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)

    with cleanup._GitHygieneLock(repo):
        result = cleanup._repo_result(repo, apply=False)

    assert result["fetch"] is None
    assert result["errors"] == [
        f"another scheduled Git hygiene run holds "
        f"{repo / '.git' / 'scheduled-git-hygiene.lock'}"
    ]


def test_worktree_prune_failure_stops_repository_run(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = _repo(tmp_path)
    monkeypatch.setattr(
        cleanup,
        "_worktree_prune",
        lambda _repo, *, apply: {
            "action": "pruned",
            "detail": "cannot prune",
            "ok": False,
        },
    )

    result = cleanup._repo_result(repo, apply=True)

    assert result["results"] == []
    assert result["branches"] == []
    assert result["maintenance"] is None
    assert result["errors"] == ["worktree prune failed; cleanup skipped"]


def test_lock_contention_is_aggregated_in_receipt(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)

    with cleanup._GitHygieneLock(repo):
        receipt = cleanup.build_receipt(
            [repo],
            apply=True,
            observed_at="2026-07-29T10:00:00Z",
        )

    assert receipt["schema_version"] == "scheduled-git-hygiene.v2"
    assert receipt["summary"]["errors"] == 1
    assert "another scheduled Git hygiene run holds" in (
        receipt["repositories"][0]["errors"][0]
    )


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
                    "branch_pruned": repo_root == public,
                }
            ],
            "branches": [
                {"action": "deleted"} if repo_root == public else {"action": "skipped"}
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
        "branches_deleted": 2,
        "orphans_reported": 1,
        "errors": 0,
        "review_temp_reaped": 0,
        "review_temp_bytes_freed": 0,
        "needs_finalize_worktrees": [],
    }
    assert receipt["mode"] == "apply"


def test_main_records_read_only_home_session_policy_and_prints_hard_warning(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    receipt = {"summary": {"errors": 0}}
    home_report = {
        "mode": "read_only",
        "policy": {"retention_days": 14},
        "lanes": [],
        "violations": [
            {
                "provider": "codex",
                "kind": "stale_sessions",
                "stale_files": 1,
                "stale_bytes": 2,
            }
        ],
    }
    monkeypatch.setattr(cleanup, "build_receipt", lambda *_args, **_kwargs: receipt)
    monkeypatch.setattr(cleanup.home_session_retention_check, "build_report", lambda: home_report)
    monkeypatch.setattr(
        cleanup.home_session_retention_check,
        "warning_lines",
        lambda _report: ["HARD WARNING: stale home session"],
    )
    monkeypatch.setattr(cleanup, "write_receipt", lambda *_args: tmp_path / "receipt.json")

    assert cleanup.main(["--repo-root", str(tmp_path), "--receipt-dir", str(tmp_path)]) == 0

    assert receipt["home_session_retention"] is home_report
    assert "HARD WARNING: stale home session" in capsys.readouterr().err


def test_git_maintenance_failure_is_reported(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = _repo(tmp_path)
    monkeypatch.setattr(cleanup.reap_worktrees, "_live_cwd_paths", lambda _repo: set())
    monkeypatch.setattr(cleanup.reap_worktrees, "reap_worktrees", lambda **_kwargs: [])
    monkeypatch.setattr(cleanup, "cleanup_gone_local_branches", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(cleanup, "find_orphaned_worktree_directories", lambda _repo: [])
    monkeypatch.setattr(
        cleanup,
        "_git_maintenance",
        lambda _repo, *, apply: {
            "action": "ran",
            "ok": False,
            "detail": "gc failed",
        },
    )

    result = cleanup._repo_result(repo, apply=True)

    assert result["errors"] == ["git maintenance failed: gc failed"]


def test_receipt_write_is_atomic_and_private(tmp_path: Path) -> None:
    receipt = {
        "schema_version": cleanup.SCHEMA_VERSION,
        "observed_at": "2026-07-28T20:00:00Z",
        "mode": "dry_run",
        "summary": {"repositories": 0, "removed": 0, "orphans_reported": 0, "errors": 0},
        "repositories": [],
    }

    receipt_dir = tmp_path / "state" / "receipts" / "v2"
    path = cleanup.write_receipt(receipt, receipt_dir)

    assert json.loads(path.read_text(encoding="utf-8")) == receipt
    assert path.stat().st_mode & 0o777 == 0o600
    assert (tmp_path / "state").stat().st_mode & 0o777 == 0o700
    assert (tmp_path / "state" / "receipts").stat().st_mode & 0o777 == 0o700
    assert receipt_dir.stat().st_mode & 0o777 == 0o700
