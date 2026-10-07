"""Real worker-config tripwires for every cleanup caller in #9914.

Only external PR/liveness observations are controlled by the existing fixture;
Git, index reads, inventory, preservation and removal all execute in production.
"""

from __future__ import annotations

import json
import shlex
import shutil
import subprocess
from pathlib import Path

import pytest

from scripts import delegate
from scripts.fleet import sibling_git
from scripts.orchestration import stale_task_records, worktree_claims
from scripts.orchestration.fleet_repos import FleetRepo
from scripts.orchestration.task_family import git_safety
from tests.orchestration.test_merge_closeout import _REAL_RUN
from tests.orchestration.test_worktree_claims_cli import _git
from tests.orchestration.test_worktree_output_chokepoint import (
    boundary_remove,
)
from tests.orchestration.test_worktree_output_chokepoint import (
    boundary_tree as boundary_tree,
)

CALLERS = ["scheduled", "closeout", "post-task", "delegate", "task-family", "sibling", "stale-record"]


@pytest.fixture(autouse=True)
def _real_git_observations(boundary_tree, monkeypatch):
    """Stub GitHub observations without replacing subprocess.run for Git.

    The reused fixture installs a GitHub subprocess stub for its own tests.
    Restore the standard subprocess implementation before any marker setup
    or production call here, and move those observations to their API seams.
    """
    from scripts.fleet import post_task_reap
    from scripts.orchestration import merge_closeout, reap_worktrees

    monkeypatch.setattr(subprocess, "run", _REAL_RUN)
    _repo, tree, _tasks, _record = boundary_tree
    head = _git(tree, "rev-parse", "HEAD")
    pr = reap_worktrees.PullRequestState(number=9645, state="MERGED", head_sha=head)
    monkeypatch.setattr(
        reap_worktrees, "_query_pr_states",
        lambda _repo, branch: ([pr] if branch == "codex/boundary" else [], None),
    )
    monkeypatch.setattr(
        reap_worktrees, "_query_pr_by_number",
        lambda _repo, number: ([pr] if number == 9645 else [], None),
    )
    monkeypatch.setattr(reap_worktrees, "_query_prs_by_head_sha", lambda *_args, **_kwargs: ([], None))
    monkeypatch.setattr(
        merge_closeout, "fetch_pr_info",
        lambda *_args, **_kwargs: merge_closeout.PullRequestInfo(9645, "MERGED", "codex/boundary", head),
    )
    monkeypatch.setattr(post_task_reap.pr_identity, "probe_open_pr_for_branch", lambda **_kwargs: (False, None))
    assert subprocess.run is _REAL_RUN


def install_markers(repo: Path, tree: Path, root: Path) -> Path:
    marker = root / "executed"
    program = root / "tripwire"
    program.write_text(f"#!/bin/sh\nprintf executed >> {shlex.quote(str(marker))}\nprintf '\\0'\n")
    program.chmod(0o700)
    hooks = root / "hooks"
    hooks.mkdir()
    for name in ["post-index-change", "reference-transaction", "post-checkout"]:
        hook = hooks / name
        hook.write_bytes(program.read_bytes())
        hook.chmod(0o700)
    _git(repo, "config", "extensions.worktreeConfig", "true")
    for key, value in {
        "core.fsmonitor": str(program),
        "core.hooksPath": str(hooks),
        "core.pager": str(program),
        "diff.external": str(program),
    }.items():
        _git(tree, "config", "--worktree", key, value)
    return marker


def drive(caller, fixture, monkeypatch, capsys):
    repo, tree, tasks, record = fixture
    if caller == "task-family":
        # Executor uses this adapter as its sole worktree-removal stage.
        assert git_safety.is_worktree_dirty(tree) is False
        git_safety.remove_unclaimed_worktree(repo, tree)
        return "removed"
    if caller == "sibling":
        public = repo.parent / "public"
        public.mkdir(exist_ok=True)
        if not (public / ".git").exists():
            _git(public, "init", "-b", "main")
        public_tasks = public / "batch_state/tasks"
        public_tasks.mkdir(parents=True, exist_ok=True)
        (public_tasks / "boundary.json").write_text(json.dumps(record))
        lock_dir = public / ".git" / worktree_claims.LOCK_DIR_NAME
        with worktree_claims.worktree_lock(tree, lock_dir=lock_dir):
            pass
        monkeypatch.setattr(
            sibling_git,
            "load_fleet_repos",
            lambda: {
                "fixture": FleetRepo("fixture", "fixture/sibling", repo.name, "private"),
            },
        )
        monkeypatch.setattr(sibling_git, "_registry_transport", lambda _key: "ssh")
        _git(repo, "config", "remote.origin.url", "git@github.com:fixture/sibling.git")
        _git(repo, "update-ref", "refs/remotes/origin/main", _git(repo, "rev-parse", "HEAD"))
        with sibling_git.git_session() as git:
            resolved = sibling_git.resolve_repository("fixture", public, git)
            result = sibling_git.worktree_remove(resolved, public, git, str(tree))
        assert result["removed"] is True
        return "removed"
    if caller == "stale-record":
        head = _git(repo, "rev-parse", "HEAD")
        candidate = stale_task_records.Candidate(
            path=tasks / "boundary.json",
            mtime_ns=0,
            age_days=1,
            record={**record, "repository": "fixture", "worktree_branch": "codex/boundary"},
        )
        facts = stale_task_records.RepoFacts(
            slug="fixture",
            checkout=repo,
            remote_heads={"codex/boundary": head},
            local_branches={"codex/boundary": head},
        )
        stale_task_records._classify_one(candidate, facts)
        assert candidate.evidence["worktree_dirty"] is False
        return candidate.klass
    if caller == "delegate":
        assert delegate._worktree_is_dirty(tree) is False
    result = boundary_remove(caller, fixture, monkeypatch)
    assert result["action"] == "removed", result
    return result["action"]


@pytest.mark.parametrize("caller", CALLERS)
def test_caller_never_executes_worker_config(boundary_tree, tmp_path, monkeypatch, capsys, caller):
    repo, tree, tasks, record = boundary_tree
    # First run the same production path with ordinary config. Recreate a
    # linked worktree at the same base for the configured case below.
    head = _git(tree, "rev-parse", "HEAD")
    expected = drive(caller, boundary_tree, monkeypatch, capsys)
    if tree.exists():
        _git(repo, "worktree", "remove", str(tree))
    _git(repo, "worktree", "add", "-B", "codex/boundary", str(tree), head)
    if caller == "closeout":
        _git(tree, "push", "-u", "origin", "codex/boundary")
    assert _git(tree, "rev-parse", "HEAD") == head
    (tasks / "boundary.json").write_text(json.dumps(record))
    marker = install_markers(repo, tree, tmp_path)
    try:
        actual = drive(caller, boundary_tree, monkeypatch, capsys)
    finally:
        assert not marker.exists(), f"{caller}: worker Git configuration executed a marker"
    assert actual == expected
    if caller != "stale-record":
        assert not tree.exists()


@pytest.mark.parametrize(
    "command", [["status", "--porcelain"], ["diff", "HEAD"], ["ls-files", "-z"], ["rev-list", "--all"]]
)
def test_shared_invocation_blocks_named_drivers_and_inherited_config(boundary_tree, tmp_path, monkeypatch, command):
    from scripts.fleet import ignored_task_output
    from scripts.orchestration import execution_safe_git as safe

    repo, tree, _tasks, _record = boundary_tree
    (tree / "probe.txt").write_text("base\n")
    (tree / ".gitattributes").write_text("probe.txt filter=trip.wire diff=trip.wire\n")
    _git(tree, "add", "probe.txt", ".gitattributes")
    _git(tree, "commit", "-m", "driver fixture")
    marker = install_markers(repo, tree, tmp_path)
    program = str(tmp_path / "tripwire")
    # Included config and dotted driver names exercise actual Git parsing,
    # rather than a test's reconstruction of the effective configuration.
    included = tmp_path / "included.config"
    included.write_text(
        f'[filter "trip.wire"]\nclean = {program}\nsmudge = {program}\nprocess = {program}\nrequired = true\n'
        f'[diff "trip.wire"]\ncommand = {program}\ntextconv = {program}\n'
        f"[pager]\nstatus = {program}\n[core]\nalternateRefsCommand = {program}\nsshCommand = {program}\n"
        f'[protocol "ext"]\nallow = always\n'
    )
    _git(tree, "config", "--worktree", "include.path", str(included))
    global_config = tmp_path / "global.config"
    global_config.write_bytes(included.read_bytes())
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(global_config))
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", str(global_config))
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "core.fsmonitor")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", program)
    monkeypatch.setenv("GIT_PAGER", program)
    (tree / "probe.txt").write_text("modified\n")
    result = safe.run_git(command, cwd=tree, text=True, capture_output=True, check=True)
    assert result.returncode == 0
    if command[0] in {"status", "diff"}:
        assert "probe.txt" in result.stdout
    assert "probe.txt" in ignored_task_output.artifacts._git_paths(tree, "--cached")
    assert not marker.exists()
    assert safe.safe_git_env()["GIT_CONFIG_GLOBAL"] == "/dev/null"
    assert safe.safe_git_env()["GIT_CONFIG_SYSTEM"] == "/dev/null"
    assert safe.safe_git_env()["GIT_CONFIG_NOSYSTEM"] == "1"


def test_runner_injection_cannot_replace_execution_controls(boundary_tree, tmp_path):
    from scripts.orchestration import execution_safe_git as safe

    repo, tree, _tasks, _record = boundary_tree
    marker = install_markers(repo, tree, tmp_path)
    result = safe.run_git(
        ["status", "--porcelain"],
        cwd=tree,
        runner=safe.SafeGitRunner("/usr/bin/git"),
        text=True,
        capture_output=True,
        check=True,
    )
    assert result.stdout == ""

    def unsafe_runner(*_args, **_kwargs):
        pytest.fail("arbitrary callback was accepted")

    with pytest.raises(TypeError, match="executable constraint"):
        safe.run_git(["status", "--porcelain"], cwd=tree, runner=unsafe_runner)
    with pytest.raises(ValueError, match="absolute"):
        safe.run_git(["status", "--porcelain"], cwd=tree, runner=safe.SafeGitRunner("git"))
    with pytest.raises(ValueError, match="local cleanup"):
        safe.run_git(["fetch", "origin"], cwd=tree)
    for command in (
        ["config", "--edit"], ["config", "--ed"], ["config", "-le"], ["config", "edit"],
        ["branch", "--edit-description"], ["branch", "--e"],
    ):
        with pytest.raises(ValueError, match="editor"):
            safe.run_git(command, cwd=tree)
    assert not marker.exists()


def test_default_removal_preserves_unborn_branch_report(boundary_tree):
    repo, tree, tasks, _record = boundary_tree
    orphan = tree.parent / "orphan"
    _git(repo, "worktree", "add", "--orphan", "-b", "orphan", str(orphan))
    assert worktree_claims.checked_out_branch(orphan) is None
    result = worktree_claims.remove_unclaimed_worktree(
        orphan, repo_root=repo, reason="unborn fixture", owner_task_id=None,
        control_root=repo, tasks_dir=tasks,
        lock_dir=worktree_claims.repository_lock_dir(repo),
    )
    assert result.action == "removed"
    assert result.branch is None
    assert not orphan.exists()


def test_raw_removal_disables_target_local_filter(boundary_tree, tmp_path):
    from scripts.orchestration import execution_safe_git as safe

    repo, tree, _tasks, _record = boundary_tree
    (tree / "probe.txt").write_text("base\n")
    (tree / ".gitattributes").write_text("probe.txt filter=target\n")
    _git(tree, "add", "probe.txt", ".gitattributes")
    _git(tree, "commit", "-m", "target-local filter fixture")
    marker = install_markers(repo, tree, tmp_path)
    clean = tmp_path / "clean"
    clean.write_text(f"#!/bin/sh\nprintf clean >> {shlex.quote(str(marker))}\ncat\n")
    clean.chmod(0o700)
    _git(tree, "config", "--worktree", "filter.target.clean", str(clean))
    (tree / "probe.txt").touch()
    # Raw removal starts in repo, while its status subprocess reads tree's
    # config.worktree. No dirty probe primes that index before this invocation.
    with worktree_claims.worktree_lock(tree, lock_dir=worktree_claims.repository_lock_dir(repo)):
        error = worktree_claims.git_worktree_remove(
            repo, tree, force=False, git_runner=safe.SafeGitRunner("/usr/bin/git")
        )
    assert not marker.exists()
    assert error is None and not tree.exists()


def test_status_disables_initialized_submodule_filter(boundary_tree, tmp_path):
    from scripts.orchestration import execution_safe_git as safe
    from tests.orchestration.test_worktree_claims_cli import _primary

    repo, tree, _tasks, _record = boundary_tree
    source_root = tmp_path / "child-source"
    source_root.mkdir()
    child_source = _primary(source_root)
    (child_source / "probe.txt").write_text("base\n")
    (child_source / ".gitattributes").write_text("probe.txt filter=child\n")
    _git(child_source, "add", ".")
    _git(child_source, "commit", "-m", "child filter fixture")
    _git(tree, "-c", "protocol.file.allow=always", "submodule", "add", str(child_source), "child")
    _git(tree, "commit", "-am", "gitlink fixture")
    assert _git(tree, "status", "--porcelain") == ""
    marker = install_markers(repo, tree, tmp_path)
    clean = tmp_path / "clean"
    clean.write_text(f"#!/bin/sh\nprintf child >> {shlex.quote(str(marker))}\ncat\n")
    clean.chmod(0o700)
    child = tree / "child"
    _git(child, "config", "filter.child.clean", str(clean))
    (child / "probe.txt").touch()
    result = safe.run_git(
        ["status", "--porcelain", "--ignore-submodules=none"], cwd=tree, text=True, capture_output=True, check=True
    )
    assert not marker.exists()
    assert result.stdout == ""


def test_status_disables_redirected_submodule_filter(boundary_tree, tmp_path):
    from scripts.orchestration import execution_safe_git as safe
    from tests.orchestration.test_worktree_claims_cli import _primary

    repo, tree, _tasks, _record = boundary_tree
    source_root = tmp_path / "child-source"
    source_root.mkdir()
    source = _primary(source_root)
    (source / "probe.txt").write_text("base\n")
    (source / ".gitattributes").write_text("probe.txt filter=redirected\n")
    _git(source, "add", ".")
    _git(source, "commit", "-m", "redirected filter fixture")
    child_head = _git(source, "rev-parse", "HEAD")
    _git(tree, "update-index", "--add", "--cacheinfo", f"160000,{child_head},child")
    _git(tree, "commit", "-m", "uninitialized gitlink fixture")
    redirected = tmp_path / "redirected"
    shutil.copytree(tree, redirected, ignore=shutil.ignore_patterns(".git"))
    _git(repo, "clone", str(source), str(redirected / "child"))
    _git(repo, "config", "extensions.worktreeConfig", "true")
    _git(tree, "config", "--worktree", "core.worktree", str(redirected))
    marker = tmp_path / "executed"
    clean = tmp_path / "clean"
    clean.write_text(f"#!/bin/sh\nprintf redirected >> {shlex.quote(str(marker))}\ncat\n")
    clean.chmod(0o700)
    _git(redirected / "child", "config", "filter.redirected.clean", str(clean))
    (redirected / "child" / "probe.txt").touch()
    result = safe.run_git(
        ["status", "--porcelain", "--ignore-submodules=none"], cwd=tree,
        text=True, capture_output=True, check=True,
    )
    assert not marker.exists()
    assert result.stdout == ""
