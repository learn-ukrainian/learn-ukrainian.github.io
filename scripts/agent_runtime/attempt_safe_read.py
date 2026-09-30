"""Bounded parent reads of seat-controlled files, with no isolation dependencies."""

from __future__ import annotations

import contextlib
import os
import stat
from pathlib import Path

# Bound bytes consumed by a parent read, including resumed suffixes.
MAX_ATTEMPT_READ_BYTES = 64 * 1024 * 1024


class AttemptReadError(RuntimeError):
    """Body-free refusal of a parent read of a seat-controlled file."""


@contextlib.contextmanager
def _checked_attempt_fd(path: Path, trusted_root: Path):
    """Walk beneath a parent-owned root resolved before launching the seat.

    Ancestors above that root are trusted; root and every component beneath it
    are opened with NOFOLLOW. Never resolve a seat-controlled path at read time.
    """
    path = path.absolute()
    if (
        not trusted_root.is_absolute() or ".." in path.parts or ".." in trusted_root.parts
        or not path.is_relative_to(trusted_root) or path == trusted_root
    ):
        raise AttemptReadError("attempt_read_outside_root")
    directory = file_fd = None
    try:
        flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
        directory = os.open(trusted_root, flags | os.O_DIRECTORY)
        for component in path.relative_to(trusted_root).parts[:-1]:
            child = os.open(component, flags | os.O_DIRECTORY, dir_fd=directory)
            os.close(directory)
            directory = child
        file_fd = os.open(path.name, flags | os.O_NONBLOCK | os.O_NOCTTY, dir_fd=directory)
        _check_attempt_fd(file_fd)
        yield file_fd
        _check_attempt_fd(file_fd)
    except FileNotFoundError:
        raise
    except OSError as exc:
        raise AttemptReadError("attempt_read_unsafe_path") from exc
    finally:
        if file_fd is not None:
            os.close(file_fd)
        if directory is not None:
            os.close(directory)


def _check_attempt_fd(file_fd: int) -> os.stat_result:
    info = os.fstat(file_fd)
    if not stat.S_ISREG(info.st_mode):
        raise AttemptReadError("attempt_read_not_regular")
    if info.st_uid != os.getuid():
        raise AttemptReadError("attempt_read_wrong_owner")
    if info.st_nlink != 1:
        raise AttemptReadError("attempt_read_link_count")
    return info


def safe_attempt_file_size(path: Path, *, trusted_root: Path = Path("/")) -> int:
    """Size a checked regular fd without reading its contents."""
    with _checked_attempt_fd(path, trusted_root) as file_fd:
        return _check_attempt_fd(file_fd).st_size


def safe_read_attempt_file(
    path: Path,
    *,
    trusted_root: Path = Path("/"),
    max_bytes: int = MAX_ATTEMPT_READ_BYTES,
    offset: int = 0,
    prefix: bool = False,
    tail: bool = False,
) -> bytes:
    """Read a bounded full file, suffix, prefix or tail from one checked fd.

    Full/suffix reads refuse overflow; prefix/tail reads intentionally stop at
    the byte bound. NONBLOCK avoids hanging on a substituted FIFO. Missing
    optional files keep FileNotFoundError; refusals contain no path or data.
    """
    if max_bytes < 0 or offset < 0 or (tail and (offset or prefix)):
        raise AttemptReadError("attempt_read_invalid_bound")
    with _checked_attempt_fd(path, trusted_root) as file_fd:
        size = _check_attempt_fd(file_fd).st_size
        if tail:
            offset = max(0, size - max_bytes)
        if offset > size:
            raise AttemptReadError("attempt_read_invalid_offset")
        limited = prefix or tail
        if not limited and size - offset > max_bytes:
            raise AttemptReadError("attempt_read_oversized")
        os.lseek(file_fd, offset, os.SEEK_SET)
        chunks: list[bytes] = []
        remaining = max_bytes if limited else max_bytes + 1
        while remaining:
            chunk = os.read(file_fd, min(remaining, 65536))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        if not limited and (remaining == 0 or _check_attempt_fd(file_fd).st_size - offset > max_bytes):
            raise AttemptReadError("attempt_read_oversized")
        return b"".join(chunks)
