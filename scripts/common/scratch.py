"""Shared fleet scratch-root resolution (#7164).

The job hosts mount ``/tmp`` as a small tmpfs with per-user quotas; sizeable
fleet scratch (review repo extractions, dispatch temp payloads, merge-queue
log pulls, contracts-job scratch) exhausted the ops user's quota and every
subsequent ``/tmp`` write failed with EDQUOT. Fleet tooling must therefore
place sizeable scratch on a disk-backed root instead of tmpfs ``/tmp``.

Resolution order (one shared resolution — do not copy per script):

1. ``LU_SCRATCH_ROOT`` environment override (explicit operator/test control);
2. the documented default ``/var/tmp/lu`` (disk-backed per POSIX; host
   ``tmpfiles.d`` aging bounds accumulation);
3. if the default cannot be created and no override was given, fall back to
   ``<system temp>/lu-scratch`` so tooling stays available on hosts without a
   writable ``/var/tmp``.

Task-owned disposable scratch for large ad-hoc runs (#8738) lives in the
``task-scratch`` namespace directly below this root; see
:mod:`scripts.common.task_scratch` and ``scripts/tools/task_scratch.py``.
Legacy sweeps must never treat that namespace, these roots, or their
ancestors as residue.

``LU_RUNTIME_TMP_BASE_ROOT`` is deliberately *not* a creation override: the
dispatcher records it so nested cleanup can find the namespace base, and
honoring it here would pull worker scratch back onto tmpfs.

``LU_SCRATCH_SCAN_ROOT`` confines reaper scans to one existing directory.
It does not change where new scratch is created. Unset, scans still cover
the current root, the default, the fallback, and legacy tmpfs locations.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

SCRATCH_ROOT_ENV_VAR = "LU_SCRATCH_ROOT"
SCRATCH_SCAN_ROOT_ENV_VAR = "LU_SCRATCH_SCAN_ROOT"
DEFAULT_SCRATCH_ROOT = Path("/var/tmp/lu")
FALLBACK_SCRATCH_DIRNAME = "lu-scratch"


def fallback_scratch_root() -> Path:
    """Return the fallback scratch root under system temp."""
    return Path(tempfile.gettempdir()) / FALLBACK_SCRATCH_DIRNAME


def _is_usable_scratch_dir(path: Path) -> bool:
    try:
        if path.exists():
            return path.is_dir() and os.access(path, os.W_OK | os.X_OK)
        parent = path.parent
        return parent.exists() and parent.is_dir() and os.access(parent, os.W_OK | os.X_OK)
    except OSError:
        return False


def resolve_scratch_root() -> Path:
    """Return the fleet scratch root in use.

    If LU_SCRATCH_ROOT override is set, returns that path.
    Otherwise, returns DEFAULT_SCRATCH_ROOT if accessible/creatable,
    or falls back to <system temp>/lu-scratch.
    """
    override = os.environ.get(SCRATCH_ROOT_ENV_VAR, "").strip()
    if override:
        return Path(override)
    if _is_usable_scratch_dir(DEFAULT_SCRATCH_ROOT):
        return DEFAULT_SCRATCH_ROOT
    return fallback_scratch_root()


def ensure_scratch_root() -> Path:
    """Return the fleet scratch root, creating it when missing.

    An explicit ``LU_SCRATCH_ROOT`` override is honored strictly: if it cannot
    be created the error propagates so a misconfiguration is visible. Only the
    built-in default falls back to ``<system temp>/lu-scratch``.
    """
    override = os.environ.get(SCRATCH_ROOT_ENV_VAR, "").strip()
    if override:
        root = Path(override)
        root.mkdir(parents=True, exist_ok=True)
        return root
    root = DEFAULT_SCRATCH_ROOT
    try:
        root.mkdir(parents=True, exist_ok=True)
    except OSError:
        root = fallback_scratch_root()
        root.mkdir(parents=True, exist_ok=True)
    return root


def make_scratch_dir(prefix: str) -> Path:
    """Create one private scratch directory under the fleet scratch root."""
    return Path(tempfile.mkdtemp(prefix=prefix, dir=ensure_scratch_root()))


def _existing_scan_dir(path: Path) -> Path | None:
    """Return ``path`` resolved when it is an existing directory."""
    try:
        resolved = path.resolve(strict=True)
    except OSError:
        return None
    if not resolved.is_dir():
        return None
    return resolved


def scratch_scan_roots() -> list[Path]:
    """Return existing roots a reaper must scan for stale fleet scratch.

    Covers the current scratch root plus the fallback root, default root,
    dispatcher base override, and legacy tmpfs locations that pre-#7164
    tooling used, so the reaper drains both old and new residue.

    When ``LU_SCRATCH_SCAN_ROOT`` is set, only candidates that resolve inside
    that directory are returned. The variable must name an existing directory;
    a missing path raises rather than falling open onto the host roots. If
    none of the usual candidates lie inside it, the scan is that directory
    alone. An empty result is not safe here: review orphan cleanup treats
    an empty scan as "use the host temp". Unset, the historical set is
    unchanged. This is a scan confinement, not a creation override.
    """
    roots: list[Path] = []
    seen: set[Path] = set()
    candidates = [
        resolve_scratch_root(),
        DEFAULT_SCRATCH_ROOT,
        fallback_scratch_root(),
    ]
    base_override = os.environ.get("LU_RUNTIME_TMP_BASE_ROOT", "").strip()
    if base_override:
        candidates.append(Path(base_override))
    candidates.append(Path(tempfile.gettempdir()))

    confine_raw = os.environ.get(SCRATCH_SCAN_ROOT_ENV_VAR, "").strip()
    confine: Path | None = None
    if confine_raw:
        confine = _existing_scan_dir(Path(confine_raw))
        if confine is None:
            raise OSError(f"{SCRATCH_SCAN_ROOT_ENV_VAR} is set but is not an existing directory: {confine_raw}")

    for candidate in candidates:
        resolved = _existing_scan_dir(candidate)
        if resolved is None or resolved in seen:
            continue
        if confine is not None and not resolved.is_relative_to(confine):
            continue
        seen.add(resolved)
        roots.append(resolved)
    if confine is not None and not roots:
        roots.append(confine)
    return roots
