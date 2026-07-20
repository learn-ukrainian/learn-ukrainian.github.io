"""Sol PR-H inventory + import/projection receipts (#5512)."""

from __future__ import annotations

from pathlib import Path

import yaml

from agents_extensions.shared.session_streams.cli import main
from agents_extensions.shared.session_streams.db import SessionStreamDatabase, load_migrations
from agents_extensions.shared.session_streams.inventory import (
    inventory_snapshot,
    load_stream_epic_inventory,
    sorted_epic_numbers,
    stream_map,
)
from agents_extensions.shared.session_streams.receipts import (
    inventory_registration_summary,
    list_migration_state,
    record_projection_receipt,
    register_manifest_inventory,
)
from agents_extensions.shared.session_streams.store import SessionStreamStore


def _fixture_repo(tmp_path: Path) -> Path:
    """Write a multi-stream issue_streams.yaml under a fake repo root."""
    streams = {
        "schema_version": 1,
        "streams": {
            "alpha": {"title": "Alpha Stream", "epics": [1001, 1002]},
            "beta": {"title": "Beta Stream", "epics": [2001, 1002]},  # 1002 shared name only once in inventory
            "gamma": {"title": "Gamma Stream", "epics": [3001]},
        },
    }
    cfg = tmp_path / "scripts" / "config"
    cfg.mkdir(parents=True)
    (cfg / "issue_streams.yaml").write_text(yaml.safe_dump(streams), encoding="utf-8")
    # One existing handoff for alpha epic 1001 default path pattern.
    handoff = tmp_path / ".claude" / "alpha-epic" / "CLAUDE-DRIVER-HANDOFF.md"
    handoff.parent.mkdir(parents=True)
    handoff.write_text("# alpha handoff\n", encoding="utf-8")
    return tmp_path


def test_sorted_epics_and_stream_map_from_multi_stream_fixture(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    epics = sorted_epic_numbers(repo)
    assert epics == [1001, 1002, 2001, 3001]
    mapping = stream_map(repo)
    assert mapping == {
        "alpha": [1001, 1002],
        "beta": [1002, 2001],
        "gamma": [3001],
    }
    records = load_stream_epic_inventory(repo)
    # Dedup: epic 1002 kept under first stream (alpha)
    assert [r.epic_number for r in records] == [1001, 1002, 2001, 3001]
    assert {r.stream_id for r in records} == {
        "epic:1001",
        "epic:1002",
        "epic:2001",
        "epic:3001",
    }
    snap = inventory_snapshot(repo)
    assert snap["epic_count"] == 4
    assert snap["epics"] == [1001, 1002, 2001, 3001]
    assert snap["hard_coded_subset_authoritative"] is False
    assert snap["authority"] == "scripts/config/issue_streams.yaml"
    assert len(snap["source_sha256"]) == 64


def test_inventory_does_not_use_hard_coded_exclusive_list(tmp_path: Path) -> None:
    """Fixture epics are the sole authority — not the old four-epic production set."""
    repo = _fixture_repo(tmp_path)
    epics = set(sorted_epic_numbers(repo))
    # Classic four-epic subset from pre-PR-H dual-write code must not appear.
    hard_coded_four = {4387, 4707, 4542, 4706}
    assert epics.isdisjoint(hard_coded_four)
    assert epics == {1001, 1002, 2001, 3001}


def test_schema_applies_inventory_receipts_migration(tmp_path: Path) -> None:
    migrations = load_migrations()
    assert [m.version for m in migrations] == [1, 2]
    assert "inventory_receipts" in migrations[1].name
    db = SessionStreamDatabase(tmp_path / "streams.sqlite3")
    conn = db.connect()
    try:
        versions = [int(r[0]) for r in conn.execute("SELECT version FROM schema_migrations ORDER BY 1")]
        assert versions == [1, 2]
        for table in (
            "stream_migration_state",
            "stream_inventory_receipts",
            "legacy_import_receipts",
            "legacy_projection_receipts",
            "stream_control_events",
        ):
            row = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
                (table,),
            ).fetchone()
            assert row is not None, table
    finally:
        conn.close()


def test_register_manifest_inventory_writes_receipts(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    store = SessionStreamStore(SessionStreamDatabase(tmp_path / "streams.sqlite3"))
    result = register_manifest_inventory(store, repo)
    assert result.epic_count == 4
    assert set(result.registered_stream_ids) == {
        "epic:1001",
        "epic:1002",
        "epic:2001",
        "epic:3001",
    }
    assert result.new_inventory_receipts == 4
    assert result.import_receipts_written >= 4  # at least one candidate per epic
    assert all(mode == "inventory" for mode in result.modes.values())

    # Idempotent for same manifest hash
    again = register_manifest_inventory(store, repo)
    assert again.new_inventory_receipts == 0

    summary = inventory_registration_summary(store)
    assert summary["inventory_receipts"] == 4
    assert summary["import_receipts"] >= 4
    assert summary["modes"] == {"inventory": 4}
    assert "blocked" in summary["cutover"]

    states = list_migration_state(store)
    assert {s["stream_id"] for s in states} == set(result.registered_stream_ids)
    assert all(s["mode"] == "inventory" for s in states)

    # Existing handoff file recorded as inventoried
    with store._read_snapshot() as conn:
        inv_rows = conn.execute(
            "SELECT status, source_path FROM legacy_import_receipts WHERE stream_id = 'epic:1001'"
        ).fetchall()
        statuses = {str(r["status"]) for r in inv_rows}
        assert "inventoried" in statuses
        assert "missing" in statuses


def test_projection_receipt_records_drift(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    store = SessionStreamStore(SessionStreamDatabase(tmp_path / "streams.sqlite3"))
    register_manifest_inventory(store, repo)
    pid = record_projection_receipt(
        store,
        stream_id="epic:1001",
        target_path=".claude/alpha-epic/CLAUDE-DRIVER-HANDOFF.md",
        target_sha256="a" * 64,
        projection_body="projected body",
        status="drift",
        error="file hash diverged",
    )
    assert pid >= 1
    summary = inventory_registration_summary(store)
    assert summary["projection_receipts"] == 1
    with store._read_snapshot() as conn:
        events = conn.execute(
            "SELECT event_type FROM stream_control_events "
            "WHERE stream_id = 'epic:1001' AND event_type = 'drift_detected'"
        ).fetchall()
        assert len(events) == 1


def test_cli_inventory_json_and_register(tmp_path: Path, capsys) -> None:
    repo = _fixture_repo(tmp_path)
    db_path = tmp_path / "streams.sqlite3"
    # Read-only inventory (no register)
    code = main(
        [
            "--db",
            str(db_path),
            "inventory",
            "--repo-root",
            str(repo),
            "--format",
            "json",
        ]
    )
    assert code == 0
    out = capsys.readouterr().out
    assert '"epic_count": 4' in out
    assert "1001" in out and "3001" in out
    assert "hard_coded_subset_authoritative" in out

    code = main(
        [
            "--db",
            str(db_path),
            "inventory",
            "--repo-root",
            str(repo),
            "--register",
            "--format",
            "json",
        ]
    )
    assert code == 0
    out = capsys.readouterr().out
    assert "registration" in out
    assert "new_inventory_receipts" in out
    summary = inventory_registration_summary(SessionStreamStore(SessionStreamDatabase(db_path)))
    assert summary["inventory_receipts"] == 4
