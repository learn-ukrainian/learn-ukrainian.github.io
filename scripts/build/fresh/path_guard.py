"""Repository path boundary for fresh build engine file access."""

from __future__ import annotations

import os
import re
import stat
import subprocess
from pathlib import Path

from scripts.level_config import PREVIOUS_EDITIONS

SLUG_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


def load_a1_reference(repo_root: Path, level: str, slug: str) -> tuple[str, bytes] | None:
    """Read only the mapped matching A1 module, without following any symlink.

    Missing working-tree bytes are optional only when both the index and HEAD
    confirm absence. Directory descriptors keep component checks bound to the
    directories opened; a substituted symlink cannot redirect the read.
    """
    if level != "a1":
        return None
    validate_module(level, slug)
    edition = PREVIOUS_EDITIONS.get(level)
    if edition is None:
        return None
    if edition != "a1-v1":
        raise ValueError("a1_reference_invalid_edition")
    relative = f"curriculum/l2-uk-en/{edition}/{slug}/module.md"
    root = repo_root.absolute()
    descriptor = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for component in (*root.parts[1:], *Path(relative).parts[:-1]):
            info = os.lstat(component, dir_fd=descriptor)
            if not stat.S_ISDIR(info.st_mode):
                raise ValueError(f"a1_reference_unsafe_component: {relative}")
            child = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        info = os.lstat("module.md", dir_fd=descriptor)
        if not stat.S_ISREG(info.st_mode) or not info.st_mode & 0o444:
            raise ValueError(f"a1_reference_not_readable_regular_file: {relative}")
        leaf = os.open("module.md", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=descriptor)
        with os.fdopen(leaf, "rb") as source:
            if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
                raise ValueError(f"a1_reference_not_regular_file: {relative}")
            data = source.read()
    except FileNotFoundError as error:
        tracked = False
        for command in (["ls-files", "--", relative], ["ls-tree", "--name-only", "HEAD", "--", relative]):
            try:
                result = subprocess.run(
                    ["git", "-C", str(root), *command], capture_output=True, text=True, timeout=30, check=False
                )
            except (OSError, subprocess.TimeoutExpired) as git_error:
                raise ValueError(f"a1_reference_git_unknown: {relative}") from git_error
            if result.returncode:
                raise ValueError(f"a1_reference_git_unknown: {relative}") from error
            tracked = tracked or bool(result.stdout.strip())
        if tracked:
            raise ValueError(f"a1_reference_tracked_missing: {relative}") from error
        return None
    finally:
        os.close(descriptor)
    if not data:
        raise ValueError(f"a1_reference_empty: {relative}")
    try:
        data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(f"a1_reference_invalid_utf8: {relative}") from error
    return relative, data


def public_diagnostic(message: str, repo_root: Path) -> str:
    """Keep repository-relative diagnostics; withhold external absolute paths."""
    root = str(repo_root.resolve())
    # Preserve HTTP(S) URL tokens before either path replacement, even when their URL
    # path happens to contain the repository root.
    parts = re.split(r"([A-Za-z][A-Za-z0-9+.-]*://[^\s\"'<>]+)", message)
    for index in range(len(parts)):
        if index % 2 and re.match(r"https?://", parts[index], re.IGNORECASE):
            continue
        part = re.sub(re.escape(root) + r"(?=/|$|[\s\"'<>()[\]{},;:])", ".", parts[index])
        # Exception messages may name files outside the repository (including home
        # directories). Their locations are never useful in tracked build state.
        parts[index] = re.sub(r"(?<![\w./])/(?:[^\s\"'<>()[\]{},;]+)", "<external-path>", part)
    return "".join(parts)


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
