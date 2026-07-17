"""Phase 2 — raw relation extraction + run-level reciprocal closure (#5230 / #5331).

1. Stream raw pointer/relation edges per lemma into durable SQLite rows.
2. Run one run-level deterministic closure pass over those durable rows.
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

    The cohort is never materialized: raw edges stream into ``raw_relations``,
    then closure is a SQL-ordered pass over those durable rows.
    """
    if reciprocal_kinds is None:
        reciprocal_kinds = frozenset({"synonym", "antonym"})

    output_db.parent.mkdir(parents=True, exist_ok=True)
    if output_db.exists():
        output_db.unlink()

    conn = sqlite3.connect(output_db)
    try:
        conn.executescript(
            """
            CREATE TABLE meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE raw_relations (
                entry_ord INTEGER NOT NULL,
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
            CREATE INDEX idx_raw_entry ON raw_relations(entry_ord, kind);
            CREATE INDEX idx_rel_source ON relations(source_key, kind);
            """
        )

        # Phase 2a — stream durable raw edges (one pass; no cohort list()).
        entry_ord = 0
        raw_batch: list[tuple[int, str, str, str, str]] = []
        for entry in entries:
            lemma = str(entry.get("lemma") or "")
            source_key = canonical_term_fn(lemma)
            if not source_key:
                entry_ord += 1
                continue
            for kind, extractor in extractors.items():
                for relation in extractor(entry):
                    target_key = str(relation.get("item") or "")
                    if not target_key:
                        continue
                    payload = json.dumps(relation, ensure_ascii=False, sort_keys=True)
                    raw_batch.append((entry_ord, source_key, kind, target_key, payload))
            entry_ord += 1
            if len(raw_batch) >= 2000:
                conn.executemany(
                    """
                    INSERT INTO raw_relations(
                        entry_ord, source_key, kind, target_key, payload
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    raw_batch,
                )
                conn.commit()
                raw_batch.clear()
        if raw_batch:
            conn.executemany(
                """
                INSERT INTO raw_relations(
                    entry_ord, source_key, kind, target_key, payload
                ) VALUES (?, ?, ?, ?, ?)
                """,
                raw_batch,
            )
            conn.commit()
            raw_batch.clear()

        # Phase 2b — run-level reciprocal closure over durable rows (legacy order).
        closed_by_kind: dict[str, dict[str, list[dict[str, Any]]]] = {
            kind: {} for kind in extractors
        }
        kind_order = list(extractors.keys())
        cursor = conn.execute(
            """
            SELECT entry_ord, source_key, kind, payload
            FROM raw_relations
            ORDER BY entry_ord, rowid
            """
        )
        current_ord: int | None = None
        # Per entry_ord: kind -> (source_key, relations) collected in extractor order.
        pending: dict[str, tuple[str, list[dict[str, Any]]]] = {}

        def _flush_entry() -> None:
            for kind in kind_order:
                packed = pending.get(kind)
                if not packed:
                    continue
                source_key, relations = packed
                if not relations:
                    continue
                bucket = closed_by_kind[kind]
                if kind in {"homonym", "paronym"}:
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
            pending.clear()

        for entry_ord_row, source_key, kind, payload in cursor:
            ord_i = int(entry_ord_row)
            if current_ord is None:
                current_ord = ord_i
            elif ord_i != current_ord:
                _flush_entry()
                current_ord = ord_i
            relation = json.loads(str(payload))
            if not isinstance(relation, dict):
                continue
            if kind not in pending:
                pending[kind] = (str(source_key), [])
            pending[kind][1].append(relation)
        if current_ord is not None:
            _flush_entry()

        closed: list[tuple[str, str, str, str, str]] = []
        for kind, by_headword in closed_by_kind.items():
            for source_key in sorted(by_headword):
                for relation in by_headword[source_key]:
                    target_key = str(relation.get("item") or "")
                    direction = str(relation.get("direction") or "forward")
                    payload = json.dumps(relation, ensure_ascii=False, sort_keys=True)
                    closed.append((source_key, kind, target_key, direction, payload))

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
