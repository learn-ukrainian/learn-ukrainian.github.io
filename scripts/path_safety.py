"""Shared filesystem path hardening helpers for user-provided values."""

from __future__ import annotations

import os
from pathlib import Path


def _validate_component(value: str) -> None:
    """Reject clearly unsafe path components."""
    if value == "" or value in {".", ".."}:
        raise ValueError("Invalid path component")
    if "\x00" in value or ":" in value or "\\" in value or "/" in value:
        raise ValueError("Invalid path component")


def safe_join(base: Path, *parts: str | Path) -> Path:
    """Resolve ``parts`` under ``base`` and ensure the result stays in-root.

    Uses os.path.commonpath for maximum compatibility with security scanners.
    """
    if not parts:
        return base.resolve()  # codeql[py/path-injection] - base is the trusted root passed by caller

    # Resolve the trusted base first. In a release snapshot it may itself be a
    # symlink to live data, so containment must use that resolved destination.
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
    resolved_target = Path(os.path.join(str(resolved_base), *clean_parts)).resolve()

    # Verification: target must be under abs_base
    try:
        common = os.path.commonpath([str(resolved_base), str(resolved_target)])
    except ValueError:
        raise ValueError("Path escapes the configured root (cross-drive)") from None

    if common != str(resolved_base):
        raise ValueError("Path escapes the configured root")

    return resolved_target
