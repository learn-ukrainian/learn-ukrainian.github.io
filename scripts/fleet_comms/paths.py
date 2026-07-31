"""Canonical durable paths for fleet communications state."""

from __future__ import annotations

import os
from pathlib import Path

from scripts.guardrails.worktree_containment import (
    NotAGitRepositoryError,
    resolve_main_root,
)

ENV_ROOT = "FLEET_COMMS_ROOT"
DEFAULT_ROOT_REL = Path("batch_state") / "fleet-comms" / "v1"


def default_plane_root(*, repo_root: Path | None = None) -> Path:
    """Resolve fleet state beneath the primary checkout, unless explicitly overridden."""
    env = os.environ.get(ENV_ROOT)
    if env:
        return Path(env).expanduser()

    candidate = repo_root if repo_root is not None else Path.cwd()
    try:
        base = resolve_main_root(candidate)
    except NotAGitRepositoryError:
        # Preserve support for isolated non-Git callers and test fixtures.
        base = candidate.resolve()
    return (base / DEFAULT_ROOT_REL).resolve()
