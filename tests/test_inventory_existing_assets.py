from __future__ import annotations

import json
import sqlite3
from copy import deepcopy
from pathlib import Path

import pytest

from scripts.projects.open_model_data import (
    inventory_existing_assets as inventory,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = (
    ROOT
    / "tests/fixtures/open_model_data/existing_asset_inventory_records.json"
)
SCHEMA = (
    ROOT
    / "data/projects/open_model_data/inventory/existing_asset_inventory_v1.schema.json"
)


def test_fixture_records_validate_and_keep_admission_closed() -> None:
    records = inventory.load_fixture_records(FIXTURE)
    schema, _ = inventory.load_schema(SCHEMA)

    inventory.validate_records(records, schema)

    assert all(
        record["eligibility"]["potential_training_admission"] is False
        for record in records
    )


def test_fixture_mode_is_byte_stable(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    common = [
        "--fixture-records",
        str(FIXTURE),
        "--schema",
        str(SCHEMA),
        "--repo-root",
        str(ROOT),
        "--snapshot-date",
        "2026-07-31",
    ]

    assert inventory.main([*common, "--output-dir", str(first)]) == 0
    assert inventory.main([*common, "--output-dir", str(second)]) == 0

    for name in (inventory.LEDGER_NAME, inventory.SUMMARY_NAME):
        assert (first / name).read_bytes() == (second / name).read_bytes()


def test_read_only_sqlite_connection_rejects_writes(tmp_path: Path) -> None:
    database = tmp_path / "fixture.db"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE evidence (value TEXT)")

    with inventory.connect_read_only(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM evidence").fetchone() == (0,)
        with pytest.raises(sqlite3.OperationalError):
            connection.execute("INSERT INTO evidence VALUES ('blocked')")


def test_overlap_views_are_excluded_from_distinct_totals() -> None:
    records = inventory.load_fixture_records(FIXTURE)
    overlap = deepcopy(records[0])
    overlap["asset_id"] = "fixture.overlap"
    overlap["measurement_scope"] = "overlap_view"
    records.append(overlap)

    summary = inventory.aggregate_summary(
        records,
        schema_sha256="0" * 64,
        ledger_sha256="1" * 64,
        snapshot_date="2026-07-31",
        repo_head="2" * 40,
    )

    human = summary["distinct_content_totals"]["by_origin_class"][
        "human_authored_source"
    ]
    assert human["lexical_words"] == 5
    assert human["content_units_by_unit_label"] == {"database_rows": 2}


def test_validation_rejects_training_admission_and_personal_paths() -> None:
    records = inventory.load_fixture_records(FIXTURE)
    schema, _ = inventory.load_schema(SCHEMA)
    unsafe = deepcopy(records[0])
    unsafe["eligibility"]["potential_training_admission"] = True
    unsafe["evidence_refs"] = ["/" + "Users/operator/private-source"]

    with pytest.raises(ValueError, match=r"inventory validation failed|absolute path"):
        inventory.validate_records([unsafe], schema)


def test_committed_summary_matches_ledger_hash() -> None:
    ledger = ROOT / "data/projects/open_model_data/inventory/recovery_ledger_v1.jsonl"
    summary_path = (
        ROOT / "data/projects/open_model_data/inventory/aggregate_summary_v1.json"
    )
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    assert summary["ledger_sha256"] == inventory.sha256_file(ledger)
    assert summary["safety_assertions"] == {
        "potential_training_admission_assets": 0,
        "redistribution_cleared_assets": 0,
        "source_record_v1_admissions": 0,
    }
