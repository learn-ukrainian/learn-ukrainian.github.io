"""Small shared helpers for Git subprocesses running under the API service."""

from __future__ import annotations

import os
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


# git-check-ref-format(1): no ASCII controls, space, or these punctuation bytes.
_REF_FORBIDDEN_CHARS = frozenset(" ~^:?*[\\")


def _rejects_git_branch_format(name: str) -> bool:
    """Return whether ``name`` violates ``git check-ref-format --branch`` rules.

    One-level names are allowed, matching ``--branch``. Three names are
    refused on purpose, beside the format rules, because a git version may
    accept or rewrite them:

    * ``@`` — ``--branch`` prints it. It is the shorthand for the current
      branch, not a branch name this gate may fetch.
    * ``@{-N}`` — git expands that shorthand to a previous checkout.
    * ``HEAD`` — it is the symbolic ref for the current commit. Some git
      versions still accept ``refs/heads/HEAD`` from ``--branch``; a branch
      of that name collides with the symbolic ref, so this gate refuses it
      on every version.
    """
    if not name or name in {"@", "HEAD"} or name.startswith("-"):
        return True
    if name.startswith("/") or name.endswith("/") or name.endswith("."):
        return True
    if ".." in name or "@{" in name or "//" in name:
        return True
    for char in name:
        if ord(char) < 0x20 or ord(char) == 0x7F or char in _REF_FORBIDDEN_CHARS:
            return True
    for component in name.split("/"):
        if not component or component.startswith(".") or component.endswith(".lock"):
            return True
    return False


def validate_plain_branch_name(branch: str, *, repo_root: str | Path) -> str:
    """Reject an unsafe branch name using pure ``check-ref-format --branch`` rules.

    Shared by the Gemini remote-branch gate, ``ask --pr`` head resolution, and
    ``delegate --branch`` reuse. Prefix rejects (``origin/``, ``refs/``,
    ``github/``, ``+``, ``-``, and ``:``) run first. The rest follows
    git-check-ref-format(1) in-process so a hung or redirected ``git`` cannot
    fail the check. ``repo_root`` stays in the signature for those callers; this
    function does not read it or invoke git.
    """
    del repo_root
    normalized = branch.strip()
    if (
        not normalized
        or normalized.startswith(_UNSAFE_BRANCH_PREFIXES)
        or ":" in normalized
        or _rejects_git_branch_format(normalized)
    ):
        raise UnsafeBranchNameError(f"refusing branch name {branch!r}")
    return normalized
