"""Small shared helpers for Git subprocesses running under the API service."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

GIT_REDIRECT_ENV_KEYS = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_PREFIX",
    "GIT_COMMON_DIR",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_NAMESPACE",
    "GIT_CEILING_DIRECTORIES",
    "GIT_DISCOVERY_ACROSS_FILESYSTEM",
)


def sanitized_git_env() -> dict[str, str]:
    """Return an environment that lets ``git -C`` select only its explicit root."""
    return {key: value for key, value in os.environ.items() if key not in GIT_REDIRECT_ENV_KEYS}


# Names that look like a remote, a ref namespace, or a fetch refspec. A plain
# branch may contain slashes (``cursor/task``) but must not be one of these.
_UNSAFE_BRANCH_PREFIXES = ("origin/", "refs/", "github/", "+", "-")


class UnsafeBranchNameError(ValueError):
    """The branch name is empty, prefixed, or not a valid git branch."""


def origin_tracking_refspec(branch: str) -> str:
    """Map ``refs/heads/<branch>`` onto ``refs/remotes/origin/<branch>``.

    An explicit destination is required: ``git fetch origin <name>`` updates
    ``origin/<name>`` only when the remote's fetch refspec covers it. A narrow
    clone otherwise writes FETCH_HEAD and leaves the tracking ref stale.
    """
    return f"+refs/heads/{branch}:refs/remotes/origin/{branch}"


def validate_plain_branch_name(branch: str, *, repo_root: str | Path) -> str:
    """Reject an unsafe branch name, then confirm it with ``git check-ref-format``.

    Shared by the Gemini remote-branch gate, ``ask --pr`` head resolution, and
    ``delegate --branch`` reuse. Prefix, ``:``, and ``@{`` checks run before git
    so a refspec or ``@{-N}`` shorthand never becomes a command argument.
    ``check-ref-format --branch`` expands ``@{-N}`` to a previous checkout and
    prints that name; the value returned is git's stdout, the name git accepted.
    """
    normalized = branch.strip()
    if (
        not normalized
        or normalized.startswith(_UNSAFE_BRANCH_PREFIXES)
        or ":" in normalized
        or "@{" in normalized
        or "\n" in normalized
        or "\x00" in normalized
    ):
        raise UnsafeBranchNameError(f"refusing branch name {branch!r}")
    try:
        proc = subprocess.run(
            ["git", "check-ref-format", "--branch", normalized],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
            env=sanitized_git_env(),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise UnsafeBranchNameError(f"refusing branch name {branch!r}: {exc}") from exc
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip().replace("\n", " ")
        raise UnsafeBranchNameError(
            f"refusing branch name {branch!r}: {detail or f'exit {proc.returncode}'}"
        )
    confirmed = (proc.stdout or "").strip()
    if (
        not confirmed
        or "\n" in confirmed
        or confirmed.startswith(_UNSAFE_BRANCH_PREFIXES)
        or ":" in confirmed
        or "@{" in confirmed
        or "\x00" in confirmed
    ):
        raise UnsafeBranchNameError(f"refusing branch name {branch!r}: git confirmed {confirmed!r}")
    return confirmed
