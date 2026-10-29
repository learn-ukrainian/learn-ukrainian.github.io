"""Shared validation for a delegate-owned read-only scratch lease.

Codex and KimiCC both export the lease as ``TMPDIR``. The lease must be a
direct child of ``<LU_RUNTIME_TMP_BASE_ROOT>/learn-ukrainian``, must not nest
with the checkout in either direction, and must not contain glob characters.

A dispatched Codex read-only task gets one lease per task, named by
:func:`dispatch_lease`. The dispatcher worker creates it just before launch and
removes it at settlement, so the lease lives exactly as long as the run.
"""

from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

_GLOB_CHARS = "*?[]{}"
_TASK_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
DISPATCH_LEASE_PREFIX = "codex-read-only-"


def _namespace() -> Path:
    from scripts.common.scratch import resolve_scratch_root

    return Path(os.environ.get("LU_RUNTIME_TMP_BASE_ROOT") or resolve_scratch_root()) / "learn-ukrainian"


def dispatch_lease(task_id: str) -> Path:
    """The path of a dispatched task's lease; nothing is created here, so a dry run leaves no residue."""
    if not _TASK_ID.fullmatch(task_id):
        raise ValueError("read-only tmp lease: the task id is unsafe as a lease name")
    return _namespace() / f"{DISPATCH_LEASE_PREFIX}{task_id}"


def create_dispatch_lease(task_id: str, cwd: Path) -> Path:
    """Create the task's private lease (exclusive, owner-only) and return it validated against ``cwd``."""
    lease = dispatch_lease(task_id)
    lease.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    lease.mkdir(mode=0o700)
    return (
        validate_read_only_tmp_root({"read_only_tmp_root": str(lease)}, cwd, "read-only", adapter="dispatcher") or lease
    )


def discard_dispatch_lease(task_id: str) -> str | None:
    """Remove the task's lease; never raises, so cleanup cannot stop the worker publishing the task."""
    try:
        lease = dispatch_lease(task_id)
        if lease.is_symlink():
            lease.unlink()
        else:
            shutil.rmtree(lease, ignore_errors=True)
            if lease.exists():
                return f"lease not removed: {lease.name}"
    except (OSError, ValueError) as exc:
        return f"{type(exc).__name__}: {exc}"[:300]
    return None


def validate_read_only_tmp_root(
    tool_config: dict,
    cwd: Path,
    mode: str,
    *,
    adapter: str,
) -> Path | None:
    """Return the resolved lease, or None when the config does not set one.

    Raises:
        ValueError: the lease is missing, nested, an ancestor of ``cwd``,
            outside the runtime tmp namespace, or contains glob characters.
    """
    raw = tool_config.get("read_only_tmp_root")
    if raw is None:
        return None
    root = Path(str(raw))
    resolved = root.resolve()
    namespace = _namespace().resolve()
    checkout = cwd.resolve()
    if (
        mode != "read-only"
        or tool_config.get("review_isolation")  # Codex sealed reviews; kimicc rejects that key first
        or not root.is_absolute()
        or root.is_symlink()
        or not root.is_dir()
        or resolved.parent != namespace
        or checkout.is_relative_to(resolved)
        or resolved.is_relative_to(checkout)
        or any(char in str(resolved) for char in _GLOB_CHARS)
    ):
        raise ValueError(f"{adapter}: read_only_tmp_root must be an existing isolated runtime tmp lease")
    return resolved
