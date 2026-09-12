"""VESUM SQLite lookup helpers.

This module owns the local VESUM morphological dictionary connection, the
public verification API (verify_word, verify_words, verify_lemma), and the
marker-aware inspection API (inspect_word, inspect_words, inspect_lemma).
"""

from __future__ import annotations

import argparse
import contextlib
import json
import sqlite3
import sys
import threading
from collections.abc import Iterator
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from scripts.rag.config import VESUM_DB_PATH

_vesum_conn = None
_vesum_conn_path: Path | None = None
_vesum_conn_stat: tuple[int, int] | None = None
_CONN_LOCK = threading.Lock()
_ACTIVE_CONNS: dict[sqlite3.Connection, int] = {}


class InspectionStatus(StrEnum):
    """Closed status enum for marker-aware VESUM inspection."""

    CLEAN = "CLEAN"
    KNOWN_INVALID = "KNOWN_INVALID"
    NONSTANDARD = "NONSTANDARD"
    COLLOQUIAL = "COLLOQUIAL"
    SLANG = "SLANG"
    ARCH_OR_DIALECT_UNRESOLVED = "ARCH_OR_DIALECT_UNRESOLVED"
    ORTHOGRAPHIC_VARIANT = "ORTHOGRAPHIC_VARIANT"
    VULGAR = "VULGAR"
    MIXED = "MIXED"
    NOT_FOUND = "NOT_FOUND"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class WordInspection:
    """Inspection result for a single word form."""

    word: str
    status: InspectionStatus
    clean_analyses: list[dict[str, Any]]
    marked_analyses: list[dict[str, Any]]
    effective_markers: list[str]
    source_locations: list[str]
    source_version: str
    pipeline_identity: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "word": self.word,
            "status": self.status.value,
            "clean_analyses": self.clean_analyses,
            "marked_analyses": self.marked_analyses,
            "effective_markers": self.effective_markers,
            "source_locations": self.source_locations,
            "source_version": self.source_version,
            "pipeline_identity": self.pipeline_identity,
        }


@dataclass(frozen=True)
class LemmaInspection:
    """Inspection result for an entire lemma paradigm."""

    lemma: str
    status: InspectionStatus
    clean_analyses: list[dict[str, Any]]
    marked_analyses: list[dict[str, Any]]
    forms: list[dict[str, Any]]
    effective_markers: list[str]
    source_locations: list[str]
    source_version: str
    pipeline_identity: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "lemma": self.lemma,
            "status": self.status.value,
            "clean_analyses": self.clean_analyses,
            "marked_analyses": self.marked_analyses,
            "forms": self.forms,
            "effective_markers": self.effective_markers,
            "source_locations": self.source_locations,
            "source_version": self.source_version,
            "pipeline_identity": self.pipeline_identity,
        }


def _resolve_vesum_db_path(db_path: str | Path | None = None) -> Path:
    if db_path is not None:
        return Path(db_path)
    return VESUM_DB_PATH


def _get_or_create_conn_locked(
    resolved_path: Path, current_stat: tuple[int, int] | None
) -> sqlite3.Connection:
    """Internal helper: return or create the cached SQLite connection under _CONN_LOCK."""
    global _vesum_conn, _vesum_conn_path, _vesum_conn_stat
    if (
        _vesum_conn is None
        or _vesum_conn_path != resolved_path
        or current_stat is None
        or _vesum_conn_stat != current_stat
    ):
        new_conn = sqlite3.connect(str(resolved_path), check_same_thread=False)
        new_conn.row_factory = sqlite3.Row

        old_conn = _vesum_conn
        _vesum_conn = new_conn
        _vesum_conn_path = resolved_path
        _vesum_conn_stat = current_stat

        # Superseded connection: only close immediately if it has NO active readers!
        if old_conn is not None and _ACTIVE_CONNS.get(old_conn, 0) <= 0:
            _ACTIVE_CONNS.pop(old_conn, None)
            with contextlib.suppress(Exception):
                old_conn.close()

    return _vesum_conn


def _release_conn(conn: sqlite3.Connection) -> None:
    """Release a reader on connection, closing it if superseded and idle."""
    global _vesum_conn
    with _CONN_LOCK:
        if conn in _ACTIVE_CONNS:
            _ACTIVE_CONNS[conn] -= 1
            if _ACTIVE_CONNS[conn] <= 0:
                _ACTIVE_CONNS.pop(conn, None)
                if conn is not _vesum_conn:
                    with contextlib.suppress(Exception):
                        conn.close()


@contextlib.contextmanager
def get_vesum_connection(db_path: str | Path | None = None) -> Iterator[sqlite3.Connection]:
    """Context manager guaranteeing connection retention across the reader's lifetime."""
    resolved_path = _resolve_vesum_db_path(db_path)
    if not resolved_path.exists():
        raise FileNotFoundError(
            f"VESUM database not found at {resolved_path}. "
            "Step 1 builds an explicit shadow database only; run "
            ".venv/bin/python scripts/rag/build_vesum_shadow.py --help "
            "and pass its explicit path with db_path after approved activation."
        )

    try:
        st = resolved_path.stat()
        current_stat = (st.st_ino, st.st_mtime_ns)
    except OSError:
        current_stat = None

    with _CONN_LOCK:
        conn = _get_or_create_conn_locked(resolved_path, current_stat)
        _ACTIVE_CONNS[conn] = _ACTIVE_CONNS.get(conn, 0) + 1

    try:
        yield conn
    finally:
        _release_conn(conn)


def get_vesum_conn(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Lazy-load SQLite connection to VESUM dictionary with automatic replacement detection."""
    resolved_path = _resolve_vesum_db_path(db_path)
    if not resolved_path.exists():
        raise FileNotFoundError(
            f"VESUM database not found at {resolved_path}. "
            "Step 1 builds an explicit shadow database only; run "
            ".venv/bin/python scripts/rag/build_vesum_shadow.py --help "
            "and pass its explicit path with db_path after approved activation."
        )

    try:
        st = resolved_path.stat()
        current_stat = (st.st_ino, st.st_mtime_ns)
    except OSError:
        current_stat = None

    with _CONN_LOCK:
        return _get_or_create_conn_locked(resolved_path, current_stat)


def close_vesum_conn(conn: sqlite3.Connection | None = None) -> None:
    """Close and reset cached SQLite connection, or close an explicitly provided connection."""
    global _vesum_conn, _vesum_conn_path, _vesum_conn_stat
    with _CONN_LOCK:
        target = conn if conn is not None else _vesum_conn
        if target is None:
            return
        if target is _vesum_conn:
            _vesum_conn = None
            _vesum_conn_path = None
            _vesum_conn_stat = None
        if _ACTIVE_CONNS.get(target, 0) <= 0:
            _ACTIVE_CONNS.pop(target, None)
            with contextlib.suppress(Exception):
                target.close()


def verify_word(
    word: str,
    pos_filter: str | None = None,
    db_path: str | Path | None = None,
) -> list[dict]:
    """Check if a word form exists in VESUM (compatibility view).

    Returns list of {lemma, pos, tags} matches. Empty list = not found.
    """
    with get_vesum_connection(db_path) as conn:
        if pos_filter:
            rows = conn.execute(
                "SELECT lemma, pos, tags FROM forms WHERE word_form = ? AND pos = ?",
                (word, pos_filter),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT lemma, pos, tags FROM forms WHERE word_form = ?",
                (word,),
            ).fetchall()
        return [{"lemma": r["lemma"], "pos": r["pos"], "tags": r["tags"]} for r in rows]


def verify_words(
    words: list[str],
    pos_filter: str | None = None,
    db_path: str | Path | None = None,
) -> dict[str, list[dict]]:
    """Batch-verify multiple word forms against VESUM in a single query.

    Returns dict mapping each word to its list of matches.
    Words not found map to an empty list.
    """
    if not words:
        return {}
    with get_vesum_connection(db_path) as conn:
        placeholders = ",".join("?" * len(words))
        if pos_filter:
            rows = conn.execute(
                f"SELECT word_form, lemma, pos, tags FROM forms WHERE word_form IN ({placeholders}) AND pos = ?",
                (*words, pos_filter),
            ).fetchall()
        else:
            rows = conn.execute(
                f"SELECT word_form, lemma, pos, tags FROM forms WHERE word_form IN ({placeholders})",
                words,
            ).fetchall()
        result: dict[str, list[dict]] = {w: [] for w in words}
        for r in rows:
            result[r["word_form"]].append({"lemma": r["lemma"], "pos": r["pos"], "tags": r["tags"]})
        return result


def verify_lemma(lemma: str, db_path: str | Path | None = None) -> list[dict]:
    """Get all inflected forms of a lemma.

    Returns list of {word_form, pos, tags} for every form.
    """
    with get_vesum_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT word_form, pos, tags FROM forms WHERE lemma = ? ORDER BY pos, tags",
            (lemma,),
        ).fetchall()
        return [{"word_form": r["word_form"], "pos": r["pos"], "tags": r["tags"]} for r in rows]


_REQUIRED_FORMS_ALL_COLS = frozenset(
    {"id", "entry_id", "word_form", "lemma", "pos", "tags", "source_comment", "source_location"}
)
_REQUIRED_FORM_MARKERS_COLS = frozenset({"form_id", "marker", "origin", "marker_class"})


def _has_inspection_schema(conn: sqlite3.Connection) -> bool:
    """Check if connection has the marker-preserving forms_all and form_markers schema with required columns."""
    try:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table', 'view') AND name IN ('forms_all', 'form_markers')"
            )
        }
        if len(tables) < 2:
            return False

        forms_all_cols = {row[1] for row in conn.execute("PRAGMA table_info(forms_all)")}
        if not _REQUIRED_FORMS_ALL_COLS.issubset(forms_all_cols):
            return False

        marker_cols = {row[1] for row in conn.execute("PRAGMA table_info(form_markers)")}
        return _REQUIRED_FORM_MARKERS_COLS.issubset(marker_cols)
    except sqlite3.Error:
        return False


def _get_metadata_and_version(conn: sqlite3.Connection) -> tuple[str, dict[str, Any]]:
    """Retrieve build metadata and version identifier if present."""
    try:
        has_meta = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='vesum_build_metadata'"
        ).fetchone()
        if not has_meta:
            return "v6.8.0", {}
        meta = {
            str(row[0]): str(row[1])
            for row in conn.execute("SELECT key, value FROM vesum_build_metadata").fetchall()
        }
        version = meta.get("canonical_jsonl_sha256") or meta.get("schema_version") or "v6.8.0"
        return version, meta
    except sqlite3.Error:
        return "v6.8.0", {}


def _resolve_inspection_status(
    clean_analyses: list[dict[str, Any]],
    marked_analyses: list[dict[str, Any]],
) -> InspectionStatus:
    """Determine closed InspectionStatus from clean and marked analyses."""
    if not clean_analyses and not marked_analyses:
        return InspectionStatus.NOT_FOUND

    if clean_analyses and not marked_analyses:
        return InspectionStatus.CLEAN

    if clean_analyses and marked_analyses:
        return InspectionStatus.MIXED

    # Only marked analyses exist.
    all_markers = {
        m["marker"]
        for a in marked_analyses
        for m in a.get("markers", [])
    }
    if not all_markers:
        return InspectionStatus.CLEAN

    if all_markers.issubset({"bad", "obsc"}):
        return InspectionStatus.KNOWN_INVALID
    if all_markers == {"subst"}:
        return InspectionStatus.NONSTANDARD
    if all_markers == {"slang"}:
        return InspectionStatus.SLANG
    if all_markers == {"coll"}:
        return InspectionStatus.COLLOQUIAL
    if all_markers.issubset({"arch", "dialect"}):
        return InspectionStatus.ARCH_OR_DIALECT_UNRESOLVED
    if all_markers == {"alt"}:
        return InspectionStatus.ORTHOGRAPHIC_VARIANT
    if all_markers == {"vulg"}:
        return InspectionStatus.VULGAR

    return InspectionStatus.MIXED


def inspect_word(
    word: str,
    pos_filter: str | None = None,
    db_path: str | Path | None = None,
) -> WordInspection:
    """Inspect a word form against VESUM forms_all and form_markers.

    Returns structured WordInspection with clean/marked separation and closed status.
    Fails closed with status=UNAVAILABLE if schema or database is unavailable.
    """
    try:
        with get_vesum_connection(db_path) as conn:
            if not _has_inspection_schema(conn):
                return WordInspection(
                    word=word,
                    status=InspectionStatus.UNAVAILABLE,
                    clean_analyses=[],
                    marked_analyses=[],
                    effective_markers=[],
                    source_locations=[],
                    source_version="unavailable",
                    pipeline_identity={},
                )

            version, meta = _get_metadata_and_version(conn)

            sql = """
                SELECT
                    f.id,
                    f.entry_id,
                    f.word_form,
                    f.lemma,
                    f.pos,
                    f.tags,
                    f.source_comment,
                    f.source_location,
                    m.marker,
                    m.origin,
                    m.marker_class
                FROM forms_all f
                LEFT JOIN form_markers m ON f.id = m.form_id
                WHERE f.word_form = ?
            """
            params: list[Any] = [word]
            if pos_filter:
                sql += " AND f.pos = ?"
                params.append(pos_filter)
            sql += " ORDER BY f.entry_id, f.id, m.marker, m.origin"

            rows = conn.execute(sql, params).fetchall()

            analyses_by_id: dict[int, dict[str, Any]] = {}
            markers_by_id: dict[int, list[dict[str, str]]] = {}
            locations: set[str] = set()
            effective_markers_set: set[str] = set()

            for r in rows:
                fid = r["id"]
                if fid not in analyses_by_id:
                    analyses_by_id[fid] = {
                        "entry_id": r["entry_id"],
                        "word_form": r["word_form"],
                        "lemma": r["lemma"],
                        "pos": r["pos"],
                        "tags": r["tags"],
                        "source_comment": r["source_comment"],
                        "source_location": r["source_location"],
                    }
                    markers_by_id[fid] = []
                    if r["source_location"]:
                        locations.add(r["source_location"])
                if r["marker"] is not None:
                    marker_dict = {
                        "marker": r["marker"],
                        "origin": r["origin"],
                        "marker_class": r["marker_class"],
                    }
                    markers_by_id[fid].append(marker_dict)
                    effective_markers_set.add(r["marker"])

            clean_analyses: list[dict[str, Any]] = []
            marked_analyses: list[dict[str, Any]] = []

            for fid, analysis in analyses_by_id.items():
                markers = markers_by_id[fid]
                if markers:
                    marked_copy = dict(analysis)
                    marked_copy["markers"] = markers
                    marked_analyses.append(marked_copy)
                else:
                    clean_analyses.append(analysis)

            status = _resolve_inspection_status(clean_analyses, marked_analyses)

            return WordInspection(
                word=word,
                status=status,
                clean_analyses=clean_analyses,
                marked_analyses=marked_analyses,
                effective_markers=sorted(effective_markers_set),
                source_locations=sorted(locations),
                source_version=version,
                pipeline_identity=meta,
            )
    except (FileNotFoundError, sqlite3.Error):
        return WordInspection(
            word=word,
            status=InspectionStatus.UNAVAILABLE,
            clean_analyses=[],
            marked_analyses=[],
            effective_markers=[],
            source_locations=[],
            source_version="unavailable",
            pipeline_identity={},
        )


def inspect_words(
    words: list[str],
    pos_filter: str | None = None,
    db_path: str | Path | None = None,
) -> dict[str, WordInspection]:
    """Batch inspect multiple word forms against VESUM forms_all and form_markers.

    Returns dict mapping each word to its WordInspection.
    """
    if not words:
        return {}

    try:
        with get_vesum_connection(db_path) as conn:
            if not _has_inspection_schema(conn):
                return {
                    w: WordInspection(
                        word=w,
                        status=InspectionStatus.UNAVAILABLE,
                        clean_analyses=[],
                        marked_analyses=[],
                        effective_markers=[],
                        source_locations=[],
                        source_version="unavailable",
                        pipeline_identity={},
                    )
                    for w in words
                }

            version, meta = _get_metadata_and_version(conn)

            unique_words = list(dict.fromkeys(words))
            placeholders = ",".join("?" * len(unique_words))
            sql = f"""
                SELECT
                    f.id,
                    f.entry_id,
                    f.word_form,
                    f.lemma,
                    f.pos,
                    f.tags,
                    f.source_comment,
                    f.source_location,
                    m.marker,
                    m.origin,
                    m.marker_class
                FROM forms_all f
                LEFT JOIN form_markers m ON f.id = m.form_id
                WHERE f.word_form IN ({placeholders})
            """
            params: list[Any] = list(unique_words)
            if pos_filter:
                sql += " AND f.pos = ?"
                params.append(pos_filter)
            sql += " ORDER BY f.word_form, f.entry_id, f.id, m.marker, m.origin"

            rows = conn.execute(sql, params).fetchall()

            data_by_word: dict[str, dict[int, dict[str, Any]]] = {w: {} for w in unique_words}
            markers_by_word_id: dict[str, dict[int, list[dict[str, str]]]] = {w: {} for w in unique_words}
            locations_by_word: dict[str, set[str]] = {w: set() for w in unique_words}
            effective_markers_by_word: dict[str, set[str]] = {w: set() for w in unique_words}

            for r in rows:
                wf = r["word_form"]
                fid = r["id"]
                if wf in data_by_word:
                    if fid not in data_by_word[wf]:
                        data_by_word[wf][fid] = {
                            "entry_id": r["entry_id"],
                            "word_form": r["word_form"],
                            "lemma": r["lemma"],
                            "pos": r["pos"],
                            "tags": r["tags"],
                            "source_comment": r["source_comment"],
                            "source_location": r["source_location"],
                        }
                        markers_by_word_id[wf][fid] = []
                        if r["source_location"]:
                            locations_by_word[wf].add(r["source_location"])
                    if r["marker"] is not None:
                        marker_dict = {
                            "marker": r["marker"],
                            "origin": r["origin"],
                            "marker_class": r["marker_class"],
                        }
                        markers_by_word_id[wf][fid].append(marker_dict)
                        effective_markers_by_word[wf].add(r["marker"])

            results: dict[str, WordInspection] = {}
            for w in words:
                clean_analyses = []
                marked_analyses = []
                analyses_dict = data_by_word.get(w, {})
                for fid, analysis in analyses_dict.items():
                    markers = markers_by_word_id[w].get(fid, [])
                    if markers:
                        marked_copy = dict(analysis)
                        marked_copy["markers"] = markers
                        marked_analyses.append(marked_copy)
                    else:
                        clean_analyses.append(analysis)
                status = _resolve_inspection_status(clean_analyses, marked_analyses)
                results[w] = WordInspection(
                    word=w,
                    status=status,
                    clean_analyses=clean_analyses,
                    marked_analyses=marked_analyses,
                    effective_markers=sorted(effective_markers_by_word.get(w, set())),
                    source_locations=sorted(locations_by_word.get(w, set())),
                    source_version=version,
                    pipeline_identity=meta,
                )

            return results
    except (FileNotFoundError, sqlite3.Error):
        return {
            w: WordInspection(
                word=w,
                status=InspectionStatus.UNAVAILABLE,
                clean_analyses=[],
                marked_analyses=[],
                effective_markers=[],
                source_locations=[],
                source_version="unavailable",
                pipeline_identity={},
            )
            for w in words
        }


def inspect_lemma(
    lemma: str,
    db_path: str | Path | None = None,
) -> LemmaInspection:
    """Inspect all inflected forms of a lemma in VESUM forms_all.

    Returns LemmaInspection with paradigm forms, clean/marked breakdown, and status.
    """
    try:
        with get_vesum_connection(db_path) as conn:
            if not _has_inspection_schema(conn):
                return LemmaInspection(
                    lemma=lemma,
                    status=InspectionStatus.UNAVAILABLE,
                    clean_analyses=[],
                    marked_analyses=[],
                    forms=[],
                    effective_markers=[],
                    source_locations=[],
                    source_version="unavailable",
                    pipeline_identity={},
                )

            version, meta = _get_metadata_and_version(conn)

            sql = """
                SELECT
                    f.id,
                    f.entry_id,
                    f.word_form,
                    f.lemma,
                    f.pos,
                    f.tags,
                    f.source_comment,
                    f.source_location,
                    m.marker,
                    m.origin,
                    m.marker_class
                FROM forms_all f
                LEFT JOIN form_markers m ON f.id = m.form_id
                WHERE f.lemma = ?
                ORDER BY f.pos, f.tags, f.word_form, m.marker
            """
            rows = conn.execute(sql, (lemma,)).fetchall()

            analyses_by_id: dict[int, dict[str, Any]] = {}
            markers_by_id: dict[int, list[dict[str, str]]] = {}
            locations: set[str] = set()
            effective_markers_set: set[str] = set()

            for r in rows:
                fid = r["id"]
                if fid not in analyses_by_id:
                    analyses_by_id[fid] = {
                        "entry_id": r["entry_id"],
                        "word_form": r["word_form"],
                        "lemma": r["lemma"],
                        "pos": r["pos"],
                        "tags": r["tags"],
                        "source_comment": r["source_comment"],
                        "source_location": r["source_location"],
                    }
                    markers_by_id[fid] = []
                    if r["source_location"]:
                        locations.add(r["source_location"])
                if r["marker"] is not None:
                    marker_dict = {
                        "marker": r["marker"],
                        "origin": r["origin"],
                        "marker_class": r["marker_class"],
                    }
                    markers_by_id[fid].append(marker_dict)
                    effective_markers_set.add(r["marker"])

            clean_analyses: list[dict[str, Any]] = []
            marked_analyses: list[dict[str, Any]] = []
            all_forms: list[dict[str, Any]] = []

            for fid, analysis in analyses_by_id.items():
                markers = markers_by_id[fid]
                form_entry = dict(analysis)
                form_entry["markers"] = markers
                all_forms.append(form_entry)
                if markers:
                    marked_analyses.append(form_entry)
                else:
                    clean_analyses.append(analysis)

            status = _resolve_inspection_status(clean_analyses, marked_analyses)

            return LemmaInspection(
                lemma=lemma,
                status=status,
                clean_analyses=clean_analyses,
                marked_analyses=marked_analyses,
                forms=all_forms,
                effective_markers=sorted(effective_markers_set),
                source_locations=sorted(locations),
                source_version=version,
                pipeline_identity=meta,
            )
    except (FileNotFoundError, sqlite3.Error):
        return LemmaInspection(
            lemma=lemma,
            status=InspectionStatus.UNAVAILABLE,
            clean_analyses=[],
            marked_analyses=[],
            forms=[],
            effective_markers=[],
            source_locations=[],
            source_version="unavailable",
            pipeline_identity={},
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Query the VESUM morphological dictionary")
    parser.add_argument("--db", "-d", type=Path, default=None, help="Explicit path to VESUM SQLite database")
    subparsers = parser.add_subparsers(dest="command", required=True)

    word_parser = subparsers.add_parser("word", help="Verify a Ukrainian word form (compatibility view)")
    word_parser.add_argument("query", help="Word form to check")
    word_parser.add_argument("--pos", type=str, help="Filter by POS, e.g. noun, verb, adj")
    word_parser.add_argument("--json", action="store_true", help="Print raw JSON")
    word_parser.add_argument("--db", "-d", type=Path, default=argparse.SUPPRESS, help="Explicit path to VESUM SQLite database")

    words_parser = subparsers.add_parser("words", help="Batch-verify Ukrainian word forms (compatibility view)")
    words_parser.add_argument("query", nargs="+", help="Word forms to check")
    words_parser.add_argument("--pos", type=str, help="Filter by POS, e.g. noun, verb, adj")
    words_parser.add_argument("--json", action="store_true", help="Print raw JSON")
    words_parser.add_argument("--db", "-d", type=Path, default=argparse.SUPPRESS, help="Explicit path to VESUM SQLite database")

    lemma_parser = subparsers.add_parser("lemma", help="Get all forms of a lemma (compatibility view)")
    lemma_parser.add_argument("query", help="Lemma to look up")
    lemma_parser.add_argument("--json", action="store_true", help="Print raw JSON")
    lemma_parser.add_argument("--db", "-d", type=Path, default=argparse.SUPPRESS, help="Explicit path to VESUM SQLite database")

    inspect_word_parser = subparsers.add_parser(
        "inspect-word", help="Inspect a word form with full marker awareness"
    )
    inspect_word_parser.add_argument("query", help="Word form to inspect")
    inspect_word_parser.add_argument("--pos", type=str, help="Filter by POS, e.g. noun, verb, adj")
    inspect_word_parser.add_argument("--json", action="store_true", help="Print raw JSON")
    inspect_word_parser.add_argument("--db", "-d", type=Path, default=argparse.SUPPRESS, help="Explicit path to VESUM SQLite database")

    inspect_words_parser = subparsers.add_parser(
        "inspect-words", help="Batch inspect word forms with full marker awareness"
    )
    inspect_words_parser.add_argument("query", nargs="+", help="Word forms to inspect")
    inspect_words_parser.add_argument("--pos", type=str, help="Filter by POS, e.g. noun, verb, adj")
    inspect_words_parser.add_argument("--json", action="store_true", help="Print raw JSON")
    inspect_words_parser.add_argument("--db", "-d", type=Path, default=argparse.SUPPRESS, help="Explicit path to VESUM SQLite database")

    inspect_lemma_parser = subparsers.add_parser(
        "inspect-lemma", help="Inspect a lemma paradigm with full marker awareness"
    )
    inspect_lemma_parser.add_argument("query", help="Lemma to inspect")
    inspect_lemma_parser.add_argument("--json", action="store_true", help="Print raw JSON")
    inspect_lemma_parser.add_argument("--db", "-d", type=Path, default=argparse.SUPPRESS, help="Explicit path to VESUM SQLite database")

    args = parser.parse_args()
    db_path = getattr(args, "db", None)

    if args.command == "word":
        matches = verify_word(args.query, pos_filter=args.pos, db_path=db_path)
        if args.json:
            print(json.dumps(matches, ensure_ascii=False, indent=2))
        elif not matches:
            print(f"'{args.query}' not found in VESUM")
        else:
            print(f"'{args.query}' - {len(matches)} match(es):")
            for match in matches:
                print(f"  lemma={match['lemma']}  pos={match['pos']}  tags={match['tags']}")
    elif args.command == "words":
        results = verify_words(args.query, pos_filter=args.pos, db_path=db_path)
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            found = sum(1 for matches in results.values() if matches)
            print(f"Found: {found}/{len(args.query)}")
            for word in args.query:
                matches = results.get(word, [])
                status = "FOUND" if matches else "NOT FOUND"
                print(f"{word}: {status}")
    elif args.command == "lemma":
        forms = verify_lemma(args.query, db_path=db_path)
        if args.json:
            print(json.dumps(forms, ensure_ascii=False, indent=2))
        elif not forms:
            print(f"Lemma '{args.query}' not found in VESUM")
        else:
            print(f"'{args.query}' - {len(forms)} form(s):")
            for form in forms:
                print(f"  {form['word_form']:20s}  {form['tags']}")
    elif args.command == "inspect-word":
        res = inspect_word(args.query, pos_filter=args.pos, db_path=db_path)
        if args.json:
            print(json.dumps(res.as_dict(), ensure_ascii=False, indent=2))
        else:
            print(f"'{res.word}' - Status: {res.status.value}")
            print(f"  Effective markers: {', '.join(res.effective_markers) or 'none'}")
            print(f"  Clean analyses: {len(res.clean_analyses)}")
            for a in res.clean_analyses:
                print(f"    lemma={a['lemma']} pos={a['pos']} tags={a['tags']}")
            print(f"  Marked analyses: {len(res.marked_analyses)}")
            for a in res.marked_analyses:
                markers_str = ", ".join(m["marker"] for m in a.get("markers", []))
                print(f"    lemma={a['lemma']} pos={a['pos']} tags={a['tags']} [{markers_str}]")
    elif args.command == "inspect-words":
        batch_res = inspect_words(args.query, pos_filter=args.pos, db_path=db_path)
        if args.json:
            print(json.dumps({k: v.as_dict() for k, v in batch_res.items()}, ensure_ascii=False, indent=2))
        else:
            for word, res in batch_res.items():
                markers_str = f" [{', '.join(res.effective_markers)}]" if res.effective_markers else ""
                print(f"- {word}: {res.status.value}{markers_str} (clean={len(res.clean_analyses)}, marked={len(res.marked_analyses)})")
    elif args.command == "inspect-lemma":
        lemma_res = inspect_lemma(args.query, db_path=db_path)
        if args.json:
            print(json.dumps(lemma_res.as_dict(), ensure_ascii=False, indent=2))
        else:
            print(f"Lemma '{lemma_res.lemma}' - Status: {lemma_res.status.value}")
            print(f"  Total forms in paradigm: {len(lemma_res.forms)}")
            print(f"  Clean analyses: {len(lemma_res.clean_analyses)}, Marked analyses: {len(lemma_res.marked_analyses)}")
            print(f"  Effective markers: {', '.join(lemma_res.effective_markers) or 'none'}")


if __name__ == "__main__":
    main()
