#!/usr/bin/env python3
"""Ingest bounded Goroh etymology snapshots for Word Atlas lemmas."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sqlite3
import sys
import time
import unicodedata
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

REPO = Path(__file__).resolve().parents[2]
DEFAULT_DB = REPO / "data" / "sources.db"
DEFAULT_MANIFEST = REPO / "starlight" / "src" / "data" / "lexicon-manifest.json"
GOROH_BASE = "https://goroh.pp.ua/Етимологія"
DEFAULT_USER_AGENT = (
    "learn-ukrainian-goroh-etymology/1.0 "
    "(noncommercial educational lookup; issue 2882)"
)

GOROH_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS goroh_etymology (
    requested_lemma TEXT PRIMARY KEY,
    headword TEXT NOT NULL DEFAULT '',
    etymology_text TEXT NOT NULL DEFAULT '',
    source_url TEXT NOT NULL DEFAULT '',
    retrieved_at TEXT NOT NULL DEFAULT '',
    content_hash TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_goroh_etymology_exact_lemma
    ON goroh_etymology(requested_lemma);
CREATE INDEX IF NOT EXISTS idx_goroh_etymology_headword
    ON goroh_etymology(headword);
"""

UPSERT_SQL = """
INSERT INTO goroh_etymology (
    requested_lemma,
    headword,
    etymology_text,
    source_url,
    retrieved_at,
    content_hash
)
VALUES (?, ?, ?, ?, ?, ?)
ON CONFLICT(requested_lemma) DO UPDATE SET
    headword = excluded.headword,
    etymology_text = excluded.etymology_text,
    source_url = excluded.source_url,
    retrieved_at = excluded.retrieved_at,
    content_hash = excluded.content_hash
"""

_SPACE_RE = re.compile(r"\s+")
_STRESS_MARK_RE = re.compile("[\u0300\u0301]")
_APOSTROPHES = ("'", "’", "ʼ")


class StopIngest(RuntimeError):
    """Raised when Goroh should not be contacted again in this run."""


def ensure_goroh_etymology_schema(conn: sqlite3.Connection) -> None:
    """Create the bounded Goroh cache table if missing."""
    conn.executescript(GOROH_SCHEMA_SQL)


def clean_text(value: str) -> str:
    """Collapse Goroh HTML text to a plain-text single paragraph."""
    cleaned = " ".join(str(value or "").replace("\xa0", " ").split())
    cleaned = cleaned.replace(" ,", ",").replace(" ;", ";").replace(" .", ".")
    cleaned = cleaned.replace("( ", "(").replace(" )", ")")
    return _SPACE_RE.sub(" ", cleaned).strip()


def lookup_key(value: str) -> str:
    """Return a lookup key without stress marks or apostrophe variants."""
    normalized = unicodedata.normalize("NFKD", clean_text(value))
    normalized = _STRESS_MARK_RE.sub("", normalized)
    normalized = unicodedata.normalize("NFC", normalized)
    normalized = normalized.replace("`", "'").replace("’", "'").replace("ʼ", "'")
    return normalized.casefold()


def headword_key(value: str) -> str:
    """Return the lexical part of a Goroh card header or variant item."""
    lexical = re.split(r"[«(]", clean_text(value), maxsplit=1)[0]
    return lookup_key(lexical.strip(" .,;:—-"))


def content_hash(text: str) -> str:
    """Return a stable content hash for one cached prose extract."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_atlas_lemmas(manifest_path: Path = DEFAULT_MANIFEST) -> list[str]:
    """Read Word Atlas lemmas from the generated manifest."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    lemmas: list[str] = []
    seen: set[str] = set()
    for entry in manifest.get("entries", []):
        lemma = clean_text(str(entry.get("lemma", "")))
        if not lemma or lemma in seen:
            continue
        seen.add(lemma)
        lemmas.append(lemma)
    return lemmas


def lookup_candidates(lemma: str) -> list[str]:
    """Return bounded Goroh lookup candidates for one Atlas lemma string."""
    candidates: list[str] = [clean_text(lemma)]
    for part in re.split(r"[/,]", lemma):
        part = clean_text(part)
        if not part:
            continue
        candidates.append(part)
    for candidate in list(candidates):
        if any(mark in candidate for mark in _APOSTROPHES):
            for apostrophe in _APOSTROPHES:
                candidates.append(candidate.replace("'", apostrophe).replace("’", apostrophe).replace("ʼ", apostrophe))
    seen: set[str] = set()
    return [item for item in candidates if item and not (item.casefold() in seen or seen.add(item.casefold()))]


def goroh_url(lemma: str) -> str:
    """Build a direct Goroh etymology URL for one lookup candidate."""
    return f"{GOROH_BASE}/{quote(lemma, safe='')}"


def _target_keys(requested_lemma: str) -> set[str]:
    return {lookup_key(candidate) for candidate in lookup_candidates(requested_lemma)}


def _variant_section_keys(card: Any) -> set[str]:
    keys: set[str] = set()
    for section in card.select(".section"):
        header = clean_text(" ".join(node.get_text(" ", strip=True) for node in section.select(".section-header")))
        if "Фонетичні та словотвірні варіанти" not in header:
            continue
        for item in section.select(".list-item"):
            key = headword_key(item.get_text(" ", strip=True))
            if key:
                keys.add(key)
        if not keys:
            for item in clean_text(section.get_text(" ", strip=True)).split():
                key = headword_key(item)
                if key:
                    keys.add(key)
    return keys


def _select_etymology_card(soup: BeautifulSoup, requested_lemma: str) -> Any | None:
    cards = soup.select(".etymology-root")
    targets = _target_keys(requested_lemma)
    for card in cards:
        header = card.select_one(".card-header")
        key = headword_key(header.get_text(" ", strip=True) if header else "")
        if key in targets:
            return card
    for card in cards:
        if _variant_section_keys(card) & targets:
            return card
    return None


def parse_goroh_html(
    page_html: str,
    *,
    requested_lemma: str,
    source_url: str,
    max_text_chars: int = 1200,
) -> dict[str, str] | None:
    """Parse one Goroh etymology page into a bounded cache row."""
    soup = BeautifulSoup(page_html, "html.parser")
    card = _select_etymology_card(soup, requested_lemma)
    if card is None:
        return None

    header = card.select_one(".card-header")
    headword = headword_key(header.get_text(" ", strip=True) if header else "")
    if not headword:
        return None

    prose_node = None
    for child in card.children:
        if getattr(child, "name", None) != "div":
            continue
        classes = set(child.get("class", []))
        if "section" in classes:
            break
        if "list" in classes:
            prose_node = child
            break
    if prose_node is None:
        return None

    text = clean_text(prose_node.get_text(" ", strip=True))
    if not text:
        return None
    if len(text) > max_text_chars:
        text = text[: max_text_chars - 1].rstrip(" ,.;:") + "…"

    return {
        "requested_lemma": clean_text(requested_lemma),
        "headword": headword,
        "etymology_text": text,
        "source_url": source_url,
        "retrieved_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat(),
        "content_hash": content_hash(text),
    }


def fetch_goroh_entry(
    lookup_lemma: str,
    *,
    requested_lemma: str,
    user_agent: str,
    timeout: int,
    max_text_chars: int,
) -> dict[str, str] | None:
    """Fetch and parse one direct Goroh etymology page."""
    url = goroh_url(lookup_lemma)
    try:
        response = requests.get(url, timeout=timeout, headers={"User-Agent": user_agent})
    except requests.RequestException as exc:
        raise StopIngest(f"Stopping after network error for {lookup_lemma}: {exc}") from exc

    if response.status_code == 429:
        raise StopIngest(f"Stopping after HTTP 429 from Goroh for {lookup_lemma}")
    if response.status_code == 404:
        return None
    if response.status_code >= 500:
        raise StopIngest(f"Stopping after HTTP {response.status_code} from Goroh for {lookup_lemma}")
    response.raise_for_status()

    return parse_goroh_html(
        response.text,
        requested_lemma=requested_lemma,
        source_url=response.url or url,
        max_text_chars=max_text_chars,
    )


def upsert_goroh_row(conn: sqlite3.Connection, row: dict[str, str]) -> None:
    """Upsert one parsed Goroh row."""
    conn.execute(
        UPSERT_SQL,
        (
            row["requested_lemma"],
            row["headword"],
            row["etymology_text"],
            row["source_url"],
            row["retrieved_at"],
            row["content_hash"],
        ),
    )


def _is_cached(conn: sqlite3.Connection, lemma: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM goroh_etymology WHERE requested_lemma = ? LIMIT 1",
        (clean_text(lemma),),
    ).fetchone()
    return row is not None


def ingest_goroh_etymology(
    db_path: Path,
    lemmas: list[str],
    *,
    refresh: bool,
    dry_run: bool,
    sleep_s: float,
    user_agent: str,
    timeout: int,
    max_text_chars: int,
) -> tuple[int, int]:
    """Fetch Atlas-bounded Goroh etymology rows into sources.db."""
    conn = None if dry_run else sqlite3.connect(str(db_path))
    fetched = 0
    loaded = 0
    try:
        if conn is not None:
            ensure_goroh_etymology_schema(conn)
        for lemma_index, lemma in enumerate(lemmas):
            if conn is not None and not refresh and _is_cached(conn, lemma):
                print(f"{lemma}: cached")
                continue

            row = None
            for candidate_index, candidate in enumerate(lookup_candidates(lemma)):
                if (lemma_index or candidate_index) and sleep_s > 0:
                    time.sleep(sleep_s)
                fetched += 1
                try:
                    row = fetch_goroh_entry(
                        candidate,
                        requested_lemma=lemma,
                        user_agent=user_agent,
                        timeout=timeout,
                        max_text_chars=max_text_chars,
                    )
                except StopIngest as exc:
                    print(str(exc), file=sys.stderr)
                    return fetched, loaded
                if row:
                    if candidate != lemma:
                        print(f"{lemma}: {row['headword']} via {candidate}")
                    else:
                        print(f"{lemma}: {row['headword']}")
                    break

            if not row:
                print(f"{lemma}: no Goroh etymology")
                if conn is not None and refresh:
                    with conn:
                        conn.execute(
                            "DELETE FROM goroh_etymology WHERE requested_lemma = ?",
                            (clean_text(lemma),),
                        )
                continue
            if dry_run:
                loaded += 1
                continue
            assert conn is not None
            with conn:
                upsert_goroh_row(conn, row)
            loaded += 1
        return fetched, loaded
    finally:
        if conn is not None:
            conn.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch explicit Goroh etymology pages for Word Atlas lemmas and cache bounded prose.\n"
            "This is a one-time ingest helper; build/enrich code must read sources.db only."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python scripts/ingest/goroh_etymology_ingest.py
  .venv/bin/python scripts/ingest/goroh_etymology_ingest.py --refresh --sleep 2

Outputs:
  Creates/updates the goroh_etymology table in data/sources.db for Atlas lemmas only.
  Stores a conservative plain-text extract plus source URL and attribution metadata.

Exit codes:
  0 on successful or partially stopped ingest; 2 when the manifest has no lemmas; >=1 on argument errors.
""",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help=f"Lexicon manifest to read. Default: {DEFAULT_MANIFEST}",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB,
        help=f"SQLite sources.db path to update. Default: {DEFAULT_DB}",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Fetch lemmas even when a cached Goroh row already exists.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and report rows but do not create or update the SQLite database.",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=1.75,
        help="Seconds to pause between Goroh requests. Default: 1.75.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=20,
        help="HTTP timeout in seconds. Default: 20.",
    )
    parser.add_argument(
        "--max-text-chars",
        type=int,
        default=1200,
        help="Maximum etymology prose characters stored per row. Default: 1200.",
    )
    parser.add_argument(
        "--user-agent",
        default=DEFAULT_USER_AGENT,
        help=f"HTTP User-Agent for direct Goroh requests. Default: {DEFAULT_USER_AGENT}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    lemmas = load_atlas_lemmas(args.manifest)
    if not lemmas:
        print(f"No Atlas lemmas found in {args.manifest}", file=sys.stderr)
        return 2
    fetched, loaded = ingest_goroh_etymology(
        args.db,
        lemmas,
        refresh=args.refresh,
        dry_run=args.dry_run,
        sleep_s=max(0.0, args.sleep),
        user_agent=args.user_agent,
        timeout=max(1, args.timeout),
        max_text_chars=max(1, args.max_text_chars),
    )
    print(f"Fetched {fetched} Goroh page(s); loaded {loaded} row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
