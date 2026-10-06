"""Open one directory component without following a symlink.

Unit installation (#9875) and artifact preservation (#9889) share this step.
:func:`open_directory_component` ``lstat``s one name, refuses a symlink or
non-directory, opens it with ``O_NOFOLLOW`` relative to the previous
descriptor, and requires the opened inode to be the one just checked.
Callers walk from a trusted descriptor and never open a multi-component path.
"""

from __future__ import annotations

import os
import stat

_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
_DIRECTORY_FLAGS = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | _NOFOLLOW


class ComponentOpenError(Exception):
    """One path component is a symlink, not a directory, or changed while opening.

    ``kind`` is ``symlinked``, ``non-directory`` or ``changed``. The message is
    that kind and never a path.
    """

    def __init__(self, kind: str) -> None:
        self.kind = kind
        super().__init__(kind)


def open_directory_component(dir_fd: int | None, name: str) -> int:
    """Open one directory component relative to ``dir_fd`` without following a symlink.

    ``dir_fd`` is ``None`` only for the trusted anchor. Every later component
    is a single name opened relative to the previous descriptor. The caller
    closes the returned descriptor.
    """
    info = os.stat(name, dir_fd=dir_fd, follow_symlinks=False)
    if not stat.S_ISDIR(info.st_mode):
        kind = "symlinked" if stat.S_ISLNK(info.st_mode) else "non-directory"
        raise ComponentOpenError(kind)
    fd = os.open(name, _DIRECTORY_FLAGS, dir_fd=dir_fd)
    try:
        held = os.fstat(fd)
        if (held.st_dev, held.st_ino) != (info.st_dev, info.st_ino) or not stat.S_ISDIR(held.st_mode):
            raise ComponentOpenError("changed")
    except BaseException:
        os.close(fd)
        raise
    return fd
