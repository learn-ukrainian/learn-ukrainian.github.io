from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pytest

from scripts.orchestration import merge_closeout as mc
from scripts.orchestration import reap_worktrees as rw

_REAL_RUN = subprocess.run


def git_env() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_") and not key.startswith("PRE_COMMIT") and key != "AGENT_NO_MERGE"
    }


def git(cwd: Path, *args: str) -> str:
    proc = _REAL_RUN(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        env=git_env(),
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    return (proc.stdout or "").strip()


def init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    remote = tmp_path / "origin.git"
    git(tmp_path, "init", "--bare", str(remote))
    git(tmp_path, "init", "--initial-branch=main", str(repo))
    git(repo, "config", "user.email", "tester@example.com")
    git(repo, "config", "user.name", "Test User")
    (repo / ".gitignore").write_text(".worktrees/\n", encoding="utf-8")
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    git(repo, "add", ".gitignore", "README.md")
    git(repo, "commit", "-m", "base")
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "-u", "origin", "main")
    return repo


def add_worktree(repo: Path, branch: str) -> Path:
    worktree = repo / ".worktrees" / "dispatch" / branch.replace("/", "-")
    worktree.parent.mkdir(parents=True, exist_ok=True)
    git(repo, "worktree", "add", "-b", branch, str(worktree), "main")
    return worktree


def add_detached_worktree(repo: Path, name: str, sha: str) -> Path:
    worktree = repo / ".worktrees" / "review" / name
    worktree.parent.mkdir(parents=True, exist_ok=True)
    git(repo, "worktree", "add", "--detach", str(worktree), sha)
    return worktree


def commit_on_branch(repo: Path, branch: str, filename: str) -> str:
    """Create a commit on a new branch off main, without touching main."""
    git(repo, "branch", branch, "main")
    worktree = repo / ".worktrees" / "dispatch" / branch.replace("/", "-")
    worktree.parent.mkdir(parents=True, exist_ok=True)
    git(repo, "worktree", "add", str(worktree), branch)
    (worktree / filename).write_text("content\n", encoding="utf-8")
    git(worktree, "add", filename)
    git(worktree, "commit", "-m", f"add {filename}")
    sha = git(worktree, "rev-parse", "HEAD")
    git(worktree, "push", "-u", "origin", branch)
    git(repo, "worktree", "remove", "--force", str(worktree))
    return sha


def publish_pr_head(repo: Path, number: int, branch: str, pr_head: str) -> None:
    """Publish a live PR ref and its branch head in the temporary bare origin."""
    git(repo, "push", "origin", f"{pr_head}:refs/heads/{branch}")
    git(repo, "push", "origin", f"{pr_head}:refs/pull/{number}/head")


def make_pr_head_after(repo: Path, branch: str, filename: str) -> tuple[str, str]:
    local_head = commit_on_branch(repo, branch, filename)
    worktree = repo / ".worktrees" / "dispatch" / f"update-{branch.replace('/', '-')}"
    worktree.parent.mkdir(parents=True, exist_ok=True)
    git(repo, "worktree", "add", "--detach", str(worktree), local_head)
    git(worktree, "commit", "--allow-empty", "-m", "update-branch merge commit")
    pr_head = git(worktree, "rev-parse", "HEAD")
    git(repo, "worktree", "remove", "--force", str(worktree))
    return local_head, pr_head


def make_pr_merge_head_after_main_advance(repo: Path, branch: str, filename: str) -> tuple[str, str, str]:
    """Create a PR head that merges a new main commit into an existing branch."""
    local_head = commit_on_branch(repo, branch, filename)
    (repo / "main-update.txt").write_text("main update\n", encoding="utf-8")
    git(repo, "add", "main-update.txt")
    git(repo, "commit", "-m", "advance main")
    main_head = git(repo, "rev-parse", "HEAD")

    worktree = repo / ".worktrees" / "dispatch" / f"merge-{branch.replace('/', '-')}"
    worktree.parent.mkdir(parents=True, exist_ok=True)
    git(repo, "worktree", "add", "--detach", str(worktree), local_head)
    git(worktree, "merge", "--no-ff", "main", "-m", "merge main into PR branch")
    pr_head = git(worktree, "rev-parse", "HEAD")
    git(repo, "worktree", "remove", "--force", str(worktree))
    return local_head, main_head, pr_head


def patch_gh(
    monkeypatch: pytest.MonkeyPatch,
    *,
    pr_number: int,
    state: str,
    head_ref_name: str | None,
    head_sha: str | None,
    branch_prs: dict[str, list[dict[str, Any]]] | None = None,
    sha_prs: dict[str, list[dict[str, Any]]] | None = None,
) -> list[list[str]]:
    branch_prs = branch_prs or {}
    sha_prs = sha_prs or {}
    calls: list[list[str]] = []

    def fake_run(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if args and args[0] == "gh":
            calls.append(args)
            if args[1:3] == ["api", "-X"]:
                payload = {
                    "number": pr_number,
                    "state": "closed" if state == "MERGED" else state.lower(),
                    "merged_at": "2026-01-02T03:04:05Z" if state == "MERGED" else None,
                    "head": {"ref": head_ref_name, "sha": head_sha},
                }
                return subprocess.CompletedProcess(args, 0, json.dumps(payload), "")
            if args[1:3] == ["pr", "view"]:
                payload = {
                    "number": pr_number,
                    "state": state,
                    "headRefName": head_ref_name,
                    "headRefOid": head_sha,
                }
                return subprocess.CompletedProcess(args, 0, json.dumps(payload), "")
            if args[1:3] == ["pr", "list"]:
                branch = args[args.index("--head") + 1]
                return subprocess.CompletedProcess(args, 0, json.dumps(branch_prs.get(branch, [])), "")
            if args[1:3] == ["search", "prs"]:
                sha = args[3]
                return subprocess.CompletedProcess(args, 0, json.dumps(sha_prs.get(sha, [])), "")
        return _REAL_RUN(args, **kwargs)

    monkeypatch.setattr(rw, "_github_owner_repo", lambda _: ("learn-ukrainian", "learn-ukrainian.github.io"))
    monkeypatch.setattr(mc.subprocess, "run", fake_run)
    monkeypatch.setattr(rw.subprocess, "run", fake_run)
    return calls


def test_fetch_pr_info_parses_gh_payload(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = init_repo(tmp_path)
    patch_gh(
        monkeypatch,
        pr_number=42,
        state="MERGED",
        head_ref_name="codex/feature",
        head_sha="deadbeef",
    )

    pr = mc.fetch_pr_info(repo, 42)

    assert pr == mc.PullRequestInfo(
        number=42, state="MERGED", head_ref_name="codex/feature", head_sha="deadbeef"
    )


@pytest.mark.parametrize(
    ("raw_state", "merged_at", "expected_state"),
    [("closed", "2026-01-02T03:04:05Z", "MERGED"), ("open", None, "OPEN"), ("closed", None, "CLOSED")],
)
def test_fetch_pr_info_maps_rest_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    raw_state: str,
    merged_at: str | None,
    expected_state: str,
) -> None:
    repo = init_repo(tmp_path)
    calls: list[list[str]] = []
    payload = {
        "number": 42,
        "state": raw_state,
        "merged_at": merged_at,
        "head": {"ref": "codex/feature", "sha": "deadbeef"},
    }

    def fake_run(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if args[:3] == ["gh", "api", "-X"]:
            calls.append(args)
            return subprocess.CompletedProcess(args, 0, json.dumps(payload), "")
        return _REAL_RUN(args, **kwargs)

    monkeypatch.setattr(rw, "_github_owner_repo", lambda _: ("learn-ukrainian", "learn-ukrainian.github.io"))
    monkeypatch.setattr(mc.subprocess, "run", fake_run)

    pr = mc.fetch_pr_info(repo, 42)

    assert pr == mc.PullRequestInfo(42, expected_state, "codex/feature", "deadbeef")
    assert len(calls) == 1
    assert calls[0][-1] == "repos/learn-ukrainian/learn-ukrainian.github.io/pulls/42"


def test_fetch_pr_info_rest_failure_falls_back_to_graphql(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = init_repo(tmp_path)
    calls: list[list[str]] = []

    def fake_run(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if args and args[0] == "gh":
            calls.append(args)
            if args[1:3] == ["api", "-X"]:
                return subprocess.CompletedProcess(args, 1, "", "REST unavailable")
            if args[1:3] == ["pr", "view"]:
                payload = {"number": 42, "state": "MERGED", "headRefName": "fallback", "headRefOid": "bead"}
                return subprocess.CompletedProcess(args, 0, json.dumps(payload), "")
        return _REAL_RUN(args, **kwargs)

    monkeypatch.setattr(rw, "_github_owner_repo", lambda _: ("learn-ukrainian", "learn-ukrainian.github.io"))
    monkeypatch.setattr(mc.subprocess, "run", fake_run)

    pr = mc.fetch_pr_info(repo, 42)

    assert pr == mc.PullRequestInfo(42, "MERGED", "fallback", "bead")
    assert [call[1:3] for call in calls] == [["api", "-X"], ["pr", "view"]]


def test_fetch_pr_info_both_fail_includes_both_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = init_repo(tmp_path)

    def fake_run(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if args and args[0] == "gh":
            if args[1:3] == ["api", "-X"]:
                return subprocess.CompletedProcess(args, 1, "", "REST unavailable")
            return subprocess.CompletedProcess(args, 1, "", "GraphQL unavailable")
        return _REAL_RUN(args, **kwargs)

    monkeypatch.setattr(rw, "_github_owner_repo", lambda _: ("learn-ukrainian", "learn-ukrainian.github.io"))
    monkeypatch.setattr(mc.subprocess, "run", fake_run)

    with pytest.raises(mc.MergeCloseoutError) as exc_info:
        mc.fetch_pr_info(repo, 42)

    assert "REST unavailable" in str(exc_info.value)
    assert "GraphQL unavailable" in str(exc_info.value)


def test_fetch_pr_info_malformed_rest_falls_back_instead_of_guessing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = init_repo(tmp_path)
    calls: list[list[str]] = []

    def fake_run(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if args and args[0] == "gh":
            calls.append(args)
            if args[1:3] == ["api", "-X"]:
                return subprocess.CompletedProcess(args, 0, json.dumps({"number": 42, "state": "unknown"}), "")
            if args[1:3] == ["pr", "view"]:
                payload = {"number": 42, "state": "OPEN", "headRefName": "safe", "headRefOid": "sha"}
                return subprocess.CompletedProcess(args, 0, json.dumps(payload), "")
        return _REAL_RUN(args, **kwargs)

    monkeypatch.setattr(rw, "_github_owner_repo", lambda _: ("learn-ukrainian", "learn-ukrainian.github.io"))
    monkeypatch.setattr(mc.subprocess, "run", fake_run)

    pr = mc.fetch_pr_info(repo, 42)

    assert pr == mc.PullRequestInfo(42, "OPEN", "safe", "sha")
    assert [call[1:3] for call in calls] == [["api", "-X"], ["pr", "view"]]


def test_fetch_pr_info_honors_repo_override_for_rest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = init_repo(tmp_path)
    calls: list[list[str]] = []
    payload = {"number": 42, "state": "open", "merged_at": None, "head": {"ref": "override", "sha": "sha"}}

    def fake_run(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if args and args[0] == "gh":
            calls.append(args)
            return subprocess.CompletedProcess(args, 0, json.dumps(payload), "")
        return _REAL_RUN(args, **kwargs)

    monkeypatch.setattr(mc.subprocess, "run", fake_run)

    pr = mc.fetch_pr_info(repo, 42, repo="other/project")

    assert pr == mc.PullRequestInfo(42, "OPEN", "override", "sha")
    assert calls[0][-1] == "repos/other/project/pulls/42"


def test_run_merge_closeout_fails_closed_when_not_merged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = init_repo(tmp_path)
    patch_gh(
        monkeypatch,
        pr_number=7,
        state="OPEN",
        head_ref_name="codex/wip",
        head_sha="abc123",
    )

    with pytest.raises(mc.MergeCloseoutError, match="not MERGED"):
        mc.run_merge_closeout(repo, 7, apply=True)


def test_run_merge_closeout_fails_closed_when_gh_pr_view_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = init_repo(tmp_path)

    def fake_run(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if args and args[0] == "gh":
            return subprocess.CompletedProcess(args, 1, "", "no such PR")
        return _REAL_RUN(args, **kwargs)

    monkeypatch.setattr(mc.subprocess, "run", fake_run)

    with pytest.raises(mc.MergeCloseoutError, match="gh pr view 99 failed"):
        mc.run_merge_closeout(repo, 99, apply=True)


def test_apply_reaps_matched_worktree_by_branch_and_deletes_branches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = init_repo(tmp_path)
    worktree = add_worktree(repo, "codex/feature")
    head_sha = git(worktree, "rev-parse", "HEAD")
    git(worktree, "push", "-u", "origin", "codex/feature")

    patch_gh(
        monkeypatch,
        pr_number=101,
        state="MERGED",
        head_ref_name="codex/feature",
        head_sha=head_sha,
        branch_prs={"codex/feature": [{"number": 101, "state": "MERGED", "headRefOid": head_sha}]},
    )

    result = mc.run_merge_closeout(repo, 101, apply=True, live_cwds=set())

    assert result.matched_worktrees == [str(worktree)]
    assert [entry["action"] for entry in result.reap_results] == ["removed"]
    assert not worktree.exists()
    assert result.branch_status is not None
    assert result.branch_status.local_gone is True
    assert result.branch_status.remote_gone is True
    assert result.errors == []
    assert result.ok is True

    assert git(repo, "ls-remote", "--heads", "origin", "codex/feature") == ""
    local = _REAL_RUN(
        ["git", "rev-parse", "--verify", "refs/heads/codex/feature"],
        cwd=repo,
        capture_output=True,
        text=True,
        env=git_env(),
    )
    assert local.returncode != 0


def test_apply_matches_detached_review_sibling_by_exact_sha(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = init_repo(tmp_path)
    head_sha = commit_on_branch(repo, "codex/reviewed", "notes.txt")
    publish_pr_head(repo, 202, "codex/reviewed", head_sha)
    review_worktree = add_detached_worktree(repo, "pr-202", head_sha)

    patch_gh(
        monkeypatch,
        pr_number=202,
        state="MERGED",
        head_ref_name="codex/reviewed",
        head_sha=head_sha,
        sha_prs={head_sha: [{"number": 202, "state": "MERGED"}]},
    )

    result = mc.run_merge_closeout(repo, 202, apply=True, live_cwds=set())

    matched = {Path(p).resolve() for p in result.matched_worktrees}
    assert review_worktree.resolve() in matched
    assert not review_worktree.exists()
    assert result.ok is True


def test_dry_run_does_not_delete_anything(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = init_repo(tmp_path)
    worktree = add_worktree(repo, "codex/dry-run")
    head_sha = git(worktree, "rev-parse", "HEAD")
    git(worktree, "push", "-u", "origin", "codex/dry-run")

    patch_gh(
        monkeypatch,
        pr_number=303,
        state="MERGED",
        head_ref_name="codex/dry-run",
        head_sha=head_sha,
        branch_prs={"codex/dry-run": [{"number": 303, "state": "MERGED", "headRefOid": head_sha}]},
    )

    result = mc.run_merge_closeout(repo, 303, apply=False, live_cwds=set())

    assert result.apply is False
    assert result.matched_worktrees == [str(worktree)]
    assert worktree.exists()
    assert git(repo, "rev-parse", "--verify", "codex/dry-run")
    assert git(repo, "ls-remote", "--heads", "origin", "codex/dry-run") != ""
    assert result.ok is True


def test_apply_deletes_stale_remote_branch_when_no_worktree_remains(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = init_repo(tmp_path)
    head_sha = commit_on_branch(repo, "codex/already-reaped", "note.txt")
    # No worktree remains for this branch, but the remote head survived merge.
    publish_pr_head(repo, 404, "codex/already-reaped", head_sha)

    patch_gh(
        monkeypatch,
        pr_number=404,
        state="MERGED",
        head_ref_name="codex/already-reaped",
        head_sha=head_sha,
    )

    result = mc.run_merge_closeout(repo, 404, apply=True, live_cwds=set())

    assert result.matched_worktrees == []
    assert result.branch_status is not None
    assert result.branch_status.remote_gone is True
    assert git(repo, "ls-remote", "--heads", "origin", "codex/already-reaped") == ""
    assert result.ok is True


def test_apply_deletes_local_branch_when_tip_is_ancestor_of_live_pr_head(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = init_repo(tmp_path)
    local_head, main_head, pr_head = make_pr_merge_head_after_main_advance(
        repo, "codex/updated", "note.txt"
    )
    assert git(repo, "rev-parse", "refs/heads/codex/updated") == local_head
    publish_pr_head(repo, 8560, "codex/updated", pr_head)
    patch_gh(
        monkeypatch,
        pr_number=8560,
        state="MERGED",
        head_ref_name="codex/updated",
        head_sha=pr_head,
        branch_prs={"codex/updated": [{"number": 8560, "state": "MERGED", "headRefOid": pr_head}]},
    )

    result = mc.run_merge_closeout(repo, 8560, apply=True, live_cwds=set())

    assert result.matched_worktrees == []
    assert result.branch_status is not None
    assert result.branch_status.local_gone is True
    assert result.branch_status.local_error is None
    assert result.ok is True
    assert local_head != pr_head
    assert git(repo, "rev-parse", f"{pr_head}^1") == local_head
    assert git(repo, "rev-parse", f"{pr_head}^2") == main_head
    local = _REAL_RUN(
        ["git", "show-ref", "--verify", "--quiet", "refs/heads/codex/updated"],
        cwd=repo,
        capture_output=True,
        text=True,
        env=git_env(),
    )
    assert local.returncode != 0


def test_apply_exact_head_delete_does_not_fetch_live_pr_head(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = init_repo(tmp_path)
    pr_head = commit_on_branch(repo, "codex/exact-head-no-fetch", "note.txt")
    publish_pr_head(repo, 8565, "codex/exact-head-no-fetch", pr_head)
    patch_gh(
        monkeypatch,
        pr_number=8565,
        state="MERGED",
        head_ref_name="codex/exact-head-no-fetch",
        head_sha=pr_head,
    )
    original_run = rw._run
    fetch_calls: list[dict[str, Any]] = []

    def record_fetch(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if args[:3] == ["git", "fetch", "--no-tags"]:
            fetch_calls.append(kwargs)
        return original_run(args, **kwargs)

    monkeypatch.setattr(rw, "_run", record_fetch)

    status = mc.verify_branch_gone(
        repo,
        mc.PullRequestInfo(8565, "MERGED", "codex/exact-head-no-fetch", pr_head),
        apply=True,
    )

    assert status is not None
    assert status.local_gone is True
    assert status.local_error is None
    assert fetch_calls == []


def test_apply_refuses_local_branch_with_commit_outside_live_pr_head(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = init_repo(tmp_path)
    pr_head = commit_on_branch(repo, "codex/extra-local", "note.txt")
    tree = git(repo, "rev-parse", f"{pr_head}^{{tree}}")
    extra = git(repo, "commit-tree", tree, "-p", pr_head, "-m", "extra local commit")
    git(repo, "update-ref", "refs/heads/codex/extra-local", extra)
    publish_pr_head(repo, 8561, "codex/extra-local", pr_head)
    patch_gh(
        monkeypatch,
        pr_number=8561,
        state="MERGED",
        head_ref_name="codex/extra-local",
        head_sha=pr_head,
    )

    status = mc.verify_branch_gone(
        repo,
        mc.PullRequestInfo(8561, "MERGED", "codex/extra-local", pr_head),
        apply=True,
    )

    assert status is not None
    assert status.local_gone is False
    assert status.local_error == "local head does not match merged PR head; refusing to delete"
    assert git(repo, "rev-parse", "refs/heads/codex/extra-local") == extra


def test_apply_deletes_local_branch_when_head_equals_live_pr_head(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = init_repo(tmp_path)
    pr_head = commit_on_branch(repo, "codex/equal-head", "note.txt")
    publish_pr_head(repo, 8562, "codex/equal-head", pr_head)
    patch_gh(
        monkeypatch,
        pr_number=8562,
        state="MERGED",
        head_ref_name="codex/equal-head",
        head_sha=pr_head,
    )

    status = mc.verify_branch_gone(
        repo,
        mc.PullRequestInfo(8562, "MERGED", "codex/equal-head", pr_head),
        apply=True,
    )

    assert status is not None
    assert status.local_gone is True
    assert status.local_error is None


def test_apply_refuses_ancestor_delete_when_fetching_live_pr_head_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = init_repo(tmp_path)
    local_head, pr_head = make_pr_head_after(repo, "codex/fetch-fails", "note.txt")
    publish_pr_head(repo, 8563, "codex/fetch-fails", pr_head)
    patch_gh(
        monkeypatch,
        pr_number=8563,
        state="MERGED",
        head_ref_name="codex/fetch-fails",
        head_sha=pr_head,
    )
    original_run = rw._run

    def fail_pr_fetch(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if args[:3] == ["git", "fetch", "--no-tags"]:
            return subprocess.CompletedProcess(args, 1, "", "network unavailable")
        return original_run(args, **kwargs)

    monkeypatch.setattr(rw, "_run", fail_pr_fetch)

    status = mc.verify_branch_gone(
        repo,
        mc.PullRequestInfo(8563, "MERGED", "codex/fetch-fails", pr_head),
        apply=True,
    )

    assert status is not None
    assert status.local_gone is False
    assert status.local_error is not None
    assert "cannot fetch live PR head refs/pull/8563/head" in status.local_error
    assert local_head != pr_head
    assert git(repo, "rev-parse", "refs/heads/codex/fetch-fails") == local_head


def test_apply_refuses_timed_out_live_pr_head_fetch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = init_repo(tmp_path)
    local_head, pr_head = make_pr_head_after(repo, "codex/fetch-timeout", "note.txt")
    publish_pr_head(repo, 8566, "codex/fetch-timeout", pr_head)
    patch_gh(
        monkeypatch,
        pr_number=8566,
        state="MERGED",
        head_ref_name="codex/fetch-timeout",
        head_sha=pr_head,
    )
    original_run = rw._run
    fetch_kwargs: dict[str, Any] | None = None

    def timeout_fetch(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        nonlocal fetch_kwargs
        if args[:3] == ["git", "fetch", "--no-tags"]:
            fetch_kwargs = kwargs
            raise subprocess.TimeoutExpired(args, timeout=kwargs["timeout"])
        return original_run(args, **kwargs)

    monkeypatch.setattr(rw, "_run", timeout_fetch)

    status = mc.verify_branch_gone(
        repo,
        mc.PullRequestInfo(8566, "MERGED", "codex/fetch-timeout", pr_head),
        apply=True,
    )

    assert status is not None
    assert status.local_gone is False
    assert status.local_error == (
        "cannot fetch live PR head refs/pull/8566/head: timed out after 30 seconds"
    )
    assert fetch_kwargs is not None
    assert fetch_kwargs["timeout"] == 30
    assert fetch_kwargs["env_overrides"] == {"GIT_TERMINAL_PROMPT": "0"}
    assert git(repo, "rev-parse", "refs/heads/codex/fetch-timeout") == local_head


def test_apply_refuses_local_delete_when_ancestry_check_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = init_repo(tmp_path)
    local_head, pr_head = make_pr_head_after(repo, "codex/ancestry-fails", "note.txt")
    publish_pr_head(repo, 8564, "codex/ancestry-fails", pr_head)
    patch_gh(
        monkeypatch,
        pr_number=8564,
        state="MERGED",
        head_ref_name="codex/ancestry-fails",
        head_sha=pr_head,
    )
    original_run = rw._run

    def fail_ancestry(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if args[:4] == ["git", "merge-base", "--is-ancestor", local_head]:
            return subprocess.CompletedProcess(args, 128, "", "repository corrupt")
        return original_run(args, **kwargs)

    monkeypatch.setattr(rw, "_run", fail_ancestry)

    status = mc.verify_branch_gone(
        repo,
        mc.PullRequestInfo(8564, "MERGED", "codex/ancestry-fails", pr_head),
        apply=True,
    )

    assert status is not None
    assert status.local_gone is False
    assert status.local_error == "cannot verify local ancestry: repository corrupt"
    assert git(repo, "rev-parse", "refs/heads/codex/ancestry-fails") == local_head


def test_apply_reports_residual_when_branch_head_diverges(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A branch whose live head no longer matches the merged PR head is left
    alone and reported as residual, never force-deleted."""
    repo = init_repo(tmp_path)
    head_sha = commit_on_branch(repo, "codex/diverged", "note.txt")
    # Advance the remote branch past the recorded merged PR head.
    worktree = repo / ".worktrees" / "dispatch" / "codex-diverged"
    worktree.parent.mkdir(parents=True, exist_ok=True)
    git(repo, "worktree", "add", str(worktree), "codex/diverged")
    (worktree / "extra.txt").write_text("more\n", encoding="utf-8")
    git(worktree, "add", "extra.txt")
    git(worktree, "commit", "-m", "extra commit after PR head was recorded")
    git(worktree, "push", "origin", "codex/diverged")
    git(repo, "worktree", "remove", "--force", str(worktree))

    patch_gh(
        monkeypatch,
        pr_number=505,
        state="MERGED",
        head_ref_name="codex/diverged",
        head_sha=head_sha,
    )

    result = mc.run_merge_closeout(repo, 505, apply=True, live_cwds=set())

    assert result.branch_status is not None
    assert result.branch_status.remote_gone is False
    assert result.branch_status.remote_error is not None
    assert result.ok is False
    assert git(repo, "ls-remote", "--heads", "origin", "codex/diverged") != ""


def test_apply_exits_nonzero_when_matched_worktree_stays_dirty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A dirty matched worktree the reaper retains (action=skipped) must not
    report a successful closeout -- CF F1."""
    repo = init_repo(tmp_path)
    head_sha = commit_on_branch(repo, "codex/dirty-retained", "note.txt")
    review_worktree = add_detached_worktree(repo, "pr-707", head_sha)
    (review_worktree / "scratch.txt").write_text("uncommitted\n", encoding="utf-8")

    patch_gh(
        monkeypatch,
        pr_number=707,
        state="MERGED",
        head_ref_name="codex/dirty-retained",
        head_sha=head_sha,
        sha_prs={head_sha: [{"number": 707, "state": "MERGED"}]},
    )

    exit_code = mc.main(["707", "--repo-root", str(repo), "--apply", "--json"])

    assert review_worktree.exists()
    payload = json.loads(capsys.readouterr().out)
    assert [entry["action"] for entry in payload["reap_results"]] == ["skipped"]
    assert payload["ok"] is False
    assert any("still registered after reap" in error for error in payload["errors"])
    assert exit_code == 1


def test_apply_fails_closed_when_origin_is_unreachable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failed ``git ls-remote`` (unreachable/auth-failing origin) must never
    be read as "branch already gone" -- CF F2."""
    repo = init_repo(tmp_path)
    head_sha = commit_on_branch(repo, "codex/origin-down", "note.txt")
    # No worktree remains for this branch.

    patch_gh(
        monkeypatch,
        pr_number=808,
        state="MERGED",
        head_ref_name="codex/origin-down",
        head_sha=head_sha,
    )
    git(repo, "remote", "set-url", "origin", str(tmp_path / "does-not-exist.git"))

    result = mc.run_merge_closeout(repo, 808, apply=True, live_cwds=set())

    assert result.branch_status is not None
    assert result.branch_status.remote_gone is False
    assert result.branch_status.remote_error is not None
    assert result.ok is False


def test_apply_refuses_fallback_branch_delete_when_open_pr_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A same-branch OPEN PR must block the fallback branch delete even when
    no worktree remains to run the reaper's own open-PR guard -- CF F3."""
    repo = init_repo(tmp_path)
    head_sha = commit_on_branch(repo, "codex/reused-branch", "note.txt")
    # No worktree remains for this branch.
    publish_pr_head(repo, 42, "codex/reused-branch", head_sha)

    patch_gh(
        monkeypatch,
        pr_number=42,
        state="MERGED",
        head_ref_name="codex/reused-branch",
        head_sha=head_sha,
        branch_prs={
            "codex/reused-branch": [
                {"number": 42, "state": "MERGED", "headRefOid": head_sha},
                {"number": 43, "state": "OPEN", "headRefOid": head_sha},
            ]
        },
    )

    result = mc.run_merge_closeout(repo, 42, apply=True, live_cwds=set())

    assert result.branch_status is not None
    assert result.branch_status.remote_gone is False
    assert result.branch_status.local_gone is False
    assert result.branch_status.remote_error is not None
    assert "open PR" in result.branch_status.remote_error
    assert result.branch_status.local_error is not None
    assert "open PR" in result.branch_status.local_error
    assert result.ok is False
    assert git(repo, "ls-remote", "--heads", "origin", "codex/reused-branch") != ""
    assert git(repo, "rev-parse", "--verify", "codex/reused-branch")


def test_apply_expected_head_missing_still_refuses_branch_with_open_pr(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = init_repo(tmp_path)
    local_head = commit_on_branch(repo, "codex/open-pr-no-expected-head", "note.txt")
    publish_pr_head(repo, 8567, "codex/open-pr-no-expected-head", local_head)
    patch_gh(
        monkeypatch,
        pr_number=8567,
        state="MERGED",
        head_ref_name="codex/open-pr-no-expected-head",
        head_sha=None,
        branch_prs={
            "codex/open-pr-no-expected-head": [
                {"number": 8568, "state": "OPEN", "headRefOid": local_head}
            ]
        },
    )

    result = mc.run_merge_closeout(repo, 8567, apply=True, live_cwds=set())

    assert result.branch_status is not None
    assert result.branch_status.local_gone is False
    assert result.branch_status.local_error == (
        "branch has an open PR (#8568); refusing to delete"
    )
    assert result.ok is False
    assert git(repo, "rev-parse", "refs/heads/codex/open-pr-no-expected-head") == local_head


def test_main_exits_nonzero_and_prints_json_when_pr_not_merged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = init_repo(tmp_path)
    patch_gh(
        monkeypatch,
        pr_number=9,
        state="CLOSED",
        head_ref_name="codex/closed",
        head_sha="deadbeef",
    )

    exit_code = mc.main(["9", "--repo-root", str(repo), "--json"])

    assert exit_code == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert "not MERGED" in payload["error"]


def test_main_dry_run_default_reports_ok_without_deleting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = init_repo(tmp_path)
    worktree = add_worktree(repo, "codex/main-cli")
    head_sha = git(worktree, "rev-parse", "HEAD")
    git(worktree, "push", "-u", "origin", "codex/main-cli")
    patch_gh(
        monkeypatch,
        pr_number=606,
        state="MERGED",
        head_ref_name="codex/main-cli",
        head_sha=head_sha,
        branch_prs={"codex/main-cli": [{"number": 606, "state": "MERGED", "headRefOid": head_sha}]},
    )
    monkeypatch.setattr(rw, "_live_cwd_paths", lambda _repo: set())

    exit_code = mc.main(["606", "--repo-root", str(repo)])

    assert exit_code == 0
    assert worktree.exists()
    out = capsys.readouterr().out
    assert "mode: dry-run" in out
    assert "OK" in out


def test_detached_earlier_pr_commit_matches_and_main_checkout_does_not(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    branch_wt = repo / ".worktrees" / "dispatch" / "feature"
    branch_wt.parent.mkdir(parents=True, exist_ok=True)
    git(repo, "branch", "grok/feature", "main")
    git(repo, "worktree", "add", str(branch_wt), "grok/feature")
    (branch_wt / "a.txt").write_text("a\n", encoding="utf-8")
    git(branch_wt, "add", "a.txt")
    git(branch_wt, "commit", "-m", "first")
    earlier = git(branch_wt, "rev-parse", "HEAD")
    (branch_wt / "b.txt").write_text("b\n", encoding="utf-8")
    git(branch_wt, "add", "b.txt")
    git(branch_wt, "commit", "-m", "second")
    pr_sha = git(branch_wt, "rev-parse", "HEAD")
    git(branch_wt, "push", "-u", "origin", "grok/feature")
    git(repo, "worktree", "remove", "--force", str(branch_wt))
    detached = add_detached_worktree(repo, "review-feature-r1", earlier)
    on_main = add_detached_worktree(repo, "review-other", git(repo, "rev-parse", "origin/main"))
    pr = mc.PullRequestInfo(
        number=7,
        state="MERGED",
        head_ref_name="grok/feature",
        head_sha=pr_sha,
    )

    matched = {info.path.resolve() for info in mc.find_matching_worktrees(repo, pr)}

    assert detached.resolve() in matched
    assert on_main.resolve() not in matched


def test_apply_keeps_same_tree_divergent_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A sibling commit with the merged PR's tree is not removed or pruned."""
    repo = init_repo(tmp_path)
    worktree = add_worktree(repo, "codex/feature")
    git(worktree, "push", "-u", "origin", "codex/feature")
    git(worktree, "commit", "--allow-empty", "-m", "sibling of merged head")
    tree = git(worktree, "rev-parse", "HEAD^{tree}")
    parent = git(repo, "rev-parse", "main")
    pr_head = git(repo, "commit-tree", tree, "-p", parent, "-m", "merged pr head")
    patch_gh(
        monkeypatch,
        pr_number=7070,
        state="MERGED",
        head_ref_name="codex/feature",
        head_sha=pr_head,
        branch_prs={"codex/feature": [{"number": 7070, "state": "MERGED", "headRefOid": pr_head}]},
    )

    result = mc.run_merge_closeout(repo, 7070, apply=True, live_cwds=set())

    assert worktree.exists()
    assert git(repo, "rev-parse", "--verify", "codex/feature")
    assert any("not deletion proof" in entry["reason"] for entry in result.reap_results)
    assert result.ok is False
