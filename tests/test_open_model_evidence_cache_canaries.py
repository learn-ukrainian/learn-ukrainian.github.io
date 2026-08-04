"""Cache-only ULIF/slovnyk adapter canaries."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from scripts.projects.open_model_data import evidence_cache_canaries as canaries


def _database(path: Path, *, mutated_entry_shape: bool = False) -> Path:
    connection = sqlite3.connect(path)
    extra = ", unexpected TEXT" if mutated_entry_shape else ""
    connection.execute(
        "CREATE TABLE ulif_dictua_entries (id INTEGER PRIMARY KEY, normalized_query TEXT NOT NULL, canonical_headword TEXT NOT NULL DEFAULT '', raw_response_ref TEXT NOT NULL DEFAULT '', retrieved_at TEXT NOT NULL DEFAULT '', response_sha256 TEXT NOT NULL DEFAULT '', parser_version TEXT NOT NULL DEFAULT '', status TEXT NOT NULL" + extra + ")"
    )
    connection.execute(
        "CREATE TABLE ulif_dictua_sections (id INTEGER PRIMARY KEY, entry_id INTEGER NOT NULL, kind TEXT NOT NULL, source_order INTEGER NOT NULL, sense_or_group_id TEXT NOT NULL DEFAULT '', payload_json TEXT NOT NULL)"
    )
    connection.execute(
        "CREATE TABLE ulif_dictua_raw_responses (response_sha256 TEXT PRIMARY KEY, body BLOB NOT NULL, content_type TEXT NOT NULL DEFAULT 'text/html', stored_at TEXT NOT NULL DEFAULT '')"
    )
    body = b"<html><headword>robota</headword></html>"
    body_hash = canaries.sha256_bytes(body)
    columns = "normalized_query,canonical_headword,raw_response_ref,retrieved_at,response_sha256,parser_version,status"
    connection.execute(
        f"INSERT INTO ulif_dictua_entries({columns}) VALUES (?,?,?,?,?,?,?)",
        ("робота", "робота", f"sha256:{body_hash}", "fixture", body_hash, "fixture-v1", "ok"),
    )
    connection.execute(
        "INSERT INTO ulif_dictua_raw_responses(response_sha256,body) VALUES (?,?)",
        (body_hash, body),
    )
    connection.execute(
        "INSERT INTO ulif_dictua_sections(entry_id,kind,source_order,sense_or_group_id,payload_json) VALUES (1,'synonyms',0,'synonyms:1','{}')"
    )
    connection.commit()
    connection.close()
    return path


def test_cache_receipt_verifies_raw_hashes_and_unavailable_slovnyk(tmp_path: Path) -> None:
    receipt = canaries.audit_database(_database(tmp_path / "sources.db"), logical_path="fixture/sources.db")
    assert receipt["network_lookups_performed"] == 0
    assert receipt["ulif_dictua"]["raw_response_hashes_verified"] == 1
    assert receipt["ulif_dictua"]["by_status"] == {"ok": 1}
    assert receipt["slovnyk_me"] == {
        "status": "adapter_unavailable",
        "table_present": False,
        "named_dictionary_required": True,
        "aggregator_only_can_strengthen_disposition": False,
        "parser_change_canaries": [
            {
                "id": "slovnyk-named-dictionary-or-unavailable",
                "passed": True,
                "failure_mode": "missing dictionary identity or non-/dict/<slug>/ locator fails closed",
            }
        ],
    }


def test_parser_shape_mutation_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(canaries.AdapterError, match="entry table shape changed"):
        canaries.audit_database(_database(tmp_path / "mutated.db", mutated_entry_shape=True))


def test_raw_response_mutation_fails_closed(tmp_path: Path) -> None:
    database = _database(tmp_path / "mutated-raw.db")
    connection = sqlite3.connect(database)
    connection.execute("UPDATE ulif_dictua_raw_responses SET body = X'00'")
    connection.commit()
    connection.close()
    with pytest.raises(canaries.AdapterError, match="raw response hash mismatch"):
        canaries.audit_database(database)
