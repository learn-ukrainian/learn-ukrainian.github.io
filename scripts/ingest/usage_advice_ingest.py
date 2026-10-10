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
    user_agent: str | None = None,
    headers: dict[str, str] | None = None,
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

    req_headers = dict(headers or {})
    if user_agent:
        req_headers["User-Agent"] = user_agent
    elif "User-Agent" not in req_headers and hasattr(session, "headers") and "User-Agent" in session.headers:
        req_headers["User-Agent"] = session.headers["User-Agent"]

    attempt = 0
    while True:
        try:
            if req_headers:
                resp = session.get(url, headers=req_headers, timeout=timeout)
            else:
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
            wait_s = (
                min(retry_after, 60.0)
                if retry_after is not None
                else delay * (retry_backoff**attempt)
            )
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
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS movne_pytannya_issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL UNIQUE,
                issue_number INTEGER NOT NULL,
                title TEXT NOT NULL,
                date TEXT NOT NULL,
                description TEXT NOT NULL,
                raw_html TEXT NOT NULL,
                article_text TEXT NOT NULL,
                content_sha256 TEXT NOT NULL,
                fetched_at TEXT NOT NULL,
                error_status TEXT DEFAULT ''
            );
        """)
        cols = [r[1] for r in conn.execute("PRAGMA table_info(movne_pytannya_issues)").fetchall()]
        if "error_status" not in cols:
            conn.execute("ALTER TABLE movne_pytannya_issues ADD COLUMN error_status TEXT DEFAULT ''")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS movne_word_pairs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                issue_id INTEGER NOT NULL,
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
                FOREIGN KEY (issue_id) REFERENCES movne_pytannya_issues(id) ON DELETE CASCADE
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_movne_issues_url ON movne_pytannya_issues(url);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_movne_pairs_issue ON movne_word_pairs(issue_number);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_movne_pairs_issue_id ON movne_word_pairs(issue_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_movne_pairs_questioned ON movne_word_pairs(questioned_form);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_movne_pairs_verdict ON movne_word_pairs(verdict_form);")


def ensure_movaua_schema(conn: sqlite3.Connection) -> None:
    """Create schema for Мова – ДНК нації (mova.ua / ukr-mova.in.ua)."""
    with conn:
        conn.execute("PRAGMA foreign_keys = ON;")
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
                fetched_at TEXT NOT NULL,
                error_status TEXT DEFAULT ''
            );
        """)
        cols = [r[1] for r in conn.execute("PRAGMA table_info(movaua_articles)").fetchall()]
        if "error_status" not in cols:
            conn.execute("ALTER TABLE movaua_articles ADD COLUMN error_status TEXT DEFAULT ''")
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
                FOREIGN KEY (article_id) REFERENCES movaua_articles(id) ON DELETE CASCADE
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
    body = (
        soup.find("div", class_="post_text")
        or soup.find("div", class_="art_body_uniq")
        or soup.find("article")
        or soup.find("div", class_="article_content")
        or soup.body
    )
    if not body:
        return []

    timestamp = created_at or dt.datetime.now(dt.UTC).isoformat()

    # Robust question marker discovery: handles headings and <p> markers whether direct or in wrapper divs
    # Find all elements in document order
    all_elements = body.find_all(["h2", "h3", "h4", "p"])
    question_sections: list[tuple[int, list[str]]] = []
    current_q_num: int | None = None
    current_paragraphs: list[str] = []

    for el in all_elements:
        txt = el.get_text().strip()
        if not txt:
            continue

        m_marker = None
        if el.name in ("h2", "h3", "h4"):
            m_marker = re.search(r"•?\s*(\d+)\s*•?", txt)
        elif el.name == "p" and len(txt) <= 20:
            m_marker = re.match(r"^•?\s*(\d+)\s*•?$", txt)

        if m_marker:
            if current_q_num is not None and current_paragraphs:
                question_sections.append((current_q_num, current_paragraphs))
            current_q_num = int(m_marker.group(1))
            current_paragraphs = []
        elif el.name == "p" and current_q_num is not None:
            # Check if this paragraph is already contained in an enclosing tag or is a sub-element
            if el.find_parent("p") is None:
                current_paragraphs.append(txt)

    if current_q_num is not None and current_paragraphs:
        question_sections.append((current_q_num, current_paragraphs))

    pairs: list[dict[str, Any]] = []

    for q_num, paragraphs in question_sections:
        if not paragraphs:
            continue
        q_text = paragraphs[0]
        ans_parts = paragraphs[1:]
        if not ans_parts:
            continue

        # Extract reader name and clean question prefixes
        reader = ""
        question_body = q_text
        if ":" in q_text:
            parts = q_text.split(":", 1)
            candidate = parts[0].strip()
            is_prefix = bool(
                re.search(
                    r"^(?:як\s+правильно|чи\s+правильно|чи\s+можна|скажіть|підкажіть|поясніть|питання|запитання|увага|довідка)\b",
                    candidate,
                    re.IGNORECASE,
                )
            )
            if not is_prefix and len(candidate) < 80:
                cleaned_reader = re.sub(
                    r"^(?:запитує|питає|запитання\s+від|питання\s+від|допис\s+від)\s+",
                    "",
                    candidate,
                    flags=re.IGNORECASE,
                ).strip()
                if not cleaned_reader.endswith("?"):
                    reader = cleaned_reader
                    question_body = parts[1].strip()

        # Parse verdict from answer
        first_ans = ans_parts[0]
        verdict_type = "advice"
        verdict_form = ""

        # Match verdict patterns up to end of sentence or clause, preserving list items
        m_prav = re.search(
            r"(?<![а-яА-ЯєіїґЄІЇҐa-zA-Z])правильно(?:\s+писати|\s+казати|\s+вживати)?(?:\s*[:–—-])?\s*([^.!\n]+)",
            first_ans,
            flags=re.IGNORECASE,
        )
        m_neprav = re.search(
            r"(?<![а-яА-ЯєіїґЄІЇҐa-zA-Z])неправильно(?:\s+писати|\s+казати|\s+вживати)?(?:\s*[:–—-])?\s*([^.!\n]+)",
            first_ans,
            flags=re.IGNORECASE,
        )

        def _clean_verdict(raw: str) -> str:
            # Strip trailing explanation clauses (", бо...", ", оскільки...", etc.)
            truncated = re.split(r",\s+(?:бо|оскільки|тому що|адже|а|якщо)\b", raw, flags=re.IGNORECASE)[0]
            if "(" in truncated and not truncated.endswith(")"):
                truncated = truncated.split("(", 1)[0]
            return truncated.strip(' «"“”».;,')

        if m_prav:
            verdict_form = _clean_verdict(m_prav.group(1))
            verdict_type = "preferred"
        elif m_neprav:
            verdict_form = _clean_verdict(m_neprav.group(1))
            verdict_type = "incorrect"

        first_ans_lower = first_ans.lower()
        if "обидві" in first_ans_lower or "обидва" in first_ans_lower or "і так, і так" in first_ans_lower:
            verdict_type = "both_valid"
        elif (
            "не є суржиком" in first_ans_lower
            or "не є росіянізмом" in first_ans_lower
            or "не росіянізм" in first_ans_lower
        ):
            verdict_type = "not_russianism"
        elif verdict_type != "preferred" and ("неправильно" in first_ans_lower or "не варто" in first_ans_lower):
            verdict_type = "incorrect"

        # Determine questioned / contrastive form
        quotes = re.findall(r"[«\"“]([^»\"”]+)[»\"”]", question_body)
        questioned_form = ""

        if len(quotes) == 2:
            q1, q2 = quotes[0].strip(), quotes[1].strip()
            if verdict_type == "preferred" and verdict_form:
                if q1.lower() in verdict_form.lower() or verdict_form.lower() in q1.lower():
                    questioned_form = q2
                elif q2.lower() in verdict_form.lower() or verdict_form.lower() in q2.lower():
                    questioned_form = q1
                else:
                    questioned_form = f"{q1} чи {q2}"
            else:
                questioned_form = f"{q1} чи {q2}"
        elif len(quotes) == 1:
            questioned_form = quotes[0].strip()
        elif quotes:
            questioned_form = ", ".join(quotes[:3])
        elif " чи " in question_body:
            m_chi = re.search(r"([А-Яа-яЄєІіЇїҐґ'’ʼ\-]+)\s+чи\s+([А-Яа-яЄєІіЇїҐґ'’ʼ\-]+)", question_body)
            if m_chi:
                w1, w2 = m_chi.group(1), m_chi.group(2)
                if verdict_type == "preferred" and verdict_form:
                    if w1.lower() in verdict_form.lower():
                        questioned_form = w2
                    elif w2.lower() in verdict_form.lower():
                        questioned_form = w1
                    else:
                        questioned_form = f"{w1} чи {w2}"
                else:
                    questioned_form = f"{w1} чи {w2}"

        if not questioned_form and m_neprav:
            questioned_form = _clean_verdict(m_neprav.group(1))

        if not questioned_form:
            questioned_form = question_body[:60].strip()

        if not verdict_form and quotes:
            for q in quotes:
                if q in first_ans and q != questioned_form:
                    verdict_form = q
                    break

        if not verdict_form:
            verdict_form = first_ans.split(".")[0].strip()[:80]

        reasoning = "\n\n".join(ans_parts)

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

    sec = section.lower()

    # 1. Anti-surzhyk
    if any(k in sec for k in ("surzh", "суржик")):
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
    elif any(k in sec for k in ("paronim", "paronym", "паронім")):
        m = re.match(r"^([^?.]+?)\s+і\s+([^?.]+?)(?:[.?]|$)", clean_t, re.IGNORECASE)
        if m:
            w1, w2 = m.group(1).strip(), m.group(2).strip()
            pairs.append(
                {
                    "article_id": article_id,
                    "url": url,
                    "category": category,
                    "questioned_form": f"{w1} / {w2}",
                    "recommended_form": f"{w1} / {w2}",
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
    elif any(k in sec for k in ("orfo", "орфограф", "правопис", "pravopys")):
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
    elif any(k in sec for k in ("nagolos", "naholos", "наголос", "stress")):
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
    elif any(k in sec for k in ("synonim", "sunonim", "синонім")):
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
    elif any(k in sec for k in ("frazeolog", "idiom", "фразеолог", "ідіом")):
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
    user_agent: str = DEFAULT_USER_AGENT,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> list[dict[str, Any]]:
    """Discover all issues from Glavcom archive index pages.

    Enforces host allowlist (glavcom.ua) and parses true issue numbers from title/URL.
    """
    target_pages = pages or [
        "https://glavcom.ua/specprojects/movne_pytannya.html",
        "https://glavcom.ua/specprojects/movne_pytannya/p2.html",
    ]

    raw_items: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    for p_url in target_pages:
        resp = polite_get(session, p_url, delay=delay, user_agent=user_agent, sleep_fn=sleep_fn)
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

            # Enforce host allowlist
            parsed = urllib.parse.urlparse(href)
            if parsed.netloc.lower() not in ("glavcom.ua", "www.glavcom.ua"):
                continue

            if href in seen_urls:
                continue
            seen_urls.add(href)

            raw_title = link.get_text().strip()
            raw_items.append(
                {
                    "url": href,
                    "title": raw_title,
                    "description": desc_div.get_text().strip() if desc_div else "",
                    "date": date_div.get_text().strip() if date_div else "",
                }
            )

    # Chronological numbering / true issue numbers
    ordered: list[dict[str, Any]] = []
    for idx, item in enumerate(reversed(raw_items), 1):
        c = dict(item)
        # Attempt to extract true issue number from title or URL
        m_title = re.search(r"(?:випуск|№|#)\s*(?:№\s*)?(\d+)", c["title"], re.IGNORECASE)
        m_url = re.search(r"[-_/](?:vypusk|vyusk|issue|n)?(\d+)\.html", c["url"], re.IGNORECASE)
        if m_title:
            c["issue_number"] = int(m_title.group(1))
        elif m_url:
            c["issue_number"] = int(m_url.group(1))
        else:
            c["issue_number"] = idx
        ordered.append(c)
    return ordered


def discover_movaua_manifest(
    session: requests.Session,
    *,
    sitemap_url: str = "https://ukr-mova.in.ua/sitemap.xml",
    delay: float = 1.0,
    user_agent: str = DEFAULT_USER_AGENT,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> list[dict[str, Any]]:
    """Discover URLs from mova.ua sitemap, supporting nested sitemap indexes."""
    all_urls: set[str] = set()
    visited_sitemaps: set[str] = set()
    to_visit: list[str] = [sitemap_url]

    while to_visit:
        cur_sm = to_visit.pop(0)
        if cur_sm in visited_sitemaps:
            continue
        visited_sitemaps.add(cur_sm)

        resp = polite_get(session, cur_sm, delay=delay, user_agent=user_agent, sleep_fn=sleep_fn)
        if resp.status_code != 200:
            continue

        try:
            root = ET.fromstring(resp.content)
            # 1. Nested sitemap index elements
            sitemaps = root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap/{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
            if not sitemaps:
                sitemaps = root.findall(".//sitemap/loc")
            for sm in sitemaps:
                sm_text = (sm.text or "").strip()
                if sm_text and sm_text.startswith("http") and sm_text not in visited_sitemaps:
                    to_visit.append(sm_text)

            # 2. URL loc elements
            url_locs = root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
            if not url_locs:
                url_locs = root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
            if not url_locs:
                url_locs = root.findall(".//url/loc")

            for loc in url_locs:
                text = (loc.text or "").strip()
                if text and text.startswith("https://ukr-mova.in.ua/") and not text.endswith(".xml"):
                    all_urls.add(text)
        except ET.ParseError as e:
            logger.warning("Error parsing sitemap XML (%s): %s", cur_sm, e)

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
    if hasattr(sess, "headers"):
        sess.headers["User-Agent"] = user_agent

    items = manifest if manifest is not None else discover_movne_manifest(
        sess, delay=delay, user_agent=user_agent, sleep_fn=sleep_fn
    )
    total_manifest = len(items)

    existing_rows = conn.execute(
        "SELECT url FROM movne_pytannya_issues WHERE content_sha256 != '' OR error_status != ''"
    ).fetchall()
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
                user_agent=user_agent,
                delay=delay,
                max_retries=max_retries,
                retry_backoff=retry_backoff,
                sleep_fn=sleep_fn,
            )
        except AccessDeniedError:
            # Record 403 in SQLite so subsequent incremental runs skip it
            with conn:
                conn.execute("PRAGMA foreign_keys = ON;")
                now_iso = dt.datetime.now(dt.UTC).isoformat()
                row = conn.execute("SELECT id FROM movne_pytannya_issues WHERE url = ?", (url,)).fetchone()
                if row:
                    conn.execute(
                        "UPDATE movne_pytannya_issues SET error_status = 'http_403', fetched_at = ? WHERE id = ?",
                        (now_iso, row[0]),
                    )
                else:
                    conn.execute(
                        """
                        INSERT INTO movne_pytannya_issues
                        (url, issue_number, title, date, description, raw_html, article_text, content_sha256, fetched_at, error_status)
                        VALUES (?, ?, ?, ?, ?, '', '', '', ?, 'http_403')
                        """,
                        (url, issue_number, item.get("title", ""), item.get("date", ""), item.get("description", ""), now_iso),
                    )
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
        body_tag = (
            soup.find("div", class_="post_text")
            or soup.find("div", class_="art_body_uniq")
            or soup.find("article")
            or soup.find("div", class_="article_content")
            or soup.body
        )
        art_text = body_tag.get_text(separator="\n").strip() if body_tag else ""
        fetched_at = dt.datetime.now(dt.UTC).isoformat()

        with conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            row = conn.execute("SELECT id, issue_number FROM movne_pytannya_issues WHERE url = ?", (url,)).fetchone()
            if row:
                issue_id, issue_num = row[0], (item.get("issue_number") or row[1])
                conn.execute(
                    """
                    UPDATE movne_pytannya_issues
                    SET issue_number = ?, title = ?, date = ?, description = ?, raw_html = ?,
                        article_text = ?, content_sha256 = ?, fetched_at = ?, error_status = ''
                    WHERE id = ?
                    """,
                    (
                        issue_num,
                        item.get("title", ""),
                        item.get("date", ""),
                        item.get("description", ""),
                        html,
                        art_text,
                        sha,
                        fetched_at,
                        issue_id,
                    ),
                )
            else:
                issue_num = (
                    item.get("issue_number")
                    or (
                        conn.execute("SELECT COALESCE(MAX(issue_number), 0) + 1 FROM movne_pytannya_issues").fetchone()[
                            0
                        ]
                    )
                )
                cur = conn.execute(
                    """
                    INSERT INTO movne_pytannya_issues
                    (url, issue_number, title, date, description, raw_html, article_text, content_sha256, fetched_at, error_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, '')
                    """,
                    (
                        url,
                        issue_num,
                        item.get("title", ""),
                        item.get("date", ""),
                        item.get("description", ""),
                        html,
                        art_text,
                        sha,
                        fetched_at,
                    ),
                )
                issue_id = cur.lastrowid

            pairs = extract_movne_word_pairs(issue_num, url, html, created_at=fetched_at)
            conn.execute("DELETE FROM movne_word_pairs WHERE issue_id = ?", (issue_id,))
            for p in pairs:
                conn.execute(
                    """
                    INSERT INTO movne_word_pairs
                    (issue_id, issue_number, question_num, reader_name, question_raw, questioned_form,
                     verdict_form, verdict_type, reasoning, url, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        issue_id,
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
    if hasattr(sess, "headers"):
        sess.headers["User-Agent"] = user_agent

    items = manifest if manifest is not None else discover_movaua_manifest(
        sess, delay=delay, user_agent=user_agent, sleep_fn=sleep_fn
    )
    total_manifest = len(items)

    existing_rows = conn.execute(
        "SELECT url FROM movaua_articles WHERE content_sha256 != '' OR error_status != ''"
    ).fetchall()
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
                user_agent=user_agent,
                delay=delay,
                max_retries=max_retries,
                retry_backoff=retry_backoff,
                sleep_fn=sleep_fn,
            )
        except AccessDeniedError:
            with conn:
                conn.execute("PRAGMA foreign_keys = ON;")
                now_iso = dt.datetime.now(dt.UTC).isoformat()
                row = conn.execute("SELECT id FROM movaua_articles WHERE url = ?", (url,)).fetchone()
                if row:
                    conn.execute(
                        "UPDATE movaua_articles SET error_status = 'http_403', fetched_at = ? WHERE id = ?",
                        (now_iso, row[0]),
                    )
                else:
                    conn.execute(
                        """
                        INSERT INTO movaua_articles
                        (url, section, title, date, image_url, image_alt, raw_html, article_text, content_sha256, fetched_at, error_status)
                        VALUES (?, ?, ?, '', '', '', '', '', '', ?, 'http_403')
                        """,
                        (url, section, item.get("title", ""), now_iso),
                    )
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

        # Extract publication date if present
        date_str = ""
        time_tag = soup.find("time")
        if time_tag:
            date_str = time_tag.get("datetime") or time_tag.get_text().strip()
        if not date_str:
            meta_date = soup.find("meta", property="article:published_time") or soup.find("meta", attrs={"name": "date"})
            if meta_date:
                date_str = meta_date.get("content", "").strip()
        if not date_str:
            date_div = soup.find(class_=re.compile(r"\b(?:date|created|published)\b", re.I))
            if date_div:
                date_str = date_div.get_text().strip()

        img_url, img_alt = "", ""
        main_img = soup.find("img", class_="img-responsive") or soup.find("div", class_="illustration")
        if main_img:
            img_tag = main_img if main_img.name == "img" else main_img.find("img")
            if img_tag:
                raw_src = img_tag.get("src", "")
                img_url = urllib.parse.urljoin(url, raw_src) if raw_src else ""
                img_alt = img_tag.get("alt", "").strip()

        content_div = soup.find("div", class_="article-content") or soup.find("div", class_="text") or soup.body
        art_text = content_div.get_text(separator="\n").strip() if content_div else ""
        fetched_at = dt.datetime.now(dt.UTC).isoformat()

        with conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            row = conn.execute("SELECT id FROM movaua_articles WHERE url = ?", (url,)).fetchone()
            if row:
                article_id = row[0]
                conn.execute(
                    """
                    UPDATE movaua_articles
                    SET section = ?, title = ?, date = ?, image_url = ?, image_alt = ?,
                        raw_html = ?, article_text = ?, content_sha256 = ?, fetched_at = ?, error_status = ''
                    WHERE id = ?
                    """,
                    (section, raw_title, date_str, img_url, img_alt, html, art_text, sha, fetched_at, article_id),
                )
            else:
                cur = conn.execute(
                    """
                    INSERT INTO movaua_articles
                    (url, section, title, date, image_url, image_alt, raw_html, article_text, content_sha256, fetched_at, error_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '')
                    """,
                    (url, section, raw_title, date_str, img_url, img_alt, html, art_text, sha, fetched_at),
                )
                article_id = cur.lastrowid

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


def reextract_movne(conn: sqlite3.Connection) -> int:
    """Re-run word pair extraction over stored raw_html for Glavcom «Мовне питання»."""
    ensure_movne_schema(conn)
    rows = conn.execute(
        "SELECT id, issue_number, url, raw_html, fetched_at FROM movne_pytannya_issues WHERE raw_html != '' ORDER BY issue_number"
    ).fetchall()
    total_pairs = 0
    with conn:
        for row in rows:
            issue_id, issue_num, url, html, fetched_at = row
            pairs = extract_movne_word_pairs(issue_num, url, html, created_at=fetched_at)
            conn.execute("DELETE FROM movne_word_pairs WHERE issue_id = ?", (issue_id,))
            for p in pairs:
                conn.execute(
                    """
                    INSERT INTO movne_word_pairs
                    (issue_id, issue_number, question_num, reader_name, question_raw, questioned_form,
                     verdict_form, verdict_type, reasoning, url, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        issue_id,
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
            total_pairs += len(pairs)
    return total_pairs


def reextract_movaua(conn: sqlite3.Connection) -> int:
    """Re-run usage pair extraction over stored raw_html for Мова – ДНК нації."""
    ensure_movaua_schema(conn)
    rows = conn.execute(
        "SELECT id, url, section, title, image_alt, article_text, fetched_at FROM movaua_articles WHERE raw_html != '' ORDER BY id"
    ).fetchall()
    total_pairs = 0
    with conn:
        for row in rows:
            article_id, url, section, title, image_alt, article_text, fetched_at = row
            pairs = extract_movaua_usage_pairs(
                article_id,
                url,
                section,
                title,
                image_alt or "",
                article_text or "",
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
            total_pairs += len(pairs)
    return total_pairs


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
        "--re-extract",
        "--reextract",
        dest="re_extract",
        action="store_true",
        default=False,
        help="Re-run word-pair / usage-advice extraction from stored raw_html without fetching from the web.",
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
    global _STOP_REQUESTED
    _STOP_REQUESTED = False

    signal.signal(signal.SIGINT, _sig_handler)
    signal.signal(signal.SIGTERM, _sig_handler)

    args = parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    stats_list: list[IngestStats] = []

    try:
        if args.source in (SourceChoice.MOVNE, SourceChoice.ALL):
            args.db_movne.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(args.db_movne) as conn:
                if args.re_extract:
                    logger.info("Running in --re-extract mode for Movne...")
                    pairs_count = reextract_movne(conn)
                    logger.info("Movne: re-extracted %d word pairs into %s", pairs_count, args.db_movne)
                    if args.export_json_movne:
                        export_movne_summary_json(conn, args.export_json_movne)
                        logger.info("Exported Movne summary JSON to %s", args.export_json_movne)
                else:
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
                if args.re_extract:
                    logger.info("Running in --re-extract mode for MovaUA...")
                    pairs_count = reextract_movaua(conn)
                    logger.info("MovaUA: re-extracted %d usage pairs into %s", pairs_count, args.db_movaua)
                    if args.export_json_movaua:
                        export_movaua_summary_json(conn, args.export_json_movaua)
                        logger.info("Exported MovaUA summary JSON to %s", args.export_json_movaua)
                else:
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
