#!/usr/bin/env python3
"""No-follow, atomic context-tier claims (#9791); standard library only.

The project directory is the trusted root. All runtime components below it
are opened relative to directory descriptors, never resolved through links.
The persistent lock inode is never unlinked: flock releases on process death,
so recovery needs neither PID checks nor stealing a live holder's lock.
"""

from __future__ import annotations

import contextlib
import fcntl
import os
import secrets
import stat
import sys
import time


def open_state_dir(project: str, *, create: bool) -> int:
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fd = os.open(project, flags)
    try:
        for name in ("batch_state", "context_monitor"):
            if create:
                with contextlib.suppress(FileExistsError):
                    os.mkdir(name, 0o700, dir_fd=fd)
            child = os.open(name, flags, dir_fd=fd)
            os.close(fd)
            fd = child
        return fd
    except BaseException:
        os.close(fd)
        raise


def require_regular(fd: int) -> None:
    info = os.fstat(fd)
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise ValueError("state must be a regular file with one link")


def read_state(directory: int, name: str) -> tuple[int, int]:
    try:
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    except FileNotFoundError:
        return 0, 0
    try:
        require_regular(fd)
        raw = os.read(fd, 128)
    finally:
        os.close(fd)
    try:
        tier, tokens = map(int, raw.split())
        return (tier, tokens) if 0 <= tier <= 3 and tokens >= 0 else (0, 0)
    except ValueError:
        return 0, 0


def lock_session(directory: int, name: str) -> int:
    flags = os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK
    try:
        fd = os.open(name, flags | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=directory)
    except FileExistsError:
        fd = os.open(name, flags, dir_fd=directory)
    try:
        require_regular(fd)
        deadline = time.monotonic() + 5
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise TimeoutError("live holder still owns the lock") from None
                time.sleep(0.01)
        # Refuse a replaced lock name rather than operate under a split lock.
        opened = os.fstat(fd)
        named = os.stat(name, dir_fd=directory, follow_symlinks=False)
        if (opened.st_dev, opened.st_ino) != (named.st_dev, named.st_ino):
            raise ValueError("lock name changed")
        return fd
    except BaseException:
        os.close(fd)
        raise


def replace_state(directory: int, name: str, tier: int, tokens: int) -> None:
    temporary = f".{name}.{secrets.token_hex(16)}.tmp"
    fd = os.open(
        temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
        0o600, dir_fd=directory,
    )
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(f"{tier} {tokens}\n".encode("ascii"))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, name, src_dir_fd=directory, dst_dir_fd=directory)
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(temporary, dir_fd=directory)


def claim(directory: int, session: str, tier: int, tokens: int) -> bool:
    lock = lock_session(directory, f"{session}.lock")
    try:
        name = f"{session}.tier"
        last_tier, last_tokens = read_state(directory, name)
        if last_tier > 0 and tokens * 100 < last_tokens * 60:
            os.unlink(name, dir_fd=directory)
            last_tier = 0
        if tier <= last_tier:
            return False
        replace_state(directory, name, tier, tokens)
        return True
    finally:
        os.close(lock)


def main(argv: list[str]) -> int:
    # Every refused/unsupported operation fails open for the hook/session,
    # with no claim output. Never announce unless the state commit succeeded.
    try:
        operation, project, session, *values = argv
        if not session or "/" in session or ".." in session or "\x00" in session:
            return 0
        if operation not in ("claim", "read"):
            return 0
        tier, tokens = (0, 0)
        if operation == "claim":
            tier, tokens = map(int, values)
            if not 0 <= tier <= 3 or tokens <= 0:
                return 0
        directory = open_state_dir(project, create=operation == "claim")
        try:
            if operation == "read":
                tier, tokens = read_state(directory, f"{session}.tier")
                print(tier, tokens)
            elif claim(directory, session, tier, tokens):
                print("claimed")
        finally:
            os.close(directory)
    except (OSError, ValueError, NotImplementedError):
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
