from __future__ import annotations

import hashlib
import os
import sqlite3
import subprocess
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from itertools import product
from pathlib import Path
from threading import Barrier, Event
from time import thread_time
from typing import Any

import pytest

from agents_extensions.shared.session_streams import store as store_module
from agents_extensions.shared.session_streams.app_lifecycle import VerifiedAppLifecycleProof, make_receipt
from agents_extensions.shared.session_streams.db import MigrationError, SessionStreamDatabase, load_migrations
from agents_extensions.shared.session_streams.dual_write import ATLAS_HANDOFF_PATH, mirror_atlas_handoff
from agents_extensions.shared.session_streams.hooks import clean_exit_hook, heartbeat_hook, lease_from_environment
from agents_extensions.shared.session_streams.model import (
    EntryRef,
    EntryType,
    HolderKind,
    LeaseHolder,
    SessionState,
    isoformat_z,
)
from agents_extensions.shared.session_streams.store import (
    _EMBEDDED_HOST_EXEMPT_FILENAMES,
    _EMBEDDED_HOST_SUFFIXES,
    _FILE_EXTENSIONS,
    _PUBLIC_SUFFIX_TLDS,
    _REPOSITORY_FILENAMES,
    _TLD_FILE_EXTENSIONS,
    MAX_ENTRY_BYTES,
    PUBLIC_SUFFIX_LIST_PATH,
    PUBLIC_SUFFIX_LIST_SHA256,
    ContentRejectedError,
    LeaseConflictError,
    LifecycleError,
    SessionStreamStore,
    _contains_hostname,
    _filename_contains_hostname,
    load_public_suffix_labels,
    validate_entry_body,
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


def _app_holder(task_id: str = "019fb7a7-5e56-7760-8f53-0980ec7f0d0b") -> LeaseHolder:
    return LeaseHolder(
        agent="codex",
        harness="codex-desktop",
        instance_id="desktop-runtime",
        task_id=task_id,
        process_id=None,
        holder_kind=HolderKind.APP_THREAD,
    )


def _app_proof(
    operation: str,
    holder: LeaseHolder,
    *,
    now: datetime = NOW,
    stream: str = "epic:4707",
    lease=None,
    state: str = "active",
    rollover_id: str | None = None,
    session_id: str | None = None,
    lease_id: str | None = None,
    generation: int | None = None,
    fencing_token: int | None = None,
):
    receipt = make_receipt(
        operation=operation,
        provider="codex-desktop",
        adapter_version="test-v1",
        holder=holder,
        state=state,
        observed_at=isoformat_z(now),
        valid_until=isoformat_z(now + timedelta(seconds=20)),
        source_schema_digest="a" * 64,
        source_authority="test-native-readback",
        readback_digest="b" * 64,
        stream_id=stream,
        session_id=lease.session_id if lease else session_id,
        lease_id=lease.lease_id if lease else lease_id,
        generation=lease.generation if lease else generation,
        fencing_token=lease.fencing_token if lease else fencing_token,
        rollover_id=rollover_id,
    )
    return VerifiedAppLifecycleProof(receipt=receipt, verifier_id="test-adapter")


def test_schema_migration_wal_and_fingerprint(tmp_path: Path) -> None:
    database = SessionStreamDatabase(tmp_path / "streams.sqlite3")
    connection = database.connect(now=NOW)
    try:
        migrations = load_migrations()
        migration = migrations[0]
        receipt = connection.execute(
            "SELECT version, name, ddl_sha256 FROM schema_migrations WHERE version = 1"
        ).fetchone()
        versions = [
            int(row[0])
            for row in connection.execute("SELECT version FROM schema_migrations ORDER BY version").fetchall()
        ]
        assert versions == [m.version for m in migrations]
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
        "schema_versions": [m.version for m in load_migrations()],
    }


def test_app_thread_requires_verified_fresh_exact_proofs_and_can_renew_after_expiry(tmp_path: Path) -> None:
    store = _store(tmp_path)
    holder = _app_holder()
    with pytest.raises(LeaseConflictError, match="verified fresh"):
        store.open_session(stream_id="epic:4707", holder=holder, lineage_id="lineage-app", ttl_seconds=10, now=NOW)
    lease = store.open_session(
        stream_id="epic:4707",
        holder=holder,
        lineage_id="lineage-app",
        ttl_seconds=10,
        session_id="session-app",
        lease_id="lease-app",
        now=NOW,
        app_proof=_app_proof(
            "acquire", holder, session_id="session-app", lease_id="lease-app", generation=1, fencing_token=1
        ),
    )
    repeated = store.open_session(
        stream_id="epic:4707",
        holder=holder,
        lineage_id="lineage-app",
        ttl_seconds=10,
        session_id="session-app",
        lease_id="lease-app",
        now=NOW,
        app_proof=_app_proof(
            "acquire", holder, session_id="session-app", lease_id="lease-app", generation=1, fencing_token=1
        ),
    )
    assert repeated == lease
    with pytest.raises(LeaseConflictError, match="requires a verified"):
        store.append_entry(
            lease, entry_type=EntryType.NOTE, body="No unproven GUI writes.", idempotency_key="app-1", now=NOW
        )
    expired = NOW + timedelta(seconds=11)
    with pytest.raises(LeaseConflictError, match="TTL has expired"):
        store.append_entry(
            lease,
            entry_type=EntryType.NOTE,
            body="Expired holder cannot append.",
            idempotency_key="app-2",
            now=expired,
            app_proof=_app_proof("append", holder, lease=lease, now=expired),
        )
    renewed = store.heartbeat(lease, now=expired, app_proof=_app_proof("renew", holder, lease=lease, now=expired))
    entry = store.append_entry(
        renewed,
        entry_type=EntryType.NOTE,
        body="Renewed GUI holder can append.",
        idempotency_key="app-3",
        now=expired + timedelta(seconds=1),
        app_proof=_app_proof("append", holder, lease=renewed, now=expired + timedelta(seconds=1)),
    ).entry
    assert entry.body == "Renewed GUI holder can append."


def test_app_recovery_requires_terminal_predecessor_and_exact_rollover(tmp_path: Path) -> None:
    store = _store(tmp_path)
    predecessor = _app_holder()
    lease = store.open_session(
        stream_id="epic:4707",
        holder=predecessor,
        lineage_id="lineage-app",
        ttl_seconds=10,
        session_id="session-app",
        lease_id="lease-app",
        now=NOW,
        app_proof=_app_proof(
            "acquire", predecessor, session_id="session-app", lease_id="lease-app", generation=1, fencing_token=1
        ),
    )
    successor = _app_holder("119fb7a7-5e56-7760-8f53-0980ec7f0d0b")
    rollover = "rollover-c88026bc03f24420976fbf17c9cda05a"
    predecessor_proof = _app_proof("recover", predecessor, lease=lease, state="terminal", rollover_id=rollover)
    successor_proof = _app_proof(
        "recover",
        successor,
        rollover_id=rollover,
        session_id="session-next",
        lease_id="lease-next",
        generation=2,
        fencing_token=2,
    )
    with pytest.raises(LeaseConflictError, match="rollover continuity"):
        store.recover_app_session(
            lease,
            successor=successor,
            lineage_id="lineage-next",
            ttl_seconds=10,
            rollover_id=rollover,
            predecessor_proof=predecessor_proof,
            successor_proof=_app_proof(
                "recover",
                successor,
                rollover_id="rollover-wrong",
                session_id="session-next",
                lease_id="lease-next",
                generation=2,
                fencing_token=2,
            ),
            session_id="session-next",
            lease_id="lease-next",
            now=NOW + timedelta(seconds=1),
        )
    recovered = store.recover_app_session(
        lease,
        successor=successor,
        lineage_id="lineage-next",
        ttl_seconds=10,
        rollover_id=rollover,
        predecessor_proof=predecessor_proof,
        successor_proof=successor_proof,
        session_id="session-next",
        lease_id="lease-next",
        now=NOW + timedelta(seconds=1),
    )
    assert (recovered.generation, recovered.fencing_token) == (2, 2)
    assert (
        store.recover_app_session(
            lease,
            successor=successor,
            lineage_id="lineage-next",
            ttl_seconds=10,
            rollover_id=rollover,
            predecessor_proof=predecessor_proof,
            successor_proof=successor_proof,
            session_id="session-next",
            lease_id="lease-next",
            now=NOW + timedelta(seconds=1),
        )
        == recovered
    )
    with pytest.raises(LeaseConflictError):
        store.append_entry(
            lease,
            entry_type=EntryType.NOTE,
            body="Stale predecessor.",
            idempotency_key="stale-app",
            now=NOW + timedelta(seconds=2),
            app_proof=_app_proof("append", predecessor, lease=lease, now=NOW + timedelta(seconds=2)),
        )


def test_app_thread_mixed_holder_contention_and_hook_identity_without_pid(tmp_path: Path) -> None:
    process_holder = _holder(instance="process", process_id=42001)
    app_holder = _app_holder()

    process_store = _store(tmp_path / "process-first")
    _open(process_store, holder=process_holder)
    with pytest.raises(LifecycleError, match="already has live session"):
        process_store.open_session(
            stream_id="epic:4707",
            holder=app_holder,
            lineage_id="lineage-app",
            ttl_seconds=10,
            session_id="session-app",
            lease_id="lease-app",
            now=NOW,
            app_proof=_app_proof(
                "acquire",
                app_holder,
                session_id="session-app",
                lease_id="lease-app",
                generation=2,
                fencing_token=2,
            ),
        )

    app_store = _store(tmp_path / "app-first")
    app_store.open_session(
        stream_id="epic:4707",
        holder=app_holder,
        lineage_id="lineage-app",
        ttl_seconds=10,
        session_id="session-app",
        lease_id="lease-app",
        now=NOW,
        app_proof=_app_proof(
            "acquire", app_holder, session_id="session-app", lease_id="lease-app", generation=1, fencing_token=1
        ),
    )
    with pytest.raises(LifecycleError, match="already has live session"):
        app_store.open_session(
            stream_id="epic:4707",
            holder=process_holder,
            lineage_id="lineage-process",
            ttl_seconds=10,
            session_id="session-process",
            lease_id="lease-process",
            now=NOW,
        )
    second_app = _app_holder("119fb7a7-5e56-7760-8f53-0980ec7f0d0b")
    with pytest.raises(LifecycleError, match="already has live session"):
        app_store.open_session(
            stream_id="epic:4707",
            holder=second_app,
            lineage_id="lineage-second",
            ttl_seconds=10,
            session_id="session-second",
            lease_id="lease-second",
            now=NOW,
            app_proof=_app_proof(
                "acquire",
                second_app,
                session_id="session-second",
                lease_id="lease-second",
                generation=2,
                fencing_token=2,
            ),
        )

    hook_lease = lease_from_environment(
        {
            "SESSION_STREAM_ID": "epic:4707",
            "SESSION_STREAM_SESSION_ID": "session-app",
            "SESSION_STREAM_LEASE_ID": "lease-app",
            "SESSION_STREAM_GENERATION": "1",
            "SESSION_STREAM_FENCING_TOKEN": "1",
            "SESSION_STREAM_AGENT": "codex",
            "SESSION_STREAM_HARNESS": "codex-desktop",
            "SESSION_STREAM_INSTANCE_ID": "desktop-runtime",
            "SESSION_STREAM_TASK_ID": app_holder.task_id or "",
            "SESSION_STREAM_HOLDER_KIND": "app_thread",
            "SESSION_STREAM_HEARTBEAT_AT": isoformat_z(NOW),
            "SESSION_STREAM_EXPIRES_AT": isoformat_z(NOW + timedelta(seconds=10)),
            "SESSION_STREAM_TTL_SECONDS": "10",
            "SESSION_STREAM_VERSION": "1",
        }
    )
    assert hook_lease.holder == app_holder
    hook_result = heartbeat_hook(
        app_store,
        hook_lease,
        now=NOW + timedelta(seconds=1),
        app_proof=_app_proof("renew", app_holder, lease=hook_lease, now=NOW + timedelta(seconds=1)),
    )
    assert hook_result.action == "heartbeat"
    assert hook_result.state == "open"


def test_concurrent_app_renew_and_recover_remain_fenced_to_one_final_holder(tmp_path: Path) -> None:
    store = _store(tmp_path)
    predecessor = _app_holder()
    lease = store.open_session(
        stream_id="epic:4707",
        holder=predecessor,
        lineage_id="lineage-app",
        ttl_seconds=10,
        session_id="session-app",
        lease_id="lease-app",
        now=NOW,
        app_proof=_app_proof(
            "acquire", predecessor, session_id="session-app", lease_id="lease-app", generation=1, fencing_token=1
        ),
    )
    successor = _app_holder("119fb7a7-5e56-7760-8f53-0980ec7f0d0b")
    rollover = "rollover-concurrent"
    barrier = Barrier(2)

    def renew() -> str:
        barrier.wait(timeout=5)
        try:
            store.heartbeat(
                lease,
                now=NOW + timedelta(seconds=1),
                app_proof=_app_proof("renew", predecessor, lease=lease, now=NOW + timedelta(seconds=1)),
            )
        except LeaseConflictError:
            return "fenced"
        return "renewed"

    def recover() -> str:
        barrier.wait(timeout=5)
        store.recover_app_session(
            lease,
            successor=successor,
            lineage_id="lineage-next",
            ttl_seconds=10,
            rollover_id=rollover,
            predecessor_proof=_app_proof(
                "recover",
                predecessor,
                lease=lease,
                state="terminal",
                rollover_id=rollover,
                now=NOW + timedelta(seconds=1),
            ),
            successor_proof=_app_proof(
                "recover",
                successor,
                rollover_id=rollover,
                session_id="session-next",
                lease_id="lease-next",
                generation=2,
                fencing_token=2,
                now=NOW + timedelta(seconds=1),
            ),
            session_id="session-next",
            lease_id="lease-next",
            now=NOW + timedelta(seconds=1),
        )
        return "recovered"

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = {executor.submit(renew), executor.submit(recover)}
        outcomes = {future.result() for future in results}

    assert "recovered" in outcomes
    projection = store.lease_projection("epic:4707")
    assert projection is not None
    assert projection[1] == "active"
    assert projection[0].holder == successor
    assert (projection[0].generation, projection[0].fencing_token) == (2, 2)


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
        assert connection.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0] == len(load_migrations())
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
    assert order.is_replay is False
    order_entry = order.entry
    constraint = store.append_entry(
        lease,
        entry_type=EntryType.NEGATIVE_CONSTRAINT,
        body="Never mutate a closed session.",
        idempotency_key="constraint-1",
        now=NOW + timedelta(seconds=2),
    ).entry
    notes = [
        store.append_entry(
            lease,
            entry_type=EntryType.NOTE,
            body=f"Recent note {index}",
            idempotency_key=f"note-{index}",
            now=NOW + timedelta(seconds=3 + index),
        ).entry
        for index in range(5)
    ]

    digest = store.load_digest("epic:4707", limit=2)

    assert [entry.entry_id for entry in digest.pinned] == [order_entry.entry_id, constraint.entry_id]
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
    assert repeated.is_replay is True
    assert repeated.entry.entry_id == order_entry.entry_id
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
    ).entry
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


@pytest.mark.parametrize(
    "filename",
    [
        "sources.db",
        "vesum.db",
        "core.md",
        "a1.yaml",
        "lexicon-manifest.json",
        "mcp-sources-requests.jsonl",
        "scripts/store.py",
        r"scripts\core.md",
        r"scripts\store.py",
        r"scripts\x.sh",
        r"C:\scripts\core.md",
        r"D:\x\server.sh",
        r"scripts\server.sh",
        r"scripts\docs.rs",
        r"scripts\fileserver.md",
        r"\\?\C:\scripts\core.md",
        r"\\.\D:\x\server.sh",
        r"\??\C:\scripts\store.py",
        r"\\host\server.sh",
        r"\\.\server.sh",
        r"scripts\UNC\server.sh",
        "scripts/x.sh",
        "scripts/.hidden.py",
        "README.md",
        "store.py",
    ],
)
def test_append_accepts_repository_filenames(tmp_path: Path, filename: str) -> None:
    store = _store(tmp_path)
    lease = _open(store)
    body = f"Updated `{filename}`."
    entry = store.append_entry(
        lease, entry_type=EntryType.NOTE, body=body, idempotency_key="filename", now=NOW + timedelta(seconds=1)
    ).entry
    assert entry.body == body
    assert store.dump_stream(lease.stream_id)["entries"][0]["body"] == body


@pytest.mark.parametrize(
    "extension",
    [
        "py",
        "md",
        "db",
        "yaml",
        "yml",
        "json",
        "sh",
        "txt",
        "toml",
        "js",
        "ts",
        "tsx",
        "css",
        "html",
        "csv",
        "jsonl",
        "lock",
        "cfg",
        "ini",
        "rs",
        "go",
        "mjs",
        "cjs",
        "svg",
        "png",
        "jpg",
        "gif",
        "pdf",
        "log",
    ],
)
def test_filename_exemption_rejects_embedded_hosts(tmp_path: Path, extension: str) -> None:
    store = _store(tmp_path)
    lease = _open(store)
    # A file extension cannot exempt a host-named file from handoff hygiene.
    with pytest.raises(ContentRejectedError, match="hostname rule"):
        store.append_entry(
            lease,
            entry_type=EntryType.NOTE,
            body=f"Changed `example.com.{extension.upper()}`.",
            idempotency_key="filename",
            now=NOW + timedelta(seconds=1),
        )
    with pytest.raises(ContentRejectedError, match="hostname rule"):
        store.append_entry(
            lease,
            entry_type=EntryType.NOTE,
            body=f"example.{extension}.example.com",
            idempotency_key="host",
            now=NOW + timedelta(seconds=2),
        )
    assert store.dump_stream(lease.stream_id)["entries"] == []


@pytest.mark.parametrize(
    "body,rule",
    [
        # Synthetic domains and documentation addresses; no runtime configuration.
        *[(f"example.{suffix}", "hostname") for suffix in ("com", "org", "net", "io", "dev", "ua", "ru")],
        *[
            (host, "hostname")
            for host in (
                "docs.rs",
                "bun.sh",
                "server.sh",
                "box.py",
                "host.md",
                ".hidden.py",
                "unknown.md",
                "SERVER.SH",
                "example.com.py",
                "api.example.co.py",
                "EXAMPLE.COM.PY",
                "server.sh/admin",
                "example.md/path",
                "example.rs?x=1",
                "example.py#frag",
                "example.local",
                "example.lan",
                "example.internal",
                "home.arpa",
                "example.zip",
                "example.mov",
                "example.ai",
                "example.io",
                "example.so",
                "example.to",
                "example.am",
                "example.cc",
                "example.ps",
                "example.pl",
                "example.pm",
                "example.sc",
                "example.py-x",
                "core.md:12",
                "store.py:55",
                "core.md/path",
                "store.py?x=1",
                "README.md#frag",
                "https://core.md",
                "//store.py",
                "//example.db",
                "https://example.json",
                "core.md.",
                "scripts/example.com.py",
                "example.com/core.md",
                "example.sh/core.md",
                r"\\server.sh\share",
                r"\\fileserver.md\public",
                r"\\box.py",
                r"\\SERVER.SH\SHARE",
                r"\\FILESERVER.MD\PUBLIC",
                r"\\BOX.PY",
                r"\/server.sh\share",
                r"/\FILESERVER.MD/public",
                "https:/server.sh",
                "HTTPS:/SERVER.SH",
                r"https:\server.sh",
                r"HTTPS:/\SERVER.SH",
                "file:/server.sh",
                "file://fileserver.md/public",
                "FILE:/BOX.PY",
                "FILE://SERVER.SH/share",
                r"file:\box.py",
                r"file:\\fileserver.md\public",
                r"FILE:/\SERVER.SH/share",
                r"file:\/BOX.PY",
                r"\Device\Mup\server.sh\share",
                r"\Device\LanmanRedirector\server.sh\share",
                r"\\?\GLOBALROOT\??\UNC\server.sh\share",
                r"\\?\GLOBALROOT\GLOBAL??\UNC\server.sh\share",
                r"\\?\GLOBALROOT\Device\LanmanRedirector\;Z:00000000000003e7\server.sh\share",
                r"\Device\Mup\;Z:00000000000003e7\server.sh\share",
                "file:///server.sh",
                "https:/core.md",
                r"\\store.py",
                "example.com.json",
                "host_vars/web01.example.com.yml",
                "nas.local.yaml",
                "host.internal.json",
                "EXAMPLE.COM.JSON",
                r"host_vars\WEB01.EXAMPLE.COM.YML",
                "web01.prod.example.net.yaml",
                "db.example.org.log",
                "example.com.txt",
            )
        ],
        ("sources.db.example.com", "hostname"),
        ("*.example.com", "hostname"),
        (".example.com", "hostname"),
        ("fixture_name.example.com", "hostname"),
        ("_service._tcp.example.com", "hostname"),
        ("EXAMPLE.COM", "hostname"),
        ("example.com.", "hostname"),
        ("example.py.", "hostname"),
        ("example.com:443", "hostname"),
        ("example.py:443", "hostname"),
        ("https://example.com:443/core.md", "hostname"),
        ("https://example.py/core.md", "hostname"),
        ("//example.py/core.md", "hostname"),
        ("https://reader@example.com/core.md", "email-address"),
        ("https://reader@example.py/core.md", "email-address"),
        ("https://reader:fixture@example.com/core.md", "email-address"),
        ("xn--bcher-kva.example.com", "hostname"),
        ("example.xn--p1ai", "hostname"),
        ("EXAMPLE.XN--P1AI.:443", "hostname"),
        ("example.pyx", "hostname"),
        ("example.py.backup", "hostname"),
        ("core.md.example", "hostname"),
        ("`sources.db` and example.com", "hostname"),
        ("192.0.2.1", "ipv4-address"),
        ("192.0.2.1:443", "ipv4-address"),
        ("https://192.0.2.1/core.md", "ipv4-address"),
        ("2001:db8::1", "ipv6-address"),
        ("[2001:DB8::1]:443", "ipv6-address"),
        ("https://[2001:db8::1]/core.md", "ipv6-address"),
        ("::1", "ipv6-address"),
    ],
)
def test_filename_exemption_preserves_host_and_ip_rejection(tmp_path: Path, body: str, rule: str) -> None:
    store = _store(tmp_path)
    lease = _open(store)
    with pytest.raises(ContentRejectedError, match=f"{rule} rule"):
        store.append_entry(
            lease, entry_type=EntryType.NOTE, body=body, idempotency_key="rejected", now=NOW + timedelta(seconds=1)
        )
    assert store.dump_stream(lease.stream_id)["entries"] == []


@pytest.mark.parametrize("namespace", ["\\\\?\\", "\\\\.\\", "\\??\\"])
@pytest.mark.parametrize(
    "network_root",
    ["UNC", r"GLOBALROOT\UNC", "GLOBALROOT", r"GLOBALROOT\Device\Mup", r"GLOBALROOT\Device\LanmanRedirector"],
)
def test_namespace_network_roots_cannot_exempt_hosts(namespace: str, network_root: str) -> None:
    # Every namespace/root pair receives the same spelling and context probes.
    # These cover the reviewed extended-UNC forms and NT network-device roots.
    for separator, upper, host, ending, wrapper in product(
        ["\\", "/", "\\/", "/\\", "\\\\", "//"],
        [False, True],
        ["server.sh", "fileserver.md", "box.py", "docs.rs"],
        ["", "\\", "\\share", "\\share\\"],
        [("", ""), ("`", "`"), ('"', '"'), ("[", "]"), ("(", ")")],
    ):
        path = namespace + network_root + "\\" + host + ending
        path = path.swapcase() if upper else path
        path = path.replace("\\", separator)
        body = f"Changed {wrapper[0]}{path}{wrapper[1]}"
        assert _contains_hostname(body), body
        with pytest.raises(ContentRejectedError, match="hostname rule"):
            validate_entry_body(body)


@pytest.mark.parametrize(
    "root",
    [
        r"\Device\Mup",
        r"\Device\LanmanRedirector",
        r"\Device\OtherRedirector",
        r"\\?\GLOBALROOT\??\UNC",
        r"\\?\GLOBALROOT\GLOBAL??\UNC",
        r"\\?\GLOBALROOT\Device\Mup",
        r"\\?\GLOBALROOT\Device\LanmanRedirector",
        r"\\?\GLOBALROOT\Device\OtherRedirector",
        r"\\.\GLOBALROOT\Device\OtherRedirector",
        r"\??\GLOBALROOT\Device\OtherRedirector",
    ],
)
def test_following_separator_rejects_hosts_under_any_device_root(root: str) -> None:
    # Arbitrary device roots and session segments must not need prefix entries.
    for separator, upper, host, session, ending in product(
        ["\\", "/", "\\/", "/\\", "\\\\", "//"],
        [False, True],
        ["server.sh", "fileserver.md", "box.py", "docs.rs"],
        ["", ";Z:", ";Z:00000000000003e7\\"],
        ["\\", "\\share"],
    ):
        path = root + "\\" + session + host + ending
        path = path.swapcase() if upper else path
        path = path.replace("\\", separator)
        body = f"Changed `{path}`"
        with pytest.raises(ContentRejectedError, match="hostname rule"):
            validate_entry_body(body)


@pytest.mark.parametrize("separator", ["/", "\\"])
@pytest.mark.parametrize("name", ["server.sh", "core.md", "store.py", "docs.rs"])
def test_host_shaped_directory_segments_are_conservatively_rejected(separator: str, name: str) -> None:
    # Intentionally reject even local directories: only the final segment can
    # use the filename exemption, so a host-shaped directory cannot hide a host.
    validate_entry_body(separator.join(["scripts", name]))
    with pytest.raises(ContentRejectedError, match="hostname rule"):
        validate_entry_body(separator.join(["scripts", name, "x"]))


@pytest.fixture
def repository_filename_paths() -> tuple[str, ...]:
    # Snapshot of the explicit exceptions, checked against Git only in tests.
    # Runtime admission never depends on the caller's filesystem or Git state.
    return (
        "agents_extensions/shared/rules/core.md",
        "README.md",
        "agents_extensions/shared/session_streams/store.py",
    )


@pytest.mark.repo_wide
def test_collision_exceptions_are_exact_tracked_repository_names(repository_filename_paths: tuple[str, ...]) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["git", "ls-files", "-z"], cwd=repo_root, check=True, capture_output=True, text=True, timeout=30
    )
    tracked = set(result.stdout.split("\0"))
    assert set(repository_filename_paths) <= tracked
    assert {Path(path).name for path in repository_filename_paths} == _REPOSITORY_FILENAMES


@pytest.mark.repo_wide
def test_embedded_host_filter_accepts_every_tracked_basename() -> None:
    # Check S1 independently: the existing collision-TLD rule intentionally
    # rejects bare unknown .md/.py names, which still need directory context.
    repo_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["git", "ls-files", "-z"], cwd=repo_root, check=True, capture_output=True, text=True, timeout=30
    )
    tracked = [path for path in result.stdout.split("\0") if path]
    assert tracked, "the guard must inspect the tracked Git index"
    rejected = [path for path in tracked if _filename_contains_hostname(Path(path).name)]
    assert rejected == [], "exempt the exact basename (_EMBEDDED_HOST_EXEMPT_FILENAMES): " + repr(rejected)


@pytest.mark.repo_wide
def test_embedded_host_exemptions_are_required_by_tracked_basenames() -> None:
    # Every exemption names its tracked collisions; a stale one must be removed.
    repo_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["git", "ls-files", "-z"], cwd=repo_root, check=True, capture_output=True, text=True, timeout=30
    )
    basenames = {Path(path).name for path in result.stdout.split("\0") if path}
    assert basenames, "the guard must inspect the tracked Git index"
    assert sorted(_EMBEDDED_HOST_EXEMPT_FILENAMES - basenames) == []


def test_embedded_host_exempt_filenames_each_need_their_exemption(monkeypatch: pytest.MonkeyPatch) -> None:
    exempt = sorted(_EMBEDDED_HOST_EXEMPT_FILENAMES)
    assert not any(_filename_contains_hostname(filename) for filename in exempt)
    monkeypatch.setattr(store_module, "_EMBEDDED_HOST_EXEMPT_FILENAMES", frozenset())
    assert [filename for filename in exempt if not _filename_contains_hostname(filename)] == []


@pytest.mark.repo_wide
def test_backslash_tracked_paths_add_no_hostname_rejections() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["git", "ls-files", "-z"], cwd=repo_root, check=True, capture_output=True, text=True, timeout=30
    )
    tracked = [path for path in result.stdout.split("\0") if path]
    assert tracked, "the guard must inspect the tracked Git index"
    # Existing bare-name and unsupported-extension rejections apply equally
    # to either spelling; backslashes must introduce no new full-path rejection.
    newly_rejected = [
        path for path in tracked if _contains_hostname(path.replace("/", "\\")) and not _contains_hostname(path)
    ]
    assert newly_rejected == [], repr(newly_rejected)
    # Independently guard file-shaped directory segments, including paths whose
    # final basename is already rejected, against losing the file exemption.
    rejected_directories = [
        path
        for path in tracked
        if any(
            segment.rpartition(".")[2].lower() in _FILE_EXTENSIONS and _contains_hostname(segment + "\\")
            for segment in path.split("/")[:-1]
        )
    ]
    assert rejected_directories == [], repr(rejected_directories)


# The closed label list used before #9430; the suffix list must keep it all.
_LEGACY_EMBEDDED_HOST_SUFFIXES = (
    *("com", "net", "org", "io", "dev", "app", "cloud", "local", "internal", "lan", "corp", "home"),
    *("arpa", "intranet", "private", "edu", "gov", "ru", "ua", "de", "nl", "fr", "us", "uk"),
)


@pytest.mark.parametrize("suffix", _LEGACY_EMBEDDED_HOST_SUFFIXES)
def test_closed_host_suffixes_cannot_be_hidden_in_filenames(suffix: str) -> None:
    assert suffix in _EMBEDDED_HOST_SUFFIXES
    for filename in (f"example.{suffix}.json", f"host_vars/example.{suffix.upper()}.YML"):
        assert _filename_contains_hostname(filename)
        with pytest.raises(ContentRejectedError, match="hostname rule"):
            validate_entry_body(filename)


def test_every_public_suffix_label_is_a_host_before_every_extension() -> None:
    # Denominator: every top-level label of the vendored snapshot, every extension.
    assert {"com", "info", "xyz", "ai", "me", "jp", "xn--p1ai"} <= _PUBLIC_SUFFIX_TLDS
    missed = [
        filename
        for label in sorted(_EMBEDDED_HOST_SUFFIXES)
        for extension in sorted(_FILE_EXTENSIONS)
        for filename in (f"example.{label}.{extension}", f"host_vars/WEB01.{label.upper()}.{extension.upper()}")
        if not _filename_contains_hostname(filename)
    ]
    assert missed == []
    passed = []
    for label in sorted(_EMBEDDED_HOST_SUFFIXES):
        try:
            validate_entry_body(f"Changed `host_vars/web01.example.{label}.yaml`.")
        except ContentRejectedError:
            continue
        passed.append(label)
    assert passed == []


@pytest.mark.parametrize(
    "body",
    [
        "example.info.json",
        "host.biz.yaml",
        "example.xyz.md",
        "model.ai.py",
        "about.me.txt",
        "host_vars/web01.example.co.jp.yml",
        r"`host_vars\WEB01.EXAMPLE.ONLINE.YML`",
        "example.xn--p1ai.json",
        "host.org.uk.md",
        "school.sch.uk.md",
        "nhs.uk.md",
        "docs/PHASE1.uk.md",
        "host.review.yaml",
        "host.review.md",
        "host.report.md",
        "x.review.json",
        "Changed `host_vars/web01.example.review.json`.",
        "Changed `host_vars/web01.example.report.json`.",
        "reviews/decol_lex_061.review.json",
        "evidence/decol_lex_001.review.json.review.json",
        "other.py.txt",
        "run_codex_baseline.py.json",
        "RUN_CODEX_BASELINE.PY.TXT",
    ],
)
def test_hosts_under_public_suffix_labels_are_rejected(body: str) -> None:
    with pytest.raises(ContentRejectedError, match="hostname rule"):
        validate_entry_body(body)


@pytest.mark.parametrize(
    "body",
    [
        "decol_lex_001.review.json",
        "reviews/decol_syn_065.review.json",
        "plan-validate.report.json",
        "baselines/v1/gpt-5.6-terra.report.json",
        "run_codex_baseline.py.txt",
        "archive/evidence/ua-eval-v0.1.0/run_codex_baseline.py.txt",
    ],
)
def test_tracked_suffix_label_conventions_remain_files(body: str) -> None:
    assert not _filename_contains_hostname(body)
    validate_entry_body(body)


@pytest.mark.parametrize(
    "body",
    [
        "example.中国.json",
        "example.рф.json",
        "україна.com.json",
        "EXAMPLE.РФ.JSON",
        "Changed `host_vars/web01.приклад.укр.yaml`.",
        r"`host_vars\web01.example.онлайн.yml`",
        "україна.com",
        "Сайт приклад.укр працює",
        "приклад.рф/шлях",
        "Дивіться приклад.рф.",
        "приклад.com.ua",
        "gіthub.com",
        "example.р\u0301ф.json",
        "example\u3002中国\u3002json",
        "example\uff0eрф",
        "example.संगठन.json",
        "एक.भारत",
    ],
)
def test_internationalized_host_names_are_rejected(body: str) -> None:
    with pytest.raises(ContentRejectedError, match="hostname rule"):
        validate_entry_body(body)


def test_every_unicode_public_suffix_label_is_rejected_in_both_spellings() -> None:
    # Denominator: every IDN top-level label of the vendored snapshot.
    unicode_labels = sorted(
        label.encode("ascii").decode("idna") for label in _PUBLIC_SUFFIX_TLDS if label.startswith("xn--")
    )
    assert len(unicode_labels) > 100 and "рф" in unicode_labels and "укр" in unicode_labels
    passed = [
        body
        for label in unicode_labels
        for body in (f"example.{label}.json", f"приклад.{label}", f"Changed `host_vars/web01.{label.upper()}.yaml`.")
        if not _contains_hostname(body)
    ]
    assert passed == []


@pytest.mark.parametrize(
    "body",
    [
        "т.д.",
        "т.п.",
        "і т.ін.",
        "і т.д. і т.п.",
        "ім. Шевченка",
        "с. Вишневе",
        "до н.е.",
        "укр. мова",
        "тис.грн",
        "вул.Хрещатик",
        "Оновлено звіт.json і docs/звіт.md",
        "Модуль готовий.Далі буде рев'ю.",
        "Мо\u0301ва — це код на\u0301ції. Пишемо українською, т.зв. живою мовою.",
        "Оновлено curriculum/l2-uk-en/a1/plans/привіт.yaml.",
    ],
)
def test_ukrainian_prose_and_abbreviations_are_not_hosts(tmp_path: Path, body: str) -> None:
    store = _store(tmp_path)
    lease = _open(store)
    entry = store.append_entry(
        lease, entry_type=EntryType.NOTE, body=body, idempotency_key="prose", now=NOW + timedelta(seconds=1)
    ).entry
    assert entry.body == body


def test_public_suffix_loader_reads_rules_wildcards_and_idn_labels(tmp_path: Path) -> None:
    snapshot = tmp_path / "psl.dat"
    data = (
        "// ===BEGIN ICANN DOMAINS===\nac\ncom.ac\n*.ck\n!www.ck\n*.sch.uk\nрф\n// ===END ICANN DOMAINS===\n"
        "// ===BEGIN PRIVATE DOMAINS===\nexample.github.io\n// ===END PRIVATE DOMAINS===\n"
    ).encode()
    snapshot.write_bytes(data)
    top_level = load_public_suffix_labels(snapshot, sha256=hashlib.sha256(data).hexdigest())
    assert top_level == {"ac", "ck", "uk", "xn--p1ai", "io"}


def _vendored_snapshot_without(tmp_path: Path, drop: Callable[[int, str], bool]) -> tuple[Path, str]:
    lines = PUBLIC_SUFFIX_LIST_PATH.read_text(encoding="utf-8").splitlines(keepends=True)
    data = "".join(line for index, line in enumerate(lines) if not drop(index, line)).encode()
    snapshot = tmp_path / "psl.dat"
    snapshot.write_bytes(data)
    return snapshot, hashlib.sha256(data).hexdigest()


def test_public_suffix_loader_fails_closed_on_truncated_snapshot(tmp_path: Path) -> None:
    half = len(PUBLIC_SUFFIX_LIST_PATH.read_text(encoding="utf-8").splitlines()) // 2
    snapshot, digest = _vendored_snapshot_without(tmp_path, lambda index, _line: index >= half)
    with pytest.raises(RuntimeError, match="pinned SHA-256"):
        load_public_suffix_labels(snapshot)
    # Even a snapshot pinned to its own digest needs all four section markers.
    with pytest.raises(RuntimeError, match="lacks section markers"):
        load_public_suffix_labels(snapshot, sha256=digest)
    with pytest.raises(FileNotFoundError):
        load_public_suffix_labels(tmp_path / "absent.dat")


@pytest.mark.parametrize(
    "drop",
    [
        pytest.param(lambda _index, line: line.strip() == "com", id="one-rule-removed"),
        pytest.param(lambda _index, line: line.strip() == "рф", id="idn-rule-removed"),
        pytest.param(lambda _index, line: not line.startswith("//"), id="markers-only"),
        pytest.param(lambda _index, line: not line.startswith("//") and line.strip() != "com", id="one-rule-only"),
    ],
)
def test_public_suffix_loader_fails_closed_on_removed_rules_with_markers_kept(
    tmp_path: Path, drop: Callable[[int, str], bool]
) -> None:
    snapshot, _digest = _vendored_snapshot_without(tmp_path, drop)
    text = snapshot.read_text(encoding="utf-8")
    assert all(
        marker in text.splitlines() for marker in ("// ===BEGIN ICANN DOMAINS===", "// ===END PRIVATE DOMAINS===")
    )
    assert text != PUBLIC_SUFFIX_LIST_PATH.read_text(encoding="utf-8")
    with pytest.raises(RuntimeError, match="pinned SHA-256"):
        load_public_suffix_labels(snapshot)


def test_vendored_public_suffix_snapshot_is_pinned_and_rules_only() -> None:
    assert hashlib.sha256(PUBLIC_SUFFIX_LIST_PATH.read_bytes()).hexdigest() == PUBLIC_SUFFIX_LIST_SHA256
    lines = PUBLIC_SUFFIX_LIST_PATH.read_text(encoding="utf-8").splitlines()
    assert any(line.startswith("// VERSION: ") for line in lines)
    assert any(line.startswith("// COMMIT: ") and len(line.split()[-1]) == 40 for line in lines)
    rules = [line for line in lines if not line.startswith("//")]
    assert rules and all(rule and not any(char.isspace() for char in rule) for rule in rules)
    # Keep the hand-written TLD/extension intersection true for this snapshot.
    assert _FILE_EXTENSIONS & _PUBLIC_SUFFIX_TLDS == _TLD_FILE_EXTENSIONS


@pytest.mark.parametrize(
    "filename",
    ["store.sources.yaml", "x.schema.json", "x.test.ts", "x.locale.json"],
)
def test_repository_stem_labels_remain_files(filename: str) -> None:
    assert not _filename_contains_hostname(filename)
    validate_entry_body(filename)


@pytest.mark.parametrize("extension", sorted(_FILE_EXTENSIONS))
def test_uk_and_arpa_host_endings_cannot_be_hidden_in_filenames(extension: str) -> None:
    filenames = [f"host.co.uk.{extension}", f"host.example.co.uk.{extension}", f"host.home.arpa.{extension}"]
    filenames.extend([f"host.uk.{extension}", f"x.uk.{extension}"])
    if extension == "md":
        # Only the exact tracked localization basenames stay files; the
        # separate collision-TLD rule still applies to bare names.
        for filename in ("README.uk.md", "DATA_CARD.uk.md"):
            assert not _filename_contains_hostname(filename)
        assert _filename_contains_hostname("PHASE1.uk.md")
    for filename in filenames:
        for body in (filename, f"host_vars/{filename.upper()}", f"`host_vars\\{filename}`"):
            assert _filename_contains_hostname(filename), filename
            with pytest.raises(ContentRejectedError, match="hostname rule"):
                validate_entry_body(body)
    # Even the two-label stem is a host; it cannot use the localization exception.
    assert _filename_contains_hostname(f"co.uk.{extension}")


@pytest.mark.parametrize(
    "body",
    [
        "Opus 5.5",
        "gpt-6.1-sol",
        "Python 3.12",
        "v1.2.3",
        "0.5",
        "4.6k",
        "e.g.",
        "i.e.",
        "U.S.",
        "foo.c",
        "foo.h",
        "package.json5",
        "python -m scripts.fleet_comms",
    ],
)
def test_append_accepts_ordinary_model_version_and_module_tokens(tmp_path: Path, body: str) -> None:
    store = _store(tmp_path)
    lease = _open(store)
    entry = store.append_entry(
        lease, entry_type=EntryType.NOTE, body=body, idempotency_key="ordinary", now=NOW + timedelta(seconds=1)
    ).entry
    assert entry.body == body


@pytest.mark.parametrize(
    "unit,rejected",
    [
        ("a", False),
        ("0123456789abcdef", False),
        ("YWJjZGVm+/", False),
        ("a.py-", True),
        ("a.", False),
        ("a.1.", False),
        ("a.py.", True),
        ("\\", False),
        ("/", False),
        ("//?/UNC/a.1/", False),
    ],
)
def test_entry_validation_handles_64_kib_tokens_without_rescanning(unit: str, rejected: bool) -> None:
    body = (unit * (MAX_ENTRY_BYTES // len(unit) + 1))[:MAX_ENTRY_BYTES]
    started = thread_time()
    # Some dotted runs are hosts; timing covers both acceptance and rejection.
    if rejected:
        with pytest.raises(ContentRejectedError, match="hostname rule"):
            validate_entry_body(body)
    else:
        validate_entry_body(body)
    elapsed = thread_time() - started
    # CPU time avoids scheduler contention; this generous regression limit
    # still rejects quadratic rescanning without a loaded-runner wall-clock flake.
    assert elapsed < 2, f"64-KiB token validation used {elapsed:.3f}s CPU"


def test_100_kb_token_has_bounded_scan_and_size_rejection() -> None:
    body = "a." * 50_000
    started = thread_time()
    assert not _contains_hostname(body)
    with pytest.raises(ContentRejectedError, match="64-KiB rule"):
        validate_entry_body(body)
    elapsed = thread_time() - started
    assert elapsed < 2, f"100-KB token scan used {elapsed:.3f}s CPU"


@pytest.mark.parametrize("body", ["contact test@example.com", "a.py-test@example.com", ".test@example.com"])
def test_email_rejection_preserved_with_linear_token_boundary(body: str) -> None:
    with pytest.raises(ContentRejectedError, match="email-address rule"):
        validate_entry_body(body)


@pytest.mark.parametrize(
    "body",
    ["ssh fixture", "scp fixture", "rsync fixture", "git@fixture:", "a.c-user@fixture:", "user-name@fixture:"],
)
def test_ssh_rejection_preserved_with_linear_token_boundary(body: str) -> None:
    with pytest.raises(ContentRejectedError, match="ssh-alias rule"):
        validate_entry_body(body)


def test_mirror_handoff_accepts_issue_filenames(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    handoff = repo_root / "handoff.md"
    body = "Updated `sources.db`, `vesum.db`, `core.md`, `a1.yaml`, `lexicon-manifest.json`, `mcp-sources-requests.jsonl`.\n"
    handoff.write_text(body, encoding="utf-8")
    store = _store(tmp_path / "runtime")
    lease = _open(store)
    result = mirror_atlas_handoff(
        store, lease, repo_root=repo_root, stream_id=lease.stream_id, source_path=Path("handoff.md"), now=NOW
    )
    assert result.entry.body == body
    assert handoff.read_text(encoding="utf-8") == body
    assert store.dump_stream(lease.stream_id)["entries"][0]["body"] == body


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
    ).entry
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
    # Live holder is never force-closed, before or after wall-clock TTL.
    with pytest.raises(LeaseConflictError, match="still live"):
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

    # Dead holder is force-closable even while TTL is still unexpired.
    process_state[41001] = False
    proof_early = store.force_close_expired_session(
        stream_id="epic:4707",
        session_id="session-one",
        candidate=candidate,
        now=NOW + timedelta(seconds=5),
    )
    assert proof_early.heartbeat_age_seconds == 5
    assert proof_early.holder_process_id == 41001
    assert proof_early.candidate_instance_id == "runtime-2"
    with pytest.raises(LeaseConflictError):
        store.heartbeat(original, now=NOW + timedelta(seconds=6))
    with pytest.raises(LeaseConflictError):
        store.append_entry(
            original,
            entry_type=EntryType.NOTE,
            body="Old holder fenced.",
            idempotency_key="old-holder",
            now=NOW + timedelta(seconds=6),
        )

    successor = store.open_session(
        stream_id="epic:4707",
        holder=candidate,
        lineage_id="lineage-successor",
        ttl_seconds=30,
        session_id="session-two",
        lease_id="lease-two",
        now=NOW + timedelta(seconds=7),
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
    assert (
        store.transition_session(
            lease,
            to_state=SessionState.ROLLING,
            reason="prepared exact rollover",
            now=NOW + timedelta(seconds=1),
        )
        is SessionState.ROLLING
    )
    assert heartbeat_hook(store, lease, now=NOW + timedelta(seconds=1)).state == "rolling"
    assert (
        store.transition_session(
            lease,
            to_state=SessionState.OPEN,
            reason="same live run resumed",
            now=NOW + timedelta(seconds=2),
        )
        is SessionState.OPEN
    )
    entry = store.append_entry(
        lease,
        entry_type=EntryType.NEXT_ACTION,
        body="Close cleanly.",
        idempotency_key="before-close",
        now=NOW + timedelta(seconds=3),
    ).entry
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
