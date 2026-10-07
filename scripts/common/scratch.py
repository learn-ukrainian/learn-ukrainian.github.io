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
A misconfigured value raises :class:`ScratchScanRootError` instead of
falling open or leaking a filesystem traceback. The message names the
variable and a reason code, never a path.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

SCRATCH_ROOT_ENV_VAR = "LU_SCRATCH_ROOT"
SCRATCH_SCAN_ROOT_ENV_VAR = "LU_SCRATCH_SCAN_ROOT"
DEFAULT_SCRATCH_ROOT = Path("/var/tmp/lu")
FALLBACK_SCRATCH_DIRNAME = "lu-scratch"
# Stable reason codes for ScratchScanRootError. The text is the contract tests
# match; do not put a path, errno, or host detail next to them.
SCAN_ROOT_REASON_RELATIVE = "relative"
SCAN_ROOT_REASON_OUTSIDE = "outside_allowed_root"
SCAN_ROOT_REASON_SYMLINK = "symlink_escape"
SCAN_ROOT_REASON_NOT_A_DIRECTORY = "not_a_directory"
_SCAN_ROOT_REASONS = frozenset(
    {
        SCAN_ROOT_REASON_RELATIVE,
        SCAN_ROOT_REASON_OUTSIDE,
        SCAN_ROOT_REASON_SYMLINK,
        SCAN_ROOT_REASON_NOT_A_DIRECTORY,
    }
)


class ScratchScanRootError(RuntimeError):
    """``LU_SCRATCH_SCAN_ROOT`` is misconfigured.

    Dispatch and review callers raise this at their own boundary. It is not a
    filesystem error from path resolution. ``reason`` is one of ``relative``,
    ``outside_allowed_root``, ``symlink_escape``, and ``not_a_directory``.
    The message names the variable and that reason. It never includes a path:
    an absolute path would reveal host layout.

    An empty value is not an error. Production leaves the variable unset, and
    :func:`resolve_confined_scan_root` returns ``None`` so the historical
    scan set stays in place.
    """

    def __init__(self, reason: str) -> None:
        if reason not in _SCAN_ROOT_REASONS:
            raise ValueError(f"unknown {SCRATCH_SCAN_ROOT_ENV_VAR} reason: {reason}")
        self.reason = reason
        super().__init__(f"{SCRATCH_SCAN_ROOT_ENV_VAR} is misconfigured: {reason}")


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


def _within(path: Path, root: Path) -> bool:
    """Return whether ``path`` resolves inside ``root``, failing closed on OS errors."""
    try:
        resolved_path = path.resolve(strict=False)
        resolved_root = root.resolve(strict=False)
    except OSError:
        return False
    return resolved_path == resolved_root or resolved_path.is_relative_to(resolved_root)


def _dotdot_boundary(path: Path) -> Path | None:
    """Return the directory a ``..`` segment steps out of, if any.

    That directory is the allowed root implied by the value itself. A path
    with no ``..`` has no implied boundary.
    """
    if ".." not in path.parts:
        return None
    prefix: list[str] = []
    for part in path.parts:
        if part == "..":
            break
        prefix.append(part)
    if len(prefix) <= 1:
        # ``/../…`` has already left every named directory.
        return Path(path.anchor)
    return Path(*prefix)


def _symlink_escapes(path: Path) -> bool:
    """Return whether a symlink component resolves outside its parent directory.

    The allowed directory is the real parent of that symlink. An ancestor
    such as a symlinked temp directory stays inside its own parent and is
    not an escape.
    """
    current = Path(path.anchor)
    for part in path.parts[1:]:
        if part == ".":
            continue
        if part == "..":
            if current.parent != current:
                current = current.parent
            continue
        candidate = current / part
        try:
            is_link = candidate.is_symlink()
        except OSError:
            return False
        if not is_link:
            current = candidate
            continue
        try:
            target = candidate.resolve(strict=True)
        except OSError:
            target = candidate.resolve(strict=False)
        # ``current`` is the directory that contains this symlink component.
        if not _within(target, current):
            return True
        current = target
    return False


def resolve_confined_scan_root() -> Path | None:
    """Return the scan confine directory, or ``None`` when the variable is unset.

    Production does not set ``LU_SCRATCH_SCAN_ROOT``. A set value must be an
    absolute existing directory. A ``..`` segment that leaves the named
    directory, or a symlink that resolves outside its parent, is
    misconfiguration. The raised :class:`ScratchScanRootError` carries a
    reason code and no path.

    This does not decide which candidates inside a valid boundary are scanned.
    :func:`scratch_scan_roots` keeps that policy.
    """
    raw = os.environ.get(SCRATCH_SCAN_ROOT_ENV_VAR, "").strip()
    if not raw:
        return None
    path = Path(raw)
    if not path.is_absolute():
        raise ScratchScanRootError(SCAN_ROOT_REASON_RELATIVE)
    if _symlink_escapes(path):
        raise ScratchScanRootError(SCAN_ROOT_REASON_SYMLINK)
    boundary = _dotdot_boundary(path)
    if boundary is not None and boundary != Path(path.anchor) and not _within(path, boundary):
        raise ScratchScanRootError(SCAN_ROOT_REASON_OUTSIDE)
    if boundary == Path(path.anchor) and ".." in path.parts:
        raise ScratchScanRootError(SCAN_ROOT_REASON_OUTSIDE)
    resolved = _existing_scan_dir(path)
    if resolved is None:
        raise ScratchScanRootError(SCAN_ROOT_REASON_NOT_A_DIRECTORY)
    return resolved


def scratch_scan_roots() -> list[Path]:
    """Return existing roots a reaper must scan for stale fleet scratch.

    Covers the current scratch root plus the fallback root, default root,
    dispatcher base override, and legacy tmpfs locations that pre-#7164
    tooling used, so the reaper drains both old and new residue.

    When ``LU_SCRATCH_SCAN_ROOT`` is set, only candidates that resolve inside
    that directory are returned. The variable must name an absolute existing
    directory; a relative path, a symlink that leaves its parent, a ``..``
    escape, or a missing path raises :class:`ScratchScanRootError` rather
    than falling open onto the host roots. If none of the usual candidates
    lie inside it, the scan is that directory alone. An empty result is not
    safe here: review orphan cleanup treats an empty scan as "use the host
    temp". Unset, the historical set is unchanged. This is a scan
    confinement, not a creation override.
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

    confine = resolve_confined_scan_root()

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
