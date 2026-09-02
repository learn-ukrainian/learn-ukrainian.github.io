"""#605 public slice: request-plane Postgres round-trip tests.

``fleet_comms`` authority ``pg``: RequestExecutor/MessagePlane create/get
run against Postgres with dialect-aware SQL; execution/claim paths raise a
typed not-implemented error. Skips (does not fail) when
``LEARN_UKRAINIAN_CP_PG_DSN`` is unset, matching
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
def test_sqlite_only_operations_raise_typed_not_implemented(
    pg_authority: str, tmp_path: Path
) -> None:
    with RequestExecutor(root=tmp_path / "plane") as executor:
        rec = executor.create_request(recipient="codex", body="ping")
        with pytest.raises(
            RequestExecutorError,
            match="not implemented for fleet_comms authority=pg in this slice",
        ):
            executor.execute_capture(rec.request_id, adapter="codex", stdout="ok")
        with pytest.raises(
            RequestExecutorError,
            match="not implemented for fleet_comms authority=pg in this slice",
        ):
            executor.requeue_stale_running()
        with pytest.raises(
            RequestExecutorError,
            match="not implemented for fleet_comms authority=pg in this slice",
        ):
            executor.touch_claim(rec.request_id)
        # The refused execute_capture left the request untouched.
        assert executor.get_request(rec.request_id).state == "queued"


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
