"""Shared filesystem path hardening helpers for user-provided values."""

from __future__ import annotations

import os
from pathlib import Path

# Dual-flavor import: several consumers load this module as top-level
# ``path_safety`` with only ``scripts/`` on sys.path (test sys.path-hack,
# build entrypoints) — a hard ``scripts.*`` import breaks that flavor.
try:
    from scripts.common.release_layout import LIVE_DATA_PATHS, MANIFEST_NAME, is_release_root
except ImportError:  # scripts/ on sys.path (stripped flavor)
    from common.release_layout import LIVE_DATA_PATHS, MANIFEST_NAME, is_release_root  # type: ignore[no-redef]


def _validate_component(value: str) -> None:
    """Reject clearly unsafe path components."""
    if value == "" or value in {".", ".."}:
        raise ValueError("Invalid path component")
    if "\x00" in value or ":" in value or "\\" in value or "/" in value:
        raise ValueError("Invalid path component")


def _is_within(root: Path, target: Path) -> bool:
    """Return whether a resolved target is contained by one resolved root."""
    try:
        common = os.path.commonpath([str(root), str(target)])
    except ValueError:
        return False
    return common == str(root)


def _declared_live_data_roots(logical_base: Path) -> tuple[Path, ...]:
    """Return the resolved, explicitly approved release data targets.

    ``LIVE_DATA_PATHS`` is the release layout's single source of truth. Only
    the closest manifest-bearing release root above the trusted base may grant
    this exception. This keeps a manifest or symlink planted below a requested
    target from acquiring a live-data exception. The logical paths remain
    snapshot-relative while their declared symlink targets are the only
    additional resolved locations that ``safe_join`` may accept.
    """
    release_root = next(
        (
            ancestor
            for ancestor in (logical_base, *logical_base.parents)
            if is_release_root(ancestor) and (ancestor / MANIFEST_NAME).is_file()
        ),
        None,
    )
    if release_root is None:
        return ()

    return tuple(
        live_root.resolve()
        for relative_name in LIVE_DATA_PATHS
        if (live_root := release_root / relative_name).is_symlink()
    )


def safe_join(base: Path, *parts: str | Path) -> Path:
    """Join ``parts`` under ``base`` after resolving only for containment.

    The returned path remains *logical* (snapshot-relative in release mode),
    so API payloads do not expose the live checkout through a resolved
    symlink.  Resolution is still mandatory for the containment check, which
    rejects undeclared child-symlink escapes.

    Uses os.path.commonpath for maximum compatibility with security scanners.
    """
    logical_base = Path(os.path.abspath(str(base)))
    if not parts:
        return logical_base  # codeql[py/path-injection] - base is the trusted root passed by caller

    # Resolve the trusted base first. In a release snapshot it may itself be a
    # declared live-data symlink, so containment uses the resolved destination
    # while callers retain the logical path below.
    resolved_base = Path(os.path.abspath(str(base))).resolve()

    # Join and normalize the target path
    # We still validate components individually to prevent embedded '..'
    # before joining, as an extra layer of defense.
    clean_parts = []
    for part in map(str, parts):
        if not part:
            raise ValueError("Invalid path component")
        if "\x00" in part:
            raise ValueError("Null byte in user path")
        candidate = Path(part)
        if candidate.is_absolute():
            raise ValueError("Absolute path input is not allowed")
        for component in candidate.parts:
            _validate_component(component)
            clean_parts.append(component)

    # Resolve the candidate too: lexical normalization alone would accept a
    # child symlink that points outside an otherwise trusted base directory.
    logical_target = Path(os.path.join(str(logical_base), *clean_parts))
    resolved_target = logical_target.resolve()

    # Fast path: plain containment under the resolved base needs no release
    # machinery. Only on a miss may the target be under one of the release's
    # deliberately small set of declared live-data symlinks (computed lazily —
    # the ancestor walk stats the filesystem); every other resolved symlink
    # escape remains forbidden. Semantics identical to checking all roots.
    if not _is_within(resolved_base, resolved_target) and not any(
        _is_within(root, resolved_target) for root in _declared_live_data_roots(logical_base)
    ):
        raise ValueError("Path escapes the configured root")

    return logical_target


def trusted_join(base: Path, *parts: str | Path) -> Path:
    """Lexically join TRUSTED repo-internal components under ``base``.

    ⚠️ NEVER pass request-derived or user-supplied values here — use
    ``safe_join``, which additionally resolves symlinks and enforces the
    release live-data containment contract. ``trusted_join`` exists for hot
    internal scanners (orient/pipeline module iteration joins config-derived
    slugs onto repo roots thousands of times per request); it validates
    components lexically (no ``..``, no absolute parts, no separators, no NUL)
    and enforces commonpath containment, but performs NO filesystem
    resolution, so a planted child symlink is not detected. That trade is
    sound only when both the base and every component come from repo-internal
    configuration or directory listings.
    """
    if not parts:
        return Path(os.path.abspath(str(base)))

    abs_base = os.path.abspath(str(base))
    clean_parts: list[str] = []
    for part in map(str, parts):
        if not part:
            raise ValueError("Invalid path component")
        if "\x00" in part:
            raise ValueError("Null byte in user path")
        candidate = Path(part)
        if candidate.is_absolute():
            raise ValueError("Absolute path input is not allowed")
        for component in candidate.parts:
            _validate_component(component)
            clean_parts.append(component)

    target = os.path.abspath(os.path.join(abs_base, *clean_parts))
    try:
        common = os.path.commonpath([abs_base, target])
    except ValueError:
        raise ValueError("Path escapes the configured root (cross-drive)") from None
    if common != abs_base:
        raise ValueError("Path escapes the configured root")
    return Path(target)
