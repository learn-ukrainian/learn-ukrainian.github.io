"""Install systemd units, drop-ins and launchd agents without following symlinks (#9875).

A unit installer writes into a directory such as ``~/.config/systemd/user`` or
``~/Library/LaunchAgents``. If that directory, any directory between it and the
home directory, or the unit file itself is a symlink, a plain ``write_text`` or
``chmod`` lands on whatever the link points at. Every installer therefore goes
through this module:

* :func:`open_unit_dir` walks from the home directory (or ``/`` for a directory
  outside home) down to the unit directory one component at a time, refusing
  any symlink and opening each step relative to its checked parent with
  ``O_NOFOLLOW``;
* :func:`read_unit` refuses anything but a regular file at the unit name;
* :func:`write_unit` writes a private temporary file beside the unit and
  renames it into place, so a link planted at the unit name is replaced, never
  written through.

:func:`load_unit`, :func:`install_unit` and :func:`remove_unit` combine them for
callers that work with one unit path at a time; :func:`check_unit_dir` refuses
an unsafe directory before a caller does anything else (an uninstall checks it
before unloading the service).
"""

from __future__ import annotations

import contextlib
import os
import secrets
import stat
from pathlib import Path

_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)


class InstallError(RuntimeError):
    """The requested unit state could not be produced."""


def _open_component(dir_fd: int | None, name: str, shown: Path) -> int:
    """``lstat`` one path component, refuse a symlink or non-directory, then open it with ``O_NOFOLLOW``."""
    info = os.stat(name, dir_fd=dir_fd, follow_symlinks=False)
    if not stat.S_ISDIR(info.st_mode):
        kind = "symlinked" if stat.S_ISLNK(info.st_mode) else "non-directory"
        raise InstallError(f"refusing {kind} path component {shown}: the unit directory must be a real directory")
    fd = os.open(name, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | _NOFOLLOW, dir_fd=dir_fd)
    if (os.fstat(fd).st_dev, os.fstat(fd).st_ino) != (info.st_dev, info.st_ino):
        os.close(fd)
        raise InstallError(f"path component changed while opening: {shown}")
    return fd


def open_unit_dir(unit_dir: Path, *, create: bool = False, home: Path | None = None) -> int | None:
    """Open the unit directory one component at a time, never through a symlink.

    Every component from ``home`` (default: the current user's home; ``/`` for
    a unit directory outside it) down to the unit directory is ``lstat``-ed and
    refused when it is a symlink, then opened relative to its checked parent
    with ``O_NOFOLLOW``. The returned descriptor is the walk's own, so no later
    path lookup can be redirected. A missing component is created only with
    ``create``; otherwise the result is ``None``. The anchor itself is never
    created: a missing home is ``None`` for a read and refused for a write.

    Pass ``home`` unresolved: resolving it first would follow a symlinked home
    before the walk could refuse it.
    """
    target = Path(os.path.abspath(unit_dir))
    home = Path(os.path.abspath(Path.home() if home is None else home))
    anchor = home if target == home or home in target.parents else Path(target.anchor)
    try:
        fd = _open_component(None, str(anchor), anchor)
    except FileNotFoundError:
        if create:
            raise InstallError(f"refusing to create the unit directory under a missing {anchor}") from None
        return None
    current = anchor
    try:
        for name in target.relative_to(anchor).parts:
            current /= name
            if create:
                with contextlib.suppress(FileExistsError):
                    os.mkdir(name, dir_fd=fd)
            try:
                child = _open_component(fd, name, current)
            except FileNotFoundError:
                os.close(fd)
                return None
            os.close(fd)
            fd = child
    except BaseException:
        os.close(fd)
        raise
    return fd


def read_unit(dir_fd: int, name: str) -> tuple[bytes, int] | None:
    """Return an installed unit's bytes and permission bits; refuse anything but a regular file."""
    try:
        info = os.stat(name, dir_fd=dir_fd, follow_symlinks=False)
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(info.st_mode):
        raise InstallError(f"refusing non-regular or symlinked unit file: {name}")
    fd = os.open(name, os.O_RDONLY | os.O_NONBLOCK | _NOFOLLOW, dir_fd=dir_fd)
    with os.fdopen(fd, "rb") as handle:
        held = os.fstat(handle.fileno())
        if (held.st_dev, held.st_ino) != (info.st_dev, info.st_ino):
            raise InstallError(f"unit file changed while reading: {name}")
        return handle.read(), stat.S_IMODE(info.st_mode)


def write_unit(dir_fd: int, name: str, content: bytes, *, mode: int) -> None:
    """Write a temporary file beside the unit and rename it into place with ``mode``.

    The temporary file is created owner-only with ``O_EXCL | O_NOFOLLOW``, so
    it never opens an existing path, and gets ``mode`` only once it is
    complete. The rename replaces the directory entry itself, so a link
    planted at the unit name is never written through.
    """
    temporary = f".{name}.{secrets.token_hex(8)}.tmp"
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | _NOFOLLOW, 0o600, dir_fd=dir_fd)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fchmod(handle.fileno(), mode)
            os.fsync(handle.fileno())
        os.replace(temporary, name, src_dir_fd=dir_fd, dst_dir_fd=dir_fd)
    except BaseException:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(temporary, dir_fd=dir_fd)
        raise
    # Best effort: the rename has already happened; some filesystems refuse a directory fsync.
    with contextlib.suppress(OSError):
        os.fsync(dir_fd)


def check_unit_dir(path: Path, *, home: Path | None = None) -> None:
    """Refuse a symlinked component on the way to ``path``'s directory before a caller acts on the unit."""
    dir_fd = open_unit_dir(path.parent, home=home)
    if dir_fd is not None:
        os.close(dir_fd)


def load_unit(path: Path, *, home: Path | None = None) -> tuple[bytes, int] | None:
    """Return the unit at ``path`` (bytes, permission bits), or ``None`` when it or its directory is missing."""
    dir_fd = open_unit_dir(path.parent, home=home)
    if dir_fd is None:
        return None
    try:
        return read_unit(dir_fd, path.name)
    finally:
        os.close(dir_fd)


def install_unit(path: Path, content: bytes, *, mode: int, home: Path | None = None) -> bool:
    """Make ``path`` hold ``content`` with ``mode``, creating its directory; return whether it wrote."""
    dir_fd = open_unit_dir(path.parent, create=True, home=home)
    if dir_fd is None:
        raise InstallError("unit directory vanished during installation")
    try:
        if read_unit(dir_fd, path.name) == (content, mode):
            return False
        write_unit(dir_fd, path.name, content, mode=mode)
        return True
    finally:
        os.close(dir_fd)


def remove_unit(path: Path, *, home: Path | None = None) -> bool:
    """Remove the entry at ``path`` inside a symlink-free directory; return whether it existed.

    ``unlink`` removes a link itself, never its target, so only the directory
    walk needs guarding: a symlinked ancestor would otherwise point the removal
    at another directory.
    """
    dir_fd = open_unit_dir(path.parent, home=home)
    if dir_fd is None:
        return False
    try:
        try:
            os.unlink(path.name, dir_fd=dir_fd)
        except FileNotFoundError:
            return False
        with contextlib.suppress(OSError):
            os.fsync(dir_fd)
        return True
    finally:
        os.close(dir_fd)
