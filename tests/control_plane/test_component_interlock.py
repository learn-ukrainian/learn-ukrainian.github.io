"""#7482 Phase 0b interlock: sqlite-shaped components refuse pg at the seam.

Before this interlock, LEARN_UKRAINIAN_CP_AUTHORITY=pg made every non-byte-plane
fleet-comms component fail at arbitrary depth (``BEGIN IMMEDIATE`` syntax
errors, ``UndefinedTable`` 500s) instead of failing closed at construction.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.control_plane.storage import (
    Authority,
    ControlPlaneError,
    ControlPlaneUnsupportedComponentError,
    StoreId,
    assert_component_supported,
)

pytestmark = pytest.mark.repo_invariant

_ENV = "LEARN_UKRAINIAN_CP_AUTHORITY_FLEET_COMMS"


@pytest.fixture(autouse=True)
def _pg_authority(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LEARN_UKRAINIAN_CP_AUTHORITY", raising=False)
    monkeypatch.setenv(_ENV, "pg")
    # A DSN must be present so refusals are attributable to the interlock,
    # never to the missing-DSN fail-closed path.
    monkeypatch.setenv(
        "LEARN_UKRAINIAN_CP_PG_DSN", "postgresql://ci:ci@127.0.0.1:1/refused"
    )


def test_assert_component_supported_refuses_pg_for_sqlite_shaped() -> None:
    with pytest.raises(ControlPlaneUnsupportedComponentError) as exc:
        assert_component_supported(StoreId.FLEET_COMMS, "authority_service")
    msg = str(exc.value)
    assert "authority_service" in msg and "'pg'" in msg
    # OPSEC: store id only — never a DSN fragment or hostname.
    assert "127.0.0.1" not in msg and "postgresql" not in msg


def test_assert_component_supported_unknown_component_fails_closed() -> None:
    with pytest.raises(ControlPlaneError):
        assert_component_supported(StoreId.FLEET_COMMS, "no_such_component")


def test_request_executor_pg_unreachable_fails_closed(tmp_path: Path) -> None:
    """#605: pg construction is allowed; an unreachable DSN fails closed with
    a typed, OPSEC-safe error instead of an interlock refusal."""
    from scripts.control_plane.storage import ControlPlanePgConnectError
    from scripts.fleet_comms.request_executor import RequestExecutor

    with pytest.raises(ControlPlanePgConnectError) as exc:
        RequestExecutor(root=tmp_path)
    msg = str(exc.value)
    assert "fleet_comms" in msg
    assert "127.0.0.1" not in msg and "postgresql" not in msg


def test_message_plane_authority_mode_still_refuses_pg(tmp_path: Path) -> None:
    """#605: live traffic is NOT flipped — authority mode keeps refusing pg
    at the verify_authority_cutover gate."""
    from scripts.fleet_comms.message_plane import (
        AuthorityCutoverRefusedError,
        MessagePlane,
    )

    with pytest.raises(AuthorityCutoverRefusedError) as exc:
        MessagePlane(mode="authority", root=tmp_path)
    assert exc.value.reason_code == "cutover_required_capability_missing"


def test_session_streams_refuses_pg_cleanly(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """#605: session_streams is sqlite-only; the interlock refuses pg at the
    seam before any connection attempt (no DSN required)."""
    from agents_extensions.shared.session_streams.db import SessionStreamDatabase

    monkeypatch.setenv("LEARN_UKRAINIAN_CP_AUTHORITY_SESSION_STREAMS", "pg")
    monkeypatch.delenv("LEARN_UKRAINIAN_CP_PG_DSN", raising=False)
    db_target = tmp_path / "session-streams.sqlite3"
    with pytest.raises(ControlPlaneUnsupportedComponentError) as exc:
        SessionStreamDatabase(path=db_target).connect()
    msg = str(exc.value)
    assert "session_streams" in msg and "'pg'" in msg
    assert not db_target.exists()


def test_plane_status_reports_real_pg_failure_not_component_refusal(tmp_path: Path) -> None:
    from scripts.fleet_comms.message_plane import read_plane_status

    # A stale local sqlite file must NOT be probed as if it were the plane.
    (tmp_path / "comms.sqlite3").write_bytes(b"")
    payload = read_plane_status(root=tmp_path)
    schema = payload.get("schema", payload)
    found = schema.get("db_error") or payload.get("db_error")
    assert found == "pg_probe_failed"
    assert schema["db_exists"] is None
    assert payload["store"]["reachable"] is False


def test_apply_migrations_refuses_non_sqlite_connection() -> None:
    from scripts.fleet_comms.migrations import apply_migrations

    class FakePgConnection:  # duck-typed psycopg stand-in
        pass

    with pytest.raises(ControlPlaneUnsupportedComponentError):
        apply_migrations(FakePgConnection())  # type: ignore[arg-type]


def test_sqlite_authority_still_constructs(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv(_ENV, "sqlite")
    from scripts.fleet_comms.request_executor import RequestExecutor

    with RequestExecutor(root=tmp_path) as executor:
        assert executor.store.authority is Authority.SQLITE


def test_injected_sqlite_store_does_not_bypass_executor_interlock(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """CF r1 (PR #7498): a store OPENED under sqlite must not smuggle sqlite
    SQL into a pg-configured plane via injection."""
    from scripts.fleet_comms.artifacts import ArtifactStore
    from scripts.fleet_comms.request_executor import RequestExecutor

    monkeypatch.setenv(_ENV, "sqlite")
    store = ArtifactStore(root=tmp_path)
    try:
        monkeypatch.setenv(_ENV, "pg")  # authority flips after the store opened
        with pytest.raises(ControlPlaneUnsupportedComponentError):
            RequestExecutor(store=store)
    finally:
        store.close()


def test_injected_executor_does_not_bypass_message_plane_interlock(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from scripts.fleet_comms.message_plane import MessagePlane
    from scripts.fleet_comms.request_executor import RequestExecutor

    monkeypatch.setenv(_ENV, "sqlite")
    executor = RequestExecutor(root=tmp_path)
    try:
        monkeypatch.setenv(_ENV, "pg")
        with pytest.raises(ControlPlaneUnsupportedComponentError):
            MessagePlane(mode="shadow", executor=executor)
    finally:
        executor.close()
