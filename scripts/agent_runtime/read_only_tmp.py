"""Shared validation for a delegate-owned read-only scratch lease.

Codex and KimiCC both export the lease as ``TMPDIR``. The lease must be a
direct child of ``<LU_RUNTIME_TMP_BASE_ROOT>/learn-ukrainian``, must not nest
with the checkout in either direction, and must not contain glob characters.
"""

from __future__ import annotations

import os
from pathlib import Path

_GLOB_CHARS = "*?[]{}"


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
    from scripts.common.scratch import resolve_scratch_root

    root = Path(str(raw))
    base = Path(os.environ.get("LU_RUNTIME_TMP_BASE_ROOT") or resolve_scratch_root())
    resolved = root.resolve()
    namespace = base.resolve() / "learn-ukrainian"
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
