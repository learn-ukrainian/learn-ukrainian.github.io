"""Shared descriptor-bound access to the mutable ``.agent`` directory."""

from __future__ import annotations

import contextlib
import os


def open_agent_directory(agent_root: str) -> int:
    """Create (when absent) and open ``agent_root`` without following links.

    The final open is the security boundary. If another process creates or swaps
    the name after ``mkdir``, ``O_NOFOLLOW`` rejects a symlink and the returned
    descriptor remains bound to the opened directory.
    """
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    try:
        return os.open(agent_root, flags)
    except FileNotFoundError:
        with contextlib.suppress(FileExistsError):
            os.mkdir(agent_root)
        return os.open(agent_root, flags)
