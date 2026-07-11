#!/usr/bin/env python3
"""Load VESUM-gated relation candidate artifacts into ``relation_pairs``.

Candidate artifacts contain relation facts and provenance only.  Miner-provided
``distinction`` prose is intentionally not imported: source glosses may be
copyrighted.  Only explicitly supplied project-authored ``gloss_a`` and
``gloss_b`` fields may enter the corpus.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lexicon.relation_pairs import (
    RELATION_TYPES,
    ensure_relation_pairs_schema,
    is_exact_vesum_lemma,
    normalize_relation_word,
)

DEFAULT_DB = ROOT / "data" / "sources.db"
DEFAULT_CANDIDATES_DIR = ROOT / "data" / "lexicon"
_CURATED_SOURCE_MARKERS = ("wikipedia", "wiktionary", "miyklas", "ukr-mova", "словник", "dictionary", "zno", "grinchyshyn")
_GENERATED_SOURCE_MARKERS = ("generated", "llm", "model")


@dataclass(frozen=True, slots=True)
class Candidate:
    relation: str
    word_a: str
    word_b: str
    gloss_a: str
    gloss_b: str
    source: str
    source_url: str
    confidence: str
    review_status: str


@dataclass(slots=True)
class LoadSummary:
    accepted: int = 0
    skipped_invalid: int = 0
    skipped_vesum: int = 0
    inserted: int = 0
    updated: int = 0
    unchanged: int = 0


def _infer_relation(path: Path, payload: object) -> str | None:
    if isinstance(payload, dict):
        relation = str(payload.get("relation") or "").strip().casefold()
        if relation in RELATION_TYPES:
            return relation
    return "paronym" if "paronym" in path.stem.casefold() else None


def _confidence_for(source: str, supplied: object) -> str:
    value = str(supplied or "").strip().casefold()
    if value in {"high", "medium", "low"}:
        return value
    source_key = source.casefold()
    if any(marker in source_key for marker in _GENERATED_SOURCE_MARKERS):
        return "low"
    if any(marker in source_key for marker in _CURATED_SOURCE_MARKERS):
        return "high"
    return "medium"


def _candidate_records(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return {}, [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return {}, []
    values = payload.get("pairs") or payload.get("relations") or payload.get("items") or []
    return payload, [item for item in values if isinstance(item, dict)] if isinstance(values, list) else []


def _project_authored_gloss(raw: dict[str, Any], root: dict[str, Any], key: str) -> str:
    """Accept a gloss only when its artifact explicitly attests its origin."""
    is_project_authored = raw.get("glosses_are_project_authored", root.get("glosses_are_project_authored", False))
    return str(raw.get(key) or "").strip() if is_project_authored is True else ""


def _normalise_candidate(path: Path, root: dict[str, Any], raw: dict[str, Any]) -> Candidate | None:
    relation = str(raw.get("relation") or root.get("relation") or _infer_relation(path, root) or "").strip().casefold()
    if relation not in RELATION_TYPES:
        return None
    word_a = normalize_relation_word(raw.get("word_a") or raw.get("lemma_a"))
    word_b = normalize_relation_word(raw.get("word_b") or raw.get("lemma_b"))
    source = str(raw.get("source") or root.get("source") or "").strip()
    if not word_a or not word_b or not source:
        return None

    # Relation pairs are undirected. Keep the gloss paired with its lemma while
    # canonicalizing the database key so reversed miner output deduplicates.
    gloss_a = _project_authored_gloss(raw, root, "gloss_a")
    gloss_b = _project_authored_gloss(raw, root, "gloss_b")
    if word_b < word_a:
        word_a, word_b = word_b, word_a
        gloss_a, gloss_b = gloss_b, gloss_a
    status = str(raw.get("review_status") or "candidate").strip().casefold()
    if status not in {"candidate", "approved", "rejected"}:
        status = "candidate"
    return Candidate(
        relation=relation,
        word_a=word_a,
        word_b=word_b,
        gloss_a=gloss_a,
        gloss_b=gloss_b,
        source=source,
        source_url=str(raw.get("source_url") or raw.get("source_page") or raw.get("url") or root.get("source_url") or "").strip(),
        confidence=_confidence_for(source, raw.get("confidence") or root.get("confidence")),
        review_status=status,
    )


def _iter_candidates(candidates_dir: Path, source_filter: str | None, summary: LoadSummary):
    for path in sorted(candidates_dir.glob("*_candidates_*.json")):
        root, records = _candidate_records(path)
        for raw in records:
            candidate = _normalise_candidate(path, root, raw)
            if candidate is None:
                summary.skipped_invalid += 1
                continue
            if source_filter and candidate.source != source_filter:
                continue
            if not (is_exact_vesum_lemma(candidate.word_a) and is_exact_vesum_lemma(candidate.word_b)):
                summary.skipped_vesum += 1
                continue
            summary.accepted += 1
            yield candidate


def _existing_row(conn: sqlite3.Connection, candidate: Candidate) -> tuple[str, str, str, str, str] | None:
    return conn.execute(
        """
        SELECT gloss_a, gloss_b, source_url, confidence, review_status
        FROM relation_pairs
        WHERE relation = ? AND word_a = ? AND word_b = ? AND source = ?
        """,
        (candidate.relation, candidate.word_a, candidate.word_b, candidate.source),
    ).fetchone()


def _upsert(conn: sqlite3.Connection, candidate: Candidate) -> None:
    conn.execute(
        """
        INSERT INTO relation_pairs(
            relation, word_a, word_b, gloss_a, gloss_b, source, source_url,
            confidence, review_status, added_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(relation, word_a, word_b, source) DO UPDATE SET
            gloss_a = CASE WHEN excluded.gloss_a != '' THEN excluded.gloss_a ELSE relation_pairs.gloss_a END,
            gloss_b = CASE WHEN excluded.gloss_b != '' THEN excluded.gloss_b ELSE relation_pairs.gloss_b END,
            source_url = CASE WHEN excluded.source_url != '' THEN excluded.source_url ELSE relation_pairs.source_url END,
            confidence = excluded.confidence,
            review_status = CASE
                WHEN relation_pairs.review_status IN ('approved', 'rejected')
                    AND excluded.review_status = 'candidate'
                THEN relation_pairs.review_status
                ELSE excluded.review_status
            END
        """,
        (
            candidate.relation,
            candidate.word_a,
            candidate.word_b,
            candidate.gloss_a,
            candidate.gloss_b,
            candidate.source,
            candidate.source_url,
            candidate.confidence,
            candidate.review_status,
            datetime.now(UTC).isoformat(),
        ),
    )


def load_candidates(
    db_path: Path,
    candidates_dir: Path,
    *,
    source_filter: str | None = None,
    dry_run: bool = False,
) -> tuple[LoadSummary, Counter[tuple[str, str]]]:
    """Load all matching candidates and return result counts by source/relation."""
    summary = LoadSummary()
    by_source_relation: Counter[tuple[str, str]] = Counter()
    candidates = list(_iter_candidates(candidates_dir, source_filter, summary))
    for candidate in candidates:
        by_source_relation[(candidate.source, candidate.relation)] += 1
    if dry_run:
        return summary, by_source_relation

    conn = sqlite3.connect(db_path)
    try:
        ensure_relation_pairs_schema(conn)
        for candidate in candidates:
            before = _existing_row(conn, candidate)
            review_status = (
                before[4]
                if before and before[4] in {"approved", "rejected"} and candidate.review_status == "candidate"
                else candidate.review_status
            )
            after = (
                candidate.gloss_a or (before[0] if before else ""),
                candidate.gloss_b or (before[1] if before else ""),
                candidate.source_url or (before[2] if before else ""),
                candidate.confidence,
                review_status,
            )
            _upsert(conn, candidate)
            if before is None:
                summary.inserted += 1
            elif before == after:
                summary.unchanged += 1
            else:
                summary.updated += 1
        conn.commit()
    finally:
        conn.close()
    return summary, by_source_relation


def _print_summary(summary: LoadSummary, by_source_relation: Counter[tuple[str, str]]) -> None:
    print(
        "relation candidates: "
        f"accepted={summary.accepted} inserted={summary.inserted} updated={summary.updated} "
        f"unchanged={summary.unchanged} skipped_invalid={summary.skipped_invalid} "
        f"skipped_vesum={summary.skipped_vesum}"
    )
    for (source, relation), count in sorted(by_source_relation.items()):
        print(f"  {source} | {relation}: {count}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Load VESUM-gated relation candidate JSON into sources.db.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="SQLite sources database path.")
    parser.add_argument("--candidates-dir", type=Path, default=DEFAULT_CANDIDATES_DIR, help="Directory containing *_candidates_*.json artifacts.")
    parser.add_argument("--source", dest="source_filter", help="Load only records attributed to this source.")
    parser.add_argument("--dry-run", action="store_true", help="Validate and summarize without creating or changing the database.")
    args = parser.parse_args()
    summary, by_source_relation = load_candidates(
        args.db,
        args.candidates_dir,
        source_filter=args.source_filter,
        dry_run=args.dry_run,
    )
    _print_summary(summary, by_source_relation)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
