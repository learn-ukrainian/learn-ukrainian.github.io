"""SQLite cache for Wikipedia API responses.

Avoids hammering uk.wikipedia.org during development and testing.
Cache entries expire after a configurable TTL (default 30 days).
Negative responses (404s) are cached to block repeated lookups
of hallucinated titles.

Usage:
    from rag.wiki_cache import WikiCache

    cache = WikiCache()                    # default: data/wiki_cache.db
    cache.get("summary", "Тарас Шевченко") # → str | None (None = miss)
    cache.put("summary", "Тарас Шевченко", '{"title": ...}')
    cache.put_negative("summary", "Не існує")  # cache a 404

Issue: #803
"""

from __future__ import annotations

import hashlib
import sqlite3
import time
from contextlib import closing
from pathlib import Path

from scripts.lib.readonly_sqlite import open_readonly

# Default cache location (relative to project root)
_DEFAULT_DB = Path(__file__).resolve().parent.parent.parent / "data" / "wiki_cache.db"

# 30 days in seconds
DEFAULT_TTL = 30 * 24 * 3600

# Sentinel value stored in `response` column for negative cache entries (404s)
NEGATIVE_SENTINEL = "__404__"

# Short negative TTL (1 hour) so outages and misses do not persist for 30 days (#9016)
DEFAULT_NEGATIVE_TTL = 3600


def read_cached(mode: str, title: str, section: str = "", *, db_path: Path | None = None) -> dict:
    """Read a cache snapshot without initializing, evicting, refreshing or fetching.

    A missing row is a cache miss, never evidence that an article does not exist.
    Only fresh positive bodies are returned; other states retain their provenance.
    """
    key = {"mode": mode, "title": WikiCache._normalize_title(title), "section": section}
    checked = int(time.time())
    result = {
        "status": "unavailable", "store": "wiki_cache.db", "source_url": "https://uk.wikipedia.org",
        "key": key, "checked_at": checked, "fetched_at": None, "expires_at": None,
        "response": None, "response_sha256": None,
    }
    try:
        with closing(open_readonly(db_path if db_path is not None else _DEFAULT_DB)) as conn:
            row = conn.execute(
                "SELECT response, fetched_at FROM wiki_cache WHERE mode=? AND title=? AND section=?",
                (mode, key["title"], section),
            ).fetchone()
    except (OSError, sqlite3.Error):
        return result
    if row is None:
        return {**result, "status": "miss"}
    response, fetched = row
    result["fetched_at"] = fetched
    if not isinstance(response, str) or not response.strip() or type(fetched) is not int or not 0 < fetched <= checked:
        return result
    expires = fetched + (DEFAULT_NEGATIVE_TTL if response == NEGATIVE_SENTINEL else DEFAULT_TTL)
    result.update(expires_at=expires, response_sha256=hashlib.sha256(response.encode()).hexdigest())
    if checked >= expires:
        result["status"] = "stale"
    elif response == NEGATIVE_SENTINEL:
        result["status"] = "negative"
    else:
        result.update(status="hit", response=response)
    return result


class WikiCache:
    """Thread-safe SQLite cache for Wikipedia API responses."""

    def __init__(
        self,
        db_path: Path | str | None = None,
        ttl: int = DEFAULT_TTL,
        negative_ttl: int | None = None,
    ):
        self.db_path = Path(db_path) if db_path else _DEFAULT_DB
        self.ttl = ttl
        self.negative_ttl = min(ttl, DEFAULT_NEGATIVE_TTL) if negative_ttl is None else negative_ttl
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False,
            isolation_level="DEFERRED",
        )
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(
            """CREATE TABLE IF NOT EXISTS wiki_cache (
                mode    TEXT NOT NULL,
                title   TEXT NOT NULL,
                section TEXT NOT NULL DEFAULT '',
                response TEXT,
                fetched_at INTEGER NOT NULL,
                PRIMARY KEY (mode, title, section)
            )"""
        )
        self._conn.commit()
        # Evict expired entries on startup
        self.clear_expired()

    @staticmethod
    def _normalize_title(title: str) -> str:
        """Normalize Wikipedia title for consistent cache keys."""
        t = title.strip().replace(" ", "_")
        if t:
            t = t[0].upper() + t[1:]
        return t

    def get(self, mode: str, title: str, section: str = "") -> str | None:
        """Fetch cached response. Returns None on miss or expiry.

        Returns NEGATIVE_SENTINEL if a negative (404) entry exists.
        """
        norm_title = self._normalize_title(title)
        now = int(time.time())
        neg_cutoff = now - self.negative_ttl
        pos_cutoff = now - self.ttl
        row = self._conn.execute(
            """SELECT response FROM wiki_cache
            WHERE mode=? AND title=? AND section=?
              AND fetched_at > CASE WHEN response = ? THEN ? ELSE ? END""",
            (mode, norm_title, section, NEGATIVE_SENTINEL, neg_cutoff, pos_cutoff),
        ).fetchone()
        if row is None:
            return None
        return row[0]

    def put(self, mode: str, title: str, response: str, section: str = "") -> None:
        """Store a response in the cache."""
        norm_title = self._normalize_title(title)
        now = int(time.time())
        self._conn.execute(
            "INSERT OR REPLACE INTO wiki_cache (mode, title, section, response, fetched_at) VALUES (?, ?, ?, ?, ?)",
            (mode, norm_title, section, response, now),
        )
        self._conn.commit()

    def put_negative(self, mode: str, title: str, section: str = "") -> None:
        """Cache a negative result (404 / not found)."""
        self.put(mode, title, NEGATIVE_SENTINEL, section)

    def is_negative(self, response: str | None) -> bool:
        """Check if a cached response is a negative entry."""
        return response == NEGATIVE_SENTINEL

    def clear_expired(self) -> int:
        """Delete expired entries. Returns count of deleted rows."""
        now = int(time.time())
        neg_cutoff = now - self.negative_ttl
        pos_cutoff = now - self.ttl
        cursor = self._conn.execute(
            """DELETE FROM wiki_cache
            WHERE fetched_at < CASE WHEN response = ? THEN ? ELSE ? END""",
            (NEGATIVE_SENTINEL, neg_cutoff, pos_cutoff),
        )
        self._conn.commit()
        return cursor.rowcount

    def stats(self) -> dict[str, int]:
        """Return cache statistics."""
        row = self._conn.execute("SELECT COUNT(*) FROM wiki_cache").fetchone()
        total = row[0] if row else 0
        neg = self._conn.execute("SELECT COUNT(*) FROM wiki_cache WHERE response = ?", (NEGATIVE_SENTINEL,)).fetchone()
        neg_count = neg[0] if neg else 0
        return {"total_entries": total, "negative_entries": neg_count}

    def close(self) -> None:
        self._conn.close()
