"""Tests for the centralized worktree containment predicate (issue #4444).

These build *real* git repositories and worktrees in ``tmp_path`` rather than
faking ``.git`` files, because the module deliberately relies on git plumbing
(``rev-parse --git-common-dir``, ``ls-files``, ``check-ignore``,
``worktree list``) rather than string prefixes.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

from scripts.guardrails import worktree_containment as wc


def _clean_env() -> dict[str, str]:
    """Env with git-redirect vars stripped.

    Under ``pre-commit`` / a git hook the process inherits ``GIT_DIR``,
    ``GIT_WORK_TREE``, ``GIT_INDEX_FILE``, etc. pointing at the repo being
    committed. Those would hijack the throwaway repos this test builds (``-C``
    alone does not override them), so we scrub them for every git subprocess —
    the same denylist the module applies internally.
    """
    return {k: v for k, v in os.environ.items() if k not in wc._GIT_ENV_DENYLIST}


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True, capture_output=True, text=True, env=_clean_env(),
    )


@dataclass(frozen=True)
class Layout:
    main: Path              # primary checkout root
    dispatch_wt: Path       # .worktrees/dispatch/claude/task-1 (registered)
    flat_wt: Path           # .worktrees/legacy (registered, non-dispatch)
    external_wt: Path       # <tmp>/external-wt (registered, outside .worktrees)
    outside: Path           # <tmp>/outside (plain dir, not a repo)


@pytest.fixture
def layout(tmp_path: Path) -> Layout:
    main = tmp_path / "main"
    main.mkdir()
    subprocess.run(
        ["git", "init", "-q", "-b", "main", str(main)],
        check=True, capture_output=True, text=True, env=_clean_env(),
    )
    _git(main, "config", "user.email", "test@example.com")
    _git(main, "config", "user.name", "Test")

    # Tracked content + gitignore rules covering runtime/local state.
    (main / ".gitignore").write_text(".worktrees/\nbuild/\n*.log\nlocal_state/\n")
    (main / "tracked.txt").write_text("tracked\n")
    (main / "pkg").mkdir()
    (main / "pkg" / "module.py").write_text("x = 1\n")
    _git(main, "add", "-A")
    _git(main, "commit", "-q", "-m", "init")

    # Real registered worktrees: a dispatch one, a flat non-dispatch one under
    # .worktrees, and an externally-located one sharing the same .git store.
    dispatch_wt = main / ".worktrees" / "dispatch" / "claude" / "task-1"
    _git(main, "worktree", "add", "-q", "-b", "claude/task-1", str(dispatch_wt))
    flat_wt = main / ".worktrees" / "legacy"
    _git(main, "worktree", "add", "-q", "-b", "legacy", str(flat_wt))
    external_wt = tmp_path / "external-wt"
    _git(main, "worktree", "add", "-q", "-b", "ext", str(external_wt))

    outside = tmp_path / "outside"
    outside.mkdir()

    return Layout(
        main=wc.canonicalize(main),
        dispatch_wt=wc.canonicalize(dispatch_wt),
        flat_wt=wc.canonicalize(flat_wt),
        external_wt=wc.canonicalize(external_wt),
        outside=wc.canonicalize(outside),
    )


# ---------------------------------------------------------------------------
# resolve_main_root — same primary root from anywhere
# ---------------------------------------------------------------------------

def test_resolve_main_root_is_stable_from_every_vantage(layout: Layout):
    assert wc.resolve_main_root(layout.main) == layout.main
    assert wc.resolve_main_root(layout.main / "pkg") == layout.main
    # From an added worktree we still resolve the SAME primary root (AC).
    assert wc.resolve_main_root(layout.dispatch_wt) == layout.main
    assert wc.resolve_main_root(layout.dispatch_wt / "pkg") == layout.main
    assert wc.resolve_main_root(layout.external_wt) == layout.main


def test_resolve_main_root_raises_outside_repo(layout: Layout):
    with pytest.raises(wc.NotAGitRepositoryError):
        wc.resolve_main_root(layout.outside)


# ---------------------------------------------------------------------------
# classify_repo_path
# ---------------------------------------------------------------------------

def test_tracked_file_in_primary_checkout_is_protected(layout: Layout):
    tracked = layout.main / "tracked.txt"
    assert wc.classify_repo_path(tracked, cwd=layout.main) == "primary_checkout"
    assert wc.is_tracked(tracked, layout.main) is True
    allowed, reason = wc.is_write_allowed(tracked, cwd=layout.main)
    assert allowed is False
    assert reason == "tracked_primary_checkout"
    decision = wc.evaluate_write(tracked, cwd=layout.main)
    assert decision.message  # actionable guidance is populated on denial
    assert ".worktrees/dispatch" in decision.message


def test_gitignored_local_state_is_allowed(layout: Layout):
    ignored = layout.main / "build" / "out.txt"
    assert wc.classify_repo_path(ignored, cwd=layout.main) == "primary_checkout"
    assert wc.is_ignored(ignored, layout.main) is True
    assert wc.is_tracked(ignored, layout.main) is False
    allowed, reason = wc.is_write_allowed(ignored, cwd=layout.main)
    assert allowed is True
    assert reason == "gitignored_local_state"


def test_untracked_non_ignored_in_primary_checkout_is_blocked(layout: Layout):
    scratch = layout.main / "scratch_new.txt"
    assert wc.classify_repo_path(scratch, cwd=layout.main) == "primary_checkout"
    assert wc.is_tracked(scratch, layout.main) is False
    assert wc.is_ignored(scratch, layout.main) is False
    allowed, reason = wc.is_write_allowed(scratch, cwd=layout.main)
    assert allowed is False
    assert reason == "untracked_primary_checkout"


def test_dispatch_worktree_path_is_allowed(layout: Layout):
    target = layout.dispatch_wt / "pkg" / "module.py"
    assert wc.classify_repo_path(target, cwd=layout.main) == "dispatch_worktree"
    assert wc.is_dispatch_worktree(target) is True
    allowed, reason = wc.is_write_allowed(target, cwd=layout.main)
    assert allowed is True
    assert reason == "dispatch_worktree"


def test_dispatch_path_allowed_even_before_worktree_exists(layout: Layout):
    # An agent is about to create .worktrees/dispatch/agy/future/ — structural
    # classification must already treat it as an allowed dispatch location.
    future = layout.main / ".worktrees" / "dispatch" / "agy" / "future" / "new.py"
    assert wc.classify_repo_path(future, cwd=layout.main) == "dispatch_worktree"
    assert wc.is_write_allowed(future, cwd=layout.main)[0] is True


def test_non_dispatch_worktree_paths_are_other_worktree(layout: Layout):
    flat = layout.flat_wt / "tracked.txt"
    ext = layout.external_wt / "tracked.txt"
    assert wc.classify_repo_path(flat, cwd=layout.main) == "other_worktree"
    assert wc.classify_repo_path(ext, cwd=layout.main) == "other_worktree"
    assert wc.is_write_allowed(flat, cwd=layout.main) == (True, "other_worktree")
    assert wc.is_write_allowed(ext, cwd=layout.main) == (True, "other_worktree")


def test_outside_repo_path(layout: Layout):
    target = layout.outside / "note.txt"
    assert wc.classify_repo_path(target, cwd=layout.main) == "outside_repo"
    assert wc.is_write_allowed(target, cwd=layout.main) == (True, "outside_repo")


# ---------------------------------------------------------------------------
# canonicalization: symlink + ".." escapes
# ---------------------------------------------------------------------------

def test_symlink_escape_is_classified_by_real_target(layout: Layout, tmp_path: Path):
    outside_target = tmp_path / "escape_target"
    outside_target.mkdir()
    link = layout.main / "escape"
    link.symlink_to(outside_target)
    # Path is lexically "inside" main, but the symlink lands outside the repo.
    escaped = link / "secret.txt"
    assert wc.classify_repo_path(escaped, cwd=layout.main) == "outside_repo"


def test_symlink_staying_inside_is_primary_checkout(layout: Layout):
    link = layout.main / "inward"
    link.symlink_to(layout.main / "pkg")
    target = link / "module.py"
    assert wc.classify_repo_path(target, cwd=layout.main) == "primary_checkout"
    # And it resolves to the tracked file, so writes are blocked.
    assert wc.is_write_allowed(target, cwd=layout.main)[0] is False


def test_dotdot_escape_is_classified_outside(layout: Layout):
    escaped = layout.main / "pkg" / ".." / ".." / "outside" / "x.txt"
    assert wc.classify_repo_path(escaped, cwd=layout.main) == "outside_repo"


def test_dotdot_staying_inside_resolves_to_primary_checkout(layout: Layout):
    inside = layout.main / "pkg" / ".." / "tracked.txt"
    assert wc.classify_repo_path(inside, cwd=layout.main) == "primary_checkout"
    assert wc.is_write_allowed(inside, cwd=layout.main)[1] == "tracked_primary_checkout"


# ---------------------------------------------------------------------------
# missing-path parent resolution
# ---------------------------------------------------------------------------

def test_missing_path_under_untracked_dir_is_blocked(layout: Layout):
    # Parent dir does not exist yet; must still classify + decide.
    missing = layout.main / "newpkg" / "deeply" / "new_module.py"
    assert wc.classify_repo_path(missing, cwd=layout.main) == "primary_checkout"
    assert wc.is_write_allowed(missing, cwd=layout.main) == (
        False,
        "untracked_primary_checkout",
    )


def test_missing_path_under_ignored_dir_is_allowed(layout: Layout):
    missing = layout.main / "build" / "sub" / "artifact.log"
    assert wc.is_ignored(missing, layout.main) is True
    assert wc.is_write_allowed(missing, cwd=layout.main) == (
        True,
        "gitignored_local_state",
    )


# ---------------------------------------------------------------------------
# is_primary_checkout / branch helpers
# ---------------------------------------------------------------------------

def test_is_primary_checkout_matrix(layout: Layout):
    assert wc.is_primary_checkout(layout.main) is True
    assert wc.is_primary_checkout(layout.main / "pkg") is True
    assert wc.is_primary_checkout(layout.dispatch_wt) is False
    assert wc.is_primary_checkout(layout.external_wt) is False
    assert wc.is_primary_checkout(layout.outside) is False


def test_branch_helpers(layout: Layout):
    assert wc.current_branch(layout.main) == "main"
    assert wc.is_protected_branch(layout.main) is True
    # Dispatch worktree sits on an agent branch, never protected.
    assert wc.current_branch(layout.dispatch_wt) == "claude/task-1"
    assert wc.is_protected_branch(layout.dispatch_wt) is False


# ---------------------------------------------------------------------------
# read-only invocation must not mutate anything
# ---------------------------------------------------------------------------

def test_read_only_operations_do_not_dirty_the_checkout(layout: Layout):
    before = _git(layout.main, "status", "--porcelain").stdout
    # Exercise the full surface from the repo root.
    wc.classify_repo_path(layout.main / "tracked.txt", cwd=layout.main)
    wc.is_write_allowed(layout.main / "tracked.txt", cwd=layout.main)
    wc.is_primary_checkout(layout.main)
    wc.registered_worktrees(layout.main)
    after = _git(layout.main, "status", "--porcelain").stdout
    assert before == after


def test_module_is_robust_to_hostile_git_env(layout: Layout, monkeypatch):
    # Consumers (#4448 hooks, #4450 git shim) run inside git hooks where GIT_DIR
    # etc. point elsewhere. The module must scrub them, so resolution/decisions
    # stay correct regardless of the ambient (redirecting) git environment.
    monkeypatch.setenv("GIT_DIR", str(layout.external_wt / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(layout.external_wt))
    assert wc.resolve_main_root(layout.main / "pkg") == layout.main
    assert wc.classify_repo_path(layout.main / "tracked.txt", cwd=layout.main) == "primary_checkout"
    assert wc.is_write_allowed(layout.main / "tracked.txt", cwd=layout.main) == (
        False,
        "tracked_primary_checkout",
    )


def test_relative_gitignored_path_resolved_against_cwd(layout: Layout):
    """#5404: relative write under a gitignored subdir cwd must be allowed."""
    ignored_dir = layout.main / "local_state" / "nested"
    ignored_dir.mkdir(parents=True, exist_ok=True)
    # ensure local_state is gitignored in fixture (test_gitignored_local_state uses local_state/)
    rel = "nested/out.log"
    decision = wc.evaluate_write(rel, cwd=ignored_dir)
    assert decision.allowed is True, decision
    assert decision.reason == "gitignored_local_state"
