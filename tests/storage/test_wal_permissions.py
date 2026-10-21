"""Permission transitions use disposable databases, never repository data."""

from __future__ import annotations

import json
import os
import sqlite3
import stat
import subprocess
import sys
from contextlib import closing
from pathlib import Path

import pytest

from scripts.storage import (
    get_companion_paths,
    hold_database,
    inspect_database_permissions,
    lift_database,
    wal_permissions,
)
from scripts.storage.cli import main


@pytest.fixture
def wal_database(tmp_path):
    db = tmp_path / "example.db"
    with closing(sqlite3.connect(db)) as keeper:
        assert keeper.execute("PRAGMA journal_mode=WAL").fetchone() == ("wal",)
        keeper.execute("CREATE TABLE items (value TEXT)")
        keeper.execute("INSERT INTO items VALUES ('before')")
        keeper.commit()
        assert Path(f"{db}-wal").stat().st_size > 0
        assert Path(f"{db}-shm").is_file()
        try:
            yield db
        finally:
            lift_database(db)


def test_wal_hold_and_lift_modes(wal_database):
    db = wal_database
    expected = [db, Path(f"{db}-wal"), Path(f"{db}-shm")]
    assert get_companion_paths(str(db)) == expected[1:]
    assert hold_database(str(db)) == expected
    assert inspect_database_permissions(db) == {
        str(db): 0o444,
        f"{db}-wal": 0o444,
        f"{db}-shm": 0o444,
        f"{db}-journal": None,
    }
    assert lift_database(db) == expected
    assert inspect_database_permissions(db) == {
        str(db): 0o644,
        f"{db}-wal": 0o644,
        f"{db}-shm": 0o644,
        f"{db}-journal": None,
    }


@pytest.mark.skipif(os.geteuid() == 0, reason="root bypasses POSIX write permission checks")
def test_wal_reads_under_hold_and_writes_only_after_lift(wal_database):
    db = wal_database
    hold_database(db)
    # Use normal connections, without mode=ro or query_only masking chmod failures.
    with closing(sqlite3.connect(db)) as held:
        assert held.execute("SELECT value FROM items").fetchall() == [("before",)]
        with pytest.raises(sqlite3.OperationalError, match="attempt to write a readonly database"):
            held.execute("INSERT INTO items VALUES ('blocked')")
    lift_database(db)
    with closing(sqlite3.connect(db)) as writable:
        writable.execute("INSERT INTO items VALUES ('after')")
        writable.commit()
    with closing(sqlite3.connect(db)) as reader:
        assert reader.execute("SELECT value FROM items ORDER BY rowid").fetchall() == [("before",), ("after",)]


@pytest.mark.parametrize("journal", [False, True])
def test_database_without_wal_companions(tmp_path, journal):
    db = tmp_path / "plain.db"
    with closing(sqlite3.connect(db)) as connection:
        connection.execute("CREATE TABLE items (value INTEGER)")
        connection.commit()
    expected = [db]
    if journal:
        sidecar = Path(f"{db}-journal")
        sidecar.write_bytes(b"isolated journal fixture")
        expected.append(sidecar)
    assert get_companion_paths(db) == expected[1:]
    for operation, mode in ((hold_database, 0o444), (lift_database, 0o644)):
        assert operation(db) == expected
        assert [stat.S_IMODE(path.stat().st_mode) for path in expected] == [mode] * len(expected)
        assert not Path(f"{db}-wal").exists()
        assert not Path(f"{db}-shm").exists()


@pytest.mark.parametrize("operation", [hold_database, lift_database])
def test_missing_database_strict_policy(tmp_path, operation):
    missing = tmp_path / "missing.db"
    with pytest.raises(FileNotFoundError):
        operation(missing)
    assert operation(missing, strict=False) == []
    assert inspect_database_permissions(missing) == {
        str(missing): None,
        f"{missing}-wal": None,
        f"{missing}-shm": None,
        f"{missing}-journal": None,
    }


@pytest.mark.parametrize("operation", [hold_database, lift_database])
def test_missing_database_does_not_modify_orphan_sidecar(tmp_path, operation):
    missing = tmp_path / "missing.db"
    sidecar = Path(f"{missing}-wal")
    sidecar.touch(mode=0o600)
    with pytest.raises(FileNotFoundError):
        operation(missing)
    assert stat.S_IMODE(sidecar.stat().st_mode) == 0o600
    assert operation(missing, strict=False) == [sidecar]


@pytest.mark.parametrize("operation,mode", [(hold_database, 0o444), (lift_database, 0o644)])
@pytest.mark.parametrize("strict", [True, False])
def test_chmod_failure_restores_original_modes(tmp_path, monkeypatch, operation, mode, strict):
    db = tmp_path / "example.db"
    paths = [db, *(Path(f"{db}{suffix}") for suffix in ("-wal", "-shm", "-journal"))]
    for path, original in zip(paths, (0o640, 0o600, 0o400, 0o660), strict=True):
        path.touch()
        path.chmod(original)
    before = inspect_database_permissions(db)
    fchmod = os.fchmod
    failing_inode = paths[-1].stat().st_ino

    def fail_last(fd, requested_mode):
        if os.fstat(fd).st_ino == failing_inode and requested_mode == mode:
            raise PermissionError("injected chmod failure")
        fchmod(fd, requested_mode)

    monkeypatch.setattr(wal_permissions.os, "fchmod", fail_last)
    with pytest.raises(PermissionError, match="injected chmod failure"):
        operation(db, strict=strict)
    assert inspect_database_permissions(db) == before


def test_rollback_failure_is_reported(tmp_path, monkeypatch):
    db = tmp_path / "example.db"
    db.touch(mode=0o600)
    Path(f"{db}-wal").touch(mode=0o600)
    fchmod = os.fchmod
    calls = 0

    def fail_change_and_rollback(fd, mode):
        nonlocal calls
        calls += 1
        if calls > 1:
            raise PermissionError("injected failure")
        fchmod(fd, mode)

    monkeypatch.setattr(wal_permissions.os, "fchmod", fail_change_and_rollback)
    with pytest.raises(ExceptionGroup, match="Permission change and rollback failed") as caught:
        hold_database(db)
    assert len(caught.value.exceptions) == 2
    assert stat.S_IMODE(db.stat().st_mode) == 0o444
    db.chmod(0o600)


@pytest.mark.parametrize("strict", [True, False])
def test_disappearing_companion_policy(tmp_path, monkeypatch, strict):
    db = tmp_path / "example.db"
    db.touch(mode=0o600)
    sidecar = Path(f"{db}-wal")
    sidecar.touch(mode=0o600)
    real_open = os.open

    def missing_sidecar(path, flags):
        if path == sidecar:
            raise FileNotFoundError("disappeared after discovery")
        return real_open(path, flags)

    monkeypatch.setattr(wal_permissions.os, "open", missing_sidecar)
    if strict:
        with pytest.raises(FileNotFoundError, match="disappeared after discovery"):
            hold_database(db)
        assert stat.S_IMODE(db.stat().st_mode) == 0o600
    else:
        assert hold_database(db, strict=False) == [db]


@pytest.mark.parametrize("component", ["db", "wal"])
@pytest.mark.parametrize("kind", ["symlink", "directory", "broken_symlink"])
def test_refuses_non_regular_components_before_changes(tmp_path, component, kind):
    db = tmp_path / "example.db"
    db.touch(mode=0o600)
    target = tmp_path / "unrelated"
    target.touch(mode=0o600)
    path = db if component == "db" else Path(f"{db}-wal")
    if component == "db":
        path.unlink()
    if kind == "directory":
        path.mkdir()
    else:
        path.symlink_to(target if kind == "symlink" else tmp_path / "absent")
    with pytest.raises(OSError):
        hold_database(db)
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    if component == "wal":
        assert stat.S_IMODE(db.stat().st_mode) == 0o600


@pytest.mark.parametrize("command,mode", [("hold", "0444"), ("lift", "0644")])
@pytest.mark.parametrize("json_output", [True, False])
def test_cli_permissions(wal_database, capsys, command, mode, json_output):
    db = wal_database
    assert main([command, str(db), *(["--json"] if json_output else [])]) == 0
    output = capsys.readouterr()
    assert output.err == ""
    expected = {str(db): mode, f"{db}-wal": mode, f"{db}-shm": mode}
    if json_output:
        assert json.loads(output.out) == expected
    else:
        assert output.out.splitlines() == [f"{path}: {mode}" for path in expected]
    assert {path: f"{value:04o}" for path, value in inspect_database_permissions(db).items() if value} == expected


def test_cli_missing_database(tmp_path, capsys):
    assert main(["hold", str(tmp_path / "missing.db"), "--json"]) == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert "hold failed:" in output.err


def test_cli_reports_rollback_failures(tmp_path, monkeypatch, capsys):
    def fail(_):
        raise ExceptionGroup("Permission change and rollback failed", [PermissionError("cannot restore")])

    monkeypatch.setattr("scripts.storage.cli.hold_database", fail)
    assert main(["hold", str(tmp_path / "example.db")]) == 1
    assert "cannot restore" in capsys.readouterr().err


def test_module_entrypoint(tmp_path):
    db = tmp_path / "example.db"
    db.touch()
    result = subprocess.run(
        [sys.executable, "-m", "scripts.storage", "hold", str(db), "--json"],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    assert json.loads(result.stdout) == {str(db): "0444"}
    assert stat.S_IMODE(db.stat().st_mode) == 0o444
