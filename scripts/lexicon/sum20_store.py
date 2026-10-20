"""Read-only SUM-20 store selection using the shared storage boundaries (#10655)."""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import closing
from functools import lru_cache
from pathlib import Path
from typing import Any

from scripts.lexdata.generation import Unavailable, open_generation
from scripts.lib.readonly_sqlite import SQLiteConnection, open_readonly
from scripts.storage.topology import StoreBinding, StoreRefusal, main_checkout_root, resolve_store
from scripts.wiki.sum20_official import normalize_sum20_lookup, sum20_live_article_where


class Sum20StoreError(ValueError):
    """A path-free refusal; an invalid store is never a dictionary miss."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def open_sources(db_path: Path | str | None = None, *, repository_root: Path | None = None) -> SQLiteConnection:
    """Open an injected or canonical sources store through the read boundary."""
    binding = None if db_path is None else StoreBinding("sources", Path(db_path))
    resolved = resolve_store("sources", repository_root, binding=binding)
    if isinstance(resolved, StoreRefusal):
        raise Sum20StoreError(resolved.reason)
    try:
        conn = open_readonly(resolved.path)
    except (OSError, sqlite3.Error):
        raise Sum20StoreError("sources_unavailable") from None
    conn.row_factory = sqlite3.Row
    return conn


def open_sum20(db_path: Path | str | None = None, *, repository_root: Path | None = None) -> SQLiteConnection:
    """Open canonical articles, validating every selected lexdata generation.

    Injected sources paths take precedence. Explicit lexdata overrides are
    exclusive, including the legacy LEXDATA_DB_PATH spelling. Only an absent
    default lexdata file or a valid generation without SUM-20 uses sources.
    The caller closes the connection. No input grants write access.
    """
    if db_path is not None:
        return open_sources(db_path, repository_root=repository_root)
    env = dict(os.environ)
    if "LEXDATA_DB_PATH" in env:
        if "LU_LEXDATA_DB" in env and env["LU_LEXDATA_DB"] != env["LEXDATA_DB_PATH"]:
            raise Sum20StoreError("conflicting_lexdata_overrides")
        env["LU_LEXDATA_DB"] = env["LEXDATA_DB_PATH"]
    exclusive = "LU_LEXDATA_DB" in env
    resolved = resolve_store("lexdata", repository_root, env=env)
    if isinstance(resolved, StoreRefusal):
        if resolved.reason == "store_missing" and not exclusive:
            return open_sources(repository_root=repository_root)
        raise Sum20StoreError(resolved.reason)
    opened = open_generation(resolved.path, repository_root=repository_root, env=env)
    if isinstance(opened, Unavailable):
        raise Sum20StoreError(opened.reason)
    conn = opened.conn
    conn.row_factory = sqlite3.Row
    present = None
    try:
        present = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='sum20_articles'").fetchone()
        if present:
            return conn
    except sqlite3.Error:
        raise Sum20StoreError("lexdata_unavailable") from None
    finally:
        if not present:
            conn.close()
    if exclusive:
        raise Sum20StoreError("sum20_table_missing")
    return open_sources(repository_root=repository_root)


def lookup_sum20_cached(
    lemma: str,
    conn: SQLiteConnection,
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
            SELECT id, wordid, headword, stressed_headword, pos, grammar, article_text, definition_text, official_url
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
                "article_text": r["article_text"],
                "senses": senses,
                "url": r["official_url"],
            }
        )
    return results


@lru_cache(maxsize=2)
def _mirror_index(path: Path, signature: tuple) -> dict[str, list[tuple[str, str, int]]]:
    """Index raw titles and slash members once per file/WAL revision.

    Only identities are cached, never article text. Rank 1 is a normalized
    whole title; rank 2 is a paired member. Exact raw matches rank 0 at lookup.
    """
    index: dict[str, list[tuple[str, str, int]]] = {}
    with closing(open_readonly(path)) as conn:
        # Validate the full reader schema even when the requested key is absent.
        conn.execute("SELECT lemma, headword, text, source_url, url FROM sum20_slovnyk_articles LIMIT 0")
        for raw, url in conn.execute("SELECT lemma, url FROM sum20_slovnyk_articles"):
            keys = [(normalize_sum20_lookup(raw), 1)]
            if "/" in raw:
                keys.extend((normalize_sum20_lookup(member), 2) for member in raw.split("/"))
            for key, rank in keys:
                if key:
                    index.setdefault(key, []).append((raw, url, rank))
    return index


def resolve_sum20_articles(
    lemma: str,
    db_path: Path | str | None = None,
    *,
    mirror_db_path: Path | str | None = None,
    repository_root: Path | None = None,
) -> list[dict[str, Any]]:
    """Read official articles first, then local mirror candidates for a missing key.

    An absent mirror is a local miss. Refused or corrupt mirrors raise a typed
    error, as do invalid official bindings. Neither path writes to a store.
    The staging file uses an injected sources binding for locality validation;
    this does not promote its records to official evidence.
    """
    with closing(open_sum20(db_path, repository_root=repository_root)) as conn:
        official = lookup_sum20_cached(lemma, conn)
    if official:
        return official
    path = (Path(mirror_db_path) if mirror_db_path is not None else
            main_checkout_root(repository_root or Path.cwd()) / "data" / "sum20_slovnyk_staging.db")
    resolved = resolve_store("sources", repository_root, binding=StoreBinding("sources", path))
    if isinstance(resolved, StoreRefusal):
        if resolved.reason == "store_missing":
            return []
        raise Sum20StoreError(resolved.reason)
    norm = normalize_sum20_lookup(lemma)
    try:
        signature = []
        for file in (resolved.path, Path(str(resolved.path) + "-wal")):
            try:
                stat = file.stat()
                signature.append(
                    None if file != resolved.path and stat.st_size == 0 else
                    (stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
                )
            except FileNotFoundError:
                signature.append(None)
        candidates = _mirror_index(resolved.path, tuple(signature)).get(norm, [])
        if not candidates:
            return []
        # One article only: exact raw, normalized whole title, paired member;
        # URL is the stable tie-breaker within a rank, regardless of row order.
        _, url, _ = min(candidates, key=lambda row: (0 if row[0] == lemma else row[2], row[1]))
        with closing(open_readonly(resolved.path)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT lemma, headword, text, source_url, url FROM sum20_slovnyk_articles "
                "WHERE url = ?",
                (url,),
            ).fetchall()
    except (OSError, sqlite3.Error):
        raise Sum20StoreError("mirror_unavailable") from None
    return [{
        "headword": row["headword"],
        "definition": row["text"],
        "article_text": row["text"],
        "senses": [],
        "url": row["source_url"] or row["url"],
        "role": "mirror_candidate",
    } for row in rows]
