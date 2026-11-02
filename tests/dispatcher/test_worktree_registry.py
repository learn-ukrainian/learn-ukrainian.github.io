"""A repository that declares a worktree registry gets every dispatched worktree registered and archived (#12540)."""

import json
from pathlib import Path

import yaml

from tests.dispatcher.test_core import run_git, sandbox  # noqa: F401  (the real-dispatcher fixture)

REGISTRY = ".agent/workspace-hygiene.json"


def declared_repo(sandbox):  # noqa: F811
    """A sibling checkout whose fleet entry declares a registry that already holds other records."""
    config = sandbox.repo / "scripts/config/fleet_repos.yaml"
    catalog = yaml.safe_load(config.read_text())
    catalog["repos"]["declared"] = dict(local_name="declared", github="example/declared", role="public-content",
                                        worktree_registry=REGISTRY)
    config.write_text(yaml.safe_dump(catalog))
    run_git(sandbox.repo, "commit", "-am", "declare a registry")
    primary = sandbox.repo.parent / "declared"
    primary.mkdir()
    run_git(primary, "init", "-b", "main")
    run_git(primary, "config", "user.name", "Stub")
    run_git(primary, "config", "user.email", "stub@example.invalid")
    run_git(primary, "commit", "--allow-empty", "-m", "fixture")
    registry = primary / REGISTRY
    registry.parent.mkdir()
    other = dict(owner="claude-cto", purpose="hand written", branch="b", head="0" * 40, state="active",
                 next_action="x", pr=None, extra="kept")
    registry.write_text(json.dumps(dict(worktrees={"/elsewhere": other}, artifacts={"/scratch/a": {"keep": 1}}, note="kept")))
    return primary, registry, other


def test_dispatched_worktree_is_registered_before_creation_and_archived_at_removal(sandbox):  # noqa: F811
    primary, registry, other = declared_repo(sandbox)
    # A non-empty directory at the path makes creation fail after registration, which must not leave a phantom.
    (primary / ".worktrees/dispatch/codex/doomed").mkdir(parents=True)
    (primary / ".worktrees/dispatch/codex/doomed/occupant").write_text("x")
    sandbox.cli("dispatch", "--agent", "sol", "--model", "echo", "--prompt", "never created", "--repo", "declared",
                "--base", "main", "--task-id", "doomed", "--initiator", "claude-cto", expected=2)
    data = json.loads(registry.read_text())
    doomed = data["worktrees"][str(primary / ".worktrees/dispatch/codex/doomed")]
    assert (doomed["state"], doomed["pr"]) == ("archived", None)
    assert "not created" in doomed["next_action"]
    assert "doomed" in doomed["owner"]
    assert "claude-cto" in doomed["owner"]

    task = sandbox.dispatch("echo", "--repo", "declared", "--base", "main", "--initiator", "claude-cto",
                            "--task-id", "registered")
    record = sandbox.settle(task)
    tree = str(primary / ".worktrees/dispatch/codex/registered")
    assert record["worktree_path"] == tree
    assert (record["worktree_disposition"], record["worktree_registry"]) == ("removed", "archived")
    data = json.loads(registry.read_text())
    entry = data["worktrees"][tree]
    assert entry["owner"] == "codex dispatch task registered; initiator claude-cto"
    assert entry["purpose"] == "literal final response"
    assert (entry["branch"], entry["pr"], entry["state"]) == ("codex/registered", None, "archived")
    assert entry["head"] == run_git(primary, "rev-parse", "main")
    assert "removed the worktree" in entry["next_action"]
    # Other records and unknown keys survive untouched; nothing is ever removed.
    assert data["worktrees"]["/elsewhere"] == other
    assert data["artifacts"] == {"/scratch/a": {"keep": 1}} and data["note"] == "kept"
    assert not Path(tree).exists()


def test_register_confirms_branch_and_head_and_a_malformed_registry_is_refused(sandbox):  # noqa: F811
    from scripts.dispatcher import git

    primary, registry, _ = declared_repo(sandbox)
    tree = primary / ".worktrees/dispatch/codex/direct"
    sha = run_git(primary, "rev-parse", "HEAD")
    git.register_worktree(registry, tree, agent="codex", task_id="direct", initiator=None, purpose="p\nq",
                          branch="codex/direct", sha=sha)
    entry = json.loads(registry.read_text())["worktrees"][str(tree.resolve())]
    assert (entry["state"], entry["pr"], entry["purpose"], entry["head"]) == ("active", None, "p q", sha)
    git.create_worktree(primary, tree, "codex/direct", sha)
    git.confirm_worktree(registry, tree)
    assert git.archive_worktree(registry, tree, "done") is True
    assert git.archive_worktree(registry, tree / "absent", "done") is False
    registry.write_text("[]")
    try:
        git.register_worktree(registry, tree / "next", agent="codex", task_id="n", initiator=None, purpose="p",
                              branch="b", sha=sha)
    except ValueError as exc:
        assert "invalid shape" in str(exc)
    else:
        raise AssertionError("a malformed registry must be refused")


def test_a_creation_that_fails_after_git_made_the_tree_leaves_the_record_active(sandbox, monkeypatch):  # noqa: F811
    from scripts.dispatcher import git

    primary, registry, _ = declared_repo(sandbox)
    sha = run_git(primary, "rev-parse", "HEAD")
    tree = primary / ".worktrees/dispatch/codex/survivor"
    registration = dict(registry=registry, agent="codex", task_id="survivor", initiator=None, purpose="p")
    real_git = git._git

    def reset_fails(where, *args, **kwargs):
        if args[:2] == ("reset", "--hard"):
            raise OSError("disk full")
        return real_git(where, *args, **kwargs)

    monkeypatch.setattr(git, "_git", reset_fails)
    try:
        git.create_worktree(primary, tree, "codex/survivor", sha, registration=registration)
    except OSError:
        pass
    else:
        raise AssertionError("the failure must propagate")
    assert tree.is_dir()
    entry = json.loads(registry.read_text())["worktrees"][str(tree.resolve())]
    assert (entry["state"], entry["branch"], entry["head"]) == ("active", "codex/survivor", sha)


def test_noncanonical_spelling_and_live_path(sandbox):  # noqa: F811
    from scripts.dispatcher import git

    primary, registry, _ = declared_repo(sandbox)
    sha = run_git(primary, "rev-parse", "HEAD")
    spelled = primary / ".worktrees/dispatch/codex/mid/../canon"
    registration = dict(registry=registry, agent="codex", task_id="canon", initiator=None, purpose="p")
    (primary / ".worktrees/dispatch/codex/mid").mkdir(parents=True)
    git.create_worktree(primary, spelled, "codex/canon", sha, registration=registration)
    canonical = str((primary / ".worktrees/dispatch/codex/canon").resolve())
    worktrees = json.loads(registry.read_text())["worktrees"]
    assert worktrees[canonical]["state"] == "active" and worktrees[canonical]["head"] == sha
    # A second dispatch to the live path is refused and leaves the first owner's record untouched.
    before = worktrees[canonical]
    try:
        git.create_worktree(primary, spelled, "codex/other", sha, registration={**registration, "task_id": "other"})
    except ValueError as exc:
        assert "already holds a worktree" in str(exc)
    else:
        raise AssertionError("a live path must not be re-registered")
    assert json.loads(registry.read_text())["worktrees"][canonical] == before


def test_a_commit_refreshes_the_record_and_a_retained_tree_keeps_its_final_head(sandbox, monkeypatch):  # noqa: F811
    from scripts.dispatcher import git, store

    monkeypatch.setattr(store, "retention_hold_disposition", lambda _record: None)  # no on-disk task record here

    primary, registry, other = declared_repo(sandbox)
    sha = run_git(primary, "rev-parse", "HEAD")
    tree = primary / ".worktrees/dispatch/codex/live"
    registration = dict(registry=registry, agent="codex", task_id="live", initiator=None, purpose="p")
    # The repository's own hook keeps running beside the refresh hooks.
    own = primary / ".git/hooks/post-commit"
    own.write_text(f"#!/bin/sh\ntouch {primary}/own-hook-ran\n")
    own.chmod(0o755)
    monkeypatch.setattr(git, "resolve_repo", lambda _key=None: (primary, dict(worktree_registry=REGISTRY)))
    git.create_worktree(primary, tree, "codex/live", sha, registration=registration)

    def entry():
        return json.loads(registry.read_text())["worktrees"][str(tree.resolve())]
    assert entry()["head"] == sha
    # Plain git commits, so the hooks really fire; the second is an amend (post-rewrite).
    run_git(tree, "-c", "user.name=S", "-c", "user.email=s@example.invalid", "commit", "--allow-empty", "-m", "one")
    first = run_git(tree, "rev-parse", "HEAD")
    assert entry()["head"] == first != sha
    run_git(tree, "-c", "user.name=S", "-c", "user.email=s@example.invalid", "commit", "--amend", "--allow-empty",
            "-m", "one again")
    second = run_git(tree, "rev-parse", "HEAD")
    assert entry()["head"] == second != first and entry()["branch"] == "codex/live"
    assert (primary / "own-hook-ran").exists()

    # Settlement of a tree it keeps records that final head; the other records stay as they were.
    (tree / "README").write_text("uncommitted\n")
    run_git(tree, "add", "README")
    record = dict(task_id="live", repo="declared", worktree_path=str(tree), worktree_branch="codex/live",
                  worktree_base_sha=sha, mode="workspace-write", options={})
    registry_before = json.loads(registry.read_text())
    stale = {**registry_before["worktrees"][str(tree.resolve())], "head": sha}
    registry.write_text(json.dumps({**registry_before, "worktrees": {**registry_before["worktrees"],
                                                                        str(tree.resolve()): stale}}))
    outcome = git.settle_worktree(record)
    assert (outcome["worktree_disposition"], outcome["worktree_disposition_reason"]) == ("retained", "dirty")
    assert outcome["worktree_registry"] == "refreshed"
    data = json.loads(registry.read_text())
    assert (data["worktrees"][str(tree.resolve())]["head"], data["worktrees"][str(tree.resolve())]["state"]) == (second, "active")
    assert data["worktrees"]["/elsewhere"] == other and data["artifacts"] == {"/scratch/a": {"keep": 1}}


def test_refresh_keeps_configured_hooks_and_contains_registry_trouble(sandbox, monkeypatch):  # noqa: F811
    import fcntl

    from scripts.dispatcher import git, store

    primary, registry, _ = declared_repo(sandbox)
    monkeypatch.setattr(store, "retention_hold_disposition", lambda _record: None)
    monkeypatch.setattr(git, "resolve_repo", lambda _key=None: (primary, dict(worktree_registry=REGISTRY)))
    sha = run_git(primary, "rev-parse", "HEAD")
    # A relative core.hooksPath is resolved against the worktree, so its guards survive; a failing post hook
    # of the repository's own does not stop the refresh.
    (primary / ".githooks").mkdir()
    guard = primary / ".githooks/pre-commit"
    guard.write_text("#!/bin/sh\nexit 1\n")
    failing = primary / ".githooks/post-commit"
    failing.write_text("#!/bin/sh\nexit 1\n")
    for hook in (guard, failing):
        hook.chmod(0o755)
    run_git(primary, "config", "core.hooksPath", ".githooks")
    run_git(primary, "add", ".githooks")
    run_git(primary, "-c", "core.hooksPath=/dev/null", "commit", "-m", "tracked hooks")
    sha = run_git(primary, "rev-parse", "HEAD")
    tree = primary / ".worktrees/dispatch/codex/guarded"
    git.create_worktree(primary, tree, "codex/guarded", sha,
                        registration=dict(registry=registry, agent="codex", task_id="guarded", initiator=None, purpose="p"))
    refused = git.subprocess.run(["git", "-C", str(tree), "-c", "user.name=S", "-c", "user.email=s@example.invalid",
                                  "commit", "--allow-empty", "-m", "x"], capture_output=True)
    assert refused.returncode != 0, "the repository's pre-commit guard must still run"
    key = str(tree.resolve())
    # A malformed entry and a held lock are contained at settlement; the disposition is unchanged.
    data = json.loads(registry.read_text())
    data["worktrees"][key] = "garbage"
    registry.write_text(json.dumps(data))
    (tree / "README").write_text("dirty\n")
    run_git(tree, "add", "README")
    record = dict(task_id="guarded", repo="declared", worktree_path=str(tree), worktree_branch="codex/guarded",
                  worktree_base_sha=sha, mode="workspace-write", options={})
    assert git.settle_worktree(record)["worktree_disposition_reason"] == "dirty"
    monkeypatch.setattr(git, "REFRESH_LOCK_WAIT", 0.2)
    data["worktrees"][key] = dict(owner="o", purpose="p", branch="codex/guarded", head=sha, state="active",
                                  next_action="n", pr=None)
    registry.write_text(json.dumps(data))
    with open(registry.with_name(registry.name + ".lock"), "ab") as held:
        fcntl.flock(held, fcntl.LOCK_EX)
        outcome = git.settle_worktree(record)
    assert outcome["worktree_disposition_reason"] == "dirty" and outcome["worktree_registry"].startswith("failed: TimeoutError")


def test_a_home_relative_hooks_path_keeps_its_guards(sandbox, monkeypatch, tmp_path):  # noqa: F811
    from scripts.dispatcher import git

    primary, registry, _ = declared_repo(sandbox)
    home = tmp_path / "home"
    (home / "hooks").mkdir(parents=True)
    guard = home / "hooks/pre-commit"
    guard.write_text("#!/bin/sh\nexit 1\n")
    guard.chmod(0o755)
    monkeypatch.setenv("HOME", str(home))
    run_git(primary, "config", "core.hooksPath", "~/hooks")
    sha = run_git(primary, "rev-parse", "HEAD")
    tree = primary / ".worktrees/dispatch/codex/tilde"
    git.create_worktree(primary, tree, "codex/tilde", sha,
                        registration=dict(registry=registry, agent="codex", task_id="tilde", initiator=None, purpose="p"))
    refused = git.subprocess.run(["git", "-C", str(tree), "-c", "user.name=S", "-c", "user.email=s@example.invalid",
                                  "commit", "--allow-empty", "-m", "x"], capture_output=True)
    assert refused.returncode != 0, "the guard behind ~/hooks must still run"
