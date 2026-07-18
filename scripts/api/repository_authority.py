"""Shared repository, live-data checkout, and serving-code identity."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse

from scripts.common.git_context import sanitized_git_env
from scripts.common.release_layout import MANIFEST_NAME, is_release_root

_FULL_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_REPOSITORY_PART_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
_GIT_TIMEOUT_S = 2.0


class RepositoryAuthorityError(RuntimeError):
    """Raised when the API cannot establish its fixed repository identity."""


def preparation_data_root(*, project_root: Path, live_repo_root: Path) -> Path:
    """Return the checkout whose files back preparation responses.

    Release snapshots link mutable data to the configured live checkout. A
    development server reads directly from its code checkout, which may itself
    be a dispatch worktree and must be reported as such.
    """
    return live_repo_root if is_release_root(project_root.resolve()) else project_root


def _checkout_role(root: Path) -> str:
    git_entry = root / ".git"
    if git_entry.is_file():
        return "dispatch_worktree" if ".worktrees/dispatch" in root.as_posix() else "linked_worktree"
    return "live_primary"


def _git(cwd: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=_GIT_TIMEOUT_S,
            check=False,
            env=sanitized_git_env(),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RepositoryAuthorityError(f"git authority probe failed: {type(exc).__name__}") from exc
    if result.returncode != 0:
        detail = result.stderr.strip() or "git command failed"
        raise RepositoryAuthorityError(detail)
    return result.stdout.strip()


def _repository_slug(remote: str) -> str:
    """Return only owner/name, never a credential-bearing remote URL."""
    value = remote.strip()
    parsed = urlparse(value)
    if parsed.scheme:
        path = parsed.path
    elif ":" in value:
        _prefix, _separator, path = value.rpartition(":")
    else:
        path = value
    parts = [part for part in path.strip("/").split("/") if part]
    if len(parts) < 2:
        raise RepositoryAuthorityError("origin remote does not identify an owner/repository")
    owner, name = parts[-2], parts[-1].removesuffix(".git")
    if not _REPOSITORY_PART_RE.fullmatch(owner) or not _REPOSITORY_PART_RE.fullmatch(name):
        raise RepositoryAuthorityError("origin remote contains an unsafe repository identifier")
    return f"{owner}/{name}"


def _release_identity(project_root: Path) -> dict[str, str | None]:
    if is_release_root(project_root):
        manifest_path = project_root / MANIFEST_NAME
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            release_sha = str(payload["sha"])
            tree_sha256 = str(payload["tree_sha256"])
        except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise RepositoryAuthorityError("serving release manifest is invalid") from exc
        if not _FULL_SHA_RE.fullmatch(release_sha) or not _HASH_RE.fullmatch(tree_sha256):
            raise RepositoryAuthorityError("serving release manifest has invalid hashes")
        return {
            "mode": "release",
            "commit_sha": release_sha,
            "tree_sha256": tree_sha256,
        }

    code_sha = _git(project_root, "rev-parse", "HEAD")
    if not _FULL_SHA_RE.fullmatch(code_sha):
        raise RepositoryAuthorityError("development serving-code SHA is invalid")
    return {
        "mode": "development",
        "commit_sha": code_sha,
        "tree_sha256": None,
    }


def build_repository_authority(
    *,
    project_root: Path,
    live_repo_root: Path,
    data_branch: str | None = None,
    data_head_sha: str | None = None,
) -> dict[str, object]:
    """Build the single authority envelope used by agent-facing API routes.

    The only filesystem path exposed is the configured, fixed live-data root.
    Callers cannot select another root, branch, commit, or worktree.
    """
    try:
        data_root = live_repo_root.resolve(strict=True)
        code_root = project_root.resolve(strict=True)
    except OSError as exc:
        raise RepositoryAuthorityError("configured repository root is unavailable") from exc

    remote = _git(data_root, "remote", "get-url", "origin")
    branch = data_branch if data_branch is not None else _git(data_root, "branch", "--show-current")
    head_sha = data_head_sha if data_head_sha is not None else _git(data_root, "rev-parse", "HEAD")
    if not _FULL_SHA_RE.fullmatch(head_sha):
        raise RepositoryAuthorityError("live-data checkout SHA is invalid")

    return {
        "repository": _repository_slug(remote),
        "data_checkout": {
            "role": _checkout_role(data_root),
            "root": str(data_root),
            "branch": branch or None,
            "head_sha": head_sha,
        },
        "service_code": _release_identity(code_root),
    }
