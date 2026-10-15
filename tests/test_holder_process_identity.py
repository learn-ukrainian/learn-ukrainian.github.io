"""Typed lease holder process identity (#10657 round 4), one reproducer per input class.

Contract: attestation succeeds only for the live holder of the lease generation
it names; every other path refuses with a registered, value-free cause. The
identity is ``holder.process_identity``: fixed by the session supervisor at
acquisition from the launcher that runs it, immutable within a generation,
outside every renew and release match, and never read from the environment.

Entry points: claim, renew (heartbeat), fenced write (handoff), release,
attest (``verify_current_custody`` with the kernel proof) and API read. Lane
succession and the attested writers' confirmed publication are exercised in
``tests/fleet/test_terminal_abandon_attest.py`` and
``tests/fleet/test_terminal_abandon_publication.py``.
"""

from __future__ import annotations

import dataclasses
import functools
import json
import os
import socket
import sqlite3
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agents_extensions.shared.session_streams import process_identity
from agents_extensions.shared.session_streams.db import SessionStreamDatabase, load_migrations
from agents_extensions.shared.session_streams.hooks import lease_from_environment
from agents_extensions.shared.session_streams.model import (
    EntryType,
    HolderKind,
    Lease,
    LeaseHolder,
    isoformat_z,
    parse_timestamp,
    utc_now,
)
from agents_extensions.shared.session_streams.store import SessionStreamStore
from scripts.api import epics_router
from scripts.fleet import terminal_abandon
from scripts.session_supervisor import remote
from tests.epics_monitor_stub import epics_app_for_store, epics_monitor_stub
from tests.fleet.test_terminal_abandon import FOREIGN_PID, kernel_identity

REPO = Path(__file__).resolve().parents[1]
STREAM = "epic:9999"
CLAIM_FIELDS = {"agent": "codex", "harness": "codex-cli", "instance_id": "codex-holder", "host_id": "api-host"}
OLD_HOLDER_KEYS = {"agent", "harness", "instance_id", "task_id", "process_id", "holder_kind", "host_id"}
# Environment an impersonator might set; nothing that derives or proves an identity reads it.
SPOOFED_ENV = {
    "SESSION_STREAM_PROCESS_IDENTITY": "v1:" + "0" * 64,
    "LU_MONITOR_HOST_ID": "host-elsewhere",
    "LU_PROCESS_IDENTITY": "v1:" + "1" * 64,
}


def _store(tmp_path: Path) -> SessionStreamStore:
    """A migrated store, as Monitor's startup inventory seed leaves it."""
    store = SessionStreamStore(SessionStreamDatabase(tmp_path / "streams.sqlite3"))
    store.database.connect().close()
    return store


def _client(store: SessionStreamStore, tmp_path: Path) -> TestClient:
    app = epics_app_for_store(store, tmp_path / "ctx")
    return TestClient(app, base_url="http://127.0.0.1", client=("127.0.0.1", 8765))


def _claim_body(*, process_id: int, identity: str | None = None, session: str = "s-1", lease: str = "l-1") -> dict:
    body = {
        "session_id": session,
        "lease_id": lease,
        "lineage_id": "lineage-r4",
        "process_id": process_id,
        "ttl_seconds": 900,
        "digest_limit": 1,
        **CLAIM_FIELDS,
    }
    if identity is not None:
        body["process_identity"] = identity
    return body


def _stored(store: SessionStreamStore) -> tuple[str | None, list[str | None]]:
    """The projection's identity and every lease event's identity, oldest first."""
    connection = store.database.connect(read_only=True)
    try:
        row = connection.execute(
            "SELECT holder_process_identity FROM stream_leases WHERE stream_id = ?", (STREAM,)
        ).fetchone()
        events = connection.execute(
            "SELECT holder_process_identity FROM lease_events WHERE stream_id = ? ORDER BY event_id", (STREAM,)
        ).fetchall()
    finally:
        connection.close()
    return (row[0] if row else None), [event[0] for event in events]


def _authority(lease: dict) -> dict:
    """What an attesting writer records: the generation and its recorded holder identity."""
    holder = {key: lease["holder"][key] for key in ("agent", "harness", "instance_id")}
    if "process_identity" in lease["holder"]:
        holder["process_identity"] = lease["holder"]["process_identity"]
    return {key: lease[key] for key in ("stream_id", "session_id", "lease_id", "generation", "fencing_token")} | {
        "holder": holder
    }


def _held_here(monkeypatch, base: str, authority: dict) -> str:
    """Attest from this test process: ``HELD`` or the registered refusal code."""
    monkeypatch.setattr(remote, "DEFAULT_MONITOR", base)
    try:
        terminal_abandon.verify_current_custody(authority, caller_holds=True)
    except terminal_abandon.Refusal as refusal:
        return refusal.code
    return "HELD"


# --- Kernel derivation: the actual long-lived holder, never a nominated value ---


PEER = r"""
import socket, sys
connection = socket.create_connection(("127.0.0.1", int(sys.argv[1])))
print(*connection.getsockname(), flush=True)
sys.stdin.readline()
"""


def _peer(port: int) -> subprocess.Popen:
    """A process connected to ``port`` that holds the connection until its stdin closes."""
    return subprocess.Popen(
        [sys.executable, "-c", PEER, str(port)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
        cwd=REPO,
        env={**os.environ, **SPOOFED_ENV},
    )


def test_monitor_derives_only_the_parent_of_the_connecting_process():
    """Monitor's derivation names the connecting process's actual parent, if it is the claimed holder PID."""
    derive = process_identity.connected_peer_parent_identity
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        server = listener.getsockname()
        child = _peer(server[1])
        try:
            accepted, client = listener.accept()
            with accepted:
                assert child.stdout is not None
                assert child.stdout.readline().split() == [client[0], str(client[1])]
                assert derive(client, server, os.getpid()) == kernel_identity(os.getpid())
                # Never the connecting command itself, a further ancestor, init or a non-integer.
                for other in (child.pid, os.getppid(), 1, True, FOREIGN_PID):
                    assert derive(client, server, other) is None
                # A connection the claim did not arrive on names nothing.
                assert derive(client, (server[0], server[1] + 1), os.getpid()) is None
        finally:
            assert child.stdin is not None
            child.stdin.close()
            child.wait(timeout=30)
        # A client connecting directly records only its own actual parent, never itself.
        with socket.create_connection(server) as own:
            accepted, client = listener.accept()
            with accepted:
                assert derive(client, server, os.getpid()) is None
                assert derive(client, server, os.getppid()) == kernel_identity(os.getppid())
                # A connection shared with another process is ambiguous and records nothing.
                sharer = subprocess.Popen(
                    [sys.executable, "-c", "import sys; sys.stdin.readline()"],
                    stdin=subprocess.PIPE,
                    pass_fds=(own.fileno(),),
                )
                try:
                    assert derive(client, server, os.getppid()) is None
                finally:
                    assert sharer.stdin is not None
                    sharer.stdin.close()
                    sharer.wait(timeout=30)


def test_monitor_derivation_fails_closed_without_kernel_facts(monkeypatch):
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        server = listener.getsockname()
        with socket.create_connection(server):
            accepted, client = listener.accept()
            with accepted:
                assert process_identity.connected_peer_parent_identity(client, server, os.getppid()) is not None

                def unreadable(*_args, **_kwargs):
                    raise OSError("no /proc")

                for name in ("_boot_id", "_namespace", "_socket_owners", "_socket_inode"):
                    with monkeypatch.context() as patch:
                        patch.setattr(process_identity, name, unreadable)
                        assert process_identity.connected_peer_parent_identity(client, server, os.getppid()) is None


def test_lineage_identity_refuses_a_non_ancestor_and_unreadable_kernel_facts(monkeypatch):
    assert process_identity.lineage_identity(os.getpid()) == kernel_identity(os.getpid())
    assert process_identity.lineage_identity(os.getppid()) == kernel_identity(os.getppid())
    with pytest.raises(LookupError):
        process_identity.lineage_identity(FOREIGN_PID)

    def no_proc():
        raise OSError("no /proc")

    monkeypatch.setattr(process_identity, "_lineage", no_proc)
    with pytest.raises(process_identity.ProcessIdentityUnavailable):
        process_identity.lineage_identity(os.getpid())


def test_lineage_that_moves_while_read_is_unverifiable(monkeypatch):
    """A chain read twice must be identical: an exited ancestor or a reused PID moves it."""
    real = process_identity._lineage
    reads = iter([real(), ((os.getpid(), 1),)])
    monkeypatch.setattr(process_identity, "_lineage", lambda: next(reads))
    with pytest.raises(process_identity.ProcessIdentityUnavailable):
        process_identity.lineage_identity(os.getpid())


@pytest.mark.parametrize(
    "value", [None, "", "a" * 64, "v1:" + "A" * 64, "v1:" + "a" * 63, "v2:" + "a" * 64, "v1:" + "g" * 64, 7]
)
def test_identity_format_is_typed_and_versioned(value):
    with pytest.raises(ValueError):
        process_identity.validate_process_identity(value)
    assert process_identity.validate_process_identity("v1:" + "a" * 64) == "v1:" + "a" * 64


def test_environment_never_supplies_an_identity(monkeypatch):
    """Copied environment values: the hook envelope carries no identity, whatever is set."""
    for key, value in {
        "SESSION_STREAM_ID": STREAM,
        "SESSION_STREAM_SESSION_ID": "s-1",
        "SESSION_STREAM_LEASE_ID": "l-1",
        "SESSION_STREAM_GENERATION": "1",
        "SESSION_STREAM_FENCING_TOKEN": "1",
        "SESSION_STREAM_AGENT": "codex",
        "SESSION_STREAM_HARNESS": "codex-cli",
        "SESSION_STREAM_INSTANCE_ID": "codex-holder",
        "SESSION_STREAM_PROCESS_ID": str(os.getpid()),
        **SPOOFED_ENV,
    }.items():
        monkeypatch.setenv(key, value)
    assert lease_from_environment().holder.process_identity is None
    assert "process_identity" not in remote.RemoteEpicClient._lease_payload(lease_from_environment())["holder"]


def test_app_thread_holder_never_records_an_identity():
    holder = LeaseHolder(
        agent="codex",
        harness="codex-app",
        instance_id="codex-app-1",
        task_id="7c9e6679-7425-40de-944b-e07fc1f90ae7",
        holder_kind=HolderKind.APP_THREAD,
        process_identity="v1:" + "a" * 64,
    )
    with pytest.raises(ValueError, match="only recorded for a process holder"):
        holder.validate()


# --- Store integrity: renewal permitted, the field immutable, no replacement ---


def _claimed_store(tmp_path: Path, identity: str | None):
    store = _store(tmp_path)
    holder = LeaseHolder(process_id=os.getpid(), process_identity=identity, **CLAIM_FIELDS)
    lease, outcome = store.claim_remote_session(
        stream_id=STREAM, holder=holder, lineage_id="lineage-r4", ttl_seconds=900, session_id="s-1", lease_id="l-1"
    )
    assert outcome == "claimed"
    return store, lease


def _raw(store: SessionStreamStore, *statements: tuple[str, tuple]) -> None:
    connection = store.database.connect()
    try:
        connection.execute("BEGIN IMMEDIATE")
        for sql, params in statements:
            connection.execute(sql, params)
        connection.execute("COMMIT")
    except Exception:
        connection.execute("ROLLBACK")
        raise
    finally:
        connection.close()


_EVENT_COLUMNS = (
    "stream_id, session_id, lease_id, generation, fencing_token, event_type, holder_kind, holder_agent, "
    "holder_harness, holder_instance_id, holder_task_id, holder_process_id, holder_host_id, ttl_seconds, ts, "
    "proof_json, reason"
)


def _old_client_event(store, *, session="s-1", lease="l-1", generation=1, fence=1, event="heartbeat", identity=None):
    """A lease event; by default written as code that predates the field would, with no identity."""
    columns, values = (
        (_EVENT_COLUMNS, "") if identity is None else (_EVENT_COLUMNS + ", holder_process_identity", ", ?")
    )
    _raw(
        store,
        (
            f"INSERT INTO lease_events({columns}) VALUES "
            "(?, ?, ?, ?, ?, ?, 'process', 'codex', 'codex-cli', 'codex-holder', NULL, ?, 'api-host', 900, ?, '{}', "
            f"'old client'{values})",
            (STREAM, session, lease, generation, fence, event, os.getpid(), isoformat_z(utc_now()))
            + (() if identity is None else (identity,)),
        ),
    )
    connection = store.database.connect(read_only=True)
    try:
        return int(connection.execute("SELECT max(event_id) FROM lease_events").fetchone()[0])
    finally:
        connection.close()


IDENTITY = "v1:" + "c" * 64


def test_store_renewal_keeps_the_identity_and_copies_it_onto_every_event(tmp_path):
    store, lease = _claimed_store(tmp_path, IDENTITY)
    # Renew, fenced write and release with the exact envelope, which carries no identity.
    envelope = dataclasses.replace(lease, holder=LeaseHolder(process_id=os.getpid(), **CLAIM_FIELDS))
    renewed = store.heartbeat(envelope)
    store.append_entry(renewed, entry_type=EntryType.STATE, body="working", idempotency_key="k-1")
    store.release_remote_session(envelope)
    projection, events = _stored(store)
    assert projection == IDENTITY
    assert events and set(events) == {IDENTITY}


@pytest.mark.parametrize("replacement", [None, "v1:" + "d" * 64])
def test_store_refuses_identity_mutation_within_a_generation(tmp_path, replacement):
    """Whole-record replacement by an old client: erasing or changing the field aborts."""
    store, _ = _claimed_store(tmp_path, IDENTITY)
    # The event agrees with the replacement, so only the generation's immutability refuses it.
    event = _old_client_event(store, identity=replacement)
    with pytest.raises(sqlite3.IntegrityError, match=r"immutable|monotonically"):
        _raw(
            store,
            (
                "UPDATE stream_leases SET holder_process_identity = ?, version = version + 1, last_event_id = ? "
                "WHERE stream_id = ?",
                (replacement, event, STREAM),
            ),
        )
    assert _stored(store)[0] == IDENTITY


def test_store_refuses_a_new_generation_that_carries_the_old_identity(tmp_path):
    """An old writer replacing the record for a new holder cannot inherit the predecessor's identity."""
    store, _ = _claimed_store(tmp_path, IDENTITY)
    now = isoformat_z(utc_now())
    store.release_remote_session(_claimed_lease_envelope(store))
    _raw(
        store,
        (
            "INSERT INTO sessions(session_id, stream_id, state, lineage_id, opened_at, updated_at, closed_at, "
            "state_version) VALUES ('s-2', ?, 'open', 'lineage-old', ?, ?, NULL, 1)",
            (STREAM, now, now),
        ),
    )
    event = _old_client_event(store, session="s-2", lease="l-2", generation=2, fence=2, event="acquired")
    with pytest.raises(sqlite3.IntegrityError, match="must match its lease event"):
        _raw(
            store,
            (
                # Every pre-0008 column, but not the identity: SQL keeps the old value.
                "UPDATE stream_leases SET session_id = 's-2', lease_id = 'l-2', generation = 2, fencing_token = 2, "
                "state = 'active', holder_kind = 'process', holder_agent = 'codex', holder_harness = 'codex-cli', "
                "holder_instance_id = 'codex-holder', holder_task_id = NULL, holder_process_id = ?, "
                "holder_host_id = 'api-host', heartbeat_at = ?, expires_at = ?, ttl_seconds = 900, "
                "version = version + 1, last_event_id = ? WHERE stream_id = ?",
                (os.getpid(), now, "2999-01-01T00:00:00Z", event, STREAM),
            ),
        )


def _claimed_lease_envelope(store: SessionStreamStore):
    projection = store.lease_projection(STREAM)
    assert projection is not None
    return dataclasses.replace(projection[0], holder=LeaseHolder(process_id=os.getpid(), **CLAIM_FIELDS))


def test_store_refuses_insert_or_replace_of_a_projection(tmp_path):
    """REPLACE would delete and re-insert the row without firing any update trigger."""
    store, _ = _claimed_store(tmp_path, IDENTITY)
    event = _old_client_event(store)
    with pytest.raises(sqlite3.IntegrityError, match="replaced only by a guarded update"):
        _raw(
            store,
            (
                "INSERT OR REPLACE INTO stream_leases(stream_id, session_id, lease_id, generation, fencing_token, "
                "state, holder_kind, holder_agent, holder_harness, holder_instance_id, holder_task_id, "
                "holder_process_id, holder_host_id, heartbeat_at, expires_at, ttl_seconds, version, last_event_id) "
                "VALUES (?, 's-1', 'l-1', 1, 1, 'active', 'process', 'codex', 'codex-cli', 'codex-holder', NULL, ?, "
                "'api-host', ?, '2999-01-01T00:00:00Z', 900, 99, ?)",
                (STREAM, os.getpid(), isoformat_z(utc_now()), event),
            ),
        )
    assert _stored(store)[0] == IDENTITY


def test_store_check_refuses_a_malformed_identity(tmp_path):
    store, _ = _claimed_store(tmp_path, None)
    with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
        _raw(
            store,
            (
                f"INSERT INTO lease_events({_EVENT_COLUMNS}, holder_process_identity) VALUES "
                "(?, 's-1', 'l-1', 1, 1, 'heartbeat', 'process', 'codex', 'codex-cli', 'codex-holder', NULL, ?, "
                "'api-host', 900, ?, '{}', 'fabricated', 'v1:NOT-HEX')",
                (STREAM, os.getpid(), isoformat_z(utc_now())),
            ),
        )


# --- API entry points: claim records, reads expose, nothing else populates ---


def _derived(monkeypatch, value: str | None) -> list[tuple]:
    """Stand in for the kernel lookup (TestClient has no socket); record what Monitor asked."""
    calls: list[tuple] = []

    def derive(client, server, parent_pid):
        calls.append((client, server, parent_pid))
        return value

    monkeypatch.setattr(epics_router, "connected_peer_parent_identity", derive)
    return calls


def test_api_claim_records_the_monitor_derived_identity_and_every_read_exposes_it(tmp_path, monkeypatch):
    calls = _derived(monkeypatch, IDENTITY)
    store = _store(tmp_path)
    client = _client(store, tmp_path)
    claimed = client.post(f"/api/epics/v1/{STREAM}/claim", json=_claim_body(process_id=os.getpid()))
    assert claimed.status_code == 200, claimed.text
    # Monitor asked the kernel about this very connection and the holder PID the claim names.
    assert calls == [(("127.0.0.1", 8765), ("127.0.0.1", 80), os.getpid())]
    assert claimed.json()["lease"]["holder"]["process_identity"] == IDENTITY
    read = client.get(f"/api/epics/v1/{STREAM}?limit=1").json()["lease"]
    assert read["holder"]["process_identity"] == IDENTITY
    listed = next(row for row in client.get("/api/epics/v1").json()["streams"] if row["stream_id"] == STREAM)
    assert listed["lease"]["holder"]["process_identity"] == IDENTITY
    assert _stored(store) == (IDENTITY, [IDENTITY])


def test_api_lease_without_the_field_keeps_its_exact_holder_shape(tmp_path):
    """Old lease: no identity, the holder object is byte-identical, and it renews and releases."""
    store = _store(tmp_path)
    client = _client(store, tmp_path)
    lease = client.post(f"/api/epics/v1/{STREAM}/claim", json=_claim_body(process_id=os.getpid())).json()["lease"]
    assert set(lease["holder"]) == OLD_HOLDER_KEYS
    for route, extra in (("heartbeat", {}), ("handoff", {"type": "state", "body": "w", "idempotency_key": "k"})):
        response = client.post(f"/api/epics/v1/{STREAM}/{route}", json={**lease, **extra})
        assert response.status_code == 200, response.text
    assert set(client.get(f"/api/epics/v1/{STREAM}?limit=1").json()["lease"]["holder"]) == OLD_HOLDER_KEYS
    assert client.post(f"/api/epics/v1/{STREAM}/release", json=lease).json()["outcome"] == "released"
    projection, events = _stored(store)
    assert projection is None and set(events) == {None}


@pytest.mark.parametrize("nested", [False, True])
@pytest.mark.parametrize(
    "nominated",
    ["own", "ancestor", "v1:" + "a" * 64, None, "", "v1:" + "A" * 64, 12345, ["v1:" + "a" * 64]],
)
def test_api_claim_refuses_any_client_nominated_identity(tmp_path, monkeypatch, nominated, nested):
    """A claim carrying the field is refused, typed, whatever it holds: a real ancestor's value included."""
    value = {"own": kernel_identity(os.getpid()), "ancestor": kernel_identity(os.getppid())}.get(
        nominated if isinstance(nominated, str) else "", nominated
    )
    calls = _derived(monkeypatch, IDENTITY)
    store = _store(tmp_path)
    client = _client(store, tmp_path)
    body = _claim_body(process_id=os.getpid())
    if nested:
        holder = {key: body.pop(key) for key in [*CLAIM_FIELDS, "process_id"]}
        body["holder"] = {**holder, "process_identity": value}
    else:
        body["process_identity"] = value
    response = client.post(f"/api/epics/v1/{STREAM}/claim", json=body)
    assert response.status_code == 400
    assert response.json()["error"] == "process_identity_nominated"
    assert calls == []
    assert client.get(f"/api/epics/v1/{STREAM}?limit=1").status_code == 404


def test_api_never_populates_or_changes_the_identity_outside_claim(tmp_path, monkeypatch):
    """Fabricated field via the API: renew, fenced write and release ignore any supplied identity."""
    _derived(monkeypatch, IDENTITY)
    store = _store(tmp_path)
    client = _client(store, tmp_path)
    lease = client.post(f"/api/epics/v1/{STREAM}/claim", json=_claim_body(process_id=os.getpid()))
    lease = lease.json()["lease"]
    forged = {**lease, "holder": {**lease["holder"], "process_identity": "v1:" + "f" * 64}}
    heartbeat = client.post(f"/api/epics/v1/{STREAM}/heartbeat", json=forged)
    assert heartbeat.status_code == 200, heartbeat.text
    assert heartbeat.json()["lease"]["holder"].get("process_identity") != "v1:" + "f" * 64
    malformed = {**lease, "holder": {**lease["holder"], "process_identity": "not-an-identity"}}
    handoff = client.post(
        f"/api/epics/v1/{STREAM}/handoff", json={**malformed, "type": "state", "body": "w", "idempotency_key": "k"}
    )
    assert handoff.status_code == 200, handoff.text
    assert client.post(f"/api/epics/v1/{STREAM}/release", json=forged).json()["outcome"] == "released"
    projection, events = _stored(store)
    assert projection == IDENTITY and set(events) == {IDENTITY}


def test_api_replayed_claim_cannot_change_the_identity(tmp_path, monkeypatch):
    store = _store(tmp_path)
    client = _client(store, tmp_path)
    body = _claim_body(process_id=os.getpid())
    _derived(monkeypatch, IDENTITY)
    assert client.post(f"/api/epics/v1/{STREAM}/claim", json=body).json()["outcome"] == "claimed"
    assert client.post(f"/api/epics/v1/{STREAM}/claim", json=body).json()["outcome"] == "replayed"
    for other in ("v1:" + "e" * 64, None):
        _derived(monkeypatch, other)
        assert client.post(f"/api/epics/v1/{STREAM}/claim", json=body).status_code == 409
    assert _stored(store)[0] == IDENTITY


def _raw_claim(base: str, body: dict) -> tuple[int, dict]:
    """POST a claim as any HTTP client would, without the session supervisor."""
    request = urllib.request.Request(
        f"{base}/api/epics/v1/{STREAM}/claim",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(request, timeout=30) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


def test_api_refuses_a_real_ancestor_fingerprint_nominated_by_a_client(tmp_path, monkeypatch):
    """The review probe: a valid kernel identity of an actual ancestor, sent straight to Monitor over HTTP.

    Before this round it was recorded and the sender then proved custody
    (``HELD``). Now the claim is refused, typed, and nothing is recorded; a
    client that claims without the field gets only what the kernel says about
    its own connection.
    """
    store = _store(tmp_path)
    with epics_monitor_stub(store) as base:
        for pid in (os.getpid(), os.getppid()):
            status, payload = _raw_claim(base, _claim_body(process_id=pid, identity=kernel_identity(pid)))
            assert (status, payload["error"]) == (400, "process_identity_nominated")
        assert _stored(store) == (None, [])
        # Without the field, this process names itself as holder; it is not its own parent.
        status, payload = _raw_claim(base, _claim_body(process_id=os.getpid()))
        assert status == 200, payload
        assert "process_identity" not in payload["lease"]["holder"]
        assert _held_here(monkeypatch, base, _authority(payload["lease"])) == "HOLDER_UNPROVEN"
        # A supervisor client that still holds a value never sends it.
        remote.RemoteEpicClient(base=base).release(_envelope(payload["lease"]))
        nominated = LeaseHolder(process_id=os.getpid(), process_identity=kernel_identity(os.getpid()), **CLAIM_FIELDS)
        lease, _ = remote.RemoteEpicClient(base=base).claim(
            stream_id=STREAM, holder=nominated, lineage_id="lineage-r4", session_id="s-2", lease_id="l-2"
        )
        assert lease.holder.process_identity is None
        assert _stored(store)[0] is None


def test_confirmation_refuses_a_lease_its_holder_revived_through_the_real_store(tmp_path, monkeypatch):
    """The review's controlled-clock probe against the real store and Monitor router.

    The lease lapses on Monitor's clock just before the pending record write,
    and its holder revives it through the store before confirmation: same
    generation, holder and identity, new ``heartbeat_at``, ``expires_at`` and
    ``version``. Confirmation refuses, the pending record is removed and the
    task record keeps its prior bytes; an unchanged lease publishes.
    """
    store = _store(tmp_path)
    holder = LeaseHolder(process_id=os.getpid(), process_identity=kernel_identity(os.getpid()), **CLAIM_FIELDS)
    lease, _ = store.claim_remote_session(
        stream_id=STREAM, holder=holder, lineage_id="lineage-r5", ttl_seconds=60, session_id="s-1", lease_id="l-1"
    )
    clock = {"now": utc_now()}
    monkeypatch.setattr(epics_router, "utc_now", lambda: clock["now"])
    record, prior = tmp_path / "record.json", b"prior bytes\n"
    record.write_bytes(prior)
    pending = terminal_abandon.pending_record_path(record)
    with epics_monitor_stub(store) as base:
        monkeypatch.setattr(remote, "DEFAULT_MONITOR", base)
        monitor = remote.RemoteEpicClient(base=base)
        authority = _authority(monitor.stream(STREAM, digest_limit=1)["lease"])
        _, before = terminal_abandon.observe_custody(authority, caller_holds=True)
        write = terminal_abandon._write_pending

        def lapse_write_revive(path, payload):
            clock["now"] = parse_timestamp(lease.expires_at) + timedelta(seconds=1)
            assert monitor.stream(STREAM, digest_limit=1)["lease"]["state"] == "expired"
            write(path, payload)
            revived = store.heartbeat(lease, now=clock["now"])
            assert (revived.generation, revived.fencing_token) == (lease.generation, lease.fencing_token)

        monkeypatch.setattr(terminal_abandon, "_write_pending", lapse_write_revive)
        confirm = functools.partial(terminal_abandon.confirm_custody, authority, before, lambda: None)
        with pytest.raises(terminal_abandon.Refusal) as refused:
            terminal_abandon.publish_record(record, {"published": "while expired"}, confirm)
        assert refused.value.code == "STALE_AUTHORITY"
        assert record.read_bytes() == prior and not pending.exists()
        # Positive control: nothing moved between the observation and the confirmation.
        monkeypatch.setattr(terminal_abandon, "_write_pending", write)
        _, unchanged = terminal_abandon.observe_custody(authority, caller_holds=True)
        confirm = functools.partial(terminal_abandon.confirm_custody, authority, unchanged, lambda: None)
        terminal_abandon.publish_record(record, {"published": "while valid"}, confirm)
        assert json.loads(record.read_bytes()) == {"published": "while valid"} and not pending.exists()


# --- End to end: real supervisor, real Monitor router, real holder and attester processes ---

HOLDER = r"""
import json, subprocess, sys
for line in sys.stdin:
    command = json.loads(line)
    done = subprocess.run(command["argv"], capture_output=True, text=True, env=command["env"], cwd=command["cwd"],
                          timeout=120)
    print(json.dumps({"rc": done.returncode, "out": done.stdout, "err": done.stderr[-4000:]}), flush=True)
"""

ATTEST = r"""
import json, sys
from scripts.api import epics_router
from scripts.fleet import terminal_abandon
from scripts.session_supervisor import remote
remote.DEFAULT_MONITOR = sys.argv[1]
try:
    terminal_abandon.verify_current_custody(json.loads(sys.argv[2]), caller_holds=True)
except terminal_abandon.Refusal as refusal:
    print(refusal.code)
else:
    print("HELD")
"""


class Holder:
    """A long-lived launcher stand-in that runs each command as its own direct child."""

    def __init__(self) -> None:
        self.process = subprocess.Popen(
            [sys.executable, "-c", HOLDER], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, cwd=REPO
        )
        self.pid = self.process.pid

    def run(self, argv: list[str], env: dict[str, str] | None = None) -> dict:
        command = {"argv": argv, "env": {**os.environ, **SPOOFED_ENV, **(env or {})}, "cwd": str(REPO)}
        assert self.process.stdin is not None and self.process.stdout is not None
        self.process.stdin.write(json.dumps(command) + "\n")
        self.process.stdin.flush()
        return json.loads(self.process.stdout.readline())

    def attest(self, base: str, authority: dict) -> str:
        """Attest from the holder's own child: ``HELD`` or the registered refusal code."""
        result = self.run([sys.executable, "-c", ATTEST, base, json.dumps(authority)])
        assert result["rc"] == 0, result["err"]
        return result["out"].strip()

    def claim(self, base: str, *, session: str, lease: str) -> dict:
        """The launcher's own claim: the real supervisor CLI, run as this holder's direct child."""
        argv = [sys.executable, "-m", "scripts.session_supervisor", "claim", "--role", "driver", "--stream", STREAM]
        for flag, value in (("--agent", "codex"), ("--harness", "codex-cli"), ("--instance-id", "codex-holder")):
            argv += [flag, value]
        argv += ["--process-id", str(self.pid), "--lineage-id", "lineage-r4", "--host-id", "api-host"]
        argv += ["--session-id", session, "--lease-id", lease]
        result = self.run(argv, env={"LU_MONITOR_LOOPBACK": base})
        assert result["rc"] == 0, result["err"]
        return json.loads(result["out"])

    def close(self) -> None:
        assert self.process.stdin is not None
        self.process.stdin.close()
        self.process.wait(timeout=30)


@pytest.fixture
def holder():
    started = Holder()
    try:
        yield started
    finally:
        started.close()


@pytest.fixture
def sibling():
    """A second launcher: neither it nor ``holder`` descends from the other."""
    started = Holder()
    try:
        yield started
    finally:
        started.close()


def _v7_database_with_an_old_lease(path: Path, holder_pid: int) -> None:
    """A store as the running fleet has it before migration 0008: one active lease, no identity."""
    now = isoformat_z(utc_now())
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        for migration in load_migrations()[:7]:
            connection.executescript(migration.sql)
            connection.execute(
                "INSERT INTO schema_migrations VALUES (?, ?, ?, ?)",
                (migration.version, migration.name, migration.sha256, now),
            )
        connection.execute("INSERT INTO streams VALUES (?, 'epic', 9999, ?)", (STREAM, now))
        connection.execute(
            "INSERT INTO sessions(session_id, stream_id, state, lineage_id, opened_at, updated_at, closed_at, "
            "state_version, expired_at) VALUES ('s-old', ?, 'open', 'lineage-old', ?, ?, NULL, 1, NULL)",
            (STREAM, now, now),
        )
        event = connection.execute(
            f"INSERT INTO lease_events({_EVENT_COLUMNS}) VALUES (?, 's-old', 'l-old', 1, 1, 'acquired', 'process', "
            "'codex', 'codex-cli', 'codex-holder', NULL, ?, 'api-host', 900, ?, '{}', 'pre-0008 claim')",
            (STREAM, holder_pid, now),
        ).lastrowid
        connection.execute(
            "INSERT INTO stream_leases(stream_id, session_id, lease_id, generation, fencing_token, state, "
            "holder_kind, holder_agent, holder_harness, holder_instance_id, holder_task_id, holder_process_id, "
            "holder_host_id, heartbeat_at, expires_at, ttl_seconds, version, last_event_id) VALUES "
            "(?, 's-old', 'l-old', 1, 1, 'active', 'process', 'codex', 'codex-cli', 'codex-holder', NULL, ?, "
            "'api-host', ?, '2999-01-01T00:00:00Z', 900, 1, ?)",
            (STREAM, holder_pid, now, event),
        )


def _envelope(lease: dict) -> Lease:
    """The launcher's exact-lease envelope, as an old or a new client sends it: no identity."""
    holder = LeaseHolder(
        agent=lease["holder"]["agent"],
        harness=lease["holder"]["harness"],
        instance_id=lease["holder"]["instance_id"],
        process_id=lease["holder"]["process_id"],
        host_id=lease["holder"]["host_id"],
    )
    return Lease(
        stream_id=lease["stream_id"],
        session_id=lease["session_id"],
        lease_id=lease["lease_id"],
        generation=lease["generation"],
        fencing_token=lease["fencing_token"],
        holder=holder,
        heartbeat_at=lease["heartbeat_at"],
        expires_at=lease["expires_at"],
        ttl_seconds=lease["ttl_seconds"],
        version=lease["version"],
    )


def test_migration_of_a_running_fleet_end_to_end(tmp_path, holder, sibling, monkeypatch):
    """Old lease renews and refuses attestation; a new acquisition accepts only its actual holder.

    Including after PID reuse and after the lease is replaced. Every step runs
    through the real Monitor router over HTTP; the claim is the real supervisor
    CLI run as the holder's direct child; each attestation runs in a separate
    process whose ancestry the kernel reports.
    """
    path = tmp_path / "streams.sqlite3"
    _v7_database_with_an_old_lease(path, holder.pid)
    store = SessionStreamStore(SessionStreamDatabase(path))
    # Monitor's startup inventory seed opens the first write connection, which migrates.
    store.database.connect().close()
    assert store.audit()["schema_versions"] == [m.version for m in load_migrations()]
    with epics_monitor_stub(store) as base:
        client = remote.RemoteEpicClient(base=base)

        # 1. The old lease, held by this very holder process, renews through its established path ...
        old = client.stream(STREAM, digest_limit=1)["lease"]
        assert set(old["holder"]) == OLD_HOLDER_KEYS
        renewed = client.heartbeat(_envelope(old))
        assert renewed.generation == 1 and renewed.holder.process_identity is None
        # ... and refuses attestation even from the holder's own child: it records no identity.
        assert holder.attest(base, _authority(old)) == "HOLDER_UNPROVEN"
        client.release(_envelope(old))
        assert _stored(store)[0] is None

        # 2. A new acquisition by the launcher records the launcher's kernel identity.
        holder.claim(base, session="s-new", lease="l-new")
        new = client.stream(STREAM, digest_limit=1)["lease"]
        assert new["generation"] == 2
        assert new["holder"]["process_identity"] == kernel_identity(holder.pid)
        assert holder.attest(base, _authority(new)) == "HELD"
        # The environment copy of the lease held by this test process proves nothing.
        assert _held_here(monkeypatch, base, _authority(new)) == "HOLDER_UNPROVEN"
        # Renewal without the field keeps it, and the holder still proves.
        client.heartbeat(_envelope(new))
        assert _stored(store)[0] == kernel_identity(holder.pid)
        assert holder.attest(base, _authority(new)) == "HELD"

        # 3. Lease replacement: another launcher's generation. The old authority is stale;
        # the previous holder cannot prove the new generation; only its own holder can.
        client.release(_envelope(new))
        sibling.claim(base, session="s-sibling", lease="l-sibling")
        replaced = client.stream(STREAM, digest_limit=1)["lease"]
        assert replaced["generation"] == 3
        assert replaced["holder"]["process_identity"] == kernel_identity(sibling.pid)
        assert holder.attest(base, _authority(new)) == "STALE_AUTHORITY"
        assert sibling.attest(base, _authority(new)) == "STALE_AUTHORITY"
        assert holder.attest(base, _authority(replaced)) == "HOLDER_UNPROVEN"
        assert sibling.attest(base, _authority(replaced)) == "HELD"
        assert _held_here(monkeypatch, base, _authority(replaced)) == "HOLDER_UNPROVEN"

        # 4. PID reuse: a generation recorded for an earlier process with the holder's PID.
        client.release(_envelope(replaced))
        earlier = LeaseHolder(
            process_id=holder.pid, process_identity=kernel_identity(holder.pid, ticks_delta=-1), **CLAIM_FIELDS
        )
        # Written through Monitor's own store: no client can record an identity.
        store.claim_remote_session(
            stream_id=STREAM,
            holder=earlier,
            lineage_id="lineage-r4",
            ttl_seconds=900,
            session_id="s-pid",
            lease_id="l-pid",
        )
        reused = client.stream(STREAM, digest_limit=1)["lease"]
        assert holder.attest(base, _authority(reused)) == "HOLDER_UNPROVEN"
        # Same-generation authority naming another identity is a different custody.
        assert holder.attest(base, _authority(reused) | {"holder": _authority(new)["holder"]}) == "STALE_AUTHORITY"


def test_supervisor_records_no_identity_for_a_holder_that_is_not_its_parent(tmp_path):
    """The real supervisor CLI: Monitor fingerprints only the claim command's own parent."""
    store = _store(tmp_path)
    with epics_monitor_stub(store) as base:
        argv = [sys.executable, "-m", "scripts.session_supervisor", "claim", "--role", "driver", "--stream", STREAM]
        argv += ["--agent", "codex", "--harness", "codex-cli", "--instance-id", "codex-holder"]
        argv += ["--lineage-id", "lineage-r4", "--host-id", "api-host"]
        env = {**os.environ, **SPOOFED_ENV, "LU_MONITOR_LOOPBACK": base}
        for process_id, session in ((os.getppid(), "s-grand"), (FOREIGN_PID, "s-foreign")):
            done = subprocess.run(
                [*argv, "--process-id", str(process_id), "--session-id", session, "--lease-id", f"l-{session}"],
                cwd=REPO,
                env=env,
                capture_output=True,
                text=True,
                timeout=120,
            )
            assert done.returncode == 0, done.stderr
            # Only the capsule reaches stdout (launchers parse it as JSON).
            assert json.loads(done.stdout)["schema"] == "session-supervisor-bootstrap.v1"
            assert _stored(store)[0] is None
            lease = remote.RemoteEpicClient(base=base).stream(STREAM, digest_limit=1)["lease"]
            assert "process_identity" not in lease["holder"]
            remote.RemoteEpicClient(base=base).release(_envelope(lease))
        done = subprocess.run(
            [*argv, "--process-id", str(os.getpid()), "--session-id", "s-parent", "--lease-id", "l-parent"],
            cwd=REPO,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert done.returncode == 0, done.stderr
        assert _stored(store)[0] == kernel_identity(os.getpid())
