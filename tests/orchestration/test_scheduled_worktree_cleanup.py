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
        if not key.startswith("GIT_") and not key.startswith("PRE_COMMIT") and key != "AGENT_NO_MERGE"
    }
    proc = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
        env=env,
        timeout=30,
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
    monkeypatch.setattr(cleanup, "cleanup_stale_origin_branches", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(cleanup, "cleanup_untracked_local_branches", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(cleanup, "find_orphaned_worktree_directories", lambda _repo: [])
    monkeypatch.setattr(cleanup, "_git_maintenance", lambda _repo, *, apply: {"ok": True})
    monkeypatch.setattr(cleanup, "sweep_review_temp_orphans", lambda: {"errors": 0})
    monkeypatch.setattr(
        cleanup,
        "sweep_tmp_leaks",
        lambda apply=False: {"errors": 0, "roots_reaped": 0, "bytes_freed": 0, "candidates": 0, "skipped_live": 0},
    )

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
    monkeypatch.setattr(cleanup, "cleanup_stale_origin_branches", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(cleanup, "cleanup_untracked_local_branches", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(cleanup, "find_orphaned_worktree_directories", lambda _repo: [])
    monkeypatch.setattr(cleanup, "_git_maintenance", lambda _repo, *, apply: {"ok": True})
    monkeypatch.setattr(cleanup, "sweep_review_temp_orphans", lambda: {"errors": 0})
    monkeypatch.setattr(
        cleanup,
        "sweep_tmp_leaks",
        lambda apply=False: {"errors": 0, "roots_reaped": 0, "bytes_freed": 0, "candidates": 0, "skipped_live": 0},
    )

    cleanup._repo_result(repo, apply=False)

    assert captured["include_terminal_dispatches"] is False


def test_scheduled_apply_reports_rescue_candidates_before_reaper(tmp_path: Path, monkeypatch) -> None:
    repo = _repo(tmp_path)
    script = repo / "scripts" / "delegate.py"
    script.parent.mkdir()
    script.write_text("# fixture\n", encoding="utf-8")
    calls: list[str] = []
    original_run = subprocess.run

    def capture_run(command, **kwargs):
        if isinstance(command, list) and str(script) in command:
            calls.append("rescue")
            assert command[-3:] == ["--all-stale", "--older-than", "6h"]
            assert "--apply" not in command
            return subprocess.CompletedProcess(
                command,
                0,
                '{"summary":{"candidate":1},"tasks":[{"task_id":"rescue-test","action":"candidate"}]}',
                "",
            )
        return original_run(command, **kwargs)

    monkeypatch.setattr(cleanup.subprocess, "run", capture_run)
    monkeypatch.setattr(cleanup, "_worktree_prune", lambda _repo, *, apply: {"ok": True})
    monkeypatch.setattr(cleanup.reap_worktrees, "_live_cwd_paths", lambda _repo: set())
    monkeypatch.setattr(cleanup.reap_worktrees, "reap_worktrees", lambda **_kwargs: calls.append("reaper") or [])
    monkeypatch.setattr(cleanup, "cleanup_gone_local_branches", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(cleanup, "cleanup_stale_origin_branches", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(cleanup, "cleanup_untracked_local_branches", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(cleanup, "find_orphaned_worktree_directories", lambda _repo: [])
    monkeypatch.setattr(cleanup, "_git_maintenance", lambda _repo, *, apply: {"ok": True})
    monkeypatch.setattr(cleanup, "sweep_review_temp_orphans", lambda: {"errors": 0})
    monkeypatch.setattr(cleanup, "sweep_tmp_leaks", lambda apply=False: {"errors": 0})

    result = cleanup._repo_result(repo, apply=True)
    assert calls[:2] == ["rescue", "reaper"]
    assert result["rescue"] == {
        "summary": {"candidate": 1},
        "tasks": [{"task_id": "rescue-test", "action": "candidate"}],
    }
    public = cleanup.build_public_summary({"repositories": [result], "summary": {}}, None)
    assert public["repositories"]["repo"]["rescue_candidates"] == 1


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
    monkeypatch.setattr(
        cleanup.reap_worktrees,
        "_query_pr_states",
        lambda *_args, **_kwargs: ([], None),
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


def test_scratch_review_branch_on_main_is_deleted_for_ancestry(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = _repo(tmp_path)
    branch = "codex/review-8115-r1"
    _gone_branch(repo, branch)
    monkeypatch.setattr(
        cleanup.reap_worktrees,
        "_query_pr_states",
        lambda _repo, _branch: ([], None),
    )

    result = cleanup.cleanup_gone_local_branches(repo, apply=True)

    row = next(item for item in result if item["branch"] == branch)
    assert row["action"] == "deleted"
    assert "ancestor of origin/main" in row["reason"]
    assert _git(repo, "branch", "--list", branch) == ""


def test_non_scratch_prefix_is_preserved(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = _repo(tmp_path)
    _git(repo, "checkout", "-b", "source-work")
    (repo / "cf.txt").write_text("not scratch\n", encoding="utf-8")
    _git(repo, "add", "cf.txt")
    _git(repo, "commit", "-m", "local only")
    _git(repo, "checkout", "main")
    branch = "cf-unproven"
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
    assert _git(repo, "branch", "--list", branch) != ""


def test_squash_parent_is_deleted_and_main_ancestor_is_not_called_contained(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = _repo(tmp_path)
    _git(repo, "checkout", "-b", "feature")
    (repo / "parent.txt").write_text("parent\n", encoding="utf-8")
    _git(repo, "add", "parent.txt")
    _git(repo, "commit", "-m", "parent")
    parent = _git(repo, "rev-parse", "HEAD")
    (repo / "tip.txt").write_text("tip\n", encoding="utf-8")
    _git(repo, "add", "tip.txt")
    _git(repo, "commit", "-m", "tip")
    tip = _git(repo, "rev-parse", "HEAD")
    _git(repo, "checkout", "main")
    contained = "codex/squash-parent"
    _git(repo, "branch", contained, parent)
    _git(repo, "push", "origin", contained)
    _git(repo, "branch", "--set-upstream-to", f"origin/{contained}", contained)
    _git(repo, "push", "origin", "--delete", contained)

    base = _git(repo, "rev-parse", "main")
    (repo / "later.txt").write_text("later\n", encoding="utf-8")
    _git(repo, "add", "later.txt")
    _git(repo, "commit", "-m", "later main")
    _git(repo, "push", "origin", "main")
    on_main = "codex/old-main"
    _git(repo, "branch", on_main, base)
    _git(repo, "push", "origin", on_main)
    _git(repo, "branch", "--set-upstream-to", f"origin/{on_main}", on_main)
    _git(repo, "push", "origin", "--delete", on_main)

    def _prs(_repo: Path, candidate: str):
        if candidate == contained:
            return (
                [cleanup.reap_worktrees.PullRequestState(number=7, state="MERGED", head_sha=tip)],
                None,
            )
        if candidate == on_main:
            return (
                [cleanup.reap_worktrees.PullRequestState(number=8, state="MERGED", head_sha=tip)],
                None,
            )
        return [], None

    monkeypatch.setattr(cleanup.reap_worktrees, "_query_pr_states", _prs)

    result = cleanup.cleanup_gone_local_branches(repo, apply=True)
    by_branch = {item["branch"]: item for item in result}
    assert by_branch[contained]["action"] == "deleted"
    assert "contained in MERGED PR #7" in by_branch[contained]["reason"]
    assert by_branch[on_main]["action"] == "deleted"
    assert "ancestor of origin/main" in by_branch[on_main]["reason"]
    assert "contained" not in by_branch[on_main]["reason"]


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
    assert "no exact merged/closed PR" in row["reason"]
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
        f"another scheduled Git hygiene run holds {repo / '.git' / 'scheduled-git-hygiene.lock'}"
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
    assert "another scheduled Git hygiene run holds" in (receipt["repositories"][0]["errors"][0])


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
            "branches": [{"action": "deleted"} if repo_root == public else {"action": "skipped"}],
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
        "retained": 1,
        "retained_exceptions": 0,
        "by_preservation_class": {
            "primary": 0,
            "active_dispatch": 0,
            "open_pr": 0,
            "dirty": 0,
            "detached_unknown": 0,
            "permission_error": 0,
            "foreign": 0,
            "unmerged": 0,
            "uncertain": 1,
        },
        "by_owner": {"unattributed": 2},
        "branches_deleted": 2,
        "origin_branches_deleted": 0,
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
    monkeypatch.setattr(cleanup, "cleanup_stale_origin_branches", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(cleanup, "cleanup_untracked_local_branches", lambda *_args, **_kwargs: [])
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


def test_exact_merged_origin_branch_is_deleted(tmp_path: Path, monkeypatch) -> None:
    repo = _repo(tmp_path)
    branch = "codex/merged-origin"
    _git(repo, "branch", branch, "main")
    _git(repo, "push", "origin", branch)
    head_sha = _git(repo, "rev-parse", branch)

    def _prs(_repo: Path, candidate: str | None):
        if candidate != branch:
            return [], None
        return (
            [
                cleanup.reap_worktrees.PullRequestState(
                    number=77,
                    state="MERGED",
                    head_sha=head_sha,
                )
            ],
            None,
        )

    monkeypatch.setattr(cleanup.reap_worktrees, "_query_pr_states", _prs)

    applied = cleanup.cleanup_stale_origin_branches(repo, apply=True)

    assert applied[0]["action"] == "deleted"
    assert "exact head of MERGED PR #77" in applied[0]["reason"]
    remote_heads = _git(tmp_path / "origin.git", "for-each-ref", "--format=%(refname:short)")
    assert branch not in remote_heads.splitlines()


def _unique_pushed_branch(repo: Path, branch: str) -> str:
    _git(repo, "checkout", "-b", branch)
    filename = branch.replace("/", "-") + ".txt"
    (repo / filename).write_text(branch + "\n", encoding="utf-8")
    _git(repo, "add", filename)
    _git(repo, "commit", "-m", branch)
    head_sha = _git(repo, "rev-parse", "HEAD")
    _git(repo, "push", "-u", "origin", branch)
    _git(repo, "checkout", "main")
    return head_sha


def _closed_pr(number: int, head_sha: str) -> cleanup.reap_worktrees.PullRequestState:
    return cleanup.reap_worktrees.PullRequestState(
        number=number,
        state="CLOSED",
        head_sha=head_sha,
    )


def test_closed_pr_exact_head_with_matching_pull_ref_is_deleted(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = _repo(tmp_path)
    branch = "codex/closed-durable"
    head_sha = _unique_pushed_branch(repo, branch)
    _git(tmp_path / "origin.git", "update-ref", "refs/pull/88/head", head_sha)
    monkeypatch.setattr(
        cleanup.reap_worktrees,
        "_query_pr_states",
        lambda _repo, candidate: ([_closed_pr(88, head_sha)], None) if candidate == branch else ([], None),
    )

    applied = cleanup.cleanup_stale_origin_branches(repo, apply=True)

    row = next(item for item in applied if item["branch"] == branch)
    assert row["action"] == "deleted"
    assert row["reason"] == "origin head; exact head of CLOSED PR #88"
    remote_heads = _git(tmp_path / "origin.git", "for-each-ref", "--format=%(refname:short)")
    assert branch not in remote_heads.splitlines()


def test_closed_pr_exact_head_with_mismatched_pull_ref_is_kept(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = _repo(tmp_path)
    branch = "codex/closed-mismatch"
    head_sha = _unique_pushed_branch(repo, branch)
    main_sha = _git(repo, "rev-parse", "main")
    _git(tmp_path / "origin.git", "update-ref", "refs/pull/89/head", main_sha)
    monkeypatch.setattr(
        cleanup.reap_worktrees,
        "_query_pr_states",
        lambda _repo, candidate: ([_closed_pr(89, head_sha)], None) if candidate == branch else ([], None),
    )

    applied = cleanup.cleanup_stale_origin_branches(repo, apply=True)

    row = next(item for item in applied if item["branch"] == branch)
    assert row["action"] == "skipped"
    assert "refs/pull/89/head" in row["reason"]
    remote_heads = _git(tmp_path / "origin.git", "for-each-ref", "--format=%(refname:short)")
    assert branch in remote_heads.splitlines()


def test_closed_pr_exact_head_ls_remote_error_is_kept(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = _repo(tmp_path)
    branch = "codex/closed-ls-remote-error"
    head_sha = _unique_pushed_branch(repo, branch)
    _git(tmp_path / "origin.git", "update-ref", "refs/pull/90/head", head_sha)
    monkeypatch.setattr(
        cleanup.reap_worktrees,
        "_query_pr_states",
        lambda _repo, candidate: ([_closed_pr(90, head_sha)], None) if candidate == branch else ([], None),
    )
    real_run_git = cleanup._run_git

    def fail_pull_ref(repo_root: Path, *args: str):
        if any(arg.startswith("refs/pull/") for arg in args):
            return subprocess.CompletedProcess(
                ["git", *args],
                128,
                "",
                "fatal: could not read from remote repository",
            )
        return real_run_git(repo_root, *args)

    monkeypatch.setattr(cleanup, "_run_git", fail_pull_ref)

    applied = cleanup.cleanup_stale_origin_branches(repo, apply=True)

    row = next(item for item in applied if item["branch"] == branch)
    assert row["action"] == "skipped"
    assert "refs/pull/90/head" in row["reason"]
    remote_heads = _git(tmp_path / "origin.git", "for-each-ref", "--format=%(refname:short)")
    assert branch in remote_heads.splitlines()


def test_unique_unproven_origin_branch_is_preserved(tmp_path: Path, monkeypatch) -> None:
    repo = _repo(tmp_path)
    _git(repo, "checkout", "-b", "codex/unique-origin")
    (repo / "unique.txt").write_text("unique\n", encoding="utf-8")
    _git(repo, "add", "unique.txt")
    _git(repo, "commit", "-m", "unique")
    _git(repo, "push", "-u", "origin", "codex/unique-origin")
    _git(repo, "checkout", "main")
    monkeypatch.setattr(
        cleanup.reap_worktrees,
        "_query_pr_states",
        lambda _repo, _branch: ([], None),
    )

    result = cleanup.cleanup_stale_origin_branches(repo, apply=True)

    row = next(item for item in result if item["branch"] == "codex/unique-origin")
    assert row["action"] == "skipped"
    assert "no exact merged/closed PR" in row["reason"]
    remote_heads = _git(tmp_path / "origin.git", "for-each-ref", "--format=%(refname:short)")
    assert "codex/unique-origin" in remote_heads


def test_untracked_ancestor_local_branch_is_deleted(tmp_path: Path, monkeypatch) -> None:
    repo = _repo(tmp_path)
    branch = "claude/old-local"
    _git(repo, "branch", branch, "main")
    monkeypatch.setattr(
        cleanup.reap_worktrees,
        "_query_pr_states",
        lambda _repo, _branch: ([], None),
    )

    result = cleanup.cleanup_untracked_local_branches(repo, apply=True)

    assert result[0]["action"] == "deleted"
    assert "ancestor of origin/main" in result[0]["reason"]
    assert _git(repo, "branch", "--list", branch) == ""


def test_rescue_ref_with_unique_commit_and_no_pr_is_skipped(tmp_path: Path, monkeypatch) -> None:
    repo = _repo(tmp_path)
    _git(repo, "checkout", "-b", "rescue/x")
    (repo / "unique.txt").write_text("keep me\n", encoding="utf-8")
    _git(repo, "add", "unique.txt")
    _git(repo, "commit", "-m", "unique rescue")
    _git(repo, "checkout", "main")
    monkeypatch.setattr(
        cleanup.reap_worktrees,
        "_query_pr_states",
        lambda _repo, _branch: ([], None),
    )

    result = cleanup.cleanup_untracked_local_branches(repo, apply=True)

    row = next(item for item in result if item["branch"] == "rescue/x")
    assert row["action"] == "skipped"
    assert "agent scratch ref" in row["reason"]
    assert "tip not contained" in row["reason"]
    assert _git(repo, "branch", "--list", "rescue/x") != ""


def test_scratch_ancestor_of_origin_main_is_deleted(tmp_path: Path, monkeypatch) -> None:
    repo = _repo(tmp_path)
    branch = "claude/review-9"
    _git(repo, "branch", branch, "main")
    monkeypatch.setattr(
        cleanup.reap_worktrees,
        "_query_pr_states",
        lambda _repo, _branch: ([], None),
    )

    result = cleanup.cleanup_untracked_local_branches(repo, apply=True)

    row = next(item for item in result if item["branch"] == branch)
    assert row["action"] == "deleted"
    assert "ancestor of origin/main" in row["reason"]
    assert _git(repo, "branch", "--list", branch) == ""


def test_scratch_ref_on_another_origin_ref_is_deleted(tmp_path: Path, monkeypatch) -> None:
    repo = _repo(tmp_path)
    _git(repo, "checkout", "-b", "feature/landed")
    (repo / "landed.txt").write_text("on origin\n", encoding="utf-8")
    _git(repo, "add", "landed.txt")
    _git(repo, "commit", "-m", "landed elsewhere")
    _git(repo, "push", "-u", "origin", "feature/landed")
    _git(repo, "checkout", "main")
    branch = "rescue/copied"
    _git(repo, "branch", branch, "feature/landed")
    monkeypatch.setattr(
        cleanup.reap_worktrees,
        "_query_pr_states",
        lambda _repo, _branch: ([], None),
    )

    result = cleanup.cleanup_untracked_local_branches(repo, apply=True)

    row = next(item for item in result if item["branch"] == branch)
    assert row["action"] == "deleted"
    assert "contained in a remote ref" in row["reason"]
    assert _git(repo, "branch", "--list", branch) == ""
    remote_heads = _git(tmp_path / "origin.git", "for-each-ref", "--format=%(refname:short)")
    assert "feature/landed" in remote_heads.splitlines()


def test_scratch_ref_is_skipped_when_remote_containment_git_errors(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = _repo(tmp_path)
    _git(repo, "checkout", "-b", "rescue/unreadable")
    (repo / "unreadable.txt").write_text("do not drop\n", encoding="utf-8")
    _git(repo, "add", "unreadable.txt")
    _git(repo, "commit", "-m", "unreadable containment")
    _git(repo, "checkout", "main")
    monkeypatch.setattr(
        cleanup.reap_worktrees,
        "_query_pr_states",
        lambda _repo, _branch: ([], None),
    )
    real_run_git = cleanup._run_git

    def flaky_run_git(repo_root: Path, *args: str):
        if "--contains" in args:
            return subprocess.CompletedProcess(
                args=["git", *args],
                returncode=128,
                stdout="",
                stderr="fatal: containment check failed",
            )
        return real_run_git(repo_root, *args)

    monkeypatch.setattr(cleanup, "_run_git", flaky_run_git)

    result = cleanup.cleanup_untracked_local_branches(repo, apply=True)

    row = next(item for item in result if item["branch"] == "rescue/unreadable")
    assert row["action"] == "skipped"
    assert "tip not contained" in row["reason"]
    assert _git(repo, "branch", "--list", "rescue/unreadable") != ""


def test_scratch_ref_on_stale_origin_ref_is_kept(tmp_path: Path, monkeypatch) -> None:
    repo = _repo(tmp_path)
    _git(repo, "checkout", "-b", "feature/landed")
    (repo / "landed.txt").write_text("on origin\n", encoding="utf-8")
    _git(repo, "add", "landed.txt")
    _git(repo, "commit", "-m", "landed elsewhere")
    _git(repo, "push", "-u", "origin", "feature/landed")
    _git(repo, "checkout", "main")
    branch = "rescue/copied"
    _git(repo, "branch", branch, "feature/landed")
    # The remote branch is deleted but the local tracking ref is never pruned:
    # refs/remotes/origin/feature/landed is now a stale cache.
    _git(tmp_path / "origin.git", "update-ref", "-d", "refs/heads/feature/landed")
    monkeypatch.setattr(
        cleanup.reap_worktrees,
        "_query_pr_states",
        lambda _repo, _branch: ([], None),
    )

    result = cleanup.cleanup_untracked_local_branches(repo, apply=True)

    row = next(item for item in result if item["branch"] == branch)
    assert row["action"] == "skipped"
    assert "tip not contained" in row["reason"]
    assert _git(repo, "branch", "--list", branch) != ""


def test_scratch_ref_is_kept_when_live_remote_check_errors(tmp_path: Path, monkeypatch) -> None:
    repo = _repo(tmp_path)
    _git(repo, "checkout", "-b", "feature/landed")
    (repo / "landed.txt").write_text("on origin\n", encoding="utf-8")
    _git(repo, "add", "landed.txt")
    _git(repo, "commit", "-m", "landed elsewhere")
    _git(repo, "push", "-u", "origin", "feature/landed")
    _git(repo, "checkout", "main")
    branch = "rescue/copied"
    _git(repo, "branch", branch, "feature/landed")
    monkeypatch.setattr(
        cleanup.reap_worktrees,
        "_query_pr_states",
        lambda _repo, _branch: ([], None),
    )
    real_run_git = cleanup._run_git

    def flaky_run_git(repo_root: Path, *args: str):
        if "ls-remote" in args:
            return subprocess.CompletedProcess(
                args=["git", *args],
                returncode=128,
                stdout="",
                stderr="fatal: unable to connect to origin",
            )
        return real_run_git(repo_root, *args)

    monkeypatch.setattr(cleanup, "_run_git", flaky_run_git)

    result = cleanup.cleanup_untracked_local_branches(repo, apply=True)

    row = next(item for item in result if item["branch"] == branch)
    assert row["action"] == "skipped"
    assert "tip not contained" in row["reason"]
    assert _git(repo, "branch", "--list", branch) != ""


def test_fetch_failure_keeps_remote_containment_deletions(tmp_path: Path, monkeypatch) -> None:
    repo = _repo(tmp_path)
    # Ancestor-of-origin/main proof and other-origin-ref proof both rely on
    # local tracking refs, so a failed fetch must keep every one of them.
    ancestor_branch = "claude/review-9"
    _git(repo, "branch", ancestor_branch, "main")
    _git(repo, "checkout", "-b", "feature/landed")
    (repo / "landed.txt").write_text("on origin\n", encoding="utf-8")
    _git(repo, "add", "landed.txt")
    _git(repo, "commit", "-m", "landed elsewhere")
    _git(repo, "push", "-u", "origin", "feature/landed")
    _git(repo, "checkout", "main")
    contained_branch = "rescue/copied"
    _git(repo, "branch", contained_branch, "feature/landed")
    monkeypatch.setattr(
        cleanup.reap_worktrees,
        "_query_pr_states",
        lambda _repo, _branch: ([], None),
    )

    result = cleanup.cleanup_untracked_local_branches(repo, apply=True, fetch_ok=False)

    for branch in (ancestor_branch, contained_branch):
        row = next(item for item in result if item["branch"] == branch)
        assert row["action"] == "skipped"
        assert "fetch_failed_no_remote_proof" in row["reason"]
        assert _git(repo, "branch", "--list", branch) != ""


def test_fetch_failure_keeps_origin_head_deletions(tmp_path: Path, monkeypatch) -> None:
    repo = _repo(tmp_path)
    _git(repo, "checkout", "-b", "feature/landed")
    (repo / "landed.txt").write_text("on origin\n", encoding="utf-8")
    _git(repo, "add", "landed.txt")
    _git(repo, "commit", "-m", "landed elsewhere")
    _git(repo, "push", "-u", "origin", "feature/landed")
    _git(repo, "checkout", "main")
    _git(repo, "branch", "-D", "feature/landed")
    _git(repo, "branch", "rescue/copied", "origin/feature/landed")
    _git(repo, "push", "origin", "rescue/copied")
    _git(repo, "branch", "-D", "rescue/copied")
    monkeypatch.setattr(
        cleanup.reap_worktrees,
        "_query_pr_states",
        lambda _repo, _branch: ([], None),
    )

    result = cleanup.cleanup_stale_origin_branches(repo, apply=True, fetch_ok=False)

    row = next(item for item in result if item["branch"] == "rescue/copied")
    assert row["action"] == "skipped"
    assert "fetch_failed_no_remote_proof" in row["reason"]
    remote_heads = _git(tmp_path / "origin.git", "for-each-ref", "--format=%(refname:short)")
    assert "rescue/copied" in remote_heads.splitlines()


def test_repo_result_fetch_failure_keeps_and_reports(tmp_path: Path, monkeypatch) -> None:
    repo = _repo(tmp_path)
    branch = "claude/review-9"
    _git(repo, "branch", branch, "main")
    # Break the remote so this run's `fetch --prune` fails.
    _git(repo, "remote", "set-url", "origin", str(tmp_path / "missing.git"))
    monkeypatch.setattr(cleanup.reap_worktrees, "_live_cwd_paths", lambda _repo: set())
    monkeypatch.setattr(cleanup.reap_worktrees, "reap_worktrees", lambda **_kwargs: [])
    monkeypatch.setattr(cleanup.reap_worktrees, "adopt_dispatch_worktrees", lambda _repo: [])
    monkeypatch.setattr(
        cleanup.reap_worktrees,
        "_query_pr_states",
        lambda _repo, _branch: ([], None),
    )
    monkeypatch.setattr(cleanup, "cleanup_stale_origin_branches", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(cleanup, "find_orphaned_worktree_directories", lambda _repo: [])
    monkeypatch.setattr(cleanup, "_git_maintenance", lambda _repo, *, apply: {"ok": True})
    monkeypatch.setattr(cleanup, "sweep_review_temp_orphans", lambda: {"errors": 0})
    monkeypatch.setattr(
        cleanup,
        "sweep_tmp_leaks",
        lambda apply=False: {"errors": 0, "roots_reaped": 0, "bytes_freed": 0, "candidates": 0, "skipped_live": 0},
    )

    result = cleanup._repo_result(repo, apply=True)

    assert result["fetch"]["ok"] is False
    assert any("fetch failed" in error for error in result["errors"])
    row = next(item for item in result["branches"] if item["branch"] == branch)
    assert row["action"] == "skipped"
    assert "fetch_failed_no_remote_proof" in row["reason"]
    assert _git(repo, "branch", "--list", branch) != ""


def test_origin_scratch_ref_is_not_deleted_for_containing_itself(tmp_path: Path, monkeypatch) -> None:
    repo = _repo(tmp_path)
    _git(repo, "checkout", "-b", "rescue/only-here")
    (repo / "only.txt").write_text("remote only\n", encoding="utf-8")
    _git(repo, "add", "only.txt")
    _git(repo, "commit", "-m", "only on this remote ref")
    _git(repo, "push", "-u", "origin", "rescue/only-here")
    _git(repo, "checkout", "main")
    monkeypatch.setattr(
        cleanup.reap_worktrees,
        "_query_pr_states",
        lambda _repo, _branch: ([], None),
    )

    result = cleanup.cleanup_stale_origin_branches(repo, apply=True)

    row = next(item for item in result if item["branch"] == "rescue/only-here")
    assert row["action"] == "skipped"
    assert "tip not contained" in row["reason"]
    remote_heads = _git(tmp_path / "origin.git", "for-each-ref", "--format=%(refname:short)")
    assert "rescue/only-here" in remote_heads.splitlines()


def test_review_checkout_unrelated_commit_is_preserved(tmp_path: Path, monkeypatch) -> None:
    repo = _repo(tmp_path)
    _git(repo, "checkout", "-b", "pr-7020")
    (repo / "review.txt").write_text("review\n", encoding="utf-8")
    _git(repo, "add", "review.txt")
    _git(repo, "commit", "-m", "review tip")
    _git(repo, "checkout", "main")
    monkeypatch.setattr(
        cleanup.reap_worktrees,
        "_query_pr_states",
        lambda _repo, _branch: ([], None),
    )
    monkeypatch.setattr(
        cleanup,
        "_query_pr_by_number",
        lambda _repo, number: (
            [
                cleanup.reap_worktrees.PullRequestState(
                    number=number,
                    state="MERGED",
                    head_sha="0" * 40,
                )
            ],
            None,
        ),
    )

    result = cleanup.cleanup_untracked_local_branches(repo, apply=True)

    assert result[0]["action"] == "skipped"
    assert "no exact merged/closed PR" in result[0]["reason"]
    assert _git(repo, "branch", "--list", "pr-7020") != ""


def test_review_checkout_exact_merged_head_is_deleted(tmp_path: Path, monkeypatch) -> None:
    repo = _repo(tmp_path)
    branch = "pr-7020"
    _git(repo, "branch", branch, "main")
    head_sha = _git(repo, "rev-parse", branch)
    monkeypatch.setattr(
        cleanup.reap_worktrees,
        "_query_pr_states",
        lambda _repo, _branch: ([], None),
    )
    monkeypatch.setattr(
        cleanup,
        "_query_pr_by_number",
        lambda _repo, number: (
            [
                cleanup.reap_worktrees.PullRequestState(
                    number=number,
                    state="MERGED",
                    head_sha=head_sha,
                )
            ],
            None,
        ),
    )

    result = cleanup.cleanup_untracked_local_branches(repo, apply=True)

    assert result[0]["action"] == "deleted"
    assert "exact head of MERGED PR #7020" in result[0]["reason"]
    assert _git(repo, "branch", "--list", branch) == ""


def test_origin_entire_checkpoint_is_not_deleted(tmp_path: Path, monkeypatch) -> None:
    repo = _repo(tmp_path)
    branch = "entire/checkpoints/v1"
    _git(repo, "branch", branch, "main")
    _git(repo, "push", "origin", branch)
    monkeypatch.setattr(
        cleanup.reap_worktrees,
        "_query_pr_states",
        lambda _repo, _branch: ([], None),
    )

    result = cleanup.cleanup_stale_origin_branches(repo, apply=True)

    assert all(item.get("branch") != branch for item in result)
    remote_heads = _git(tmp_path / "origin.git", "for-each-ref", "--format=%(refname:short)")
    assert branch in remote_heads.splitlines()


def test_entire_checkpoint_branch_is_not_deleted(tmp_path: Path, monkeypatch) -> None:
    repo = _repo(tmp_path)
    _git(repo, "branch", "entire/checkpoints/v1", "main")
    monkeypatch.setattr(
        cleanup.reap_worktrees,
        "_query_pr_states",
        lambda _repo, _branch: ([], None),
    )

    result = cleanup.cleanup_untracked_local_branches(repo, apply=True)

    assert result == []
    assert _git(repo, "branch", "--list", "entire/checkpoints/v1") != ""


def test_dry_run_zero_repo_mutation(tmp_path: Path, monkeypatch) -> None:
    repo = _repo(tmp_path)
    remote = tmp_path / "origin.git"

    # Add a stale refspec that reconcile_fetch_refspecs would prune if apply=True
    _git(
        repo,
        "config",
        "--add",
        "remote.origin.fetch",
        "+refs/heads/gone-head:refs/remotes/origin/gone-head",
    )
    config_before = (repo / ".git" / "config").read_text(encoding="utf-8")
    refs_before = _git(repo, "for-each-ref")

    # Push a new commit to remote directly, so if fetch was called, refs would change
    work_clone = tmp_path / "clone"
    _git(tmp_path, "clone", str(remote), str(work_clone))
    _git(work_clone, "config", "user.email", "remote@example.invalid")
    _git(work_clone, "config", "user.name", "Remote User")
    _git(work_clone, "checkout", "-b", "remote-feature")
    (work_clone / "feature.txt").write_text("feature\n", encoding="utf-8")
    _git(work_clone, "add", "feature.txt")
    _git(work_clone, "commit", "-m", "remote feature")
    _git(work_clone, "push", "origin", "remote-feature")

    monkeypatch.setattr(
        cleanup.reap_worktrees,
        "_query_pr_states",
        lambda _repo, _branch: ([], None),
    )

    result = cleanup._repo_result(repo, apply=False)

    # 1. Fetch was not run in dry-run
    assert result["fetch"] is None
    # 2. Refspec reconcile was dry-run (not applied)
    assert result["fetch_refspecs"] is not None
    assert result["fetch_refspecs"]["applied"] is False
    assert "+refs/heads/gone-head:refs/remotes/origin/gone-head" in result["fetch_refspecs"]["pruned"]

    # 3. .git/config is completely unmodified
    config_after = (repo / ".git" / "config").read_text(encoding="utf-8")
    assert config_after == config_before

    # 4. Git refs in local repo are completely unmodified (new remote-feature ref was NOT fetched)
    refs_after = _git(repo, "for-each-ref")
    assert refs_after == refs_before
    assert "remote-feature" not in refs_after


def test_report_mode_preserves_review_temp_orphans(tmp_path: Path, monkeypatch) -> None:
    """Report/dry-run mode must never mutate filesystem or delete review temp orphans."""
    repo = _repo(tmp_path)
    tmp_base = tmp_path / "scratch"
    tmp_base.mkdir()
    monkeypatch.setenv("LU_RUNTIME_TMP_BASE_ROOT", str(tmp_base))
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(tmp_base))

    from scripts.review.isolation import REVIEW_TEMP_ROOT_MANIFEST_NAME, create_review_temp_root

    root = create_review_temp_root(prefix="lu-review-snap-", dir=tmp_base)
    manifest_path = root / REVIEW_TEMP_ROOT_MANIFEST_NAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["owner_pid"] = 999999
    manifest["created_at_epoch"] = 1000.0
    manifest_path.chmod(0o600)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    monkeypatch.setattr(
        cleanup.reap_worktrees,
        "_query_pr_states",
        lambda _repo, _branch: ([], None),
    )

    # In report/dry-run mode (apply=False), root MUST NOT be reaped
    result_dry = cleanup._repo_result(repo, apply=False)
    assert result_dry.get("review_temp_sweep") is None
    assert root.exists(), "review temp orphan was deleted during report-only dry-run!"

    # In apply mode (apply=True), root IS reaped
    result_apply = cleanup._repo_result(repo, apply=True)
    assert result_apply.get("review_temp_sweep") is not None
    assert result_apply["review_temp_sweep"]["roots_reaped"] == 1
    assert not root.exists(), "review temp orphan should be reaped during apply mode"


def test_default_parser_targets_both_repositories() -> None:
    parser = cleanup.build_parser()
    args = parser.parse_args([])
    assert len(args.default_repo_roots) == 2
    assert args.default_repo_roots[0] == cleanup.default_public_repo()
    assert args.default_repo_roots[1] == cleanup.default_private_repo(cleanup.default_public_repo())


def test_build_public_summary_zero_path_dumps(tmp_path: Path) -> None:
    receipt = {
        "schema_version": cleanup.SCHEMA_VERSION,
        "observed_at": "2026-09-06T20:00:00Z",
        "mode": "dry_run",
        "summary": {
            "repositories": 2,
            "removed": 1,
            "retained": 3,
            "retained_exceptions": 2,
            "by_preservation_class": {
                "primary": 1,
                "dirty": 1,
                "permission_error": 1,
                "unmerged": 0,
            },
            "by_owner": {"codex": 2, "claude": 1},
            "branches_deleted": 0,
            "origin_branches_deleted": 0,
            "orphans_reported": 0,
            "errors": 0,
            "review_temp_reaped": 0,
            "review_temp_bytes_freed": 0,
        },
        "repositories": [
            {
                "repo_root": "/home/secret/host/learn-ukrainian",
                "retained": 2,
                "retained_exceptions": 1,
                "by_preservation_class": {"primary": 1, "dirty": 1},
                "by_owner": {"codex": 2},
                "results": [
                    {
                        "path": "/home/secret/host/learn-ukrainian/.worktrees/dispatch/codex/t1",
                        "branch": "codex/t1",
                        "action": "skipped",
                        "reason": "dirty",
                        "dirty": True,
                        "owner": "codex",
                    },
                ],
                "branches": [],
                "origin_branches": [],
                "orphans": [],
                "errors": [],
            },
            {
                "repo_root": "/home/secret/host/learn-ukrainian-infra-private",
                "retained": 1,
                "retained_exceptions": 1,
                "by_preservation_class": {"permission_error": 1},
                "by_owner": {"claude": 1},
                "results": [
                    {
                        "path": "/home/secret/host/learn-ukrainian-infra-private/.worktrees/dispatch/claude/t2",
                        "branch": "claude/t2",
                        "action": "error",
                        "reason": "permission denied",
                        "error": "permission denied",
                        "dirty": False,
                        "owner": "claude",
                    },
                ],
                "branches": [],
                "origin_branches": [],
                "orphans": [],
                "errors": [],
            },
        ],
    }

    receipt_path = Path("/home/secret/state/receipts/v2/20260906T200000Z-abcdef123456.json")
    public = cleanup.build_public_summary(receipt, receipt_path)

    assert public["receipt_id"] == "20260906T200000Z-abcdef123456.json"
    assert "learn-ukrainian" in public["repositories"]
    assert "learn-ukrainian-infra-private" in public["repositories"]
    assert public["summary"]["retained_exceptions"] == 2
    assert public["summary"]["by_owner"] == {"codex": 2, "claude": 1}

    # Verify zero host paths dumped anywhere
    dumped = json.dumps(public)
    assert "/home/secret" not in dumped
    assert ".worktrees" not in dumped
    assert "t1" not in dumped
    assert "t2" not in dumped


def test_classify_repo_results_retains_exceptions_and_owners() -> None:
    results = [
        {"action": "removed", "reason": "merged", "owner": "codex"},
        {"action": "skipped", "reason": "dirty worktree", "dirty": True, "owner": "codex"},
        {"action": "error", "reason": "failed", "error": "permission denied removing worktree", "owner": "claude"},
        {"action": "skipped", "reason": "primary checkout", "owner": "unattributed"},
    ]
    counts = cleanup.classify_repo_results(results)
    assert counts["total"] == 4
    assert counts["reaped"] == 1
    assert counts["retained"] == 3
    assert counts["retained_exceptions"] == 2  # dirty + permission_error
    assert counts["by_preservation_class"]["primary"] == 1
    assert counts["by_preservation_class"]["dirty"] == 1
    assert counts["by_preservation_class"]["permission_error"] == 1
    assert counts["by_owner"] == {"claude": 1, "codex": 2, "unattributed": 1}
    assert counts["reaped_by_owner"] == {"codex": 1}
