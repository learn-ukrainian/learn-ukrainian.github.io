#!/usr/bin/env python3
"""Incremental ingest and word/usage-pair extractor for Ukrainian usage sources.

Supported sources:
1. Glavcom «Мовне питання» (Olha Vasylieva column archive)
   Source: https://glavcom.ua/specprojects/movne_pytannya.html
2. Мова – ДНК нації (mova.ua / ukr-mova.in.ua)
   Source: https://ukr-mova.in.ua/

Features:
- Honest identifying User-Agent by default with CLI override
- Immediate circuit-breaker stop on HTTP 403 (does not retry or corrupt state)
- Exponential backoff on HTTP 429 and 5xx, respecting Retry-After headers
- Incremental mode (--incremental, default true) checking existing SQLite records
  and only requesting unseen / un-ingested articles
- Full fidelity: untruncated raw HTML, article text, content SHA-256, and metadata
- Structured usage-advice pair extraction with linguistic reasoning and provenance
- Summary JSON export for downstream lexicon review and UNLP dataset integration
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import email.utils
import hashlib
import json
import logging
import re
import signal
import sqlite3
import sys
import time
import urllib.parse
import xml.etree.ElementTree as ET
from collections.abc import Callable
from enum import StrEnum
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger("usage_advice_ingest")

DEFAULT_USER_AGENT = (
    "learn-ukrainian-usage-ingest/1.0 "
    "(noncommercial educational research; "
    "https://github.com/learn-ukrainian/learn-ukrainian.github.io)"
)

DEFAULT_MOVNE_DB = Path("data/movne_pytannya.db")
DEFAULT_MOVAUA_DB = Path("data/movaua.db")

MOVNE_AUTHOR = "Ольга Васильєва, редакторка та мовознавиця, колонка «Мовне питання» (Главком)"
MOVAUA_CREDIT = "Мова – ДНК нації (ukr-mova.in.ua)"
MOVAUA_SOURCE_ID = "movaua_ukr_mova"

# Exit codes following repository standards
EXIT_OK = 0
EXIT_USAGE_ERROR = 2
EXIT_HTTP_403_FORBIDDEN = 3
EXIT_PARSE_ERROR = 4
EXIT_HTTP_SERVER_ERROR = 5

_STOP_REQUESTED = False


def _sig_handler(signum: int, frame: Any) -> None:  # pragma: no cover
    global _STOP_REQUESTED
    logger.info("Signal %s received; finishing current item before graceful exit...", signum)
    _STOP_REQUESTED = True


class UsageAdviceIngestError(Exception):
    """Base exception for usage advice ingest errors."""


class AccessDeniedError(UsageAdviceIngestError):
    """Raised when an endpoint returns HTTP 403 Forbidden."""


class RateLimitOrServerError(UsageAdviceIngestError):
    """Raised when rate limits (429) or server errors (5xx) exhaust retries."""


class SourceChoice(StrEnum):
    MOVNE = "movne_pytannya"
    MOVAUA = "movaua"
    ALL = "all"


@dataclasses.dataclass(frozen=True, slots=True)
class IngestStats:
    source: str
    total_manifest: int
    cached_existing: int
    fetched_new: int
    pairs_extracted: int
    errors: int
    interrupted: bool = False


# ---------------------------------------------------------------------------
# HTTP & Retry Utilities
# ---------------------------------------------------------------------------


def parse_retry_after(header_val: str | None) -> float | None:
    """Parse standard HTTP Retry-After header (seconds or HTTP date)."""
    if not header_val or not header_val.strip():
        return None
    val = header_val.strip()
    if val.isdigit():
        return max(0.0, float(val))
    try:
        parsed_date = email.utils.parsedate_to_datetime(val)
        if parsed_date is not None:
            now = dt.datetime.now(dt.UTC)
            delta = (parsed_date - now).total_seconds()
            return max(0.0, delta)
    except Exception:
        pass
    return None


def polite_get(
    session: requests.Session,
    url: str,
    *,
    delay: float = 1.0,
    max_retries: int = 3,
    retry_backoff: float = 2.0,
    timeout: float = 20.0,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> requests.Response:
    """Perform polite HTTP GET with 403 circuit breaker and 429/5xx backoff.

    - Immediately raises AccessDeniedError on HTTP 403 (never retries).
    - Backs off exponentially on HTTP 429 / 5xx, respecting Retry-After.
    - Honors graceful termination signal.
    """
    global _STOP_REQUESTED
    if _STOP_REQUESTED:
        raise UsageAdviceIngestError("Operation interrupted by user or supervisor.")

    attempt = 0
    while True:
        try:
            resp = session.get(url, timeout=timeout)
        except requests.RequestException as exc:
            if attempt >= max_retries:
                raise RateLimitOrServerError(
                    f"Network error requesting {url} after {max_retries} retries: {exc}"
                ) from exc
            wait_s = delay * (retry_backoff**attempt)
            logger.warning("Network error on %s: %s; retrying in %.1fs", url, exc, wait_s)
            sleep_fn(wait_s)
            attempt += 1
            continue

        if resp.status_code == 200:
            if delay > 0:
                sleep_fn(delay)
            return resp

        if resp.status_code == 403:
            logger.error("HTTP 403 Forbidden received for %s. Circuit-breaker stopping.", url)
            raise AccessDeniedError(f"HTTP 403 Forbidden for {url}")

        if resp.status_code == 429 or 500 <= resp.status_code < 600:
            if attempt >= max_retries:
                raise RateLimitOrServerError(f"HTTP {resp.status_code} for {url} after {max_retries} retries.")
            retry_after = parse_retry_after(resp.headers.get("Retry-After"))
            wait_s = retry_after if retry_after is not None else delay * (retry_backoff**attempt)
            logger.warning(
                "HTTP %s for %s; retrying in %.1fs (attempt %d/%d)",
                resp.status_code,
                url,
                wait_s,
                attempt + 1,
                max_retries,
            )
            sleep_fn(wait_s)
            attempt += 1
            continue

        # For 404 or other 4xx client errors, return without retry
        if delay > 0:
            sleep_fn(delay)
        return resp


# ---------------------------------------------------------------------------
# Schema Management
# ---------------------------------------------------------------------------


def ensure_movne_schema(conn: sqlite3.Connection) -> None:
    """Create schema for Glavcom «Мовне питання»."""
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS movne_pytannya_issues (
                issue_number INTEGER PRIMARY KEY,
                url TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                date TEXT NOT NULL,
                description TEXT NOT NULL,
                raw_html TEXT NOT NULL,
                article_text TEXT NOT NULL,
                content_sha256 TEXT NOT NULL,
                fetched_at TEXT NOT NULL
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS movne_word_pairs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                issue_number INTEGER NOT NULL,
                question_num INTEGER NOT NULL,
                reader_name TEXT NOT NULL,
                question_raw TEXT NOT NULL,
                questioned_form TEXT NOT NULL,
                verdict_form TEXT NOT NULL,
                verdict_type TEXT NOT NULL,
                reasoning TEXT NOT NULL,
                url TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (issue_number) REFERENCES movne_pytannya_issues(issue_number)
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_movne_pairs_issue ON movne_word_pairs(issue_number);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_movne_pairs_questioned ON movne_word_pairs(questioned_form);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_movne_pairs_verdict ON movne_word_pairs(verdict_form);")


def ensure_movaua_schema(conn: sqlite3.Connection) -> None:
    """Create schema for Мова – ДНК нації (mova.ua / ukr-mova.in.ua)."""
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS movaua_articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL UNIQUE,
                section TEXT NOT NULL,
                title TEXT NOT NULL,
                date TEXT,
                image_url TEXT,
                image_alt TEXT,
                raw_html TEXT NOT NULL,
                article_text TEXT NOT NULL,
                content_sha256 TEXT NOT NULL,
                fetched_at TEXT NOT NULL
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS movaua_usage_pairs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                category TEXT NOT NULL,
                questioned_form TEXT,
                recommended_form TEXT,
                pair_type TEXT NOT NULL,
                reasoning TEXT NOT NULL,
                source_title TEXT NOT NULL,
                credit TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (article_id) REFERENCES movaua_articles(id)
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_movaua_articles_url ON movaua_articles(url);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_movaua_articles_section ON movaua_articles(section);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_movaua_pairs_article ON movaua_usage_pairs(article_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_movaua_pairs_questioned ON movaua_usage_pairs(questioned_form);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_movaua_pairs_recommended ON movaua_usage_pairs(recommended_form);")


# ---------------------------------------------------------------------------
# Extraction Logic
# ---------------------------------------------------------------------------


def extract_movne_word_pairs(
    issue_number: int,
    url: str,
    raw_html: str,
    *,
    created_at: str | None = None,
) -> list[dict[str, Any]]:
    """Parse questions and answers from Glavcom «Мовне питання» article HTML."""
    soup = BeautifulSoup(raw_html, "html.parser")
    body = soup.find("div", class_="post_text") or soup.find("div", class_="art_body_uniq")
    if not body:
        return []

    timestamp = created_at or dt.datetime.now(dt.UTC).isoformat()
    headings = body.find_all(["h2", "h3", "h4"])
    pairs: list[dict[str, Any]] = []

    for h in headings:
        txt = h.get_text().strip()
        m = re.search(r"•?\s*(\d+)\s*•?", txt)
        if not m:
            continue
        q_num = int(m.group(1))

        curr = h.find_next_sibling()
        q_text = ""
        ans_parts: list[str] = []
        while curr and curr.name not in ("h2", "h3", "h4"):
            if curr.name == "p":
                p_str = curr.get_text().strip()
                if p_str:
                    if not q_text:
                        q_text = p_str
                    else:
                        ans_parts.append(p_str)
            curr = curr.find_next_sibling()

        if not q_text or not ans_parts:
            continue

        reader = ""
        question_body = q_text
        if ":" in q_text:
            parts = q_text.split(":", 1)
            if len(parts[0].strip()) < 80:
                reader = parts[0].strip()
                question_body = parts[1].strip()

        questioned_form = ""
        quotes = re.findall(r"[«\"“]([^»\"”]+)[»\"”]", question_body)
        if quotes:
            questioned_form = ", ".join(quotes[:3])
        elif " чи " in question_body:
            m_chi = re.search(r"([А-Яа-яЄєІіЇїҐґ'\-]+)\s+чи\s+([А-Яа-яЄєІіЇїҐґ'\-]+)", question_body)
            if m_chi:
                questioned_form = f"{m_chi.group(1)} чи {m_chi.group(2)}"
        if not questioned_form:
            questioned_form = question_body[:60].strip()

        reasoning = "\n\n".join(ans_parts)
        first_ans = ans_parts[0]

        verdict_type = "advice"
        verdict_form = ""

        if "правильн" in first_ans.lower():
            m_prav = re.search(
                r"правильно(?:\s+писати|\s+казати|\s+вживати)?(?:\s*[:–—-])?\s*([^.;,]+)",
                first_ans,
                flags=re.IGNORECASE,
            )
            if m_prav:
                verdict_form = m_prav.group(1).strip(' «"“”»')
                verdict_type = "preferred"

        if not verdict_form and quotes:
            for q in quotes:
                if q in first_ans:
                    verdict_form = q
                    break

        if not verdict_form:
            verdict_form = first_ans.split(".")[0].strip()[:80]

        first_ans_lower = first_ans.lower()
        if "обидві" in first_ans_lower or "обидва" in first_ans_lower or "і так, і так" in first_ans_lower:
            verdict_type = "both_valid"
        elif (
            "не є суржиком" in first_ans_lower
            or "не є росіянізмом" in first_ans_lower
            or "не росіянізм" in first_ans_lower
        ):
            verdict_type = "not_russianism"
        elif "неправильно" in first_ans_lower or "не варто" in first_ans_lower:
            verdict_type = "incorrect"

        pairs.append(
            {
                "issue_number": issue_number,
                "question_num": q_num,
                "reader_name": reader,
                "question_raw": q_text,
                "questioned_form": questioned_form,
                "verdict_form": verdict_form,
                "verdict_type": verdict_type,
                "reasoning": reasoning,
                "url": url,
                "created_at": timestamp,
            }
        )

    return pairs


def clean_movaua_title(title: str) -> str:
    """Strip site branding suffix from title."""
    return re.sub(r"\s*\|\s*Мова\s*[-–—]?\s*ДНК\s*нації.*$", "", title, flags=re.IGNORECASE).strip()


def extract_movaua_usage_pairs(
    article_id: int,
    url: str,
    section: str,
    title: str,
    image_alt: str,
    article_text: str,
    *,
    created_at: str | None = None,
) -> list[dict[str, Any]]:
    """Extract structured usage-advice pairs from mova.ua article content."""
    pairs: list[dict[str, Any]] = []
    timestamp = created_at or dt.datetime.now(dt.UTC).isoformat()
    clean_t = clean_movaua_title(title)
    category = section.split("/")[-1] if "/" in section else section

    # 1. Anti-surzhyk
    if "antusurzhuk" in section:
        m = re.match(r"^([^?]+?)\s+чи\s+([^?]+?)(?:\?|$)", clean_t, re.IGNORECASE)
        if m:
            part1 = m.group(1).strip()
            part2 = m.group(2).strip()
            if image_alt and (part2.lower() in image_alt.lower() or image_alt.lower() in part2.lower()):
                q_form, r_form = part1, image_alt
            elif image_alt and (part1.lower() in image_alt.lower() or image_alt.lower() in part1.lower()):
                q_form, r_form = part2, image_alt
            else:
                q_form, r_form = part1, part2

            pairs.append(
                {
                    "article_id": article_id,
                    "url": url,
                    "category": category,
                    "questioned_form": q_form,
                    "recommended_form": r_form,
                    "pair_type": "anti_surzhyk",
                    "reasoning": article_text or clean_t,
                    "source_title": clean_t,
                    "credit": MOVAUA_CREDIT,
                    "created_at": timestamp,
                }
            )
        else:
            q_form = ""
            r_form = image_alt or clean_t
            m_calque = re.search(r"«([^»]+?)\s*—\s*калька»", article_text)
            if m_calque:
                q_form = m_calque.group(1).strip()
            pairs.append(
                {
                    "article_id": article_id,
                    "url": url,
                    "category": category,
                    "questioned_form": q_form,
                    "recommended_form": r_form,
                    "pair_type": "anti_surzhyk",
                    "reasoning": article_text or clean_t,
                    "source_title": clean_t,
                    "credit": MOVAUA_CREDIT,
                    "created_at": timestamp,
                }
            )

    # 2. Paronyms
    elif "paronimu" in section:
        m = re.match(r"^([^?.]+?)\s+і\s+([^?.]+?)(?:[.?]|$)", clean_t, re.IGNORECASE)
        if m:
            w1, w2 = m.group(1).strip(), m.group(2).strip()
            pairs.append(
                {
                    "article_id": article_id,
                    "url": url,
                    "category": category,
                    "questioned_form": f"{w1} vs {w2}",
                    "recommended_form": f"{w1} / {w2} (диференціація значень)",
                    "pair_type": "paronym",
                    "reasoning": article_text or clean_t,
                    "source_title": clean_t,
                    "credit": MOVAUA_CREDIT,
                    "created_at": timestamp,
                }
            )
        else:
            pairs.append(
                {
                    "article_id": article_id,
                    "url": url,
                    "category": category,
                    "questioned_form": "",
                    "recommended_form": image_alt or clean_t,
                    "pair_type": "paronym",
                    "reasoning": article_text or clean_t,
                    "source_title": clean_t,
                    "credit": MOVAUA_CREDIT,
                    "created_at": timestamp,
                }
            )

    # 3. Orthography
    elif "orfografiya" in section:
        m = re.match(r"^([^?]+?)\s+чи\s+([^?]+?)(?:\?|$)", clean_t, re.IGNORECASE)
        if m:
            part1, part2 = m.group(1).strip(), m.group(2).strip()
            if image_alt and (part1.lower() in image_alt.lower() or image_alt.lower() in part1.lower()):
                q_form, r_form = part2, image_alt
            elif image_alt and (part2.lower() in image_alt.lower() or image_alt.lower() in part2.lower()):
                q_form, r_form = part1, image_alt
            else:
                q_form, r_form = part2, part1
            pairs.append(
                {
                    "article_id": article_id,
                    "url": url,
                    "category": category,
                    "questioned_form": q_form,
                    "recommended_form": r_form,
                    "pair_type": "orthography",
                    "reasoning": article_text or clean_t,
                    "source_title": clean_t,
                    "credit": MOVAUA_CREDIT,
                    "created_at": timestamp,
                }
            )
        else:
            pairs.append(
                {
                    "article_id": article_id,
                    "url": url,
                    "category": category,
                    "questioned_form": "",
                    "recommended_form": image_alt or clean_t,
                    "pair_type": "orthography",
                    "reasoning": article_text or clean_t,
                    "source_title": clean_t,
                    "credit": MOVAUA_CREDIT,
                    "created_at": timestamp,
                }
            )

    # 4. Stress
    elif "nagolos" in section:
        m = re.search(r"«([^»]+)»", clean_t)
        word = m.group(1).strip() if m else clean_t
        pairs.append(
            {
                "article_id": article_id,
                "url": url,
                "category": category,
                "questioned_form": word,
                "recommended_form": image_alt or word,
                "pair_type": "stress",
                "reasoning": article_text or clean_t,
                "source_title": clean_t,
                "credit": MOVAUA_CREDIT,
                "created_at": timestamp,
            }
        )

    # 5. Synonyms
    elif "sunonimu" in section:
        m = re.search(r"«([^»]+)»", clean_t)
        word = m.group(1).strip() if m else clean_t
        pairs.append(
            {
                "article_id": article_id,
                "url": url,
                "category": category,
                "questioned_form": word,
                "recommended_form": image_alt or word,
                "pair_type": "synonym",
                "reasoning": article_text or clean_t,
                "source_title": clean_t,
                "credit": MOVAUA_CREDIT,
                "created_at": timestamp,
            }
        )

    # 6. Idioms
    elif "frazeologizmu" in section:
        m = re.search(r"«([^»]+)»", clean_t)
        idiom = m.group(1).strip() if m else (image_alt or clean_t)
        pairs.append(
            {
                "article_id": article_id,
                "url": url,
                "category": category,
                "questioned_form": "",
                "recommended_form": idiom,
                "pair_type": "idiom",
                "reasoning": article_text or clean_t,
                "source_title": clean_t,
                "credit": MOVAUA_CREDIT,
                "created_at": timestamp,
            }
        )

    # 7. General rule advice
    else:
        pairs.append(
            {
                "article_id": article_id,
                "url": url,
                "category": category,
                "questioned_form": "",
                "recommended_form": image_alt or clean_t,
                "pair_type": "rule_advice",
                "reasoning": article_text or clean_t,
                "source_title": clean_t,
                "credit": MOVAUA_CREDIT,
                "created_at": timestamp,
            }
        )

    return pairs


# ---------------------------------------------------------------------------
# Manifest Discovery
# ---------------------------------------------------------------------------


def discover_movne_manifest(
    session: requests.Session,
    *,
    pages: list[str] | None = None,
    delay: float = 1.0,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> list[dict[str, Any]]:
    """Discover all issues from Glavcom archive index pages."""
    target_pages = pages or [
        "https://glavcom.ua/specprojects/movne_pytannya.html",
        "https://glavcom.ua/specprojects/movne_pytannya/p2.html",
    ]

    raw_items: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    for p_url in target_pages:
        resp = polite_get(session, p_url, delay=delay, sleep_fn=sleep_fn)
        if resp.status_code != 200:
            logger.warning("Failed to fetch archive page %s (HTTP %s)", p_url, resp.status_code)
            continue
        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.find_all("div", class_="article_story_list"):
            title_div = a.find("div", class_="article_title")
            link = title_div.find("a") if title_div else None
            desc_div = a.find("div", class_="article_description")
            date_div = a.find("div", class_="article_date")
            if not link:
                continue
            href = link.get("href", "")
            if not href.startswith("http"):
                href = urllib.parse.urljoin("https://glavcom.ua", href)
            if href in seen_urls:
                continue
            seen_urls.add(href)
            raw_items.append(
                {
                    "url": href,
                    "title": link.get_text().strip(),
                    "description": desc_div.get_text().strip() if desc_div else "",
                    "date": date_div.get_text().strip() if date_div else "",
                }
            )

    # Chronological numbering: earliest publication is #1
    ordered: list[dict[str, Any]] = []
    for idx, item in enumerate(reversed(raw_items), 1):
        c = dict(item)
        c["issue_number"] = idx
        ordered.append(c)
    return ordered


def discover_movaua_manifest(
    session: requests.Session,
    *,
    sitemap_url: str = "https://ukr-mova.in.ua/sitemap.xml",
    delay: float = 1.0,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> list[dict[str, Any]]:
    """Discover URLs from mova.ua sitemap and pagination."""
    resp = polite_get(session, sitemap_url, delay=delay, sleep_fn=sleep_fn)
    all_urls: set[str] = set()
    if resp.status_code == 200:
        try:
            root = ET.fromstring(resp.content)
            for loc in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
                text = (loc.text or "").strip()
                if text and text.startswith("https://ukr-mova.in.ua/"):
                    all_urls.add(text)
        except ET.ParseError as e:
            logger.warning("Error parsing sitemap XML: %s", e)

    # Filter out RSS and non-content endpoints
    clean_urls: list[dict[str, Any]] = []
    for u in sorted(all_urls):
        if "/rss" in u or u.endswith("/policy") or u.endswith("/policy/"):
            continue
        rel = u.replace("https://ukr-mova.in.ua/", "").strip("/")
        parts = rel.split("/")
        sec = parts[0] if parts and parts[0] else "root"
        if sec == "library" and len(parts) > 1:
            sec = f"library/{parts[1]}"
        clean_urls.append({"url": u, "section": sec})

    return clean_urls


# ---------------------------------------------------------------------------
# Ingest Runners
# ---------------------------------------------------------------------------


def ingest_movne_pytannya(
    conn: sqlite3.Connection,
    *,
    session: requests.Session | None = None,
    manifest: list[dict[str, Any]] | None = None,
    incremental: bool = True,
    limit: int | None = None,
    delay: float = 1.5,
    max_retries: int = 3,
    retry_backoff: float = 2.0,
    user_agent: str = DEFAULT_USER_AGENT,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> IngestStats:
    """Ingest Glavcom «Мовне питання» issues and extract pairs."""
    global _STOP_REQUESTED
    ensure_movne_schema(conn)

    sess = session or requests.Session()
    if hasattr(sess, "headers") and hasattr(sess.headers, "setdefault"):
        sess.headers.setdefault("User-Agent", user_agent)

    items = manifest if manifest is not None else discover_movne_manifest(sess, delay=delay, sleep_fn=sleep_fn)
    total_manifest = len(items)

    existing_rows = conn.execute("SELECT url FROM movne_pytannya_issues WHERE content_sha256 != ''").fetchall()
    existing_urls = {r[0] for r in existing_rows}
    cached_existing = len(existing_urls)

    pending = [it for it in items if it["url"] not in existing_urls] if incremental else items

    if limit is not None and limit >= 0:
        pending = pending[:limit]

    fetched_new = 0
    pairs_extracted = 0
    errors = 0

    for item in pending:
        if _STOP_REQUESTED:
            break

        url = item["url"]
        issue_number = item["issue_number"]

        try:
            resp = polite_get(
                sess,
                url,
                delay=delay,
                max_retries=max_retries,
                retry_backoff=retry_backoff,
                sleep_fn=sleep_fn,
            )
        except AccessDeniedError:
            raise
        except Exception as exc:
            logger.error("Failed to fetch issue %s (%s): %s", issue_number, url, exc)
            errors += 1
            continue

        if resp.status_code != 200:
            logger.warning("Issue %s (%s) returned HTTP %s", issue_number, url, resp.status_code)
            errors += 1
            continue

        html = resp.text
        sha = hashlib.sha256(html.encode("utf-8")).hexdigest()
        soup = BeautifulSoup(html, "html.parser")
        body_tag = soup.find("div", class_="post_text") or soup.find("div", class_="art_body_uniq")
        art_text = body_tag.get_text(separator="\n").strip() if body_tag else ""
        fetched_at = dt.datetime.now(dt.UTC).isoformat()

        with conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO movne_pytannya_issues
                (issue_number, url, title, date, description, raw_html, article_text, content_sha256, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    issue_number,
                    url,
                    item.get("title", ""),
                    item.get("date", ""),
                    item.get("description", ""),
                    html,
                    art_text,
                    sha,
                    fetched_at,
                ),
            )

            pairs = extract_movne_word_pairs(issue_number, url, html, created_at=fetched_at)
            conn.execute("DELETE FROM movne_word_pairs WHERE issue_number = ?", (issue_number,))
            for p in pairs:
                conn.execute(
                    """
                    INSERT INTO movne_word_pairs
                    (issue_number, question_num, reader_name, question_raw, questioned_form,
                     verdict_form, verdict_type, reasoning, url, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        p["issue_number"],
                        p["question_num"],
                        p["reader_name"],
                        p["question_raw"],
                        p["questioned_form"],
                        p["verdict_form"],
                        p["verdict_type"],
                        p["reasoning"],
                        p["url"],
                        p["created_at"],
                    ),
                )
            pairs_extracted += len(pairs)

        fetched_new += 1

    return IngestStats(
        source="movne_pytannya",
        total_manifest=total_manifest,
        cached_existing=cached_existing,
        fetched_new=fetched_new,
        pairs_extracted=pairs_extracted,
        errors=errors,
        interrupted=_STOP_REQUESTED,
    )


def ingest_movaua(
    conn: sqlite3.Connection,
    *,
    session: requests.Session | None = None,
    manifest: list[dict[str, Any]] | None = None,
    incremental: bool = True,
    limit: int | None = None,
    delay: float = 1.0,
    max_retries: int = 3,
    retry_backoff: float = 2.0,
    user_agent: str = DEFAULT_USER_AGENT,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> IngestStats:
    """Ingest mova.ua articles and extract usage advice pairs."""
    global _STOP_REQUESTED
    ensure_movaua_schema(conn)

    sess = session or requests.Session()
    if hasattr(sess, "headers") and hasattr(sess.headers, "setdefault"):
        sess.headers.setdefault("User-Agent", user_agent)

    items = manifest if manifest is not None else discover_movaua_manifest(sess, delay=delay, sleep_fn=sleep_fn)
    total_manifest = len(items)

    existing_rows = conn.execute("SELECT url FROM movaua_articles WHERE content_sha256 != ''").fetchall()
    existing_urls = {r[0] for r in existing_rows}
    cached_existing = len(existing_urls)

    pending = [it for it in items if it["url"] not in existing_urls] if incremental else items

    if limit is not None and limit >= 0:
        pending = pending[:limit]

    fetched_new = 0
    pairs_extracted = 0
    errors = 0

    for item in pending:
        if _STOP_REQUESTED:
            break

        url = item["url"]
        section = item.get("section", "root")

        try:
            resp = polite_get(
                sess,
                url,
                delay=delay,
                max_retries=max_retries,
                retry_backoff=retry_backoff,
                sleep_fn=sleep_fn,
            )
        except AccessDeniedError:
            raise
        except Exception as exc:
            logger.error("Failed to fetch movaua %s: %s", url, exc)
            errors += 1
            continue

        if resp.status_code != 200:
            logger.warning("movaua %s returned HTTP %s", url, resp.status_code)
            errors += 1
            continue

        html = resp.text
        sha = hashlib.sha256(html.encode("utf-8")).hexdigest()
        soup = BeautifulSoup(html, "html.parser")

        title_tag = soup.find("title")
        raw_title = title_tag.get_text().strip() if title_tag else ""
        date_str = ""
        img_url, img_alt = "", ""

        # Extract illustration image if present
        main_img = soup.find("img", class_="img-responsive") or soup.find("div", class_="illustration")
        if main_img:
            img_tag = main_img if main_img.name == "img" else main_img.find("img")
            if img_tag:
                img_url = img_tag.get("src", "")
                img_alt = img_tag.get("alt", "").strip()

        content_div = soup.find("div", class_="article-content") or soup.find("div", class_="text") or soup.body
        art_text = content_div.get_text(separator="\n").strip() if content_div else ""
        fetched_at = dt.datetime.now(dt.UTC).isoformat()

        with conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO movaua_articles
                (url, section, title, date, image_url, image_alt, raw_html, article_text, content_sha256, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (url, section, raw_title, date_str, img_url, img_alt, html, art_text, sha, fetched_at),
            )
            article_id = conn.execute("SELECT id FROM movaua_articles WHERE url = ?", (url,)).fetchone()[0]

            pairs = extract_movaua_usage_pairs(
                article_id,
                url,
                section,
                raw_title,
                img_alt,
                art_text,
                created_at=fetched_at,
            )
            conn.execute("DELETE FROM movaua_usage_pairs WHERE article_id = ?", (article_id,))
            for p in pairs:
                conn.execute(
                    """
                    INSERT INTO movaua_usage_pairs
                    (article_id, url, category, questioned_form, recommended_form,
                     pair_type, reasoning, source_title, credit, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        p["article_id"],
                        p["url"],
                        p["category"],
                        p["questioned_form"],
                        p["recommended_form"],
                        p["pair_type"],
                        p["reasoning"],
                        p["source_title"],
                        p["credit"],
                        p["created_at"],
                    ),
                )
            pairs_extracted += len(pairs)

        fetched_new += 1

    return IngestStats(
        source="movaua",
        total_manifest=total_manifest,
        cached_existing=cached_existing,
        fetched_new=fetched_new,
        pairs_extracted=pairs_extracted,
        errors=errors,
        interrupted=_STOP_REQUESTED,
    )


# ---------------------------------------------------------------------------
# Export Utilities
# ---------------------------------------------------------------------------


def export_movne_summary_json(conn: sqlite3.Connection, output_path: Path) -> dict[str, Any]:
    """Export summary of Glavcom «Мовне питання» data to JSON."""
    ensure_movne_schema(conn)
    issues_count = conn.execute("SELECT count(*) FROM movne_pytannya_issues").fetchone()[0]
    pairs = conn.execute(
        """
        SELECT issue_number, question_num, reader_name, questioned_form, verdict_form,
               verdict_type, reasoning, url
        FROM movne_word_pairs
        ORDER BY issue_number, question_num
        """
    ).fetchall()

    export_data = {
        "source": "glavcom_movne_pytannya",
        "author": MOVNE_AUTHOR,
        "exported_at": dt.datetime.now(dt.UTC).isoformat(),
        "total_issues": issues_count,
        "total_pairs": len(pairs),
        "pairs": [
            {
                "issue_number": r[0],
                "question_num": r[1],
                "reader_name": r[2],
                "questioned_form": r[3],
                "verdict_form": r[4],
                "verdict_type": r[5],
                "reasoning": r[6],
                "url": r[7],
            }
            for r in pairs
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(export_data, ensure_ascii=False, indent=2), encoding="utf-8")
    return export_data


def export_movaua_summary_json(conn: sqlite3.Connection, output_path: Path) -> dict[str, Any]:
    """Export summary of mova.ua data to JSON."""
    ensure_movaua_schema(conn)
    articles_count = conn.execute("SELECT count(*) FROM movaua_articles").fetchone()[0]
    pairs = conn.execute(
        """
        SELECT article_id, url, category, questioned_form, recommended_form,
               pair_type, reasoning, source_title, credit
        FROM movaua_usage_pairs
        ORDER BY article_id
        """
    ).fetchall()

    export_data = {
        "source": MOVAUA_SOURCE_ID,
        "credit": MOVAUA_CREDIT,
        "exported_at": dt.datetime.now(dt.UTC).isoformat(),
        "total_articles": articles_count,
        "total_pairs": len(pairs),
        "pairs": [
            {
                "article_id": r[0],
                "url": r[1],
                "category": r[2],
                "questioned_form": r[3],
                "recommended_form": r[4],
                "pair_type": r[5],
                "reasoning": r[6],
                "source_title": r[7],
                "credit": r[8],
            }
            for r in pairs
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(export_data, ensure_ascii=False, indent=2), encoding="utf-8")
    return export_data


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="usage_advice_ingest",
        description="Polite, incremental ingest and word/usage-pair extraction for Ukrainian language advice.",
    )
    parser.add_argument(
        "--source",
        type=SourceChoice,
        default=SourceChoice.ALL,
        choices=[SourceChoice.MOVNE, SourceChoice.MOVAUA, SourceChoice.ALL],
        help="Source to ingest (default: all)",
    )
    parser.add_argument(
        "--db-movne",
        type=Path,
        default=DEFAULT_MOVNE_DB,
        help="SQLite database path for Glavcom «Мовне питання»",
    )
    parser.add_argument(
        "--db-movaua",
        type=Path,
        default=DEFAULT_MOVAUA_DB,
        help="SQLite database path for Мова – ДНК нації",
    )
    parser.add_argument(
        "--incremental",
        dest="incremental",
        action="store_true",
        default=True,
        help="Skip already-ingested articles (default)",
    )
    parser.add_argument(
        "--no-incremental",
        dest="incremental",
        action="store_false",
        help="Re-ingest all articles even if present",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum new articles to fetch per source",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Polite inter-request delay in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum retries on 429/5xx (default: 3)",
    )
    parser.add_argument(
        "--retry-backoff",
        type=float,
        default=2.0,
        help="Exponential backoff multiplier (default: 2.0)",
    )
    parser.add_argument(
        "--user-agent",
        type=str,
        default=DEFAULT_USER_AGENT,
        help="Identifying User-Agent header",
    )
    parser.add_argument(
        "--export-json-movne",
        type=Path,
        default=None,
        help="Optional path to export Glavcom «Мовне питання» JSON summary",
    )
    parser.add_argument(
        "--export-json-movaua",
        type=Path,
        default=None,
        help="Optional path to export mova.ua JSON summary",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    signal.signal(signal.SIGINT, _sig_handler)
    signal.signal(signal.SIGTERM, _sig_handler)

    args = parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    stats_list: list[IngestStats] = []

    try:
        if args.source in (SourceChoice.MOVNE, SourceChoice.ALL):
            args.db_movne.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(args.db_movne) as conn:
                logger.info("Ingesting Glavcom «Мовне питання» into %s...", args.db_movne)
                s = ingest_movne_pytannya(
                    conn,
                    incremental=args.incremental,
                    limit=args.limit,
                    delay=args.delay,
                    max_retries=args.max_retries,
                    retry_backoff=args.retry_backoff,
                    user_agent=args.user_agent,
                )
                stats_list.append(s)
                logger.info(
                    "Movne: total=%d, cached=%d, fetched_new=%d, pairs=%d, errors=%d",
                    s.total_manifest,
                    s.cached_existing,
                    s.fetched_new,
                    s.pairs_extracted,
                    s.errors,
                )
                if args.export_json_movne:
                    export_movne_summary_json(conn, args.export_json_movne)
                    logger.info("Exported Movne summary JSON to %s", args.export_json_movne)

        if args.source in (SourceChoice.MOVAUA, SourceChoice.ALL):
            args.db_movaua.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(args.db_movaua) as conn:
                logger.info("Ingesting Мова – ДНК нації into %s...", args.db_movaua)
                s = ingest_movaua(
                    conn,
                    incremental=args.incremental,
                    limit=args.limit,
                    delay=args.delay,
                    max_retries=args.max_retries,
                    retry_backoff=args.retry_backoff,
                    user_agent=args.user_agent,
                )
                stats_list.append(s)
                logger.info(
                    "MovaUA: total=%d, cached=%d, fetched_new=%d, pairs=%d, errors=%d",
                    s.total_manifest,
                    s.cached_existing,
                    s.fetched_new,
                    s.pairs_extracted,
                    s.errors,
                )
                if args.export_json_movaua:
                    export_movaua_summary_json(conn, args.export_json_movaua)
                    logger.info("Exported MovaUA summary JSON to %s", args.export_json_movaua)

    except AccessDeniedError as exc:
        logger.error("HTTP 403 Forbidden encountered: %s", exc)
        return EXIT_HTTP_403_FORBIDDEN
    except RateLimitOrServerError as exc:
        logger.error("HTTP server/rate-limit error: %s", exc)
        return EXIT_HTTP_SERVER_ERROR
    except Exception as exc:
        logger.exception("Unexpected error in usage advice ingest: %s", exc)
        return EXIT_PARSE_ERROR

    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
