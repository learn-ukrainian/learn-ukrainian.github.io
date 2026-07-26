"""Synchronize shared extensions into ``.agent`` without a path-swap window.

``.agent`` is mutable runtime state: other local agents can rename it or replace
it with a symlink while deploy is running.  Opening it by pathname and later
passing that pathname to rsync is therefore unsafe.  This helper opens the
directory with ``O_NOFOLLOW | O_DIRECTORY``, changes into that held descriptor,
and only then execs rsync with ``.`` as its destination.  A later rename changes
what the pathname names, but cannot change rsync's working directory.

macOS does not provide a usable ``/proc/self/fd`` path for this purpose;
``fchdir`` is the portable descriptor-bound operation used here.
"""

from __future__ import annotations

import argparse
import contextlib
import os
import sys
from pathlib import Path


def _directory_flags() -> int:
    """Return flags that open a real directory without following a symlink."""
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    return flags


def open_agent_directory(agent_root: str) -> int:
    """Create (when absent) and open ``agent_root`` without following links.

    The final open is always the security boundary.  If another process creates
    or swaps the name after ``mkdir``, ``O_NOFOLLOW`` rejects a symlink and the
    descriptor returned for a directory remains bound to the opened object.
    """
    flags = _directory_flags()
    try:
        return os.open(agent_root, flags)
    except FileNotFoundError:
        with contextlib.suppress(FileExistsError):
            os.mkdir(agent_root)
        # A concurrent creator may have won the race.  The no-follow open below
        # still verifies that its entry is a real directory.
        return os.open(agent_root, flags)


def sync_agent_mirror(source_root: str, agent_root: str) -> None:
    """Exec rsync into the directory represented by an open descriptor."""
    source = Path(source_root).resolve(strict=True)
    if not source.is_dir():
        raise NotADirectoryError(f"shared source is not a directory: {source}")

    agent_fd = open_agent_directory(agent_root)
    try:
        # Python makes newly opened fds non-inheritable.  Keep this descriptor
        # open in rsync as well: that makes the held-directory lifetime explicit
        # from validation through the write, in addition to the descriptor-bound
        # working directory selected by fchdir.
        os.set_inheritable(agent_fd, True)
        os.fchdir(agent_fd)
        os.execvp("rsync", ("rsync", "-av", f"{source}/", "."))
    finally:
        # execvp never returns on success.  Close only on an fchdir/exec failure.
        os.close(agent_fd)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--agent-root", required=True)
    args = parser.parse_args(argv)

    try:
        sync_agent_mirror(args.source_root, args.agent_root)
    except OSError as exc:
        print(f"Error: refusing .agent mirror sync: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
