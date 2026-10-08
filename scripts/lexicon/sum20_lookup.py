"""Decolonized dictionary evidence lookup: official СУМ-20 + Soviet colonization context (СУМ-11).

Provides:
- lookup_sum20_articles: Fetches and caches authentic modern СУМ-20 entries from sum20ua.com.
- lookup_sum11_colonization_context: Fetches Soviet-era СУМ-11 definitions, flagged with
  sovietization_risk and keywords for historical transparency.
- lookup_decolonized_heteronym_evidence: Combines modern baseline with colonization context.
"""

from __future__ import annotations

import contextlib
import json
import math
import os
import re
import sqlite3
import time
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

from scripts.wiki.sum20_official import (
    ensure_sum20_official_schema,
    live_article_predicate,
    normalize_sum20_lookup,
    parse_sum20_article,
    upsert_sum20_article,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_USER_AGENT = (
    "learn-ukrainian-sum20/1.0 "
    "(+https://github.com/learn-ukrainian/learn-ukrainian.github.io; educational dictionary lookup)"
)
_sum20_robots: RobotFileParser | None = None
_sum20_last_request: float | None = None
_sum20_stopped = False


class _Sum20AccessStopped(RuntimeError):
    """Terminal stop, distinct from a dictionary miss or retryable error."""

    def __init__(self, message: str, http_status: int | None = None):
        super().__init__(message)
        self.http_status = http_status


def _sum20_check_response(response: requests.Response) -> None:
    global _sum20_stopped
    from scripts.lexicon.enrich_manifest import _slovnyk_access_denied

    if _slovnyk_access_denied(response.status_code, response.text, response.headers) or 300 <= response.status_code < 400:
        _sum20_stopped = True
        raise _Sum20AccessStopped("SUM-20 access denied or challenged; no further requests", response.status_code)


def _sum20_get(
    url: str,
    timeout_s: float,
    *,
    client=None,
    sleep: Callable[[float], None] | None = None,
    clock: Callable[[], float] | None = None,
    delay_s: float = 2.0,
    params=None,
    user_agent: str = DEFAULT_USER_AGENT,
) -> requests.Response:
    global _sum20_robots, _sum20_last_request, _sum20_stopped
    if _sum20_stopped:
        raise _Sum20AccessStopped("SUM-20 access stopped for this process")
    client = client or requests
    sleep = sleep or time.sleep
    clock = clock or time.monotonic
    headers = {"User-Agent": user_agent, "Accept": "text/html,application/xhtml+xml"}
    if _sum20_robots is None:
        try:
            response = client.get(
                "https://sum20ua.com/robots.txt", headers=headers, timeout=timeout_s, allow_redirects=False
            )
            _sum20_last_request = clock()
            _sum20_check_response(response)
            if response.status_code not in {200, 404}:
                raise _Sum20AccessStopped("SUM-20 robots unavailable", response.status_code)
        except requests.RequestException as exc:
            _sum20_stopped = True
            raise _Sum20AccessStopped("SUM-20 robots unavailable") from exc
        except _Sum20AccessStopped:
            _sum20_stopped = True
            raise
        _sum20_robots = RobotFileParser()
        # robotparser accepts integer delays; round fractional observations up.
        robots_text = re.sub(
            r"(?im)^(\s*crawl-delay\s*:\s*)(\d+\.\d+)(\s*(?:#.*)?)$",
            lambda match: f"{match[1]}{math.ceil(float(match[2]))}{match[3]}",
            response.text,
        )
        _sum20_robots.parse(robots_text.splitlines() if response.status_code == 200 else [])
    if not _sum20_robots.can_fetch(user_agent, url):
        _sum20_stopped = True
        raise _Sum20AccessStopped("SUM-20 robots disallows target")
    delay = max(2.0, delay_s, _sum20_robots.crawl_delay(user_agent) or 0)
    if _sum20_last_request is not None:
        remaining = delay - (clock() - _sum20_last_request)
        if remaining > 0:
            sleep(remaining)
    _sum20_last_request = clock()
    response = client.get(url, headers=headers, timeout=timeout_s, allow_redirects=False, **({"params": params} if params is not None else {}))
    _sum20_check_response(response)
    return response


@lru_cache(maxsize=1)
def _resolve_primary_checkout() -> Path | None:
    parts = REPO_ROOT.parts
    if ".worktrees" in parts:
        return Path(*parts[: parts.index(".worktrees")])
    return REPO_ROOT


def _resolve_sources_db() -> Path:
    env_path = os.environ.get("SOURCES_DB_PATH")
    if env_path and Path(env_path).is_file():
        return Path(env_path)
    local = REPO_ROOT / "data" / "sources.db"
    if local.is_file() and local.stat().st_size > 1_000_000:
        return local
    primary = _resolve_primary_checkout()
    if primary:
        prim_db = primary / "data" / "sources.db"
        if prim_db.is_file():
            return prim_db
    return local


def _read_only_uri(uri: str) -> str:
    """``uri`` with ``mode=ro`` enforced; a fragment or any other ``mode`` is refused."""
    parts = urlsplit(uri)
    if "#" in uri:  # SQLite ends the path/query at "#", so even an empty fragment changes the parse
        raise ValueError(f"read-only СУМ-20 lookup refuses a URI with a fragment: {uri}")
    params = parse_qsl(parts.query, keep_blank_values=True)
    for key, value in params:
        if key == "mode" and value != "ro":
            raise ValueError(f"read-only СУМ-20 lookup refuses a URI with mode={value}: {uri}")
    kept = [(key, value) for key, value in params if key != "mode"]
    return urlunsplit(parts._replace(query=urlencode([*kept, ("mode", "ro")])))


def _get_db(db_path: Path | str | None = None, *, write: bool = False) -> sqlite3.Connection:
    if isinstance(db_path, str) and db_path.startswith("file:"):
        conn = sqlite3.connect(db_path if write else _read_only_uri(db_path), uri=True)
    else:
        target = Path(db_path) if db_path else _resolve_sources_db()
        read_only_uri = f"{target.resolve().as_uri()}?mode=ro"
        conn = sqlite3.connect(target) if write else sqlite3.connect(read_only_uri, uri=True)
    conn.row_factory = sqlite3.Row
    if not write:
        with contextlib.suppress(sqlite3.OperationalError):
            conn.execute("PRAGMA query_only = ON")
    else:
        ensure_sum20_official_schema(conn)
    return conn


def lookup_sum20_cached(lemma: str, conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Retrieve locally cached СУМ-20 records for lemma (read-only safe)."""
    norm = normalize_sum20_lookup(lemma)
    cur = conn.cursor()
    try:
        cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='sum20_articles'")
        if not cur.fetchone():
            return []
        columns = [str(row[1]) for row in cur.execute("PRAGMA table_info(sum20_articles)").fetchall()]
        cur.execute(
            f"""
            SELECT a.id, a.wordid, a.headword, a.stressed_headword, a.pos, a.grammar, a.definition_text, a.official_url
            FROM sum20_articles a
            WHERE (a.normalized_lookup_key = ? OR a.normalized_lookup_key LIKE ?)
              AND {live_article_predicate(columns, "a")}
            ORDER BY a.wordid
            """,
            (norm, f"{norm} %"),
        )
        rows = cur.fetchall()
    except sqlite3.OperationalError:
        return []

    results = []
    for r in rows:
        art_id = r["id"]
        senses = []
        try:
            cur.execute(
                """
                SELECT sense_order, definition, register_labels
                FROM sum20_senses
                WHERE article_id = ?
                ORDER BY sense_order
                """,
                (art_id,),
            )
            senses = [
                {
                    "sense_order": s["sense_order"],
                    "definition": s["definition"],
                    "register_labels": json.loads(s["register_labels"] or "[]"),
                }
                for s in cur.fetchall()
            ]
        except (sqlite3.OperationalError, json.JSONDecodeError):
            pass

        results.append(
            {
                "id": art_id,
                "wordid": r["wordid"],
                "headword": r["headword"],
                "stressed_headword": r["stressed_headword"],
                "pos": r["pos"],
                "grammar": r["grammar"],
                "definition": r["definition_text"],
                "senses": senses,
                "url": r["official_url"],
            }
        )
    return results


def fetch_and_cache_sum20(
    lemma: str,
    conn: sqlite3.Connection,
    timeout_s: float = 15.0,
) -> list[dict[str, Any]]:
    """Fetch official СУМ-20 articles for lemma from sum20ua.com and cache into sources.db."""
    norm_lemma = normalize_sum20_lookup(lemma)
    url = f"https://sum20ua.com/List/Search?searchWord={quote(lemma)}"
    try:
        resp = _sum20_get(url, timeout_s)
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        matching_wordids: list[int] = []
        for a in soup.find_all("a", href=re.compile(r"wordid=\d+")):
            text = a.get_text(strip=True)
            norm_text = normalize_sum20_lookup(text)
            if norm_text == norm_lemma or norm_text.rstrip("1234567890") == norm_lemma:
                m = re.search(r"wordid=(\d+)", a["href"])
                if m:
                    wid = int(m.group(1))
                    if wid not in matching_wordids:
                        matching_wordids.append(wid)

        for wid in matching_wordids:
            art_url = f"https://sum20ua.com/?wordid={wid}&page=0"
            art_resp = _sum20_get(art_url, timeout_s)
            if art_resp.status_code == 200:
                try:
                    parsed = parse_sum20_article(art_resp.text, wordid=wid)
                    upsert_sum20_article(conn, parsed)
                except Exception:
                    continue
        conn.commit()
    except _Sum20AccessStopped:
        conn.commit()  # retain successful earlier articles; denial is never a miss
        raise
    except Exception:
        pass

    return lookup_sum20_cached(lemma, conn)


def lookup_sum20_articles(
    lemma: str,
    db_path: Path | str | None = None,
    *,
    write: bool = False,
) -> list[dict[str, Any]]:
    """Retrieve modern authoritative СУМ-20 articles for lemma.

    By default (write=False), only read-only lookup against cached records is performed,
    enforcing PRAGMA query_only = ON and never attempting schema creation or cache writes.
    To allow network fetching and caching on miss, pass write=True.
    """
    try:
        conn = _get_db(db_path, write=False)
    except sqlite3.OperationalError:  # no database file yet: nothing cached
        cached: list[dict[str, Any]] = []
    else:
        try:
            cached = lookup_sum20_cached(lemma, conn)
        finally:
            conn.close()
    if cached or not write:
        return cached

    try:
        write_conn = _get_db(db_path, write=True)
        try:
            return fetch_and_cache_sum20(lemma, write_conn)
        finally:
            write_conn.close()
    except sqlite3.OperationalError:
        return []


def lookup_sum11_colonization_context(lemma: str, db_path: Path | str | None = None) -> dict[str, Any] | None:
    """Retrieve Soviet-era СУМ-11 interpretation explicitly contextualized for historical analysis."""
    try:
        conn = _get_db(db_path, write=False)
    except Exception:
        return None
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='sum11'")
        if not cur.fetchone():
            return None
        cur.execute(
            """
            SELECT definition, text, sovietization_risk, sovietization_keywords
            FROM sum11
            WHERE lower(word) = ?
            LIMIT 1
            """,
            (lemma.lower(),),
        )
        row = cur.fetchone()
        if not row:
            return None
        defn = str(row["definition"] or "").strip()
        risk = int(row["sovietization_risk"] or 0)
        kw_str = str(row["sovietization_keywords"] or "")
        keywords = [k.strip() for k in kw_str.split(",") if k.strip()]

        return {
            "source": "СУМ-11 (1970–1980)",
            "red_flag": True,  # Explicit contrast warning, independent of the risk score.
            "definition": defn[:400].strip(),
            "sovietization_risk": risk,
            "keywords": keywords,
            "historical_note": (
                "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). "
                "Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
            ),
        }
    finally:
        conn.close()


def lookup_decolonized_heteronym_evidence(
    lemma: str,
    db_path: Path | str | None = None,
    *,
    write: bool = False,
) -> dict[str, Any]:
    """Return complete decolonized evidence bundle for a heteronym lemma."""
    sum20 = lookup_sum20_articles(lemma, db_path, write=write)
    col_context = lookup_sum11_colonization_context(lemma, db_path)
    return {
        "lemma": lemma,
        "modern_sum20": sum20,
        "soviet_colonization_context": col_context,
    }
