"""Exact-head delivery, review checkout, dry-run flags and contributor mode."""

import json
import os
import signal
from pathlib import Path

import pytest

from scripts.dispatcher import git, worker
from scripts.dispatcher.cli import ALIASES
from scripts.review.record_cf_verdict import _review_branch
from tests.dispatcher.conftest import await_file, run_git


@pytest.mark.parametrize(
    ("target", "commits", "dirty", "expected", "reason", "crash"),
    [
        ("pinned", 1, False, "pushed", "remote_head_matches", False),
        ("pinned", 1, False, "pushed", "remote_head_matches", True),
        ("own", 1, False, "pushed", "remote_head_matches", False),
        ("unrelated", 1, False, "unpushed", "remote_head_differs", False),
        ("prefix", 1, False, "unpushed", "remote_branch_missing", False),
        ("pinned", 1, True, "unpushed", "dirty_worktree", False),
        (None, 0, False, "unpushed", "remote_branch_missing", False),
        ("pinned", 0, False, "pushed", "remote_head_matches", False),
    ],
)
@pytest.mark.parametrize("preexisting", [False, True])
def test_delivery_only_counts_exact_heads_on_authorized_branches(
    sandbox, target, commits, dirty, expected, reason, crash, preexisting,
):
    """Prefix tricks and supervisor crashes cannot falsify pinned-branch delivery evidence."""
    pinned = "codex/existing-pr"
    run_git(sandbox.repo, "checkout", "-b", pinned, "main")
    if preexisting:
        (sandbox.repo / "earlier.txt").write_text("previous round\n")
        run_git(sandbox.repo, "add", "earlier.txt")
        run_git(sandbox.repo, "commit", "-m", "preexisting branch commit")
    starting_head = run_git(sandbox.repo, "rev-parse", "HEAD")
    run_git(sandbox.repo, "checkout", "main")
    run_git(sandbox.repo, "push", "origin", pinned)
    task = sandbox.dispatch("blocked", "--mode", "workspace-write", "--branch", pinned)
    record_path = sandbox.tasks / f"{task[0]}.json"
    record = json.loads(record_path.read_text())
    assert record["publish_branch"] == pinned
    child = int(await_file(Path(record["prompt_file"]).with_suffix(".started")))
    if target in {None, "prefix"}:
        run_git(sandbox.repo, "push", "origin", f":refs/heads/{pinned}")
    worktree = Path(record["worktree_path"])
    branch = record["worktree_branch"]
    if commits:
        (worktree / "fix.txt").write_text("fix round\n")
        run_git(worktree, "add", "fix.txt")
        run_git(worktree, "commit", "-m", "fix round")
    remote_branch = {
        "pinned": pinned, "own": branch, "unrelated": "codex/unrelated", "prefix": f"x/refs/heads/{pinned}",
    }.get(target)
    if remote_branch:
        run_git(worktree, "push", "origin", f"HEAD:refs/heads/{remote_branch}")
    if dirty:
        (worktree / "uncommitted.txt").write_text("still local\n")
    head = run_git(worktree, "rev-parse", "HEAD")
    if crash:
        before_crash = git.snapshot_delivery(worker._spec(record, {}), record)
        assert before_crash["push_state"] == "pushed"
        assert before_crash["remote_ref"] == f"refs/heads/{pinned}"
        os.kill(record["pid"], signal.SIGKILL)
        os.killpg(child, signal.SIGKILL)
    else:
        Path(record["prompt_file"]).with_suffix(".release").touch()
    delivery_error = (
        "worktree_dirty_or_unknown" if dirty else "no_commits_or_unknown" if not commits
        else "work_not_pushed_or_unknown" if expected != "pushed" else None
    )
    observed = sandbox.settle(task, expected=1 if crash or delivery_error else 0)
    assert observed["status"] == ("crashed" if crash else "no_deliverable" if delivery_error else "done")
    if not crash:
        assert observed.get("no_deliverable_reason") == delivery_error
    matched = remote_branch if target in {"pinned", "own"} else None
    assert observed["push_state"] == expected
    assert observed["push_state_reason"] == reason
    assert observed["publish_branch"] == pinned
    assert observed["remote_ref"] == (f"refs/heads/{matched}" if matched else None)
    if crash:
        assert observed["remote_ref"] == before_crash["remote_ref"]
    assert observed["head_sha"] == head
    assert observed["commits_ahead"] == commits
    assert observed["worktree_start_sha"] == starting_head
    assert observed["worktree_dirty_on_exit"] is dirty
    if matched:
        assert observed["remote_head_sha"] == head
        assert run_git(sandbox.remote, "rev-parse", f"refs/heads/{matched}") == head
    else:
        assert observed["remote_head_sha"] == (starting_head if target not in {None, "prefix"} else None)


def test_review_uses_exact_commit_on_fresh_branch_and_cwd_reuses(sandbox):
    task = sandbox.dispatch("unpushed", "--mode", "workspace-write")
    first = sandbox.settle(task, expected=1)
    # A read-only --branch dispatch is a review (C-2902 F10): attribute the stub delivery to a family
    # outside the stub reviewer's, keeping its tree and parent.
    sandbox.review_models("echo")
    head = run_git(sandbox.repo, "commit-tree", f"{first['head_sha']}^{{tree}}", "-p", f"{first['head_sha']}^",
                   "-m", "stub delivery\n\nX-Agent: claude/claude-opus-5-5")
    run_git(sandbox.repo, "update-ref", f"refs/heads/{first['worktree_branch']}", head)
    result = sandbox.cli(
        "dispatch",
        "--agent",
        "sol",
        "--model",
        "echo",
        "--prompt",
        "review",
        "--branch",
        first["worktree_branch"],
        "--pinned-head",
        head,
    )
    review = sandbox.settle(result.stdout.splitlines())
    assert review["worktree_base_sha"] == head
    assert review["pinned_head"] == head
    assert review["review_branch"] == first["worktree_branch"]
    assert _review_branch(review) == first["worktree_branch"]
    assert review["worktree_branch"] != first["worktree_branch"]
    assert review["push_state"] == "not_applicable"
    assert not Path(review["cwd"]).exists()
    reused = sandbox.settle(sandbox.dispatch("echo", "--cwd", first["cwd"]))
    assert (reused["cwd"], reused["worktree_disposition_reason"]) == (first["cwd"], "borrowed_worktree")
    assert Path(first["cwd"]).is_dir()
    assert run_git(sandbox.repo, "branch", "--show-current") == "main"


def test_selected_sibling_repo_keeps_records_in_shared_store(sandbox):
    private = sandbox.repo.parent / "private"
    private.mkdir()
    run_git(private, "init", "-b", "main")
    run_git(private, "config", "user.name", "Stub")
    run_git(private, "config", "user.email", "stub@example.invalid")
    run_git(private, "commit", "--allow-empty", "-m", "private fixture")
    task = sandbox.dispatch("echo", "--repo", "private", "--base", "main")
    record = sandbox.settle(task)
    assert record["repo"] == "private"
    assert record["repository_id"] == record["repository"] == "example/private"
    assert Path(record["cwd"]).is_relative_to(private / ".worktrees/dispatch/codex")
    assert Path(record["prompt_file"]).parent == sandbox.tasks
    assert run_git(private, "branch", "--show-current") == "main"


@pytest.mark.parametrize("mode", ["read-only", "workspace-write"])
def test_dry_run_and_invalid_flags_create_nothing(sandbox, mode):
    before = run_git(sandbox.repo, "branch", "--list")
    result = sandbox.cli("dispatch", "--agent", "sol", "--model", "echo", "--prompt", "preview", "--dry-run")
    plan = json.loads(result.stdout)
    assert plan["argv"][2] == "echo"
    assert not Path(plan["worktree"]).exists()
    assert not sandbox.tasks.exists()
    assert run_git(sandbox.repo, "branch", "--list") == before
    sandbox.cli("dispatch", "--agent", "sol", "--model", "echo", "--prompt", "x", "--force-new", expected=2)
    sandbox.cli("dispatch", "--agent", "sol", "--model", "echo", "--prompt", "x", "--prompt-file", "y", expected=2)
    for include in ("../curriculum", "site/src", "unknown", ""):
        sandbox.cli("dispatch", "--agent", "sol", "--model", "echo", "--prompt", "x", "--sparse-include", include, expected=2)
    for branch in ("unsafe..branch", "origin/feature", "refs/heads/feature", "bad:name", ""):
        sandbox.cli(
            "dispatch", "--agent", "sol", "--model", "echo", "--prompt", "x",
            "--mode", mode, "--branch", branch,
            "--pinned-head", run_git(sandbox.repo, "rev-parse", "HEAD"), expected=2,
        )
    assert run_git(sandbox.repo, "branch", "--list") == before
    assert not sandbox.tasks.exists()


@pytest.mark.parametrize("contributor", ["on", "off", None])
def test_muse_cli_forwards_contributor_mode_and_keeps_auditable_record(sandbox, contributor):
    """Missing CLI options must not silently force explicit contributor requests off."""
    args = ["dispatch", "--agent", "muse", "--model", "muse-wonder-full-1.0", "--prompt", "public input"]
    if contributor is not None:
        args += ["--contributor-mode", contributor]
    plan = json.loads(sandbox.cli(*args, "--dry-run").stdout)
    argv = plan["argv"]
    assert argv[argv.index("--contributor-mode") + 1] == (contributor or "off")
    assert not sandbox.tasks.exists()
    assert not Path(plan["worktree"]).exists()

    # Keep the real confinement, file transport and parser; replace only the
    # paid runtime with the launcher's supported exact native-file layout.
    binary_dir = sandbox.repo.parent / "bin"
    binary_dir.mkdir(exist_ok=True)
    version = "0.0.0-R1"
    (binary_dir / ".muse-version").write_text(version)
    executable = binary_dir / "muse"
    executable.write_text('#!/bin/sh\nexec "$(dirname "$0")/muse-bin-0.0.0-R1" "$@"\n')
    native = binary_dir / f"muse-bin-{version}"
    native.write_text(r'''#!/bin/sh
set -eu
while [ "$#" -gt 0 ]; do
    if [ "$1" = "--prompt-file" ]; then
        shift
        prompt=$(cat "$1")
        break
    fi
    shift
done
case "$prompt" in '<rules-core seat="core"'*) ;; *) exit 1 ;; esac
case "$prompt" in *'</rules-core>'*'public input') ;; *) exit 1 ;; esac
printf '%s\n' '{"payload_type":"run.terminal.completed","payload":{"text":"Finished."}}'
''')
    executable.chmod(0o755)
    native.chmod(0o755)
    home = sandbox.repo.parent / "synthetic-home"
    home.mkdir()
    sandbox.env.update(HOME=str(home), XDG_CONFIG_HOME=str(home / ".config"))
    sandbox.env["PATH"] = str(binary_dir) + os.pathsep + sandbox.env["PATH"]
    task = sandbox.cli(*args).stdout.splitlines()
    record = sandbox.settle(task)
    assert record["contributor_mode"] == (contributor or "off")
    assert json.loads((sandbox.tasks / f"{task[0]}.json").read_text())["contributor_mode"] == (contributor or "off")


@pytest.mark.parametrize("agent", sorted((set(ALIASES) | set(ALIASES.values()) | {"claude"}) - {"muse"}))
@pytest.mark.parametrize("contributor", ["on", "off"])
def test_contributor_mode_refuses_non_muse_agents_without_side_effects(sandbox, agent, contributor):
    before = run_git(sandbox.repo, "branch", "--list")
    result = sandbox.cli(
        "dispatch",
        "--agent",
        agent,
        "--model",
        "echo",
        "--prompt",
        "public input",
        "--contributor-mode",
        contributor,
        expected=2,
    )
    assert result.stderr == "dispatcher: --contributor-mode is only supported with --agent muse\n"
    assert not sandbox.tasks.exists()
    assert run_git(sandbox.repo, "branch", "--list") == before
