"""Decolonized dictionary evidence lookup: official СУМ-20 + Soviet colonization context (СУМ-11).

Provides:
- lookup_sum20_articles: reads locally stored modern СУМ-20 articles. A miss is empty.
- lookup_sum11_colonization_context: reads Soviet-era СУМ-11 rows, flagged with
  sovietization_risk and keywords for historical transparency.
- lookup_decolonized_heteronym_evidence: combines the local modern baseline with
  colonization context.

Public SUM-20 lookups are strictly offline (#10655). They share the live-article
filter in ``scripts.wiki.sum20_official`` and never fetch or scrape. ``data/lexdata.db``
is the canonical file when it already holds ``sum20_articles``; otherwise the
read-only official sources collection is the store. Staging databases are not
fallback caches. Official ingest owns store population.
"""

from __future__ import annotations

import contextlib
import json
import os
import sqlite3
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from scripts.wiki.sum20_official import (
    ensure_sum20_official_schema,
    normalize_sum20_lookup,
    select_sum20_database,
    sum20_live_article_where,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
_EXCLUSIVE_MISS = object()


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


def _sum20_table_present(path: Path) -> bool:
    """True when ``path`` already has official SUM-20 articles. Read-only."""
    try:
        conn = _get_db(path, write=False)
    except sqlite3.Error:
        return False
    try:
        row = conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'sum20_articles'").fetchone()
        return row is not None
    except sqlite3.Error:
        return False
    finally:
        conn.close()


def _selected_sum20_db(db_path: Path | str | None) -> Path | str | object | None:
    """Explicit database, canonical lexdata, sources default, or an exclusive miss.

    ``None`` tells ``_get_db`` to open the read-only sources default. The
    exclusive-miss sentinel means ``LEXDATA_DB_PATH`` was blank.
    """
    if db_path is not None:
        return db_path
    selection = select_sum20_database(REPO_ROOT, article_table_present=_sum20_table_present)
    if selection.exclusive:
        if selection.path is None:
            return _EXCLUSIVE_MISS
        return selection.path
    return selection.path


def lookup_sum20_cached(
    lemma: str,
    conn: sqlite3.Connection,
    *,
    prefix: bool = True,
) -> list[dict[str, Any]]:
    """Retrieve locally stored СУМ-20 records for lemma (read-only safe).

    ``prefix=True`` keeps the lexicon homonym match (exact key or key plus a
    space). ``prefix=False`` is the exact official match used by ``query_sum20``.
    """
    norm = normalize_sum20_lookup(lemma)
    cur = conn.cursor()
    try:
        columns = [str(row[1]) for row in cur.execute("PRAGMA table_info(sum20_articles)").fetchall()]
        if not columns:
            return []
        where = sum20_live_article_where(columns, prefix=prefix)
        parameters = (norm, f"{norm} %") if prefix else (norm,)
        cur.execute(
            f"""
            SELECT id, wordid, headword, stressed_headword, pos, grammar, definition_text, official_url
            FROM sum20_articles
            WHERE {where}
            ORDER BY wordid
            """,
            parameters,
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


def lookup_sum20_articles(
    lemma: str,
    db_path: Path | str | None = None,
    *,
    write: bool = False,
) -> list[dict[str, Any]]:
    """Return modern СУМ-20 articles already stored for ``lemma``.

    Strictly offline (#10655). The connection is read-only (``PRAGMA query_only``).
    A missing database, table, or row returns ``[]`` and does not fetch or scrape.
    ``write`` is retained for existing callers. ``True`` does not open a writable
    database, populate a cache, or contact the network. Official ingest owns that.
    """
    # ``write`` cannot select a live fallback. Both values take the local read.
    _ = write
    chosen = _selected_sum20_db(db_path)
    if chosen is _EXCLUSIVE_MISS:
        return []
    open_path: Path | str | None = chosen if isinstance(chosen, (Path, str)) else None
    try:
        conn = _get_db(open_path, write=False)
    except sqlite3.OperationalError:  # no database file yet: nothing stored
        return []
    try:
        return lookup_sum20_cached(lemma, conn)
    finally:
        conn.close()


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
    """Return the local decolonized evidence bundle for a heteronym lemma.

    Both layers are read from local databases. A modern miss is an empty list;
    a missing colonization row is ``None``. ``write`` is forwarded and still
    cannot authorize a network request (#10655). An omitted ``db_path`` reads
    SUM-20 from the canonical file and SUM-11 from the sources collection.
    """
    sum20 = lookup_sum20_articles(lemma, db_path, write=write)
    col_context = lookup_sum11_colonization_context(lemma, db_path)
    return {
        "lemma": lemma,
        "modern_sum20": sum20,
        "soviet_colonization_context": col_context,
    }
