"""Decolonized dictionary evidence lookup: official СУМ-20 + Soviet colonization context (СУМ-11).

Provides:
- lookup_sum20_articles: reads locally stored modern СУМ-20 articles. A miss is empty.
- lookup_sum11_colonization_context: reads Soviet-era СУМ-11 rows, flagged with
  sovietization_risk and keywords for historical transparency.
- lookup_decolonized_heteronym_evidence: combines the local modern baseline with
  colonization context.

Public SUM-20 lookups are strictly offline (#10655). They share the live-article
filter in ``scripts.wiki.sum20_official`` and never fetch or scrape. ``data/lexdata.db``
is canonical only when its published generation passes validation and holds
``sum20_articles``; an absent default uses the read-only official sources
collection. On a local key miss the binding reads mirror staging as mirror_candidate evidence.
Official ingest owns official store population; readers never populate stores.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.lexicon.sum20_store import lookup_sum20_cached as lookup_sum20_cached
from scripts.lexicon.sum20_store import open_sources, resolve_sum20_articles
from scripts.lib.readonly_sqlite import SQLiteConnection

REPO_ROOT = Path(__file__).resolve().parents[2]
def _get_db(db_path: Path | str | None = None, *, write: bool = False) -> SQLiteConnection:
    """Legacy connection helper; even write=True cannot grant write access."""
    return open_sources(db_path, repository_root=REPO_ROOT)


def lookup_sum20_articles(
    lemma: str,
    db_path: Path | str | None = None,
    *,
    write: bool = False,
    mirror_db_path: Path | str | None = None,
) -> list[dict[str, Any]]:
    """Return modern СУМ-20 articles already stored for ``lemma``.

    Strictly offline (#10655). The connection is read-only (``PRAGMA query_only``).
    A missing table or row returns ``[]``. Refused stores raise Sum20StoreError.
    ``write`` is retained for existing callers. ``True`` does not open a writable
    database, populate a cache, or contact the network. Official ingest owns that.
    """
    # ``write`` cannot select a live fallback. Both values take the local read.
    _ = write
    return resolve_sum20_articles(lemma, db_path, mirror_db_path=mirror_db_path, repository_root=REPO_ROOT)


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
