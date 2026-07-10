"""Centralized main-checkout vs worktree containment predicate (issue #4444).

Several proposed guardrails need the same answer: is a target path inside the
protected *primary checkout*, inside an added *worktree*, gitignored *runtime
state*, or *outside* the repo entirely? If each hook / runtime path / git shim
reimplements that logic, containment bugs drift apart. This module is the single
source of truth those layers import instead of duplicating prefix checks.

Design notes
------------
* **Canonicalize first.** Every path is resolved to a real absolute path with
  ``Path.resolve()`` (symlinks followed, ``..`` segments collapsed) *before* any
  containment comparison. Non-existent leaves resolve lexically against their
  nearest existing ancestor, so a path about to be created classifies the same
  as one that already exists.
* **Ask git, not the filesystem.** The primary root is resolved via
  ``git rev-parse --git-common-dir`` (the shared object store lives at
  ``<main_root>/.git``), which is robust from the main checkout, a subdirectory,
  a ``.worktrees/**`` dispatch worktree, or an unrelated added worktree — all
  resolve to the *same* primary root. Tracked/ignored status comes from
  ``git ls-files`` and ``git check-ignore`` semantics, never raw string
  matching, so ``.gitignore`` edits never desync this module.

Public API
----------
* :func:`resolve_main_root` — primary checkout root that owns the shared ``.git``
* :func:`classify_repo_path` — :data:`PathClass` for any path
* :func:`is_primary_checkout` — is a cwd/path the protected primary checkout?
* :func:`is_tracked` / :func:`is_ignored` — git plumbing predicates
* :func:`evaluate_write` / :func:`is_write_allowed` — write-guard decision

Downstream guardrail issues (#4448 hooks, #4449 monitor, #4450 git shim) import
these helpers rather than re-deriving containment.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from scripts.git_context import GIT_REDIRECT_ENV_KEYS, sanitized_git_env

__all__ = [
    "PROTECTED_BRANCHES",
    "NotAGitRepositoryError",
    "PathClass",
    "WriteDecision",
    "canonicalize",
    "classify_repo_path",
    "current_branch",
    "evaluate_write",
    "is_dispatch_worktree",
    "is_ignored",
    "is_primary_checkout",
    "is_protected_branch",
    "is_tracked",
    "is_write_allowed",
    "primary_checkout_dirty_status",
    "registered_worktrees",
    "resolve_main_root",
]

# A path is exactly one of these relative to the primary checkout:
#   primary_checkout  – inside the protected main checkout (NOT under .worktrees)
#   dispatch_worktree – inside <main>/.worktrees/dispatch/<agent>/<task>/...
#   other_worktree    – any other registered worktree (flat .worktrees/* or an
#                       externally-located worktree sharing the same .git store)
#   outside_repo      – not inside the primary checkout or any known worktree
PathClass = Literal[
    "primary_checkout",
    "dispatch_worktree",
    "other_worktree",
    "outside_repo",
]

# Branches on which the primary checkout must stay clean. Consumers gate their
# enforcement on this (hooks/#4448, monitor/#4449, git shim/#4450 all speak of
# "a protected branch"); containment classification itself is branch-agnostic.
PROTECTED_BRANCHES: frozenset[str] = frozenset({"main", "master"})

# Compatibility export for callers that construct isolated Git fixtures. The
# canonical list and the production sanitizer both live in ``git_context``.
_GIT_ENV_DENYLIST = frozenset(GIT_REDIRECT_ENV_KEYS)

@dataclass(frozen=True)
class WriteDecision:
    """Outcome of a write-guard evaluation.

    ``allowed`` is the boolean decision. ``reason`` is a stable snake_case code
    (safe to branch on). ``path_class`` is the underlying classification.
    ``message`` is operator/agent-facing guidance (populated on denial).
    """

    allowed: bool
    reason: str
    path_class: PathClass
    message: str = ""


# ---------------------------------------------------------------------------
# git helpers
# ---------------------------------------------------------------------------

def _run_git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run a read-only git command scoped to ``cwd`` with sanitized env."""
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        capture_output=True,
        text=True,
        check=False,
        env=sanitized_git_env(),
    )


def _git_dir_for(path: Path) -> Path:
    """Directory to hand to ``git -C`` for ``path`` (its parent if a file)."""
    real = canonicalize(path)
    return real if real.is_dir() else real.parent


# ---------------------------------------------------------------------------
# canonicalization + root resolution
# ---------------------------------------------------------------------------

def canonicalize(path: Path | str) -> Path:
    """Resolve ``path`` to a real absolute path.

    Follows symlinks and collapses ``..`` for the portion that exists; any
    non-existent leaf is appended lexically (``..`` still collapsed). This is
    what lets a not-yet-created file be classified the same as an existing one,
    and neutralizes both symlink escapes and ``..`` escapes before containment
    checks (``Path.resolve`` is non-strict on Python 3.6+).
    """
    return Path(path).expanduser().resolve()


class NotAGitRepositoryError(RuntimeError):
    """Raised by :func:`resolve_main_root` when ``start`` is not in a repo."""


def _resolve_main_root_or_none(start: Path) -> Path | None:
    """Primary checkout root for ``start``, or None if it is not in a repo.

    Prefers ``git rev-parse --git-common-dir`` (the common dir is
    ``<main_root>/.git``); if git is unavailable it falls back to walking
    ``.git`` links on disk. Returns None — never a fabricated root — when
    nothing git-owned is found, so out-of-repo paths classify honestly.
    """
    start_dir = _git_dir_for(start)

    proc = _run_git(start_dir, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if proc.returncode == 0:
        common = proc.stdout.strip()
        if common:
            common_dir = canonicalize(Path(common))
            # A non-bare repo's common dir is ``<main_root>/.git``.
            if common_dir.name == ".git":
                return common_dir.parent
            # Bare repo / unusual layout: the working root is the toplevel.
            top = _run_git(start_dir, "rev-parse", "--show-toplevel")
            if top.returncode == 0 and top.stdout.strip():
                return canonicalize(Path(top.stdout.strip()))

    return _fs_main_root(start_dir)


def resolve_main_root(start: Path | str | None = None) -> Path:
    """Return the primary checkout root that owns the shared ``.git`` store.

    Robust from anywhere in the tree: the main checkout, a subdirectory, a
    ``.worktrees/**`` dispatch worktree, or an externally-located added
    worktree all resolve to the *same* root. ``start`` defaults to the process
    cwd. Raises :class:`NotAGitRepositoryError` if ``start`` is not inside a
    git repository — soft callers should use :func:`classify_repo_path`,
    :func:`is_primary_checkout`, or the internal helper instead.
    """
    origin = Path(start) if start is not None else Path.cwd()
    root = _resolve_main_root_or_none(origin)
    if root is None:
        raise NotAGitRepositoryError(f"{origin} is not inside a git repository")
    return root


def _fs_main_root(start_dir: Path) -> Path | None:
    """Filesystem fallback when git is unavailable.

    Walks upward from ``start_dir`` for a ``.git`` entry. A ``.git`` *directory*
    marks a primary checkout. A ``.git`` *file* points at a worktree gitdir; if
    that lives under ``<root>/.git/worktrees/<name>`` the primary root is that
    outer ``<root>``. Returns None when no ``.git`` is found upward.
    """
    for candidate in (start_dir, *start_dir.parents):
        git_path = candidate / ".git"
        if git_path.is_dir():
            return candidate
        if git_path.is_file():
            try:
                first = git_path.read_text().splitlines()[0]
            except (IndexError, OSError):
                continue
            prefix = "gitdir:"
            if not first.startswith(prefix):
                continue
            git_dir = Path(first[len(prefix):].strip())
            if not git_dir.is_absolute():
                git_dir = candidate / git_dir
            git_dir = canonicalize(git_dir)
            if git_dir.parent.name == "worktrees" and git_dir.parent.parent.name == ".git":
                return git_dir.parent.parent.parent
            return candidate
    return None


def registered_worktrees(main_root: Path) -> list[Path]:
    """Canonical paths of every worktree registered with ``main_root``.

    Includes the primary checkout itself (first entry). Empty list if git is
    unavailable; callers fall back to structural ``.worktrees/**`` checks.
    """
    proc = _run_git(main_root, "worktree", "list", "--porcelain")
    if proc.returncode != 0:
        return []
    roots: list[Path] = []
    for line in proc.stdout.splitlines():
        if line.startswith("worktree "):
            roots.append(canonicalize(Path(line[len("worktree "):].strip())))
    return roots


# ---------------------------------------------------------------------------
# containment classification
# ---------------------------------------------------------------------------

def _is_within(path: Path, base: Path) -> bool:
    """True if ``path`` is ``base`` or nested under it (both pre-canonicalized)."""
    return path == base or path.is_relative_to(base)


def classify_repo_path(path: Path | str, cwd: Path | str | None = None) -> PathClass:
    """Classify ``path`` relative to the primary checkout.

    ``cwd`` (defaulting to the process cwd) only anchors *which* repo we resolve
    the primary root from; the classification is about ``path`` itself. Returns
    one of :data:`PathClass`.
    """
    target = canonicalize(path)
    anchor = canonicalize(cwd) if cwd is not None else Path.cwd().resolve()
    main_root = _resolve_main_root_or_none(anchor)
    if main_root is None:
        # The anchor is not in any repo (e.g. classifying a bare tmp path with
        # a non-repo cwd). Fall back to resolving from the target itself.
        main_root = _resolve_main_root_or_none(target)
        if main_root is None:
            return "outside_repo"
    worktrees_dir = main_root / ".worktrees"

    # The ``.worktrees/**`` subtree is classified structurally so a dispatch
    # directory an agent is about to create (not yet a registered worktree)
    # still reads as an allowed dispatch location.
    if _is_within(target, worktrees_dir):
        rel = target.relative_to(worktrees_dir)
        if rel.parts and rel.parts[0] == "dispatch":
            return "dispatch_worktree"
        return "other_worktree"

    # Any other registered worktree sharing this .git store — e.g. an
    # externally-located worktree under ~/.codex/worktrees/... — is isolated
    # from the primary checkout and therefore an allowed write location.
    for worktree in registered_worktrees(main_root):
        if worktree == main_root:
            continue
        if _is_within(target, worktree):
            return "other_worktree"

    if _is_within(target, main_root):
        return "primary_checkout"

    return "outside_repo"


def is_primary_checkout(path_or_cwd: Path | str | None = None) -> bool:
    """True if ``path_or_cwd`` (default: process cwd) is the primary checkout."""
    target = Path(path_or_cwd) if path_or_cwd is not None else Path.cwd()
    return classify_repo_path(target, cwd=target) == "primary_checkout"


def is_dispatch_worktree(path_or_cwd: Path | str | None = None) -> bool:
    """True if ``path_or_cwd`` is inside a ``.worktrees/dispatch/**`` worktree."""
    target = Path(path_or_cwd) if path_or_cwd is not None else Path.cwd()
    return classify_repo_path(target, cwd=target) == "dispatch_worktree"


# ---------------------------------------------------------------------------
# tracked / ignored plumbing
# ---------------------------------------------------------------------------

def _relpath_in_root(path: Path, main_root: Path) -> str | None:
    """``path`` expressed relative to ``main_root``, or None if not contained.

    A relative pathspec avoids /var vs /private/var canonicalization skew
    between what git reports and what we resolve.
    """
    real = canonicalize(path)
    try:
        return str(real.relative_to(main_root))
    except ValueError:
        return None


def is_tracked(path: Path | str, main_root: Path | None = None) -> bool:
    """True if ``path`` is a file tracked in the primary checkout's index."""
    root = canonicalize(main_root) if main_root is not None else _resolve_main_root_or_none(Path(path))
    if root is None:
        return False
    rel = _relpath_in_root(Path(path), root)
    if rel is None:
        return False
    proc = _run_git(root, "ls-files", "--error-unmatch", "--", rel)
    return proc.returncode == 0


def is_ignored(path: Path | str, main_root: Path | None = None) -> bool:
    """True if ``path`` matches a gitignore rule in the primary checkout."""
    root = canonicalize(main_root) if main_root is not None else _resolve_main_root_or_none(Path(path))
    if root is None:
        return False
    rel = _relpath_in_root(Path(path), root)
    if rel is None:
        return False
    # -q: quiet, exit 0 == ignored, 1 == not ignored, 128 == error.
    proc = _run_git(root, "check-ignore", "-q", "--", rel)
    return proc.returncode == 0


def current_branch(root: Path | str | None = None) -> str | None:
    """Current branch name of the checkout at ``root``, or None if detached."""
    start = _git_dir_for(Path(root) if root is not None else Path.cwd())
    proc = _run_git(start, "symbolic-ref", "--quiet", "--short", "HEAD")
    if proc.returncode != 0:
        return None
    return proc.stdout.strip() or None


def is_protected_branch(root: Path | str | None = None) -> bool:
    """True if the checkout at ``root`` is on a :data:`PROTECTED_BRANCHES` branch."""
    branch = current_branch(root)
    return branch is not None and branch in PROTECTED_BRANCHES


def _parse_status_porcelain_z(stdout: str) -> list[dict[str, str]]:
    """Parse ``git status --porcelain=v1 -z`` entries.

    Ignored files are absent because callers do not pass ``--ignored``. Rename
    and copy entries carry a second NUL-delimited source path; we skip that
    extra token because the destination path is sufficient for the dirty-main
    tripwire.
    """
    entries: list[dict[str, str]] = []
    parts = stdout.split("\0")
    index = 0
    while index < len(parts):
        raw = parts[index]
        index += 1
        if not raw:
            continue
        xy = raw[:2]
        path = raw[3:] if len(raw) > 3 else ""
        entries.append({
            "xy": xy,
            "path": path,
            "kind": "untracked" if xy == "??" else "tracked",
        })
        if xy[:1] in {"R", "C"} or xy[1:2] in {"R", "C"}:
            index += 1
    return entries


def primary_checkout_dirty_status(start: Path | str | None = None) -> dict:
    """Return dirty-state detail for the protected primary checkout.

    The check intentionally uses git status plumbing from the primary checkout
    root and omits ignored files, so gitignored local runtime state does not
    count as dirty. Tracked modifications/deletions and untracked non-ignored
    files both count because either would pollute the primary checkout for the
    next dispatched writer.
    """
    main_root = resolve_main_root(start)
    branch = current_branch(main_root)
    command = ("git", "status", "--porcelain=v1", "-z", "--untracked-files=all")
    proc = _run_git(main_root, *command[1:])
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip() or "git status failed"
        raise RuntimeError(
            f"could not inspect primary checkout dirty state "
            f"(cwd={main_root}, command={' '.join(command)}): {detail}"
        )

    entries = _parse_status_porcelain_z(proc.stdout or "")
    tracked_count = sum(1 for entry in entries if entry["kind"] == "tracked")
    untracked_count = sum(1 for entry in entries if entry["kind"] == "untracked")
    return {
        "main_root": str(main_root),
        "branch": branch,
        "protected_branch": branch in PROTECTED_BRANCHES if branch else False,
        "dirty": bool(entries),
        "dirty_count": len(entries),
        "tracked_dirty_count": tracked_count,
        "untracked_dirty_count": untracked_count,
        "entries": entries,
        "checked_cwd": str(main_root),
        "checked_command": " ".join(command),
    }


# ---------------------------------------------------------------------------
# write-guard decision
# ---------------------------------------------------------------------------

_WORKTREE_HINT = (
    "Primary checkout is protected. Create and cd into a dispatch worktree "
    "(.worktrees/dispatch/<agent>/<task>/) before writing."
)


def evaluate_write(path: Path | str, cwd: Path | str | None = None) -> WriteDecision:
    """Decide whether a write to ``path`` is allowed, with full detail.

    Writes are allowed everywhere except tracked or untracked-and-not-ignored
    files inside the primary checkout — both would dirty the protected tree.
    Gitignored local/runtime state inside the primary checkout is allowed.
    """
    path_class = classify_repo_path(path, cwd=cwd)

    if path_class != "primary_checkout":
        # Worktrees (dispatch or otherwise) and out-of-repo paths are isolated
        # from the protected tree.
        return WriteDecision(allowed=True, reason=path_class, path_class=path_class)

    # class == primary_checkout guarantees the target resolved under a real
    # primary root; resolve it once and reuse for both plumbing calls.
    anchor = canonicalize(cwd) if cwd is not None else canonicalize(path)
    main_root = _resolve_main_root_or_none(anchor) or _resolve_main_root_or_none(canonicalize(path))
    if is_tracked(path, main_root):
        return WriteDecision(
            allowed=False,
            reason="tracked_primary_checkout",
            path_class=path_class,
            message=_WORKTREE_HINT,
        )
    if is_ignored(path, main_root):
        return WriteDecision(
            allowed=True,
            reason="gitignored_local_state",
            path_class=path_class,
        )
    # Untracked and not ignored: creating/writing this dirties the primary
    # working tree with a new file. Blocked with a distinct reason so a
    # consumer that only cares about tracked files (e.g. #4448) can branch.
    return WriteDecision(
        allowed=False,
        reason="untracked_primary_checkout",
        path_class=path_class,
        message=_WORKTREE_HINT,
    )


def is_write_allowed(path: Path | str, cwd: Path | str | None = None) -> tuple[bool, str]:
    """``(allowed, reason)`` for a write to ``path`` — see :func:`evaluate_write`."""
    decision = evaluate_write(path, cwd=cwd)
    return decision.allowed, decision.reason
