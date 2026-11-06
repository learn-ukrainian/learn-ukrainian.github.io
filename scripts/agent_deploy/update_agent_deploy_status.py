"""Safely persist or clear launcher deploy breadcrumbs under ``.agent``.

``.agent`` is writable runtime state. The launcher cannot write status files
there by pathname because a concurrent agent can replace that path with a
symlink after a check. Every operation below is relative to a directory opened
with ``O_NOFOLLOW | O_DIRECTORY``; temporary files and replacements use the
same held descriptor.
"""

from __future__ import annotations

import argparse
import contextlib
import os
import secrets
import sys
from datetime import UTC, datetime
from pathlib import Path

from agent_directory import open_agent_directory

STATUS_FILE = "last-deploy-status"
FAILURE_LOG = "last-deploy-failure.log"


def _write_atomically(agent_fd: int, filename: str, contents: bytes) -> None:
    """Write one breadcrumb without following a leaf or root symlink."""
    temporary = f".{filename}.{os.getpid()}.{secrets.token_hex(8)}.tmp"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    fd = os.open(temporary, flags, 0o600, dir_fd=agent_fd)
    try:
        with os.fdopen(fd, "wb") as destination:
            destination.write(contents)
            destination.flush()
            os.fsync(destination.fileno())
        os.replace(temporary, filename, src_dir_fd=agent_fd, dst_dir_fd=agent_fd)
    except BaseException:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(temporary, dir_fd=agent_fd)
        raise


def record_failure(agent_root: str, script: str, exit_code: int, failure_log: Path) -> None:
    """Store a failed deploy status and its captured log under a held root fd."""
    status = (
        "FAILED\n"
        f"script={script}\n"
        f"exit_code={exit_code}\n"
        f"when={datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')}\n"
    ).encode()
    log_contents = failure_log.read_bytes()
    agent_fd = open_agent_directory(agent_root)
    try:
        _write_atomically(agent_fd, STATUS_FILE, status)
        _write_atomically(agent_fd, FAILURE_LOG, log_contents)
    finally:
        os.close(agent_fd)


def clear_breadcrumb(agent_root: str) -> None:
    """Remove the two breadcrumb leaves without traversing their targets."""
    agent_fd = open_agent_directory(agent_root)
    try:
        for filename in (STATUS_FILE, FAILURE_LOG):
            with contextlib.suppress(FileNotFoundError):
                os.unlink(filename, dir_fd=agent_fd)
    finally:
        os.close(agent_fd)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    clear = actions.add_parser("clear")
    clear.add_argument("--agent-root", required=True)
    failure = actions.add_parser("record-failure")
    failure.add_argument("--agent-root", required=True)
    failure.add_argument("--script", required=True)
    failure.add_argument("--exit-code", required=True, type=int)
    failure.add_argument("--failure-log", required=True, type=Path)
    args = parser.parse_args(argv)

    try:
        if args.action == "clear":
            clear_breadcrumb(args.agent_root)
        else:
            record_failure(args.agent_root, args.script, args.exit_code, args.failure_log)
    except OSError as exc:
        print(f"Error: refusing .agent deploy-status update: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
