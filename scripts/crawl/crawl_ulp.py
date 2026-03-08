#!/usr/bin/env python3
"""Crawl ukrainianlessons.com: podcast episodes + blog articles.

Gathers metadata from multiple sources:
  - iTunes API: 200 most recent ULP episodes (seasons 2-6) + all 60 FMU episodes
  - Website season1 page: season 1 episodes (1-40) — too old for iTunes limit
  - Existing blog catalog: 119 blog article entries with topics/levels

Outputs a unified blog_db.json v3.0 with all resources typed and tagged.

Usage:
    .venv/bin/python scripts/crawl_ulp.py                    # full crawl
    .venv/bin/python scripts/crawl_ulp.py --episodes-only    # just episodes
    .venv/bin/python scripts/crawl_ulp.py --blog-only        # just blog articles
    .venv/bin/python scripts/crawl_ulp.py --dry-run          # show plan without fetching

Output:
    docs/resources/ukrainianlessons/blog_db.json (v3.0)

Ref: https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/724
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

import httpx

# ── Config ────────────────────────────────────────────────────────
BASE_URL = "https://www.ukrainianlessons.com"
OUTPUT_PATH = Path(__file__).parent.parent.parent / "docs" / "resources" / "ukrainianlessons" / "blog_db.json"

# iTunes podcast IDs
ULP_ITUNES_ID = 1128346151
FMU_ITUNES_ID = 1532711571

# Season metadata
SEASONS: dict[int, dict] = {
    1: {"start": 1, "end": 40, "level": "A1", "focus": "beginner basics, greetings, vocabulary, pronunciation"},
    2: {"start": 41, "end": 80, "level": "A2", "focus": "elementary grammar, housing, animals, travel, history"},
    3: {"start": 81, "end": 120, "level": "B1", "focus": "intermediate conversation, slow Ukrainian"},
    4: {"start": 121, "end": 160, "level": "B1", "focus": "slow Ukrainian, idioms, expressions"},
    5: {"start": 161, "end": 200, "level": "B2", "focus": "slow Ukrainian, useful sentences, real conversations"},
    6: {"start": 201, "end": 240, "level": "B2", "focus": "slow Ukrainian, biographies, poetry, culture"},
}

REQUEST_TIMEOUT = 30


# ── Topic extraction ─────────────────────────────────────────────

TOPIC_PATTERNS: list[tuple[str, list[str]]] = [
    # Grammar
    (r"case[s]?\b|відмін|відмінк", ["grammar", "cases"]),
    (r"accusative|знахідн", ["grammar", "accusative", "cases"]),
    (r"genitive|родов", ["grammar", "genitive", "cases"]),
    (r"dative|давальн", ["grammar", "dative", "cases"]),
    (r"locative|місцев", ["grammar", "locative", "cases"]),
    (r"instrumental|орудн", ["grammar", "instrumental", "cases"]),
    (r"vocative|клич", ["grammar", "vocative", "cases"]),
    (r"verb[s]?\b|дієсло", ["grammar", "verbs"]),
    (r"past tense|минул", ["grammar", "verbs", "past tense"]),
    (r"future|майбутн", ["grammar", "verbs", "future tense"]),
    (r"imperative|наказов", ["grammar", "verbs", "imperative"]),
    (r"aspect\b|вид\b|доконан|недоконан", ["grammar", "verbs", "aspect"]),
    (r"conjugat|дієвідмін", ["grammar", "verbs", "conjugation"]),
    (r"pronoun|займен", ["grammar", "pronouns"]),
    (r"adjective|прикметн", ["grammar", "adjectives"]),
    (r"preposition|прийменн", ["grammar", "prepositions"]),
    (r"conjunction|сполучн", ["grammar", "conjunctions"]),
    (r"plural|множин", ["grammar", "plural"]),
    (r"gender\b|рід\b", ["grammar", "gender"]),
    (r"number|числ|цифр", ["numbers"]),
    # Vocabulary
    (r"food|їж[аі]|страв|їсти", ["vocabulary", "food"]),
    (r"family|сім['\u02bcʼ]|родин", ["vocabulary", "family"]),
    (r"cloth|одяг", ["vocabulary", "clothing"]),
    (r"animal|тварин", ["vocabulary", "animals"]),
    (r"color|колір|кольор", ["vocabulary", "colors"]),
    (r"emotion|feel|почутт", ["vocabulary", "emotions"]),
    (r"weather|погод", ["vocabulary", "weather"]),
    (r"body|health|здоров", ["vocabulary", "health"]),
    (r"travel|подорож", ["vocabulary", "travel"]),
    (r"job|profession|професі", ["vocabulary", "professions"]),
    (r"holiday|свят", ["culture", "holidays"]),
    (r"house|home|квартир|кімнат|дім\b", ["vocabulary", "housing"]),
    (r"idiom|ідіом|прислів|вираз", ["vocabulary", "idioms"]),
    # Communication
    (r"greet|вітан|привіт", ["phrases", "greetings"]),
    (r"introduc|знайом", ["phrases", "introductions"]),
    (r"goodbye|прощан|до побач", ["phrases", "goodbyes"]),
    (r"phrase", ["phrases"]),
    # Culture & History
    (r"histor|істор", ["culture", "history"]),
    (r"Kyiv|Київ", ["culture", "kyiv"]),
    (r"Lviv|Львів", ["culture", "lviv"]),
    (r"tradition|традиц", ["culture", "traditions"]),
    (r"poet|поез|вірш", ["culture", "poetry"]),
    (r"Shevchenko|Шевченк", ["culture", "literature", "shevchenko"]),
    (r"interview|інтерв", ["conversation", "interview"]),
    (r"review|повторен|тест", ["review"]),
    # Skills
    (r"pronunciat|вимов", ["pronunciation"]),
    (r"alphabet|абетк|cyrillic|кирил", ["alphabet"]),
    (r"listen|слухан", ["listening"]),
]


def extract_topics(title: str, description: str = "") -> list[str]:
    """Extract topic tags from title + description."""
    text = f"{title} {description}".lower()
    topics: list[str] = []
    seen: set[str] = set()
    for pattern, tags in TOPIC_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            for t in tags:
                if t not in seen:
                    topics.append(t)
                    seen.add(t)
    return topics or ["general"]


# ── Season + level helpers ───────────────────────────────────────

def get_season_info(episode_num: int) -> tuple[int, str, str]:
    """Return (season, level, focus) for a ULP episode number."""
    for s, info in SEASONS.items():
        if info["start"] <= episode_num <= info["end"]:
            return s, info["level"], info["focus"]
    return 6, "B2", "advanced"


def get_fmu_level(episode_num: int) -> str:
    """Estimate CEFR level for an FMU episode."""
    if episode_num <= 20:
        return "A1"
    if episode_num <= 40:
        return "A2"
    return "B1"


# ── iTunes API scraping ─────────────────────────────────────────

def fetch_itunes_episodes(podcast_id: int, limit: int = 300) -> list[dict]:
    """Fetch podcast episodes from iTunes Lookup API."""
    url = f"https://itunes.apple.com/lookup?id={podcast_id}&media=podcast&entity=podcastEpisode&limit={limit}"
    client = httpx.Client(follow_redirects=True, timeout=REQUEST_TIMEOUT)
    try:
        r = client.get(url)
        r.raise_for_status()
        data = r.json()
        return [e for e in data.get("results", []) if e.get("kind") == "podcast-episode"]
    finally:
        client.close()


def parse_ulp_itunes(episodes: list[dict]) -> list[dict]:
    """Parse ULP episodes from iTunes into our format."""
    entries: list[dict] = []
    for ep in episodes:
        title = ep.get("trackName", "")
        desc = ep.get("description", "")[:500]
        release = ep.get("releaseDate", "")[:10]

        # Parse episode titles — multiple formats:
        # S2,4-6: "ULP S-NN | Title UK | Title EN"
        # S3:     "ULP 3-NN Title UK – Title EN + Grammar note"
        # Special: "Епізод №100! ..."
        m = re.match(r"ULP\s+(\d+)-(\d+)\s*\|\s*(.*?)(?:\s*\|\s*(.*))?$", title)
        if m:
            season = int(m.group(1))
            ep_num = int(m.group(2))
            title_uk = m.group(3).strip()
            title_en = (m.group(4) or "").strip()
        else:
            # Season 3 format: "ULP 3-NN Title UK – Title EN"
            m2 = re.match(r"ULP\s+(\d+)-(\d+)\s+(.*)", title)
            if m2:
                season = int(m2.group(1))
                ep_num = int(m2.group(2))
                rest = m2.group(3).strip()
                # Split on " – " (en dash) or " - " (hyphen) between UK and EN parts
                parts = re.split(r"\s+[–—-]\s+", rest, maxsplit=1)
                title_uk = parts[0].strip()
                title_en = parts[1].strip() if len(parts) > 1 else ""
            else:
                # Special episodes (e.g., "Епізод №100!")
                ep_num_m = re.search(r"(?:[\u0415\u0435Ee]p(?:ізод|isode)?\s*(?:№\s*)?|№\s*)(\d+)", title)
                ep_num = int(ep_num_m.group(1)) if ep_num_m else 0
                season = 0
                title_uk = title
                title_en = ""
                # Try to split on " – " for UK/EN parts
                parts = re.split(r"\s+[–—]\s+", title, maxsplit=1)
                if len(parts) == 2:
                    title_uk = parts[0].strip()
                    title_en = parts[1].strip()

        if ep_num == 0:
            continue

        if season == 0:
            season, _, _ = get_season_info(ep_num)

        _, level, focus = get_season_info(ep_num)
        clean_title = title_en if title_en else title_uk
        # Remove " Ukrainian Lessons Podcast" suffix from EN titles
        clean_title = re.sub(r"\s*\|?\s*Ukrainian Lessons(?:\s+Podcast)?\s*$", "", clean_title).strip()

        entries.append({
            "id": f"ulp-ep-{ep_num:03d}",
            "content_type": "podcast_episode",
            "series": "ULP",
            "season": season,
            "episode": ep_num,
            "url": f"{BASE_URL}/episode{ep_num}/",
            "title": clean_title,
            "title_uk": title_uk,
            "description": desc,
            "topics": extract_topics(title_uk, f"{title_en} {desc}"),
            "suggested_level": level,
            "season_focus": focus,
            "release_date": release,
        })

    return entries


def parse_fmu_itunes(episodes: list[dict]) -> list[dict]:
    """Parse FMU episodes from iTunes into our format."""
    entries: list[dict] = []
    for ep in episodes:
        title = ep.get("trackName", "")
        desc = ep.get("description", "")[:500]
        release = ep.get("releaseDate", "")[:10]

        # Parse "FMU 1-NN | Title | 5 Minute Ukrainian"
        m = re.match(r"FMU\s+\d+-(\d+)\s*\|\s*(.*?)(?:\s*\|\s*5\s*Minute\s*Ukrainian)?$", title)
        if m:
            ep_num = int(m.group(1))
            clean_title = m.group(2).strip()
        else:
            ep_num_m = re.search(r"(\d+)", title)
            ep_num = int(ep_num_m.group(1)) if ep_num_m else 0
            clean_title = title

        if ep_num == 0:
            continue

        level = get_fmu_level(ep_num)

        entries.append({
            "id": f"fmu-ep-{ep_num:03d}",
            "content_type": "podcast_episode_short",
            "series": "FMU",
            "episode": ep_num,
            "url": f"{BASE_URL}/fmu{ep_num}/",
            "title": clean_title,
            "description": desc,
            "topics": extract_topics(clean_title, desc),
            "suggested_level": level,
            "release_date": release,
        })

    return entries


# ── Website scraping (season 1 only) ────────────────────────────

def scrape_season1_from_website() -> list[dict]:
    """Scrape season 1 episode titles from the website (too old for iTunes).

    Uses requests (not httpx) — the website's Cloudflare responds better to it
    for the first request in a fresh session.
    """
    import requests as req

    session = req.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,uk;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
    })

    try:
        r = session.get(f"{BASE_URL}/season1/", timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        r.encoding = "utf-8"
        text = r.text
    except Exception as e:
        print(f"  WARNING: Could not fetch season1 page: {e}")
        return []
    finally:
        session.close()

    entries: list[dict] = []
    pattern = r'href="https://www\.ukrainianlessons\.com/episode(\d+)/?"[^>]*>([^<]*(?:<strong>[^<]*</strong>[^<]*)*)</a>'
    matches = re.findall(pattern, text)

    seen: set[int] = set()
    for ep_num_str, raw_title in matches:
        ep_num = int(ep_num_str)
        if ep_num in seen:
            continue

        # Clean HTML tags
        clean = re.sub(r"</?strong>", "", raw_title).strip()
        if clean.lower() in ("go to lesson", ""):
            continue

        seen.add(ep_num)

        # Remove ULP prefix
        title = re.sub(r"^ULP\s+\d+-\d+\s*", "", clean).strip()
        _, level, focus = get_season_info(ep_num)

        entries.append({
            "id": f"ulp-ep-{ep_num:03d}",
            "content_type": "podcast_episode",
            "series": "ULP",
            "season": 1,
            "episode": ep_num,
            "url": f"{BASE_URL}/episode{ep_num}/",
            "title": title,
            "title_uk": "",
            "description": "",
            "topics": extract_topics(title, ""),
            "suggested_level": level,
            "season_focus": focus,
            "release_date": "",
        })

    return entries


# Static fallback for season 1 (if website is blocked by Cloudflare)
SEASON1_TITLES: dict[int, str] = {
    1: "Informal Greetings in Ukrainian",
    2: "Formal Greetings and Saying Goodbye in Ukrainian + Pronouns",
    3: "How to Introduce Yourself in Ukrainian",
    4: "Talking About Where You Come From and Where You Live in Ukrainian",
    5: "Numbers 1-20 in Ukrainian + Pronunciation Trainer",
    6: "Talking about your family in Ukrainian + I have, you have",
    7: "More about your family in Ukrainian + Possessive Pronouns",
    8: "Talking about jobs and professions in Ukrainian",
    9: "How much does it cost? At the market in Ukraine",
    10: "About me in Ukrainian — Review 1-9",
    11: "Ordering drinks in Ukrainian",
    12: "Ordering food in Ukrainian",
    13: "More about food in Ukrainian",
    14: "Likes and dislikes — common verbs in Ukrainian",
    15: "Days of the Week, Months, Seasons + Pronunciation Trainer",
    16: "Talking about weather in Ukrainian",
    17: "Where is it? Here and there in Ukrainian",
    18: "Directions in Ukrainian",
    19: "Asking for a phone number in Ukrainian",
    20: "My favorite city in Ukrainian — Review 11-19",
    21: "What languages do you speak?",
    22: "Are you going to the party? — First verb conjugation in Ukrainian",
    23: "Happy New Year and Merry Christmas in Ukrainian",
    24: "What a surprise! Second conjugation in Ukrainian",
    25: "Colors in Ukrainian + Pronunciation Trainer",
    26: "Talking about traveling — Past tense in Ukrainian",
    27: "Traveling in Ukraine in winter — More Past tense",
    28: "Making plans for the weekend — Future tense in Ukrainian",
    29: "Talking about love in Ukrainian",
    30: "Review 21-29 — My travels in Ukrainian",
    31: "Shopping in Ukrainian — At the shoe shop",
    32: "Shopping for clothes — Accusative case in Ukrainian",
    33: "Talking about books in Ukrainian — Accusative case of people",
    34: "Going to the movies in Ukraine — Perfective verbs in Ukrainian",
    35: "Question words in Ukrainian + Pronunciation trainer",
    36: "Interview 1: Do you have a favorite subject?",
    37: "Interview 2: Are you studying or working?",
    38: "Interview 3: Oh! That's an interesting fact...",
    39: "Interview 4: Have you lived in Ukraine for a long time?",
    40: "Q&A — Questions and Answers",
}


def season1_fallback() -> list[dict]:
    """Generate season 1 entries from static title data."""
    entries: list[dict] = []
    for ep_num, title in SEASON1_TITLES.items():
        _, level, focus = get_season_info(ep_num)
        entries.append({
            "id": f"ulp-ep-{ep_num:03d}",
            "content_type": "podcast_episode",
            "series": "ULP",
            "season": 1,
            "episode": ep_num,
            "url": f"{BASE_URL}/episode{ep_num}/",
            "title": title,
            "title_uk": "",
            "description": "",
            "topics": extract_topics(title, ""),
            "suggested_level": level,
            "season_focus": focus,
            "release_date": "",
        })
    return entries


# ── Blog articles (from existing catalog) ────────────────────────

def load_blog_articles() -> list[dict]:
    """Load blog articles from the existing crawl_ulp_blog.py catalog."""
    sys.path.insert(0, str(Path(__file__).parent.parent))
    try:
        from crawl_ulp_blog import ARTICLES
    except ImportError:
        print("  WARNING: could not import crawl_ulp_blog.ARTICLES")
        return []

    entries: list[dict] = []
    for i, (slug, title, category, topics, level, content_type) in enumerate(ARTICLES):
        entries.append({
            "id": f"ulp-blog-{i:03d}",
            "content_type": content_type,
            "category": category,
            "url": f"{BASE_URL}/{slug}/",
            "title": title,
            "topics": topics,
            "suggested_level": level,
        })

    return entries


# ── Assembly ─────────────────────────────────────────────────────

def build_db(ulp: list[dict], fmu: list[dict], blog: list[dict]) -> dict:
    """Assemble the unified resource database."""
    # Sort episodes by number
    ulp.sort(key=lambda x: x.get("episode", 0))
    fmu.sort(key=lambda x: x.get("episode", 0))

    return {
        "version": "3.0",
        "source": "Ukrainian Lessons (www.ukrainianlessons.com)",
        "generated_at": str(date.today()),
        "stats": {
            "ulp_episodes": len(ulp),
            "fmu_episodes": len(fmu),
            "blog_articles": len(blog),
            "total": len(ulp) + len(fmu) + len(blog),
        },
        "articles": blog + ulp + fmu,
    }


# ── Main ─────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Crawl ukrainianlessons.com podcast + blog")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--episodes-only", action="store_true", dest="episodes_only")
    parser.add_argument("--blog-only", action="store_true", dest="blog_only")
    parser.add_argument("--dry-run", action="store_true", dest="dry_run")
    args = parser.parse_args()

    ulp_episodes: list[dict] = []
    fmu_episodes: list[dict] = []
    blog_articles: list[dict] = []

    do_all = not (args.episodes_only or args.blog_only)

    if do_all or args.episodes_only:
        if args.dry_run:
            print("Would fetch: 240 ULP episodes (iTunes API + season1 page)")
            print("Would fetch: 60 FMU episodes (iTunes API)")
        else:
            # 1. Get seasons 2-6 from iTunes (200 episodes)
            print("Fetching ULP episodes from iTunes API...")
            itunes_raw = fetch_itunes_episodes(ULP_ITUNES_ID, limit=300)
            itunes_episodes = parse_ulp_itunes(itunes_raw)
            itunes_nums = {e["episode"] for e in itunes_episodes}
            print(f"  iTunes: {len(itunes_episodes)} episodes (range: {min(itunes_nums)}-{max(itunes_nums)})")

            # 2. Get season 1 from website (too old for iTunes 200-limit)
            print("Fetching season 1 from website...")
            s1_episodes = scrape_season1_from_website()
            s1_only = [e for e in s1_episodes if e["episode"] not in itunes_nums]
            if not s1_only:
                print("  Website blocked — using static fallback for season 1")
                s1_only = [e for e in season1_fallback() if e["episode"] not in itunes_nums]
            print(f"  Season 1: {len(s1_only)} episodes")

            ulp_episodes = itunes_episodes + s1_only

            # 3. Check coverage
            all_nums = {e["episode"] for e in ulp_episodes}
            missing = set(range(1, 241)) - all_nums
            if missing:
                print(f"  Missing episodes: {sorted(missing)}")
            else:
                print("  Complete: all 240 episodes covered")

            # 4. Get FMU
            print("Fetching FMU episodes from iTunes API...")
            fmu_raw = fetch_itunes_episodes(FMU_ITUNES_ID, limit=100)
            fmu_episodes = parse_fmu_itunes(fmu_raw)
            print(f"  FMU: {len(fmu_episodes)} episodes")

    if do_all or args.blog_only:
        if args.dry_run:
            print("Would load: 119 blog articles (existing catalog)")
        else:
            print("Loading blog articles from catalog...")
            blog_articles = load_blog_articles()
            print(f"  Blog: {len(blog_articles)} articles")

    db = build_db(ulp_episodes, fmu_episodes, blog_articles)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(db, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    prefix = "[DRY RUN] " if args.dry_run else ""
    print(f"\n{prefix}Wrote {db['stats']['total']} entries to {args.output}")
    print(f"  ULP episodes: {db['stats']['ulp_episodes']}")
    print(f"  FMU episodes: {db['stats']['fmu_episodes']}")
    print(f"  Blog articles: {db['stats']['blog_articles']}")

    # Show per-season breakdown
    if ulp_episodes:
        print("\n  Per season:")
        for s in range(1, 7):
            count = len([e for e in ulp_episodes if e.get("season") == s])
            info = SEASONS.get(s, {})
            print(f"    S{s} ({info.get('level', '?')}): {count} episodes — {info.get('focus', '')}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
