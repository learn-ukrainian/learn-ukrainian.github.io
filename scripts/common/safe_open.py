"""Open one file below a trusted directory descriptor without following, blocking or trusting it (#8652).

A directory that another user can write into (a formerly group-writable receipts root, a scoped
review home) can hold a planted symlink, FIFO, device or foreign-owned file at any name we are
about to open. A plain ``open`` follows the symlink and blocks forever on a FIFO with no peer, so
every file below the anchor goes through :func:`safe_open_below` instead.
"""

from __future__ import annotations

import errno
import os
import stat

UNSAFE_ENTRY = "a file below the trusted directory is a symlink, not a regular file, or not owned by the current user"

# ``ELOOP``: ``O_NOFOLLOW`` met a symlink. ``ENXIO``: ``O_NONBLOCK | O_WRONLY`` met a FIFO with no
# reader. ``EISDIR``/``ENOTDIR``/``ENODEV`` are other wrong types the kernel refuses for us.
_WRONG_TYPE_ERRNOS = (errno.ELOOP, errno.ENXIO, errno.EISDIR, errno.ENOTDIR, errno.ENODEV)


class UnsafeEntryError(OSError):
    """The entry is not a regular file we own. The message is fixed wording and never names a path."""

    def __init__(self) -> None:
        super().__init__(UNSAFE_ENTRY)


def safe_open_below(dir_fd: int, name: str, flags: int, mode: int = 0o600, *, blocking: bool = True) -> int:
    """Open ``name`` relative to ``dir_fd`` and return an fd that is provably a regular file we own.

    ``flags`` is the caller's access mode plus any ``O_CREAT``/``O_EXCL``/``O_APPEND``/``O_TRUNC``. The
    open always adds ``O_NOFOLLOW | O_NONBLOCK | O_CLOEXEC``, so a planted symlink is refused and a
    planted FIFO can never make the open wait. The result is then ``fstat``-ed (on the descriptor, so
    the answer describes the very file that will be used) and anything that is not a regular file
    owned by the current user is closed and refused. ``O_NONBLOCK`` is cleared again unless
    ``blocking=False``, for callers that need ordinary blocking I/O.

    Errors that mean "the entry is not what we expected" raise :class:`UnsafeEntryError`; ordinary
    ones (``FileNotFoundError``, ``FileExistsError``, permissions) propagate unchanged.
    """
    try:
        fd = os.open(name, flags | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, mode, dir_fd=dir_fd)
    except OSError as exc:
        if exc.errno in _WRONG_TYPE_ERRNOS:
            raise UnsafeEntryError from None
        raise
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid():
            raise UnsafeEntryError
        if blocking:
            os.set_blocking(fd, True)
    except BaseException:
        os.close(fd)
        raise
    return fd
