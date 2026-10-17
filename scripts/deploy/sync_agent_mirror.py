"""Synchronize shared extensions into ``.agent`` without a path-swap window.

``.agent`` is mutable runtime state: other local agents can rename it or replace
it with a symlink while deploy is running.  Opening it by pathname and later
passing that pathname to rsync is therefore unsafe.  This helper opens the
directory with ``O_NOFOLLOW | O_DIRECTORY``, changes into that held descriptor,
and only then execs rsync with ``.`` as its destination.  A later rename changes
what the pathname names, but cannot change rsync's working directory.

macOS does not provide a usable ``/proc/self/fd`` path for this purpose;
``fchdir`` is the portable descriptor-bound operation used here.

Resolve the actual rsync before fchdir, then execv it (#10910). execvp submits
even nonexistent PATH candidates to Python's execution audit hooks. Deployment
owns this resolution, including its shell rsync calls: adapter-only filtering
misses PATH changes inside a worker, while shared environment filtering would
change unrelated providers and tools. Priority PATH wrappers remain supported,
but an installed Cursor target, including through aliases, is never a deploy tool.
"""

from __future__ import annotations

import argparse
import os
import shutil
import stat
import sys
from pathlib import Path

from agent_directory import open_agent_directory


def resolve_rsync() -> str:
    """Resolve one executable, refusing Cursor installation targets before any sync."""
    found = shutil.which("rsync")
    if found is None:
        raise FileNotFoundError("rsync not found on PATH; install system rsync or provide a trusted PATH wrapper")
    executable = Path(found).resolve(strict=True)
    # This path is also returned to Bash via command substitution. In
    # particular, a trailing newline would be stripped and name another file.
    if any(ord(char) < 32 or ord(char) == 127 for char in str(executable)):
        raise PermissionError("rsync target contains control characters; use a trusted executable path")
    installation = (Path.home() / ".local/share/cursor-agent").resolve()
    cli_targets = {
        Path(target).resolve(strict=True) for name in ("cursor-agent", "agent") if (target := shutil.which(name))
    }
    if executable.is_relative_to(installation) or executable in cli_targets:
        raise PermissionError(
            "rsync resolves to an installed Cursor target; put system rsync or a trusted wrapper first on PATH"
        )
    info = executable.stat()
    if (
        not stat.S_ISREG(info.st_mode)
        or not os.access(executable, os.X_OK)
        or info.st_uid not in (0, os.geteuid())
        or info.st_mode & (stat.S_IWGRP | stat.S_IWOTH)
    ):
        raise PermissionError("rsync target is not a trusted executable; check its ownership, permissions and PATH")
    return str(executable)


def sync_agent_mirror(source_root: str, agent_root: str) -> None:
    """Exec rsync into the directory represented by an open descriptor."""
    source = Path(source_root).resolve(strict=True)
    if not source.is_dir():
        raise NotADirectoryError(f"shared source is not a directory: {source}")
    executable = resolve_rsync()

    agent_fd = open_agent_directory(agent_root)
    try:
        # Python makes newly opened fds non-inheritable.  Keep this descriptor
        # open in rsync as well: that makes the held-directory lifetime explicit
        # from validation through the write, in addition to the descriptor-bound
        # working directory selected by fchdir.
        os.set_inheritable(agent_fd, True)
        os.fchdir(agent_fd)
        os.execv(executable, (executable, "-av", f"{source}/", "."))
    finally:
        # execv never returns on success. Close only on an fchdir/exec failure.
        os.close(agent_fd)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Synchronize shared extensions into a descriptor-bound .agent directory.\n"
        "Used by deploy_prompts.sh; --resolve-rsync only validates the tool, without syncing.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
        "  .venv/bin/python scripts/deploy/sync_agent_mirror.py --resolve-rsync\n"
        "  .venv/bin/python scripts/deploy/sync_agent_mirror.py "
        "--source-root agents_extensions/shared --agent-root .agent\n"
        "Outputs: validated executable on stdout, or shared files copied into .agent.\n"
        "Exit codes: 0 success; 1 unsafe/missing tool or sync failure; 2 invalid arguments.\n"
        "Related: scripts/deploy_prompts.sh; #10910.",
    )
    parser.add_argument("--resolve-rsync", action="store_true", help="print the validated executable for shell syncs")
    parser.add_argument(
        "--source-root", help="shared source directory, e.g. agents_extensions/shared; required for sync"
    )
    parser.add_argument("--agent-root", help="destination directory, e.g. .agent; required for sync")
    args = parser.parse_args(argv)
    if not args.resolve_rsync and (args.source_root is None or args.agent_root is None):
        parser.error("--source-root and --agent-root are required for mirror sync")

    try:
        if args.resolve_rsync:
            print(resolve_rsync())
        else:
            sync_agent_mirror(args.source_root, args.agent_root)
    except (OSError, RuntimeError) as exc:
        print(f"Error: refusing .agent mirror sync: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
