"""Call-time location of the shared dispatch task store."""

from __future__ import annotations

import os
from pathlib import Path

from scripts.common.repo_root import resolve_repo_root


def tasks_dir() -> Path:
    """Use a test override or the primary checkout's dispatch task store."""
    override = os.environ.get("LU_TASKS_DIR")
    if override:
        return Path(override)
    return resolve_repo_root(Path(__file__), 2) / "batch_state" / "tasks"
