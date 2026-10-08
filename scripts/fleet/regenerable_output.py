"""Regenerable cache/build patterns and delegate's scratch taxonomy (#9828, #10061)."""

from __future__ import annotations

import re
import stat
from pathlib import Path

from scripts.orchestration.worktree_artifacts import REGENERABLE_CACHE_DIRECTORIES

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
    # npm run hydrate:manifest: hydrate-manifest.mjs writes then renames .tmp.
    r"site/src/data/lexicon-manifest\.json(?:\.tmp)?",
    # npm run hydrate:practice: hydrate-practice-deck.mjs stages .json.tmp.
    r"site/public/lexicon/practice-(?:index|lexemes|cloze|stress|classify|paradigm|synonym|heritage|paronym|antonym|homonym)\.(?:A1|A2|B1|B2|C1)\.json(?:\.tmp)?",
    # Repository root: scripts/audit/generate_practice_deck.py writes imperative
    # shards directly (write_shards), without a temporary sibling.
    r"site/public/lexicon/practice-imperative\.(?:A1|A2|B1|B2|C1)\.json",
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
