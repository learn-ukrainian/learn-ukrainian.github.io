"""Backup receipt status is visible in the Monitor health glance."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from scripts.api import main as api_main
from scripts.api.monitor_context import fixture_context


def test_backup_health_reports_failure_and_timestamp(tmp_path: Path) -> None:
    batch_state = tmp_path / "batch_state"
    receipt = batch_state / "backups" / "last-run.json"
    receipt.parent.mkdir(parents=True)
    now = datetime(2026, 9, 30, 9, tzinfo=UTC)
    assert api_main._backup_last_run_health(batch_state, now=now) == {"status": "unknown", "reason": "no_receipt"}
    receipt.write_text(json.dumps({"exit_status": 78, "finished_at_utc": "2026-09-29T03:36:00Z"}))
    assert api_main._backup_last_run_health(batch_state, now=now) == {
        "status": "failed", "exit_status": 78, "finished_at_utc": "2026-09-29T03:36:00Z"
    }
    fresh = (now - timedelta(hours=5)).isoformat().replace("+00:00", "Z")
    receipt.write_text(json.dumps({"exit_status": 0, "finished_at_utc": fresh}))
    assert api_main._backup_last_run_health(batch_state, now=now)["status"] == "ok"
    old = (now - timedelta(hours=29)).isoformat().replace("+00:00", "Z")
    receipt.write_text(json.dumps({"exit_status": 0, "finished_at_utc": old}))
    assert api_main._backup_last_run_health(batch_state, now=now)["status"] == "stale"
    receipt.write_text("not json")
    assert api_main._backup_last_run_health(batch_state, now=now)["status"] == "unknown"


def test_health_section_reads_context_batch_state(tmp_path: Path) -> None:
    ctx = fixture_context(tmp_path)
    receipt = ctx.roots.batch_state_dir / "backups" / "last-run.json"
    receipt.parent.mkdir(parents=True)
    receipt.write_text('{"exit_status":1,"finished_at_utc":"2026-09-29T03:36:00Z"}')
    assert api_main._collect_health_orient_data(ctx)["backup_last_run"] == {
        "status": "failed", "exit_status": 1, "finished_at_utc": "2026-09-29T03:36:00Z"
    }
