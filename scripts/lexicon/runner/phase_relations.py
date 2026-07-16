"""Phase 2 — raw relation extraction + run-level reciprocal closure (#5230 / #5331).

1. Extract raw pointer/relation edges per lemma into durable rows.
2. Run one run-level deterministic closure join over the complete cohort.
3. Add reciprocal definition-pointer edges and normalize antonym / homonym /
   paronym / corpus relations.
4. Seal the resulting relation table.

No lemma is finally enriched before closure succeeds.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

from scripts.lexicon.runner.contracts import RELATION_CLOSURE_VERSION, PhaseSeal, canonical_json

RelationKind = str  # synonym | antonym | homonym | paronym | corpus_synonym | …


def extract_and_close_relations(
    *,
    entries: Iterable[dict[str, Any]],
    extractors: dict[str, Callable[[dict[str, Any]], list[dict[str, Any]]]],
    headwords: dict[str, str],
    canonical_term_fn: Callable[[object], str | None],
    vesum_valid_fn: Callable[[str], bool] | None,
    output_db: Path,
    reciprocal_kinds: frozenset[str] | None = None,
) -> PhaseSeal:
    """Extract raw edges then seal reciprocal closure.

    Closure order matches ``_*_relations_by_headword`` exactly: for each entry in
    cohort order, append forward edges to the source, then append reciprocal
    edges onto targets that are cohort headwords. Kinds in ``reciprocal_kinds``
    receive reciprocity (synonym also requires ``vesum_valid_fn(source)``).
    """
    if reciprocal_kinds is None:
        reciprocal_kinds = frozenset({"synonym", "antonym"})

    output_db.parent.mkdir(parents=True, exist_ok=True)
    if output_db.exists():
        output_db.unlink()

    entry_list = list(entries)
    # Phase 2a — durable raw edges (deterministic).
    raw_rows: list[tuple[str, str, str, str]] = []
    for entry in entry_list:
        lemma = str(entry.get("lemma") or "")
        source_key = canonical_term_fn(lemma)
        if not source_key:
            continue
        for kind, extractor in extractors.items():
            for relation in extractor(entry):
                target_key = str(relation.get("item") or "")
                if not target_key:
                    continue
                payload = json.dumps(relation, ensure_ascii=False, sort_keys=True)
                raw_rows.append((source_key, kind, target_key, payload))

    # Phase 2b — run-level reciprocal closure (legacy by_headword order).
    closed_by_kind: dict[str, dict[str, list[dict[str, Any]]]] = {
        kind: {} for kind in extractors
    }
    for entry in entry_list:
        lemma = str(entry.get("lemma") or "")
        source_key = canonical_term_fn(lemma)
        if not source_key:
            continue
        for kind, extractor in extractors.items():
            relations = extractor(entry)
            if not relations:
                continue
            bucket = closed_by_kind[kind]
            if kind in {"homonym", "paronym"}:
                # Homonym/paronym by_headword replaces (not extends) per source.
                bucket[source_key] = list(relations)
                continue
            bucket.setdefault(source_key, []).extend(relations)
            if kind not in reciprocal_kinds:
                continue
            for relation in relations:
                target_key = str(relation.get("item") or "")
                if target_key not in headwords:
                    continue
                if (
                    kind == "synonym"
                    and vesum_valid_fn is not None
                    and not vesum_valid_fn(source_key)
                ):
                    continue
                reciprocal = dict(relation)
                reciprocal["item"] = headwords[source_key]
                reciprocal["direction"] = "reciprocal"
                bucket.setdefault(target_key, []).append(reciprocal)

    closed: list[tuple[str, str, str, str, str]] = []
    for kind, by_headword in closed_by_kind.items():
        for source_key in sorted(by_headword):
            for relation in by_headword[source_key]:
                target_key = str(relation.get("item") or "")
                direction = str(relation.get("direction") or "forward")
                payload = json.dumps(relation, ensure_ascii=False, sort_keys=True)
                closed.append((source_key, kind, target_key, direction, payload))

    conn = sqlite3.connect(output_db)
    try:
        conn.executescript(
            """
            CREATE TABLE meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE raw_relations (
                source_key TEXT NOT NULL,
                kind TEXT NOT NULL,
                target_key TEXT NOT NULL,
                payload TEXT NOT NULL
            );
            CREATE TABLE relations (
                source_key TEXT NOT NULL,
                kind TEXT NOT NULL,
                target_key TEXT NOT NULL,
                direction TEXT NOT NULL,
                payload TEXT NOT NULL
            );
            CREATE INDEX idx_rel_source ON relations(source_key, kind);
            """
        )
        conn.executemany(
            """
            INSERT INTO raw_relations(source_key, kind, target_key, payload)
            VALUES (?, ?, ?, ?)
            """,
            raw_rows,
        )
        conn.executemany(
            """
            INSERT INTO relations(source_key, kind, target_key, direction, payload)
            VALUES (?, ?, ?, ?, ?)
            """,
            closed,
        )
        # Seal over closed maps in legacy list order (not re-sorted payloads).
        seal_payload = {
            "algorithm_version": RELATION_CLOSURE_VERSION,
            "closed": {
                kind: {
                    source: by_hw[source]
                    for source in sorted(by_hw)
                }
                for kind, by_hw in closed_by_kind.items()
            },
        }
        seal_sha = hashlib.sha256(canonical_json(seal_payload).encode("utf-8")).hexdigest()
        conn.execute(
            "INSERT INTO meta(key, value) VALUES (?, ?)",
            ("seal_sha256", seal_sha),
        )
        conn.execute(
            "INSERT INTO meta(key, value) VALUES (?, ?)",
            ("algorithm_version", RELATION_CLOSURE_VERSION),
        )
        conn.execute(
            "INSERT INTO meta(key, value) VALUES (?, ?)",
            ("row_count", str(len(closed))),
        )
        conn.commit()
    finally:
        conn.close()
    return PhaseSeal(
        phase="relation_closure",
        seal_sha256=seal_sha,
        algorithm_version=RELATION_CLOSURE_VERSION,
        row_count=len(closed),
    )


def load_closed_relations_by_headword(
    path: Path,
    *,
    kind: str,
) -> dict[str, list[dict[str, Any]]]:
    """Load sealed closed relations for one kind, keyed by source headword.

    Preserves insertion order within each source (legacy by_headword order).
    """
    conn = sqlite3.connect(f"file:{path.resolve().as_posix()}?mode=ro", uri=True)
    try:
        out: dict[str, list[dict[str, Any]]] = {}
        for source_key, payload in conn.execute(
            """
            SELECT source_key, payload FROM relations
            WHERE kind = ?
            ORDER BY rowid
            """,
            (kind,),
        ):
            relation = json.loads(str(payload))
            if isinstance(relation, dict):
                out.setdefault(str(source_key), []).append(relation)
        return out
    finally:
        conn.close()


def seal_hash(path: Path) -> str:
    conn = sqlite3.connect(f"file:{path.resolve().as_posix()}?mode=ro", uri=True)
    try:
        row = conn.execute("SELECT value FROM meta WHERE key = 'seal_sha256'").fetchone()
        if not row:
            raise ValueError(f"missing seal_sha256 in {path}")
        return str(row[0])
    finally:
        conn.close()
