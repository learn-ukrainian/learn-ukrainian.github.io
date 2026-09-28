"""Branch deletion contract using local repositories and injected PR evidence."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts.hygiene import branch_sweep as sweep
from scripts.orchestration.reap_worktrees import PullRequestState


def git(repo: Path, *args: str) -> str:
    # Fixture seeding pushes main to a disposable bare origin; the host's
    # production pre-push hook correctly forbids agents pushing real main.
    command = ["git", "-c", "core.hooksPath=/dev/null", *args] if args[0] == "push" else ["git", *args]
    result = subprocess.run(command, cwd=repo, capture_output=True, text=True, check=False, timeout=30)
    assert result.returncode == 0, f"git {args[0]} failed: {result.stderr}"
    return result.stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    remote = tmp_path / "origin.git"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True, timeout=30)
    root = tmp_path / "checkout"
    root.mkdir()
    git(root, "init", "-b", "main")
    git(root, "config", "user.name", "Test")
    git(root, "config", "user.email", "test@example.invalid")
    (root / "readme").write_text("base\n")
    git(root, "add", "readme")
    git(root, "commit", "-m", "base")
    git(root, "remote", "add", "origin", str(remote))
    git(root, "push", "-u", "origin", "main")
    return root


def branch(repo: Path, name: str, *, unique: bool = False, remote: bool = True) -> str:
    git(repo, "branch", name, "main")
    if unique:
        parent = git(repo, "rev-parse", "main")
        tree = git(repo, "rev-parse", "main^{tree}")
        new_head = git(repo, "commit-tree", tree, "-p", parent, "-m", name)
        git(repo, "update-ref", f"refs/heads/{name}", new_head)
    sha = git(repo, "rev-parse", f"refs/heads/{name}")
    if remote:
        git(repo, "push", "origin", name)
    return sha


def lookup(states: dict[str, list[PullRequestState]] | None = None, error: str | None = None):
    states = states or {}
    return lambda _repo, name: (states.get(name, []), error)


def only(repo: Path, name: str, *, apply: bool = False, states=None, error=None) -> sweep.Decision:
    return next(item for item in sweep.sweep(
        repo, apply=apply, pr_lookup=lookup(states, error), protected_lookup=lambda _repo: set(),
    ) if item.branch == name)


def test_open_pr_is_never_deleted(repo: Path) -> None:
    sha = branch(repo, "codex/open", unique=True)
    item = only(repo, "codex/open", apply=True, states={"codex/open": [PullRequestState(1, "OPEN", sha)]})
    assert item.classification == "skipped-open-PR"
    assert git(repo, "ls-remote", "--heads", "origin", "codex/open")


def test_registered_worktree_is_never_deleted(repo: Path, tmp_path: Path) -> None:
    branch(repo, "claude/checked-out")
    git(repo, "worktree", "add", str(tmp_path / "other"), "claude/checked-out")
    item = only(repo, "claude/checked-out", apply=True)
    assert item.classification == "skipped-worktree"
    assert git(repo, "ls-remote", "--heads", "origin", "claude/checked-out")


def test_detached_worktree_at_tip_is_never_deleted(repo: Path, tmp_path: Path) -> None:
    sha = branch(repo, "claude/detached")
    git(repo, "worktree", "add", "--detach", str(tmp_path / "detached"), sha)
    item = only(repo, "claude/detached", apply=True)
    assert item.classification == "skipped-worktree"
    assert git(repo, "ls-remote", "--heads", "origin", "claude/detached")


def test_running_task_is_never_deleted(repo: Path) -> None:
    branch(repo, "grok/live")
    directory = repo / "batch_state" / "tasks"
    directory.mkdir(parents=True)
    (directory / "live.json").write_text(json.dumps({"status": "spawning", "worktree_branch": "grok/live"}))
    item = only(repo, "grok/live", apply=True)
    assert item.classification == "skipped-live-task"
    assert git(repo, "ls-remote", "--heads", "origin", "grok/live")


@pytest.mark.parametrize("name", ["main", "gh-pages", "production", "ordinary/branch"])
def test_protected_or_non_candidate_name_is_not_deleted(repo: Path, name: str) -> None:
    if name != "main":
        branch(repo, name)
    item = only(repo, name, apply=True)
    assert item.classification == "protected"


@pytest.mark.parametrize("state", ["MERGED", "CLOSED"])
def test_matching_closed_pr_head_deletes_both_refs(repo: Path, state: str) -> None:
    sha = branch(repo, "codex/finished", unique=True)
    item = only(repo, "codex/finished", apply=True, states={"codex/finished": [PullRequestState(4, state, sha)]})
    assert item.classification == "delete-merged"
    assert item.remote_deleted and item.local_deleted
    assert not git(repo, "ls-remote", "--heads", "origin", "codex/finished")
    assert not git(repo, "branch", "--list", "codex/finished")


def test_closed_pr_head_mismatch_with_unique_commits_is_report_only(repo: Path) -> None:
    branch(repo, "codex/moved", unique=True)
    item = only(repo, "codex/moved", apply=True, states={"codex/moved": [PullRequestState(5, "MERGED", "0" * 40)]})
    assert item.classification == "report-only"
    assert "does not match" in item.reason
    assert git(repo, "ls-remote", "--heads", "origin", "codex/moved")


def test_ancestor_of_main_deletes_both_refs(repo: Path) -> None:
    branch(repo, "agy/old")
    item = only(repo, "agy/old", apply=True)
    assert item.classification == "delete-ancestor"
    assert item.remote_deleted and item.local_deleted
    assert not git(repo, "ls-remote", "--heads", "origin", "agy/old")


def test_no_pr_unique_commit_is_report_only_with_age(repo: Path) -> None:
    branch(repo, "kimi/unmerged", unique=True)
    item = only(repo, "kimi/unmerged", apply=True)
    assert item.classification == "report-only"
    assert item.age_days is not None
    assert git(repo, "ls-remote", "--heads", "origin", "kimi/unmerged")


@pytest.mark.parametrize("name", ["codex/has space", "-codex/flag", "codex/a:b", "codex/a..b", "codex/@{bad"])
def test_hostile_branch_name_is_never_passed_to_git(repo: Path, name: str, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, ...]] = []
    original = sweep._git

    def capture(root: Path, *args: str, **kwargs):
        calls.append(args)
        return original(root, *args, **kwargs)

    monkeypatch.setattr(sweep, "_git", capture)
    item = sweep._classify(repo, sweep.Branch(name, remote_sha=git(repo, "rev-parse", "main")),
                           worktree_branches=set(), detached_heads=set(), active_tasks=set(),
                           protected_branches=sweep.PROTECTED,
                           pr_lookup=lookup())
    assert item.classification in {"protected", "report-only"}
    assert not calls


def test_unknown_pr_state_and_malformed_task_fail_closed(repo: Path) -> None:
    branch(repo, "glm/unknown")
    assert only(repo, "glm/unknown", apply=True, error="quota exhausted").classification == "report-only"
    directory = repo / "batch_state" / "tasks"
    directory.mkdir(parents=True)
    (directory / "bad.json").write_text("{")
    with pytest.raises(RuntimeError, match="cannot inspect task state"):
        sweep.sweep(repo, apply=True, pr_lookup=lookup(), protected_lookup=lambda _repo: set())


def test_local_remote_tip_difference_is_report_only(repo: Path) -> None:
    branch(repo, "cursor/diverged")
    parent = git(repo, "rev-parse", "cursor/diverged")
    tree = git(repo, "rev-parse", "main^{tree}")
    new_head = git(repo, "commit-tree", tree, "-p", parent, "-m", "later")
    git(repo, "update-ref", "refs/heads/cursor/diverged", new_head)
    item = only(repo, "cursor/diverged", apply=True)
    assert item.classification == "report-only"
    assert "tips differ" in item.reason


def test_dry_run_preserves_eligible_refs(repo: Path) -> None:
    branch(repo, "gemini/old")
    item = only(repo, "gemini/old")
    assert item.classification == "delete-ancestor"
    assert not item.remote_deleted and not item.local_deleted
    assert git(repo, "ls-remote", "--heads", "origin", "gemini/old")


def test_dynamic_protected_branch_is_never_deleted(repo: Path) -> None:
    branch(repo, "codex/locked")
    item = next(d for d in sweep.sweep(
        repo, apply=True, pr_lookup=lookup(), protected_lookup=lambda _repo: {"codex/locked"},
    ) if d.branch == "codex/locked")
    assert item.classification == "protected"
    assert git(repo, "ls-remote", "--heads", "origin", "codex/locked")


def test_unavailable_protection_query_is_report_only(repo: Path) -> None:
    branch(repo, "codex/unknown-protection")

    def unavailable(_repo: Path) -> set[str]:
        raise RuntimeError("query unavailable")

    item = next(d for d in sweep.sweep(
        repo, apply=True, pr_lookup=lookup(), protected_lookup=unavailable,
    ) if d.branch == "codex/unknown-protection")
    assert item.classification == "report-only"
    assert "protection query unavailable" in item.reason
    assert git(repo, "ls-remote", "--heads", "origin", "codex/unknown-protection")


def test_remote_head_change_prevents_push_and_local_deletion(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    branch(repo, "codex/moved-remotely")
    original = sweep._origin_head

    def moved(root: Path, name: str) -> str | None:
        return "0" * 40 if name == "codex/moved-remotely" else original(root, name)

    monkeypatch.setattr(sweep, "_origin_head", moved)
    item = only(repo, "codex/moved-remotely", apply=True)
    assert item.classification == "report-only"
    assert "changed" in item.reason
    assert git(repo, "ls-remote", "--heads", "origin", "codex/moved-remotely")
    assert git(repo, "branch", "--list", "codex/moved-remotely")


def test_remote_deletion_passes_one_validated_refspec(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    branch(repo, "pr-123")
    calls: list[tuple[str, ...]] = []
    original = sweep._git

    def capture(root: Path, *args: str, **kwargs):
        if args[0] == "push":
            calls.append(args)
        return original(root, *args, **kwargs)

    monkeypatch.setattr(sweep, "_git", capture)
    item = only(repo, "pr-123", apply=True)
    assert item.classification == "delete-ancestor"
    assert calls == [("push", "origin", "--delete", "pr-123")]
