"""Acceptance coverage for #5646 metadata-only bottleneck alerts."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from agents_extensions.shared.session_streams import LeaseHolder, SessionStreamDatabase, SessionStreamStore
from scripts.ai_agent_bridge import _channels, _db, _inbox
from scripts.fleet_comms.bottleneck_alerts import scan_bottlenecks_at_inbox_checkpoint

NOW = datetime(2026, 7, 22, 12, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def isolate_broker(tmp_path: Path):
    broker_db = tmp_path / "messages.db"
    with patch("scripts.ai_agent_bridge._config.DB_PATH", broker_db), patch(
        "scripts.ai_agent_bridge._db.DB_PATH", broker_db
    ):
        _db.init_db()
        yield broker_db


def _metrics(*, age_s: float | None, threshold_s: int = 7_200, **_: object) -> dict[str, object]:
    return {
        "content_included": False,
        "threshold_seconds": {
            "dispatch": threshold_s,
            "formal_cf_publication": 3_600,
            "gate_to_merge": 3_600,
        },
        "by_stream_epic": {
            "4707": {
                "dispatch": {"backlog_age_s": age_s, "raw": {"unfinished_count": 1}},
            }
        },
        "source_errors": [],
    }


def _open_lease(path: Path, *, holder: str = "claude") -> None:
    store = SessionStreamStore(SessionStreamDatabase(path))
    store.open_session(
        stream_id="epic:4707",
        holder=LeaseHolder(
            agent=holder,
            harness="test",
            instance_id="instance-1",
            process_id=1,
            task_id="5646",
        ),
        lineage_id="test-lineage",
        ttl_seconds=3_600,
        now=NOW,
    )


def _alerts() -> list[dict[str, object]]:
    return _channels.read("fleet-comms", tail=20)


def test_duplicate_scan_posts_one_action_required_system_alert(tmp_path: Path) -> None:
    session_db = tmp_path / "streams.sqlite3"
    _open_lease(session_db)

    def collector(**kwargs: object) -> dict[str, object]:
        return _metrics(age_s=7_200, **kwargs)

    first = scan_bottlenecks_at_inbox_checkpoint(
        repo_root=tmp_path,
        now=NOW,
        session_db=session_db,
        rate_limit_seconds=0,
        metrics_collector=collector,
    )
    second = scan_bottlenecks_at_inbox_checkpoint(
        repo_root=tmp_path,
        now=NOW + timedelta(seconds=1),
        session_db=session_db,
        rate_limit_seconds=0,
        metrics_collector=collector,
    )

    assert first.alerts_posted == 1
    assert second.alerts_posted == 0
    messages = _alerts()
    assert len(messages) == 1
    assert messages[0]["kind"] == "system"
    assert messages[0]["priority"] == "action_required"
    conn = _db.get_db()
    try:
        recipients = {
            row["to_agent"]
            for row in conn.execute("SELECT to_agent FROM deliveries WHERE message_id = ?", (messages[0]["message_id"],))
        }
    finally:
        conn.close()
    assert recipients == {"claude", "claude-infra"}


def test_persistent_breach_rearms_at_next_threshold_multiple(tmp_path: Path) -> None:
    def collector(**kwargs: object) -> dict[str, object]:
        return _metrics(age_s=7_200, **kwargs)

    scan_bottlenecks_at_inbox_checkpoint(
        repo_root=tmp_path, now=NOW, rate_limit_seconds=0, metrics_collector=collector
    )
    rearmed = scan_bottlenecks_at_inbox_checkpoint(
        repo_root=tmp_path,
        now=NOW + timedelta(seconds=1),
        rate_limit_seconds=0,
        metrics_collector=lambda **kwargs: _metrics(age_s=14_400, **kwargs),
    )

    assert rearmed.alerts_posted == 1
    assert len(_alerts()) == 2


def test_clear_resets_alert_state_for_a_later_breach(tmp_path: Path) -> None:
    scan_bottlenecks_at_inbox_checkpoint(
        repo_root=tmp_path,
        now=NOW,
        rate_limit_seconds=0,
        metrics_collector=lambda **kwargs: _metrics(age_s=7_200, **kwargs),
    )
    cleared = scan_bottlenecks_at_inbox_checkpoint(
        repo_root=tmp_path,
        now=NOW + timedelta(seconds=1),
        rate_limit_seconds=0,
        metrics_collector=lambda **kwargs: _metrics(age_s=None, **kwargs),
    )
    again = scan_bottlenecks_at_inbox_checkpoint(
        repo_root=tmp_path,
        now=NOW + timedelta(seconds=2),
        rate_limit_seconds=0,
        metrics_collector=lambda **kwargs: _metrics(age_s=7_200, **kwargs),
    )

    assert cleared.cleared == 1
    assert again.alerts_posted == 1
    assert len(_alerts()) == 2


def test_no_or_stale_lease_escalates_to_claude_infra_only(tmp_path: Path) -> None:
    result = scan_bottlenecks_at_inbox_checkpoint(
        repo_root=tmp_path,
        now=NOW,
        session_db=tmp_path / "missing.sqlite3",
        rate_limit_seconds=0,
        metrics_collector=lambda **kwargs: _metrics(age_s=7_200, **kwargs),
    )

    assert result.alerts_posted == 1
    conn = _db.get_db()
    try:
        recipients = [row["to_agent"] for row in conn.execute("SELECT to_agent FROM deliveries")]
    finally:
        conn.close()
    assert recipients == ["claude-infra"]


def test_failed_delivery_is_loud_and_recorded_without_blocking_rescan(tmp_path: Path) -> None:
    def collector(**kwargs: object) -> dict[str, object]:
        return _metrics(age_s=7_200, **kwargs)

    scan_bottlenecks_at_inbox_checkpoint(
        repo_root=tmp_path, now=NOW, rate_limit_seconds=0, metrics_collector=collector
    )
    conn = _db.get_db()
    try:
        conn.execute("UPDATE deliveries SET status = 'failed', error = 'test transport failure'")
        conn.commit()
    finally:
        conn.close()

    result = scan_bottlenecks_at_inbox_checkpoint(
        repo_root=tmp_path,
        now=NOW + timedelta(seconds=1),
        rate_limit_seconds=0,
        metrics_collector=collector,
    )

    assert result.delivery_failures == 1
    conn = _db.get_db()
    try:
        state = conn.execute(
            "SELECT last_delivery_error, delivery_failure_reported FROM bottleneck_alert_state"
        ).fetchone()
    finally:
        conn.close()
    assert state["last_delivery_error"] == "test transport failure"
    assert state["delivery_failure_reported"] == 1


def test_inbox_drain_invokes_the_rate_limited_alert_checkpoint() -> None:
    with patch("scripts.fleet_comms.bottleneck_alerts.scan_bottlenecks_at_inbox_checkpoint") as scan:
        _inbox.run_inbox("claude", until_idle=False)

    scan.assert_called_once_with(repo_root=_inbox.REPO_ROOT)


def test_alert_state_and_messages_never_contain_collector_prompt_or_body(tmp_path: Path) -> None:
    payload = _metrics(age_s=7_200)
    payload["prompt"] = "PRIVATE PROMPT TEXT"
    payload["body"] = "PRIVATE MESSAGE BODY"
    scan_bottlenecks_at_inbox_checkpoint(
        repo_root=tmp_path,
        now=NOW,
        rate_limit_seconds=0,
        metrics_collector=lambda **kwargs: payload,
    )

    conn = _db.get_db()
    try:
        state = [dict(row) for row in conn.execute("SELECT * FROM bottleneck_alert_state")]
    finally:
        conn.close()
    serialized = json.dumps({"state": state, "messages": _alerts()}).lower()
    assert "private prompt" not in serialized
    assert "private message" not in serialized
    # The channel message necessarily has its own generated alert body, but
    # never reflects untrusted task/message payload fields from the collector.
    assert "inspect lifecycle metadata" in serialized
