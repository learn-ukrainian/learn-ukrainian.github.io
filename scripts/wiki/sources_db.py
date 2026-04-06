"""SQLite FTS5 interface for ALL source content (textbooks + external articles).

Provides:
- search_sources() — FTS5 keyword search across all content
- search_textbooks() — FTS5 search filtered to textbook chunks only
- search_external() — FTS5 search filtered to external articles only
- lookup_by_url() — exact URL lookup for YAML-mapped resources
"""

import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCES_DB_PATH = PROJECT_ROOT / "data" / "external_articles" / "sources.db"

_conn: sqlite3.Connection | None = None


def _get_conn() -> sqlite3.Connection:
    """Get or create a cached database connection."""
    global _conn
    if _conn is None:
        if not SOURCES_DB_PATH.exists():
            raise FileNotFoundError(
                f"Sources database not found at {SOURCES_DB_PATH}. "
                "Run: .venv/bin/python scripts/wiki/build_sources_db.py"
            )
        _conn = sqlite3.connect(str(SOURCES_DB_PATH), check_same_thread=False)
        _conn.row_factory = sqlite3.Row
    return _conn


def _build_fts_query(keywords: set[str], min_len: int = 3) -> str | None:
    """Build FTS5 MATCH query from keywords. Returns None if no valid terms."""
    terms = [f'"{kw}"' for kw in keywords if len(kw) >= min_len]
    if not terms:
        return None
    return " OR ".join(terms)


def _kw_score(text: str, title: str, keywords: set[str]) -> int:
    """Count keyword hits using space-padded matching."""
    searchable = f" {title} {text} ".lower()
    return sum(1 for w in keywords if f" {w} " in searchable)


def search_sources(
    ukr_keywords: set[str],
    source_type: str | None = None,
    max_total: int = 40,
    exclude_urls: set[str] | None = None,
) -> list[dict]:
    """Search all sources using FTS5 full-text search.

    Args:
        ukr_keywords: Ukrainian keywords to search for
        source_type: Filter by "textbook" or "external" (None = all)
        max_total: Maximum results to return
        exclude_urls: URLs to skip (for dedup with YAML-mapped)

    Returns chunk dicts: {text, chunk_id, source_type, _kw_score, ...}
    """
    if not ukr_keywords:
        return []

    try:
        conn = _get_conn()
    except FileNotFoundError:
        return []

    fts_query = _build_fts_query(ukr_keywords)
    if not fts_query:
        return []

    skip_urls = exclude_urls or set()

    # Build SQL with optional source_type filter
    type_filter = "AND s.source_type = ?" if source_type else ""
    params: list = [fts_query, max_total * 3]
    if source_type:
        params = [fts_query, source_type, max_total * 3]

    rows = conn.execute(
        f"""SELECT s.chunk_id, s.url, s.title, s.text, s.source_type,
                   s.source_file, s.grade, s.author, s.domain,
                   bm25(sources_fts, 5.0, 1.0) AS rank
            FROM sources_fts
            JOIN sources s ON s.id = sources_fts.rowid
            WHERE sources_fts MATCH ?
            {type_filter}
            ORDER BY rank
            LIMIT ?""",
        params,
    ).fetchall()

    chunks: list[dict] = []
    for row in rows:
        if len(chunks) >= max_total:
            break
        url = row["url"]
        if url and url in skip_urls:
            continue

        title = row["title"]
        text = row["text"]
        score = _kw_score(text, title, ukr_keywords)

        chunk = {
            "text": text,
            "chunk_id": row["chunk_id"],
            "source_type": row["source_type"],
            "source_file": row["source_file"],
            "_kw_score": score,
        }

        # Add metadata based on source type
        if row["source_type"] == "textbook":
            chunk["grade"] = row["grade"]
            chunk["author"] = row["author"]
            chunk["section_title"] = title
        else:
            chunk["url"] = url
            chunk["domain"] = row["domain"]
            chunk["title"] = title
            # Format external articles for the compiler prompt
            chunk["text"] = (
                f"External article: {title}\n"
                f"Source: {row['domain'] or row['source_file']}\n"
                f"URL: {url}\n\n"
                f"{text}"
            )[:8000]

        chunks.append(chunk)

    return chunks


def search_textbooks(ukr_keywords: set[str], max_total: int = 40) -> list[dict]:
    """Search textbook chunks only."""
    return search_sources(ukr_keywords, source_type="textbook", max_total=max_total)


def search_external(
    ukr_keywords: set[str],
    max_total: int = 10,
    exclude_urls: set[str] | None = None,
) -> list[dict]:
    """Search external articles only."""
    return search_sources(
        ukr_keywords, source_type="external",
        max_total=max_total, exclude_urls=exclude_urls,
    )


def lookup_by_url(url: str) -> dict | None:
    """Look up an article by URL. Handles www/non-www variants."""
    try:
        conn = _get_conn()
    except FileNotFoundError:
        return None

    normalized = url.replace("://www.", "://")
    row = conn.execute(
        "SELECT url, title, domain, text FROM sources WHERE url = ? OR url_normalized = ? LIMIT 1",
        (url, normalized),
    ).fetchone()

    if row:
        return dict(row)
    return None


def source_count(source_type: str | None = None) -> int:
    """Return total number of entries in the database."""
    try:
        conn = _get_conn()
    except FileNotFoundError:
        return 0
    if source_type:
        return conn.execute(
            "SELECT COUNT(*) FROM sources WHERE source_type = ?", (source_type,)
        ).fetchone()[0]
    return conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
