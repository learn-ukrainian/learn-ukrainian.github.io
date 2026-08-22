"""The one shared open-PR identity probe for worktree-retention callers (#7127).

``post_task_reap._no_open_pr_for_branch`` (the reaper) and
``hramatka_hygiene_check._branch_has_open_pr`` (the closeout gate) both answer
"does this branch still have an open PR?" for the same dispatch worktrees, and
they must not drift apart again — #7126 found them already disagreeing on
malformed rows.  This module expresses the PR-identity binding exactly once:

* an explicit ``--repo`` scope, never gh's cwd fallback;
* ``state == "OPEN"``;
* exact ``headRefName`` equality with the probed branch;
* a non-fork (same-repository) head;
* a positive integer ``number``.

A row that fails any clause makes the WHOLE answer unknown: a partially
understood response never proves absence.  Unknowns come back as
``(None, reason)`` so each caller keeps its own fail-closed direction — the
reaper retains, the gate still counts.  This probe never chooses for them.

Deliberately NOT required: that the PR head OID equals the local worktree
HEAD.  A worktree legitimately sits ahead of or behind its pushed PR head, so
demanding equality would recreate an unpassable gate.  Branch identity plus a
same-repo head is the binding that answers the actual question — is this
worktree still serving an open PR?

This module is a leaf: it imports nothing from either caller, so neither
module body can form an import cycle.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

DEFAULT_PROBE_TIMEOUT_SECONDS = 30.0
_REPO_SLUG_TIMEOUT_SECONDS = 15.0

# Same isolation contract as the reaper modules: gh/git must resolve nothing
# from a stray GIT_* environment pointing at an unrelated checkout.
_GIT_ENV_DENYLIST = {
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_NAMESPACE",
    "GIT_CEILING_DIRECTORIES",
    "GIT_DISCOVERY_ACROSS_FILESYSTEM",
    "GIT_COMMON_DIR",
}

# Same remote-URL grammar as scripts/delegate.py::_GITHUB_REMOTE_PATTERNS.
_GITHUB_REMOTE_PATTERNS = (
    re.compile(r"^https?://(?:[^/@\s]+@)?github\.com/([^/\s]+)/([^/\s]+?)(?:\.git)?/?$", re.IGNORECASE),
    re.compile(r"^ssh://git@github\.com/([^/\s]+)/([^/\s]+?)(?:\.git)?/?$", re.IGNORECASE),
    re.compile(r"^git@github\.com:([^/\s]+)/([^/\s]+?)(?:\.git)?/?$", re.IGNORECASE),
    re.compile(r"^git://github\.com/([^/\s]+)/([^/\s]+?)(?:\.git)?/?$", re.IGNORECASE),
)


def _sanitized_env() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if key not in _GIT_ENV_DENYLIST and not key.startswith("PRE_COMMIT")
    }


def _run_gh(cmd: list[str], *, cwd: Path, timeout: float) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        env=_sanitized_env(),
    )


def resolve_repo_slug(repo_root: Path) -> str | None:
    """Return ``owner/repo`` for the checkout's ``remote.origin.url``, else None.

    Local git-config read only — no network, no gh.  A caller that cannot prove
    the repository identity must treat the open-PR answer as unknown, never
    fall back to gh's cwd-based repository resolution.
    """
    try:
        proc = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=_REPO_SLUG_TIMEOUT_SECONDS,
            check=False,
            env=_sanitized_env(),
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    url = (proc.stdout or "").strip()
    if not url:
        return None
    for pattern in _GITHUB_REMOTE_PATTERNS:
        match = pattern.match(url)
        if match:
            return f"{match.group(1)}/{match.group(2)}"
    return None


def probe_open_pr_for_branch(
    *,
    repo_root: Path,
    repo: str | None,
    branch: str | None,
    timeout: float = DEFAULT_PROBE_TIMEOUT_SECONDS,
) -> tuple[bool | None, str | None]:
    """Return ``(has_open_pr, error)`` for ``branch`` in one explicit repository.

    ``True``  — GitHub provably reports at least one OPEN PR bound to this
                 exact branch (same repo, non-fork head, positive number).
    ``False`` — GitHub provably reports none.
    ``None``  — unknown; ``error`` carries the structural reason.  Error
                 strings never echo gh stderr so they can land in reports.

    Callers choose their own fail-closed direction for ``None``; this probe
    never guesses in either direction.
    """
    if not branch:
        return None, "no branch identity to probe for an open PR"
    if not repo:
        return None, "no explicit repository identity bound to this checkout"
    try:
        proc = _run_gh(
            [
                "gh",
                "pr",
                "list",
                "--repo",
                repo,
                "--head",
                branch,
                "--state",
                "open",
                "--json",
                "number,state,headRefName,isCrossRepository",
            ],
            cwd=repo_root,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        return None, f"gh pr list timed out after {exc.timeout}s"
    except OSError as exc:
        return None, f"gh pr list failed to run: {exc}"
    if proc.returncode != 0:
        return None, f"gh pr list failed (exit {proc.returncode})"
    try:
        rows = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError:
        return None, "gh pr list returned invalid JSON"
    if not isinstance(rows, list):
        return None, "gh pr list returned a non-list payload"

    matched = False
    for row in rows:
        if not isinstance(row, dict):
            return None, "gh pr list returned a malformed row (not an object)"
        number = row.get("number")
        if isinstance(number, bool) or not isinstance(number, int) or number <= 0:
            return None, "gh pr list returned a row without a usable PR number"
        if row.get("state") != "OPEN":
            return None, "gh pr list returned a row whose state is not OPEN"
        if row.get("isCrossRepository") is not False:
            return None, "gh pr list returned a cross-repository (fork) row"
        if row.get("headRefName") != branch:
            return None, "gh pr list returned a row bound to a different branch"
        matched = True
    return matched, None
