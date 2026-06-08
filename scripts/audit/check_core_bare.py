#!/usr/bin/env python3
"""Repo-health canary: assert (and optionally fix) git ``core.bare`` on this repo.

A stray ``git config core.bare true`` on this *working* repository silently
breaks ``git status`` / ``add`` / ``commit`` / worktree operations for the main
checkout **and every linked worktree at once** — they all read the shared
``.git/config``. The value is never pushed, so GitHub CI cannot catch it; only a
local canary can. See issue #2842.

This repo always has a working tree, so ``core.bare`` must be ``false``. If it
has drifted to ``true``, ``--fix`` resets it.

Usage::

    python scripts/audit/check_core_bare.py            # check only; exit 1 if core.bare=true
    python scripts/audit/check_core_bare.py --fix      # reset to false if drifted; exit 0
    python scripts/audit/check_core_bare.py --fix -q   # silent unless it had to fix

Runs independently of a working tree (``git config`` works even in the broken
``core.bare=true`` state), so it functions *while* the repo is broken — which is
exactly when it is needed. Wire into the SessionStart hook and/or a periodic
health check.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _git_config_get(repo: Path, key: str) -> str | None:
    """Return the effective git config value for ``key``, or None if unset."""
    proc = subprocess.run(
        ["git", "-C", str(repo), "config", "--get", key],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def check_core_bare(repo: Path, *, fix: bool) -> tuple[bool, str]:
    """Check ``core.bare`` on ``repo``.

    Returns ``(ok, message)``. ``ok`` is True when ``core.bare`` is false/unset,
    or when it was true and ``fix`` reset it. ``ok`` is False when it is true and
    ``fix`` is not set (the repo's work tree is broken and needs repair).
    """
    value = _git_config_get(repo, "core.bare")
    if value != "true":
        return True, f"core.bare={value or 'unset'} (ok)"
    if not fix:
        return False, (
            "core.bare=true — every git work tree on this repo is BROKEN. "
            "Re-run with --fix (or `git config --local core.bare false`); see #2842"
        )
    subprocess.run(
        ["git", "-C", str(repo), "config", "--local", "core.bare", "false"],
        check=True,
    )
    return True, "core.bare reset true→false (repo work tree was broken; see #2842)"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Assert git core.bare is false on this working repo (#2842).",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="reset core.bare to false if it has drifted to true",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="suppress the OK message (still reports a fix)",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="repo path to check (default: this project root)",
    )
    args = parser.parse_args(argv)

    ok, message = check_core_bare(args.repo, fix=args.fix)
    if not ok:
        print(f"❌ {message}", file=sys.stderr)
        return 1
    # Always surface an actual fix; suppress the routine OK under --quiet.
    if "reset" in message:
        print(f"⚠️  {message}", file=sys.stderr)
    elif not args.quiet:
        print(f"✅ {message}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
