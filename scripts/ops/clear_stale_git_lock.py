"""Inspect and, with explicit approval, remove an abandoned Git lock (#8887)."""

from __future__ import annotations

import argparse
import os
import stat
import subprocess
import sys
import time
from pathlib import Path

import psutil

MIN_AGE_SECONDS = 600


def _git_dirs(repo: Path) -> tuple[Path, Path]:
    result = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--show-toplevel", "--absolute-git-dir"],
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    )
    root, admin = result.stdout.splitlines()
    return Path(root).resolve(), Path(admin).resolve()


def _within(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def _git_process_for_repo(repo: Path, admin: Path) -> bool:
    """Fail closed if a Git process cannot be inspected or targets this checkout."""
    for proc in psutil.process_iter():
        try:
            name = proc.name().lower()
            if name != "git" and not name.startswith("git-"):
                continue
            argv = proc.cmdline()
            cwd = Path(proc.cwd()).resolve()
            env = proc.environ()
        except (psutil.NoSuchProcess, psutil.ZombieProcess):
            continue
        except (psutil.AccessDenied, OSError):
            return True
        if _within(cwd, repo) or _within(cwd, admin):
            return True
        for index, arg in enumerate(argv):
            if arg == "-C" and index + 1 < len(argv):
                if _within((cwd / argv[index + 1]).resolve(), repo):
                    return True
            elif arg.startswith("-C") and len(arg) > 2:
                if _within((cwd / arg[2:]).resolve(), repo):
                    return True
            elif arg == "--git-dir" and index + 1 < len(argv):
                if (cwd / argv[index + 1]).resolve() == admin:
                    return True
            elif arg.startswith("--git-dir=") and (cwd / arg.partition("=")[2]).resolve() == admin:
                return True
        git_dir = env.get("GIT_DIR")
        if git_dir and (cwd / git_dir).resolve() == admin:
            return True
        work_tree = env.get("GIT_WORK_TREE")
        if work_tree and _within((cwd / work_tree).resolve(), repo):
            return True
    return False


def _lock_stat(admin: Path, name: str) -> os.stat_result:
    if Path(name).name != name or not name.endswith(".lock") or name == ".lock":
        raise ValueError("--lock must be a .lock basename inside the repository Git directory")
    lock = admin / name
    info = lock.lstat()
    if not stat.S_ISREG(info.st_mode):
        raise ValueError("lock is not a regular file")
    age = time.time() - info.st_mtime
    if age < MIN_AGE_SECONDS:
        raise ValueError("lock is younger than 10 minutes or changed within 10 minutes")
    return info


def clear_lock(repo: Path, name: str = "index.lock", *, apply: bool = False) -> str:
    root, admin = _git_dirs(repo)
    before = _lock_stat(admin, name)
    if _git_process_for_repo(root, admin):
        raise ValueError("a Git process for this repository is running or cannot be inspected")
    if not apply:
        return f"DRY RUN: eligible stale Git lock {admin / name} (size={before.st_size})"
    # Check the name and inode again immediately before unlinking. A new lock
    # replacing the old one must never be removed under the old eligibility proof.
    current = _lock_stat(admin, name)

    def identity(info: os.stat_result) -> tuple[int, int, int, int, int]:
        return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns

    if identity(current) != identity(before):
        raise ValueError("lock changed during inspection")
    if _git_process_for_repo(root, admin):
        raise ValueError("a Git process appeared during inspection")
    (admin / name).unlink()
    return f"REMOVED: stale Git lock {admin / name} (size={before.st_size})"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect an old Git lock and optionally remove it. "
            "Use only after a Git command reports a stale lock; never schedule automatic removal."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.ops.clear_stale_git_lock --repo . --dry-run\n"
            "  .venv/bin/python -m scripts.ops.clear_stale_git_lock --repo . --apply\n\n"
            "Outputs: inspection/removal receipt to stdout; --apply removes one Git lock.\n"
            "Exit codes: 0 eligible or removed; 1 unsafe or failed.\n"
            "Related: docs/runbooks/clear-stale-git-lock.md; issues #8887 and #8874."
        ),
    )
    parser.add_argument("--repo", type=Path, required=True, help="Checkout to inspect, for example .")
    parser.add_argument("--lock", default="index.lock", help="Git-directory .lock basename; default: index.lock")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Inspect only (the default); write nothing")
    mode.add_argument("--apply", action="store_true", help="Remove the eligible lock after another safety check")
    args = parser.parse_args(argv)
    try:
        print(clear_lock(args.repo, args.lock, apply=args.apply), flush=True)
    except (ValueError, FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr, flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
