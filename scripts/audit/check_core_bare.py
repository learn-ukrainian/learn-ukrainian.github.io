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
import os
import subprocess
import sys
from pathlib import Path

# Git commit hooks inject GIT_DIR / GIT_INDEX_FILE / etc. into the environment.
# Config checks must not inherit those or they inspect the outer repo, not the
# fixture / --repo path under test.
_GIT_REDIRECT_KEYS = frozenset(
    {
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_COMMON_DIR",
        "GIT_PREFIX",
        "GIT_NAMESPACE",
    }
)


def _clean_git_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k not in _GIT_REDIRECT_KEYS}


def _git_config_cmd_prefix(repo: Path) -> list[str]:
    """Build a git prefix that can read/write config even when core.bare=true.

    Prefer ``--git-dir=<repo>/.git`` (normal checkout). Fall back to bare-root
    ``--git-dir=<repo>`` or ``-C <repo>``.
    """
    git_path = repo / ".git"
    if git_path.is_file():
        text = git_path.read_text(encoding="utf-8").strip()
        if text.startswith("gitdir:"):
            target = Path(text.split(":", 1)[1].strip())
            if not target.is_absolute():
                target = (repo / target).resolve()
            return ["git", f"--git-dir={target}"]
    if git_path.is_dir():
        return ["git", f"--git-dir={git_path}"]
    if (repo / "HEAD").is_file() and (repo / "objects").is_dir():
        return ["git", f"--git-dir={repo}"]
    return ["git", "-C", str(repo)]


def _git_config_get(repo: Path, key: str) -> str | None:
    """Return the effective git config value for ``key``, or None if unset."""
    proc = subprocess.run(
        [*_git_config_cmd_prefix(repo), "config", "--get", key],
        capture_output=True,
        text=True,
        env=_clean_git_env(),
    )
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def _git_config_set(repo: Path, key: str, value: str) -> None:
    subprocess.run(
        [*_git_config_cmd_prefix(repo), "config", key, value],
        check=True,
        env=_clean_git_env(),
    )


def _config_file_says_bare(repo: Path) -> bool:
    """Parse ``.git/config`` directly (works when git CLI is confused)."""
    cfg = repo / ".git" / "config"
    if not cfg.is_file():
        # bare-root layout
        cfg = repo / "config"
    if not cfg.is_file():
        return False
    try:
        text = cfg.read_text(encoding="utf-8")
    except OSError:
        return False
    # crude but reliable: core.bare true in the common config file
    for line in text.splitlines():
        stripped = line.strip().lower().replace(" ", "")
        if stripped in {"bare=true", "bare=1"}:
            return True
    return False


def _is_bare_broken(repo: Path) -> bool:
    """True when primary is bare (config CLI, config file, and/or rev-parse)."""
    if _git_config_get(repo, "core.bare") == "true":
        return True
    if _config_file_says_bare(repo):
        return True
    proc = subprocess.run(
        [*_git_config_cmd_prefix(repo), "rev-parse", "--is-bare-repository"],
        capture_output=True,
        text=True,
        env=_clean_git_env(),
    )
    return proc.returncode == 0 and proc.stdout.strip().lower() == "true"


def check_core_bare(repo: Path, *, fix: bool) -> tuple[bool, str]:
    """Check ``core.bare`` on ``repo`` (layout A: bare is a bug to heal).

    Returns ``(ok, message)``. ``ok`` is True when ``core.bare`` is false/unset,
    or when it was true and ``fix`` reset it. ``ok`` is False when it is true and
    ``fix`` is not set (the repo's work tree is broken and needs repair).

    Also asserts ``extensions.worktreeConfig=true`` when ``fix`` is set so
    worktree-local config cannot re-pollute shared ``core.bare`` (#2842 / Fable A).
    """
    parts: list[str] = []
    value = _git_config_get(repo, "core.bare")
    bare_broken = _is_bare_broken(repo)
    if bare_broken:
        if not fix:
            return False, (
                "core.bare=true — primary is BROKEN (layout A: bare is a bug). "
                "Re-run with --fix (or `git config --local core.bare false`); see #2842"
            )
        _git_config_set(repo, "core.bare", "false")
        parts.append("core.bare reset true→false")
    else:
        parts.append(f"core.bare={value or 'unset'} (ok)")

    wtc = _git_config_get(repo, "extensions.worktreeConfig")
    if wtc != "true":
        if fix:
            _git_config_set(repo, "extensions.worktreeConfig", "true")
            parts.append("extensions.worktreeConfig set true")
        else:
            return False, (
                "extensions.worktreeConfig is not true — worktree config can pollute "
                "shared core.bare (#2842). Re-run with --fix."
            )
    else:
        parts.append("extensions.worktreeConfig=true (ok)")

    return True, "; ".join(parts)


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
