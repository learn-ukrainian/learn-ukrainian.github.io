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
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from .config import CURRICULUM_ROOT, LEVELS

# scripts/wiki is not a package, so we add the scripts/ root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import wiki.config as wiki_config
import wiki.quality_gate as wiki_quality
import wiki.sources as wiki_sources
import wiki.state as wiki_state

router = APIRouter(tags=["wiki"])

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCES_DB_PATH = PROJECT_ROOT / "data" / "sources.db"
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


def _known_tracks() -> list[str]:
    plan_root = CURRICULUM_ROOT / "plans"
    configured = [level["id"] for level in LEVELS]
    existing = {path.name for path in plan_root.iterdir() if path.is_dir()} if plan_root.exists() else set()
    ordered = [track for track in configured if track in existing]
    extras = sorted(existing - set(configured))
    return ordered + extras


def _track_exists(track: str) -> bool:
    return track in _known_tracks() or (CURRICULUM_ROOT / "plans" / track).exists()


def _ensure_track_exists(track: str) -> None:
    if not _track_exists(track):
        raise HTTPException(status_code=404, detail=f"Track not found: {track}")


def _track_slugs(track: str) -> list[str]:
    try:
        return wiki_sources.list_discovery_slugs(track)
    except Exception:
        return []


def _list_article_candidates() -> dict[str, list[dict[str, Any]]]:
    progress = wiki_state.load_progress().get("articles", {})
    candidates: dict[str, list[dict[str, Any]]] = {}

    for article in wiki_state.list_wiki_articles():
        rel_path = article["path"]
        slug = Path(rel_path).stem
        progress_key = rel_path.removesuffix(".md")
        progress_info = progress.get(progress_key, {})
        candidates.setdefault(slug, []).append({
            "path": rel_path,
            "progress_key": progress_key,
            "compiled_at": progress_info.get("compiled_at"),
            "source_count": progress_info.get("source_count"),
        })

    return candidates


def _matches_track_domain(track: str, rel_path: str) -> bool:
    domains = wiki_config.TRACK_DOMAINS.get(track, [])
    if not domains:
        return True
    return any(rel_path.startswith(f"{domain}/") for domain in domains)


def _resolve_article(track: str, slug: str) -> dict[str, Any] | None:
    candidates = _list_article_candidates().get(slug, [])
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


def _source_count(track: str, slug: str) -> int:
    try:
        data = wiki_sources.gather_discovery_sources(track, slug)
    except Exception:
        return 0

    if not data or data.get("error"):
        return 0

    return (
        len(data.get("literary_chunks", []))
        + len(data.get("textbook_chunks", []))
        + len(data.get("literary_files", []))
    )


def _track_status_rows(track: str) -> list[dict[str, Any]]:
    _ensure_track_exists(track)
    slugs = _track_slugs(track)
    word_cache: dict[Path, dict[str, Any]] = {}
    rows = []

    for slug in slugs:
        article = _resolve_article(track, slug)
        article_path = wiki_config.WIKI_DIR / article["path"] if article else None
        compiled = bool(article_path and article_path.exists())
        word_count = 0

        if compiled and article_path is not None:
            word_count = _read_article_metrics(article_path, word_cache)["word_count"]

        rows.append({
            "slug": slug,
            "compiled": compiled,
            "word_count": word_count,
            "compiled_at": article.get("compiled_at") if article else None,
            "source_count": _source_count(track, slug),
        })

    return rows


@router.get("/status")
async def wiki_status():
    """Per-track wiki compilation status."""
    wiki_state.get_status_summary()
    tracks = []

    for track in _known_tracks():
        slugs = _track_slugs(track)
        if not slugs:
            continue
        modules = _track_status_rows(track)
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

    return {"tracks": tracks}


@router.get("/status/{track}")
async def wiki_status_track(track: str):
    """Per-module wiki compilation status for one track."""
    return _track_status_rows(track)


@router.get("/article/{track}/{slug}")
async def wiki_article(track: str, slug: str):
    """Single article metadata plus a short preview."""
    _ensure_track_exists(track)
    if slug not in _track_slugs(track):
        raise HTTPException(status_code=404, detail=f"Article not found: {track}/{slug}")

    article = _resolve_article(track, slug)
    source_count = _source_count(track, slug)

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

    article_path = wiki_config.WIKI_DIR / article["path"]
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
async def wiki_quality_gate():
    """Aggregate wiki quality gate issues for all tracks."""
    return {track: wiki_quality.scan_track(track) for track in _known_tracks()}


@router.get("/quality-gate/{track}")
async def wiki_quality_gate_track(track: str):
    """Quality gate issues for one track."""
    _ensure_track_exists(track)
    return {track: wiki_quality.scan_track(track)}


@router.get("/build-log")
async def wiki_build_log(
    track: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
):
    """Recent wiki build log events."""
    if track is not None:
        _ensure_track_exists(track)
    events = wiki_state.read_log(track=track, last_n=limit)
    return {"events": events[-limit:]}


@router.get("/sources")
async def wiki_sources_inventory():
    """Row counts for the sources SQLite database."""
    if not SOURCES_DB_PATH.exists():
        return {"tables": [], "total_entries": 0}

    tables = []
    total_entries = 0

    with sqlite3.connect(str(SOURCES_DB_PATH)) as conn:
        for table_name in _TABLE_NAMES:
            try:
                row_count = conn.execute(f"SELECT count(*) FROM {table_name}").fetchone()[0]
            except sqlite3.Error:
                continue
            tables.append({"name": table_name, "row_count": row_count})
            total_entries += row_count

    return {"tables": tables, "total_entries": total_entries}


@router.get("/sources/{track}/{slug}")
async def wiki_sources_module(track: str, slug: str):
    """Source availability for a single module."""
    _ensure_track_exists(track)
    if slug not in _track_slugs(track):
        raise HTTPException(status_code=404, detail=f"Article not found: {track}/{slug}")

    try:
        data = wiki_sources.gather_discovery_sources(track, slug)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=f"Discovery not found: {track}/{slug}") from exc

    if not data or data.get("error"):
        raise HTTPException(status_code=404, detail=f"Discovery not found: {track}/{slug}")

    return data
