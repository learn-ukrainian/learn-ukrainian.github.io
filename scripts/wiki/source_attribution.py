"""Resolve stable source attribution metadata for compiled wiki citations."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from .config import PROJECT_ROOT
from .sources_schema import _infer_source_type, normalize_source_filename

DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "sources.db"

_CHUNK_SUFFIX_RE = re.compile(r"(_[cs]\d+)$", re.IGNORECASE)
_TRAILING_DIGITS_RE = re.compile(r"(\d+)$")
_NON_SLUG_RE = re.compile(r"[^0-9A-Za-zА-Яа-яІіЇїЄєҐґ_-]+")
_CORPUS_ALIASES = {
    "textbook_sections": "textbook_sections",
    "textbooks": "textbooks",
    "textbook": "textbooks",
    "modern_literary": "literary_texts",
    "archaic_literary": "literary_texts",
    "literary_texts": "literary_texts",
    "literary": "literary_texts",
    "external": "external_articles",
    "external_articles": "external_articles",
    "external_article": "external_articles",
    "wikipedia": "wikipedia",
    "wiki": "wikipedia",
    "ukrainian_wiki": "ukrainian_wiki",
}


def resolve_chunk_attribution(chunk_id: str, corpus: str) -> dict:
    """Return rich source attribution for a retrieved corpus row."""
    raw_chunk_id = str(chunk_id or "").strip()
    raw_corpus = str(corpus or "").strip()
    normalized_corpus = _CORPUS_ALIASES.get(raw_corpus, raw_corpus)

    if not raw_chunk_id:
        return {
            "file": "unknown",
            "type": "unknown",
            "title": "Unknown source",
        }

    try:
        with sqlite3.connect(str(DEFAULT_DB_PATH)) as conn:
            conn.row_factory = sqlite3.Row
            if normalized_corpus == "textbook_sections":
                attribution = _resolve_textbook_section(conn, raw_chunk_id)
            elif normalized_corpus == "textbooks":
                attribution = _resolve_textbook_chunk(conn, raw_chunk_id)
            elif normalized_corpus == "literary_texts":
                attribution = _resolve_literary_chunk(conn, raw_chunk_id)
            elif normalized_corpus == "external_articles":
                attribution = _resolve_external_chunk(conn, raw_chunk_id)
            elif normalized_corpus == "wikipedia":
                attribution = _resolve_wikipedia_chunk(conn, raw_chunk_id)
            elif normalized_corpus == "ukrainian_wiki":
                attribution = _resolve_ukrainian_wiki_chunk(conn, raw_chunk_id)
            else:
                attribution = None
    except sqlite3.Error:
        attribution = None

    if attribution is not None:
        return attribution

    normalized_file = normalize_source_filename(raw_chunk_id)
    return {
        "file": normalized_file,
        "type": _infer_source_type(normalized_file),
        "title": raw_chunk_id,
    }


def _resolve_textbook_section(conn: sqlite3.Connection, chunk_id: str) -> dict | None:
    section_id = _parse_section_id(chunk_id)
    if section_id is None:
        return None

    row = conn.execute(
        """
        SELECT section_id, source_file, grade, section_title, page_start
        FROM textbook_sections
        WHERE section_id = ?
        """,
        (section_id,),
    ).fetchone()
    if row is None:
        return None

    return {
        "file": f"{normalize_source_filename(str(row['source_file'] or ''))}_s{section_id:04d}",
        "type": "textbook",
        "title": str(row["section_title"] or ""),
        "grade": _maybe_int(row["grade"]),
        "page": _maybe_int(row["page_start"]),
    }


def _resolve_textbook_chunk(conn: sqlite3.Connection, chunk_id: str) -> dict | None:
    row = conn.execute(
        """
        SELECT id, chunk_id, title, source_file, grade, author
        FROM textbooks
        WHERE chunk_id = ?
        LIMIT 1
        """,
        (chunk_id,),
    ).fetchone()
    if row is None:
        return None

    return {
        "file": _build_chunk_file(
            str(row["source_file"] or ""),
            str(row["chunk_id"] or ""),
            row["id"],
        ),
        "type": "textbook",
        "title": str(row["title"] or ""),
        "grade": _maybe_int(row["grade"]),
        "author": _maybe_text(row["author"]),
    }


def _resolve_literary_chunk(conn: sqlite3.Connection, chunk_id: str) -> dict | None:
    row = conn.execute(
        """
        SELECT id, chunk_id, title, source_file, author, work
        FROM literary_texts
        WHERE chunk_id = ?
        LIMIT 1
        """,
        (chunk_id,),
    ).fetchone()
    if row is None:
        return None

    return {
        "file": _build_chunk_file(
            str(row["source_file"] or ""),
            str(row["chunk_id"] or ""),
            row["id"],
        ),
        "type": "literary",
        "title": str(row["work"] or row["title"] or ""),
        "author": _maybe_text(row["author"]),
    }


def _resolve_external_chunk(conn: sqlite3.Connection, chunk_id: str) -> dict | None:
    row = conn.execute(
        """
        SELECT
            id,
            chunk_id,
            url,
            title,
            source_file,
            domain,
            video_id,
            chunk_start_ts,
            chunk_end_ts
        FROM external_articles
        WHERE chunk_id = ?
        LIMIT 1
        """,
        (chunk_id,),
    ).fetchone()
    if row is None:
        return None

    ts_start = _maybe_int(row["chunk_start_ts"])
    url = _maybe_text(row["url"])
    resolved_url = _with_ts_suffix(url, ts_start) if url else None
    domain = _maybe_text(row["domain"])
    file_value = resolved_url or _external_fallback_file(domain, row["id"], row["source_file"])
    return {
        "file": file_value,
        "type": "external",
        "title": str(row["title"] or ""),
        "url": resolved_url or url,
        "domain": domain,
        "video_id": _maybe_text(row["video_id"]),
        "ts_start": ts_start,
        "ts_end": _maybe_int(row["chunk_end_ts"]),
    }


def _resolve_wikipedia_chunk(conn: sqlite3.Connection, chunk_id: str) -> dict | None:
    row = conn.execute(
        """
        SELECT title, url
        FROM wikipedia
        WHERE title = ?
        LIMIT 1
        """,
        (chunk_id,),
    ).fetchone()
    if row is None:
        return None

    title = str(row["title"] or "")
    return {
        "file": f"wikipedia/{title}",
        "type": "wikipedia",
        "title": title,
        "url": _maybe_text(row["url"]),
    }


def _resolve_ukrainian_wiki_chunk(conn: sqlite3.Connection, chunk_id: str) -> dict | None:
    row = conn.execute(
        """
        SELECT article_slug, article_title, section_path
        FROM ukrainian_wiki
        WHERE passage_id = ?
        LIMIT 1
        """,
        (chunk_id,),
    ).fetchone()
    if row is None:
        return None

    article_slug = str(row["article_slug"] or "")
    section_path = str(row["section_path"] or "")
    section_suffix = _slugify(section_path) or "root"
    return {
        "file": f"ukrainian_wiki/{article_slug}_{section_suffix}",
        "type": "ukrainian_wiki",
        "title": str(row["article_title"] or ""),
        "section_path": section_path or None,
    }


def _parse_section_id(chunk_id: str) -> int | None:
    candidate = str(chunk_id or "").strip()
    if candidate.startswith(("S", "s")):
        candidate = candidate[1:]
    try:
        return int(candidate)
    except ValueError:
        return None


def _build_chunk_file(source_file: str, chunk_id: str, row_id: object) -> str:
    source_slug = normalize_source_filename(source_file)
    suffix_match = _CHUNK_SUFFIX_RE.search(chunk_id)
    if suffix_match:
        return f"{source_slug}{suffix_match.group(1).lower()}"

    trailing_digits = _TRAILING_DIGITS_RE.search(chunk_id)
    if trailing_digits:
        return f"{source_slug}_c{int(trailing_digits.group(1)):04d}"

    if row_id is not None:
        return f"{source_slug}_c{int(row_id):04d}"
    return source_slug


def _with_ts_suffix(url: str | None, ts_start: int | None) -> str | None:
    if not url:
        return None
    if ts_start is None:
        return url
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}t={ts_start}s"


def _external_fallback_file(domain: str | None, row_id: object, source_file: object) -> str:
    base = _slugify(domain or str(source_file or "")) or "external"
    suffix = f"{int(row_id):04d}" if row_id is not None else "unknown"
    return f"{base}_{suffix}"


def _slugify(value: str) -> str:
    slug = _NON_SLUG_RE.sub("-", str(value or "").strip())
    slug = re.sub(r"-{2,}", "-", slug).strip("-_")
    return slug


def _maybe_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _maybe_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None
