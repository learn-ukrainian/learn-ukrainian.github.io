"""Resolve agent CLI binaries under login-shell PATH directories.

Dispatch and runtime spawns inherit a minimal PATH (systemd, cron, SSH
non-interactive shells) that omits ``~/.local/bin`` and ``~/.opencode/bin``
where seat CLIs are installed on job hosts. Augment lookup with those dirs
and return absolute paths for ``Popen`` argv[0].

Issue: #7161
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

_LOGIN_BIN_SUFFIXES: tuple[str, ...] = (
    ".local/bin",
    ".opencode/bin",
)


def _login_bin_dirs() -> tuple[str, ...]:
    home = Path.home()
    return tuple(str(home / suffix) for suffix in _LOGIN_BIN_SUFFIXES)


def augment_path_for_login_bins(path: str | None) -> str:
    """Append login install dirs to *path* when they are not already present."""
    entries = [entry for entry in (path or "").split(os.pathsep) if entry]
    present = {os.path.normcase(entry) for entry in entries}
    for directory in _login_bin_dirs():
        normalized = os.path.normcase(directory)
        if normalized not in present:
            entries.append(directory)
            present.add(normalized)
    return os.pathsep.join(entries)


def resolve_agent_binary(binary: str, *, path: str | None = None) -> str | None:
    """Return an absolute executable path for *binary*, or ``None`` if absent.

  When *binary* is a bare name, lookup uses *path* augmented with the login
  install directories. Existing absolute or relative paths are accepted when
  they already point at an executable file.
    """
    if not binary:
        return None

    if os.sep in binary or (os.altsep and os.altsep in binary):
        candidate = Path(binary)
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate.resolve())

    search_path = augment_path_for_login_bins(path)
    found = shutil.which(binary, path=search_path)
    if found:
        return str(Path(found).resolve())
    return None
