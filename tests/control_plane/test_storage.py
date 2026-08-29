"""Phase 0b control-plane storage seam tests (sqlite default; pg fail-closed)."""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path

import pytest

from agents_extensions.shared.session_streams.db import SessionStreamDatabase
from scripts.control_plane.storage import (
    ControlPlanePgConnectError,
    ControlPlanePgDsnMissingError,
    ControlPlaneSqliteRefusedError,
    ControlPlaneStoreUnavailableError,
    StoreId,
    connect,
    resolve_authority,
    sqlite_path,
)
from scripts.fleet_comms.artifacts import ArtifactStore
from scripts.fleet_comms.efficiency_metrics import _connect
from scripts.guardrails.delegate_ownership import OwnershipLedger
from scripts.hygiene import lint_control_plane_sqlite

pytestmark = pytest.mark.repo_invariant

# Unreachable local port — fails closed quickly without DNS (no example.invalid).
_UNREACHABLE_DSN = "postgresql://cp_ci:cp_ci@127.0.0.1:1/postgres"


@pytest.mark.parametrize(
    "store_id",
    [
        StoreId.WRITE_OWNERSHIP,
        StoreId.FLEET_COMMS,
        StoreId.SESSION_STREAMS,
    ],
)
def test_default_authority_is_sqlite(
    store_id: StoreId,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("LEARN_UKRAINIAN_CP_AUTHORITY", raising=False)
    monkeypatch.delenv(f"LEARN_UKRAINIAN_CP_AUTHORITY_{store_id.name}", raising=False)
    assert resolve_authority(store_id).value == "sqlite"


def test_sqlite_path_resolution(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("LEARN_UKRAINIAN_OWNERSHIP_LEDGER", raising=False)
    fleet_path = sqlite_path(StoreId.FLEET_COMMS)
    assert fleet_path.name == "comms.sqlite3"
    assert fleet_path.parent.name == "v1"
    assert fleet_path.parent.parent.name == "fleet-comms"

    streams_path = sqlite_path(StoreId.SESSION_STREAMS)
    assert streams_path.name == "session-streams.sqlite3"
    assert streams_path.parent.name == "v1"
    assert streams_path.parent.parent.name == "session-streams"

    ownership_path = sqlite_path(StoreId.WRITE_OWNERSHIP)
    assert ownership_path.name == "write-ownership.sqlite3"
    assert ownership_path.parent.name == "tasks"

    custom_override = tmp_path / "custom-ledger.sqlite3"
    monkeypatch.setenv("LEARN_UKRAINIAN_OWNERSHIP_LEDGER", str(custom_override))
    assert sqlite_path(StoreId.WRITE_OWNERSHIP) == custom_override.resolve()


def test_ownership_ledger_uses_seam_and_begin_immediate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ledger_path = tmp_path / "write-ownership.sqlite3"
    monkeypatch.setenv("LEARN_UKRAINIAN_OWNERSHIP_LEDGER", str(ledger_path))
    ledger = OwnershipLedger(task_state_dir=tmp_path / "tasks")
    with ledger._connect() as conn:
        assert isinstance(conn, sqlite3.Connection)
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT 1").fetchone()
        assert row is not None
        conn.execute("COMMIT")


@pytest.mark.parametrize(
    ("store_id", "env_suffix"),
    [
        (StoreId.WRITE_OWNERSHIP, "WRITE_OWNERSHIP"),
        (StoreId.FLEET_COMMS, "FLEET_COMMS"),
        (StoreId.SESSION_STREAMS, "SESSION_STREAMS"),
    ],
)
def test_pg_without_dsn_fails_closed_no_sqlite_created(
    store_id: StoreId,
    env_suffix: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(f"LEARN_UKRAINIAN_CP_AUTHORITY_{env_suffix}", "pg")
    monkeypatch.delenv("LEARN_UKRAINIAN_CP_PG_DSN", raising=False)
    target = tmp_path / f"would-not-create-{store_id.value}.sqlite3"
    with pytest.raises(ControlPlanePgDsnMissingError, match=store_id.value):
        connect(store_id, path=target)
    assert not target.exists()


@pytest.mark.parametrize(
    ("store_id", "env_suffix"),
    [
        (StoreId.WRITE_OWNERSHIP, "WRITE_OWNERSHIP"),
        (StoreId.FLEET_COMMS, "FLEET_COMMS"),
        (StoreId.SESSION_STREAMS, "SESSION_STREAMS"),
    ],
)
def test_pg_unreachable_dsn_fails_closed_quickly_no_sqlite(
    store_id: StoreId,
    env_suffix: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(f"LEARN_UKRAINIAN_CP_AUTHORITY_{env_suffix}", "pg")
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_PG_DSN", _UNREACHABLE_DSN)
    target = tmp_path / f"still-not-created-{store_id.value}.sqlite3"
    started = time.monotonic()
    with pytest.raises(ControlPlanePgConnectError, match=store_id.value) as raised:
        connect(store_id, path=target)
    elapsed = time.monotonic() - started
    assert not target.exists()
    assert elapsed < 8.0, f"pg connect must fail closed quickly; took {elapsed:.1f}s"
    message = str(raised.value)
    assert "127.0.0.1" not in message
    assert "cp_ci" not in message
    assert "postgresql://" not in message


def test_artifact_store_pg_unreachable_no_sqlite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_AUTHORITY_FLEET_COMMS", "pg")
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_PG_DSN", _UNREACHABLE_DSN)
    plane_root = tmp_path / "plane"
    started = time.monotonic()
    with pytest.raises(ControlPlanePgConnectError, match="fleet_comms"):
        ArtifactStore(root=plane_root)
    elapsed = time.monotonic() - started
    assert not (plane_root / "comms.sqlite3").exists()
    assert elapsed < 8.0


def test_session_streams_db_pg_unreachable_no_sqlite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_AUTHORITY_SESSION_STREAMS", "pg")
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_PG_DSN", _UNREACHABLE_DSN)
    db_target = tmp_path / "session-streams.sqlite3"
    db = SessionStreamDatabase(path=db_target)
    started = time.monotonic()
    with pytest.raises(ControlPlanePgConnectError, match="session_streams"):
        db.connect()
    elapsed = time.monotonic() - started
    assert not db_target.exists()
    assert elapsed < 8.0


def test_efficiency_metrics_connect_pg_unreachable_no_sqlite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_AUTHORITY_FLEET_COMMS", "pg")
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_PG_DSN", _UNREACHABLE_DSN)
    target = tmp_path / "comms.sqlite3"
    started = time.monotonic()
    with pytest.raises(ControlPlanePgConnectError, match="fleet_comms"):
        with _connect(target):
            pass
    elapsed = time.monotonic() - started
    assert not target.exists()
    assert elapsed < 8.0


def test_control_plane_sqlite_refused_error_still_exported() -> None:
    assert issubclass(ControlPlaneSqliteRefusedError, Exception)


def test_task_index_has_no_sqlite_path() -> None:
    with pytest.raises(ControlPlaneStoreUnavailableError, match="task_index"):
        sqlite_path(StoreId.TASK_INDEX)


def test_control_plane_lint_allowlists_remaining_direct_opens() -> None:
    violations = lint_control_plane_sqlite.find_unallowlisted_connects()
    assert violations == [], f"unallowlisted control-plane sqlite opens: {violations}"


@pytest.mark.parametrize(
    ("target_store", "db_rel_path"),
    [
        ("write_ownership", "batch_state/tasks/write-ownership.sqlite3"),
        ("fleet_comms", "batch_state/fleet-comms/v1/comms.sqlite3"),
        ("session_streams", ".agent/session-streams/v1/session-streams.sqlite3"),
    ],
)
def test_control_plane_lint_detects_new_direct_open(
    target_store: str,
    db_rel_path: str,
    tmp_path: Path,
) -> None:
    scripts = tmp_path / "scripts" / "evil"
    scripts.mkdir(parents=True)
    (scripts / "rogue.py").write_text(
        "\n".join(
            [
                "import sqlite3",
                f"def open_{target_store}():",
                f'    return sqlite3.connect("{db_rel_path}")',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    violations = lint_control_plane_sqlite.find_unallowlisted_connects(repo_root=tmp_path)
    assert len(violations) == 1
    assert Path(db_rel_path).name in violations[0][1]
