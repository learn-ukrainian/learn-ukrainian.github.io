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


def test_register_confirms_branch_and_head_and_a_malformed_registry_is_refused(sandbox, tmp_path):  # noqa: F811
    from scripts.dispatcher import git

    primary, registry, _ = declared_repo(sandbox)
    tree = primary / ".worktrees/dispatch/codex/direct"
    sha = run_git(primary, "rev-parse", "HEAD")
    git.register_worktree(registry, tree, agent="sol", task_id="direct", initiator=None, purpose="p\nq", branch="sol/direct",
                          sha=sha)
    entry = json.loads(registry.read_text())["worktrees"][str(tree)]
    assert (entry["state"], entry["pr"], entry["purpose"], entry["head"]) == ("active", None, "p q", sha)
    git.create_worktree(primary, tree, "sol/direct", sha)
    git.confirm_worktree(registry, tree)
    assert git.archive_worktree(registry, tree, "done") is True
    assert git.archive_worktree(registry, tree / "absent", "done") is False
    registry.write_text("[]")
    try:
        git.register_worktree(registry, tree, agent="sol", task_id="direct", initiator=None, purpose="p", branch="b", sha=sha)
    except ValueError as exc:
        assert "invalid shape" in str(exc)
    else:
        raise AssertionError("a malformed registry must be refused")
