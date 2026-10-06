"""Reviewed regenerable output patterns and delegate's scratch taxonomy (#9828)."""

from __future__ import annotations

import hashlib
import json
import stat
import subprocess
from pathlib import Path

from scripts.orchestration.worktree_artifacts import REGENERABLE_CACHE_DIRECTORIES, _safe_git_env

# Directory patterns apply at any depth, only to real directories.
AUTO_FINALIZE_CACHE_DIRECTORIES = frozenset(
    {
        "__pycache__",  # Python regenerates bytecode when importing source modules.
        ".pytest_cache",  # Pytest regenerates its cache on the next test run.
    }
)
DEPENDENCY_DIRECTORY = "node_modules"  # npm ci recreates dependencies from the tracked sibling package-lock.json.
# Re-downloadable from the published release via scripts/lexicon/manifest_io.py,
# but only when its bytes match the committed, unmodified release pointer.
GENERATED_MANIFEST = "site/src/data/lexicon-manifest.json"
MANIFEST_POINTER = "site/src/data/lexicon-manifest.pointer.json"


def _manifest_matches_published_release(worktree: Path, tracked: set[str]) -> bool:
    """Missing or untrusted release proof leaves the manifest as task output."""
    pointer = worktree / MANIFEST_POINTER
    if MANIFEST_POINTER not in tracked:
        return False
    try:
        if not stat.S_ISREG(pointer.lstat().st_mode):
            return False
        # Require the committed, indexed and local pointer to agree, including
        # a staged edit whose working copy has subsequently been restored.
        for revision in (("HEAD",), ()):
            clean = subprocess.run(
                ["git", "diff", "--no-ext-diff", "--quiet", *revision, "--", MANIFEST_POINTER],
                cwd=worktree,
                env=_safe_git_env(),
                capture_output=True,
                check=False,
                timeout=30,
            )
            if clean.returncode != 0:
                return False
        release = json.loads(pointer.read_bytes())
        if not isinstance(release, dict) or not isinstance(release.get("json_sha256"), str):
            return False
        with (worktree / GENERATED_MANIFEST).open("rb") as handle:
            return hashlib.file_digest(handle, "sha256").hexdigest() == release["json_sha256"]
    except (OSError, ValueError, subprocess.SubprocessError):
        return False


def is_regenerable_ignored_path(path: str, *, worktree: Path, tracked: set[str]) -> bool:
    """Classify regenerable output without traversing any symbolic link.

    A lockfile must be tracked and a local regular file. Environment contents
    without that proof remain output, including caches inside those environments.
    The manifest additionally needs a clean tracked pointer and matching bytes.
    Callers cache the classification for the duration of each inventory.
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
    return (
        relative.as_posix() == GENERATED_MANIFEST
        and stat.S_ISREG(status.st_mode)
        and _manifest_matches_published_release(worktree, tracked)
    )


def is_disposable_auto_finalize_path(path: str) -> bool:
    """Keep delegate's existing scratch semantics; removal needs stronger proof."""
    parts = tuple(part for part in path.replace("\\", "/").split("/") if part and part != ".")
    if not parts:
        return True
    # Auto-finalize historically excludes these two caches, not every cache.
    if any(part in {".venv", DEPENDENCY_DIRECTORY, *AUTO_FINALIZE_CACHE_DIRECTORIES} for part in parts):
        return True
    return parts[-1].endswith(".pyc")
