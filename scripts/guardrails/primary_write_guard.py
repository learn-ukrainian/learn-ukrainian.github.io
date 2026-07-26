#!/usr/bin/env python3
"""Primary checkout write guard (issue #5389).

Ensures that agents cannot write to tracked files in the primary checkout.
"""

from __future__ import annotations

import argparse
import os
import stat
import subprocess
import sys
from pathlib import Path

# Dual-flavor import support
try:
    from scripts.guardrails import worktree_containment as wc
except ImportError:
    try:
        import worktree_containment as wc  # type: ignore[import-not-found]
    except ImportError:
        _root = Path(__file__).resolve().parent.parent.parent
        if str(_root) not in sys.path:
            sys.path.insert(0, str(_root))
        from scripts.guardrails import worktree_containment as wc

# Dual-flavor git environment sanitizer import
try:
    from scripts.common.git_context import sanitized_git_env
except ImportError:
    try:
        from common.git_context import sanitized_git_env  # type: ignore[import-not-found]
    except ImportError:
        def sanitized_git_env() -> dict[str, str]:
            # Mirror of scripts.common.git_context.GIT_REDIRECT_ENV_KEYS — keep in sync.
            _GIT_ENV = {
                "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX",
                "GIT_COMMON_DIR", "GIT_OBJECT_DIRECTORY",
                "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_NAMESPACE",
                "GIT_CEILING_DIRECTORIES", "GIT_DISCOVERY_ACROSS_FILESYSTEM",
            }
            return {k: v for k, v in os.environ.items() if k not in _GIT_ENV}


def check_primary_checkout_root(hook_mode: bool = False) -> Path:
    """Verify that we are executing from the root of the primary checkout."""
    try:
        main_root = wc.resolve_main_root()
    except Exception as e:
        if hook_mode:
            sys.exit(0)
        print(f"Error: Not inside a git repository: {e}", file=sys.stderr)
        sys.exit(1)

    cwd = Path.cwd().resolve()
    if cwd != main_root:
        if hook_mode:
            sys.exit(0)
        print(
            f"Error: Must be run from the primary checkout root ({main_root}), current cwd is ({cwd})",
            file=sys.stderr,
        )
        sys.exit(1)

    path_class = wc.classify_repo_path(cwd)
    if path_class != "primary_checkout":
        if hook_mode:
            sys.exit(0)
        print(
            f"Error: Refusing to run inside a worktree (classification: {path_class})",
            file=sys.stderr,
        )
        sys.exit(1)

    return main_root


def get_writable_tracked_files(main_root: Path) -> list[Path]:
    """Get all regular tracked files in the repository that have write permissions."""
    try:
        proc = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=str(main_root),
            capture_output=True,
            text=True,
            check=True,
            env=sanitized_git_env(),
        )
    except subprocess.CalledProcessError as e:
        print(f"Error listing tracked files: {e}", file=sys.stderr)
        sys.exit(1)

    tracked_files = proc.stdout.split("\0")
    if tracked_files and not tracked_files[-1]:
        tracked_files.pop()

    writable_files = []
    for rel_path_str in tracked_files:
        if not rel_path_str:
            continue
        file_path = main_root / rel_path_str
        try:
            st = file_path.lstat()
            # Must be a regular file, NOT a directory, NOT a symlink, and must have write permission (u, g, or o)
            if stat.S_ISREG(st.st_mode) and not stat.S_ISLNK(st.st_mode) and (st.st_mode & 0o222):
                writable_files.append(file_path)
        except OSError:
            # File might not exist (e.g. deleted or sparse checkout) or permission error
            continue

    return writable_files


def apply_guard(hook_mode: bool = False) -> None:
    """Make all tracked files read-only (chmod a-w).

    Note the deliberate asymmetry with :func:`release_guard`: apply strips ALL
    write bits (u,g,o), release restores only the owner bit (u+w). A file that
    was group-writable before the first apply stays group-read-only after a
    release — accepted metadata loss; only the owner needs write access here.
    """
    main_root = check_primary_checkout_root(hook_mode=hook_mode)

    try:
        proc = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=str(main_root),
            capture_output=True,
            text=True,
            check=True,
            env=sanitized_git_env(),
        )
    except subprocess.CalledProcessError as e:
        print(f"Error listing tracked files: {e}", file=sys.stderr)
        sys.exit(1)

    tracked_files = proc.stdout.split("\0")
    if tracked_files and not tracked_files[-1]:
        tracked_files.pop()

    chmod_count = 0
    for rel_path_str in tracked_files:
        if not rel_path_str:
            continue
        file_path = main_root / rel_path_str
        try:
            st = file_path.lstat()
            if stat.S_ISREG(st.st_mode) and not stat.S_ISLNK(st.st_mode):
                current_mode = st.st_mode
                new_mode = current_mode & ~0o222
                if current_mode != new_mode:
                    os.chmod(file_path, new_mode)
                    chmod_count += 1
        except OSError:
            continue

    if not hook_mode:
        print(f"Guard applied: {chmod_count} tracked files made read-only.")


def release_guard() -> None:
    """Restore write permission on tracked files (chmod u+w only — see apply_guard docstring)."""
    main_root = check_primary_checkout_root(hook_mode=False)

    try:
        proc = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=str(main_root),
            capture_output=True,
            text=True,
            check=True,
            env=sanitized_git_env(),
        )
    except subprocess.CalledProcessError as e:
        print(f"Error listing tracked files: {e}", file=sys.stderr)
        sys.exit(1)

    tracked_files = proc.stdout.split("\0")
    if tracked_files and not tracked_files[-1]:
        tracked_files.pop()

    chmod_count = 0
    for rel_path_str in tracked_files:
        if not rel_path_str:
            continue
        file_path = main_root / rel_path_str
        try:
            st = file_path.lstat()
            if stat.S_ISREG(st.st_mode) and not stat.S_ISLNK(st.st_mode):
                current_mode = st.st_mode
                new_mode = current_mode | 0o200
                if current_mode != new_mode:
                    os.chmod(file_path, new_mode)
                    chmod_count += 1
        except OSError:
            continue

    print(f"Guard released: restored write permissions on {chmod_count} tracked files.")
    print("⚠️  LOUD REMINDER: Please remember to re-apply the write guard with 'apply' before dispatching agents!")


def status_guard() -> None:
    """Report whether the write guard is ON or OFF, plus offender count."""
    try:
        main_root = wc.resolve_main_root()
    except Exception as e:
        print(f"Error: Not inside a git repository: {e}", file=sys.stderr)
        sys.exit(1)

    writable = get_writable_tracked_files(main_root)
    state = "ON" if not writable else "OFF"
    print(f"{state} ({len(writable)} writable tracked files)")


def check_guard() -> None:
    """Exit non-zero and name offenders if guard is expected ON but writable files exist."""
    try:
        main_root = wc.resolve_main_root()
    except Exception as e:
        print(f"Error: Not inside a git repository: {e}", file=sys.stderr)
        sys.exit(1)

    writable = get_writable_tracked_files(main_root)
    if writable:
        print("Error: Primary write guard is OFF (writable tracked files exist).", file=sys.stderr)
        print("Offending writable tracked files:", file=sys.stderr)
        for f in writable:
            print(f"  {f.relative_to(main_root)}", file=sys.stderr)
        sys.exit(1)
    else:
        print("Primary write guard is ON. No writable tracked files.")
        sys.exit(0)


def install_hooks() -> None:
    """Delegate hook installation to the repository's tracked hook installer."""
    main_root = check_primary_checkout_root(hook_mode=False)
    installer = main_root / "scripts" / "install_git_hooks.sh"
    if not installer.is_file():
        print(f"Tracked Git hook installer not found at {installer}", file=sys.stderr)
        sys.exit(1)
    try:
        subprocess.run(
            ["bash", str(installer)],
            cwd=main_root,
            check=True,
            env=sanitized_git_env(),
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"Failed to install tracked Git hooks: {exc}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Primary Checkout Write Guard")
    subparsers = parser.add_subparsers(dest="command", required=True)

    apply_parser = subparsers.add_parser("apply", help="Make tracked files read-only")
    apply_parser.add_argument(
        "--hook",
        action="store_true",
        help="Run in hook mode (graceful exit on worktree or non-root cwd)",
    )

    subparsers.add_parser("release", help="Restore write permissions on tracked files")
    subparsers.add_parser("status", help="Report status of the write guard")
    subparsers.add_parser("check", help="Verify write guard is ON and exit non-zero if not")
    subparsers.add_parser("install-hooks", help="Install primary write guard into local git hooks")

    args = parser.parse_args()

    if args.command == "apply":
        apply_guard(hook_mode=args.hook)
    elif args.command == "release":
        release_guard()
    elif args.command == "status":
        status_guard()
    elif args.command == "check":
        check_guard()
    elif args.command == "install-hooks":
        install_hooks()


if __name__ == "__main__":
    main()
