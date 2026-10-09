"""Pure path derivation shared by dispatch and its execution bindings."""

from __future__ import annotations

import re
from pathlib import Path


def normalize_task_id(agent: str, task_id: str) -> str:
    """Strip one leading agent prefix from a task identifier."""
    for prefix in (f"{agent}-", f"{agent}/"):
        if task_id.startswith(prefix):
            return task_id[len(prefix) :]
    return task_id


def automatic_worktree_path(agent: str, task_id: str, *, repo_root: Path) -> Path:
    """Derive the exact automatic checkout; flatten the task to one component."""
    normalized = normalize_task_id(agent, task_id)
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", normalized).strip("./-") or "task"
    return repo_root.resolve() / ".worktrees" / "dispatch" / agent / safe
