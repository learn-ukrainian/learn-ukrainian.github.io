"""Mutation guards for the remote epic TTL/fencing store seam (#7178)."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from agents_extensions.shared.session_streams.db import SessionStreamDatabase
from agents_extensions.shared.session_streams.model import EntryType, LeaseHolder, utc_now
from agents_extensions.shared.session_streams.store import (
    ContentRejectedError,
    LeaseConflictError,
    SessionStreamStore,
)


def _store(tmp_path: Path) -> SessionStreamStore:
    return SessionStreamStore(SessionStreamDatabase(tmp_path / "remote.sqlite3"))


def _holder(agent: str, instance: str, host: str) -> LeaseHolder:
    return LeaseHolder(
        agent=agent,
        harness=f"{agent}-harness",
        instance_id=instance,
        process_id=1234,
        host_id=host,
    )


def test_claim_heartbeat_handoff_release_replay_conflict_and_fencing(tmp_path: Path) -> None:
    store = _store(tmp_path)
    first = _holder("codex", "first", "alpha")
    second = _holder("gemini", "second", "beta")
    now = utc_now()

    lease, outcome = store.claim_remote_session(
        stream_id="epic:7178",
        holder=first,
        lineage_id="lineage-first",
        ttl_seconds=30,
        session_id="session-first",
        lease_id="lease-first",
        now=now,
    )
    assert outcome == "claimed"
    replay, outcome = store.claim_remote_session(
        stream_id="epic:7178",
        holder=first,
        lineage_id="lineage-first",
        ttl_seconds=30,
        session_id="session-first",
        lease_id="lease-first",
        now=now + timedelta(seconds=1),
    )
    assert outcome == "replayed"
    assert replay == lease

    with pytest.raises(LeaseConflictError, match="live holder"):
        store.claim_remote_session(
            stream_id="epic:7178",
            holder=second,
            lineage_id="lineage-second",
            ttl_seconds=30,
            session_id="session-second",
            lease_id="lease-second",
            now=now + timedelta(seconds=2),
        )

    renewed = store.heartbeat(lease, now=now + timedelta(seconds=3))
    entry = store.append_entry(
        renewed,
        entry_type=EntryType.STATE,
        body="working",
        idempotency_key="state-1",
        now=now + timedelta(seconds=4),
    )
    assert entry.type is EntryType.STATE
    assert store.release_remote_session(renewed, now=now + timedelta(seconds=5)).value == "closed"
    assert store.release_remote_session(renewed, now=now + timedelta(seconds=6)).value == "closed"

    # A closed exact lease is fenced from a later claim, but clean release is idempotent.
    successor, outcome = store.claim_remote_session(
        stream_id="epic:7178",
        holder=second,
        lineage_id="lineage-second",
        ttl_seconds=30,
        session_id="session-second",
        lease_id="lease-second",
        now=now + timedelta(seconds=7),
    )
    assert outcome == "claimed"
    assert (successor.generation, successor.fencing_token) == (2, 2)
    with pytest.raises(LeaseConflictError):
        store.heartbeat(renewed, now=now + timedelta(seconds=8))
    with pytest.raises(LeaseConflictError):
        store.append_entry(
            renewed,
            entry_type=EntryType.NOTE,
            body="late",
            idempotency_key="late-note",
            now=now + timedelta(seconds=8),
        )
    with pytest.raises(LeaseConflictError):
        store.release_remote_session(renewed, now=now + timedelta(seconds=8))


def test_expired_claim_recovery_is_one_cas_receipt_and_old_lease_is_expired(tmp_path: Path) -> None:
    store = _store(tmp_path)
    now = utc_now()
    old, _ = store.claim_remote_session(
        stream_id="epic:7000",
        holder=_holder("codex", "old", "alpha"),
        lineage_id="old-lineage",
        ttl_seconds=5,
        session_id="old-session",
        lease_id="old-lease",
        now=now,
    )
    new, outcome = store.claim_remote_session(
        stream_id="epic:7000",
        holder=_holder("codex", "new", "beta"),
        lineage_id="new-lineage",
        ttl_seconds=5,
        session_id="new-session",
        lease_id="new-lease",
        now=now + timedelta(seconds=6),
    )
    assert outcome == "recovered"
    assert new.generation == old.generation + 1
    assert new.fencing_token == old.fencing_token + 1
    assert (
        store.session_state("epic:7000", "old-session").value == "expired"
    )  # allow-hardcoded-epic: synthetic expiry recovery stream fixture
    with store._read_snapshot() as connection:
        recovery = connection.execute(
            "SELECT proof_json FROM lease_events WHERE stream_id = ? AND event_type = 'recovered'",
            ("epic:7000",),
        ).fetchone()
    assert recovery is not None
    assert "old-session" in str(recovery["proof_json"])
    assert "new-session" in str(recovery["proof_json"])


def test_late_heartbeat_before_successor_revives_exact_lease(tmp_path: Path) -> None:
    store = _store(tmp_path)
    now = utc_now()
    lease, _ = store.claim_remote_session(
        stream_id="epic:7001",
        holder=_holder("codex", "late", "alpha"),
        lineage_id="late-lineage",
        ttl_seconds=5,
        session_id="late-session",
        lease_id="late-lease",
        now=now,
    )
    revived = store.heartbeat(lease, now=now + timedelta(seconds=6))
    assert revived.expires_at > lease.expires_at
    with pytest.raises(LeaseConflictError):
        store.claim_remote_session(
            stream_id="epic:7001",
            holder=_holder("gemini", "competitor", "beta"),
            lineage_id="competitor-lineage",
            ttl_seconds=5,
            session_id="competitor-session",
            lease_id="competitor-lease",
            now=now + timedelta(seconds=7),
        )


@pytest.mark.parametrize(
    "body",
    ["contact 10.0.0.7", "write /Users/alice/private.txt", "ssh atlas-runner", "connect example.com"],
)
def test_remote_entry_body_rejects_opsec_tokens(tmp_path: Path, body: str) -> None:
    store = _store(tmp_path)
    lease, _ = store.claim_remote_session(
        stream_id="epic:7002",
        holder=_holder("codex", "opsec", "alpha"),
        lineage_id="opsec-lineage",
        ttl_seconds=30,
        session_id="opsec-session",
        lease_id="opsec-lease",
    )
    with pytest.raises(ContentRejectedError):
        store.append_entry(lease, entry_type=EntryType.NOTE, body=body, idempotency_key="opsec")


def test_holder_host_is_part_of_the_fence(tmp_path: Path) -> None:
    store = _store(tmp_path)
    lease, _ = store.claim_remote_session(
        stream_id="epic:7003",
        holder=_holder("codex", "same", "alpha"),
        lineage_id="host-lineage",
        ttl_seconds=30,
        session_id="host-session",
        lease_id="host-lease",
    )
    forged = replace(lease, holder=replace(lease.holder, host_id="beta"))
    with pytest.raises(LeaseConflictError):
        store.heartbeat(forged)


def test_remote_claim_never_probes_holder_pid(tmp_path: Path) -> None:
    def forbidden_probe(_process_id: int) -> bool:
        raise AssertionError("remote claims must not probe holder PIDs")

    store = SessionStreamStore(SessionStreamDatabase(tmp_path / "remote.sqlite3"), _process_probe=forbidden_probe)
    lease, outcome = store.claim_remote_session(
        stream_id="epic:7004",
        holder=_holder("codex", "no-probe", "alpha"),
        lineage_id="no-probe-lineage",
        ttl_seconds=30,
        session_id="no-probe-session",
        lease_id="no-probe-lease",
    )
    assert outcome == "claimed"
    assert lease.holder.process_id == 1234
