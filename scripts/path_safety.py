"""Shared filesystem path hardening helpers for user-provided values."""

from __future__ import annotations

from pathlib import Path


def _validate_component(value: str) -> None:
    """Reject clearly unsafe path components."""
    if value == "" or value in {".", ".."}:
        raise ValueError("Invalid path component")
    if "\x00" in value or ":" in value or "\\" in value or "/" in value:
        raise ValueError("Invalid path component")


def safe_join(base: Path, *parts: str | Path) -> Path:
    """Resolve ``parts`` under ``base`` and ensure the result stays in-root.

    ``parts`` may contain nested separators (``a/b``); every component is
    validated individually to prevent traversal and path-shape escapes.
    """
    resolved_base = base.resolve()
    if not parts:
        return resolved_base

    expanded_parts: list[str] = []
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
            expanded_parts.append(component)

    if not expanded_parts:
        return resolved_base

    raw = Path(*expanded_parts)

    resolved = (resolved_base / raw).resolve()
    if not resolved.is_relative_to(resolved_base):
        raise ValueError("Path escapes the configured root")

    return resolved
