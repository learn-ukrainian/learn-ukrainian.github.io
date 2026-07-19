#!/usr/bin/env python3
"""Assert the protected primary checkout is attached to ``main`` (#4857).

Use from launchers (start-*.sh) and SessionStart. Optionally **heal** a
detached / wrong-branch primary with ``--heal`` (ff-only checkout of main).

Exit codes:
  0 — primary is on main (or not a protected primary / not a git repo)
  1 — primary is detached or not on main (and --heal was not requested / failed)
  2 — usage / environment error
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

# Allow running as scripts/guardrails/*.py
_REPO_CANDIDATE = Path(__file__).resolve().parents[2]
if str(_REPO_CANDIDATE) not in sys.path:
    sys.path.insert(0, str(_REPO_CANDIDATE))

from scripts.guardrails.worktree_containment import (
    is_primary_checkout,
    resolve_main_root,
)


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    for name in (
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_PREFIX",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    ):
        env.pop(name, None)
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def primary_head_state(cwd: Path | None = None) -> dict[str, object]:
    """Return head diagnostics for the main worktree of this repo."""
    start = (cwd or Path.cwd()).resolve()
    main_root = resolve_main_root(start)
    if main_root is None:
        return {"ok": True, "reason": "not_a_git_repo", "path": str(start)}
    if not is_primary_checkout(main_root):
        # Called from inside an added worktree — primary state is a separate check.
        return {
            "ok": True,
            "reason": "not_primary_checkout",
            "path": str(main_root),
            "cwd": str(start),
        }

    branch_p = _git(main_root, "symbolic-ref", "--quiet", "--short", "HEAD")
    if branch_p.returncode != 0:
        sha = _git(main_root, "rev-parse", "--short", "HEAD").stdout.strip()
        return {
            "ok": False,
            "reason": "detached_head",
            "path": str(main_root),
            "head": sha,
            "message": (
                f"PRIMARY checkout is DETACHED at {sha or 'unknown'}. "
                "It must stay on branch main (orientation only; writes go in worktrees)."
            ),
        }

    branch = branch_p.stdout.strip()
    if branch not in {"main", "master"}:
        return {
            "ok": False,
            "reason": "wrong_branch",
            "path": str(main_root),
            "branch": branch,
            "message": (
                f"PRIMARY checkout is on '{branch}', not main. "
                "Agents must not switch the primary branch (see #4857)."
            ),
        }

    return {
        "ok": True,
        "reason": "on_main",
        "path": str(main_root),
        "branch": branch,
    }


def heal_primary_to_main(main_root: Path) -> tuple[bool, str]:
    """Force primary back onto main (no force-reset of dirty files)."""
    # Prefer local main; if missing, create tracking branch from origin/main.
    show = _git(main_root, "show-ref", "--verify", "--quiet", "refs/heads/main")
    if show.returncode != 0:
        fetch = _git(main_root, "fetch", "origin", "main")
        if fetch.returncode != 0:
            return False, f"fetch origin main failed: {fetch.stderr.strip()}"
        create = _git(main_root, "checkout", "-B", "main", "origin/main")
        if create.returncode != 0:
            return False, f"checkout -B main origin/main failed: {create.stderr.strip()}"
        return True, "created/reset local main from origin/main"

    co = _git(main_root, "checkout", "main")
    if co.returncode != 0:
        return False, f"git checkout main failed: {co.stderr.strip()}"
    # Fast-forward if possible (never merge/rebase here).
    pull = _git(main_root, "pull", "--ff-only", "origin", "main")
    if pull.returncode != 0:
        # Still on main; behind is acceptable for orientation.
        return True, f"on main (ff-only pull skipped: {pull.stderr.strip() or 'not possible'})"
    return True, "on main and fast-forwarded to origin/main"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cwd",
        type=Path,
        default=None,
        help="Starting directory for repo discovery (default: process cwd)",
    )
    parser.add_argument(
        "--heal",
        action="store_true",
        help="If primary is detached/wrong-branch, checkout main (+ optional ff-only)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="No stdout on success",
    )
    args = parser.parse_args(argv)

    state = primary_head_state(args.cwd)
    if state.get("ok"):
        if not args.quiet:
            print(f"OK primary on {state.get('branch', 'n/a')} ({state.get('path')})")
        return 0

    msg = str(state.get("message") or state.get("reason"))
    print(f"ERROR: {msg}", file=sys.stderr)

    if not args.heal:
        print(
            "Fix: cd <primary> && git checkout main && git pull --ff-only origin main\n"
            "Or:  .venv/bin/python scripts/guardrails/assert_primary_on_main.py --heal",
            file=sys.stderr,
        )
        return 1

    main_root = Path(str(state["path"]))
    ok, detail = heal_primary_to_main(main_root)
    if not ok:
        print(f"HEAL FAILED: {detail}", file=sys.stderr)
        return 1
    print(f"HEALED: {detail}")
    # Re-check
    again = primary_head_state(main_root)
    if not again.get("ok"):
        print(f"ERROR after heal: {again.get('message')}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
