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
import os
import re
import sqlite3
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from scripts.wiki.sum20_official import (
    ensure_sum20_official_schema,
    normalize_sum20_lookup,
    parse_sum20_article,
    upsert_sum20_article,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"


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


def _get_db(db_path: Path | str | None = None, *, write: bool = False) -> sqlite3.Connection:
    if isinstance(db_path, str) and (db_path.startswith("file:") or "?" in db_path):
        conn = sqlite3.connect(db_path, uri=True)
    else:
        target = Path(db_path) if db_path else _resolve_sources_db()
        conn = sqlite3.connect(target)
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
        cur.execute(
            """
            SELECT a.id, a.wordid, a.headword, a.stressed_headword, a.pos, a.grammar, a.definition_text, a.official_url
            FROM sum20_articles a
            WHERE a.normalized_lookup_key = ? OR a.normalized_lookup_key LIKE ?
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
    headers = {"User-Agent": DEFAULT_USER_AGENT}
    try:
        resp = requests.get(url, headers=headers, timeout=timeout_s)
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
            art_resp = requests.get(art_url, headers=headers, timeout=timeout_s)
            if art_resp.status_code == 200:
                try:
                    parsed = parse_sum20_article(art_resp.text, wordid=wid)
                    upsert_sum20_article(conn, parsed)
                except Exception:
                    continue
        conn.commit()
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
    conn = _get_db(db_path, write=False)
    try:
        cached = lookup_sum20_cached(lemma, conn)
        if cached or not write:
            return cached
    finally:
        conn.close()

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
