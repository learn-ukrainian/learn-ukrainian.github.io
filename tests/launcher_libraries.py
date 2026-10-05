"""Tracked library inventory for fixtures that run real launcher entry points."""

from __future__ import annotations

import subprocess
from pathlib import Path


def launcher_library_files(repo: Path) -> tuple[Path, ...]:
    """Include every tracked library, including future additions and package data."""
    tracked = subprocess.run(
        ["git", "ls-files", "-z", "--", "scripts/lib"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    return tuple(Path(raw) for raw in tracked.stdout.split("\0") if raw)
