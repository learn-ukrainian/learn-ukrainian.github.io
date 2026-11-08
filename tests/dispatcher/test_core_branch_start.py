"""Merged-PR delivery, branch-start attribution, stale refs and origin poisoning."""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest
from lu_machinery.dispatcher import cli, git, worker

from tests.dispatcher.conftest import MERGED, await_file, prior_worktree, run_git


def test_accepted_merged_pr_without_new_commits_is_delivered(merged_delivery_world):
    """Defect class: a task that landed a PR it accepted, with no commits of its own, was marked no_deliverable."""
    world = merged_delivery_world
    world.accept(77)
    world.prs[77], world.files[77] = MERGED, ["docs/owned.md"]
    worker._enforce_delivery(world.record)
    assert (world.record["status"], world.record["error"]) == ("done", None)
    assert world.record["delivery_pr"] == "org/repo#77"


def test_branch_reset_or_deleted_after_merge_is_delivered(merged_delivery_world):
    """Defect class: the task's own PR merged, then the branch was reset or deleted, so the check read a git error."""
    world = merged_delivery_world
    world.record["commits_ahead"] = 2
    world.listed = [{"number": 78, "isCrossRepository": False, "headRefName": "claude/merge-probe"}]
    world.prs[78], world.files[78] = MERGED, ["docs/owned.md"]
    worker._enforce_delivery(world.record)
    assert (world.record["status"], world.record["error"]) == ("done", None)
    assert world.record["delivery_pr"] == "org/repo#78"


def test_merged_pr_outside_owned_paths_is_still_refused(merged_delivery_world):
    """Control: a merged PR is no licence to change paths outside the task's ownership."""
    world = merged_delivery_world
    world.accept(79)
    world.prs[79], world.files[79] = MERGED, ["docs/owned.md", "scripts/elsewhere.py"]
    worker._enforce_delivery(world.record)
    assert (world.record["status"], world.record["error"]) == (
        "no_deliverable", "outside_owned_paths: scripts/elsewhere.py")
    # A name that only differs from an owned path by a trailing newline is not that path.
    world.record.update(status="done", error=None)
    world.files[79] = ["docs/owned.md\n"]
    worker._enforce_delivery(world.record)
    assert world.record["status"] == "no_deliverable"
    assert world.record["error"].startswith("outside_owned_paths: docs/owned.md")


@pytest.mark.parametrize("fault", [
    "open-pr", "merged-before-start", "foreign-base", "unpublished-head", "github-timeout", "ledger-unreadable",
    "missing-field",
])
def test_unpushed_change_without_a_provable_merged_delivery_is_still_refused(merged_delivery_world, fault):
    """Control: unpushed work, even beside a merged, stale or foreign PR or a failed lookup, keeps its exact refusal."""
    from lu_machinery.orchestration import pr_ownership

    world = merged_delivery_world
    world.accept(80)
    world.prs[80], world.files[80] = dict(MERGED), ["docs/owned.md"]
    world.record["commits_ahead"] = 1
    expected = "owned_paths_verification_failed: git fetch failed"
    if fault == "open-pr":
        world.prs[80]["state"] = "OPEN"
    elif fault == "merged-before-start":
        world.prs[80]["mergedAt"] = "2026-10-29T07:00:00Z"
    elif fault == "foreign-base":
        world.prs[80]["baseRefName"] = "other"
    elif fault == "unpublished-head":
        # Merged work must not hide a further local commit that was never pushed.
        world.published = (None, False)
    elif fault == "github-timeout":
        world.lookup_error = subprocess.TimeoutExpired(["gh"], 60)
    elif fault == "ledger-unreadable":
        pr_ownership.state_path().write_text("{")
    else:
        del world.record["commits_ahead"]
        world.published = (None, False)
        expected = "no_commits_or_unknown"
    worker._enforce_delivery(world.record)
    assert (world.record["status"], world.record["error"]) == ("no_deliverable", expected)
    assert "delivery_pr" not in world.record
    if fault == "open-pr":
        world.record.update(status="done", owned_paths=None)
        worker._enforce_delivery(world.record)
        assert world.record["error"] == "work_not_pushed_or_unknown"


@pytest.mark.parametrize("reuse_cwd", [False, True])
def test_preexisting_branch_commits_are_not_attributed_to_new_task(sandbox, reuse_cwd, monkeypatch):
    if reuse_cwd:
        tree = prior_worktree(sandbox)
        flags = ["--cwd", str(tree)]
    else:
        tree = sandbox.repo
        run_git(tree, "checkout", "-b", "feature-x")
        flags = ["--branch", "feature-x"]
    (tree / "outside.txt").write_text("previous task\n")
    run_git(tree, "add", "outside.txt")
    run_git(tree, "commit", "-m", "preexisting outside scope")
    starting_head = run_git(tree, "rev-parse", "HEAD")
    if not reuse_cwd:
        run_git(tree, "push", "origin", "feature-x")
    result = sandbox.settle(sandbox.dispatch("pushed", "--mode", "workspace-write",
                                            "--owned-path", "delivered.txt", *flags))
    assert result["worktree_base_sha"] == starting_head
    assert (result["status"], result["error"]) == ("done", None)
    # Settlement can now remove this published tree; restore the exact head for the older-Git proof.
    if not Path(result["worktree_path"]).exists():
        run_git(sandbox.repo, "worktree", "add", "--detach", result["worktree_path"], result["head_sha"])
    original = git._verification_git
    monkeypatch.setattr(git, "_verification_git", lambda path, command, *args, **kw:
                        "git version 2.35.0" if command == "version" else original(path, command, *args, **kw))
    worker._enforce_delivery(result)
    assert (result["status"], result["error"]) == ("done", None)


@pytest.mark.parametrize("attach", ["branch", "pinned-head", "cwd"])
@pytest.mark.parametrize("new_path", ["delivered.txt", "new-outside.txt"])
def test_branch_fix_round_ownership_starts_after_preexisting_commits(sandbox, attach, new_path):
    tree = prior_worktree(sandbox)
    base = run_git(sandbox.repo, "rev-parse", "origin/main")
    (tree / "earlier-outside.txt").write_text("previous round\n")
    run_git(tree, "add", "earlier-outside.txt")
    run_git(tree, "commit", "-m", "previous round outside current scope")
    starting_head = run_git(tree, "rev-parse", "HEAD")
    branch = "codex/prior-round"
    run_git(tree, "push", "origin", "HEAD")
    flags = ["--cwd", str(tree)] if attach == "cwd" else ["--branch", branch]
    if attach == "pinned-head":
        flags += ["--pinned-head", starting_head]
    task = sandbox.dispatch("blocked", "--mode", "workspace-write", "--owned-path", "delivered.txt", *flags)
    path = sandbox.tasks / f"{task[0]}.json"
    record = json.loads(path.read_text())
    await_file(Path(record["prompt_file"]).with_suffix(".started"))
    tree = Path(record["cwd"])
    (tree / new_path).write_text("current round\n")
    run_git(tree, "add", new_path)
    run_git(tree, "commit", "-m", "current round delivery")
    run_git(tree, "push", "origin", f"HEAD:{branch}")
    Path(record["prompt_file"]).with_suffix(".release").touch()
    outside = new_path != "delivered.txt"
    result = sandbox.settle(task, expected=1 if outside else 0)
    if attach != "cwd":
        # Settlement removed the published worktree; re-attach it at its head for the recheck below.
        assert (result["worktree_disposition"], result.get("worktree_disposition_reason")) == ("removed", "clean")
        run_git(sandbox.repo, "worktree", "add", "-b", result["worktree_branch"], result["cwd"], result["head_sha"])
    # Recheck the reported defect's record shape: base is main, start is the branch tip.
    # Keep the actual start captured at dispatch, independent of the configured base.
    result.update(worktree_base_sha=base, status="done", error=None)
    result.update(git.snapshot_delivery(worker._spec(result, {}), result))
    worker._enforce_delivery(result)
    assert (result["status"], result["error"]) == (
        ("no_deliverable", "outside_owned_paths: new-outside.txt") if outside else ("done", None)
    )
    assert result["worktree_start_sha"] == starting_head
    assert result["worktree_base_sha"] == base
    assert result["commits_ahead"] == 1
    assert result["push_state"] == "pushed"
    assert result["remote_head_sha"] == result["head_sha"]


@pytest.mark.parametrize("pinned", [False, True])
@pytest.mark.parametrize("new_path", ["delivered.txt", "new-outside.txt"])
def test_branch_fix_round_uses_remote_start_when_local_branch_is_stale(sandbox, pinned, new_path, monkeypatch):
    branch = "codex/existing-pr"
    stale_head = run_git(sandbox.repo, "rev-parse", "HEAD")
    run_git(sandbox.repo, "branch", branch)
    previous_tree = prior_worktree(sandbox)
    (previous_tree / "earlier-outside.txt").write_text("previous author round\n")
    run_git(previous_tree, "add", "earlier-outside.txt")
    run_git(previous_tree, "commit", "-m", "earlier outside-scope delivery")
    remote_start = run_git(previous_tree, "rev-parse", "HEAD")
    run_git(previous_tree, "push", "origin", f"HEAD:{branch}")
    assert run_git(sandbox.repo, "rev-parse", branch) == stale_head
    if not pinned:
        # Change shared refs and URL rewrites after origin validation. Neither may
        # replace the object advertised through the private canonical origin.
        run_git(previous_tree, "commit", "--allow-empty", "-m", "unpublished local tip")
        planted = run_git(previous_tree, "rev-parse", "HEAD")
        alternate = sandbox.repo.parent / "alternate.git"
        run_git(sandbox.repo, "init", "--bare", str(alternate))
        run_git(previous_tree, "push", str(alternate), f"HEAD:{branch}")
        original = git._verification_git
        rewrite = f"url.{alternate}.insteadOf"
        def race(path, command, *args, **kwargs):
            if command == "init":
                run_git(sandbox.repo, "config", rewrite, str(sandbox.remote))
                run_git(sandbox.repo, "config", "remote.origin.url", str(alternate))
            result = original(path, command, *args, **kwargs)
            if command in {"ls-remote", "fetch"}:
                run_git(sandbox.repo, "update-ref", f"refs/remotes/origin/{branch}", planted)
            return result
        with monkeypatch.context() as injected:
            injected.setattr(git, "_verification_git", race)
            resolved, remote = git.publish_start(
                sandbox.repo, {"github": str(sandbox.remote), "transport": "file"}, branch, "private-start",
            )
        assert (resolved, remote) == (remote_start, str(sandbox.remote))
        assert run_git(sandbox.repo, "rev-parse", f"refs/remotes/origin/{branch}") == planted
        run_git(sandbox.repo, "config", "--unset", rewrite)
        run_git(sandbox.repo, "config", "remote.origin.url", str(sandbox.remote))
    flags = ["--branch", branch]
    if pinned:
        flags += ["--pinned-head", remote_start]
    task = sandbox.dispatch("blocked", "--mode", "workspace-write", "--owned-path", "delivered.txt", *flags)
    record = json.loads((sandbox.tasks / f"{task[0]}.json").read_text())
    await_file(Path(record["prompt_file"]).with_suffix(".started"))
    tree = Path(record["cwd"])
    # A fix worker synchronizes the already-published PR before adding its own commit.
    run_git(tree, "fetch", "origin", branch)
    run_git(tree, "merge", "--ff-only", f"origin/{branch}")
    (tree / new_path).write_text("fix round\n")
    run_git(tree, "add", new_path)
    run_git(tree, "commit", "-m", "current fix round")
    run_git(tree, "push", "origin", f"HEAD:{branch}")
    Path(record["prompt_file"]).with_suffix(".release").touch()
    outside = new_path != "delivered.txt"
    result = sandbox.settle(task, expected=1 if outside else 0)
    assert (result["status"], result["error"]) == (
        ("no_deliverable", "outside_owned_paths: new-outside.txt") if outside else ("done", None)
    )
    assert result["worktree_start_sha"] == remote_start
    assert result["commits_ahead"] == 1
    assert result["push_state"] == "pushed"
    assert result["remote_head_sha"] == result["head_sha"]
    assert run_git(sandbox.repo, "rev-parse", branch) == stale_head


def test_branch_write_starts_at_advertised_object_despite_shared_replace_ref(sandbox):
    """A shared replace ref must not change the published start's checkout or record."""
    branch = "codex/existing-pr"
    advertised = run_git(sandbox.repo, "rev-parse", "HEAD")
    run_git(sandbox.repo, "push", "origin", f"HEAD:refs/heads/{branch}")
    run_git(sandbox.repo, "checkout", "-b", "planted")
    (sandbox.repo / "outside.txt").write_text("outside current ownership\n")
    run_git(sandbox.repo, "add", "outside.txt")
    run_git(sandbox.repo, "commit", "-m", "local outside-scope commit")
    run_git(sandbox.repo, "replace", advertised, run_git(sandbox.repo, "rev-parse", "HEAD"))
    run_git(sandbox.repo, "checkout", "main")
    task = sandbox.dispatch("pushed", "--mode", "workspace-write", "--owned-path", "delivered.txt", "--branch", branch)
    result = sandbox.settle(task)
    assert not (Path(result["cwd"]) / "outside.txt").exists()
    assert result["worktree_start_sha"] == advertised
    assert (result["status"], result["error"], result["commits_ahead"]) == ("done", None, 1)


def test_branch_write_refuses_local_outside_commit_after_remote_branch_deleted(sandbox):
    """A deleted remote must not let a planted local commit escape ownership."""
    branch = "codex/existing-pr"
    run_git(sandbox.repo, "branch", branch)
    run_git(sandbox.repo, "push", "origin", branch)
    (sandbox.repo / "outside.txt").write_text("outside current ownership\n")
    run_git(sandbox.repo, "add", "outside.txt")
    run_git(sandbox.repo, "commit", "-m", "local outside-scope commit")
    planted = run_git(sandbox.repo, "rev-parse", "HEAD")
    run_git(sandbox.repo, "update-ref", f"refs/heads/{branch}", planted)
    run_git(sandbox.repo, "push", "origin", f":refs/heads/{branch}")
    result = subprocess.run(
        [sys.executable, "scripts/dispatch.py", "dispatch", "--agent", "sol", "--model", "pushed",
         "--prompt", "literal final response", "--task-id", "missing-remote", "--mode", "workspace-write",
         "--owned-path", "delivered.txt", "--branch", branch],
        cwd=sandbox.repo, env=sandbox.env, text=True, capture_output=True, timeout=30,
    )
    if result.returncode == 0:
        accepted = sandbox.settle(tuple(result.stdout.splitlines()))
        assert accepted["worktree_start_sha"] == planted
        assert (Path(accepted["cwd"]) / "outside.txt").read_text() == "outside current ownership\n"
        print(f"Deleted-remote delivery accepted: status={accepted['status']}, error={accepted['error']}")
    assert result.returncode == 2, (result.stdout, result.stderr)
    assert "publish branch is absent from the canonical remote" in result.stderr
    assert not (sandbox.tasks / "missing-remote.json").exists()
    assert not (sandbox.repo / ".worktrees/dispatch/codex/missing-remote").exists()


def test_workspace_write_sha_base_is_refused_at_dispatch(sandbox):
    """A commit SHA is not an origin base, so settlement would record no_deliverable."""
    sha = run_git(sandbox.repo, "rev-parse", "HEAD")
    result = sandbox.cli(
        "dispatch", "--agent", "sol", "--model", "echo", "--prompt", "literal final response",
        "--task-id", "sha-base-write", "--mode", "workspace-write", "--base", sha,
        expected=2,
    )
    assert "workspace_write_base_unverified:" in result.stderr
    assert "--base origin/main --branch <PR head branch>" in result.stderr
    assert "with the PR's files as owned paths" in result.stderr
    assert not (sandbox.tasks / "sha-base-write.json").exists()
    assert not (sandbox.repo / ".worktrees/dispatch/codex/sha-base-write").exists()


def test_workspace_write_base_equal_to_branch_is_refused_at_dispatch(sandbox):
    """A publish branch used as its own base is refused before a task or worktree exists (#12667)."""
    branch = "codex/existing-pr"
    remote_head = _published_branch(sandbox, branch)
    refused = sandbox.cli(
        "dispatch", "--agent", "sol", "--model", "echo", "--prompt", "takeover",
        "--task-id", "base-equals-branch", "--mode", "workspace-write",
        "--owned-path", "delivered.txt", "--base", f"origin/{branch}", "--branch", branch,
        expected=2,
    )
    assert "workspace_write_base_equals_branch:" in refused.stderr
    assert "--base origin/main --branch <PR head branch>" in refused.stderr
    assert "with the PR's files as owned paths" in refused.stderr
    assert not (sandbox.tasks / "base-equals-branch.json").exists()
    assert not (sandbox.repo / ".worktrees/dispatch/codex/base-equals-branch").exists()
    # refs/remotes/origin/<branch> is the same base, and it is refused the same way.
    prefixed = sandbox.cli(
        "dispatch", "--agent", "sol", "--model", "echo", "--prompt", "takeover",
        "--task-id", "base-equals-branch-prefixed", "--mode", "workspace-write",
        "--owned-path", "delivered.txt", "--base", f"refs/remotes/origin/{branch}", "--branch", branch,
        expected=2,
    )
    assert "workspace_write_base_equals_branch:" in prefixed.stderr
    assert not (sandbox.tasks / "base-equals-branch-prefixed.json").exists()
    # The allowed form still dispatches: origin/main with a different publish branch.
    allowed = sandbox.settle(sandbox.dispatch(
        "pushed", "--task-id", "base-is-main", "--mode", "workspace-write",
        "--owned-path", "delivered.txt", "--base", "origin/main", "--branch", branch,
    ))
    assert (allowed["status"], allowed["error"]) == ("done", None)
    assert allowed["worktree_base_ref"] == "origin/main"
    assert allowed["publish_branch"] == branch
    assert allowed["worktree_start_sha"] == remote_head


def test_read_only_sha_base_is_still_admitted(sandbox):
    """Read-only reviews keep a commit SHA as --base; settlement does not verify it."""
    sha = run_git(sandbox.repo, "rev-parse", "HEAD")
    record = sandbox.settle(sandbox.dispatch("echo", "--task-id", "sha-base-read", "--mode", "read-only", "--base", sha))
    assert record["status"] == "done"
    assert record["mode"] == "read-only"
    assert record["worktree_base_ref"] == sha


def test_stale_local_ref_never_yields_read_only_checkout_at_stale_commit(sandbox):
    """Defect (#12441): a branch-pinned read-only dispatch ran at a stale local ref, ignoring --base."""
    sandbox.review_models("echo")
    stale = run_git(sandbox.repo, "commit-tree", "HEAD^{tree}", "-p", "HEAD", "-m",
                    "stale authored change\n\nX-Agent: claude/claude-opus-5-5")
    run_git(sandbox.repo, "branch", "review-stale", stale)
    run_git(sandbox.repo, "push", "origin", "review-stale")
    remote_head = run_git(sandbox.repo, "commit-tree", "HEAD^{tree}", "-p", stale, "-m",
                          "newer authored change\n\nX-Agent: claude/claude-opus-5-5")
    run_git(sandbox.repo, "push", "origin", f"{remote_head}:refs/heads/review-stale")
    assert run_git(sandbox.repo, "rev-parse", "refs/heads/review-stale") == stale
    record = sandbox.settle(sandbox.dispatch(
        "echo", "--task-id", "stale-local-ref", "--mode", "read-only",
        "--branch", "review-stale", "--base", remote_head,
    ))
    assert record["status"] == "done"
    assert record["worktree_start_sha"] == remote_head
    assert record["pinned_head"] == remote_head
    assert record["head_sha"] == remote_head
    # The fix never moves the primary checkout's local branch ref.
    assert run_git(sandbox.repo, "rev-parse", "refs/heads/review-stale") == stale
    refused = sandbox.cli(
        "dispatch", "--agent", "sol", "--model", "echo", "--prompt", "review",
        "--task-id", "stale-local-ref-mismatch", "--mode", "read-only",
        "--branch", "review-stale", "--base", stale, expected=2,
    )
    assert "read_only_branch_base_mismatch:" in refused.stderr
    assert not (sandbox.tasks / "stale-local-ref-mismatch.json").exists()
    # Git accepts unique abbreviations from four characters; they refuse the same way.
    short = sandbox.cli(
        "dispatch", "--agent", "sol", "--model", "echo", "--prompt", "review",
        "--task-id", "stale-local-ref-short", "--mode", "read-only",
        "--branch", "review-stale", "--base", stale[:6], expected=2,
    )
    assert "read_only_branch_base_mismatch:" in short.stderr
    assert not (sandbox.tasks / "stale-local-ref-short.json").exists()


def _published_branch(sandbox, name):
    """Push ``name`` to origin at a commit that is not the local ``name`` (if any)."""
    remote_head = run_git(sandbox.repo, "commit-tree", "HEAD^{tree}", "-p", "HEAD", "-m", "remote pr head")
    run_git(sandbox.repo, "push", "origin", f"{remote_head}:refs/heads/{name}")
    return remote_head


def _write_branch_plan(sandbox, branch, *extra):
    result = sandbox.cli(
        "dispatch", "--agent", "sol", "--model", "echo", "--prompt", "takeover", "--mode", "workspace-write",
        "--owned-path", "delivered.txt", "--branch", branch, "--dry-run", *extra,
    )
    assert not sandbox.tasks.exists()
    return json.loads(result.stdout)


def test_write_branch_dry_run_without_local_ref_starts_at_remote_head(sandbox):
    """Defect (#12468): a write --branch preview rev-parsed a missing local ref and died as CalledProcessError."""
    remote_head = _published_branch(sandbox, "takeover-no-local")
    assert not run_git(sandbox.repo, "branch", "--list", "takeover-no-local")
    assert _write_branch_plan(sandbox, "takeover-no-local")["start_sha"] == remote_head
    assert not run_git(sandbox.repo, "branch", "--list", "takeover-no-local")


def test_write_branch_dry_run_ignores_stale_local_ref(sandbox):
    """Defect (#12468): a stale local refs/heads/<branch> must never set the start of a takeover."""
    stale = run_git(sandbox.repo, "rev-parse", "HEAD")
    run_git(sandbox.repo, "branch", "takeover-stale", stale)
    remote_head = _published_branch(sandbox, "takeover-stale")
    assert _write_branch_plan(sandbox, "takeover-stale")["start_sha"] == remote_head
    assert run_git(sandbox.repo, "rev-parse", "refs/heads/takeover-stale") == stale
    refused = sandbox.cli(
        "dispatch", "--agent", "sol", "--model", "echo", "--prompt", "takeover", "--mode", "workspace-write",
        "--owned-path", "delivered.txt", "--branch", "takeover-missing", "--dry-run", expected=2,
    )
    assert "branch_absent_on_remote:" in refused.stderr and "takeover-missing" in refused.stderr


def test_failed_git_call_reports_its_operation_and_a_constant_summary_without_secrets(capsys, monkeypatch):
    """Defect (#12468): a failed git call printed only the exception class name.

    Nothing user-controlled is printed: the subcommand and a summary chosen from the first stderr line, both
    constants. Every disclosure probe from the review of the first attempt must end in them.
    """
    def fail(command, stderr):
        error = subprocess.CalledProcessError(128, [command[0], "-C", "/home/ops/private", *command[1:]], stderr=stderr)
        monkeypatch.setattr(cli, "_dispatch", Mock(side_effect=error))
        assert cli.main(["dispatch", "--agent", "sol", "--model", "echo", "--prompt", "x"]) == 2
        return capsys.readouterr().err

    assert fail(["git", "rev-parse", "--verify", "topic^{commit}"], "fatal: Needed a single revision") == (
        "dispatcher: CalledProcessError: git rev-parse exited 128: needed a single revision\n")
    assert fail(["git", "fetch", "--", "https://user:token@example.com/org/repo.git", "abc"],
                "fatal: could not read from https://user:token@example.com/org/repo.git\nsecond line\n") == (
        "dispatcher: CalledProcessError: git fetch exited 128: remote not reachable\n")
    assert fail(["curl", "https://example.com"], "secret") == "dispatcher: CalledProcessError: external command exited 128\n"
    assert fail(["/usr/bin/git", "fetch"], "fatal: could not read from x") == (
        "dispatcher: CalledProcessError: git fetch exited 128: remote not reachable\n")
    assert fail(["git", "--git-dir", "/synthetic/x", "fetch"], "fatal: denied") == (
        "dispatcher: CalledProcessError: git fetch exited 128: unrecognized git error\n")
    summaries = {text for _pattern, text in cli._GIT_FAILURES} | {cli.UNRECOGNIZED_GIT_FAILURE}
    for command, stderr, leaked in (
        (["git", "fetch"], "remote: Authorization: Bearer SYNTHETIC_SECRET", "SYNTHETIC_SECRET"),
        (["git", "fetch"], "remote: Password: shallow branch denied object", "shallow"),
        (["git", "fetch"], "fatal: cannot open '/synthetic/Acme Open Access Client/repo': denied", "Access"),
        (["git", "fetch"], "fatal: Unable to create '/synthetic/private directory/worktree/index.lock': denied", "worktree"),
        (["git", "worktree", "add", "--no-checkout", "worktree", "status"], "remote: secret", "worktree status"),
        (["git", "fetch", "user:syntheticsecret"], "fatal: denied", "syntheticsecret"),
    ):
        message = fail(command, stderr)
        assert message.rstrip("\n").rsplit(": ", 1)[1] in summaries
        assert leaked not in message and "synthetic" not in message.lower() and "/home/ops/private" not in message


def test_scope_error_is_bounded_and_local_base_fails_closed(delivery_settle, monkeypatch):
    record, settle = delivery_settle
    record = settle("pushed")
    original = git._verification_git
    monkeypatch.setattr(git, "_verification_git", lambda path, command, *args, **kw:
                        "\0".join(f"outside-{n:04d}.txt" for n in range(200)) if command == "log"
                        else original(path, command, *args, **kw))
    worker._enforce_delivery(record)
    assert record["status"] == "no_deliverable"
    assert record["error"].startswith("outside_owned_paths: outside-0000.txt")
    assert len(record["error"]) <= 1024
    assert record["error"].endswith("... (truncated)")
    record.update(status="done", worktree_base_ref="main")
    worker._enforce_delivery(record)
    assert (record["status"], record["error"]) == ("no_deliverable", "owned_paths_verification_failed: ownership verification requires an origin base")


@pytest.mark.parametrize("transport", ["ssh", "https"])
def test_canonical_origins_does_not_reject_same_identity_when_clone_transport_differs(transport):
    """Clone transport mismatches must not reject the registered repository identity."""
    origins = git.canonical_origins({"github": "org/repo", "transport": transport})
    assert "https://github.com/org/repo.git" in origins
    accepted = {
        "https://github.com/org/repo.git", "https://github.com/org/repo",
        "git@github.com:org/repo.git", "git@github.com:org/repo",
        "ssh://git@github.com/org/repo.git", "ssh://git@github.com/org/repo",
    }
    assert set(origins) == accepted
    assert len(origins) == len(accepted)
    refused = [
        "https://github.com/org/other.git", "git@github.com:org/other.git", "https://github.com/org/rep.git",
        "https://github.com/org/repo-fork.git", "https://github.com/someone/repo.git", "git@github.com:someone/repo.git",
        "https://gitlab.com/org/repo.git", "git@gitlab.com:org/repo.git", "ssh://git@example.com/org/repo.git",
        "/srv/org/repo.git", "file:///srv/org/repo.git", "https://user:token@github.com/org/repo.git",
        "https://token@github.com/org/repo.git", "ssh://user:token@github.com/org/repo.git",
        "https://github.com/Org/repo.git", "https://GitHub.com/org/repo.git", "git@github.com:org/Repo.git",
        "https://github.com/org/repo/", "https://github.com/org/repo.git/", "git@github.com:org/repo.git/",
        "https://github.com/org/repo.git.bak", "git@github.com:org/repo.gitx", "https://github.com/org/repo.git/extra",
        " https://github.com/org/repo.git", "\tgit@github.com:org/repo.git", "https://github.com/org/repo.git\n",
    ]
    for origin in refused:
        assert origin not in origins


def test_prior_worker_origin_poisoning_refuses_dispatch_and_fails_closed(sandbox):
    """Shared config poisoned before dispatch cannot certify a forged empty range."""
    earlier = sandbox.settle(sandbox.dispatch("unpushed", "--mode", "workspace-write"), expected=1)
    fake = sandbox.repo.parent / "forged.git"
    tree = Path(earlier["cwd"])
    run_git(tree, "clone", "--bare", str(sandbox.remote), str(fake))
    run_git(tree, "remote", "set-url", "origin", str(fake))
    result = sandbox.cli(
        "dispatch", "--agent", "sol", "--model", "pushed", "--prompt", "deliver",
        "--task-id", "poisoned", "--mode", "workspace-write", "--owned-path", "delivered.txt", expected=2,
    )
    assert "origin must match the registered canonical repository URL" in result.stderr
    assert not (sandbox.tasks / "poisoned.json").exists()
    assert not (sandbox.tasks / "poisoned.started").exists()
    # Read-only admission still records missing trust; even a later write settle fails closed.
    record = sandbox.settle(sandbox.dispatch())
    assert record["worktree_remote_url"] is None
    # Its own worktree was removed at settlement; forge the delivery from an earlier round's worktree.
    tree = prior_worktree(sandbox)
    for name in ("outside.txt", "delivered.txt"):
        (tree / name).write_text("forged delivery\n")
    run_git(tree, "add", "outside.txt", "delivered.txt")
    run_git(tree, "commit", "-m", "forged delivery")
    run_git(tree, "push", "origin", f"HEAD:refs/heads/{record['worktree_branch']}", "HEAD:main")
    record.update(
        worktree_path=str(tree), cwd=str(tree), mode="workspace-write", owned_paths=["delivered.txt"], head_sha=run_git(tree, "rev-parse", "HEAD"),
        push_state="pushed", commits_ahead=1, worktree_dirty_on_exit=False,
    )
    assert run_git(fake, "rev-parse", "main") == record["head_sha"]
    assert run_git(sandbox.remote, "rev-parse", "main") == record["worktree_base_sha"]
    worker._enforce_delivery(record)
    assert record["status"] == "no_deliverable"
    assert record["error"].startswith("owned_paths_verification_failed: ")
