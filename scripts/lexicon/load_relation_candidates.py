#!/usr/bin/env python3
"""Load relation candidate artifacts into ``relation_pairs``.

Candidate artifacts contain relation facts and provenance only.  Miner-provided
``distinction`` prose is intentionally not imported: source glosses may be
copyrighted.  Only explicitly supplied project-authored ``gloss_a`` and
``gloss_b`` fields may enter the corpus.

Untrusted mined candidates remain VESUM-gated. A VESUM gap can be retained
only through an exact local dictionary attestation, or through a deliberately
small set of source-vetted candidate registers.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.audit.validate_atlas_conformance import HeritageLemmaLookup
from scripts.lexicon.relation_pairs import (
    RELATION_TYPES,
    ensure_relation_pairs_schema,
    is_exact_vesum_lemma,
    normalize_relation_word,
)

DEFAULT_DB = ROOT / "data" / "sources.db"
DEFAULT_CANDIDATES_DIR = ROOT / "data" / "lexicon"
DEFAULT_SYNONYM_VERDICTS = DEFAULT_CANDIDATES_DIR / "synonym_pair_verdicts.yaml"
SYNONYM_VERDICTS_SOURCE = "synonym_verdicts"
_CURATED_SOURCE_MARKERS = (
    "wikipedia",
    "wiktionary",
    "miyklas",
    "ukr-mova",
    "словник",
    "dictionary",
    "zno",
    "grinchyshyn",
)
_GENERATED_SOURCE_MARKERS = ("generated", "llm", "model")
_EXCLUDED_CANDIDATE_FILENAMES = frozenset({"relation_candidates_sample.json"})
# These registers are teacher- or dictionary-vetted rather than mined guesses.
# Keep this explicit: every other source remains VESUM- and heritage-gated.
TRUSTED_CANDIDATE_SOURCES = frozenset(
    {
        "miyklas.com.ua",
        "grinchyshyn-1986",
        "ukr-mova.in.ua",
    }
)


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
    kept_via_heritage: int = 0
    kept_via_trusted_source: int = 0
    still_dropped: int = 0
    dropped_lemmas: Counter[str] = field(default_factory=Counter)
    inserted: int = 0
    updated: int = 0
    unchanged: int = 0


class RelationHeritageLookup(HeritageLemmaLookup):
    """Exact heritage/dictionary lookup for relation-candidate VESUM gaps.

    This reuses #3211's ``HeritageLemmaLookup`` for exact Грінченко and ЕСУМ
    headwords. Relation candidates also need the canonical СУМ-20 snapshot used
    by ``sources.search_heritage``. When that snapshot is not cached locally,
    the project СУМ dictionary table remains a compatible exact-headword
    fallback. No prefix or body matches are accepted.
    """

    _SUM_TABLES = (("sum20", "word"), ("sum11", "word"))

    def __init__(self, db_path: Path = DEFAULT_DB):
        super().__init__(db_path)
        self._dictionary_tables: frozenset[str] | None = None
        self._dictionary_columns: dict[str, frozenset[str]] = {}
        self._dictionary_cache: dict[str, bool] = {}

    def has_attestation(self, lemma: str) -> bool:
        normalized = normalize_relation_word(lemma)
        if not normalized:
            return False
        if normalized in self._dictionary_cache:
            return self._dictionary_cache[normalized]

        try:
            if super().has_attestation(normalized):
                self._dictionary_cache[normalized] = True
                return True
        except sqlite3.DatabaseError:
            # A deliberately small fixture or a partial sources database can
            # lack a #3211 table. Continue to the available exact dictionary
            # tables; missing evidence must still fail closed.
            pass

        self._dictionary_cache[normalized] = self._has_dictionary_headword(normalized)
        return self._dictionary_cache[normalized]

    def _has_dictionary_headword(self, lemma: str) -> bool:
        self.open()
        assert self._conn is not None
        if self._dictionary_tables is None:
            self._dictionary_tables = frozenset(
                str(row[0]) for row in self._conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
            )

        slovnyk_columns = self._columns_for("slovnyk_me_entries")
        if {"normalized_word", "dictionary_slug"} <= slovnyk_columns:
            row = self._conn.execute(
                """
                SELECT 1 FROM slovnyk_me_entries
                WHERE normalized_word = ? AND dictionary_slug = 'newsum'
                LIMIT 1
                """,
                (lemma,),
            ).fetchone()
            if row:
                return True

        for table, column in self._SUM_TABLES:
            if column not in self._columns_for(table):
                continue
            row = self._conn.execute(
                f"SELECT 1 FROM {table} WHERE {column} = ? LIMIT 1",
                (lemma,),
            ).fetchone()
            if row:
                return True
        return False

    def _columns_for(self, table: str) -> frozenset[str]:
        if self._dictionary_tables is None or table not in self._dictionary_tables:
            return frozenset()
        if table not in self._dictionary_columns:
            self._dictionary_columns[table] = frozenset(
                str(row[1]) for row in self._conn.execute(f"PRAGMA table_info({table})")
            )
        return self._dictionary_columns[table]


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
        source_url=str(
            raw.get("source_url") or raw.get("source_page") or raw.get("url") or root.get("source_url") or ""
        ).strip(),
        confidence=_confidence_for(source, raw.get("confidence") or root.get("confidence")),
        review_status=status,
    )


def _is_trusted_candidate_source(source: str) -> bool:
    return source.strip().casefold() in TRUSTED_CANDIDATE_SOURCES


def _iter_candidates(
    candidates_dir: Path,
    source_filter: str | None,
    summary: LoadSummary,
    heritage: RelationHeritageLookup | None,
):
    for path in sorted(candidates_dir.glob("*_candidates_*.json")):
        if path.name in _EXCLUDED_CANDIDATE_FILENAMES:
            continue
        root, records = _candidate_records(path)
        for raw in records:
            candidate = _normalise_candidate(path, root, raw)
            if candidate is None:
                summary.skipped_invalid += 1
                continue
            if source_filter and candidate.source != source_filter:
                continue
            missing_vesum = [word for word in (candidate.word_a, candidate.word_b) if not is_exact_vesum_lemma(word)]
            if not missing_vesum:
                summary.accepted += 1
                yield candidate
                continue
            if heritage is not None and all(heritage.has_attestation(word) for word in missing_vesum):
                summary.kept_via_heritage += 1
                summary.accepted += 1
                yield candidate
                continue
            if _is_trusted_candidate_source(candidate.source):
                summary.kept_via_trusted_source += 1
                summary.accepted += 1
                yield candidate
                continue

            # Retain the legacy field for downstream callers while exposing a
            # more accurate name and the exact missing lemmas in the CLI report.
            summary.still_dropped += 1
            summary.dropped_lemmas.update(missing_vesum)
            summary.skipped_vesum += 1


def _approved_synonym_verdict_candidates(verdicts_path: Path) -> list[Candidate]:
    """Return deterministic corpus rows from reviewed synonym verdicts only.

    The verdict artifact is a human-reviewed approval register, unlike mined
    ``*_candidates_*.json`` artifacts.  Its rows therefore enter the corpus
    with an explicit, dedicated provenance rather than inheriting any mining
    source or candidate status.
    """
    try:
        payload = yaml.safe_load(verdicts_path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise ValueError(f"Cannot load synonym verdicts: {verdicts_path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Synonym verdicts must be a mapping: {verdicts_path}")
    approved = payload.get("approved")
    if not isinstance(approved, list):
        raise ValueError(f"Synonym verdicts approved section must be a list: {verdicts_path}")

    pairs: set[tuple[str, str]] = set()
    for index, verdict in enumerate(approved):
        if not isinstance(verdict, dict):
            raise ValueError(f"Approved synonym verdict {index} must be a mapping: {verdicts_path}")
        if str(verdict.get("polarity") or "").strip().casefold() != "synonym":
            continue
        word_a = normalize_relation_word(verdict.get("a"))
        word_b = normalize_relation_word(verdict.get("b"))
        if not word_a or not word_b:
            raise ValueError(f"Approved synonym verdict {index} lacks a valid lemma: {verdicts_path}")
        if word_a != word_b:
            pairs.add(tuple(sorted((word_a, word_b))))

    return [
        Candidate(
            relation="synonym",
            word_a=word_a,
            word_b=word_b,
            gloss_a="",
            gloss_b="",
            source=SYNONYM_VERDICTS_SOURCE,
            source_url="",
            confidence="high",
            review_status="approved",
        )
        for word_a, word_b in sorted(pairs)
    ]


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
    heritage_db_path: Path | None = DEFAULT_DB,
) -> tuple[LoadSummary, Counter[tuple[str, str]]]:
    """Load all matching candidates and return result counts by source/relation."""
    summary = LoadSummary()
    by_source_relation: Counter[tuple[str, str]] = Counter()
    heritage: RelationHeritageLookup | None = None
    if heritage_db_path is not None:
        try:
            heritage = RelationHeritageLookup(heritage_db_path)
            heritage.open()
        except FileNotFoundError:
            heritage = None
    try:
        candidates = list(_iter_candidates(candidates_dir, source_filter, summary, heritage))
    finally:
        if heritage is not None:
            heritage.close()
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


def load_approved_synonym_verdicts(
    db_path: Path,
    verdicts_path: Path = DEFAULT_SYNONYM_VERDICTS,
    *,
    dry_run: bool = False,
) -> LoadSummary:
    """Import only approved synonym verdicts as durable approved corpus rows.

    This is deliberately separate from mined-candidate ingestion: no candidate
    row is promoted here, and verdict rows use ``synonym_verdicts`` provenance
    so their review origin remains visible in rendered manifest sections.
    """
    summary = LoadSummary()
    candidates: list[Candidate] = []
    for candidate in _approved_synonym_verdict_candidates(verdicts_path):
        if not (is_exact_vesum_lemma(candidate.word_a) and is_exact_vesum_lemma(candidate.word_b)):
            summary.skipped_vesum += 1
            continue
        summary.accepted += 1
        candidates.append(candidate)
    if dry_run:
        return summary

    conn = sqlite3.connect(db_path)
    try:
        ensure_relation_pairs_schema(conn)
        for candidate in candidates:
            before = _existing_row(conn, candidate)
            _upsert(conn, candidate)
            if before is None:
                summary.inserted += 1
            elif before == (
                candidate.gloss_a,
                candidate.gloss_b,
                candidate.source_url,
                candidate.confidence,
                candidate.review_status,
            ):
                summary.unchanged += 1
            else:
                summary.updated += 1
        conn.commit()
    finally:
        conn.close()
    return summary


def _print_summary(summary: LoadSummary, by_source_relation: Counter[tuple[str, str]]) -> None:
    dropped_lemmas = ",".join(sorted(summary.dropped_lemmas)) or "none"
    print(
        "relation candidates: "
        f"accepted={summary.accepted} inserted={summary.inserted} updated={summary.updated} "
        f"unchanged={summary.unchanged} skipped_invalid={summary.skipped_invalid} "
        f"skipped_vesum={summary.skipped_vesum} "
        f"kept_via_heritage={summary.kept_via_heritage} "
        f"kept_via_trusted_source={summary.kept_via_trusted_source} "
        f"still_dropped={summary.still_dropped} dropped_lemmas={dropped_lemmas}"
    )
    for (source, relation), count in sorted(by_source_relation.items()):
        print(f"  {source} | {relation}: {count}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Load VESUM- or source-attested relation candidate JSON into sources.db."
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="SQLite sources database path.")
    parser.add_argument(
        "--candidates-dir",
        type=Path,
        default=DEFAULT_CANDIDATES_DIR,
        help="Directory containing *_candidates_*.json artifacts.",
    )
    parser.add_argument(
        "--synonym-verdicts", type=Path, default=DEFAULT_SYNONYM_VERDICTS, help="Reviewed synonym verdict YAML."
    )
    parser.add_argument(
        "--heritage-db",
        type=Path,
        default=DEFAULT_DB,
        help="sources.db for the exact Грінченко/ЕСУМ/СУМ heritage fallback.",
    )
    parser.add_argument("--source", dest="source_filter", help="Load only records attributed to this source.")
    parser.add_argument(
        "--dry-run", action="store_true", help="Validate and summarize without creating or changing the database."
    )
    args = parser.parse_args()
    summary, by_source_relation = load_candidates(
        args.db,
        args.candidates_dir,
        source_filter=args.source_filter,
        dry_run=args.dry_run,
        heritage_db_path=args.heritage_db,
    )
    _print_summary(summary, by_source_relation)
    verdict_summary = load_approved_synonym_verdicts(
        args.db,
        args.synonym_verdicts,
        dry_run=args.dry_run,
    )
    print(
        "approved synonym verdicts: "
        f"accepted={verdict_summary.accepted} inserted={verdict_summary.inserted} "
        f"updated={verdict_summary.updated} unchanged={verdict_summary.unchanged} "
        f"skipped_vesum={verdict_summary.skipped_vesum}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
