"""Canonical durable paths for fleet communications state."""

from __future__ import annotations

import os
from pathlib import Path

from scripts.guardrails.worktree_containment import (
    NotAGitRepositoryError,
    resolve_main_root,
)

ENV_ROOT = "FLEET_COMMS_ROOT"
ENV_ALLOW_LOCAL_SHADOW = "FLEET_COMMS_ALLOW_LOCAL_SHADOW"
DEFAULT_ROOT_REL = Path("batch_state") / "fleet-comms" / "v1"
RETIRED_LOCAL_MARKER = "READ_ME_CANONICAL_ON_JOB_HOST.txt"
RETIRED_LOCAL_PLANE_MESSAGE = (
    "local fleet-comms sqlite is retired; the job-host Monitor owns "
    "the canonical plane. Do not chmod the stub directory. Observe "
    "via the tunneled API, or set FLEET_COMMS_ALLOW_LOCAL_SHADOW=1 "
    "only for an isolated fixture."
)


class PlaneRootAnchorError(RuntimeError):
    """Raised when the plane root cannot be anchored to the primary checkout."""


def _retired_marker_present(root: Path) -> bool:
    """True when the notebook plane root (or its parent) carries the retire marker."""
    return (root / RETIRED_LOCAL_MARKER).is_file() or (
        root.parent / RETIRED_LOCAL_MARKER
    ).is_file()


def local_plane_is_retired(
    *,
    repo_root: Path | None = None,
    root: Path | None = None,
) -> bool:
    """Return True when this checkout's local plane has been retired to the job host.

    Does not raise. Honors ``FLEET_COMMS_ALLOW_LOCAL_SHADOW=1`` (fixtures) as
    not-retired so isolated tests can open a local sqlite. Never creates or
    chmods the stub directory.
    """
    if os.environ.get(ENV_ALLOW_LOCAL_SHADOW, "").strip() == "1":
        return False
    if root is not None:
        return _retired_marker_present(Path(root).expanduser().resolve())
    env = os.environ.get(ENV_ROOT)
    if env:
        return _retired_marker_present(Path(env).expanduser().resolve())
    candidate = repo_root if repo_root is not None else Path.cwd()
    try:
        base = resolve_main_root(candidate)
    except NotAGitRepositoryError:
        return False
    return _retired_marker_present((base / DEFAULT_ROOT_REL).resolve())


def _refuse_retired_local_plane(root: Path) -> None:
    """Fail closed when the notebook copy has been retired to the job host.

    The marker is an ordinary file in the plane root (gitignored). Tests and
    explicit recovery set ``FLEET_COMMS_ALLOW_LOCAL_SHADOW=1``.
    """
    if os.environ.get(ENV_ALLOW_LOCAL_SHADOW, "").strip() == "1":
        return
    if _retired_marker_present(root):
        raise PlaneRootAnchorError(RETIRED_LOCAL_PLANE_MESSAGE)


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
        root = Path(env).expanduser().resolve()
        _refuse_retired_local_plane(root)
        return root

    candidate = repo_root if repo_root is not None else Path.cwd()
    try:
        base = resolve_main_root(candidate)
    except NotAGitRepositoryError as exc:
        if not allow_non_git:
            raise PlaneRootAnchorError(
                f"refusing to anchor the fleet-comms plane root at {candidate}: "
                "not inside a git repository, so the primary checkout cannot be "
                "verified. A silent fallback here once materialized a shadow "
                "comms DB under a garbage cwd (#6863). Set FLEET_COMMS_ROOT for an "
                "explicit override, or pass allow_non_git=True for an isolated "
                "non-git fixture."
            ) from exc
        base = candidate.resolve()
    root = (base / DEFAULT_ROOT_REL).resolve()
    _refuse_retired_local_plane(root)
    return root
