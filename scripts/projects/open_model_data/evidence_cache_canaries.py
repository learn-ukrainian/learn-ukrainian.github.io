#!/usr/bin/env python3
"""Audit cache-only ULIF/slovnyk evidence adapters and parser canaries."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
SCHEMA = ROOT / "data/projects/open_model_data/contracts/correction_protection_adapter_receipt_v1.schema.json"
EXPECTED_ULIF_ENTRY_COLUMNS = (
    "id",
    "normalized_query",
    "canonical_headword",
    "raw_response_ref",
    "retrieved_at",
    "response_sha256",
    "parser_version",
    "status",
)
EXPECTED_ULIF_SECTION_COLUMNS = (
    "id",
    "entry_id",
    "kind",
    "source_order",
    "sense_or_group_id",
    "payload_json",
)
EXPECTED_SECTION_KINDS = frozenset({"antonyms", "paradigm", "phraseology", "synonyms"})
ALLOWED_ENTRY_STATUSES = frozenset({"ok", "not_found", "parse_error"})


class AdapterError(ValueError):
    """A cache or parser state is unsafe to consume."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AdapterError(message)


def table_columns(connection: sqlite3.Connection, table: str) -> tuple[str, ...]:
    return tuple(str(row[1]) for row in connection.execute(f"PRAGMA table_info({table})"))


def schema_hash(columns: tuple[str, ...]) -> str:
    return sha256_text(canonical_json(list(columns)))


def audit_database(database: Path, *, logical_path: str = "data/sources.db") -> dict[str, Any]:
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        tables = {
            str(row[0])
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        required = {"ulif_dictua_entries", "ulif_dictua_sections", "ulif_dictua_raw_responses"}
        require(required <= tables, "ULIF cache tables are unavailable")
        entry_columns = table_columns(connection, "ulif_dictua_entries")
        section_columns = table_columns(connection, "ulif_dictua_sections")
        require(entry_columns == EXPECTED_ULIF_ENTRY_COLUMNS, "ULIF entry table shape changed")
        require(section_columns == EXPECTED_ULIF_SECTION_COLUMNS, "ULIF section table shape changed")

        entries = list(connection.execute("SELECT * FROM ulif_dictua_entries ORDER BY id"))
        sections = list(connection.execute("SELECT * FROM ulif_dictua_sections ORDER BY entry_id, source_order, id"))
        statuses = Counter(str(row["status"]) for row in entries)
        require(set(statuses) <= ALLOWED_ENTRY_STATUSES, "unknown ULIF parser status")
        section_kinds = Counter(str(row["kind"]) for row in sections)
        require(set(section_kinds) <= EXPECTED_SECTION_KINDS, "unknown ULIF section kind")

        section_counts = Counter(int(row["entry_id"]) for row in sections)
        raw_verified = 0
        for row in entries:
            response_sha256 = str(row["response_sha256"])
            raw = connection.execute(
                "SELECT body FROM ulif_dictua_raw_responses WHERE response_sha256 = ?",
                (response_sha256,),
            ).fetchone()
            require(raw is not None, f"missing ULIF raw response: {response_sha256}")
            body = bytes(raw["body"])
            require(sha256_bytes(body) == response_sha256, f"ULIF raw response hash mismatch: {response_sha256}")
            require(str(row["raw_response_ref"]) == f"sha256:{response_sha256}", "ULIF raw response ref mismatch")
            raw_verified += 1
            status = str(row["status"])
            if status == "ok":
                require(bool(str(row["canonical_headword"])), "ULIF ok row lacks canonical headword")
                require(section_counts[int(row["id"])] > 0, "ULIF ok row lacks parsed sections")
            elif status == "not_found":
                require(section_counts[int(row["id"])] == 0, "ULIF not-found row has parsed sections")

        slovnyk_present = "slovnyk_me_entries" in tables
        if slovnyk_present:
            slovnyk_columns = set(table_columns(connection, "slovnyk_me_entries"))
            require({"dictionary_identity", "locator"} <= slovnyk_columns, "slovnyk cache lacks named dictionary identity")
            invalid = connection.execute(
                "SELECT COUNT(*) FROM slovnyk_me_entries WHERE dictionary_identity = '' OR locator NOT LIKE 'https://slovnyk.me/dict/%'"
            ).fetchone()[0]
            require(int(invalid) == 0, "slovnyk aggregator-only row cannot strengthen evidence")

        receipt = {
            "schema_version": "correction_protection_adapter_receipt_v1",
            "source_database": {
                "logical_path": logical_path,
                "bytes": database.stat().st_size,
                "sha256": sha256_file(database),
            },
            "network_lookups_performed": 0,
            "ulif_dictua": {
                "status": "bounded_cache",
                "entry_table_schema_sha256": schema_hash(entry_columns),
                "section_table_schema_sha256": schema_hash(section_columns),
                "entries": len(entries),
                "sections": len(sections),
                "by_status": dict(sorted(statuses.items())),
                "by_section_kind": dict(sorted(section_kinds.items())),
                "raw_response_hashes_verified": raw_verified,
                "parser_change_canaries": [
                    {"id": "ulif-entry-table-exact-shape", "passed": True, "failure_mode": "unknown column or removed field fails closed"},
                    {"id": "ulif-raw-response-hash", "passed": True, "failure_mode": "body/ref/hash mismatch fails closed"},
                    {"id": "ulif-status-and-section-consistency", "passed": True, "failure_mode": "unknown status/kind or inconsistent sections fail closed"},
                ],
            },
            "slovnyk_me": {
                "status": "bounded_cache" if slovnyk_present else "adapter_unavailable",
                "table_present": slovnyk_present,
                "named_dictionary_required": True,
                "aggregator_only_can_strengthen_disposition": False,
                "parser_change_canaries": [
                    {
                        "id": "slovnyk-named-dictionary-or-unavailable",
                        "passed": True,
                        "failure_mode": "missing dictionary identity or non-/dict/<slug>/ locator fails closed",
                    }
                ],
            },
            "safety": {
                "raw_payloads_published": False,
                "live_fallback": False,
                "human_gold": False,
                "authoritative": False,
            },
        }
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        errors = sorted(Draft202012Validator(schema).iter_errors(receipt), key=lambda error: list(error.path))
        require(not errors, f"adapter receipt schema violation: {errors[0].message if errors else ''}")
        return receipt
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--logical-database-path", default="data/sources.db")
    args = parser.parse_args()
    receipt = audit_database(args.database, logical_path=args.logical_database_path)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        dir=args.output.parent,
        prefix=f".{args.output.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        temporary = Path(handle.name)
        handle.write(canonical_json(receipt) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, args.output)


if __name__ == "__main__":
    main()
