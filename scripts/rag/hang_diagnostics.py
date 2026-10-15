"""All-thread stack dump when systemd's watchdog aborts the sources server (#10674).

``learn-ukrainian-sources.service`` keeps the default ``WatchdogSignal=SIGABRT``
and creates its owner-only state directory (``StateDirectory=``, mode 0700).
At start-up the standalone server calls :func:`arm_abort_dump`, which:

- opens that directory once, without following a symlink, and refuses it
  unless it is owned by this user and closed to group and others;
- prunes earlier processes' dump files through that descriptor (below);
- creates this process's dump file there (0600, new name, ``O_EXCL``), takes
  an exclusive ``flock`` on it for the process's lifetime, and hands the
  open descriptor to ``faulthandler.enable(all_threads=True)``.

On SIGABRT (and the other fatal signals) faulthandler writes every thread's
stack to that descriptor and lets the signal kill the process. Nothing is
opened by path at crash time. ``faulthandler.register`` cannot take SIGABRT;
``enable`` is the supported route.

Retention. Every process creates one file and a fatal signal ends the
process, so each file holds at most one dump, and faulthandler caps a dump
at 100 threads of 100 frames with names cut at 500 characters
(``MAX_DUMP_BYTES``, 11 MiB, is above that ceiling). At start-up the server
removes earlier empty files, then keeps the newest earlier dumps up to
``keep - 1`` files and ``max_bytes - MAX_DUMP_BYTES`` bytes, leaving room
for its own file. The directory therefore never holds more than ``keep``
dump files or ``max_bytes`` bytes of dumps. A file whose ``flock`` cannot
be taken belongs to a live process and is never touched; a symlink is
never followed or removed.

Privacy. Stacks carry file names, line numbers and function names, never
argument values. The process also turns off core dumps (``RLIMIT_CORE`` 0
and ``PR_SET_DUMPABLE`` 0, which stops a piped ``core_pattern`` helper as
well), so memory never leaves the process.

The same descriptor serves :func:`write_ready_marker`: the invocation that
reached readiness, which the failure notice uses to tell a start-up failure
from a later one.
"""

from __future__ import annotations

import contextlib
import ctypes
import faulthandler
import fcntl
import os
import re
import resource
import secrets
import stat
import sys
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import IO

STATE_DIRECTORY_ENV = "STATE_DIRECTORY"
DUMP_PREFIX = "abort-"
DUMP_SUFFIX = ".txt"
DEFAULT_KEEP_DUMPS = 8
DEFAULT_MAX_DUMP_BYTES = 32 * 1024 * 1024
# Above one faulthandler dump's ceiling: 100 threads x 100 frames x two
# 500-character names per frame line, plus headers (about 10.5 MB).
MAX_DUMP_BYTES = 11 * 1024 * 1024
READY_MARKER = "ready-invocation"
_INVOCATION = re.compile(r"[0-9a-f]{32}")
_PR_SET_DUMPABLE = 4

# The armed dump file and the state directory stay open for the process's
# lifetime: faulthandler writes to the descriptor, and the flock marks the
# file as live.
_DUMP_FILE: IO[str] | None = None
_STATE_DIR_FD: int | None = None


class StateDirectoryError(RuntimeError):
    """The state directory is missing, not a directory, or not private."""


def open_state_dir(path: str) -> int:
    """Open ``path`` as a private directory and return its descriptor."""
    try:
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    except OSError as error:
        raise StateDirectoryError(f"cannot open the state directory: {type(error).__name__}") from None
    info = os.fstat(fd)
    if info.st_uid != os.getuid() or info.st_mode & 0o077:
        os.close(fd)
        raise StateDirectoryError("the state directory is not owner-only")
    return fd


def _dump_name(now: datetime, pid: int) -> str:
    return f"{DUMP_PREFIX}{now:%Y%m%dT%H%M%SZ}-pid{pid}-{secrets.token_hex(4)}{DUMP_SUFFIX}"


def prune_dumps(dir_fd: int, *, keep: int, max_bytes: int) -> list[str]:
    """Bound earlier dump files in the directory open as ``dir_fd``; return removed names.

    Removes empty files, then keeps the newest non-empty ones while at most
    ``keep`` files and ``max_bytes`` bytes. Only regular files whose
    ``flock`` this call holds are candidates, so a live process's file is
    never removed; a name is unlinked only while it still names the locked
    file.
    """
    held: list[tuple[str, int, os.stat_result]] = []
    try:
        for name in os.listdir(dir_fd):
            if not (name.startswith(DUMP_PREFIX) and name.endswith(DUMP_SUFFIX)):
                continue
            try:
                fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=dir_fd)
            except OSError:
                continue  # a symlink (ELOOP), or gone since the listing
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode):
                os.close(fd)
                continue
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                os.close(fd)
                continue  # held by a live process
            held.append((name, fd, info))
        # Names carry a UTC stamp, so name order is age order; newest first.
        held.sort(key=lambda entry: entry[0], reverse=True)
        kept = total = 0
        doomed: list[tuple[str, os.stat_result]] = []
        for name, _fd, info in held:
            if info.st_size and kept < keep and total + info.st_size <= max_bytes:
                kept += 1
                total += info.st_size
            else:
                doomed.append((name, info))
        removed = []
        for name, info in doomed:
            with contextlib.suppress(OSError):
                current = os.stat(name, dir_fd=dir_fd, follow_symlinks=False)
                if (current.st_dev, current.st_ino) == (info.st_dev, info.st_ino):
                    os.unlink(name, dir_fd=dir_fd)
                    removed.append(name)
        return removed
    finally:
        for _name, fd, _info in held:
            os.close(fd)


def _disable_core_dumps() -> None:
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    if sys.platform.startswith("linux"):
        libc = ctypes.CDLL(None, use_errno=True)
        if libc.prctl(_PR_SET_DUMPABLE, 0, 0, 0, 0) != 0:
            raise OSError(ctypes.get_errno(), "prctl(PR_SET_DUMPABLE) failed")


def arm_abort_dump(
    environ: Mapping[str, str] | None = None,
    *,
    keep: int = DEFAULT_KEEP_DUMPS,
    max_bytes: int = DEFAULT_MAX_DUMP_BYTES,
    now: datetime | None = None,
) -> str | None:
    """Arm the all-thread dump in the unit's state directory; return the file name.

    Returns None, changing nothing, when ``$STATE_DIRECTORY`` is unset (the
    server is not running under the unit). Raises
    :class:`StateDirectoryError` for a directory that is not private.
    """
    global _DUMP_FILE, _STATE_DIR_FD
    environ = os.environ if environ is None else environ
    directory = environ.get(STATE_DIRECTORY_ENV, "").split(":")[0]
    if not directory:
        return None
    dir_fd = open_state_dir(directory)
    try:
        prune_dumps(dir_fd, keep=max(0, keep - 1), max_bytes=max_bytes - MAX_DUMP_BYTES)
        name = _dump_name(now or datetime.now(UTC), os.getpid())
        fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=dir_fd)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        handle = os.fdopen(fd, "w", encoding="utf-8")
    except BaseException:
        os.close(dir_fd)
        raise
    _disable_core_dumps()
    faulthandler.enable(file=handle, all_threads=True)
    _DUMP_FILE = handle
    _STATE_DIR_FD = dir_fd
    return name


def write_ready_marker(environ: Mapping[str, str] | None = None) -> bool:
    """Record this unit invocation as having reached readiness; False when not armed."""
    environ = os.environ if environ is None else environ
    invocation = environ.get("INVOCATION_ID", "")
    if _STATE_DIR_FD is None or not _INVOCATION.fullmatch(invocation):
        return False
    temporary = f".{READY_MARKER}-{secrets.token_hex(4)}"
    try:
        fd = os.open(
            temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=_STATE_DIR_FD
        )
        with os.fdopen(fd, "w", encoding="ascii") as handle:
            handle.write(invocation + "\n")
        os.replace(temporary, READY_MARKER, src_dir_fd=_STATE_DIR_FD, dst_dir_fd=_STATE_DIR_FD)
    except OSError:
        with contextlib.suppress(OSError):
            os.unlink(temporary, dir_fd=_STATE_DIR_FD)
        return False
    return True


def read_ready_marker(dir_fd: int) -> str | None:
    """The invocation id in the ready marker of the directory open as ``dir_fd``, if valid."""
    try:
        fd = os.open(READY_MARKER, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=dir_fd)
    except OSError:
        return None
    with os.fdopen(fd, "rb") as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            return None
        text = handle.read(64).decode("ascii", "replace").strip()
    return text if _INVOCATION.fullmatch(text) else None
