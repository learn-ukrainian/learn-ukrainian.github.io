"""Regenerable cache/build patterns and delegate's scratch taxonomy (#9828, #10061)."""

from __future__ import annotations

import hashlib
import os
import re
import stat
from pathlib import Path
from typing import Any

from scripts.orchestration.worktree_artifacts import REGENERABLE_CACHE_DIRECTORIES

# #10227: archive before release; these are never auto-finalize exclusions.
BRANCH_HOLDER_SCRATCH_PATTERNS = ("*.orig", "*.patch", "pytest_out.txt")
MAX_BRANCH_HOLDER_FILE_BYTES = 256 * 1024 * 1024


def branch_holder_scratch_inventory(worktree: Path, *, primary: Path) -> dict[str, Any]:
    """Closed regular-file contract for branch hand-off, separate from ignored output.

    Git names are NUL-delimited. Any unknown/non-scratch entry refuses the
    whole inventory. Identity plus bytes bind the later descriptor unlink.
    """
    from scripts.orchestration import worktree_artifacts as artifacts

    status = artifacts.safe_git(
        ["status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignore-submodules=none"],
        cwd=worktree, env=artifacts._safe_git_env(), capture_output=True, check=True, timeout=30,
    ).stdout
    stages = artifacts.safe_git(
        ["ls-files", "--stage", "-z"], cwd=worktree, env=artifacts._safe_git_env(),
        capture_output=True, check=True, timeout=30,
    ).stdout.split(b"\0")
    if any(entry.startswith(b"160000 ") for entry in stages):
        raise ValueError("submodule")
    if any(entry[:3] != b"?? " for entry in status.split(b"\0") if entry):
        raise ValueError("tracked_modification")
    tracked = set(artifacts._git_paths(worktree, "--cached"))
    # Porcelain can conceal assume-unchanged/skip-worktree edits. Sparse absent
    # paths are fine; a present concealed path must still match its index blob.
    flagged = artifacts._git_paths(worktree, "-v")
    staged = {os.fsdecode(entry.split(b"\t", 1)[1]): entry.split()[1] for entry in stages if entry}
    for entry in flagged:
        flag, name = entry[:1], entry[2:]
        if flag.islower() or flag.upper() == "S":
            file = worktree / name
            if flag.upper() == "S" and not os.path.lexists(file):
                continue
            walked = artifacts._read_preserved_bytes(file, root=worktree)
            if walked.file_type != "regular":
                raise ValueError("not_regular_file")
            digest = hashlib.sha256() if len(staged[name]) == 64 else hashlib.sha1()
            digest.update(f"blob {len(walked.payload)}\0".encode("ascii"))
            digest.update(walked.payload)
            if digest.hexdigest().encode("ascii") != staged[name]:
                raise ValueError("tracked_modification")
    scratch = artifacts._git_paths(worktree, "--others", "--exclude-standard")
    ignored = artifacts._git_paths(worktree, "--others", "--ignored", "--exclude-standard")
    # Git omits FIFOs/sockets entirely. A filesystem pass is therefore required
    # even when Git says clean; no unsupported entry can vanish with the tree.
    def scan_error(error: OSError) -> None:
        raise error

    observed = set()
    for directory, dirs, files in os.walk(worktree, followlinks=False, onerror=scan_error):
        parent = Path(directory)
        if parent != worktree and os.path.lexists(parent / ".git"):
            raise ValueError("nested_repository")
        for name in list(dirs) + files:
            relative = (parent / name).relative_to(worktree)
            if relative == Path(".git"):
                continue
            if artifacts.is_disposable_path(relative, worktree=worktree, primary=primary):
                if name in dirs:
                    dirs.remove(name)
                continue
            info = (parent / name).lstat()
            if stat.S_ISDIR(info.st_mode):
                continue
            if not stat.S_ISREG(info.st_mode):
                raise ValueError("not_regular_file")
            if relative.as_posix() not in tracked:
                observed.add(relative.as_posix())
    if observed - set(scratch + ignored):
        raise ValueError("inventory_unknown")
    entries = []
    # Inspect ignored output independently: arbitrary regular output is archived,
    # while cache and verified provisioned-link exemptions retain their taxonomy.
    for name in sorted(set(scratch + ignored)):
        relative = Path(name)
        artifacts._relative_parts(worktree / relative, worktree)
        if artifacts.is_disposable_path(relative, worktree=worktree, primary=primary):
            continue
        root_fd = artifacts._open_trusted_root(worktree)
        try:
            parent_fd, owned = artifacts._open_parent(root_fd, relative.parts[:-1])
            try:
                # No nested repository, including an ignored nested checkout.
                current = worktree
                for part in relative.parts[:-1]:
                    current /= part
                    if os.path.lexists(current / ".git"):
                        raise ValueError("nested_repository")
                info = os.stat(relative.name, dir_fd=parent_fd, follow_symlinks=False)
                if not stat.S_ISREG(info.st_mode):
                    raise ValueError("not_regular_file")
                if info.st_nlink != 1:
                    raise ValueError("hard_link")
                if info.st_size > MAX_BRANCH_HOLDER_FILE_BYTES:
                    raise ValueError("file_size_cap")
                if name in scratch:
                    eligible = (
                        relative.name == BRANCH_HOLDER_SCRATCH_PATTERNS[2]
                        or relative.name.endswith(BRANCH_HOLDER_SCRATCH_PATTERNS[1][1:])
                        or (relative.name.endswith(BRANCH_HOLDER_SCRATCH_PATTERNS[0][1:]) and name[:-5] in tracked)
                    )
                    if not eligible:
                        raise ValueError("non_allowlisted_untracked")
                size, digest = artifacts._fingerprint(worktree / relative, root=worktree)
                after = os.stat(relative.name, dir_fd=parent_fd, follow_symlinks=False)
                if (
                    (info.st_dev, info.st_ino, info.st_mode, info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
                    != (after.st_dev, after.st_ino, after.st_mode, after.st_nlink, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
                    or size != info.st_size
                ):
                    raise ValueError("source_changed")
                entries.append({
                    "path": name, "size": size, "sha256": digest,
                    "identity": [info.st_dev, info.st_ino, info.st_mtime_ns, info.st_ctime_ns],
                    "kind": "scratch" if name in scratch else "ignored",
                })
            finally:
                if owned:
                    os.close(parent_fd)
        finally:
            os.close(root_fd)
    root = worktree.lstat()
    return {"directory_identity": [root.st_dev, root.st_ino], "paths": entries}


# Directory patterns apply at any depth, only to real directories.
AUTO_FINALIZE_CACHE_DIRECTORIES = frozenset(
    {
        "__pycache__",  # Python regenerates bytecode when importing source modules.
        ".pytest_cache",  # Pytest regenerates its cache on the next test run.
    }
)
DEPENDENCY_DIRECTORY = "node_modules"  # npm ci recreates dependencies from the tracked sibling package-lock.json.

# #10061: only ignored build-written files, never whole public/src/data trees.
# Commands below run from site/, except the explicitly repository-root commands.
SITE_BUILD_OUTPUT_PATTERNS = (
    # npm run build / build:shell / build:full: Astro emits every route tree.
    r"site/dist/.+",
    # Manifest and practice shards can contain unpublished work: hydration
    # refuses to clobber richer local data (#4917). Preserve them and .tmp files.
    # npm run hydrate:teacher: only these two SERVED_FILES are written.
    r"site/public/lexicon/practice-(?:deck|cloze)\.teacher\.json",
    # npm run hydrate: hydrate-lexicon-api-shards.ts calls copyPracticeApiShards.
    r"site/public/api/lexicon/practice-(?:index|lexemes|cloze)\.(?:A1|A2|B1|B2|C1)\.json",
    # Same command calls writeSearchShardFiles, writing direct JSON children.
    r"site/public/lexicon/search/[^/]+\.json",
    # Repository root: make atlas-export-runtime (scripts.atlas.export_runtime_shards).
    # Include interrupted _ExportStage writes as well as installed versions.
    r"site/public/atlas/(?:current|\.current-[0-9]+-[0-9a-f]+)\.json",
    r"site/public/atlas/versions/[^/]+/manifest\.json",
    r"site/public/atlas/versions/[^/]+/entries/[^/]+\.json\.gz",
    r"site/public/atlas/versions/[^/]+/search/(?:articles|aliases)/[^/]+\.json\.gz",
    r"site/public/atlas/versions/[^/]+/decks/(?:A1|A2|B1|B2|C1)/(?:index|lexemes|cloze)\.json\.gz",
    # npm run build*: astro.config.mjs pronunciation-fallback-manifest hook.
    r"site/public/audio/pronunciation/manifest\.json",
)
_SITE_BUILD_OUTPUT = re.compile("(?:" + "|".join(SITE_BUILD_OUTPUT_PATTERNS) + ")")
_DATABASE_SUFFIXES = frozenset(
    extension + sidecar
    for extension in (".db", ".sqlite", ".sqlite3", ".db3", ".duckdb", ".mdb")
    for sidecar in ("", "-wal", "-shm", "-journal")
)


def is_regenerable_ignored_path(path: str, *, worktree: Path, tracked: set[str]) -> bool:
    """Classify regenerable output without traversing any symbolic link.

    A lockfile must be tracked and a local regular file. Environment contents
    without that proof remain output, including caches inside those environments.
    """
    relative = Path(path)
    if relative.is_absolute() or ".." in relative.parts or ".venv" in relative.parts or not relative.parts:
        return False
    if relative.as_posix() in tracked:
        return False
    # Site candidates require a complete component walk before pattern matching.
    site_tree = relative.parts[:2] in {("site", "dist"), ("site", "public")} or relative.parts[:3] == (
        "site",
        "src",
        "data",
    )
    if not site_tree and not (REGENERABLE_CACHE_DIRECTORIES | {DEPENDENCY_DIRECTORY}) & set(relative.parts):
        return False
    current = worktree
    for index, part in enumerate(relative.parts):
        current /= part
        status = current.lstat()
        if stat.S_ISLNK(status.st_mode):
            return False
        if not (stat.S_ISDIR(status.st_mode) or stat.S_ISREG(status.st_mode)):
            return False
        if not site_tree and part == DEPENDENCY_DIRECTORY and stat.S_ISDIR(status.st_mode):
            lock = Path(*relative.parts[:index]) / "package-lock.json"
            # No traversal into dependency trees (which normally contain links).
            try:
                return lock.as_posix() in tracked and stat.S_ISREG((worktree / lock).lstat().st_mode)
            except FileNotFoundError:
                return False
        elif not site_tree and part in REGENERABLE_CACHE_DIRECTORIES and stat.S_ISDIR(status.st_mode):
            return True
    # Directories must still be inventoried: a descendant can be a symlink,
    # a tracked file, a database, or unlisted output. Never exempt a subtree.
    return (
        stat.S_ISREG(status.st_mode)
        and not _DATABASE_SUFFIXES.intersection(suffix.casefold() for suffix in relative.suffixes)
        and _SITE_BUILD_OUTPUT.fullmatch(relative.as_posix()) is not None
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
