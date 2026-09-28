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


@pytest.mark.parametrize("status", ["spawning", "needs_finalize", None, "unexpected", {"unknown": True}])
def test_unreleased_task_is_never_deleted(repo: Path, status: object) -> None:
    branch(repo, "grok/live")
    directory = repo / "batch_state" / "tasks"
    directory.mkdir(parents=True)
    state = {"worktree_branch": "grok/live"}
    if status is not None:
        state["status"] = status
    (directory / "live.json").write_text(json.dumps(state))
    item = only(repo, "grok/live", apply=True)
    assert item.classification == "skipped-live-task"
    assert git(repo, "ls-remote", "--heads", "origin", "grok/live")


@pytest.mark.parametrize("name", [
    "main", "gh-pages", "production", "ordinary/branch",
    "gh-readonly-queue/main/pr-1-x", "dependabot/x/pr-2", "release/pr-3",
])
def test_protected_or_non_candidate_name_is_not_deleted(repo: Path, name: str) -> None:
    if name != "main":
        branch(repo, name)
    item = only(repo, name, apply=True)
    assert item.classification == "protected"


def test_matching_merged_pr_head_deletes_both_refs(repo: Path) -> None:
    sha = branch(repo, "codex/finished", unique=True)
    item = only(repo, "codex/finished", apply=True, states={"codex/finished": [PullRequestState(4, "MERGED", sha)]})
    assert item.classification == "delete-merged"
    assert item.remote_deleted and item.local_deleted
    assert not git(repo, "ls-remote", "--heads", "origin", "codex/finished")
    assert not git(repo, "branch", "--list", "codex/finished")


@pytest.mark.parametrize("unique", [True, False])
def test_matching_closed_unmerged_pr_head_is_report_only(repo: Path, unique: bool) -> None:
    sha = branch(repo, "codex/closed", unique=unique)
    item = only(repo, "codex/closed", apply=True, states={"codex/closed": [PullRequestState(4, "CLOSED", sha)]})
    assert item.classification == "report-only"
    assert "unmerged" in item.reason
    assert git(repo, "ls-remote", "--heads", "origin", "codex/closed")
    assert git(repo, "branch", "--list", "codex/closed")


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


@pytest.mark.parametrize("name", ["codex/has space", "-x/review-1", "codex/a:b", "codex/a..b", "codex/@{bad"])
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
    if name == "-x/review-1":
        assert sweep._candidate(name)
        assert item.reason == "invalid or unsafe branch name"
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
    assert item.classification == "skipped-moved"
    assert "changed" in item.reason
    assert git(repo, "ls-remote", "--heads", "origin", "codex/moved-remotely")
    assert git(repo, "branch", "--list", "codex/moved-remotely")


def test_remote_deletion_passes_one_validated_refspec(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sha = branch(repo, "pr-123")
    calls: list[tuple[str, ...]] = []
    original = sweep._git

    def capture(root: Path, *args: str, **kwargs):
        if args[0] == "push":
            calls.append(args)
        return original(root, *args, **kwargs)

    monkeypatch.setattr(sweep, "_git", capture)
    item = only(repo, "pr-123", apply=True)
    assert item.classification == "delete-ancestor"
    assert calls == [(
        "push", "--porcelain", f"--force-with-lease=refs/heads/pr-123:{sha}",
        "origin", ":refs/heads/pr-123",
    )]


def test_remote_advance_during_push_preserves_both_refs(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    old_sha = branch(repo, "codex/racing")
    tree = git(repo, "rev-parse", "main^{tree}")
    new_sha = git(repo, "commit-tree", tree, "-p", old_sha, "-m", "new remote work")
    original = sweep._git
    pushes: list[tuple[str, ...]] = []

    def advance_before_push(root: Path, *args: str, **kwargs):
        if args[0] == "push":
            pushes.append(args)
            git(repo, "push", "origin", f"{new_sha}:refs/heads/codex/racing")
        return original(root, *args, **kwargs)

    monkeypatch.setattr(sweep, "_git", advance_before_push)
    item = only(repo, "codex/racing", apply=True)
    assert item.classification == "skipped-moved"
    assert not item.remote_deleted and not item.local_deleted
    assert git(repo, "ls-remote", "--heads", "origin", "codex/racing").split()[0] == new_sha
    assert git(repo, "rev-parse", "refs/heads/codex/racing") == old_sha
    assert pushes == [(
        "push", "--porcelain", f"--force-with-lease=refs/heads/codex/racing:{old_sha}",
        "origin", ":refs/heads/codex/racing",
    )]


def test_remote_disappears_after_classification_allows_local_deletion(
    repo: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    branch(repo, "codex/absent")
    original = sweep._origin_head

    def disappear(root: Path, name: str) -> str | None:
        if name == "codex/absent":
            git(repo, "push", "origin", "--delete", name)
        return original(root, name)

    monkeypatch.setattr(sweep, "_origin_head", disappear)
    item = only(repo, "codex/absent", apply=True)
    assert item.classification == "delete-ancestor"
    assert not item.remote_deleted and item.local_deleted
    assert not git(repo, "branch", "--list", "codex/absent")


def test_already_absent_remote_and_local_has_honest_receipt(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    branch(repo, "pr-absent")
    git(repo, "branch", "-D", "pr-absent")
    original = sweep._origin_head

    def disappear(root: Path, name: str) -> str | None:
        if name == "pr-absent":
            git(repo, "push", "origin", "--delete", name)
        return original(root, name)

    monkeypatch.setattr(sweep, "_origin_head", disappear)
    item = only(repo, "pr-absent", apply=True)
    assert item.classification == "already-absent"
    assert not item.remote_deleted and not item.local_deleted


@pytest.mark.parametrize("failure", ["fetch", "task-recheck"])
def test_json_receipts_survive_failure_after_deletion(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], failure: str,
) -> None:
    branch(repo, "codex/a")
    branch(repo, "codex/b")
    original_sweep = sweep.sweep
    monkeypatch.setattr(sweep.reaper, "resolve_repo_root", lambda: repo)
    monkeypatch.setattr(sweep, "sweep", lambda root, *, apply: original_sweep(
        root, apply=apply, pr_lookup=lookup(), protected_lookup=lambda _repo: set(),
    ))
    if failure == "fetch":
        original_checked = sweep._checked

        def fail_fetch(root: Path, *args: str) -> str:
            if args[0] == "fetch":
                raise RuntimeError("final fetch failed")
            return original_checked(root, *args)

        monkeypatch.setattr(sweep, "_checked", fail_fetch)
    else:
        original_tasks = sweep._active_tasks
        calls = 0

        def fail_recheck(root: Path) -> set[str]:
            nonlocal calls
            calls += 1
            if calls == 3:
                raise RuntimeError("task file unreadable")
            return original_tasks(root)

        monkeypatch.setattr(sweep, "_active_tasks", fail_recheck)
    assert sweep.main(["--apply", "--json"]) == 1
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["ok"] is False
    assert failure.split("-")[0] in receipt["error"]
    deleted = [d for d in receipt["decisions"] if d["branch"] == "codex/a"]
    assert len(deleted) == 1
    assert deleted[0]["remote_deleted"] and deleted[0]["local_deleted"]
    assert not git(repo, "ls-remote", "--heads", "origin", "codex/a")
