"""SQLite-backed compatibility queries for older RAG callers.

The project corpus now lives in ``data/sources.db`` and is queried through
``scripts.wiki.sources_db``.  This module keeps the old public function names
used by pipeline/debug scripts without retaining the retired vector DB client.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

try:
    from wiki import sources_db
except ImportError:  # pragma: no cover - package import fallback
    from scripts.wiki import sources_db


def _keywords(query: str) -> set[str]:
    """Extract Ukrainian/Latin tokens suitable for FTS helper APIs."""
    return {tok.lower() for tok in re.findall(r"[\w'’ʼ-]+", query, flags=re.UNICODE)}


def _score(row: dict[str, Any]) -> float:
    raw = row.get("_kw_score", row.get("score", 0.0))
    try:
        return float(raw)
    except (TypeError, ValueError):
        return 0.0


def _text_hit(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "score": _score(row),
        "chunk_id": row.get("chunk_id") or str(row.get("id", "")),
        "text": row.get("text", ""),
        "section_title": row.get("section_title") or row.get("title", ""),
        "grade": row.get("grade", 0) or 0,
        "author": row.get("author_uk") or row.get("author", ""),
        "page": row.get("page_start", ""),
        "trust_tier": row.get("trust_tier", 0) or 0,
        "source_type": row.get("source_type", "textbook"),
        "source_file": row.get("source_file", ""),
        "subject": row.get("subject", ""),
    }


def _literary_hit(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "score": _score(row),
        "chunk_id": row.get("chunk_id") or str(row.get("id", "")),
        "text": row.get("text", ""),
        "section_title": row.get("title", ""),
        "author": row.get("author", ""),
        "work": row.get("work") or row.get("title", ""),
        "work_id": row.get("work_id", ""),
        "year": row.get("year", ""),
        "genre": row.get("genre", ""),
        "language_period": row.get("language_period", ""),
        "source_url": row.get("source_url", ""),
        "source_type": row.get("source_type", "literary"),
        "source_file": row.get("source_file", ""),
    }


def build_filter(
    grade: int | None = None,
    subject: str | None = None,
    trust_tier: int | None = None,
    author: str | None = None,
) -> dict[str, Any]:
    """Return a plain compatibility filter descriptor for tests/debug callers."""
    return {
        key: value
        for key, value in {
            "grade": grade,
            "subject": subject,
            "trust_tier": trust_tier,
            "author": author,
        }.items()
        if value is not None
    }


def search_text(
    query: str,
    grade: int | None = None,
    subject: str | None = None,
    trust_tier: int | None = None,
    limit: int = 5,
    rerank: bool = False,
) -> list[dict[str, Any]]:
    """Search textbook chunks through SQLite FTS5."""
    del rerank
    canonical_subject = sources_db.normalize_subject_slug(subject)
    rows = sources_db.search_textbooks(
        _keywords(query),
        max_total=max(limit * 3, limit),
        subject=canonical_subject,
    )
    hits = [_text_hit(row) for row in rows]
    if grade is not None:
        hits = [hit for hit in hits if hit.get("grade") == grade]
    if subject and canonical_subject is None:
        subject_l = subject.lower()
        hits = [
            hit
            for hit in hits
            if subject_l in str(hit.get("source_file", "")).lower()
            or subject_l in str(hit.get("section_title", "")).lower()
        ]
    if trust_tier is not None:
        hits = [hit for hit in hits if hit.get("trust_tier") == trust_tier]
    return hits[:limit]


def search_literary(
    query: str,
    work: str | None = None,
    genre: str | None = None,
    period: str | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Search literary chunks through SQLite FTS5."""
    rows = sources_db.search_literary(_keywords(query), max_total=max(limit * 3, limit))
    hits = [_literary_hit(row) for row in rows]
    if work:
        work_l = work.lower()
        hits = [hit for hit in hits if work_l in str(hit.get("work", "")).lower()]
    if genre:
        genre_l = genre.lower()
        hits = [hit for hit in hits if genre_l in str(hit.get("genre", "")).lower()]
    if period:
        period_l = period.lower()
        hits = [
            hit
            for hit in hits
            if period_l in str(hit.get("language_period", "")).lower()
        ]
    return hits[:limit]


def get_full_text(work: str, max_chars: int = 50_000) -> dict[str, Any]:
    """Return concatenated literary text snippets for a work search term."""
    hits = search_literary(work, work=work, limit=200)
    if not hits:
        hits = search_literary(work, limit=200)
    text = "\n\n".join(hit.get("text", "") for hit in hits if hit.get("text"))
    truncated = len(text) > max_chars
    if truncated:
        text = text[:max_chars] + "\n\n[... truncated character limit ...]"
    first = hits[0] if hits else {}
    return {
        "work": first.get("work", work),
        "author": first.get("author", ""),
        "year": first.get("year", ""),
        "genre": first.get("genre", ""),
        "language_period": first.get("language_period", ""),
        "text": text,
        "chunk_count": len(hits),
        "truncated": truncated,
    }


def search_images(
    query: str,
    grade: int | None = None,
    teaching_value: str | None = None,
    subject: str | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Image vector search was retired with the vector DB backend."""
    del query, grade, teaching_value, subject, limit
    return []


def get_chunk_context(chunk_id: str, window: int = 2) -> list[dict[str, Any]]:
    """Return nearby textbook chunks from SQLite by chunk id when available."""
    db_path = sources_db.SOURCES_DB_PATH
    if not db_path.exists():
        return []
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT source_file, chunk_id FROM textbooks WHERE chunk_id = ?",
            (chunk_id,),
        ).fetchone()
        if row is None:
            return []
        rows = conn.execute(
            """
            SELECT chunk_id, title, text
            FROM textbooks
            WHERE source_file = ?
            ORDER BY id
            """,
            (row["source_file"],),
        ).fetchall()
    ids = [r["chunk_id"] for r in rows]
    try:
        idx = ids.index(chunk_id)
    except ValueError:
        return []
    selected = rows[max(0, idx - window) : idx + window + 1]
    return [
        {
            "chunk_id": r["chunk_id"],
            "text": r["text"],
            "section_title": r["title"],
            "is_target": r["chunk_id"] == chunk_id,
        }
        for r in selected
    ]


def search_dictionary(
    query: str,
    collection: str,
    limit: int = 5,
    rerank: bool = True,
) -> list[dict[str, Any]]:
    """Search dictionary/reference tables through SQLite helpers."""
    del rerank
    collection = collection.lower()
    if collection in {"sum11", "sum", "definitions"}:
        rows = sources_db.search_definitions(query, limit=limit)
    elif collection in {"grinchenko", "grinchenko_dict", "grinchenko_1907"}:
        rows = sources_db.search_grinchenko_1907(query, limit=limit)
    elif collection in {"style_guide", "style"}:
        rows = sources_db.search_style_guide(query, limit=limit)
    elif collection in {"puls_cefr", "cefr"}:
        rows = sources_db.query_cefr_level(query, limit=limit)
    elif collection in {"frazeolohichnyi", "idioms"}:
        rows = sources_db.search_idioms(query, limit=limit)
    elif collection in {"ukrajinet", "synonyms"}:
        rows = sources_db.search_synonyms(query, limit=limit)
    elif collection in {"esum", "etymology"}:
        rows = sources_db.search_esum(query, limit=limit)
    else:
        rows = sources_db.search_sources(query, track="a1", limit=limit)

    hits: list[dict[str, Any]] = []
    for row in rows[:limit]:
        text = row.get("text") or row.get("definition") or row.get("guideword") or ""
        hits.append(
            {
                "score": _score(row),
                "text": text,
                "word": row.get("word", query),
                "collection": collection,
                "source": row.get("source", ""),
                "metadata": row,
            }
        )
    return hits


def collection_stats() -> dict[str, dict[str, Any]]:
    """Return SQLite source database status."""
    try:
        total = sources_db.source_count()
        tables = sources_db.list_tables()
    except FileNotFoundError:
        return {"sources_db": {"error": "data/sources.db not found"}}
    return {
        "sources_db": {
            "points_count": total,
            "tables": tables,
            "status": "ok",
        }
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Query SQLite source corpus")
    subparsers = parser.add_subparsers(dest="command", required=True)

    text_parser = subparsers.add_parser("text", help="Search textbook chunks")
    text_parser.add_argument("query")
    text_parser.add_argument("--grade", type=int)
    text_parser.add_argument("--subject")
    text_parser.add_argument("--trust-tier", type=int)
    text_parser.add_argument("--limit", type=int, default=5)

    lit_parser = subparsers.add_parser("literary", help="Search literary texts")
    lit_parser.add_argument("query")
    lit_parser.add_argument("--work")
    lit_parser.add_argument("--genre")
    lit_parser.add_argument("--period")
    lit_parser.add_argument("--limit", type=int, default=5)

    dict_parser = subparsers.add_parser("dict", help="Search dictionary/reference data")
    dict_parser.add_argument("collection")
    dict_parser.add_argument("query")
    dict_parser.add_argument("--limit", type=int, default=5)

    full_parser = subparsers.add_parser("full-text", help="Concatenate literary text")
    full_parser.add_argument("work")
    full_parser.add_argument("--max-chars", type=int, default=50_000)

    subparsers.add_parser("stats", help="Source table counts")

    args = parser.parse_args()
    if args.command == "text":
        result = search_text(
            args.query,
            grade=args.grade,
            subject=args.subject,
            trust_tier=args.trust_tier,
            limit=args.limit,
        )
    elif args.command == "literary":
        result = search_literary(
            args.query,
            work=args.work,
            genre=args.genre,
            period=args.period,
            limit=args.limit,
        )
    elif args.command == "dict":
        result = search_dictionary(args.query, args.collection, limit=args.limit)
    elif args.command == "full-text":
        result = get_full_text(args.work, max_chars=args.max_chars)
    else:
        result = collection_stats()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
