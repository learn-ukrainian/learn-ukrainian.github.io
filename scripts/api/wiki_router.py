"""
Wiki compilation API router.

Mounts under /api/wiki in main.py. Provides read-only observability into:
- Compilation status (progress.db)
- Per-article quality gate results
- Build log events
- Source database inventory

Issue: #1171
"""
from __future__ import annotations

import sqlite3
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from .config import LEVELS
from .monitor_context import MonitorContext, get_ctx, resolve_context
from .state_helpers import cache_get, cache_set

# scripts/wiki is not a package, so we add the scripts/ root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import wiki.config as wiki_config
import wiki.quality_gate as wiki_quality
import wiki.sources as wiki_sources
import wiki.state as wiki_state

try:
    from path_safety import safe_join  # scripts/ on sys.path (test sys.path-hack)
except ImportError:
    from ..path_safety import safe_join  # scripts.api package import (production)

router = APIRouter(tags=["wiki"])

_TABLE_NAMES = [
    "textbooks",
    "literary",
    "literary_texts",
    "external",
    "external_articles",
    "wikipedia",
    "sum11",
    "grinchenko",
    "balla_en_uk",
    "dmklinger_uk_en",
    "ukrajinet",
    "wiktionary",
    "frazeolohichnyi",
    "puls_cefr",
    "style_guide",
]
_WORD_COUNT_WORKERS = 4




def _wiki_dir(ctx: MonitorContext | None = None) -> Path:
    """Return the wiki tree for the serving context.

    Fixture contexts own a project-local wiki tree.  Plain production callers
    retain the compiler's configured path, which is also the seam used by the
    existing wiki tests and deployment redirections.
    """
    resolved_ctx = resolve_context(ctx)
    if resolved_ctx.root is not None:
        return resolved_ctx.roots.project_root / "wiki"
    return Path(wiki_config.WIKI_DIR)


def _known_tracks(ctx: MonitorContext) -> list[str]:
    plan_root = ctx.roots.curriculum_root / "plans"
    configured = tuple(level["id"] for level in LEVELS)
    cache_key = f"wiki:known_tracks:{plan_root.resolve()}:{configured!r}"

    def build() -> list[str]:
        existing = {path.name for path in plan_root.iterdir() if path.is_dir()} if plan_root.exists() else set()
        ordered = [track for track in configured if track in existing]
        extras = sorted(existing - set(configured))
        return ordered + extras

    return ctx.runtime.get_or_create_derived(cache_key, build)


def _track_exists(track: str, ctx: MonitorContext) -> bool:
    return track in _known_tracks(ctx)


def _safe_join(base: Path, *parts: str | Path) -> Path | None:
    try:
        return safe_join(base, *parts)
    except ValueError:
        return None


def _ensure_track_exists(track: str, ctx: MonitorContext) -> None:
    if not _track_exists(track, ctx):
        raise HTTPException(status_code=404, detail=f"Track not found: {track}")


def _track_slugs(track: str) -> list[str]:
    try:
        return wiki_sources.list_discovery_slugs_readonly(track)
    except Exception:
        return []


def _build_article_candidates(wiki_dir: Path) -> dict[str, list[dict[str, Any]]]:
    progress = wiki_state.load_progress().get("articles", {})
    candidates: dict[str, list[dict[str, Any]]] = {}

    for progress_key, progress_info in progress.items():
        rel_path = f"{progress_key}.md"
        slug = Path(rel_path).stem
        candidates.setdefault(slug, []).append({
            "path": rel_path,
            "progress_key": progress_key,
            "compiled_at": progress_info.get("compiled_at"),
            "source_count": progress_info.get("source_count"),
            "word_count": progress_info.get("word_count"),
            "from_progress": True,
        })

    known_paths = {candidate["path"] for rows in candidates.values() for candidate in rows}
    for md_file in sorted(wiki_dir.rglob("*.md")):
        rel = md_file.relative_to(wiki_dir)
        if any(part.startswith(".") for part in rel.parts):
            continue
        if rel.name == "index.md" or rel.name.startswith("."):
            continue
        rel_path = str(rel)
        if rel_path in known_paths:
            continue
        slug = rel.stem
        progress_key = rel_path.removesuffix(".md")
        candidates.setdefault(slug, []).append({
            "path": rel_path,
            "progress_key": progress_key,
            "compiled_at": None,
            "source_count": None,
            "word_count": None,
            "from_progress": False,
        })

    return candidates


def _list_article_candidates(
    ctx: MonitorContext | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Return one context-scoped snapshot of the wiki article index."""
    resolved_ctx = resolve_context(ctx)
    wiki_dir = _wiki_dir(resolved_ctx)
    state_dir = Path(wiki_state.WIKI_STATE_DIR)
    cache_key = f"wiki:article_candidates:{wiki_dir.resolve()}:{state_dir.resolve()}"
    return resolved_ctx.runtime.get_or_create_derived(
        cache_key,
        lambda: _build_article_candidates(wiki_dir),
    )


def _matches_track_domain(track: str, rel_path: str) -> bool:
    domains = wiki_config.TRACK_DOMAINS.get(track, [])
    if not domains:
        return True
    return any(rel_path.startswith(f"{domain}/") for domain in domains)


def _resolve_article(
    track: str,
    slug: str,
    candidates_by_slug: dict[str, list[dict[str, Any]]] | None = None,
    ctx: MonitorContext | None = None,
) -> dict[str, Any] | None:
    article_candidates = (
        _list_article_candidates(ctx) if candidates_by_slug is None else candidates_by_slug
    )
    candidates = article_candidates.get(slug, [])
    if not candidates:
        return None

    domain_matches = [candidate for candidate in candidates if _matches_track_domain(track, candidate["path"])]
    preferred = domain_matches or candidates
    return sorted(preferred, key=lambda item: item["path"])[0]


def _read_article_metrics(path: Path, cache: dict[Path, dict[str, Any]]) -> dict[str, Any]:
    cached = cache.get(path)
    if cached is not None:
        return cached

    text = path.read_text(encoding="utf-8")
    data = {
        "text": text,
        "word_count": len(text.split()),
        "preview": text[:500],
    }
    cache[path] = data
    return data


def _count_article_words(path: Path) -> tuple[Path, int]:
    try:
        return path, len(path.read_bytes().split())
    except OSError:
        return path, 0


def _read_article_word_count(path: Path, cache: dict[Path, int]) -> int:
    cached = cache.get(path)
    if cached is not None:
        return cached

    _, word_count = _count_article_words(path)
    cache[path] = word_count
    return word_count


def _preload_article_word_counts(
    candidates_by_slug: dict[str, list[dict[str, Any]]],
    cache: dict[Path, int],
    wiki_dir: Path | None = None,
) -> None:
    if wiki_dir is None:
        wiki_dir = Path(wiki_config.WIKI_DIR)
    paths: list[Path] = []
    seen: set[Path] = set()
    for candidates in candidates_by_slug.values():
        for article in candidates:
            if article.get("word_count") is not None or not article.get("from_progress"):
                continue
            article_path = _safe_join(wiki_dir, article["path"])
            if not article_path or not article_path.exists() or article_path in seen:
                continue
            seen.add(article_path)
            paths.append(article_path)

    if len(paths) < 16:
        for path in paths:
            _read_article_word_count(path, cache)
        return

    with ThreadPoolExecutor(max_workers=_WORD_COUNT_WORKERS) as executor:
        for path, word_count in executor.map(_count_article_words, paths):
            cache[path] = word_count


def _source_count(track: str, slug: str) -> int:
    try:
        data = wiki_sources.gather_discovery_sources_readonly(track, slug)
    except Exception:
        return 0

    if not data or data.get("error"):
        return 0

    return (
        len(data.get("literary_chunks", []))
        + len(data.get("textbook_chunks", []))
        + len(data.get("literary_files", []))
    )


def _track_status_rows(
    track: str,
    candidates_by_slug: dict[str, list[dict[str, Any]]] | None = None,
    word_count_cache: dict[Path, int] | None = None,
    ctx: MonitorContext | None = None,
) -> list[dict[str, Any]]:
    _ensure_track_exists(track, ctx)
    slugs = _track_slugs(track)
    article_candidates = (
        _list_article_candidates(ctx) if candidates_by_slug is None else candidates_by_slug
    )
    rows = []

    for slug in slugs:
        article = _resolve_article(track, slug, article_candidates, ctx=ctx)
        article_path = _safe_join(_wiki_dir(ctx), article["path"]) if article else None
        compiled = bool(article_path and article_path.exists())
        word_count = 0

        if compiled:
            progress_word_count = article.get("word_count")
            if progress_word_count is None and article.get("from_progress") and article_path:
                cache = word_count_cache if word_count_cache is not None else {}
                word_count = _read_article_word_count(article_path, cache)
            else:
                word_count = int(progress_word_count or 0)

        rows.append({
            "slug": slug,
            "compiled": compiled,
            "word_count": word_count,
            "compiled_at": article.get("compiled_at") if article else None,
            "source_count": article.get("source_count") if article else 0,
        })

    return rows


@router.get("/status")
async def wiki_status(ctx: MonitorContext = Depends(get_ctx)):
    """Per-track wiki compilation status."""
    known_tracks = _known_tracks(ctx)
    cache_key = f"wiki_status_{_wiki_dir(ctx)}_" + ",".join(known_tracks)
    cached = cache_get(cache_key, ttl=60.0)
    if cached is not None:
        return cached

    article_candidates = _list_article_candidates(ctx)
    word_count_cache: dict[Path, int] = {}
    _preload_article_word_counts(article_candidates, word_count_cache, _wiki_dir(ctx))
    tracks = []

    for track in known_tracks:
        slugs = _track_slugs(track)
        if not slugs:
            continue
        modules = _track_status_rows(track, article_candidates, word_count_cache, ctx=ctx)
        total = len(modules)
        compiled = sum(1 for module in modules if module["compiled"])
        total_words = sum(module["word_count"] for module in modules)
        tracks.append({
            "track": track,
            "total": total,
            "compiled": compiled,
            "pct": round(compiled / total * 100, 1) if total else 0,
            "total_words": total_words,
        })

    result = {"tracks": tracks}
    cache_set(cache_key, result)
    return result


@router.get("/status/{track}")
async def wiki_status_track(track: str, ctx: MonitorContext = Depends(get_ctx)):
    """Per-module wiki compilation status for one track."""
    cache_key = f"wiki_status_track_{track}_{_wiki_dir(ctx)}"
    cached = cache_get(cache_key, ttl=60.0)
    if cached is not None:
        return cached
    result = _track_status_rows(track, ctx=ctx)
    cache_set(cache_key, result)
    return result


@router.get("/article/{track}/{slug}")
async def wiki_article(track: str, slug: str, ctx: MonitorContext = Depends(get_ctx)):
    """Single article metadata plus a short preview."""
    _ensure_track_exists(track, ctx)
    if slug not in _track_slugs(track):
        raise HTTPException(status_code=404, detail=f"Article not found: {track}/{slug}")

    article = _resolve_article(track, slug, ctx=ctx)
    source_count = article.get("source_count") if article else _source_count(track, slug)

    if not article:
        return {
            "track": track,
            "slug": slug,
            "compiled": False,
            "path": None,
            "word_count": 0,
            "preview": None,
            "source_count": source_count,
            "compiled_at": None,
        }

    article_path = _safe_join(_wiki_dir(ctx), article["path"])
    if article_path is None:
        return {
            "track": track,
            "slug": slug,
            "compiled": False,
            "path": None,
            "word_count": 0,
            "preview": None,
            "source_count": source_count,
            "compiled_at": article.get("compiled_at"),
        }
    if not article_path.exists():
        return {
            "track": track,
            "slug": slug,
            "compiled": False,
            "path": str(article_path),
            "word_count": 0,
            "preview": None,
            "source_count": source_count,
            "compiled_at": article.get("compiled_at"),
        }

    metrics = _read_article_metrics(article_path, {})
    return {
        "track": track,
        "slug": slug,
        "compiled": True,
        "path": str(article_path),
        "word_count": metrics["word_count"],
        "preview": metrics["preview"],
        "source_count": article.get("source_count") or source_count,
        "compiled_at": article.get("compiled_at"),
    }


@router.get("/quality-gate")
async def wiki_quality_gate(ctx: MonitorContext = Depends(get_ctx)):
    """Aggregate wiki quality gate issues for all tracks."""
    return {track: wiki_quality.scan_track(track) for track in _known_tracks(ctx)}


@router.get("/quality-gate/{track}")
async def wiki_quality_gate_track(track: str, ctx: MonitorContext = Depends(get_ctx)):
    """Quality gate issues for one track."""
    _ensure_track_exists(track, ctx)
    return {track: wiki_quality.scan_track(track)}


@router.get("/build-log")
async def wiki_build_log(
    track: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    ctx: MonitorContext = Depends(get_ctx),
):
    """Recent wiki build log events."""
    if track is not None:
        _ensure_track_exists(track, ctx)
    events = wiki_state.read_log(track=track, last_n=limit)
    return {"events": events[-limit:]}


@router.get("/sources")
async def wiki_sources_inventory(ctx: MonitorContext = Depends(get_ctx)):
    """Row counts for the sources SQLite database."""
    handle = ctx.stores.sources_db
    if handle is None or not handle.path.exists():
        return {"tables": [], "total_entries": 0}

    tables = []
    total_entries = 0

    with handle.connect() as conn:
        for table_name in _TABLE_NAMES:
            try:
                row_count = conn.execute(f"SELECT count(*) FROM {table_name}").fetchone()[0]
            except sqlite3.Error:
                continue
            tables.append({"name": table_name, "row_count": row_count})
            total_entries += row_count

    return {"tables": tables, "total_entries": total_entries}


@router.get("/sources/{track}/{slug}")
async def wiki_sources_module(
    track: str, slug: str, ctx: MonitorContext = Depends(get_ctx)
):
    """Source availability for a single module."""
    _ensure_track_exists(track, ctx)
    if slug not in _track_slugs(track):
        raise HTTPException(status_code=404, detail=f"Article not found: {track}/{slug}")

    try:
        data = wiki_sources.gather_discovery_sources_readonly(track, slug)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=f"Discovery not found: {track}/{slug}") from exc

    if not data or data.get("error"):
        raise HTTPException(status_code=404, detail=f"Discovery not found: {track}/{slug}")

    return data
