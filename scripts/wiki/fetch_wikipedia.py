#!/usr/bin/env python3
"""Fetch Ukrainian Wikipedia articles for wiki enrichment.

Reads plan YAML titles to identify Wikipedia articles to fetch,
stores them in data/sources.db (wikipedia table).

Usage:
    # Fetch for a specific track
    .venv/bin/python scripts/wiki/fetch_wikipedia.py --track folk
    .venv/bin/python scripts/wiki/fetch_wikipedia.py --track hist

    # Fetch for all seminar tracks
    .venv/bin/python scripts/wiki/fetch_wikipedia.py --all

    # Status
    .venv/bin/python scripts/wiki/fetch_wikipedia.py --status
"""

import argparse
import datetime
import json
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "sources.db"
CURRICULUM_DIR = PROJECT_ROOT / "curriculum" / "l2-uk-en"

WIKI_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS wikipedia (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    url TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    char_count INTEGER DEFAULT 0,
    fetched_at TEXT NOT NULL DEFAULT ''
);
CREATE VIRTUAL TABLE IF NOT EXISTS wikipedia_fts USING fts5(
    title, text, content='wikipedia', content_rowid='id', tokenize='unicode61'
);
CREATE TRIGGER IF NOT EXISTS wikipedia_ai AFTER INSERT ON wikipedia BEGIN
    INSERT INTO wikipedia_fts(rowid, title, text) VALUES (new.id, new.title, new.text);
END;
CREATE INDEX IF NOT EXISTS idx_wiki_title ON wikipedia(title);

-- Negative cache for topics known NOT to map to any Wikipedia article.
-- Prevents repeated API calls on every run for the same dead topics
-- (e.g. seminar section headers like "Джерела: Рішительні пункти..."
-- which are pedagogical headings, not real article titles).
CREATE TABLE IF NOT EXISTS wikipedia_negative_cache (
    topic TEXT PRIMARY KEY,
    tried_at TEXT NOT NULL DEFAULT ''
);
"""

# Seminar tracks that benefit from Wikipedia.
# Source of truth: curriculum/l2-uk-en/curriculum.yaml. Keep aligned with
# scripts/wiki/config.py:ALL_TRACKS. lit-doc and lit-crimea were merged into
# other lit-* tracks and are no longer separate tracks.
SEMINAR_TRACKS = ["folk", "hist", "bio", "istorio", "lit", "oes", "ruth",
                  "lit-essay", "lit-war", "lit-hist-fic", "lit-youth",
                  "lit-fantastika", "lit-humor", "lit-drama"]

# Section-header prefixes that indicate a pedagogical heading, not a real
# Wikipedia topic. Content_outline sections with these prefixes get filtered
# out of the search set — they would never return a valid article and every
# query wastes the API rate budget.
#
# Pattern: word-colon-phrase, where word is a Ukrainian academic/essay
# structural marker. Matched case-insensitively at the START of the section.
_PEDAGOGICAL_HEADER_PREFIXES = (
    "вступ", "вступний", "основ", "висновк", "висновок",
    "джерел", "контекст", "аналіз", "аналітик", "методологія",
    "огляд", "підсумк", "рефлексі", "дискусі", "розгляд",
    "тема", "тези", "фокус", "мета", "завдання", "план",
    "розділ", "частина", "глава", "секція", "підрозділ",
    "додаток", "бібліографія", "примітк",
    # English equivalents that sometimes sneak into Ukrainian plan YAMLs
    "introduction", "conclusion", "sources", "analysis", "context",
    "overview", "summary", "methodology", "discussion",
)


def _is_pedagogical_header(topic: str) -> bool:
    """True if a topic string looks like a module section header, not a
    real Wikipedia topic. Used to filter plan content_outline entries.

    Heuristics, in order:
    1. Empty or too short
    2. Starts with a known pedagogical prefix (case-insensitive)
    3. Has a colon with a short word on the left (section-header pattern
       like "Аналіз: Наслідки") — the colon-and-substring pattern is a
       strong signal even when the prefix isn't in our known list
    """
    topic = topic.strip()
    if len(topic) < 5:
        return True
    lowered = topic.lower()
    for prefix in _PEDAGOGICAL_HEADER_PREFIXES:
        if lowered.startswith(prefix):
            return True
    # Colon with short word on the left (up to 2 words before ":") = header
    if ":" in topic:
        before = topic.split(":", 1)[0].strip()
        if len(before.split()) <= 2 and len(before) <= 25:
            return True
    return False


def _ensure_table(conn: sqlite3.Connection) -> None:
    """Create wikipedia table if it doesn't exist."""
    conn.executescript(WIKI_TABLE_SCHEMA)


# ── Rate limiting + 429 backoff ──────────────────────────────────────
# Wikipedia's API asks clients to stay under ~10 req/sec. We stay well
# below that (1 req/sec minimum) and back off exponentially on 429.

_MIN_INTERVAL_S = 1.0            # minimum gap between consecutive API calls
_BACKOFF_BASE_S = 30.0           # first backoff after 429
_BACKOFF_MAX_S = 600.0           # cap at 10 minutes
_MAX_429_RETRIES = 4             # total attempts per URL before giving up

# Module-level tracker of when we last hit the API (any endpoint)
_last_call_ts: float = 0.0


def _pace_api_call() -> None:
    """Sleep just enough to ensure at least _MIN_INTERVAL_S between calls.
    Call this BEFORE every network request, not after — so even failed
    calls count toward the rate budget.
    """
    global _last_call_ts
    now = time.monotonic()
    gap = now - _last_call_ts
    if gap < _MIN_INTERVAL_S:
        time.sleep(_MIN_INTERVAL_S - gap)
    _last_call_ts = time.monotonic()


def _api_get(url: str) -> dict | None:
    """Call a Wikipedia API URL with pacing + exponential backoff on 429.

    Returns the decoded JSON on success, None on any non-recoverable
    failure (not-found, timeout, permanent error). Raises RuntimeError
    only if every 429 retry is exhausted — callers catch and skip.
    """
    req = urllib.request.Request(
        url, headers={"User-Agent": "learn-ukrainian-bot/1.0 (https://learn-ukrainian.github.io)"},
    )
    for attempt in range(_MAX_429_RETRIES):
        _pace_api_call()
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = min(_BACKOFF_BASE_S * (2 ** attempt), _BACKOFF_MAX_S)
                print(f"    ⏳ rate-limited (429), sleeping {wait:.0f}s "
                      f"(attempt {attempt + 1}/{_MAX_429_RETRIES})")
                time.sleep(wait)
                continue
            # Other HTTP errors: don't retry
            print(f"    ⚠️  HTTP {e.code} for URL")
            return None
        except Exception as e:
            print(f"    ⚠️  API error: {type(e).__name__}: {str(e)[:80]}")
            return None
    print(f"    ❌ giving up after {_MAX_429_RETRIES} 429 retries")
    return None


def _fetch_wikipedia_article(title: str) -> dict | None:
    """Fetch a single article from Ukrainian Wikipedia API."""
    params = {
        "action": "query",
        "titles": title,
        "prop": "extracts",
        "explaintext": "1",
        "exlimit": "1",
        "format": "json",
    }
    url = "https://uk.wikipedia.org/w/api.php?" + urllib.parse.urlencode(params)
    data = _api_get(url)
    if data is None:
        return None

    pages = data.get("query", {}).get("pages", {})
    for page_id, page in pages.items():
        if page_id == "-1":
            return None  # Not found
        extract = page.get("extract", "")
        if not extract or len(extract) < 100:
            return None
        return {
            "title": page.get("title", title),
            "url": f"https://uk.wikipedia.org/wiki/{urllib.parse.quote(page.get('title', title))}",
            "text": extract,
            "char_count": len(extract),
        }
    return None


def _search_wikipedia(query: str, limit: int = 3) -> list[str]:
    """Search Wikipedia for article titles matching a query."""
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": str(limit),
        "format": "json",
    }
    url = "https://uk.wikipedia.org/w/api.php?" + urllib.parse.urlencode(params)
    data = _api_get(url)
    if data is None:
        return []
    results = data.get("query", {}).get("search", [])
    return [r["title"] for r in results]


def _extract_topics_from_plans(track: str) -> list[str]:
    """Extract Wikipedia-searchable topics from plan YAML files.

    Returns a de-duplicated list of topics with pedagogical section
    headers (like "Джерела: ...", "Аналіз: ...") filtered out — those
    would never return a valid Wikipedia article and every query wastes
    the API rate budget.
    """
    import yaml

    plans_dir = CURRICULUM_DIR / "plans" / track
    if not plans_dir.exists():
        return []

    seen: set[str] = set()
    topics: list[str] = []

    def _add(candidate: str) -> None:
        candidate = candidate.strip()
        if not candidate or _is_pedagogical_header(candidate):
            return
        key = candidate.lower()
        if key in seen:
            return
        seen.add(key)
        topics.append(candidate)

    for plan_path in sorted(plans_dir.glob("*.yaml")):
        try:
            plan = yaml.safe_load(plan_path.read_text("utf-8")) or {}
        except Exception:
            continue

        # Use plan title as primary topic
        _add(plan.get("title", ""))

        # Also extract Ukrainian keywords from content_outline sections
        for section in plan.get("content_outline", []) or []:
            if not isinstance(section, dict):
                continue
            section_title = section.get("section", "") or ""
            # Take just the Ukrainian part (before parenthetical English)
            if "(" in section_title:
                section_title = section_title.split("(")[0].strip()
            _add(section_title)

    return topics


def fetch_for_track(track: str) -> int:
    """Fetch Wikipedia articles for a track. Returns count of new articles."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    _ensure_table(conn)

    # Positive cache: titles we already have
    existing = {
        row[0].lower()
        for row in conn.execute("SELECT title FROM wikipedia").fetchall()
    }
    # Negative cache: topics that previously returned nothing — skip them
    negative = {
        row[0].lower()
        for row in conn.execute("SELECT topic FROM wikipedia_negative_cache").fetchall()
    }

    topics = _extract_topics_from_plans(track)
    if not topics:
        print(f"  ⚠️  No plans found for {track}")
        conn.close()
        return 0

    pre_neg = len(topics)
    topics = [t for t in topics if t.lower() not in negative]
    skipped_neg = pre_neg - len(topics)

    print(f"  📋 {len(topics)} topics from {track} plans"
          + (f" ({skipped_neg} skipped via negative cache)" if skipped_neg else ""))

    new_count = 0
    seen_titles: set[str] = set()
    now_iso = datetime.datetime.now(tz=datetime.UTC).isoformat()

    for topic in topics:
        # Search Wikipedia for matching articles
        titles = _search_wikipedia(topic, limit=2)
        if not titles:
            # No search result → try direct fetch with the topic as title
            titles = [topic]

        got_any = False
        for title in titles:
            if title.lower() in existing or title.lower() in seen_titles:
                # Already have it — count as "got_any" so we don't
                # negative-cache a topic that resolves to a known article
                got_any = True
                continue
            seen_titles.add(title.lower())

            article = _fetch_wikipedia_article(title)
            if not article:
                continue

            conn.execute(
                """INSERT OR IGNORE INTO wikipedia (title, url, text, char_count, fetched_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (article["title"], article["url"], article["text"],
                 article["char_count"], now_iso),
            )
            existing.add(article["title"].lower())
            new_count += 1
            got_any = True
            print(f"    ✅ {article['title']} ({article['char_count']:,} chars)")

        if not got_any:
            # Record topic in negative cache so future runs skip it
            conn.execute(
                "INSERT OR IGNORE INTO wikipedia_negative_cache (topic, tried_at) VALUES (?, ?)",
                (topic, now_iso),
            )

    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM wikipedia").fetchone()[0]
    neg_total = conn.execute("SELECT COUNT(*) FROM wikipedia_negative_cache").fetchone()[0]
    conn.close()
    print(f"  📥 {new_count} new articles (total: {total}, negative cache: {neg_total})")
    return new_count


def show_status() -> None:
    """Show Wikipedia fetch status."""
    if not DB_PATH.exists():
        print("Database not found. Run build_sources_db.py first.")
        return

    conn = sqlite3.connect(str(DB_PATH))
    try:
        count = conn.execute("SELECT COUNT(*) FROM wikipedia").fetchone()[0]
        total_chars = conn.execute("SELECT SUM(char_count) FROM wikipedia").fetchone()[0] or 0
        print(f"\n📊 Wikipedia: {count} articles, {total_chars:,} chars")

        # By first word of title (rough category)
        titles = [r[0] for r in conn.execute("SELECT title FROM wikipedia ORDER BY title").fetchall()]
        print(f"Sample titles: {titles[:10]}")
    except sqlite3.OperationalError:
        print("Wikipedia table not yet created.")
    conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch Wikipedia articles for wiki enrichment")
    parser.add_argument("--track", help="Fetch for specific track")
    parser.add_argument("--all", action="store_true", help="Fetch for all seminar tracks")
    parser.add_argument("--status", action="store_true", help="Show status")
    args = parser.parse_args()

    if args.status:
        show_status()
        return

    if not DB_PATH.exists():
        print(f"Error: {DB_PATH} not found. Run build_sources_db.py first.", file=sys.stderr)
        sys.exit(1)

    if args.all:
        total = 0
        for track in SEMINAR_TRACKS:
            print(f"\n🌐 Fetching Wikipedia for {track}...")
            total += fetch_for_track(track)
        print(f"\n✅ Total new articles: {total}")
    elif args.track:
        print(f"🌐 Fetching Wikipedia for {args.track}...")
        fetch_for_track(args.track)
    else:
        parser.error("Specify --track or --all")


if __name__ == "__main__":
    main()
