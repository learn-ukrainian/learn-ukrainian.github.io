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
import json
import sqlite3
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
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
"""

# Seminar tracks that benefit from Wikipedia
SEMINAR_TRACKS = ["folk", "hist", "bio", "istorio", "lit", "oes", "ruth",
                  "lit-essay", "lit-war", "lit-hist-fic", "lit-youth",
                  "lit-fantastika", "lit-humor", "lit-drama", "lit-doc", "lit-crimea"]


def _ensure_table(conn: sqlite3.Connection) -> None:
    """Create wikipedia table if it doesn't exist."""
    conn.executescript(WIKI_TABLE_SCHEMA)


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

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "learn-ukrainian-bot/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"    ⚠️  API error for '{title}': {e}")
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

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "learn-ukrainian-bot/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return []

    results = data.get("query", {}).get("search", [])
    return [r["title"] for r in results]


def _extract_topics_from_plans(track: str) -> list[str]:
    """Extract Wikipedia-searchable topics from plan YAML files."""
    import yaml

    plans_dir = CURRICULUM_DIR / "plans" / track
    if not plans_dir.exists():
        return []

    topics = []
    for plan_path in sorted(plans_dir.glob("*.yaml")):
        try:
            plan = yaml.safe_load(plan_path.read_text("utf-8")) or {}
        except Exception:
            continue

        # Use plan title as primary topic
        title = plan.get("title", "")
        if title:
            topics.append(title)

        # Also extract Ukrainian keywords from content_outline sections
        for section in plan.get("content_outline", []):
            section_title = section.get("section", "")
            # Take just the Ukrainian part (before parenthetical English)
            if "(" in section_title:
                section_title = section_title.split("(")[0].strip()
            if section_title and len(section_title) > 5:
                topics.append(section_title)

    return topics


def fetch_for_track(track: str) -> int:
    """Fetch Wikipedia articles for a track. Returns count of new articles."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    _ensure_table(conn)

    # Get existing titles to avoid re-fetching
    existing = {
        row[0].lower()
        for row in conn.execute("SELECT title FROM wikipedia").fetchall()
    }

    topics = _extract_topics_from_plans(track)
    if not topics:
        print(f"  ⚠️  No plans found for {track}")
        conn.close()
        return 0

    print(f"  📋 {len(topics)} topics from {track} plans")

    new_count = 0
    seen_titles: set[str] = set()

    for topic in topics:
        # Search Wikipedia for matching articles
        titles = _search_wikipedia(topic, limit=2)
        if not titles:
            # Try direct fetch with the topic as title
            titles = [topic]

        for title in titles:
            if title.lower() in existing or title.lower() in seen_titles:
                continue
            seen_titles.add(title.lower())

            article = _fetch_wikipedia_article(title)
            if not article:
                continue

            conn.execute(
                """INSERT OR IGNORE INTO wikipedia (title, url, text, char_count, fetched_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (article["title"], article["url"], article["text"],
                 article["char_count"], datetime.now(datetime.UTC).isoformat()),
            )
            new_count += 1
            print(f"    ✅ {article['title']} ({article['char_count']:,} chars)")

            # Rate limit: 1 req/sec to be nice to Wikipedia
            time.sleep(1)

    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM wikipedia").fetchone()[0]
    conn.close()
    print(f"  📥 {new_count} new articles (total: {total})")
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
