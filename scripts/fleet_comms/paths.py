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


class PlaneRootAnchorError(RuntimeError):
    """Raised when the plane root cannot be anchored to the primary checkout."""


def default_plane_root(
    *,
    repo_root: Path | None = None,
    allow_non_git: bool = False,
) -> Path:
    """Resolve fleet state beneath the primary checkout, unless explicitly overridden.

    Anchoring order:

    1. ``FLEET_COMMS_ROOT`` env override (explicit operator choice) — honored as-is.
    2. The primary checkout that owns the shared ``.git`` store, resolved from
       ``repo_root`` (default: process cwd).

    When neither applies — the candidate is not inside a git repository — the
    default is a HARD ERROR (#6863), never a silent fallback to the raw
    candidate. The old fallback let a process running with a garbage cwd (a
    transport-leak directory fragment at the repo root) materialize a shadow
    ``batch_state/fleet-comms/v1`` tree there, converting a quoting bug into
    silent message loss. Isolated non-git callers and test fixtures must opt in
    explicitly with ``allow_non_git=True``.
    """
    env = os.environ.get(ENV_ROOT)
    if env:
        return Path(env).expanduser().resolve()

    candidate = repo_root if repo_root is not None else Path.cwd()
    try:
        base = resolve_main_root(candidate)
    except NotAGitRepositoryError as exc:
        if not allow_non_git:
            raise PlaneRootAnchorError(
                f"refusing to anchor the fleet-comms plane root at {candidate}: "
                "not inside a git repository, so the primary checkout cannot be "
                "verified. A silent fallback here once materialized a shadow comms "
                "DB under a garbage cwd (#6863). Set FLEET_COMMS_ROOT for an "
                "explicit override, or pass allow_non_git=True for an isolated "
                "non-git fixture."
            ) from exc
        base = candidate.resolve()
    return (base / DEFAULT_ROOT_REL).resolve()
