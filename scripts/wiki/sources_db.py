"""SQLite interface for ALL source content — replaces Qdrant RAG entirely.

FTS5 tables (prose search):
- search_textbooks() — textbook chunks
- search_external() — external articles (ULP, blogs, YouTube)
- search_literary() — literary texts (chronicles, poetry, legal)

Indexed tables (dictionary headword lookup):
- search_definitions() — СУМ-11
- search_etymology() — Грінченко
- search_idioms() — Фразеологічний
- search_synonyms() — Ukrajinet WordNet
- translate_en_uk() — Балла EN→UK
- query_cefr_level() — PULS CEFR
- search_style_guide() — Антоненко-Давидович
- lookup_by_url() — external article URL lookup
"""

import sqlite3
from pathlib import Path

from .channels import rank_external_hits

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCES_DB_PATH = PROJECT_ROOT / "data" / "sources.db"

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
    terms = []
    for kw in keywords:
        if len(kw) < min_len:
            continue
        # Strip FTS5 special characters that break MATCH syntax
        clean = kw.replace('"', '').replace("'", '').replace('/', ' ').strip()
        if len(clean) >= min_len:
            terms.append(f'"{clean}"')
    return " OR ".join(terms) if terms else None


def _is_noise(text: str) -> bool:
    """Detect chunks that are noise — no citable content for wiki articles.

    Catches:
    1. TOC pages — dot leaders (". . . . 154") with section numbers
    2. Publisher/metadata fragments — multiple rnk.com.ua URLs
    """
    # TOC pages: 3+ dot-leader patterns
    if text.count(". . .") >= 3:
        return True

    # Publisher/URL fragments
    return text.count("rnk.com.ua") >= 2


def _kw_score(text: str, title: str, keywords: set[str]) -> int:
    """Count keyword hits using space-padded matching.

    Returns 0 for TOC/noise chunks regardless of keyword matches.
    """
    if _is_noise(text):
        return 0
    searchable = f" {title} {text} ".lower()
    return sum(1 for w in keywords if f" {w} " in searchable)


def _table_columns(table: str) -> set[str]:
    """Return the column names for a SQLite table."""
    try:
        conn = _get_conn()
    except FileNotFoundError:
        return set()
    return {
        row["name"]
        for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
    }


# ── FTS5 search functions (prose) ───────────────────────────────


def _fts_search(fts_table: str, data_table: str,
                keywords: set[str], max_total: int,
                extra_cols: str = "",
                min_text_len: int = 300) -> list[dict]:
    """Generic FTS5 search across any prose table.

    Args:
        min_text_len: Minimum text length to include (default 300).
            Filters noise: TOC pages, captions, exercise headers,
            publisher fragments, OCR artifacts. 300 chars ≈ 2 sentences
            of real content — below that, chunks rarely contain
            anything the wiki compiler can cite.
            Set to 0 to disable.
    """
    try:
        conn = _get_conn()
    except FileNotFoundError:
        return []

    fts_query = _build_fts_query(keywords)
    if not fts_query:
        return []

    cols = f"s.*, bm25({fts_table}, 5.0, 1.0) AS rank"
    if extra_cols:
        cols = f"s.*, {extra_cols}, bm25({fts_table}, 5.0, 1.0) AS rank"

    # Filter out short/noise chunks (TOC pages, captions, exercise headers)
    length_filter = f"AND length(s.text) >= {min_text_len}" if min_text_len > 0 else ""

    rows = conn.execute(
        f"""SELECT {cols}
            FROM {fts_table}
            JOIN {data_table} s ON s.id = {fts_table}.rowid
            WHERE {fts_table} MATCH ?
            {length_filter}
            ORDER BY rank
            LIMIT ?""",
        (fts_query, max_total),
    ).fetchall()

    return [dict(row) for row in rows]


def search_textbooks(ukr_keywords: set[str], max_total: int = 40) -> list[dict]:
    """Search textbook chunks via FTS5.

    Filters out TOC pages and short noise chunks before returning.
    Requests extra rows from FTS5 to compensate for filtered-out noise.
    """
    # Request 2x to compensate for filtered TOC/noise chunks
    rows = _fts_search("textbooks_fts", "textbooks", ukr_keywords, max_total * 2)
    results = []
    for r in rows:
        text = r.get("text", "")
        if _is_noise(text):
            continue
        r["_kw_score"] = _kw_score(text, r.get("title", ""), ukr_keywords)
        r["source_type"] = "textbook"
        r["section_title"] = r.get("title", "")
        results.append(r)
        if len(results) >= max_total:
            break
    return results


def search_external(
    ukr_keywords: set[str],
    max_total: int = 10,
    exclude_urls: set[str] | None = None,
    *,
    channel: str | None = None,
    register: str | None = None,
    decolonization: str | None = None,
    min_quality_tier: int | None = None,
    track: str | None = None,
) -> list[dict]:
    """Search external articles via FTS5."""
    try:
        conn = _get_conn()
    except FileNotFoundError:
        return []

    fts_query = _build_fts_query(ukr_keywords)
    if not fts_query:
        return []

    columns = _table_columns("external_articles")
    where = ["external_fts MATCH ?"]
    params: list[object] = [fts_query]
    if channel:
        if "channel_id" not in columns:
            return []
        where.append("s.channel_id = ?")
        params.append(channel)
    if register:
        if "register_tag" not in columns:
            return []
        where.append("s.register_tag = ?")
        params.append(register)
    if decolonization:
        if "decolonization_tag" not in columns:
            return []
        where.append("s.decolonization_tag = ?")
        params.append(decolonization)
    if min_quality_tier is not None:
        if "quality_tier" not in columns:
            return []
        where.append("COALESCE(s.quality_tier, 99) <= ?")
        params.append(int(min_quality_tier))

    rows = conn.execute(
        f"""SELECT s.*, bm25(external_fts) AS rank
            FROM external_fts
            JOIN external_articles s ON s.id = external_fts.rowid
            WHERE {' AND '.join(where)}
            ORDER BY rank
            LIMIT ?""",
        (*params, max_total * 5),
    ).fetchall()

    skip = exclude_urls or set()
    results: list[dict] = []
    channels: dict[str, dict] = {}
    try:
        from .channels import load_channels

        channels = load_channels()
    except Exception:
        channels = {}

    for row in rows:
        r = dict(row)
        url = str(r.get("url", "")).strip()
        if url in skip:
            continue

        source_file = str(r.get("source_file", "")).strip()
        channel_meta = channels.get(source_file, {})
        channel_id = str(r.get("channel_id", "") or source_file).strip()
        quality_tier = int(r.get("quality_tier", channel_meta.get("quality_tier", 2)) or 2)
        speaker = str(r.get("speaker", "") or channel_meta.get("host", "")).strip()
        register_tag = str(r.get("register_tag", "") or channel_meta.get("register_tag", "")).strip()
        decolonization_tag = str(
            r.get("decolonization_tag", "") or channel_meta.get("decolonization_tag", "")
        ).strip()
        channel_name = str(channel_meta.get("name", "")).strip()

        r["_kw_score"] = _kw_score(r.get("text", ""), r.get("title", ""), ukr_keywords)
        r["source_type"] = "external"
        r["channel_id"] = channel_id
        r["speaker"] = speaker
        r["register_tag"] = register_tag
        r["decolonization_tag"] = decolonization_tag
        r["quality_tier"] = quality_tier
        r["source_name"] = channel_name or r.get("domain", r.get("source_file", ""))
        r["text"] = r.get("text", "")[:6000]
        r["adjusted_score"] = r.get("rank", 0.0)
        results.append(r)

    if track:
        results = rank_external_hits(
            results,
            track=track,
            apply_quality_without_track=False,
        )

    return results[:max_total]


def search_literary(ukr_keywords: set[str], max_total: int = 20) -> list[dict]:
    """Search literary texts via FTS5."""
    rows = _fts_search("literary_fts", "literary_texts", ukr_keywords, max_total)
    for r in rows:
        r["_kw_score"] = _kw_score(r.get("text", ""), r.get("title", ""), ukr_keywords)
        r["source_type"] = "literary"
    return rows


def search_wikipedia(ukr_keywords: set[str], max_total: int = 10) -> list[dict]:
    """Search Wikipedia articles via FTS5."""
    try:
        conn = _get_conn()
        # Check if wikipedia table exists
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='wikipedia'"
        ).fetchall()]
        if "wikipedia" not in tables:
            return []
    except (FileNotFoundError, Exception):
        return []

    rows = _fts_search("wikipedia_fts", "wikipedia", ukr_keywords, max_total)
    for r in rows:
        r["_kw_score"] = _kw_score(r.get("text", ""), r.get("title", ""), ukr_keywords)
        r["source_type"] = "wikipedia"
        r["source_name"] = "Wikipedia"
        r["text"] = r.get("text", "")[:5000]
    return rows


# ── Dictionary lookup functions (indexed tables) ────────────────


def _dict_lookup(table: str, word: str, limit: int = 10) -> list[dict]:
    """Generic headword lookup on an indexed dictionary table."""
    try:
        conn = _get_conn()
    except FileNotFoundError:
        return []

    # Exact match first, then prefix match
    rows = conn.execute(
        f"SELECT * FROM {table} WHERE word = ? COLLATE NOCASE LIMIT ?",
        (word, limit),
    ).fetchall()

    if not rows:
        rows = conn.execute(
            f"SELECT * FROM {table} WHERE word LIKE ? COLLATE NOCASE LIMIT ?",
            (f"{word}%", limit),
        ).fetchall()

    return [dict(r) for r in rows]


def search_definitions(word: str, limit: int = 10) -> list[dict]:
    """Look up word in СУМ-11 (Ukrainian explanatory dictionary)."""
    return _dict_lookup("sum11", word, limit)


def search_etymology(word: str, limit: int = 10) -> list[dict]:
    """Look up word in Грінченко (historical dictionary)."""
    return _dict_lookup("grinchenko", word, limit)


def translate_en_uk(word: str, limit: int = 10) -> list[dict]:
    """Look up English→Ukrainian translation in Балла."""
    return _dict_lookup("balla_en_uk", word, limit)


def search_idioms(word: str, limit: int = 10) -> list[dict]:
    """Look up idioms/expressions in Фразеологічний."""
    return _dict_lookup("frazeolohichnyi", word, limit)


def search_synonyms(word: str, limit: int = 20) -> list[dict]:
    """Look up synonyms in Ukrajinet WordNet."""
    try:
        conn = _get_conn()
    except FileNotFoundError:
        return []

    # Search in the 'words' field (comma-separated synset members)
    rows = conn.execute(
        "SELECT * FROM ukrajinet WHERE words LIKE ? COLLATE NOCASE LIMIT ?",
        (f"%{word}%", limit),
    ).fetchall()
    return [dict(r) for r in rows]


def query_cefr_level(word: str, limit: int = 5) -> list[dict]:
    """Look up CEFR level for a word in PULS vocabulary."""
    return _dict_lookup("puls_cefr", word, limit=limit)


def search_style_guide(word: str, limit: int = 5) -> list[dict]:
    """Look up calques/Russianisms in Антоненко-Давидович style guide."""
    return _dict_lookup("style_guide", word, limit)


def lookup_by_url(url: str) -> dict | None:
    """Look up an external article by URL. Handles www/non-www variants."""
    try:
        conn = _get_conn()
    except FileNotFoundError:
        return None

    normalized = url.replace("://www.", "://")
    row = conn.execute(
        "SELECT * FROM external_articles WHERE url = ? OR url_normalized = ? LIMIT 1",
        (url, normalized),
    ).fetchone()
    return dict(row) if row else None


def source_count(table: str | None = None) -> int:
    """Return entry count for a table, or total across all tables."""
    try:
        conn = _get_conn()
    except FileNotFoundError:
        return 0

    if table:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

    tables = [
        "textbooks", "external_articles", "literary_texts",
        "sum11", "grinchenko", "balla_en_uk", "dmklinger_uk_en",
        "ukrajinet", "wiktionary", "frazeolohichnyi", "puls_cefr", "style_guide",
    ]
    return sum(
        conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        for t in tables
    )


def list_tables() -> dict[str, int]:
    """Return {table_name: count} for all content tables."""
    try:
        conn = _get_conn()
    except FileNotFoundError:
        return {}

    tables = [
        "textbooks", "external_articles", "literary_texts",
        "sum11", "grinchenko", "balla_en_uk", "dmklinger_uk_en",
        "ukrajinet", "wiktionary", "frazeolohichnyi", "puls_cefr", "style_guide",
    ]
    return {
        t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        for t in tables
    }
