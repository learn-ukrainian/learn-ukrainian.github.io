"""SQLite FTS5 interface for external article sources.

Provides search_articles() and lookup_by_url() as drop-in replacements
for the JSONL-based _search_external_articles() and _get_article_cache().
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


def search_articles(
    ukr_keywords: set[str],
    max_total: int = 10,
    exclude_urls: set[str] | None = None,
) -> list[dict]:
    """Search external articles using FTS5 full-text search.

    Returns chunk dicts compatible with the enrichment pipeline:
    {text, chunk_id, source_type, _kw_score}
    """
    if not ukr_keywords:
        return []

    try:
        conn = _get_conn()
    except FileNotFoundError:
        return []

    skip_urls = exclude_urls or set()

    # Build FTS5 query: OR-ed quoted keywords
    terms = [f'"{kw}"' for kw in ukr_keywords if len(kw) >= 3]
    if not terms:
        return []
    fts_query = " OR ".join(terms)

    # FTS5 MATCH with bm25 ranking (title weighted 5x over text)
    rows = conn.execute(
        """SELECT a.url, a.title, a.domain, a.text, a.source_file,
                  bm25(articles_fts, 5.0, 1.0) AS rank
           FROM articles_fts
           JOIN articles a ON a.id = articles_fts.rowid
           WHERE articles_fts MATCH ?
           ORDER BY rank
           LIMIT ?""",
        (fts_query, max_total * 3),  # Fetch extra to account for URL filtering
    ).fetchall()

    chunks: list[dict] = []
    for row in rows:
        if len(chunks) >= max_total:
            break
        url = row["url"]
        if url in skip_urls:
            continue

        title = row["title"]
        text = row["text"]
        domain = row["domain"] or row["source_file"]

        # Count actual keyword hits for _kw_score (for cross-source sorting)
        searchable = f"{title} {text}".lower()
        kw_score = sum(
            1 for w in ukr_keywords
            if f" {w} " in f" {searchable} "
        )

        chunks.append({
            "text": (
                f"External article: {title}\n"
                f"Source: {domain}\n"
                f"URL: {url}\n\n"
                f"{text}"
            )[:8000],
            "chunk_id": f"ext-fts-{len(chunks)}",
            "source_type": "external_keyword",
            "_kw_score": kw_score,
        })

    return chunks


def lookup_by_url(url: str) -> dict | None:
    """Look up an article by URL. Handles www/non-www variants.

    Returns dict with url, title, domain, text keys, or None.
    """
    try:
        conn = _get_conn()
    except FileNotFoundError:
        return None

    normalized = url.replace("://www.", "://")
    row = conn.execute(
        "SELECT url, title, domain, text FROM articles WHERE url = ? OR url_normalized = ? LIMIT 1",
        (url, normalized),
    ).fetchone()

    if row:
        return dict(row)
    return None


def article_count() -> int:
    """Return total number of articles in the database."""
    try:
        conn = _get_conn()
    except FileNotFoundError:
        return 0
    return conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
