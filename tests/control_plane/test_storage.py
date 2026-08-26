"""Phase 0 control-plane storage seam tests (sqlite authority)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from scripts.control_plane.storage import (
    ControlPlanePgDsnMissingError,
    ControlPlaneSqliteRefusedError,
    ControlPlaneStoreUnavailableError,
    StoreId,
    connect,
    resolve_authority,
    sqlite_path,
)
from scripts.guardrails.delegate_ownership import OwnershipLedger
from scripts.hygiene import lint_control_plane_sqlite

pytestmark = pytest.mark.repo_invariant


def test_default_authority_is_sqlite(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LEARN_UKRAINIAN_CP_AUTHORITY", raising=False)
    monkeypatch.delenv("LEARN_UKRAINIAN_CP_AUTHORITY_WRITE_OWNERSHIP", raising=False)
    assert resolve_authority(StoreId.WRITE_OWNERSHIP).value == "sqlite"


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


def test_pg_without_dsn_fails_closed_no_sqlite_created(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_AUTHORITY_WRITE_OWNERSHIP", "pg")
    monkeypatch.delenv("LEARN_UKRAINIAN_CP_PG_DSN", raising=False)
    target = tmp_path / "would-not-create.sqlite3"
    with pytest.raises(ControlPlanePgDsnMissingError, match="write_ownership"):
        connect(StoreId.WRITE_OWNERSHIP, path=target)
    assert not target.exists()


def test_pg_with_dsn_still_refuses_sqlite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_AUTHORITY_WRITE_OWNERSHIP", "pg")
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_PG_DSN", "postgresql://example.invalid/db")
    target = tmp_path / "still-not-created.sqlite3"
    with pytest.raises(ControlPlaneSqliteRefusedError, match="write_ownership"):
        connect(StoreId.WRITE_OWNERSHIP, path=target)
    assert not target.exists()


def test_task_index_has_no_sqlite_path() -> None:
    with pytest.raises(ControlPlaneStoreUnavailableError, match="task_index"):
        sqlite_path(StoreId.TASK_INDEX)


def test_control_plane_lint_allowlists_remaining_direct_opens() -> None:
    violations = lint_control_plane_sqlite.find_unallowlisted_connects()
    assert violations == [], f"unallowlisted control-plane sqlite opens: {violations}"


def test_control_plane_lint_detects_new_direct_open(tmp_path: Path) -> None:
    scripts = tmp_path / "scripts" / "evil"
    scripts.mkdir(parents=True)
    (scripts / "rogue.py").write_text(
        "\n".join(
            [
                "import sqlite3",
                "def open_ledger():",
                '    return sqlite3.connect("batch_state/tasks/write-ownership.sqlite3")',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    violations = lint_control_plane_sqlite.find_unallowlisted_connects(repo_root=tmp_path)
    assert len(violations) == 1
    assert "write-ownership.sqlite3" in violations[0][1]
