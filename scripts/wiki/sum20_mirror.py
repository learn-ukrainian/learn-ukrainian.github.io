"""Imported СУМ-20 mirror rows beside the official collection (#8579).

``scripts.ingest.sum20_mirror_import`` is the only writer of these tables. This
module holds their schema and the read-time rule ``sum20-mirror-rule-v1`` that
``query_sum20`` applies; any other reader must use ``served_rows`` too. It never
writes, never opens a store and never touches the official ``sum20_*`` tables.

For a lookup key, compare each mirror row with every official row of that key:

- no official row: ``mirror_only`` (served, labelled mirror);
- equal to a live official row: ``agrees_with_official`` (suppressed; official serves);
- official rows exist but none is live: ``official_quarantined`` (served, flagged;
  the quarantined row stays hidden);
- otherwise: ``differs_from_official`` (served after the official rows, flagged).

Equality is the reconciliation report's comparison payload: markup, transport
wrappers and whitespace are dropped; letters, case and punctuation are kept.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Sequence
from typing import Any

from scripts.lexicon.reconcile_sum20 import _comparison_payload
from scripts.wiki.sum20_official import live_article_predicate, normalize_sum20_lookup

MIRROR_SOURCE_ID = "sum20_slovnyk_mirror"
RULE_VERSION = "sum20-mirror-rule-v1"
MIRROR_ATTRIBUTION_LABEL = (
    "Словник української мови у 20 томах — копія slovnyk.me (newsum); не звірено з офіційним виданням"
)
MIRROR_ONLY = "mirror_only"
AGREES = "agrees_with_official"
OFFICIAL_QUARANTINED = "official_quarantined"
DIFFERS = "differs_from_official"
RELATIONS = (MIRROR_ONLY, AGREES, OFFICIAL_QUARANTINED, DIFFERS)
MIRROR_TABLES = ("sum20_mirror_imports", "sum20_mirror_articles")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sum20_mirror_imports (
    id INTEGER PRIMARY KEY,
    generation TEXT NOT NULL UNIQUE,
    rule_version TEXT NOT NULL,
    staging_sha256 TEXT NOT NULL,
    staging_records INTEGER NOT NULL,
    checkpoint_count INTEGER NOT NULL,
    checkpoint_last_url TEXT NOT NULL,
    checkpoint_updated_at TEXT NOT NULL,
    official_digest TEXT NOT NULL,
    relation_counts TEXT NOT NULL,
    imported_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sum20_mirror_articles (
    id INTEGER PRIMARY KEY,
    mirror_url TEXT NOT NULL UNIQUE,
    source_url TEXT NOT NULL,
    mirror TEXT NOT NULL,
    lemma TEXT NOT NULL,
    headword TEXT NOT NULL,
    normalized_lookup_key TEXT NOT NULL,
    title TEXT NOT NULL,
    article_text TEXT NOT NULL,
    senses_json TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    content_sha256 TEXT NOT NULL,
    import_id INTEGER NOT NULL REFERENCES sum20_mirror_imports(id)
);
CREATE INDEX IF NOT EXISTS idx_sum20_mirror_articles_lookup
    ON sum20_mirror_articles(normalized_lookup_key, mirror_url);
"""

_ARTICLE_COLUMNS = "id, mirror_url, source_url, mirror, headword, article_text, senses_json, fetched_at, content_sha256"


def mirror_key(headword: str) -> str:
    """Lookup key of a mirror row: its page headword, not the URL slug (``м_ясо``)."""
    return normalize_sum20_lookup(headword)


def classify(headword: str, article_text: str, official: Sequence[tuple[str, str, str, bool]]) -> str:
    """Relation of one mirror article to the official rows of its key.

    ``official`` holds ``(headword, article_text, normalized_lookup_key, live)``
    for every official row of the key, live and excluded alike.
    """
    if not official:
        return MIRROR_ONLY
    payload = _comparison_payload(headword, article_text, headword, staging=True)
    live = [row for row in official if row[3]]
    if any(_comparison_payload(h, t, k, staging=False) == payload for h, t, k, _ in live):
        return AGREES
    return DIFFERS if live else OFFICIAL_QUARANTINED


def is_served(relation: str) -> bool:
    """Agreeing mirror rows are redundant: the official record serves the meaning."""
    return relation != AGREES


def mirror_tables_present(conn: Any) -> bool:
    names = {
        str(row[0])
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name IN (?, ?)", MIRROR_TABLES
        ).fetchall()
    }
    return names == set(MIRROR_TABLES)


def official_rows(conn: Any, key: str) -> list[tuple[str, str, str, bool]]:
    """Every official row of ``key`` with its live flag; empty without an official table."""
    columns = [str(row[1]) for row in conn.execute("PRAGMA table_info(sum20_articles)").fetchall()]
    if not columns:
        return []
    rows = conn.execute(
        f"SELECT headword, article_text, normalized_lookup_key, ({live_article_predicate(columns)}) "
        "FROM sum20_articles WHERE normalized_lookup_key = ? ORDER BY wordid",
        (key,),
    ).fetchall()
    return [(str(h or ""), str(t or ""), str(k or ""), bool(flag)) for h, t, k, flag in rows]


def served_rows(conn: Any, key: str, official: Any = None) -> list[tuple[dict[str, Any], str]]:
    """Mirror rows for ``key`` in ``conn`` that the rule serves, each with its relation, in URL order.

    ``official`` is the connection whose official rows the caller served (default
    ``conn``), so the relation is always judged against what the reader returns.
    """
    if not key or not mirror_tables_present(conn):
        return []
    cursor = conn.execute(
        f"SELECT {_ARTICLE_COLUMNS} FROM sum20_mirror_articles WHERE normalized_lookup_key = ? ORDER BY mirror_url",
        (key,),
    )
    names = [column[0] for column in cursor.description]
    rows = [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]
    if not rows:
        return []
    official_for_key = official_rows(conn if official is None else official, key)
    served = []
    for row in rows:
        relation = classify(str(row["headword"]), str(row["article_text"]), official_for_key)
        if is_served(relation):
            served.append((row, relation))
    return served


def _senses(senses_json: str) -> tuple[str, str, list[dict[str, Any]]]:
    """Stressed headword, header grammar and verbatim sense texts from the staged parse."""
    try:
        parsed = json.loads(senses_json or "{}")
    except ValueError:
        return "", "", []
    if not isinstance(parsed, dict):
        return "", "", []
    senses = []
    for sense in parsed.get("senses") or []:
        if not isinstance(sense, dict):
            continue
        order = sense.get("sense_num")
        text = str(sense.get("raw_text") or sense.get("definition") or "").strip()
        if not isinstance(order, int) or not text:
            continue
        # raw_text repeats the printed sense number; the record carries it as sense_order.
        senses.append(
            {
                "sense_order": order,
                "definition": re.sub(rf"^{order}\.\s+", "", text),
                "register_labels": [],
            }
        )
    return str(parsed.get("headword") or ""), str(parsed.get("header_grammar") or ""), senses


def mirror_record(row: dict[str, Any], relation: str) -> dict[str, Any]:
    """A ``query_sum20`` record for a served mirror row; the article text is verbatim."""
    stressed, grammar, senses = _senses(str(row["senses_json"]))
    return {
        "source_id": MIRROR_SOURCE_ID,
        "source_role": "mirror",
        "official_relation": relation,
        "rule_version": RULE_VERSION,
        "source_record_id": str(row["mirror_url"]),
        "headword": str(row["headword"]),
        "stressed_headword": stressed,
        "pos": "",
        "grammar": grammar,
        "article_text": str(row["article_text"]),
        "senses": senses,
        "citations": [],
        "official_url": "",
        "source_url": str(row["source_url"]),
        "mirror": str(row["mirror"]),
        "retrieved_at": str(row["fetched_at"]),
        "content_sha256": str(row["content_sha256"]),
        "parser_version": "",
        "status": "ok",
        "attribution_label": MIRROR_ATTRIBUTION_LABEL,
    }


def mirror_records(conn: Any, key: str, official: Any = None) -> list[dict[str, Any]]:
    return [mirror_record(row, relation) for row, relation in served_rows(conn, key, official)]


def relation_counts(relations: Iterable[str]) -> dict[str, int]:
    counts = dict.fromkeys(RELATIONS, 0)
    for relation in relations:
        counts[relation] += 1
    return counts
