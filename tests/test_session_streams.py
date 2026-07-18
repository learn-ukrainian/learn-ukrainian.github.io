from __future__ import annotations

import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Barrier, Event
from typing import Any

import pytest

from agents_extensions.shared.session_streams.db import MigrationError, SessionStreamDatabase, load_migrations
from agents_extensions.shared.session_streams.dual_write import ATLAS_HANDOFF_PATH, mirror_atlas_handoff
from agents_extensions.shared.session_streams.hooks import clean_exit_hook, heartbeat_hook
from agents_extensions.shared.session_streams.model import EntryRef, EntryType, LeaseHolder, SessionState
from agents_extensions.shared.session_streams.store import (
    ContentRejectedError,
    LeaseConflictError,
    LifecycleError,
    SessionStreamStore,
)

NOW = datetime(2026, 7, 18, 12, 0, tzinfo=UTC)


def _holder(
    *,
    harness: str = "codex",
    agent: str = "codex",
    instance: str = "runtime-1",
    process_id: int = 41001,
) -> LeaseHolder:
    return LeaseHolder(
        agent=agent,
        harness=harness,
        instance_id=instance,
        process_id=process_id,
        task_id=f"task-{instance}",
    )


def _store(tmp_path: Path, process_state: dict[int, bool] | None = None) -> SessionStreamStore:
    state = process_state if process_state is not None else {}
    return SessionStreamStore(
        SessionStreamDatabase(tmp_path / "streams.sqlite3"),
        _process_probe=lambda process_id: state.get(process_id, False),
    )


def _open(store: SessionStreamStore, *, holder: LeaseHolder | None = None, stream: str = "epic:4707"):
    return store.open_session(
        stream_id=stream,
        holder=holder or _holder(),
        lineage_id="lineage-test",
        ttl_seconds=30,
        session_id="session-one",
        lease_id="lease-one",
        now=NOW,
    )


def test_schema_migration_wal_and_fingerprint(tmp_path: Path) -> None:
    database = SessionStreamDatabase(tmp_path / "streams.sqlite3")
    connection = database.connect(now=NOW)
    try:
        migration = load_migrations()[0]
        receipt = connection.execute(
            "SELECT version, name, ddl_sha256 FROM schema_migrations"
        ).fetchone()
        assert str(connection.execute("PRAGMA journal_mode").fetchone()[0]).lower() == "wal"
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute("PRAGMA synchronous").fetchone()[0] == 2
        assert dict(receipt) == {
            "version": 1,
            "name": migration.name,
            "ddl_sha256": migration.sha256,
        }
    finally:
        connection.close()

    assert SessionStreamStore(database).audit() == {
        "integrity_check": "ok",
        "foreign_key_violations": [],
        "schema_versions": [1],
    }


def test_migration_fingerprint_drift_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "drift.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.execute(
            "CREATE TABLE schema_migrations("
            "version INTEGER PRIMARY KEY, name TEXT NOT NULL, ddl_sha256 TEXT NOT NULL, applied_at TEXT NOT NULL)"
        )
        connection.execute(
            "INSERT INTO schema_migrations VALUES (1, '0001_initial.sql', ?, '2026-07-18T12:00:00Z')",
            ("0" * 64,),
        )

    with pytest.raises(MigrationError, match="fingerprint mismatch"):
        SessionStreamDatabase(path).connect()


def test_concurrent_first_open_serializes_migration_and_session_contention(tmp_path: Path) -> None:
    database_path = tmp_path / "shared-empty.sqlite3"
    barrier = Barrier(8)

    def attempt(index: int) -> str:
        store = SessionStreamStore(
            SessionStreamDatabase(database_path),
            _process_probe=lambda _process_id: False,
        )
        barrier.wait(timeout=5)
        try:
            store.open_session(
                stream_id="epic:4707",
                holder=_holder(instance=f"runtime-{index}", process_id=45000 + index),
                lineage_id=f"lineage-{index}",
                ttl_seconds=30,
                session_id=f"session-{index}",
                lease_id=f"lease-{index}",
                now=NOW,
            )
        except LifecycleError:
            return "lifecycle-conflict"
        return "opened"

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(attempt, range(8)))

    assert results.count("opened") == 1
    assert results.count("lifecycle-conflict") == 7
    connection = SessionStreamDatabase(database_path).connect(read_only=True)
    try:
        assert connection.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0] == 1
    finally:
        connection.close()


def test_pinned_entries_precede_bounded_recent_tail(tmp_path: Path) -> None:
    store = _store(tmp_path)
    lease = _open(store)
    order = store.append_entry(
        lease,
        entry_type=EntryType.BINDING_ORDER,
        body="Operator order stays visible.",
        idempotency_key="order-1",
        refs=(EntryRef(kind="github", uri="https://github.com/example/issues/1"),),
        now=NOW + timedelta(seconds=1),
    )
    constraint = store.append_entry(
        lease,
        entry_type=EntryType.NEGATIVE_CONSTRAINT,
        body="Never mutate a closed session.",
        idempotency_key="constraint-1",
        now=NOW + timedelta(seconds=2),
    )
    notes = [
        store.append_entry(
            lease,
            entry_type=EntryType.NOTE,
            body=f"Recent note {index}",
            idempotency_key=f"note-{index}",
            now=NOW + timedelta(seconds=3 + index),
        )
        for index in range(5)
    ]

    digest = store.load_digest("epic:4707", limit=2)

    assert [entry.entry_id for entry in digest.pinned] == [order.entry_id, constraint.entry_id]
    assert [entry.entry_id for entry in digest.recent] == [notes[-2].entry_id, notes[-1].entry_id]
    assert digest.entries == digest.pinned + digest.recent
    assert len(digest.digest_sha256) == 64

    repeated = store.append_entry(
        lease,
        entry_type=EntryType.BINDING_ORDER,
        body="Operator order stays visible.",
        idempotency_key="order-1",
        refs=(EntryRef(kind="github", uri="https://github.com/example/issues/1"),),
        now=NOW + timedelta(seconds=20),
    )
    assert repeated.entry_id == order.entry_id
    with pytest.raises(LeaseConflictError, match="different immutable content"):
        store.append_entry(
            lease,
            entry_type=EntryType.BINDING_ORDER,
            body="Different body.",
            idempotency_key="order-1",
            now=NOW + timedelta(seconds=20),
        )


def test_digest_uses_one_wal_snapshot_during_concurrent_pinned_append(tmp_path: Path) -> None:
    database_path = tmp_path / "snapshot.sqlite3"
    write_store = SessionStreamStore(SessionStreamDatabase(database_path))
    lease = _open(write_store)
    note = write_store.append_entry(
        lease,
        entry_type=EntryType.NOTE,
        body="Existing snapshot note.",
        idempotency_key="snapshot-note",
        now=NOW + timedelta(seconds=1),
    )
    pinned_query_started = Event()
    writer_finished = Event()

    class InterleavingConnection:
        def __init__(self, inner: sqlite3.Connection) -> None:
            self.inner = inner
            self.interleaved = False

        def execute(self, sql: str, parameters: Any = ()):
            cursor = self.inner.execute(sql, parameters)
            if "FROM entries WHERE stream_id = ? AND type IN" in sql and not self.interleaved:
                self.interleaved = True
                pinned_query_started.set()
                if not writer_finished.wait(timeout=5):
                    raise RuntimeError("concurrent writer did not finish")
            return cursor

        def close(self) -> None:
            self.inner.close()

    class InterleavingDatabase(SessionStreamDatabase):
        def __init__(self, path: Path) -> None:
            super().__init__(path)
            self.wrap_next_read = True

        def connect(self, *, read_only: bool = False, now: datetime | None = None):
            connection = super().connect(read_only=read_only, now=now)
            if read_only and self.wrap_next_read:
                self.wrap_next_read = False
                return InterleavingConnection(connection)
            return connection

    def append_pinned() -> None:
        assert pinned_query_started.wait(timeout=5)
        write_store.append_entry(
            lease,
            entry_type=EntryType.BINDING_ORDER,
            body="Concurrent binding order.",
            idempotency_key="snapshot-order",
            now=NOW + timedelta(seconds=2),
        )
        writer_finished.set()

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(append_pinned)
        snapshot = SessionStreamStore(InterleavingDatabase(database_path)).load_digest(
            "epic:4707",
            limit=10,
        )
        future.result(timeout=5)

    assert snapshot.pinned == ()
    assert [entry.entry_id for entry in snapshot.recent] == [note.entry_id]
    assert snapshot.high_water_entry_id == note.entry_id
    refreshed = write_store.load_digest("epic:4707", limit=10)
    assert [entry.body for entry in refreshed.pinned] == ["Concurrent binding order."]
    assert refreshed.high_water_entry_id > snapshot.high_water_entry_id


@pytest.mark.parametrize(
    "body,rule",
    [
        ("contact test@example.com", "email-address"),
        ("api_key=secret-value-123", "credential-assignment"),
        ("\x00binary", "control-character"),
    ],
)
def test_append_rejects_sensitive_or_non_text_content(tmp_path: Path, body: str, rule: str) -> None:
    store = _store(tmp_path)
    lease = _open(store)
    with pytest.raises(ContentRejectedError, match=rule):
        store.append_entry(
            lease,
            entry_type=EntryType.NOTE,
            body=body,
            idempotency_key="rejected",
            now=NOW + timedelta(seconds=1),
        )


def test_ttl_heartbeat_and_expired_write_fencing(tmp_path: Path) -> None:
    store = _store(tmp_path)
    lease = _open(store)

    with pytest.raises(LeaseConflictError, match="TTL has expired"):
        store.append_entry(
            lease,
            entry_type=EntryType.STATE,
            body="Too late.",
            idempotency_key="late",
            now=NOW + timedelta(seconds=30),
        )

    renewed = store.heartbeat(lease, now=NOW + timedelta(seconds=31))
    assert renewed.expires_at == "2026-07-18T12:01:01Z"
    entry = store.append_entry(
        lease,
        entry_type=EntryType.STATE,
        body="Holder process revived its own exact lease.",
        idempotency_key="revived",
        now=NOW + timedelta(seconds=32),
    )
    assert entry.entry_id > 0


def test_valid_lease_untouchable_and_crash_force_close_opens_distinct_session(tmp_path: Path) -> None:
    process_state = {41001: True, 42002: True}
    store = _store(tmp_path, process_state)
    original = _open(store)
    candidate = _holder(harness="agy", agent="gemini", instance="runtime-2", process_id=42002)

    with pytest.raises(LifecycleError, match="already has live session"):
        store.open_session(
            stream_id="epic:4707",
            holder=candidate,
            lineage_id="lineage-successor",
            ttl_seconds=30,
            session_id="session-two",
            now=NOW + timedelta(seconds=1),
        )
    with pytest.raises(LeaseConflictError, match="untouchable"):
        store.force_close_expired_session(
            stream_id="epic:4707",
            session_id="session-one",
            candidate=candidate,
            now=NOW + timedelta(seconds=29),
        )
    with pytest.raises(LeaseConflictError, match="still live"):
        store.force_close_expired_session(
            stream_id="epic:4707",
            session_id="session-one",
            candidate=candidate,
            now=NOW + timedelta(seconds=31),
        )

    process_state[41001] = False
    proof = store.force_close_expired_session(
        stream_id="epic:4707",
        session_id="session-one",
        candidate=candidate,
        now=NOW + timedelta(seconds=31),
    )
    assert proof.heartbeat_age_seconds == 31
    assert proof.holder_process_id == 41001
    assert proof.candidate_instance_id == "runtime-2"
    with pytest.raises(LeaseConflictError):
        store.heartbeat(original, now=NOW + timedelta(seconds=32))
    with pytest.raises(LeaseConflictError):
        store.append_entry(
            original,
            entry_type=EntryType.NOTE,
            body="Old holder fenced.",
            idempotency_key="old-holder",
            now=NOW + timedelta(seconds=32),
        )

    successor = store.open_session(
        stream_id="epic:4707",
        holder=candidate,
        lineage_id="lineage-successor",
        ttl_seconds=30,
        session_id="session-two",
        lease_id="lease-two",
        now=NOW + timedelta(seconds=32),
    )
    assert successor.session_id != original.session_id
    assert successor.generation == original.generation + 1
    assert successor.fencing_token == original.fencing_token + 1
    history = store.dump_stream("epic:4707")
    assert [session["state"] for session in history["sessions"]] == ["closed", "open"]
    assert any(event["event_type"] == "stale_observed" for event in history["lease_events"])
    assert any(event["event_type"] == "force_closed" for event in history["lease_events"])


def test_open_rolling_closed_state_machine_and_sql_immutability(tmp_path: Path) -> None:
    store = _store(tmp_path)
    lease = _open(store)
    assert store.transition_session(
        lease,
        to_state=SessionState.ROLLING,
        reason="prepared exact rollover",
        now=NOW + timedelta(seconds=1),
    ) is SessionState.ROLLING
    assert heartbeat_hook(store, lease, now=NOW + timedelta(seconds=1)).state == "rolling"
    assert store.transition_session(
        lease,
        to_state=SessionState.OPEN,
        reason="same live run resumed",
        now=NOW + timedelta(seconds=2),
    ) is SessionState.OPEN
    entry = store.append_entry(
        lease,
        entry_type=EntryType.NEXT_ACTION,
        body="Close cleanly.",
        idempotency_key="before-close",
        now=NOW + timedelta(seconds=3),
    )
    assert store.close_session(lease, now=NOW + timedelta(seconds=4)) is SessionState.CLOSED
    assert store.close_session(lease, now=NOW + timedelta(seconds=5)) is SessionState.CLOSED
    successor = store.open_session(
        stream_id="epic:4707",
        holder=_holder(instance="successor", process_id=43003),
        lineage_id="lineage-successor",
        ttl_seconds=30,
        session_id="session-successor",
        lease_id="lease-successor",
        now=NOW + timedelta(seconds=6),
    )
    assert successor.session_id == "session-successor"
    assert store.close_session(lease, now=NOW + timedelta(seconds=7)) is SessionState.CLOSED

    connection = store.database.connect()
    try:
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("UPDATE entries SET body = 'rewritten' WHERE entry_id = ?", (entry.entry_id,))
        with pytest.raises(sqlite3.IntegrityError, match="terminal"):
            connection.execute("UPDATE sessions SET updated_at = ? WHERE session_id = ?", ("later", lease.session_id))
        with pytest.raises(sqlite3.IntegrityError, match="never deleted"):
            connection.execute("DELETE FROM sessions WHERE session_id = ?", (lease.session_id,))
    finally:
        connection.close()


@pytest.mark.parametrize(
    ("agent", "harness"),
    [
        ("claude", "claude-code"),
        ("codex", "codex"),
        ("grok", "grok"),
        ("gemini", "agy"),
        ("kimi", "kimi"),
        ("interim", "interim-driver"),
    ],
)
def test_fleet_harnesses_share_heartbeat_and_exit_contract(
    tmp_path: Path,
    agent: str,
    harness: str,
) -> None:
    store = _store(tmp_path)
    holder = _holder(agent=agent, harness=harness, instance=f"{harness}-instance", process_id=os.getpid())
    lease = _open(store, holder=holder)

    heartbeat = heartbeat_hook(store, lease, now=NOW + timedelta(seconds=1))
    closed = clean_exit_hook(store, lease, now=NOW + timedelta(seconds=2))

    assert heartbeat.action == "heartbeat"
    assert heartbeat.expires_at == "2026-07-18T12:00:31Z"
    assert closed.state == "closed"


def test_atlas_dual_write_mirrors_file_without_modifying_or_deleting_it(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    handoff = repo_root / ATLAS_HANDOFF_PATH
    handoff.parent.mkdir(parents=True)
    handoff.write_text("# Atlas handoff\n\nCurrent state.\n", encoding="utf-8")
    store = _store(tmp_path / "runtime")
    lease = _open(store, stream="epic:4700")

    first = mirror_atlas_handoff(
        store,
        lease,
        repo_root=repo_root,
        stream_id="epic:4700",
        now=NOW + timedelta(seconds=1),
    )
    repeated = mirror_atlas_handoff(
        store,
        lease,
        repo_root=repo_root,
        stream_id="epic:4700",
        now=NOW + timedelta(seconds=2),
    )

    assert handoff.read_text(encoding="utf-8") == "# Atlas handoff\n\nCurrent state.\n"
    assert first.entry.entry_id == repeated.entry.entry_id
    assert first.mirror_id == repeated.mirror_id
    assert handoff.exists()
    history = store.dump_stream("epic:4700")
    assert len(history["entries"]) == 1
    assert len(history["legacy_mirrors"]) == 1
    assert history["entries"][0]["refs"][0]["kind"] == "legacy_source"

    handoff.write_text("# Atlas handoff\n\nUpdated state.\n", encoding="utf-8")
    changed = mirror_atlas_handoff(
        store,
        lease,
        repo_root=repo_root,
        stream_id="epic:4700",
        now=NOW + timedelta(seconds=3),
    )
    assert changed.entry.entry_id != first.entry.entry_id
    assert len(store.dump_stream("epic:4700")["entries"]) == 2

    with pytest.raises(ValueError, match="must match"):
        mirror_atlas_handoff(
            store,
            lease,
            repo_root=repo_root,
            stream_id="epic:4220",
            now=NOW + timedelta(seconds=4),
        )

    store.close_session(lease, now=NOW + timedelta(seconds=5))
    with pytest.raises(LeaseConflictError, match="current active"):
        mirror_atlas_handoff(
            store,
            lease,
            repo_root=repo_root,
            stream_id="epic:4700",
            now=NOW + timedelta(seconds=6),
        )
