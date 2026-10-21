"""The Postgres skip guard turns a silent skip into a red shard (#9062)."""

from pathlib import Path

from scripts.ci.pg_skip_guard import postgres_test_files as find_pg_files


def test_postgres_files_are_found_in_the_repo():
    found = find_pg_files(Path(__file__).resolve().parents[1])
    assert "tests/fleet_comms/test_pg_schema_ledger.py" in found
    assert "tests/fleet_comms/test_artifacts_pg_transactions.py" in found
