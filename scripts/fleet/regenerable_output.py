"""Reviewed regenerable output patterns and delegate's scratch taxonomy (#9828)."""

from __future__ import annotations

import stat
from pathlib import Path

# Directory patterns apply at any depth, only to real directories.
AUTO_FINALIZE_CACHE_DIRECTORIES = frozenset(
    {
        "__pycache__",  # Python regenerates bytecode when importing source modules.
        ".pytest_cache",  # Pytest regenerates its cache on the next test run.
    }
)
REGENERABLE_CACHE_DIRECTORIES = AUTO_FINALIZE_CACHE_DIRECTORIES | {
    ".ruff_cache",  # Ruff regenerates its cache on the next lint run.
    ".mypy_cache",  # Mypy regenerates its cache on the next type-check run.
}
DEPENDENCY_DIRECTORY = "node_modules"  # npm ci recreates dependencies from the tracked sibling package-lock.json.
# scripts/lexicon/build_data_manifest.py generates this file; enrich_manifest.py enriches it.
GENERATED_MANIFEST = "site/src/data/lexicon-manifest.json"


def is_regenerable_ignored_path(path: str, *, worktree: Path, tracked: set[str]) -> bool:
    """Classify before hashing/copying, without traversing any symbolic link.

    A lockfile must be tracked and a local regular file. Environment contents
    without that proof remain output, including caches inside those environments.
    This only classifies ignored paths; it never deletes or opens their bytes.
    """
    relative = Path(path)
    if relative.is_absolute() or ".." in relative.parts or ".venv" in relative.parts or not relative.parts:
        return False
    if relative.as_posix() != GENERATED_MANIFEST and not (
        (REGENERABLE_CACHE_DIRECTORIES | {DEPENDENCY_DIRECTORY}) & set(relative.parts)
    ):
        return False
    current = worktree
    for index, part in enumerate(relative.parts):
        current /= part
        status = current.lstat()
        if stat.S_ISLNK(status.st_mode):
            return False
        if part == DEPENDENCY_DIRECTORY and stat.S_ISDIR(status.st_mode):
            lock = Path(*relative.parts[:index]) / "package-lock.json"
            # No traversal into dependency trees (which normally contain links).
            try:
                return lock.as_posix() in tracked and stat.S_ISREG((worktree / lock).lstat().st_mode)
            except FileNotFoundError:
                return False
        elif part in REGENERABLE_CACHE_DIRECTORIES and stat.S_ISDIR(status.st_mode):
            return True
    return relative.as_posix() == GENERATED_MANIFEST and stat.S_ISREG(status.st_mode)


def is_disposable_auto_finalize_path(path: str) -> bool:
    """Keep delegate's existing scratch semantics; removal needs stronger proof."""
    parts = tuple(part for part in path.replace("\\", "/").split("/") if part and part != ".")
    if not parts:
        return True
    # Auto-finalize historically excludes these two caches, not every cache.
    if any(part in {".venv", DEPENDENCY_DIRECTORY, *AUTO_FINALIZE_CACHE_DIRECTORIES} for part in parts):
        return True
    return parts[-1].endswith(".pyc")
