"""Hold or lift a SQLite database and its existing companion files together.

Callers must quiesce database clients and prevent concurrent file creation,
replacement, or removal. POSIX has no atomic multi-file chmod: these operations
restore original modes on failure, but cannot survive a process crash atomically.
Existing SQLite connections can retain writable descriptors after a hold; reopen
connections after changing permissions. Privileged users can bypass mode bits.
"""

from __future__ import annotations

import os
import stat
from contextlib import ExitStack
from pathlib import Path

_SUFFIXES = ("-wal", "-shm", "-journal")


def get_companion_paths(db_path: Path | str) -> list[Path]:
    """Return existing WAL, shared-memory, and rollback-journal paths, in order."""
    companions = []
    for suffix in _SUFFIXES:
        path = Path(f"{db_path}{suffix}")
        try:
            path.lstat()
        except FileNotFoundError:
            continue
        companions.append(path)
    return companions


def _set_permissions(db_path: Path | str, mode: int, *, strict: bool) -> list[Path]:
    paths = [Path(db_path), *get_companion_paths(db_path)]
    with ExitStack() as stack:
        targets = []
        for path in paths:
            try:
                fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            except FileNotFoundError:
                if strict:
                    raise
                continue
            stack.callback(os.close, fd)
            metadata = os.fstat(fd)
            if not stat.S_ISREG(metadata.st_mode):
                raise OSError(f"Not a regular database component: {path}")
            targets.append((path, fd, stat.S_IMODE(metadata.st_mode)))

        changed = []
        try:
            for path, fd, original in targets:
                os.fchmod(fd, mode)
                changed.append((path, fd, original))
        except OSError as error:
            failures = []
            for path, fd, original in reversed(changed):
                try:
                    os.fchmod(fd, original)
                except OSError as rollback_error:
                    rollback_error.add_note(f"Could not restore permissions: {path}")
                    failures.append(rollback_error)
            if failures:
                raise ExceptionGroup("Permission change and rollback failed", [error, *failures]) from error
            raise
    return [path for path, _, _ in changed]


def hold_database(db_path: Path | str, *, strict: bool = True) -> list[Path]:
    """Set db and existing companions to 0444; return the affected paths.

    Missing companions are optional. With strict=True a missing database or a
    discovered component disappearing raises FileNotFoundError before any chmod.
    strict=False skips missing paths; other errors always raise and roll back.
    Symlinks and non-regular files are refused before any chmod.
    """
    return _set_permissions(db_path, 0o444, strict=strict)


def lift_database(db_path: Path | str, *, strict: bool = True) -> list[Path]:
    """Set db and existing companions to 0644; use hold_database's strict policy."""
    return _set_permissions(db_path, 0o644, strict=strict)


def inspect_database_permissions(db_path: Path | str) -> dict[str, int | None]:
    """Map the db and all three companion path strings to modes, or None if absent.

    Symlinks are inspected without following them. Other stat errors propagate.
    """
    modes = {}
    for path in [Path(db_path), *(Path(f"{db_path}{suffix}") for suffix in _SUFFIXES)]:
        try:
            modes[str(path)] = stat.S_IMODE(path.lstat().st_mode)
        except FileNotFoundError:
            modes[str(path)] = None
    return modes
