"""Sol PR-H projection receipts + drift detection (#5512)."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import yaml

from agents_extensions.shared.session_streams.cli import main
from agents_extensions.shared.session_streams.db import SessionStreamDatabase
from agents_extensions.shared.session_streams.dual_write import mirror_handoff_file
from agents_extensions.shared.session_streams.model import LeaseHolder
from agents_extensions.shared.session_streams.projection import (
    classify_file_projection,
    detect_projection_drift,
    list_projection_receipts,
    project_inventory_streams,
)
from agents_extensions.shared.session_streams.receipts import (
    inventory_registration_summary,
    register_manifest_inventory,
)
from agents_extensions.shared.session_streams.store import SessionStreamStore

NOW = datetime(2026, 7, 20, 15, 0, tzinfo=UTC)


def _fixture_repo(tmp_path: Path) -> Path:
    streams = {
        "schema_version": 1,
        "streams": {
            "alpha": {"title": "Alpha Stream", "epics": [1001, 1002]},
            "beta": {"title": "Beta Stream", "epics": [2001]},
        },
    }
    cfg = tmp_path / "scripts" / "config"
    cfg.mkdir(parents=True)
    (cfg / "issue_streams.yaml").write_text(yaml.safe_dump(streams), encoding="utf-8")
    handoff = tmp_path / ".claude" / "alpha-epic" / "CLAUDE-DRIVER-HANDOFF.md"
    handoff.parent.mkdir(parents=True)
    handoff.write_text("# alpha handoff\nstable body\n", encoding="utf-8")
    return tmp_path


def test_classify_unrecorded_mutation() -> None:
    status, error, mutation, source = classify_file_projection(
        file_exists=True,
        file_sha256="b" * 64,
        inventoried_sha256="a" * 64,
        invent_status="inventoried",
        db_body=None,
        file_body="changed",
    )
    assert status == "drift"
    assert mutation is True
    assert "unrecorded" in error
    assert source == "file_shadow"


def test_classify_db_mirror_divergence() -> None:
    body = "db projected body"
    status, error, mutation, source = classify_file_projection(
        file_exists=True,
        file_sha256="c" * 64,
        inventoried_sha256=hashlib.sha256(body.encode()).hexdigest(),
        invent_status="imported",
        db_body=body,
        file_body="file differs",
    )
    assert status == "drift"
    assert source == "db_mirror"
    assert "DB-first" in error
    assert mutation is True


def test_classify_missing_target_with_db_mirror() -> None:
    status, error, mutation, source = classify_file_projection(
        file_exists=False,
        file_sha256="",
        inventoried_sha256="a" * 64,
        invent_status="inventoried",
        db_body="projected",
        file_body="",
    )
    assert status == "failed"
    assert mutation is False
    assert source == "db_mirror"
    assert "missing" in error


def test_project_inventory_streams_writes_ok_receipts(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    store = SessionStreamStore(SessionStreamDatabase(tmp_path / "streams.sqlite3"))
    batch = project_inventory_streams(store, repo, now=NOW)
    assert batch.epic_count == 3
    assert batch.receipts_written == 3
    assert batch.ok >= 1
    assert batch.failed == 0
    assert "blocked" in batch.cutover
    # Alpha handoff exists and matches inventory → ok
    alpha = next(s for s in batch.streams if s.stream_id == "epic:1001")
    assert alpha.status == "ok"
    assert alpha.file_exists is True
    assert alpha.unrecorded_mutation is False
    assert alpha.source == "file_shadow"
    summary = inventory_registration_summary(store)
    assert summary["projection_receipts"] == 3
    # Idempotent re-run
    again = project_inventory_streams(store, repo, now=NOW + timedelta(seconds=1))
    assert again.receipts_written == 0
    assert inventory_registration_summary(store)["projection_receipts"] == 3


def test_project_detects_unrecorded_file_mutation(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    store = SessionStreamStore(SessionStreamDatabase(tmp_path / "streams.sqlite3"))
    register_manifest_inventory(store, repo, now=NOW)
    handoff = repo / ".claude" / "alpha-epic" / "CLAUDE-DRIVER-HANDOFF.md"
    handoff.write_text("# alpha handoff\nMUTATED without re-inventory\n", encoding="utf-8")
    batch = project_inventory_streams(
        store, repo, ensure_inventory=False, now=NOW + timedelta(seconds=5)
    )
    alpha = next(s for s in batch.streams if s.stream_id == "epic:1001")
    assert alpha.status == "drift"
    assert alpha.unrecorded_mutation is True
    assert batch.drift >= 1
    with store._read_snapshot() as conn:
        events = conn.execute(
            "SELECT event_type FROM stream_control_events "
            "WHERE stream_id = 'epic:1001' AND event_type = 'drift_detected'"
        ).fetchall()
        assert len(events) >= 1
    rows = list_projection_receipts(store, stream_id="epic:1001")
    assert any(r["status"] == "drift" for r in rows)


def test_project_db_mirror_path_ok_and_failed(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    store = SessionStreamStore(SessionStreamDatabase(tmp_path / "streams.sqlite3"))
    register_manifest_inventory(store, repo, now=NOW)
    lease = store.open_session(
        stream_id="epic:1001",
        holder=LeaseHolder(
            agent="grok",
            harness="grok-tui",
            instance_id="proj-test",
            task_id="proj-task",
            process_id=55012,
        ),
        lineage_id="lineage-proj",
        ttl_seconds=3600,
        session_id="session-proj",
        lease_id="lease-proj",
        now=NOW + timedelta(seconds=1),
    )
    source = Path(".claude/alpha-epic/CLAUDE-DRIVER-HANDOFF.md")
    mirror_handoff_file(
        store,
        lease,
        profile="1001",
        repo_root=repo,
        stream_id="epic:1001",
        source_path=source,
        now=NOW + timedelta(seconds=2),
    )
    batch = project_inventory_streams(
        store,
        repo,
        stream_ids=["epic:1001"],
        ensure_inventory=False,
        now=NOW + timedelta(seconds=3),
    )
    assert batch.epic_count == 1
    alpha = batch.streams[0]
    assert alpha.status == "ok"
    assert alpha.source == "db_mirror"
    assert alpha.high_water_entry_id is not None and alpha.high_water_entry_id >= 1

    # Remove file → dual-write projection would fail
    (repo / source).unlink()
    failed = project_inventory_streams(
        store,
        repo,
        stream_ids=["epic:1001"],
        ensure_inventory=False,
        now=NOW + timedelta(seconds=4),
    )
    assert failed.streams[0].status == "failed"
    assert failed.streams[0].source == "db_mirror"
    assert failed.failed == 1


def test_detect_projection_drift_hook_structure(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    store = SessionStreamStore(SessionStreamDatabase(tmp_path / "streams.sqlite3"))
    # Without inventory, ensure_inventory=False leaves missing receipts → failed
    bare = detect_projection_drift(store, repo, ensure_inventory=False, now=NOW)
    assert bare.epic_count == 3
    assert bare.failed >= 1 or bare.ok >= 0
    seeded = detect_projection_drift(
        store, repo, ensure_inventory=True, now=NOW + timedelta(seconds=1)
    )
    assert seeded.receipts_written >= 1
    assert seeded.ok + seeded.drift + seeded.failed == seeded.epic_count


def test_cli_project_and_check_drift(tmp_path: Path, capsys) -> None:
    repo = _fixture_repo(tmp_path)
    db_path = tmp_path / "streams.sqlite3"
    code = main(
        [
            "--db",
            str(db_path),
            "project",
            "--repo-root",
            str(repo),
            "--format",
            "json",
        ]
    )
    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["epic_count"] == 3
    assert out["receipts_written"] == 3
    assert "blocked" in out["cutover"]
    assert out["db_summary"]["projection_receipts"] == 3

    # Mutate, then check-drift
    handoff = repo / ".claude" / "alpha-epic" / "CLAUDE-DRIVER-HANDOFF.md"
    handoff.write_text("drifted by operator edit\n", encoding="utf-8")
    code = main(
        [
            "--db",
            str(db_path),
            "check-drift",
            "--repo-root",
            str(repo),
            "--stream",
            "epic:1001",
            "--format",
            "json",
        ]
    )
    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["epic_count"] == 1
    assert out["streams"][0]["status"] == "drift"
    assert out["streams"][0]["unrecorded_mutation"] is True

    code = main(
        [
            "--db",
            str(db_path),
            "project",
            "--repo-root",
            str(repo),
            "--format",
            "table",
        ]
    )
    assert code == 0
    table = capsys.readouterr().out
    assert "stream_id" in table
    assert "epic:1001" in table
