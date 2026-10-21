"""Tests for the routing-assignments recency window and zombie expiry (#7088).

Overdue ``reserved``/``running`` rows persist forever when no write-path
ledger activity happens; the read-only projection must present them as
terminal/stale instead of live routing, and report whether the loaded
window is actually recent.
"""

from __future__ import annotations

import sys
import types
from datetime import UTC, datetime, timedelta

import scripts.api.runtime_router as runtime_router

_NOW = datetime.now(UTC)


def _iso(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _decision_row(
    reservation_id: str,
    *,
    state: str,
    created_at: datetime,
    expires_at: datetime | None = None,
    failure_classification: str | None = None,
) -> dict:
    return {
        "reservation_id": reservation_id,
        "authority_key": f"key-{reservation_id}",
        "decision_id": f"decision-{reservation_id}",
        "event_type": "started" if state == "running" else state,
        "state": state,
        "created_at": _iso(created_at),
        "evidence": {},
        "requested": {"initiator": "dispatcher", "route_mode": "auto"},
        "resolved": {"route": "codex"},
        "quota": {"snapshot": {}},
        "retry": {},
        "replay": {},
        "lifecycle": {
            "status": state,
            "created_at": _iso(created_at),
            "expires_at": _iso(expires_at) if expires_at else None,
            "failure_classification": failure_classification,
        },
    }


def _stub_ledger(monkeypatch, rows: list[dict]) -> None:
    ledger = types.SimpleNamespace(list_routing_decisions=lambda **_kwargs: rows)
    monkeypatch.setitem(sys.modules, "scripts.fleet_comms.routing_reservations", ledger)
    monkeypatch.setattr(
        runtime_router,
        "_routing_plane_status",
        lambda *_args, **_kwargs: {"mode": "shadow", "enabled": True, "authority": "test", "cutover": "test"},
    )


def test_zombie_running_row_is_terminal_and_window_stale(monkeypatch):
    """A running row past its TTL is reported expired, not live (#7088)."""
    old = _NOW - timedelta(days=14)
    rows = [
        _decision_row("res-zombie", state="running", created_at=old, expires_at=old + timedelta(minutes=5)),
        _decision_row(
            "res-fresh",
            state="running",
            created_at=_NOW - timedelta(minutes=5),
            expires_at=_NOW + timedelta(minutes=30),
        ),
    ]
    _stub_ledger(monkeypatch, rows)

    result = runtime_router.list_routing_assignments()

    assert result["availability"] == "available"
    by_id = {item["source_authority_id"]: item for item in result["assignments"]}

    zombie = by_id["res-zombie"]
    assert zombie["current_state"] == "expired"
    assert zombie["reservation_state"] == "expired"
    assert zombie["terminal_status"] == "expired"
    assert zombie["failure_classification"] == "ttl_expired_orphan"
    assert zombie["zombie_expired"] is True

    fresh = by_id["res-fresh"]
    assert fresh["current_state"] == "running"
    assert "zombie_expired" not in fresh

    window = result["window"]
    assert window["stale"] is False  # res-fresh keeps the window recent
    assert result["as_of"]


def test_stale_window_reported_when_newest_event_is_old(monkeypatch):
    """A window whose newest event is older than 45 minutes is stale."""
    old = _NOW - timedelta(days=14)
    rows = [
        _decision_row(
            "res-zombie",
            state="reserved",
            created_at=old,
            expires_at=old + timedelta(minutes=5),
        )
    ]
    _stub_ledger(monkeypatch, rows)

    result = runtime_router.list_routing_assignments()

    (item,) = result["assignments"]
    assert item["current_state"] == "expired"
    assert item["zombie_expired"] is True
    window = result["window"]
    assert window["stale"] is True
    assert window["newest_at"] == _iso(old)
    assert window["oldest_at"] == _iso(old)


def test_zombie_expiry_preserves_recorded_failure(monkeypatch):
    """Observer-side expiry never overwrites a recorded failure classification."""
    old = _NOW - timedelta(days=2)
    rows = [
        _decision_row(
            "res-zombie",
            state="running",
            created_at=old,
            expires_at=old + timedelta(minutes=5),
            failure_classification="provider_unavailable",
        )
    ]
    _stub_ledger(monkeypatch, rows)

    (item,) = runtime_router.list_routing_assignments()["assignments"]

    assert item["current_state"] == "expired"
    assert item["failure_classification"] == "provider_unavailable"


def test_active_row_without_expiry_is_left_alone(monkeypatch):
    """Active rows lacking expires_at cannot be TTL-judged; they stay active."""
    rows = [
        _decision_row("res-no-ttl", state="running", created_at=_NOW - timedelta(days=14), expires_at=None)
    ]
    _stub_ledger(monkeypatch, rows)

    (item,) = runtime_router.list_routing_assignments()["assignments"]

    assert item["current_state"] == "running"
    assert "zombie_expired" not in item


def test_terminal_rows_untouched_and_empty_window(monkeypatch):
    """Complete/failed rows are never reclassified; empty history has no window."""
    old = _NOW - timedelta(days=14)
    rows = [_decision_row("res-done", state="complete", created_at=old, expires_at=old)]
    _stub_ledger(monkeypatch, rows)

    result = runtime_router.list_routing_assignments()
    (item,) = result["assignments"]
    assert item["current_state"] == "complete"
    assert "zombie_expired" not in item
    assert result["window"]["stale"] is True

    _stub_ledger(monkeypatch, [])
    empty = runtime_router.list_routing_assignments()
    assert empty["availability"] == "empty"
    assert empty["window"] is None
    assert empty["as_of"]
