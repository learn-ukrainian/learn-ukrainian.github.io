"""Regenerable cache/build patterns and delegate's scratch taxonomy (#9828, #10061)."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from urllib.parse import quote

from scripts.common.nofollow_walk import ComponentOpenError
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

# These names alone never authorize deletion. The committed hydrators reproduce
# exactly the bytes pinned by their committed release pointers; richer local
# manifests/shards must still be preserved (#4917).
RELEASE_OUTPUT_PATTERNS = (
    r"site/src/data/lexicon-manifest\.json",
    r"site/public/lexicon/practice-(?:index|lexemes|cloze|stress|classify|paradigm|synonym|heritage|paronym|antonym|homonym|imperative)\.(?:A1|A2|B1|B2|C1)\.json",
)
_RELEASE_OUTPUT = re.compile("(?:" + "|".join(RELEASE_OUTPUT_PATTERNS) + ")")


def _release_is_recoverable(worktree: Path, stem: str, pointer: dict[str, Any]) -> bool:
    """Prefer a kept gzip; otherwise require fresh uploaded-asset metadata.

    The fixed sibling gzip is never regenerable/disposable: the ordinary
    preservation gate must retain it (or refuse removal at its unchanged cap).
    A gzip in this checkout therefore cannot prove its own deletion safe.
    """
    from scripts.common import github_client
    from scripts.orchestration import worktree_artifacts as artifacts

    size, digest = pointer.get("gz_bytes"), pointer.get("gz_sha256")
    if type(size) is not int or size <= 0 or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        return False
    kept = Path(f"site/src/data/{stem}.json.gz")
    if os.path.lexists(worktree / kept):
        if kept.as_posix() not in artifacts._git_paths(worktree, "--others", "--ignored", "--exclude-standard"):
            return False
        return _matches_release_pin(worktree, kept, (size, digest))
    tag, url = pointer.get("release_tag"), pointer.get("asset_url")
    if not isinstance(tag, str) or not tag:
        return False
    prefix = "https://github.com/learn-ukrainian/learn-ukrainian.github.io/releases/download/"
    if not isinstance(url, str) or not url.startswith(f"{prefix}{quote(tag, safe='')}/"):
        return False
    result = github_client.run(
        ["gh", "api", f"repos/learn-ukrainian/learn-ukrainian.github.io/releases/tags/{quote(tag, safe='')}"],
        cwd=worktree,
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
        fresh=True,
    )
    listing = json.loads(result.stdout)
    assets = listing.get("assets") if isinstance(listing, dict) else None
    if not isinstance(assets, list):
        return False
    matches = [asset for asset in assets if isinstance(asset, dict) and asset.get("browser_download_url") == url]
    return len(matches) == 1 and (
        matches[0].get("state") == "uploaded"
        and type(matches[0].get("size")) is int
        and matches[0]["size"] == size
        and matches[0].get("digest") == f"sha256:{digest}"
    )


def committed_release_pins(worktree: Path, tracked: set[str]) -> dict[str, tuple[int, str]]:
    """Read clean HEAD pointers with recoverability proof once per inventory."""
    from scripts.orchestration import worktree_artifacts as artifacts

    pins = {}
    for stem, command in (
        ("lexicon-manifest", "hydrate-manifest.mjs"),
        ("lexicon-practice-deck", "hydrate-practice-deck.mjs"),
    ):
        pointer = f"site/src/data/{stem}.pointer.json"
        generator = f"site/scripts/{command}"
        if not {pointer, generator} <= tracked:
            continue
        try:
            # Check the index and worktree independently: a staged pointer
            # restored only on disk must not acquire committed provenance.
            for args in (
                ["diff", "--cached", "--quiet", "HEAD", "--", pointer, generator],
                ["diff", "--quiet", "--", pointer, generator],
            ):
                artifacts.safe_git(
                    args, cwd=worktree, env=artifacts._safe_git_env(), capture_output=True, check=True, timeout=30
                )
            committed = artifacts.safe_git(
                ["cat-file", "blob", f"HEAD:{pointer}"],
                cwd=worktree,
                env=artifacts._safe_git_env(),
                capture_output=True,
                check=True,
                timeout=30,
            ).stdout
            walked = artifacts._read_preserved_bytes(worktree / pointer, root=worktree)
            if walked.file_type != "regular" or walked.payload != committed:
                continue
            command_bytes = artifacts.safe_git(
                ["cat-file", "blob", f"HEAD:{generator}"],
                cwd=worktree,
                env=artifacts._safe_git_env(),
                capture_output=True,
                check=True,
                timeout=30,
            ).stdout
            command_file = artifacts._read_preserved_bytes(worktree / generator, root=worktree)
            if command_file.file_type != "regular" or command_file.payload != command_bytes:
                continue
            pointer_data = json.loads(committed)
            if not isinstance(pointer_data, dict):
                continue
            if not str(pointer_data.get("asset_url", "")).startswith(
                "https://github.com/learn-ukrainian/learn-ukrainian.github.io/releases/download/"
            ):
                continue
            if not all(pointer_data.get(key) for key in ("release_tag", "gz_sha256", "gz_bytes")):
                continue
            if not _release_is_recoverable(worktree, stem, pointer_data):
                continue
            if stem == "lexicon-manifest":
                if not all(
                    pointer_data.get(key)
                    for key in (
                        "manifest_version",
                        "manifest_fingerprint",
                        "fingerprint_schema_version",
                    )
                ):
                    continue
                entries = [
                    (
                        "site/src/data/lexicon-manifest.json",
                        pointer_data.get("json_bytes"),
                        pointer_data.get("json_sha256"),
                    )
                ]
            else:
                files = pointer_data.get("files")
                if (
                    pointer_data.get("package_schema_version") != 1
                    or not isinstance(files, list)
                    or len(files) != pointer_data.get("file_count")
                    or not all(pointer_data.get(key) for key in ("deck_version", "package_sha256", "package_bytes"))
                ):
                    continue
                entries = [
                    (f"site/public/lexicon/{item.get('path', '')}", item.get("bytes"), item.get("sha256"))
                    for item in files
                    if isinstance(item, dict)
                ]
                if len(entries) != len(files) or len({name for name, _, _ in entries}) != len(entries):
                    continue
            for name, size, digest in entries:
                if (
                    _RELEASE_OUTPUT.fullmatch(name)
                    and type(size) is int
                    and size >= 0
                    and isinstance(digest, str)
                    and re.fullmatch(r"[0-9a-f]{64}", digest)
                ):
                    pins[name] = (size, digest)
        except (OSError, ValueError, ComponentOpenError, subprocess.SubprocessError):
            # Unverifiable regeneration is ordinary task output, never permission.
            continue
    return pins


def _matches_release_pin(worktree: Path, relative: Path, pin: tuple[int, str]) -> bool:
    """Stream bytes through the existing descriptor walk; never follow a link."""
    from scripts.orchestration import worktree_artifacts as artifacts

    root_fd = artifacts._open_trusted_root(worktree)
    try:
        parent_fd, owned = artifacts._open_parent(root_fd, relative.parts[:-1])
        try:
            fd = os.open(relative.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent_fd)
            try:
                before = os.fstat(fd)
                if not stat.S_ISREG(before.st_mode) or before.st_size != pin[0]:
                    return False
                digest = hashlib.sha256()
                size = 0
                while chunk := os.read(fd, 1024 * 1024):
                    size += len(chunk)
                    if size > pin[0]:
                        return False
                    digest.update(chunk)
                after = os.fstat(fd)
                # Rewalk after hashing: a renamed ancestor or replaced leaf
                # must not lend the old inode's proof to new local output.
                current_parent, current_owned = artifacts._open_parent(root_fd, relative.parts[:-1])
                try:
                    current = os.stat(relative.name, dir_fd=current_parent, follow_symlinks=False)
                finally:
                    if current_owned:
                        os.close(current_parent)
                return (size, digest.hexdigest()) == pin and (
                    before.st_dev,
                    before.st_ino,
                    before.st_size,
                    before.st_mtime_ns,
                    before.st_ctime_ns,
                ) == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns) == (
                    current.st_dev,
                    current.st_ino,
                    current.st_size,
                    current.st_mtime_ns,
                    current.st_ctime_ns,
                )
            finally:
                os.close(fd)
        finally:
            if owned:
                os.close(parent_fd)
    except (OSError, ValueError, ComponentOpenError):
        return False
    finally:
        os.close(root_fd)


# #10519: the issue-stream audit's refresh sidecars (scripts/orchestration/
# issue_stream_audit.py REFRESH_STATE_PATH / REFRESH_LOCK_PATH) are runtime
# state that the next audit run rewrites. Older audit runs wrote them into the
# invoking checkout; exactly these two root-level names are regenerable. The
# size bound keeps unrelated output that merely reuses a name from vanishing.
AUDIT_REFRESH_STATE_FILES = frozenset(
    {
        "batch_state/issue_stream_audit_refresh.json",
        "batch_state/issue_stream_audit_refresh.lock",
    }
)
AUDIT_REFRESH_STATE_MAX_BYTES = 4096
_DATABASE_SUFFIXES = frozenset(
    extension + sidecar
    for extension in (".db", ".sqlite", ".sqlite3", ".db3", ".duckdb", ".mdb")
    for sidecar in ("", "-wal", "-shm", "-journal")
)


def is_regenerable_ignored_path(
    path: str,
    *,
    worktree: Path,
    tracked: set[str],
    ignored: set[str] | None = None,
    release_pins: Mapping[str, tuple[int, str]] | None = None,
) -> bool:
    """Classify regenerable output without traversing any symbolic link.

    A lockfile must be tracked and a local regular file. Environment contents
    without that proof remain output, including caches inside those environments.
    """
    relative = Path(path)
    if relative.is_absolute() or ".." in relative.parts or ".venv" in relative.parts or not relative.parts:
        return False
    if relative.as_posix() in tracked:
        return False
    if ignored is None:
        from scripts.orchestration import worktree_artifacts as artifacts

        ignored = set(artifacts._git_paths(worktree, "--others", "--ignored", "--exclude-standard"))
    if relative.as_posix() not in ignored:
        return False
    # Site candidates require a complete component walk before pattern matching.
    site_tree = relative.parts[:2] in {("site", "dist"), ("site", "public")} or relative.parts[:3] == (
        "site",
        "src",
        "data",
    )
    audit_state = relative.as_posix() in AUDIT_REFRESH_STATE_FILES
    if (
        not site_tree
        and not audit_state
        and not (REGENERABLE_CACHE_DIRECTORIES | {DEPENDENCY_DIRECTORY}) & set(relative.parts)
    ):
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
    if audit_state:
        return stat.S_ISREG(status.st_mode) and status.st_size <= AUDIT_REFRESH_STATE_MAX_BYTES
    if stat.S_ISREG(status.st_mode) and _RELEASE_OUTPUT.fullmatch(relative.as_posix()):
        if release_pins is None:
            release_pins = committed_release_pins(worktree, tracked)
        pin = release_pins.get(relative.as_posix())
        return pin is not None and _matches_release_pin(worktree, relative, pin)
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
