"""Tests for the centralized worktree containment predicate (issue #4444).

These build *real* git repositories and worktrees in ``tmp_path`` rather than
faking ``.git`` files, because the module deliberately relies on git plumbing
(``rev-parse --git-common-dir``, ``ls-files``, ``check-ignore``,
``worktree list``) rather than string prefixes.
"""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest

from scripts.common.scratch import ensure_scratch_root
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
        check=True,
        capture_output=True,
        text=True,
        env=_clean_env(),
        timeout=30,
    )


@dataclass(frozen=True)
class Layout:
    main: Path  # primary checkout root
    dispatch_wt: Path  # .worktrees/dispatch/claude/task-1 (registered)
    flat_wt: Path  # .worktrees/legacy (registered, non-dispatch)
    external_wt: Path  # <tmp>/external-wt (registered, outside .worktrees)
    outside: Path  # <tmp>/outside (plain dir, not a repo)


@pytest.fixture
def layout(tmp_path: Path) -> Layout:
    main = tmp_path / "main"
    main.mkdir()
    subprocess.run(
        ["git", "init", "-q", "-b", "main", str(main)],
        check=True,
        capture_output=True,
        text=True,
        env=_clean_env(),
        timeout=30,
    )
    _git(main, "config", "user.email", "test@example.com")
    _git(main, "config", "user.name", "Test")

    # Tracked content + gitignore rules covering runtime/local state.
    (main / ".gitignore").write_text(".worktrees/\nbuild/\n*.log\nlocal_state/\n")
    marker = main / "curriculum/l2-uk-en/curriculum.yaml"
    marker.parent.mkdir(parents=True)
    marker.touch()
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


@pytest.fixture
def outside_any_repo() -> Iterator[Path]:
    """A directory outside every git repository, independent of pytest's basetemp.

    The protected-push gate puts basetemp under the primary checkout's ``.git``
    directory, so ``tmp_path`` (and ``layout.outside``) may itself lie inside a
    repository there; this directory is checked to lie outside one.
    """
    directory = wc.canonicalize(
        tempfile.mkdtemp(prefix="wc-outside-", dir=os.environ.get("TMPDIR", ensure_scratch_root()))
    )
    try:
        assert wc._resolve_main_root_or_none(directory) is None, "the scratch directory is inside a git repository"
        yield directory
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def test_resolve_main_root_raises_outside_repo(layout: Layout, outside_any_repo: Path):
    with pytest.raises(wc.NotAGitRepositoryError):
        wc.resolve_main_root(outside_any_repo)


def test_resolve_main_root_uses_filesystem_fallback_when_git_cannot_execute(
    layout: Layout, monkeypatch: pytest.MonkeyPatch
):
    def missing_git(*_args, **_kwargs):
        raise FileNotFoundError("git unavailable")

    monkeypatch.setattr(wc.subprocess, "run", missing_git)

    assert wc.resolve_main_root(layout.main) == layout.main
    assert wc.resolve_main_root(layout.dispatch_wt) == layout.main


def test_git_probe_propagates_non_missing_executable_errors(layout: Layout, monkeypatch: pytest.MonkeyPatch):
    def forbidden_git(*_args, **_kwargs):
        raise PermissionError("git execution forbidden")

    monkeypatch.setattr(wc.subprocess, "run", forbidden_git)

    with pytest.raises(PermissionError, match="forbidden"):
        wc.resolve_main_root(layout.main)


def test_resolve_main_root_without_git_matches_git_and_never_spawns(layout: Layout, monkeypatch: pytest.MonkeyPatch):
    def no_subprocess(*_args, **_kwargs):
        raise AssertionError("resolve_main_root_without_git ran a subprocess")

    monkeypatch.setattr(wc.subprocess, "run", no_subprocess)
    monkeypatch.setenv("GIT_DIR", str(layout.dispatch_wt / ".git"))
    monkeypatch.setenv("PATH", str(layout.outside))
    for checkout in (layout.main, layout.dispatch_wt, layout.flat_wt, layout.external_wt):
        assert wc.resolve_main_root_without_git(checkout) == layout.main


def _worktree_gitdir(worktree: Path) -> Path:
    return Path((worktree / ".git").read_text().removeprefix("gitdir:").strip())


@pytest.mark.parametrize(
    "defect",
    [
        "no_git",
        "symlinked_dot_git",
        "gitdir_outside_worktrees",
        "relative_link_outside_worktrees",
        "multi_line_link",
        "oversized_link",
        "broken_back_link",
        "foreign_commondir",
        "symlinked_common_dir",
        "symlinked_worktrees_dir",
        "empty_dot_git_dir",
        "primary_without_head",
        "primary_with_malformed_head",
        "primary_without_objects",
        "worktree_gitdir_without_head",
        "fabricated_store",
        "nul_byte_link",
    ],
)
def test_resolve_main_root_without_git_refuses_unexpected_links(layout: Layout, defect: str):
    worktree = layout.dispatch_wt
    gitdir = _worktree_gitdir(worktree)
    target = worktree
    if defect == "no_git":
        target = layout.outside
    elif defect == "symlinked_worktrees_dir":
        # An intermediate component of the derived gitdir path, not only its ends.
        moved = layout.main.parent / "moved-worktrees"
        (layout.main / ".git" / "worktrees").rename(moved)
        (layout.main / ".git" / "worktrees").symlink_to(moved, target_is_directory=True)
    elif defect == "empty_dot_git_dir":
        (layout.outside / ".git").mkdir()
        target = layout.outside
    elif defect == "primary_without_head":
        (layout.main / ".git" / "HEAD").unlink()
        target = layout.main
    elif defect == "primary_with_malformed_head":
        (layout.main / ".git" / "HEAD").write_text("not a ref\n")
    elif defect == "primary_without_objects":
        shutil.rmtree(layout.main / ".git" / "objects")
    elif defect == "worktree_gitdir_without_head":
        (gitdir / "HEAD").unlink()
    elif defect == "fabricated_store":
        # Mutually consistent links into a store that is not a repository.
        store = layout.outside / "fake" / ".git" / "worktrees" / "wt"
        store.mkdir(parents=True)
        target = layout.outside / "wt"
        target.mkdir()
        (target / ".git").write_text(f"gitdir: {store}\n")
        (store / "gitdir").write_text(f"{target / '.git'}\n")
        (store / "commondir").write_text("../..\n")
        (store / "HEAD").write_text("ref: refs/heads/main\n")
    elif defect == "nul_byte_link":
        (worktree / ".git").write_text(f"gitdir: {gitdir}\x00x\n")
    elif defect == "symlinked_dot_git":
        (worktree / ".git").unlink()
        (worktree / ".git").symlink_to(layout.main / ".git")
    elif defect == "gitdir_outside_worktrees":
        (worktree / ".git").write_text(f"gitdir: {layout.main / '.git'}\n")
    elif defect == "relative_link_outside_worktrees":
        (worktree / ".git").write_text("gitdir: ../elsewhere\n")
    elif defect == "multi_line_link":
        (worktree / ".git").write_text(f"gitdir: {gitdir}\nextra\n")
    elif defect == "oversized_link":
        (worktree / ".git").write_text("gitdir: " + "x" * 5000 + "\n")
    elif defect == "broken_back_link":
        (gitdir / "gitdir").write_text(f"{layout.flat_wt / '.git'}\n")
    elif defect == "foreign_commondir":
        (gitdir / "commondir").write_text(f"{layout.outside}\n")
    elif defect == "symlinked_common_dir":
        moved = layout.main.parent / "store"
        (layout.main / ".git").rename(moved)
        (layout.main / ".git").symlink_to(moved, target_is_directory=True)
    with pytest.raises(wc.NotAGitRepositoryError):
        wc.resolve_main_root_without_git(target)


@pytest.mark.parametrize("link", [".git", "gitdir", "commondir", "HEAD"])
def test_resolve_main_root_without_git_refuses_a_fifo_link_without_blocking(layout: Layout, link: str):
    worktree = layout.dispatch_wt
    gitdir = _worktree_gitdir(worktree)
    fifo = worktree / ".git" if link == ".git" else gitdir / link
    fifo.unlink()
    os.mkfifo(fifo)
    outcome: dict[str, BaseException] = {}

    def resolve() -> None:
        try:
            wc.resolve_main_root_without_git(worktree)
        except BaseException as exc:  # recorded for the assertion below
            outcome["raised"] = exc

    thread = threading.Thread(target=resolve, daemon=True)
    thread.start()
    thread.join(timeout=10)
    if thread.is_alive():
        # Give the blocked reader a writer so the thread can end, then fail.
        os.close(os.open(fifo, os.O_WRONLY | os.O_NONBLOCK))
        thread.join(timeout=10)
        pytest.fail(f"resolution blocked on a FIFO {link}")
    assert isinstance(outcome.get("raised"), wc.NotAGitRepositoryError)


def test_resolve_main_root_without_git_follows_relative_worktree_links(layout: Layout):
    """``worktree.useRelativePaths`` writes both links relative to their own files."""
    worktree = layout.dispatch_wt
    gitdir = _worktree_gitdir(worktree)
    (worktree / ".git").write_text(f"gitdir: {os.path.relpath(gitdir, worktree)}\n")
    (gitdir / "gitdir").write_text(f"{os.path.relpath(worktree / '.git', gitdir)}\n")
    assert wc.resolve_main_root_without_git(worktree) == layout.main


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


def test_is_primary_checkout_matrix(layout: Layout, outside_any_repo: Path):
    assert wc.is_primary_checkout(layout.main) is True
    assert wc.is_primary_checkout(layout.main / "pkg") is True
    assert wc.is_primary_checkout(layout.dispatch_wt) is False
    assert wc.is_primary_checkout(layout.external_wt) is False
    assert wc.is_primary_checkout(outside_any_repo) is False


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
@pytest.mark.parametrize("redirect", ["gitfile", "symlinked_gitfile", "git_env"])
@pytest.mark.parametrize("tool", ["Write", "Bash", "glob", "nested"])
def test_primary_guard_rejects_cwd_repository_identity_substitution(layout: Layout, redirect: str, tool: str):
    """Worker-controlled Git identity must not redefine the configured protected checkout."""
    foreign = layout.outside / "foreign"
    subprocess.run(
        ["git", "init", "-q", "-b", "main", str(foreign)],
        check=True, capture_output=True, env=_clean_env(), timeout=30,
    )
    env = {
        key: value for key, value in _clean_env().items()
        if key not in {"LEARN_UK_ALLOW_PRIMARY_GIT_WRITE", "LEARN_UK_ALLOW_PRIMARY_WRITE"}
    }
    env["LU_PRODUCT_ROOT"] = str(layout.main)
    env["LEARN_UKRAINIAN_PRIMARY_REPO_ROOT"] = str(layout.main)
    if redirect == "git_env":
        env["GIT_DIR"] = str(foreign / ".git")
        env["GIT_WORK_TREE"] = str(foreign)
    else:
        gitfile = layout.dispatch_wt / ".git"
        if redirect == "symlinked_gitfile":
            replacement = layout.outside / "gitfile"
            replacement.write_text(f"gitdir: {foreign}/.git\n")
            gitfile.unlink()
            gitfile.symlink_to(replacement)
        else:
            gitfile.write_text(f"gitdir: {foreign}/.git\n")
    hook = Path(__file__).resolve().parents[1] / "agents_extensions/shared/hooks/guard-primary-checkout-write.py"

    def decision(target: Path) -> subprocess.CompletedProcess[str]:
        if tool == "Write":
            name, args = "Write", {"file_path": str(target), "content": "replacement"}
        else:
            command = f"touch {target}"
            if tool == "glob":
                command = f"touch {target.parent}/trac*.txt"
            elif tool == "nested":
                command = f"cd {foreign}; touch {target}"
            name, args = "Bash", {"command": command}
        return subprocess.run(
            [sys.executable, str(hook)],
            input=json.dumps({"tool_name": name, "cwd": str(layout.dispatch_wt), "tool_input": args}),
            cwd=layout.dispatch_wt, env=env, capture_output=True, text=True, timeout=60,
        )

    denied = decision(layout.main / "tracked.txt")
    assert denied.returncode == 2, denied.stderr
    assert "BLOCKED" in denied.stderr
    assert (layout.main / "tracked.txt").read_text() == "tracked\n"
    allowed = decision(layout.dispatch_wt / "tracked.txt")
    assert allowed.returncode == 0, allowed.stderr


@pytest.mark.parametrize(
    "product_kind",
    ["primary", "worktree", "alias", "other_primary", "primary_alias", "subdirectory", "snapshot", "other_worktree", "foreign_cwd"],
)
@pytest.mark.parametrize("tool", ["Write", "Bash", "glob", "stdin", "stdin_inplace", "find_list"])
def test_primary_guard_keeps_configured_and_additional_primary_protection(layout: Layout, product_kind: str, tool: str):
    """Root contexts must preserve direct primary denials and configured/cwd parser refusals."""
    other = layout.outside
    _git(other, "init", "-q", "-b", "main")
    _git(other, "config", "user.email", "fixture@example.invalid")
    _git(other, "config", "user.name", "Fixture")
    (other / "tracked.txt").write_text("other\n")
    _git(other, "add", "tracked.txt")
    _git(other, "commit", "-qm", "fixture")
    alias = layout.main.parent / "primary-alias"
    alias.symlink_to(layout.main, target_is_directory=True)
    snapshot = layout.main.parent / "snapshot"
    snapshot.mkdir()
    other_worktree = other / ".worktrees/dispatch/codex/product"
    _git(other, "worktree", "add", "-q", "-b", "product", str(other_worktree))
    product = {
        "worktree": layout.dispatch_wt, "alias": alias, "other_primary": other,
        "subdirectory": layout.main / "pkg", "snapshot": snapshot, "other_worktree": other_worktree,
    }.get(product_kind, layout.main)
    cwd = other_worktree if product_kind in {"other_worktree", "foreign_cwd"} else layout.dispatch_wt
    env = {
        key: value for key, value in _clean_env().items()
        if key not in {"LEARN_UK_ALLOW_PRIMARY_GIT_WRITE", "LEARN_UK_ALLOW_PRIMARY_WRITE"}
    }
    marker = product / "curriculum/l2-uk-en/curriculum.yaml"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.touch()
    env.update(
        LU_PRODUCT_ROOT=str(product),
        LEARN_UKRAINIAN_PRIMARY_REPO_ROOT=str(alias if product_kind == "primary_alias" else layout.main),
    )
    hook = Path(__file__).resolve().parents[1] / "agents_extensions/shared/hooks/guard-primary-checkout-write.py"

    def decision(name: str, args: dict) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(hook)],
            input=json.dumps({"tool_name": name, "cwd": str(cwd), "tool_input": args}),
            cwd=cwd, env=env, capture_output=True, text=True, timeout=60,
        )

    readonly = decision("Bash", {"command": "ls"})
    assert readonly.returncode == 0, readonly.stderr
    for target, expected in ((layout.main / "tracked.txt", 2), (layout.dispatch_wt / "tracked.txt", 0), (other / "tracked.txt", 2)):
        if tool == "Write":
            name, args = "Write", {"file_path": str(target), "content": "replacement"}
        elif tool in {"Bash", "glob"}:
            word = shlex.quote(str(target)) if tool == "Bash" else f"{shlex.quote(str(target.parent))}/trac*.txt"
            name, args = "Bash", {"command": f"touch {word}"}
        else:
            if tool == "find_list":
                command = f"find -files0-from {shlex.quote(str(target.parent / 'list'))} -delete"
            else:
                writer = "sed -i s/a/b/" if tool == "stdin_inplace" else "rm"
                command = f"printf '%s\\n' {shlex.quote(str(target))} | xargs {writer}"
            name, args = "Bash", {"command": command}
            # Stdin is undecidable for configured/cwd primaries. An unrelated
            # source word alone did not select a primary in the original parser.
            if target.parent == other and product_kind not in {"other_primary", "other_worktree", "foreign_cwd"}:
                expected = 0
        result = decision(name, args)
        assert result.returncode == expected, result.stderr
    if product_kind in {"other_primary", "other_worktree"}:
        for primary in (layout.main, other):
            result = decision("Bash", {"command": f"git -C {shlex.quote(str(primary))} reset --hard"})
            assert result.returncode == 2, result.stderr
    elif product_kind == "foreign_cwd":
        result = decision("Bash", {"command": f"git -C {shlex.quote(str(other))} merge --ff-only main"})
        assert result.returncode == 0, result.stderr
    assert (layout.main / "tracked.txt").read_text() == "tracked\n"
    assert (other / "tracked.txt").read_text() == "other\n"




@pytest.mark.parametrize("invalid", ["worktree", "relative", "missing", "nongit", "symlinked_git", "commondir"])
def test_primary_guard_refuses_invalid_mandatory_authority(layout: Layout, invalid: str):
    """An invalid mandatory primary must not be replaced by an otherwise valid product."""
    primary = layout.main
    value = {
        "worktree": str(layout.dispatch_wt), "relative": ".", "missing": str(layout.outside / "missing"),
        "nongit": str(layout.outside),
    }.get(invalid, str(primary))
    if invalid == "symlinked_git":
        original = primary / ".git"
        moved = layout.outside / "git-metadata"
        original.rename(moved)
        original.symlink_to(moved, target_is_directory=True)
    elif invalid == "commondir":
        (primary / ".git/commondir").write_text(".\n")
    environment = _clean_env()
    environment.update(LU_PRODUCT_ROOT=str(primary), LEARN_UKRAINIAN_PRIMARY_REPO_ROOT=value)
    environment.pop("LEARN_UK_ALLOW_PRIMARY_WRITE", None)
    hook = Path(__file__).resolve().parents[1] / "agents_extensions/shared/hooks/guard-primary-checkout-write.py"
    result = subprocess.run(
        [sys.executable, str(hook)], cwd=layout.dispatch_wt, env=environment,
        input=json.dumps({"tool_name": "Write", "cwd": str(layout.dispatch_wt),
                          "tool_input": {"file_path": str(primary / "tracked.txt")}}),
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 2, result.stderr
    assert "product_root_unavailable" in result.stderr
    assert (primary / "tracked.txt").read_text() == "tracked\n"
