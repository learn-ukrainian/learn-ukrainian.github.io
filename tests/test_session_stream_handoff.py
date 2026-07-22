"""Cross-agent epic-stream handoff status + claim (#5530)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from agents_extensions.shared.session_streams.db import SessionStreamDatabase
from agents_extensions.shared.session_streams.handoff import claim_stream, diagnose_handoff
from agents_extensions.shared.session_streams.model import LeaseHolder
from agents_extensions.shared.session_streams.store import SessionStreamStore

NOW = datetime(2026, 7, 20, 12, 0, tzinfo=UTC)


def _store(tmp_path: Path, process_state: dict[int, bool] | None = None) -> SessionStreamStore:
    state = process_state if process_state is not None else {}
    return SessionStreamStore(
        SessionStreamDatabase(tmp_path / "streams.sqlite3"),
        _process_probe=lambda process_id: state.get(process_id, False),
    )


def _holder(agent: str = "codex", pid: int = 1001, instance: str = "codex-inst-1") -> LeaseHolder:
    return LeaseHolder(
        agent=agent,
        harness="native_codex",
        instance_id=instance,
        process_id=pid,
        task_id=f"{agent}-task",
    )


def test_diagnose_empty_stream_is_claimable_open(tmp_path: Path) -> None:
    store = _store(tmp_path)
    # open once so stream exists, then close
    lease = store.open_session(
        stream_id="epic:4542",
        holder=_holder(),
        lineage_id="lineage-a",
        ttl_seconds=60,
        now=NOW,
    )
    store.close_session(lease, now=NOW + timedelta(seconds=1))
    status = diagnose_handoff(store, "epic:4542", now=NOW + timedelta(hours=1))
    assert status.session_id is None
    assert status.claimable_force_close is False
    assert "safe to open" in status.reason


def test_diagnose_expired_dead_holder_claimable(tmp_path: Path) -> None:
    state = {1001: True}
    store = _store(tmp_path, state)
    store.open_session(
        stream_id="epic:4542",
        holder=_holder(pid=1001),
        lineage_id="lineage-a",
        ttl_seconds=60,
        now=NOW,
    )
    # Simulate crash: process gone, time past TTL
    state[1001] = False
    status = diagnose_handoff(store, "epic:4542", now=NOW + timedelta(minutes=5))
    assert status.lease_expired is True
    assert status.holder_process_alive is False
    assert status.claimable_force_close is True


def test_diagnose_unexpired_dead_holder_claimable(tmp_path: Path) -> None:
    """Crash before TTL: dead PID must be reclaimable without waiting hours."""
    state = {1001: True}
    store = _store(tmp_path, state)
    store.open_session(
        stream_id="epic:4707",
        holder=_holder(pid=1001),
        lineage_id="lineage-a",
        ttl_seconds=6 * 3600,
        now=NOW,
    )
    state[1001] = False
    status = diagnose_handoff(store, "epic:4707", now=NOW + timedelta(seconds=30))
    assert status.lease_expired is False
    assert status.holder_process_alive is False
    assert status.claimable_force_close is True
    assert "dead holder" in status.reason


def test_claim_force_closes_and_opens(tmp_path: Path) -> None:
    state = {1001: True, 2002: True}
    store = _store(tmp_path, state)
    store.open_session(
        stream_id="epic:4542",
        holder=_holder(pid=1001, instance="codex-dead"),
        lineage_id="lineage-codex",
        ttl_seconds=60,
        now=NOW,
    )
    state[1001] = False
    receipt = claim_stream(
        store,
        stream_id="epic:4542",
        agent="claude",
        harness="claude-code",
        instance_id="claude-hramatka-1",
        process_id=2002,
        lineage_id="lineage-claude",
        ttl_seconds=3600,
        now=NOW + timedelta(minutes=5),
    )
    assert receipt["force_closed"] is not None
    assert receipt["lease"]["holder"]["agent"] == "claude"
    status = diagnose_handoff(store, "epic:4542", now=NOW + timedelta(minutes=6))
    assert status.holder_agent == "claude"
    assert status.claimable_force_close is False
    assert status.lease_expired is False


def test_claim_force_closes_unexpired_dead_holder(tmp_path: Path) -> None:
    state = {1001: True, 2002: True}
    store = _store(tmp_path, state)
    store.open_session(
        stream_id="epic:4707",
        holder=_holder(pid=1001, instance="grok-dead"),
        lineage_id="lineage-grok",
        ttl_seconds=6 * 3600,
        now=NOW,
    )
    state[1001] = False
    receipt = claim_stream(
        store,
        stream_id="epic:4707",
        agent="grok",
        harness="grok-tui",
        instance_id="grok-fresh",
        process_id=2002,
        lineage_id="lineage-grok-2",
        ttl_seconds=6 * 3600,
        now=NOW + timedelta(seconds=45),
    )
    assert receipt["force_closed"] is not None
    assert receipt["prior_status"]["lease_expired"] is False
    assert receipt["lease"]["holder"]["agent"] == "grok"


def test_claim_refuses_live_lease(tmp_path: Path) -> None:
    state = {1001: True, 2002: True}
    store = _store(tmp_path, state)
    store.open_session(
        stream_id="epic:4542",
        holder=_holder(pid=1001),
        lineage_id="lineage-codex",
        ttl_seconds=3600,
        now=NOW,
    )
    with pytest.raises(ValueError, match="cannot claim"):
        claim_stream(
            store,
            stream_id="epic:4542",
            agent="claude",
            harness="claude-code",
            instance_id="claude-1",
            process_id=2002,
            lineage_id="lineage-claude",
            now=NOW + timedelta(seconds=10),
        )
