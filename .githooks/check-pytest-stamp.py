"""Require a recent pytest stamp before content is pushed to ``main``.

Git has already resolved the working tree and ref updates before this hook is
called.  That makes the update records on stdin the sole authority for whether
this is a push to ``main``; do not infer it from HEAD or shell arguments.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pytest_stamp import (
    MARKER_MAX_AGE_SECONDS,
    StampIdentity,
    marker_is_fresh,
    marker_path,
    stamp_identity_for_branch,
)

TRIGGER_PREFIXES = (
    "tests/",
    "scripts/",
    "curriculum/",
    "agents_extensions/shared/rules/",
    ".dagger/",
)
MAIN_REF = "refs/heads/main"


def _is_all_zero(value: str) -> bool:
    return bool(value) and set(value) == {"0"}


def _git_environment() -> dict[str, str]:
    """Avoid caller-provided Git state changing the repository Git selected.

    Git invokes a non-bare hook from the worktree root, so discovery from this
    process's cwd is sufficient.  Removing inherited ``GIT_*`` overrides keeps
    a poisoned shell environment from turning a required check into fail-open.
    """
    return {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}


def _git_output(*args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            check=False,
            env=_git_environment(),
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout


def _changed_paths(remote_sha: str, local_sha: str) -> list[str] | None:
    if _is_all_zero(remote_sha):
        merge_base = _git_output("merge-base", "origin/main", local_sha)
        if merge_base is None:
            return None
        base = merge_base.strip()
        if not base:
            return None
        diff_range = f"{base}..{local_sha}"
    else:
        diff_range = f"{remote_sha}..{local_sha}"

    output = _git_output("diff", "--name-only", diff_range)
    if output is None:
        return None
    return [path for path in output.splitlines() if path]


def _is_trigger_path(path: str) -> bool:
    return path.startswith(TRIGGER_PREFIXES)


def _branch_from_local_ref(local_ref: str, local_sha: str) -> str | None:
    prefix = "refs/heads/"
    if local_ref.startswith(prefix):
        branch = local_ref.removeprefix(prefix)
        return branch or None

    # Git sends the literal ``HEAD`` for ``git push origin HEAD:main``.  It
    # does not include the symbolic branch name in the stdin record.  Resolve
    # the pushed object against local branch refs, rather than consulting the
    # current branch (which is unrelated to an explicit refspec).  A missing
    # or ambiguous result must be refused by ``main()``: otherwise a SHA push,
    # detached HEAD, or probe failure could evade the pytest requirement.
    if local_ref != "HEAD":
        return None
    output = _git_output("for-each-ref", "--format=%(refname)", "--points-at", local_sha, "refs/heads")
    if output is None:
        return None
    branches = [line.removeprefix(prefix) for line in output.splitlines() if line.startswith(prefix)]
    return branches[0] if len(branches) == 1 else None


def _stamp_identity(branch: str) -> StampIdentity | None:
    return stamp_identity_for_branch(Path.cwd(), branch)


def _block_message(branch: str, marker: Path) -> None:
    print(
        "Push to main blocked: this update changes pytest-triggering paths.\n"
        f"The pytest stamp for local branch '{branch}' is missing or older than "
        f"{MARKER_MAX_AGE_SECONDS} seconds:\n"
        f"  {marker}\n\n"
        "Rerun pytest to refresh the stamp, then push again.\n"
        "To intentionally bypass this discipline check, use: git push --no-verify",
        file=sys.stderr,
    )


def _verification_error(reason: str) -> None:
    """Explain a fail-closed refusal when the guard cannot verify an update."""
    print(
        "Push to main blocked: "
        f"{reason}; the pytest requirement could not be verified.\n"
        "Resolve the Git or filesystem error and push again.\n"
        "To intentionally bypass this discipline check, use: git push --no-verify",
        file=sys.stderr,
    )


def _updates() -> list[tuple[str, str, str, str]] | None:
    try:
        lines = sys.stdin.read().splitlines()
    except OSError:
        return None

    updates: list[tuple[str, str, str, str]] = []
    for line in lines:
        fields = line.split()
        if len(fields) != 4:
            return None
        updates.append(tuple(fields))
    return updates


def main() -> int:
    if os.environ.get("SKIP_PYTEST_HOOK") == "1":
        return 0

    updates = _updates()
    if updates is None:
        _verification_error("could not read valid ref updates from Git")
        return 1

    for local_ref, local_sha, remote_ref, remote_sha in updates:
        if remote_ref != MAIN_REF or _is_all_zero(local_sha):
            continue

        paths = _changed_paths(remote_sha, local_sha)
        if paths is None:
            _verification_error("could not determine changed paths")
            return 1
        if not any(_is_trigger_path(path) for path in paths):
            continue

        branch = _branch_from_local_ref(local_ref, local_sha)
        if branch is None:
            _verification_error("could not determine the local source branch for the pytest stamp")
            return 1
        identity = _stamp_identity(branch)
        if identity is None:
            _verification_error(
                f"could not resolve the registered worktree for local branch '{branch}'"
            )
            return 1
        marker = marker_path(identity)
        is_fresh = marker_is_fresh(marker, identity)
        if is_fresh is None:
            _verification_error(f"could not inspect the pytest stamp at {marker}")
            return 1
        if not is_fresh:
            _block_message(branch, marker)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
