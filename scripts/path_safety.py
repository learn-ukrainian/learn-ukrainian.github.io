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
        return base.resolve()

    # Ensure base is absolute and normalized
    abs_base = os.path.abspath(str(base))

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

    target = os.path.abspath(os.path.join(abs_base, *clean_parts))

    # Verification: target must be under abs_base
    try:
        common = os.path.commonpath([abs_base, target])
    except ValueError:
        raise ValueError("Path escapes the configured root (cross-drive)") from None

    if common != abs_base:
        raise ValueError("Path escapes the configured root")

    return Path(target)
