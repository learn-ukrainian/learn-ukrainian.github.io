"""#605 follow-on: request-plane Postgres execute/claim round-trip tests.

``fleet_comms`` authority ``pg``: RequestExecutor create/get/execute/reclaim/
sweep/heartbeat run against Postgres with dialect-aware SQL. Skips (does not
fail) when ``LEARN_UKRAINIAN_CP_PG_DSN`` is unset, matching
``tests/fleet_comms/test_artifacts_pg_byte_plane.py``.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from scripts.control_plane.storage import (
    Authority,
    ControlPlaneUnsupportedComponentError,
)
from scripts.fleet_comms.artifacts import ArtifactStore
from scripts.fleet_comms.message_plane import MessagePlane
from scripts.fleet_comms.request_executor import (
    RequestExecutor,
    RequestExecutorError,
)

pytestmark = pytest.mark.repo_invariant

_PG_DSN_ENV = "LEARN_UKRAINIAN_CP_PG_DSN"
_AUTHORITY_ENV = "LEARN_UKRAINIAN_CP_AUTHORITY_FLEET_COMMS"


def _pg_dsn_or_skip() -> str:
    dsn = (os.environ.get(_PG_DSN_ENV) or "").strip()
    if not dsn:
        pytest.skip(f"{_PG_DSN_ENV} unset/empty — Postgres request-plane test skipped")
    return dsn


@pytest.fixture
def pg_authority(monkeypatch: pytest.MonkeyPatch) -> str:
    dsn = _pg_dsn_or_skip()
    monkeypatch.setenv(_AUTHORITY_ENV, "pg")
    return dsn


@pytest.mark.postgres
def test_create_and_get_request_round_trip(pg_authority: str, tmp_path: Path) -> None:
    root = tmp_path / "plane"
    with RequestExecutor(root=root) as executor:
        assert executor.authority is Authority.PG
        rec = executor.create_request(recipient="codex", body="ping")
        assert rec.state == "queued"
        assert rec.completion_state == "unknown"
        assert rec.requested_recipient == "codex"
        assert rec.resolved_recipient == "codex"

        fetched = executor.get_request(rec.request_id)
        assert fetched == rec

        # The pg request plane never creates a host-local sqlite plane file.
        assert not (root / "comms.sqlite3").exists()

        # Idempotent conversation insert: a second request in the same
        # conversation must not violate the conversation PK.
        second = executor.create_request(
            recipient="codex", body="ping again", conversation_id="conv-605-shared"
        )
        third = executor.create_request(
            recipient="codex", body="ping thrice", conversation_id="conv-605-shared"
        )
        assert second.request_id != third.request_id

    with RequestExecutor(root=root) as executor:
        with pytest.raises(RequestExecutorError, match="request not found"):
            executor.get_request("request-no-such-id")


@pytest.mark.postgres
def test_execute_capture_round_trip(pg_authority: str, tmp_path: Path) -> None:
    """Claim → conformance → artifact → finalize, all on Postgres."""
    with RequestExecutor(root=tmp_path / "plane") as executor:
        rec = executor.create_request(recipient="codex", body="ping")
        done = executor.execute_capture(rec.request_id, adapter="codex", stdout="ok")
        assert done.state in {"complete", "incomplete", "failed"}
        assert done.completion_state != "unknown" or done.state == "incomplete"
        assert done.raw_capture_artifact_id is not None
        assert done.envelope is not None

        # Capture bytes live in Postgres and read back through the store.
        assert executor.store.read_bytes(done.raw_capture_artifact_id)
        # The raw_capture reference row protects the artifact from GC.
        refs = executor.store.connection.execute(
            "SELECT COUNT(*) AS n FROM message_artifacts WHERE artifact_id = %s",
            (done.raw_capture_artifact_id,),
        ).fetchone()
        assert int(refs["n"]) >= 1

        fetched = executor.get_request(rec.request_id)
        assert fetched.state == done.state
        assert fetched.completion_state == done.completion_state

        # A finished request is terminal — not claimable again.
        with pytest.raises(RequestExecutorError, match="not executable"):
            executor.execute_capture(rec.request_id, adapter="codex", stdout="again")


@pytest.mark.postgres
def test_claim_reclaim_touch_and_sweep(pg_authority: str, tmp_path: Path) -> None:
    """#7485/#7504 exactly-once semantics on pg: atomic claim, stale-only
    reclaim, heartbeat protection, and the reconciliation sweep."""
    with RequestExecutor(root=tmp_path / "plane") as executor:
        conn = executor.store.connection
        req = executor.create_request(recipient="codex", body="ping")
        # Simulate a crashed executor: claim without finalizing.
        conn.execute(
            "UPDATE requests SET state = 'running' WHERE request_id = %s",
            (req.request_id,),
        )
        with pytest.raises(RequestExecutorError, match="already claimed"):
            executor.execute_capture(req.request_id, adapter="codex", stdout="ok")
        # A FRESH running claim is never stolen, even with reclaim=True.
        with pytest.raises(RequestExecutorError, match="refusing to steal"):
            executor.execute_capture(
                req.request_id, adapter="codex", stdout="ok", reclaim=True
            )
        # Heartbeat protects a slow-but-alive claimant from the sweep.
        assert executor.touch_claim(req.request_id) is True
        assert executor.requeue_stale_running(stale_after_seconds=60) == []
        assert executor.touch_claim("request-nope") is False
        # A stale claim is swept back to queued, then executes normally.
        conn.execute(
            "UPDATE requests SET updated_at = '2000-01-01T00:00:00Z' WHERE request_id = %s",
            (req.request_id,),
        )
        assert executor.requeue_stale_running(stale_after_seconds=60) == [req.request_id]
        assert executor.get_request(req.request_id).state == "queued"
        done = executor.execute_capture(req.request_id, adapter="codex", stdout="ok")
        assert done.state in {"complete", "incomplete"}


@pytest.mark.postgres
def test_finalize_failure_is_atomic(
    pg_authority: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failure inside finalize must leave NO partial state: request stays
    running (reconcilable via reclaim), no reply row, no reference rows."""
    with RequestExecutor(root=tmp_path / "plane") as executor:
        req = executor.create_request(recipient="codex", body="ping")

        def boom(**_kw: object) -> None:
            raise RuntimeError("induced finalize failure")

        monkeypatch.setattr(executor, "_finalize_capture", boom)
        with pytest.raises(RuntimeError, match="induced finalize failure"):
            executor.execute_capture(req.request_id, adapter="codex", stdout="ok")

        assert executor.get_request(req.request_id).state == "running"
        conn = executor.store.connection
        reply = conn.execute(
            "SELECT 1 FROM comms_messages WHERE kind = 'reply' AND in_reply_to = %s",
            (req.request_message_id,),
        ).fetchone()
        assert reply is None
        refs = conn.execute(
            "SELECT COUNT(*) AS n FROM message_artifacts WHERE message_id = %s",
            (req.request_message_id,),
        ).fetchone()
        assert int(refs["n"]) == 0

        monkeypatch.undo()
        # Production reconciliation: age the claim out, reclaim, finish.
        conn.execute(
            "UPDATE requests SET updated_at = '2000-01-01T00:00:00Z' WHERE request_id = %s",
            (req.request_id,),
        )
        done = executor.execute_capture(
            req.request_id, adapter="codex", stdout="ok", reclaim=True
        )
        assert done.state in {"complete", "incomplete"}


@pytest.mark.postgres
def test_expired_request_expires_on_claim(pg_authority: str, tmp_path: Path) -> None:
    """The expiry path (``_set_state``) is dialect-aware too."""
    with RequestExecutor(root=tmp_path / "plane") as executor:
        rec = executor.create_request(recipient="codex", body="ping", ttl_seconds=-1)
        with pytest.raises(RequestExecutorError, match="expired"):
            executor.execute_capture(rec.request_id, adapter="codex", stdout="ok")
        assert executor.get_request(rec.request_id).state == "expired"


@pytest.mark.postgres
def test_message_plane_open_ask_load_and_parity(pg_authority: str, tmp_path: Path) -> None:
    with MessagePlane(mode="shadow", root=tmp_path / "plane") as plane:
        rec = plane.open_ask(recipient="codex", body="ping from plane")
        assert rec is not None

        loaded = plane.load_request(rec.request_id)
        assert loaded.request_id == rec.request_id

        parity = plane.compute_parity(rec.request_id)
        assert parity.parity_ok
        assert parity.request_state == "queued"

        # shadow mode: the plane never controls legacy writes.
        assert plane.may_mark_legacy_replied(rec.request_id)


@pytest.mark.postgres
def test_injected_pg_store_refused_when_authority_flips_back_to_sqlite(
    pg_authority: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Mismatch guard, reverse direction (#605): a store opened under pg must
    not be driven by an executor once the resolved authority flips to sqlite."""
    store = ArtifactStore(root=tmp_path / "plane")
    try:
        monkeypatch.setenv(_AUTHORITY_ENV, "sqlite")
        with pytest.raises(ControlPlaneUnsupportedComponentError, match="does not match"):
            RequestExecutor(store=store)
    finally:
        store.close()


@pytest.mark.postgres
def test_injected_pg_executor_refused_by_message_plane_under_sqlite(
    pg_authority: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Mismatch guard on MessagePlane (#605): injected pg executor vs
    sqlite-resolved authority refuses at construction."""
    executor = RequestExecutor(root=tmp_path / "plane")
    try:
        monkeypatch.setenv(_AUTHORITY_ENV, "sqlite")
        with pytest.raises(ControlPlaneUnsupportedComponentError, match="does not match"):
            MessagePlane(mode="shadow", executor=executor)
    finally:
        executor.close()
