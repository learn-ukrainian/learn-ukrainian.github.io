#!/usr/bin/env python3
"""Reconcile the university denominator with the live sources database.

The receipt is intentionally text-free. It reports database identity and set
parity only; it cannot admit, quarantine, or assign linguistic authority to a
source.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "data/projects/open_model_data/contracts/phase3_university_reconciliation_v3.schema.json"
SCHEMA_VERSION = "phase3_university_reconciliation_v3"


class UniversityReconciliationError(ValueError):
    """The denominator, database, or generated receipt is invalid."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_value(value: Any) -> str:
    return sha256_bytes(canonical_json(value).encode("utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise UniversityReconciliationError(message)


def _display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return path.name


def _load_denominator(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise UniversityReconciliationError(f"cannot read university denominator: {path}") from exc
    _require(isinstance(value, dict), "university denominator must be a mapping")
    _require(value.get("schema_version") == "university_corpus_denominator_v1", "unexpected denominator schema")
    sources = value.get("sources")
    _require(isinstance(sources, list) and sources, "denominator sources are required")
    return value


def _expected_sources(denominator: Mapping[str, Any]) -> list[dict[str, Any]]:
    expected: list[dict[str, Any]] = []
    for source in denominator["sources"]:
        identity = source.get("database_identity") or {}
        required = {
            "source_id": source.get("source_id"),
            "source_file": identity.get("source_file"),
            "domain": source.get("domain"),
            "admission_state": source.get("admission_state"),
            "expected_rows": identity.get("inserted_rows"),
            "expected_linked_rows": identity.get("linked_rows"),
        }
        _require(
            all(value is not None and value != "" for value in required.values()),
            "denominator source lacks database identity",
        )
        _require(required["source_id"] == required["source_file"], "source_id and database source_file differ")
        _require(
            isinstance(required["expected_rows"], int) and isinstance(required["expected_linked_rows"], int),
            "expected row counts must be integers",
        )
        expected.append(required)
    expected.sort(key=lambda item: item["source_file"])
    _require(len({item["source_file"] for item in expected}) == len(expected), "duplicate denominator source_file")
    return expected


def _rejected_source_ids(denominator: Mapping[str, Any]) -> set[str]:
    return {
        item["source_id"]
        for item in denominator.get("rejected_candidates", [])
        if isinstance(item, dict) and item.get("source_id")
    }


def _table_names(connection: sqlite3.Connection) -> set[str]:
    return {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view')")}


def _observed_sources(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    query = """
        SELECT
            t.source_file,
            COUNT(*) AS observed_rows,
            SUM(
                CASE WHEN t.parent_section_id IS NOT NULL AND EXISTS (
                    SELECT 1 FROM textbook_sections s
                    WHERE s.section_id = t.parent_section_id AND s.source_file = t.source_file
                ) THEN 1 ELSE 0 END
            ) AS observed_linked_rows,
            SUM(CASE WHEN f.id IS NOT NULL THEN 1 ELSE 0 END) AS observed_fts_rows,
            COUNT(DISTINCT t.parent_section_id) AS observed_sections
        FROM textbooks t
        LEFT JOIN textbooks_fts_docsize f ON f.id = t.id
        WHERE t.grade = 'university'
        GROUP BY t.source_file
        ORDER BY t.source_file
    """
    return [
        {
            "source_file": row[0],
            "observed_rows": row[1],
            "observed_linked_rows": row[2],
            "observed_fts_rows": row[3],
            "observed_sections": row[4],
        }
        for row in connection.execute(query)
    ]


def _count_rows(connection: sqlite3.Connection, table: str) -> int:
    return int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def _foreign_key_failure_count(connection: sqlite3.Connection) -> int:
    return sum(1 for _ in connection.execute("PRAGMA foreign_key_check"))


def _source_status(expected: Mapping[str, Any], observed: Mapping[str, Any] | None) -> str:
    if observed is None:
        return "missing_from_database"
    if observed["observed_rows"] != expected["expected_rows"]:
        return "row_count_mismatch"
    if observed["observed_linked_rows"] != expected["expected_linked_rows"]:
        return "linked_row_mismatch"
    if observed["observed_fts_rows"] != expected["expected_rows"]:
        return "fts_row_mismatch"
    return "exact_count_link_fts_match"


def _validate_receipt(receipt: Mapping[str, Any]) -> None:
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UniversityReconciliationError(f"cannot read reconciliation schema: {SCHEMA_PATH}") from exc
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(receipt), key=lambda item: list(item.path))
    if errors:
        location = "/".join(str(part) for part in errors[0].path) or "receipt"
        raise UniversityReconciliationError(f"schema violation at {location}: {errors[0].message}")


def reconcile(*, denominator_path: Path, database_path: Path, as_of: str) -> dict[str, Any]:
    """Return a deterministic text-free source/database reconciliation."""
    _require(as_of.strip() != "", "as-of identity is required")
    denominator = _load_denominator(denominator_path)
    expected = _expected_sources(denominator)
    rejected_ids = _rejected_source_ids(denominator)
    _require(database_path.is_file(), f"sources database is missing: {database_path}")

    connection = sqlite3.connect(f"file:{database_path.resolve()}?mode=ro", uri=True)
    try:
        tables = _table_names(connection)
        required_tables = {
            "textbooks",
            "textbook_sections",
            "textbooks_fts",
            "textbooks_fts_docsize",
        }
        _require(required_tables <= tables, f"sources database lacks tables: {sorted(required_tables - tables)}")
        observed = _observed_sources(connection)
        integrity = str(connection.execute("PRAGMA integrity_check").fetchone()[0])
        foreign_key_failures = _foreign_key_failure_count(connection)
        database_counts = {
            "textbook_rows": _count_rows(connection, "textbooks"),
            "textbook_section_rows": _count_rows(connection, "textbook_sections"),
            # For an external-content FTS5 table, COUNT(*) on the virtual table
            # mirrors the content table even when the search index is empty.
            # The docsize shadow table has one row per actually indexed row.
            "textbook_fts_rows": _count_rows(connection, "textbooks_fts_docsize"),
            "university_rows": sum(item["observed_rows"] for item in observed),
            "university_sources": len(observed),
        }
    finally:
        connection.close()

    observed_by_source = {item["source_file"]: item for item in observed}
    expected_files = {item["source_file"] for item in expected}
    reconciled_sources: list[dict[str, Any]] = []
    for item in expected:
        found = observed_by_source.get(item["source_file"])
        reconciled = dict(item)
        reconciled.update(
            found
            or {
                "observed_rows": 0,
                "observed_linked_rows": 0,
                "observed_fts_rows": 0,
                "observed_sections": 0,
            }
        )
        reconciled["status"] = _source_status(item, found)
        reconciled_sources.append(reconciled)

    extras = [
        {
            **item,
            "denominator_status": "rejected_candidate" if item["source_file"] in rejected_ids else "unlisted",
        }
        for item in observed
        if item["source_file"] not in expected_files
    ]
    source_counts = {
        "expected_sources": len(expected),
        "expected_rows": sum(item["expected_rows"] for item in expected),
        "exact_match_sources": sum(item["status"] == "exact_count_link_fts_match" for item in reconciled_sources),
        "missing_sources": sum(item["status"] == "missing_from_database" for item in reconciled_sources),
        "mismatched_sources": sum(
            item["status"] not in {"exact_count_link_fts_match", "missing_from_database"} for item in reconciled_sources
        ),
        "extra_sources": len(extras),
        "extra_rows": sum(item["observed_rows"] for item in extras),
    }
    identity_reconciled = (
        source_counts["exact_match_sources"] == source_counts["expected_sources"]
        and not extras
        and integrity == "ok"
        and foreign_key_failures == 0
        and database_counts["textbook_rows"] == database_counts["textbook_fts_rows"]
    )
    blockers: list[str] = []
    if source_counts["missing_sources"]:
        blockers.append("denominator_sources_missing_from_database")
    if source_counts["mismatched_sources"]:
        blockers.append("denominator_source_count_link_or_fts_mismatch")
    if extras:
        blockers.append("database_contains_unlisted_or_rejected_university_sources")
    if integrity != "ok":
        blockers.append("database_integrity_check_failed")
    if foreign_key_failures:
        blockers.append("database_foreign_key_failures_present")
    if database_counts["textbook_rows"] != database_counts["textbook_fts_rows"]:
        blockers.append("database_textbook_fts_row_count_mismatch")
    blockers.append("university_content_fitness_and_gap_audit_requires_authorized_review_seats")

    receipt: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "as_of": as_of,
        "text_free": True,
        "authority_boundary": {
            "database_identity_only": True,
            "may_admit_or_quarantine_sources": False,
            "may_assign_linguistic_authority": False,
        },
        "inputs": {
            "denominator_path": _display_path(denominator_path),
            "denominator_sha256": sha256_file(denominator_path),
            "database_path": _display_path(database_path),
            "database_sha256": sha256_file(database_path),
        },
        "database": {
            **database_counts,
            "integrity_check": integrity,
            "foreign_key_failure_count": foreign_key_failures,
        },
        "source_counts": source_counts,
        "set_hashes": {
            "expected_source_files_sha256": sha256_value(sorted(expected_files)),
            "observed_university_source_files_sha256": sha256_value(sorted(observed_by_source)),
        },
        "expected_sources": reconciled_sources,
        "extra_database_sources": extras,
        "gates": {
            "database_identity_reconciled": identity_reconciled,
            "university_content_audit_complete": False,
            "proceed_to_source_freeze": False,
        },
        "status": "identity_reconciled_content_audit_pending"
        if identity_reconciled
        else "mismatch_requires_reconciliation",
        "blockers": blockers,
    }
    _validate_receipt(receipt)
    return receipt


def _write_receipt(path: Path, receipt: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--denominator", type=Path, required=True)
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(list(argv) if argv is not None else None)
    receipt = reconcile(denominator_path=args.denominator, database_path=args.db, as_of=args.as_of)
    if args.output:
        _write_receipt(args.output, receipt)
    else:
        print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if receipt["gates"]["database_identity_reconciled"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
