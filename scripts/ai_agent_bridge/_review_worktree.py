"""Ephemeral, branch-pinned worktrees for bridge review asks.

Bridge asks normally run from the primary checkout (or, for Agy, grant that
checkout through ``--add-dir``).  A review that names a branch must instead
read a freshly fetched ``origin/<branch>`` snapshot.  This module owns that
short-lived checkout so every review adapter uses the same stale-head and
cleanup rules.
"""

from __future__ import annotations

import contextlib
import json
import os
import shutil
import stat
import subprocess
import tempfile
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ReviewWorktreeError(RuntimeError):
    """A branch-pinned review checkout could not be safely prepared."""


@dataclass(frozen=True)
class ReviewTarget:
    """A review target supplied as either a branch name or a pull request."""

    branch: str | None = None
    pr_number: int | None = None

    def __post_init__(self) -> None:
        if (self.branch is None) == (self.pr_number is None):
            raise ValueError("review target must specify exactly one of branch or pr_number")
        if self.branch is not None and (
            not isinstance(self.branch, str) or not self.branch.strip()
        ):
            raise ValueError("review branch must be a non-empty string")
        if self.pr_number is not None:
            if isinstance(self.pr_number, bool) or not isinstance(self.pr_number, int):
                raise ValueError("review PR number must be an integer")
            if self.pr_number <= 0:
                raise ValueError("review PR number must be positive")


@dataclass(frozen=True)
class ProvisionedReviewWorktree:
    """The immutable branch snapshot made available to one review ask."""

    path: Path
    branch: str
    sha: str
    pr_number: int | None = None


def review_target_payload(
    branch: str | None = None, pr_number: int | None = None
) -> dict[str, Any] | None:
    """Return serializable review-target metadata for a bridge message."""
    if branch is None and pr_number is None:
        return None
    target = ReviewTarget(branch=branch, pr_number=pr_number)
    if target.branch is not None:
        return {"branch": target.branch}
    return {"pr": target.pr_number}


def review_target_from_message(message: dict[str, Any]) -> ReviewTarget | None:
    """Recover optional branch-review metadata stored by ``send_message``."""
    raw_data = message.get("data")
    if not raw_data:
        return None
    try:
        metadata = json.loads(raw_data)
    except (TypeError, json.JSONDecodeError):
        return None
    if not isinstance(metadata, dict):
        return None
    if "review_target" not in metadata:
        return None
    raw_target = metadata.get("review_target")
    if not isinstance(raw_target, dict):
        # Fail closed (#5175 review BLOCKER): a present-but-malformed target must
        # never silently degrade to a primary-checkout review — that IS the bug
        # this module exists to fix.
        raise ReviewWorktreeError("review_target metadata must be an object when present")

    branch = raw_target.get("branch")
    pr_number = raw_target.get("pr")
    if branch is not None and not isinstance(branch, str):
        raise ReviewWorktreeError("review target branch metadata must be a string")
    if pr_number is not None and (isinstance(pr_number, bool) or not isinstance(pr_number, int)):
        raise ReviewWorktreeError("review target PR metadata must be an integer")
    try:
        return ReviewTarget(branch=branch, pr_number=pr_number)
    except ValueError as exc:
        raise ReviewWorktreeError(f"invalid review target metadata: {exc}") from exc


def _run_command(command: list[str], *, cwd: Path) -> str:
    """Run one deterministic checkout command and surface useful failures."""
    completed = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "unknown command failure").strip()
        raise ReviewWorktreeError(f"{' '.join(command)} failed: {detail}")
    return completed.stdout.strip()


def _validate_branch_name(branch: str, *, repo_root: Path) -> str:
    """Reject ambiguous revision syntax before building ``origin/<branch>``."""
    normalized = branch.strip()
    if not normalized or normalized.startswith(("-", "origin/", "refs/")):
        raise ReviewWorktreeError(
            "--branch must be a non-empty branch name without origin/ or refs/ prefixes"
        )
    _run_command(["git", "check-ref-format", "--branch", normalized], cwd=repo_root)
    return normalized


def _resolve_pr_branch(pr_number: int, *, repo_root: Path) -> str:
    """Resolve a PR head name without consulting local branch state."""
    raw = _run_command(
        ["gh", "pr", "view", str(pr_number), "--json", "headRefName"], cwd=repo_root
    )
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ReviewWorktreeError(f"PR #{pr_number} returned invalid JSON") from exc
    branch = payload.get("headRefName") if isinstance(payload, dict) else None
    if not isinstance(branch, str) or not branch.strip():
        raise ReviewWorktreeError(f"PR #{pr_number} did not provide a head branch")
    return _validate_branch_name(branch, repo_root=repo_root)


def _resolve_branch(target: ReviewTarget, *, repo_root: Path) -> tuple[str, int | None]:
    if target.branch is not None:
        return _validate_branch_name(target.branch, repo_root=repo_root), None
    assert target.pr_number is not None
    return _resolve_pr_branch(target.pr_number, repo_root=repo_root), target.pr_number


def _set_owner_writable(path: Path, *, writable: bool) -> None:
    """Toggle owner write permission without following repository symlinks."""
    if not path.exists():
        return
    paths: list[Path] = [path]
    for root, directories, files in os.walk(path, followlinks=False):
        root_path = Path(root)
        paths.extend(root_path / name for name in [*directories, *files])
    for candidate in reversed(paths) if writable else paths:
        try:
            mode = candidate.lstat().st_mode
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(mode):
            continue
        updated = mode | stat.S_IWUSR if writable else mode & ~stat.S_IWUSR
        if updated != mode:
            candidate.chmod(updated)


def _remove_unregistered_path(path: Path) -> None:
    """Remove a temporary directory when ``git worktree add`` never registered it."""
    if not path.exists():
        return
    _set_owner_writable(path, writable=True)
    shutil.rmtree(path)


@contextlib.contextmanager
def provision_review_worktree(
    target: ReviewTarget | None, *, repo_root: Path
) -> Iterator[ProvisionedReviewWorktree | None]:
    """Yield a read-only detached worktree for a branch-targeted review.

    The remote fetch and ``origin/<branch>`` resolution happen before any
    worktree is created.  This deliberately refuses stale local branch heads.
    The teardown is in ``finally`` so reviewer failures cannot strand a
    temporary checkout.
    """
    if target is None:
        yield None
        return

    root = repo_root.resolve()
    # Self-heal SIGKILL-stranded registrations from prior review asks: the
    # finally-teardown below cannot run under SIGKILL, and a stale
    # .git/worktrees/<id> entry otherwise persists forever (#5175 review).
    _run_command(["git", "worktree", "prune"], cwd=root)
    branch, pr_number = _resolve_branch(target, repo_root=root)
    origin_ref = f"origin/{branch}"
    _run_command(["git", "fetch", "origin", branch], cwd=root)
    sha = _run_command(["git", "rev-parse", "--verify", origin_ref], cwd=root)

    path = Path(tempfile.mkdtemp(prefix="learn-ukrainian-review-"))
    path.rmdir()
    registered = False
    try:
        _run_command(
            ["git", "worktree", "add", "--detach", str(path), sha], cwd=root
        )
        registered = True
        actual_sha = _run_command(["git", "rev-parse", "HEAD"], cwd=path)
        if actual_sha != sha:
            raise ReviewWorktreeError(
                f"review worktree HEAD {actual_sha} did not match {origin_ref} {sha}"
            )
        _set_owner_writable(path, writable=False)
        yield ProvisionedReviewWorktree(path, branch, sha, pr_number)
    finally:
        _set_owner_writable(path, writable=True)
        if registered:
            _run_command(["git", "worktree", "remove", "--force", str(path)], cwd=root)
        else:
            _remove_unregistered_path(path)
