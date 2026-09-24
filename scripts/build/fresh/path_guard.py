"""Repository path boundary for fresh build engine file access."""

from __future__ import annotations

import re
from pathlib import Path

SLUG_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


def validate_module(level: str, slug: str) -> None:
    """Reject malformed module identifiers before building any filesystem path."""
    from scripts.build.fresh.draft_schema import LEVELS

    if level not in LEVELS:
        raise ValueError(f"invalid_level: {level}")
    if not SLUG_RE.fullmatch(slug):
        raise ValueError(f"invalid_slug: {slug}")


def checked_path(repo_root: Path, relative: str | Path, allowed_root: str | Path) -> Path:
    """Build a literal repo path, then reject symlinks escaping its allowed root."""
    root = repo_root.resolve()
    rel = Path(relative)
    allowed = Path(allowed_root)
    if rel.is_absolute() or allowed.is_absolute() or ".." in rel.parts or ".." in allowed.parts:
        raise ValueError(f"path_outside_allowed_root: {relative}")
    path = (root / rel).resolve()
    boundary = root / allowed  # Keep this lexical: a symlink cannot redefine the allowed root.
    if not path.is_relative_to(boundary):
        raise ValueError(f"path_outside_allowed_root: {relative}")
    parts = path.relative_to(root).parts
    if ((parts[:2] == ("curriculum", "l2-uk-en") and len(parts) > 2
            and parts[2] not in {"lesson-plans", "evidence"})
            or "wiki" in parts or any(part.endswith("-v1") for part in parts)):
        raise ValueError(f"path_forbidden: {relative}")
    return path


def checked_existing_path(repo_root: Path, path: Path, allowed_root: str | Path) -> Path:
    """Check a path assembled by an engine helper without trusting its resolution."""
    try:
        relative = path.relative_to(repo_root.resolve())
    except ValueError as err:
        raise ValueError(f"path_outside_allowed_root: {path}") from err
    return checked_path(repo_root, relative, allowed_root)
