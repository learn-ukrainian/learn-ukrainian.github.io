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
            _GIT_ENV = {
                "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
                "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_NAMESPACE", "GIT_CEILING_DIRECTORIES",
                "GIT_DISCOVERY_ACROSS_FILESYSTEM", "GIT_COMMON_DIR"
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
    """Make all tracked files read-only (chmod a-w)."""
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
    """Restore write permission on tracked files (chmod u+w)."""
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
    """Install the primary write guard logic into local git hooks."""
    main_root = check_primary_checkout_root(hook_mode=False)
    hooks_dir = main_root / ".git" / "hooks"

    if not hooks_dir.exists():
        try:
            hooks_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            print(f"Error creating hooks directory: {e}", file=sys.stderr)
            sys.exit(1)

    hook_names = ["post-merge", "post-checkout", "post-commit"]
    hook_command = (
        "\n# AGY_PRIMARY_WRITE_GUARD_START\n"
        'if [ -f "scripts/guardrails/primary_write_guard.py" ]; then\n'
        "    python3 scripts/guardrails/primary_write_guard.py apply --hook\n"
        "fi\n"
        "# AGY_PRIMARY_WRITE_GUARD_END\n"
    )

    for hook_name in hook_names:
        hook_path = hooks_dir / hook_name
        content = ""
        if hook_path.exists():
            try:
                content = hook_path.read_text(encoding="utf-8")
            except OSError as e:
                print(f"Error reading existing hook {hook_name}: {e}", file=sys.stderr)
                sys.exit(1)

        if "# AGY_PRIMARY_WRITE_GUARD_START" in content:
            print(f"Hook '{hook_name}' already has primary write guard installed.")
            continue

        new_content = content
        if not new_content:
            new_content = "#!/bin/sh\n"
        elif not new_content.endswith("\n"):
            new_content += "\n"

        new_content += hook_command

        try:
            hook_path.write_text(new_content, encoding="utf-8")
            current_mode = hook_path.stat().st_mode
            hook_path.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            print(f"Successfully installed primary write guard in hook '{hook_name}'.")
        except OSError as e:
            print(f"Error writing hook {hook_name}: {e}", file=sys.stderr)
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
