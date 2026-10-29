from __future__ import annotations

import contextlib
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.common import task_scratch
from scripts.maintenance.claude_session_scratch import ProcessEvidence, sweep_sessions
from scripts.orchestration import scheduled_worktree_cleanup as cleanup


@pytest.fixture(autouse=True)
def _isolated_task_scratch_root(tmp_path_factory, monkeypatch) -> Path:
    """Keep the #8738 task-scratch recovery hook off the host's real scratch root.

    ``_repo_result`` now runs ``recover_task_scratch``; without this override an
    apply-mode test would inspect (and, for provably dead orphans, reclaim)
    the live ``/var/tmp/lu/task-scratch`` namespace.
    """
    root = tmp_path_factory.mktemp("task-scratch-root")
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(root))
    session_root = root / f"claude-{os.getuid()}"
    monkeypatch.setattr(cleanup, "sweep_sessions", lambda **kwargs: sweep_sessions(session_root, **kwargs))
    real_tmp_sweep = cleanup.sweep_tmp_leaks
    monkeypatch.setattr(cleanup, "sweep_tmp_leaks", lambda **kwargs: real_tmp_sweep(tmp_roots=[root], **kwargs))
    return root


@pytest.mark.parametrize("apply", [False, True])
def test_main_sweeps_sessions_once_and_reports_counts_only(tmp_path: Path, monkeypatch, capsys, apply: bool) -> None:
    root = tmp_path / f"claude-{os.getuid()}"
    session = root / "project" / "12345678-1234-1234-1234-123456789abc"
    session.mkdir(parents=True)
    (session / "payload").write_bytes(b"payload")
    calls = []

    def sweep(**kwargs):
        calls.append(kwargs)
        return sweep_sessions(root, probe=lambda: ProcessEvidence(complete=True), **kwargs)

    monkeypatch.setattr(cleanup, "sweep_sessions", sweep)
    monkeypatch.setattr(
        cleanup,
        "build_receipt",
        lambda *_args, **_kwargs: {"observed_at": "2026-10-03T00:00:00Z", "summary": {"errors": 0}, "repositories": []},
    )
    monkeypatch.setattr(cleanup.home_session_retention_check, "build_report", lambda: {})
    monkeypatch.setattr(cleanup.home_session_retention_check, "warning_lines", lambda _report: [])
    args = [
        "--repo-root",
        str(tmp_path / "first"),
        "--repo-root",
        str(tmp_path / "second"),
        "--receipt-dir",
        str(tmp_path / "receipts"),
    ]
    if apply:
        args.append("--apply")
    assert cleanup.main(args) == 0
    assert len(calls) == 1 and calls[0]["apply"] == apply
    assert calls[0]["rollover_roots"] == [
        tmp_path / "first/.agent/thread-rollovers/claude",
        tmp_path / "second/.agent/thread-rollovers/claude",
    ]
    summary = json.loads(capsys.readouterr().out)
    assert summary["claude_session_scratch"]["removed" if apply else "would_remove"] == 1
    assert summary["claude_session_scratch"]["reclaimable_bytes"] == 7
    assert str(root) not in json.dumps(summary) and session.name not in json.dumps(summary)
    assert session.exists() is not apply


def test_main_session_error_is_recorded_and_returns_failure(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cleanup,
        "build_receipt",
        lambda *_args, **_kwargs: {"observed_at": "2026-10-03T00:00:00Z", "summary": {"errors": 0}, "repositories": []},
    )
    monkeypatch.setattr(cleanup.home_session_retention_check, "build_report", lambda: {})
    monkeypatch.setattr(cleanup.home_session_retention_check, "warning_lines", lambda _report: [])
    monkeypatch.setattr(cleanup, "sweep_sessions", lambda **_kwargs: {"summary": {"errors": 2}})
    assert cleanup.main(["--repo-root", str(tmp_path), "--receipt-dir", str(tmp_path / "receipts")]) == 1
    summary = json.loads(capsys.readouterr().out)
    assert summary["summary"]["errors"] == 2


def test_main_nested_lease_json_writes_receipt_and_keeps_scratch(tmp_path: Path, monkeypatch, capsys) -> None:
    root = tmp_path / f"claude-{os.getuid()}"
    session = root / "12345678-1234-1234-1234-123456789abc"
    session.mkdir(parents=True)
    (session / "payload").write_bytes(b"keep")
    lineage = tmp_path / ".agent/thread-rollovers/claude/lineage"
    lineage.mkdir(parents=True)
    (lineage / "lease.json").write_text("[" * 10000 + "]" * 10000)
    monkeypatch.setattr(
        cleanup,
        "sweep_sessions",
        lambda **kwargs: sweep_sessions(root, probe=lambda: ProcessEvidence(complete=True), **kwargs),
    )
    monkeypatch.setattr(
        cleanup,
        "build_receipt",
        lambda *_args, **_kwargs: {"observed_at": "2026-10-03T00:00:00Z", "summary": {"errors": 0}, "repositories": []},
    )
    monkeypatch.setattr(cleanup.home_session_retention_check, "build_report", lambda: {})
    monkeypatch.setattr(cleanup.home_session_retention_check, "warning_lines", lambda _report: [])
    receipts = tmp_path / "receipts"
    assert cleanup.main(["--repo-root", str(tmp_path), "--receipt-dir", str(receipts)]) == 1
    summary = json.loads(capsys.readouterr().out)
    assert summary["summary"]["errors"] == 1
    assert summary["claude_session_scratch"]["kept_by_reason"] == {"unknown_session": 1}
    assert summary["claude_session_scratch"]["would_remove"] == 0
    receipt_files = list(receipts.glob("*.json"))
    assert len(receipt_files) == 1
    receipt = json.loads(receipt_files[0].read_text())
    assert receipt["claude_session_scratch"]["entries"][0]["reason"] == "unreadable_lease_RecursionError"
    assert (session / "payload").read_bytes() == b"keep"


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


def test_scheduled_apply_reports_rescue_candidates(tmp_path: Path, monkeypatch) -> None:
    """Terminal worktrees still on disk are inventoried for rescue, never removed."""
    repo = _repo(tmp_path)
    calls: list[str] = []

    def report(_repo):
        calls.append("rescue")
        return {"summary": {"candidate": 1}, "tasks": [{"task_id": "rescue-test", "action": "report"}]}

    monkeypatch.setattr(cleanup, "report_terminal_worktrees", report)
    monkeypatch.setattr(cleanup, "_worktree_prune", lambda _repo, *, apply: {"ok": True})
    monkeypatch.setattr(cleanup, "cleanup_gone_local_branches", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(cleanup, "cleanup_stale_origin_branches", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(cleanup, "cleanup_untracked_local_branches", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(cleanup, "find_orphaned_worktree_directories", lambda _repo: [])
    monkeypatch.setattr(cleanup, "_git_maintenance", lambda _repo, *, apply: {"ok": True})
    monkeypatch.setattr(cleanup, "sweep_review_temp_orphans", lambda: {"errors": 0})
    monkeypatch.setattr(cleanup, "sweep_tmp_leaks", lambda apply=False: {"errors": 0})

    result = cleanup._repo_result(repo, apply=True)
    assert calls == ["rescue"]
    assert result["rescue"] == {
        "summary": {"candidate": 1},
        "tasks": [{"task_id": "rescue-test", "action": "report"}],
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


def test_runtime_error_marks_repository_run_failed(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = _repo(tmp_path)
    monkeypatch.setattr(
        cleanup,
        "cleanup_stale_origin_branches",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("branch cleanup lock held")),
    )

    result = cleanup._repo_result(repo, apply=True)

    assert result["errors"] == ["branch cleanup lock held"]


def test_stale_worktree_registration_is_pruned(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = _repo(tmp_path)
    branch = "codex/stale-registration"
    worktree = repo / ".worktrees" / "dispatch" / "codex" / "stale-registration"
    _git(repo, "worktree", "add", "-b", branch, str(worktree), "main")
    shutil.rmtree(worktree)
    monkeypatch.setattr(
        cleanup.worktree_git,
        "_query_pr_states",
        lambda *_args, **_kwargs: ([], None),
    )

    result = cleanup._repo_result(repo, apply=True)

    assert result["errors"] == []
    assert result["worktree_prune"]["ok"] is True
    registered = cleanup.worktree_git.list_git_worktrees(repo)
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
        cleanup.worktree_git,
        "_query_pr_states",
        lambda _repo, candidate: (
            [
                cleanup.worktree_git.PullRequestState(
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
        cleanup.worktree_git,
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
        cleanup.worktree_git,
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
                [cleanup.worktree_git.PullRequestState(number=7, state="MERGED", head_sha=tip)],
                None,
            )
        if candidate == on_main:
            return (
                [cleanup.worktree_git.PullRequestState(number=8, state="MERGED", head_sha=tip)],
                None,
            )
        return [], None

    monkeypatch.setattr(cleanup.worktree_git, "_query_pr_states", _prs)

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
        cleanup.worktree_git,
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
        cleanup.worktree_git,
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
        cleanup.worktree_git,
        "_query_pr_states",
        lambda _repo, _branch: (
            [
                cleanup.worktree_git.PullRequestState(
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

    assert result["branches"] == []
    assert result["maintenance"] is None
    assert result["errors"] == ["worktree prune failed; cleanup skipped"]


def test_receipt_aggregates_both_repositories(tmp_path: Path, monkeypatch) -> None:
    public = tmp_path / "public"
    private = tmp_path / "private"

    def fake_repo_result(repo_root: Path, *, apply: bool):
        return {
            "repo_root": str(repo_root),
            "fetch": {"ok": True, "detail": None},
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
        "branches_deleted": 1,
        "origin_branches_deleted": 0,
        "orphans_reported": 1,
        "errors": 0,
        "review_temp_reaped": 0,
        "review_temp_bytes_freed": 0,
        "task_scratch_reaped": 0,
        "task_scratch_bytes_freed": 0,
        "task_scratch_preserved": 0,
    }
    assert receipt["mode"] == "apply"


def _git_env() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_") and not key.startswith("PRE_COMMIT") and key != "AGENT_NO_MERGE"
    }


def _trace_children(payload: bytes) -> list[list[str]]:
    children: list[list[str]] = []
    for line in payload.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        argv = event.get("argv")
        if event.get("event") == "child_start" and isinstance(argv, list):
            children.append([str(part) for part in argv])
    return children


def _maintenance_child(argv: list[str]) -> bool:
    return "maintenance" in argv or argv[1:3] == ["reflog", "expire"] or argv[1:3] == ["gc", "--auto"]


def _arm_auto_maintenance(repo: Path) -> None:
    """Enough loose objects that an ordinary fetch starts ``maintenance run --auto``."""
    _git(repo, "config", "gc.autoDetach", "false")
    _git(repo, "config", "maintenance.autoDetach", "false")
    _git(repo, "config", "gc.auto", "1")
    _git(repo, "config", "gc.autoPackLimit", "1")
    _git(repo, "config", "maintenance.auto", "true")
    env = _git_env()
    for index in range(20):
        proc = subprocess.run(
            ["git", "hash-object", "-w", "--stdin"],
            cwd=repo,
            input=f"loose-{index}-{time.time_ns()}\n",
            text=True,
            capture_output=True,
            check=False,
            env=env,
            timeout=30,
        )
        assert proc.returncode == 0, proc.stderr


def test_hourly_fetch_never_starts_maintenance(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Hourly hygiene never starts GC, including when fetch would trigger it."""
    repo = _repo(tmp_path)
    _arm_auto_maintenance(repo)
    control = tmp_path / "control.trace"
    control_env = _git_env()
    control_env["GIT_TRACE2_EVENT"] = str(control)
    probed = subprocess.run(
        ["git", "fetch", "--prune", "origin"],
        cwd=repo,
        env=control_env,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert probed.returncode == 0, probed.stderr
    assert any(_maintenance_child(argv) for argv in _trace_children(control.read_bytes()))
    _arm_auto_maintenance(repo)

    timeline: list[str] = []
    fetched: list[tuple[str, ...]] = []
    fetch_traces: list[bytes] = []
    trace = tmp_path / "scheduler.trace"
    real_run_git = cleanup._run_git
    monkeypatch.setenv("GIT_TRACE2_EVENT", str(trace))

    def spy_run_git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        if "fetch" in args:
            timeline.append("fetch")
            fetched.append(args)
            if len(fetched) == 1:
                return subprocess.CompletedProcess(
                    args,
                    1,
                    "",
                    "error: cannot lock ref 'refs/remotes/origin/main': is at abc123 but expected def456\n"
                    " ! def456..abc123 main -> origin/main (unable to update local ref)\n"
                    "error: fetching ref refs/remotes/origin/main failed: incorrect old value provided\n",
                )
            before = trace.stat().st_size if trace.exists() else 0
            result = real_run_git(repo_root, *args)
            fetch_traces.append(trace.read_bytes()[before:])
            return result
        if args[:2] == ("gc", "--auto"):
            timeline.append("gc")
        return real_run_git(repo_root, *args)

    monkeypatch.setattr(cleanup, "_run_git", spy_run_git)
    monkeypatch.setattr(cleanup, "_worktree_prune", lambda _repo, *, apply: {"ok": True})
    monkeypatch.setattr(cleanup, "cleanup_gone_local_branches", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(cleanup, "cleanup_stale_origin_branches", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(cleanup, "cleanup_untracked_local_branches", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(cleanup, "find_orphaned_worktree_directories", lambda _repo: [])
    monkeypatch.setattr(cleanup, "sweep_review_temp_orphans", lambda: {"errors": 0})
    monkeypatch.setattr(
        cleanup,
        "sweep_tmp_leaks",
        lambda apply=False: {"errors": 0, "roots_reaped": 0, "bytes_freed": 0, "candidates": 0, "skipped_live": 0},
    )
    monkeypatch.setattr(
        cleanup,
        "recover_task_scratch",
        lambda apply=False: {"errors": 0, "candidates": 0, "reaped": 0, "bytes_freed": 0, "preserved": 0},
    )

    result = cleanup._repo_result(repo, apply=True)

    assert timeline == ["fetch", "fetch", "fetch"]
    assert fetched == [("-c", "maintenance.auto=false", "-c", "gc.auto=0", "fetch", "--prune", "origin")] * 3
    assert result["fetch"]["ok"] is True
    assert fetch_traces and not any(_maintenance_child(argv) for blob in fetch_traces for argv in _trace_children(blob))
    assert result["maintenance"]["action"] == "scheduled_separately"
    assert result["maintenance"]["ok"] is True


def test_git_maintenance_failure_is_reported(tmp_path: Path, monkeypatch) -> None:
    repo = _repo(tmp_path)
    monkeypatch.setattr(cleanup, "_git_maintenance", lambda _repo, *, apply: {
        "action": "ran", "ok": False, "detail": "gc failed",
    })
    result = cleanup._maintenance_repo_result(repo, apply=True)
    assert result["errors"] == ["git maintenance failed: gc failed"]


def _maintenance_repo(tmp_path: Path, monkeypatch) -> Path:
    repo = _repo(tmp_path)
    _git(repo, "config", "gc.auto", "0")
    _git(repo, "config", "maintenance.auto", "false")
    _git(repo, "config", "gc.autoDetach", "true")
    monkeypatch.setattr(cleanup, "_maintenance_limits", lambda: {
        "memory": 2 * 1024**3, "swap": 0, "cpu": 1, "tasks": 32,
    })
    return repo


def _pack_threshold(repo: Path) -> None:
    # More than Git's default autoPackLimit, all reachable and nonempty.
    for index in range(52):
        (repo / f"object-{index}").write_text(f"reachable object {index}\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "pack input")
    objects = _git(repo, "rev-list", "--objects", "--all").splitlines()
    for row in objects:
        subprocess.run(
            [cleanup.GIT, "pack-objects", str(repo / ".git/objects/pack/pack")],
            cwd=repo, input=row.split()[0] + "\n", text=True, capture_output=True,
            check=True, env=_git_env(), timeout=30,
        )


@pytest.mark.parametrize("lock_name,mode", [
    ("lu-pre-push-gate/admission.lock", "shared"),
    ("lu-pre-push-gate/admission.lock", "exclusive"),
    ("scheduled-git-hygiene.lock", "exclusive"),
])
def test_maintenance_defers_for_live_validation_and_maintenance(tmp_path: Path, monkeypatch, lock_name, mode) -> None:
    """A second process excludes maintenance through existing SH/EX admission or hygiene locks."""
    repo = _maintenance_repo(tmp_path, monkeypatch)
    lock = repo / ".git" / lock_name
    lock.parent.mkdir(exist_ok=True)
    holder = subprocess.Popen(
        [sys.executable, "-c",
         "import fcntl,sys; f=open(sys.argv[1], 'a+'); "
         "fcntl.flock(f, fcntl.LOCK_SH if sys.argv[2]=='shared' else fcntl.LOCK_EX); "
         "print('ready', flush=True); sys.stdin.readline()", str(lock), mode],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
    )
    try:
        assert holder.stdout.readline().strip() == "ready"
        result = cleanup._git_maintenance(repo, apply=True)
        assert result["action"] == "deferred", result
        assert result["ok"] is True
        assert not (repo / ".git/gc.pid").exists()
    finally:
        holder.communicate("release\n", timeout=10)
    assert holder.returncode == 0
    result = cleanup._git_maintenance(repo, apply=True)
    assert result["ok"] is True, result
    assert result["changed"] is False


def test_foreground_maintenance_preserves_objects_and_holds_admission_in_git_tree(tmp_path: Path, monkeypatch) -> None:
    """Real repack cannot bypass admission, detach, or lose refs, staged objects or active worktrees."""
    repo = _maintenance_repo(tmp_path, monkeypatch)
    _pack_threshold(repo)
    active = tmp_path / "active"
    _git(repo, "worktree", "add", "-b", "active", str(active))
    (active / "README.md").write_text("uncommitted learner work\n")
    _git(active, "add", "README.md")
    staged = _git(active, "rev-parse", ":README.md")
    refs = _git(repo, "show-ref")
    objects = _git(repo, "rev-list", "--objects", "--all")
    worktrees = _git(repo, "worktree", "list", "--porcelain")
    incident = repo / ".git/objects/pack/tmp_pack_incident"
    incident.write_bytes(b"preserve incident evidence")
    probe = tmp_path / "admission-proof"
    lock = repo / ".git/lu-pre-push-gate/admission.lock"
    hook = repo / ".git/hooks/pre-auto-gc"
    hook.write_text(
        f"#!{sys.executable}\nimport fcntl, os\n"
        f"lock = {str(lock)!r}\nf = open(lock, 'r+')\n"
        "try:\n fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)\n"
        "except BlockingIOError:\n"
        f" open({str(probe)!r}, 'w').write('excluded')\n"
        "else:\n raise SystemExit('GC bypassed validation admission')\n"
    )
    hook.chmod(0o700)
    trace = tmp_path / "gc.trace"
    monkeypatch.setenv("GIT_TRACE2_EVENT", str(trace))
    monkeypatch.setenv("GIT_TRACE2_CONFIG_PARAMS", "pack.threads,pack.windowMemory,pack.deltaCacheSize,gc.autoDetach")
    result = cleanup._git_maintenance(repo, apply=True)
    assert result["ok"] is True, result
    assert result["changed"] is True
    assert probe.read_text() == "excluded"
    assert _git(repo, "count-objects", "-v").split("packs: ")[1].splitlines()[0] == "1"
    assert _git(repo, "show-ref") == refs
    assert _git(repo, "rev-list", "--objects", "--all") == objects
    assert _git(repo, "worktree", "list", "--porcelain") == worktrees
    _git(repo, "cat-file", "-e", staged)
    assert "error:" not in _git(repo, "fsck", "--full")
    assert (active / "README.md").read_text() == "uncommitted learner work\n"
    assert incident.read_bytes() == b"preserve incident evidence"
    events = [json.loads(line) for line in trace.read_text().splitlines()]
    params = {(e.get("param"), e.get("value")) for e in events if e.get("event") == "def_param"}
    assert {("pack.threads", "1"), ("pack.windowmemory", "64m"), ("pack.deltacachesize", "64m"), ("gc.autodetach", "false")} <= params
    assert any("pack-objects" in child for child in _trace_children(trace.read_bytes()))
    assert _git(repo, "config", "gc.auto") == "0"
    assert _git(repo, "config", "maintenance.auto") == "false"


def test_maintenance_refuses_unbounded_and_automatic_paths_and_writes_receipt(tmp_path: Path, monkeypatch, capsys) -> None:
    """Unknown cgroups or ordinary auto-GC never silently publish successful maintenance."""
    repo = _maintenance_repo(tmp_path, monkeypatch)
    monkeypatch.setattr(cleanup, "_maintenance_limits", lambda: None)
    receipt_dir = tmp_path / "receipts"
    assert cleanup.main(["--repo-root", str(repo), "--git-maintenance", "--apply", "--receipt-dir", str(receipt_dir)]) == 1
    receipt = json.loads(next(receipt_dir.glob("*.json")).read_text())
    assert receipt["repositories"][0]["maintenance"]["action"] == "refused_unbounded"
    assert json.loads(capsys.readouterr().out)["summary"]["errors"] == 1
    monkeypatch.setattr(cleanup, "_maintenance_limits", lambda: {"memory": 2**31, "swap": 0, "tasks": 32, "cpu": 1})
    _git(repo, "config", "maintenance.auto", "true")
    assert cleanup._git_maintenance(repo, apply=True)["action"] == "refused_automatic"
    _git(repo, "config", "maintenance.auto", "false")
    assert cleanup._git_maintenance(repo, apply=True)["ok"] is True


@pytest.mark.parametrize("escaped", [False, True])
def test_maintenance_timeout_terminates_git_tree_and_recovers(tmp_path: Path, monkeypatch, escaped: bool) -> None:
    """Timeout cleanup removes real Git ref locks; escaped pipe holders report GC failure truthfully."""
    repo = _maintenance_repo(tmp_path, monkeypatch)
    _pack_threshold(repo)
    refs = _git(repo, "show-ref")
    hook = repo / ".git/hooks/pre-auto-gc"
    pid_path = tmp_path / "hook.pid"
    hook.write_text(f"#!/bin/sh\nexec {cleanup.GIT} update-ref refs/heads/main HEAD^\n")
    transaction_hook = repo / ".git/hooks/reference-transaction"
    transaction_hook.write_text(
        f"#!{sys.executable}\nimport os, signal, sys, time\nfrom pathlib import Path\n"
        "if sys.argv[1] != 'prepared': raise SystemExit(0)\n"
        "def delay_term(*args):\n os.close(1)\n os.close(2)\n time.sleep(30)\n"
        f"if {escaped!r}: os.setsid()\n"
        "signal.signal(signal.SIGTERM, delay_term)\n"
        f"Path({str(pid_path)!r}).write_text(str(os.getpid()))\nsignal.pause()\n"
    )
    hook.chmod(0o700)
    transaction_hook.chmod(0o700)
    monkeypatch.setattr(cleanup, "GC_DEADLINE_SECONDS", 0.5)
    try:
        receipt = cleanup.build_receipt([repo], apply=True, git_maintenance=True)
    finally:
        if escaped and pid_path.exists():
            with contextlib.suppress(ProcessLookupError):
                os.kill(int(pid_path.read_text()), signal.SIGKILL)
    assert receipt["repositories"][0]["maintenance"]["action"] == "timeout"
    assert receipt["summary"]["errors"] == 1
    detail = receipt["repositories"][0]["maintenance"]["detail"]
    assert "SIGTERM" in detail and "SIGKILL" in detail
    assert ("output pipes remain open" in detail) is escaped
    pid = int(pid_path.read_text())
    stat_path = Path(f"/proc/{pid}/stat")
    deadline = time.monotonic() + 5
    while True:
        try:
            state = stat_path.read_text().split(") ", 1)[1][0]
        except (FileNotFoundError, ProcessLookupError):  # a task that exits mid-read raises ESRCH
            state = None
        if state in {None, "Z"}:
            break
        assert time.monotonic() < deadline, f"GC child survived timeout: {state}"
        time.sleep(0.01)
    hook.write_text("#!/bin/sh\nexit 0\n")
    transaction_hook.write_text("#!/bin/sh\nexit 0\n")
    assert not (repo / ".git/refs/heads/main.lock").exists()
    assert _git(repo, "show-ref") == refs
    # A real ref write fails here if timeout cleanup stranded Git's lock.
    _git(repo, "update-ref", "refs/heads/main", "HEAD")
    monkeypatch.setattr(cleanup, "GC_DEADLINE_SECONDS", 30)
    result = cleanup._git_maintenance(repo, apply=True)
    assert result["ok"] is True, result
    assert result["changed"] is True
    assert _git(repo, "show-ref") == refs
    assert "error:" not in _git(repo, "fsck", "--full")


@pytest.mark.parametrize("memory,swap,tasks,cpu,expected", [
    ("2147483648", "0", "32", "100000 100000", True),
    ("max", "0", "32", "100000 100000", False),
    ("2147483648", "max", "32", "100000 100000", False),
    ("2147483648", "0", "max", "100000 100000", False),
    ("2147483648", "0", "32", "max 100000", False),
    ("garbled", "0", "32", "100000 100000", False),
    ("3221225472", "0", "32", "100000 100000", False),
    ("2147483648", "0", "64", "100000 100000", False),
    ("2147483648", "0", "32", "200000 100000", False),
    (None, "0", "32", "100000 100000", False),
])
def test_maintenance_requires_effective_kernel_bounds(tmp_path: Path, monkeypatch, memory, swap, tasks, cpu, expected) -> None:
    """Missing, unlimited and malformed controller limits cannot admit a repack."""
    root = tmp_path / "cgroup"
    group = root / "maintenance"
    group.mkdir(parents=True)
    for name, value in {"memory.max": memory, "memory.swap.max": swap, "pids.max": tasks, "cpu.max": cpu}.items():
        if value is not None:
            (group / name).write_text(value)
    proc = tmp_path / "self-cgroup"
    proc.write_text("0::/maintenance\n")
    monkeypatch.setattr(cleanup, "CGROUP_ROOT", root)
    monkeypatch.setattr(cleanup, "SELF_CGROUP", proc)
    assert (cleanup._maintenance_limits() is not None) is expected


def test_maintenance_uses_stricter_ancestor_limits(tmp_path: Path, monkeypatch) -> None:
    """An unlimited leaf can run only when every resource is bounded by an ancestor."""
    root = tmp_path / "cgroup"
    parent = root / "bounded"
    leaf = parent / "leaf"
    leaf.mkdir(parents=True)
    for name, limit in {"memory.max": "2147483648", "memory.swap.max": "0", "pids.max": "32", "cpu.max": "100000 100000"}.items():
        (parent / name).write_text(limit)
        (leaf / name).write_text("max 100000" if name == "cpu.max" else "max")
    proc = tmp_path / "self-cgroup"
    proc.write_text("0::/bounded/leaf\n")
    monkeypatch.setattr(cleanup, "CGROUP_ROOT", root)
    monkeypatch.setattr(cleanup, "SELF_CGROUP", proc)
    assert cleanup._maintenance_limits() == {"memory": 2147483648, "swap": 0, "tasks": 32, "cpu": 1}


def test_metadata_query_timeout_does_not_claim_gc_was_killed(tmp_path: Path, monkeypatch) -> None:
    """Failure before GC must describe the metadata timeout rather than invented GC termination."""
    repo = _maintenance_repo(tmp_path, monkeypatch)
    real_run = cleanup._run_git

    def slow_metadata(root, *args):
        if args[0] == "count-objects":
            raise subprocess.TimeoutExpired("git count-objects", 120)
        return real_run(root, *args)

    monkeypatch.setattr(cleanup, "_run_git", slow_metadata)
    result = cleanup._git_maintenance(repo, apply=True)
    assert result == {"action": "timeout", "ok": False, "detail": "Git metadata query exceeded its timeout"}


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
                cleanup.worktree_git.PullRequestState(
                    number=77,
                    state="MERGED",
                    head_sha=head_sha,
                )
            ],
            None,
        )

    monkeypatch.setattr(cleanup.worktree_git, "_query_pr_states", _prs)

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


def _closed_pr(number: int, head_sha: str) -> cleanup.worktree_git.PullRequestState:
    return cleanup.worktree_git.PullRequestState(
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
        cleanup.worktree_git,
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
        cleanup.worktree_git,
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
        cleanup.worktree_git,
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
        cleanup.worktree_git,
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
        cleanup.worktree_git,
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
        cleanup.worktree_git,
        "_query_pr_states",
        lambda _repo, _branch: ([], None),
    )

    result = cleanup.cleanup_untracked_local_branches(repo, apply=True)

    row = next(item for item in result if item["branch"] == "rescue/x")
    assert row["action"] == "skipped"
    assert "agent scratch ref" in row["reason"]
    assert "tip not contained" in row["reason"]
    assert _git(repo, "branch", "--list", "rescue/x") != ""


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
        cleanup.worktree_git,
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
        cleanup.worktree_git,
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
        cleanup.worktree_git,
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
        cleanup.worktree_git,
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
        cleanup.worktree_git,
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
        cleanup.worktree_git,
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
    monkeypatch.setattr(cleanup.worktree_git, "_live_cwd_paths", lambda _repo: set())
    monkeypatch.setattr(
        cleanup.worktree_git,
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

    # The same fail-closed result applies to mixed diagnostics and a failed
    # retry. Returning a successful local ref lookup would hide the fetch error.
    args = ("-c", "maintenance.auto=false", "-c", "gc.auto=0", "fetch", "--prune", "origin")
    race = "error: fetching ref refs/remotes/origin/main failed: incorrect old value provided\n"
    failed = subprocess.CompletedProcess(args, 1, "", "fatal: ordinary fetch failure\n")
    for diagnostic in (
        failed.stderr,
        race + failed.stderr,
        race + "remote: error: remote failure\n",
        race + " ! [rejected] other -> origin/other (non-fast-forward)\n",
        race.replace("origin/main", "origin/other"),
        "",
    ):
        mixed = subprocess.CompletedProcess(args, 1, "", diagnostic)
        with patch.object(cleanup, "_run_git", return_value=mixed) as fetch:
            assert cleanup._fetch_origin(repo) is mixed
            fetch.assert_called_once_with(repo, *args)
    for diagnostic in (
        race,
        "error: cannot lock ref 'refs/remotes/origin/main': is at abc123 but expected def456\n",
    ):
        with patch.object(
            cleanup, "_run_git", side_effect=[subprocess.CompletedProcess(args, 1, "", diagnostic), failed]
        ) as fetch:
            assert cleanup._fetch_origin(repo) is failed
            assert fetch.call_count == 2
            assert all(call.args == (repo, *args) for call in fetch.call_args_list)


def test_origin_scratch_ref_is_not_deleted_for_containing_itself(tmp_path: Path, monkeypatch) -> None:
    repo = _repo(tmp_path)
    _git(repo, "checkout", "-b", "rescue/only-here")
    (repo / "only.txt").write_text("remote only\n", encoding="utf-8")
    _git(repo, "add", "only.txt")
    _git(repo, "commit", "-m", "only on this remote ref")
    _git(repo, "push", "-u", "origin", "rescue/only-here")
    _git(repo, "checkout", "main")
    monkeypatch.setattr(
        cleanup.worktree_git,
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
        cleanup.worktree_git,
        "_query_pr_states",
        lambda _repo, _branch: ([], None),
    )
    monkeypatch.setattr(
        cleanup,
        "_query_pr_by_number",
        lambda _repo, number: (
            [
                cleanup.worktree_git.PullRequestState(
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
        cleanup.worktree_git,
        "_query_pr_states",
        lambda _repo, _branch: ([], None),
    )
    monkeypatch.setattr(
        cleanup,
        "_query_pr_by_number",
        lambda _repo, number: (
            [
                cleanup.worktree_git.PullRequestState(
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
        cleanup.worktree_git,
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
        cleanup.worktree_git,
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
        cleanup.worktree_git,
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

    from scripts.review.isolation import REVIEW_TEMP_ROOT_MANIFEST_NAME, _write_review_temp_root_marker

    root = Path(tempfile.mkdtemp(prefix="lu-review-snap-", dir=tmp_base))
    _write_review_temp_root_marker(root, prefix="lu-review-snap-")
    manifest_path = root / REVIEW_TEMP_ROOT_MANIFEST_NAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["owner_pid"] = 999999
    manifest["created_at_epoch"] = 1000.0
    manifest_path.chmod(0o600)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    monkeypatch.setattr(
        cleanup.worktree_git,
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


def test_build_public_summary_zero_path_dumps(tmp_path: Path) -> None:
    receipt = {
        "schema_version": cleanup.SCHEMA_VERSION,
        "observed_at": "2026-09-06T20:00:00Z",
        "mode": "dry_run",
        "summary": {
            "repositories": 2,
            "branches_deleted": 1,
            "origin_branches_deleted": 0,
            "orphans_reported": 0,
            "errors": 0,
            "review_temp_reaped": 0,
            "review_temp_bytes_freed": 0,
        },
        "repositories": [
            {
                "repo_root": "/home/secret/host/learn-ukrainian",
                "branches": [{"branch": "codex/t1", "action": "deleted", "reason": "merged"}],
                "origin_branches": [],
                "orphans": [],
                "errors": [],
            },
            {
                "repo_root": "/home/secret/host/learn-ukrainian-infra-private",
                "branches": [],
                "origin_branches": [],
                "orphans": [
                    {
                        "path": "/home/secret/host/learn-ukrainian-infra-private/.worktrees/dispatch/claude/t2",
                        "reason": "unregistered worktree with missing gitdir",
                    },
                ],
                "errors": ["permission denied"],
            },
        ],
    }

    receipt_path = Path("/home/secret/state/receipts/v2/20260906T200000Z-abcdef123456.json")
    public = cleanup.build_public_summary(receipt, receipt_path)

    assert public["receipt_id"] == "20260906T200000Z-abcdef123456.json"
    assert "learn-ukrainian" in public["repositories"]
    assert "learn-ukrainian-infra-private" in public["repositories"]
    assert public["summary"]["branches_deleted"] == 1
    assert public["repositories"]["learn-ukrainian"]["branches_deleted"] == 1
    assert public["repositories"]["learn-ukrainian-infra-private"]["orphans_reported"] == 1
    assert public["repositories"]["learn-ukrainian-infra-private"]["errors"] == 1

    # Verify zero host paths dumped anywhere
    dumped = json.dumps(public)
    assert "/home/secret" not in dumped
    assert ".worktrees" not in dumped
    assert "t1" not in dumped
    assert "t2" not in dumped


def _stub_repo_hooks(monkeypatch, *, leak_sweep_calls: list[bool]) -> None:
    monkeypatch.setattr(cleanup, "_worktree_prune", lambda _repo, *, apply: {"ok": True})
    monkeypatch.setattr(cleanup.worktree_git, "_live_cwd_paths", lambda _repo: set())
    monkeypatch.setattr(cleanup, "cleanup_gone_local_branches", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(cleanup, "cleanup_stale_origin_branches", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(cleanup, "cleanup_untracked_local_branches", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(cleanup, "find_orphaned_worktree_directories", lambda _repo: [])
    monkeypatch.setattr(cleanup, "_git_maintenance", lambda _repo, *, apply: {"ok": True})
    monkeypatch.setattr(cleanup, "sweep_review_temp_orphans", lambda: {"errors": 0})
    monkeypatch.setattr(
        cleanup,
        "sweep_tmp_leaks",
        lambda apply=False: (
            leak_sweep_calls.append(apply)
            or {"errors": 0, "roots_reaped": 0, "bytes_freed": 0, "candidates": 0, "skipped_live": 0}
        ),
    )


def _plant_dead_orphan(root: Path, *, age_s: float) -> Path:
    """Allocate a lease whose owner is a fake dead pid and age it."""
    scratch = task_scratch.allocate("8738-orphan", root=root)
    (scratch.payload_dir / "atlas.db").write_bytes(b"x" * 4096)
    scratch.lease["owner"] = {"pid": 2_000_000_000, "start_time": 1, "boot_id": scratch.lease["owner"]["boot_id"]}
    task_scratch._write_lease_at(scratch._dir_fd, scratch.lease)
    scratch.preserve()
    past = time.time() - age_s
    for path in [scratch.path, *scratch.path.rglob("*")]:
        os.utime(path, (past, past))
    return scratch.path


def test_scheduled_dry_run_reports_task_scratch_without_mutation(tmp_path: Path, monkeypatch) -> None:
    root = Path(os.environ["LU_SCRATCH_ROOT"])
    orphan = _plant_dead_orphan(root, age_s=10 * 3600)
    repo = _repo(tmp_path)
    calls: list[bool] = []
    _stub_repo_hooks(monkeypatch, leak_sweep_calls=calls)

    result = cleanup._repo_result(repo, apply=False)

    assert orphan.is_dir()
    recovery = result["task_scratch_recovery"]
    assert recovery["candidates"] == 1
    assert recovery["reaped"] == 0
    assert recovery["errors"] == 0
    assert "entries" not in recovery
    assert str(orphan) not in json.dumps(result["task_scratch_recovery"])


def test_scheduled_apply_reclaims_proven_orphan_and_reports_counts_only(tmp_path: Path, monkeypatch) -> None:
    root = Path(os.environ["LU_SCRATCH_ROOT"])
    orphan = _plant_dead_orphan(root, age_s=10 * 3600)
    live = task_scratch.allocate("8738-live", root=root)  # lock held: must be preserved
    repo = _repo(tmp_path)
    calls: list[bool] = []
    _stub_repo_hooks(monkeypatch, leak_sweep_calls=calls)
    try:
        result = cleanup._repo_result(repo, apply=True)
    finally:
        live.preserve()

    assert not orphan.exists()
    assert live.path.is_dir()
    recovery = result["task_scratch_recovery"]
    assert recovery["reaped"] == 1
    assert recovery["bytes_freed"] >= 4096
    assert recovery["preserved_by_reason"] == {"in_use": 1}
    assert recovery["errors"] == 0
    assert result["errors"] == []

    receipt = cleanup.build_receipt([repo], apply=True, observed_at="2026-09-24T20:00:00Z")
    public = cleanup.build_public_summary(receipt, None)
    assert public["summary"]["task_scratch_reaped"] == 0  # second pass: already reclaimed
    serialized = json.dumps(public)
    assert str(root) not in serialized
    assert "8738-orphan" not in serialized


def test_scheduled_recovery_failure_is_reported_not_fatal(tmp_path: Path, monkeypatch) -> None:
    repo = _repo(tmp_path)
    calls: list[bool] = []
    _stub_repo_hooks(monkeypatch, leak_sweep_calls=calls)

    def boom(*, apply: bool):
        raise RuntimeError("namespace exploded")

    monkeypatch.setattr(cleanup, "recover_task_scratch", boom)
    result = cleanup._repo_result(repo, apply=False)
    assert any("task scratch recovery failed" in error for error in result["errors"])
    assert "task_scratch_recovery" not in result


def test_origin_branch_deleted_by_someone_else_is_already_absent_not_an_error(tmp_path: Path, monkeypatch) -> None:
    repo = _repo(tmp_path)
    branch = "gh-readonly-queue/main/pr-1-abc"
    _git(repo, "branch", branch, "main")
    _git(repo, "push", "origin", branch)
    head_sha = _git(repo, "rev-parse", branch)

    def _prs(_repo: Path, candidate: str | None):
        if candidate != branch:
            return [], None
        # The merge queue drops its temporary branch while cleanup is running.
        _git(tmp_path / "origin.git", "update-ref", "-d", f"refs/heads/{branch}")
        return (
            [cleanup.worktree_git.PullRequestState(number=1, state="MERGED", head_sha=head_sha)],
            None,
        )

    monkeypatch.setattr(cleanup.worktree_git, "_query_pr_states", _prs)

    rows = cleanup.cleanup_stale_origin_branches(repo, apply=True)

    row = next(item for item in rows if item["branch"] == branch)
    assert row["action"] == "already_absent"
    assert row["error"] is None


@pytest.fixture
def rescue_repo(tmp_path: Path, monkeypatch):
    repo = _repo(tmp_path)
    worktree = repo / ".worktrees" / "dispatch" / "test" / "terminal"
    _git(repo, "worktree", "add", "-b", "test/terminal", str(worktree))
    tasks = repo / "batch_state" / "tasks"
    tasks.mkdir(parents=True)
    monkeypatch.setattr(cleanup.worktree_git, "control_plane_root", lambda _repo: repo)
    return repo, worktree, tasks


@pytest.mark.parametrize("schema", [1, 2])
@pytest.mark.parametrize("case", ["dirty", "unpushed", "clean", "running", "recent", "missing"])
def test_terminal_report_filters_and_never_writes(rescue_repo, schema: int, case: str, monkeypatch) -> None:
    """Defect classes: lost terminal work, active/recent false positives, and rescue writes."""
    repo, worktree, tasks = rescue_repo
    if case == "unpushed":
        (worktree / "README.md").write_text("unpublished commit\n")
        _git(worktree, "commit", "-am", "unpublished")
    if case in {"dirty", "running", "recent"}:
        (worktree / "README.md").write_text("uncommitted\n")
        (worktree / "new.txt").write_text("untracked\n")
    record = {
        "schema_version": schema,
        "task_id": "terminal",
        "status": "running" if case == "running" else "failed",
        "finished_at": (datetime.now(UTC) - timedelta(hours=5 if case == "recent" else 7)).isoformat(),
        "worktree_branch": "test/terminal",
        "worktree_path": str(worktree),
    }
    if case == "missing":
        record["finished_at"] = None
    directory = tasks if schema == 2 else tasks / "archive"
    directory.mkdir(exist_ok=True)
    task_file = directory / "terminal.json"
    task_file.write_text(json.dumps(record))
    if case == "missing":
        _git(repo, "worktree", "remove", str(worktree))
    calls = []
    real_git = cleanup.safe_git

    def inspect(args, **kwargs):
        calls.append(args[0])
        return real_git(args, **kwargs)

    monkeypatch.setattr(cleanup, "safe_git", inspect)
    before_refs = _git(repo, "show-ref")
    before_status = _git(repo, "status", "--porcelain", "--untracked-files=all")
    before_record = task_file.read_bytes()
    before_work = _git(worktree, "status", "--porcelain") if worktree.exists() else None
    monkeypatch.setenv("GIT_DIR", str(tasks))
    report = cleanup.report_terminal_worktrees(repo)
    expected = case in {"dirty", "unpushed"}
    assert report["summary"]["candidate"] == int(expected)
    if expected:
        (row,) = report["tasks"]
        assert row == {
            "task_id": "terminal",
            "action": "report",
            "branch": "test/terminal",
            "worktree_path": ".worktrees/dispatch/test/terminal",
            "dirty": 2 if case == "dirty" else 0,
            "unpushed": int(case == "unpushed"),
            "age_seconds": row["age_seconds"],
        }
        assert 7 * 3600 <= row["age_seconds"] < 8 * 3600
    else:
        assert report["tasks"] == []
    assert set(calls) <= {"status", "rev-list", "rev-parse"}
    assert _git(repo, "show-ref") == before_refs
    assert _git(repo, "status", "--porcelain", "--untracked-files=all") == before_status
    assert task_file.read_bytes() == before_record
    if before_work is not None:
        assert _git(worktree, "status", "--porcelain") == before_work
        if case == "dirty":
            assert (worktree / "README.md").read_text() == "uncommitted\n"
            assert (worktree / "new.txt").read_text() == "untracked\n"


@pytest.mark.parametrize("status", ["done", "dry_run"])
@pytest.mark.parametrize("archived", [False, True])
def test_terminal_record_without_worktree_is_skipped(rescue_repo, monkeypatch, status: str, archived: bool) -> None:
    repo, _worktree, tasks = rescue_repo
    directory = tasks / "archive" if archived else tasks
    directory.mkdir(exist_ok=True)
    (directory / "no-worktree.json").write_text(
        json.dumps({"status": status, "finished_at": None, "worktree_path": None, "cwd": str(repo)})
    )
    monkeypatch.setattr(cleanup.worktree_git, "_live_cwd_paths", lambda _repo: set())
    result = cleanup._repo_result(repo, apply=True)
    assert result["errors"] == []
    assert result["rescue"] == {"summary": {"candidate": 0}, "tasks": []}


@pytest.mark.parametrize("failure", ["json", "recursion", "path_type", "read", "git", "finished_at"])
def test_rescue_read_errors_reach_caller_without_crashing(rescue_repo, monkeypatch, failure: str) -> None:
    """Defect classes: unreadable records, failed Git probes, and suppressed unknown finish metadata on real targets."""
    repo, worktree, tasks = rescue_repo
    task = tasks / "broken.json"
    task.write_text(
        "{"
        if failure == "json"
        else json.dumps(
            {
                "status": "failed",
                "finished_at": None if failure == "finished_at" else "2000-01-01T00:00:00Z",
                "worktree_path": 42 if failure == "path_type" else str(worktree),
            }
        )
    )
    if failure == "finished_at":
        companion = tasks / "stale.json"
        companion.write_text(json.dumps({"status": "failed", "finished_at": None, "worktree_path": None}))
        before_task = task.read_bytes()
        before_companion = companion.read_bytes()
    if failure == "recursion":
        task.write_text("[" * 10000 + "]" * 10000)
    if failure == "read":
        real_read = Path.read_text

        def read(path, *args, **kwargs):
            if path == task:
                raise PermissionError("synthetic read refusal")
            return real_read(path, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", read)
    if failure == "git":
        monkeypatch.setattr(cleanup, "safe_git", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError()))
    monkeypatch.setattr(cleanup.worktree_git, "_live_cwd_paths", lambda _repo: set())
    result = cleanup._repo_result(repo, apply=True)
    (row,) = result["rescue"]["tasks"]
    assert row["action"] == "error"
    assert row["error"] in result["errors"]
    assert result["rescue"]["summary"] == {"candidate": 0}
    if failure == "finished_at":
        assert row["task_id"] == "broken"
        assert result["errors"] == [row["error"]]
        assert task.read_bytes() == before_task
        assert companion.read_bytes() == before_companion
        assert worktree.exists()


@pytest.mark.parametrize("mode", ["apply", "dry_run", "disabled"])
def test_caller_reports_without_delegate_script(rescue_repo, monkeypatch, mode: str) -> None:
    """Defect classes: dependency on deleted delegate and bypass of the reaper kill switch."""
    repo, worktree, tasks = rescue_repo
    (worktree / "README.md").write_text("uncommitted\n")
    (tasks / "terminal.json").write_text(
        json.dumps(
            {
                "task_id": "terminal",
                "status": "done",
                "finished_at": "2000-01-01T00:00:00Z",
                "worktree_path": str(worktree.relative_to(repo)),
            }
        )
    )
    monkeypatch.setenv("LU_REAPER_DISABLED", "1" if mode == "disabled" else "0")
    monkeypatch.setattr(cleanup.worktree_git, "_live_cwd_paths", lambda _repo: set())
    result = cleanup._repo_result(repo, apply=mode != "dry_run")
    assert result["errors"] == []
    assert (worktree / "README.md").read_text() == "uncommitted\n"
    if mode == "apply":
        assert result["rescue"]["summary"] == {"candidate": 1}
    else:
        assert result["rescue"] is None


def test_systemd_timer_does_not_leave_both_root_cleanup_on_four_hour_cadence() -> None:
    """A slow or randomized timer leaves eligible resources past the hourly sweep."""
    import configparser

    packaging = Path(__file__).resolve().parents[2] / "packaging" / "systemd"
    timer = configparser.ConfigParser()
    timer.read(packaging / "learn-ukrainian-worktree-gc.timer")
    assert timer["Timer"]["OnCalendar"] == "hourly"
    assert timer["Timer"].get("RandomizedDelaySec", "0") == "0"
    assert "OnUnitActiveSec" not in timer["Timer"]
    assert timer["Timer"]["OnBootSec"] == "15min"
    assert timer["Timer"]["Persistent"] == "true"
    assert timer["Timer"]["Unit"] == "learn-ukrainian-worktree-gc.service"
    service = configparser.ConfigParser()
    service.read(packaging / "learn-ukrainian-worktree-gc.service")
    assert service["Service"]["ExecStart"].split() == [
        "/usr/bin/env",
        "bash",
        "@REPO_ROOT@/scripts/orchestration/run_scheduled_worktree_cleanup.sh",
        "--repo-root",
        "@REPO_ROOT@",
        "--repo-root",
        "@PRIVATE_ROOT@",
        "--apply",
    ]
