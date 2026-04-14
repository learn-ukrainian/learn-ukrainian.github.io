from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime.result import Result
from ai_agent_bridge import _channels, _cli, _db, _inbox, _reconcile


@pytest.fixture(autouse=True)
def isolate_db(tmp_path):
    db_file = tmp_path / "messages.db"
    with patch("ai_agent_bridge._config.DB_PATH", db_file), patch(
        "ai_agent_bridge._db.DB_PATH", db_file
    ):
        _db.init_db()
        yield
def _run_cli(argv: list[str]) -> int:
    with patch.object(sys, "argv", ["ab", *argv]):
        try:
            _cli.main()
        except SystemExit as exc:
            return exc.code if isinstance(exc.code, int) else 0
    return 0
def _delivery_row(delivery_id: str):
    conn = _db.get_db()
    try:
        return conn.execute(
            """
            SELECT status, error, delivered_at
            FROM deliveries
            WHERE delivery_id = ?
            """,
            (delivery_id,),
        ).fetchone()
    finally:
        conn.close()
def _set_delivery(delivery_id: str, **fields: object) -> None:
    assignments = ", ".join(f"{name} = ?" for name in fields)
    conn = _db.get_db()
    try:
        conn.execute(
            f"UPDATE deliveries SET {assignments} WHERE delivery_id = ?",
            (*fields.values(), delivery_id),
        )
        conn.commit()
    finally:
        conn.close()
def _ok_result(agent: str) -> Result:
    return Result(
        ok=True,
        agent=agent,
        model="test-model",
        mode="read-only",
        response=f"{agent} reply",
        stderr_excerpt=None,
        duration_s=0.1,
        session_id=None,
        rate_limited=False,
        stalled=False,
        returncode=0,
        usage_record={},
    )
def test_reconcile_dry_run_prints_worker_disappeared_without_applying(capsys):
    _channels.create_channel("reviews")
    post = _channels.post("reviews", "user", "stuck", to_agents=["claude"], auto_snapshot=False)
    delivery_id = post["delivery_ids"][0]
    _set_delivery(
        delivery_id,
        status="processing",
        deadline_seconds=60,
        lease_until=(datetime.now(UTC) - timedelta(minutes=5)).isoformat(),
    )

    with patch("ai_agent_bridge._reconcile._has_active_worker", return_value=False):
        exit_code = _run_cli(["reconcile", "--dry-run"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "would reconcile: 1 deliveries" in captured.out
    assert delivery_id in captured.out
    assert "reconcile:worker-disappeared" in captured.out
    assert _delivery_row(delivery_id)["status"] == "processing"


def test_reconcile_applies_max_attempts_exceeded():
    _channels.create_channel("reviews")
    post = _channels.post("reviews", "user", "retry me", to_agents=["claude"], auto_snapshot=False)
    delivery_id = post["delivery_ids"][0]
    _set_delivery(
        delivery_id,
        attempt_count=_channels.DEFAULT_MAX_DELIVERY_ATTEMPTS,
        retry_after=(datetime.now(UTC) - timedelta(seconds=1)).isoformat(),
    )

    changes = _reconcile.reconcile_deliveries()

    assert changes == (
        _reconcile.ReconcileChange(
            delivery_id=delivery_id,
            from_status="pending",
            to_status="failed",
            error="reconcile:max-attempts-exceeded",
        ),
    )
    row = _delivery_row(delivery_id)
    assert row["status"] == "failed"
    assert row["error"] == "reconcile:max-attempts-exceeded"


def test_reconcile_marks_workspace_write_delivery_delivered_when_recovery_commit_found():
    _channels.create_channel("reviews")
    post = _channels.post(
        "reviews", "user", "recover me", to_agents=["codex"], auto_snapshot=False, mode="workspace-write"
    )
    delivery_id = post["delivery_ids"][0]
    _set_delivery(delivery_id, status="processing")

    with patch("ai_agent_bridge._reconcile._find_timeout_recovery_commit", return_value="abc123"):
        changes = _reconcile.reconcile_deliveries()

    assert changes[0].error == "reconcile:git-commit-found:abc123"
    row = _delivery_row(delivery_id)
    assert row["status"] == "delivered"
    assert row["error"] == "reconcile:git-commit-found:abc123"
    assert row["delivered_at"] is not None


@patch("ai_agent_bridge._inbox.runtime_invoke")
@patch("ai_agent_bridge._inbox.reconcile_deliveries")
def test_run_inbox_calls_reconcile_at_end(mock_reconcile, mock_invoke):
    _channels.create_channel("reviews")
    _channels.post("reviews", "user", "hello", to_agents=["claude"], auto_snapshot=False)
    mock_invoke.return_value = _ok_result("claude")

    summary = _inbox.run_inbox("claude", until_idle=False)

    assert summary.deliveries_delivered == 1
    mock_reconcile.assert_called_once_with()
