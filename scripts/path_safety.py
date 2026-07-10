"""Shared filesystem path hardening helpers for user-provided values."""

from __future__ import annotations

import os
from pathlib import Path

from scripts.api.release_snapshot import LIVE_DATA_PATHS, MANIFEST_NAME


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


def _declared_live_data_roots(logical_target: Path) -> tuple[Path, ...]:
    """Return the resolved, explicitly approved release data targets.

    ``LIVE_DATA_PATHS`` is the release layout's single source of truth.  A
    manifest marks the ancestor as a completed release, preventing an
    unrelated symlink merely named ``curriculum`` or ``docs`` from acquiring
    this exception. The logical paths remain snapshot-relative while their
    declared symlink targets are the only additional resolved locations that
    ``safe_join`` may accept.
    """
    roots: list[Path] = []
    for ancestor in logical_target.parents:
        if not (ancestor / MANIFEST_NAME).is_file():
            continue
        for relative_name in LIVE_DATA_PATHS:
            live_root = ancestor / relative_name
            if live_root.is_symlink():
                roots.append(live_root.resolve())
    return tuple(roots)


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

    # A release has a deliberately small set of live-data symlinks.  A target
    # may be under the resolved base or one of those declared destinations;
    # every other resolved symlink escape remains forbidden.
    allowed_roots = (resolved_base, *_declared_live_data_roots(logical_target))
    if not any(_is_within(root, resolved_target) for root in allowed_roots):
        raise ValueError("Path escapes the configured root")

    return logical_target
