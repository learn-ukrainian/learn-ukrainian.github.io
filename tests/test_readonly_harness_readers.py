"""Read-only harness boundaries preserve exact paths and refuse mutation (#9662)."""

from __future__ import annotations

import ast
import builtins
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from scripts.lib.readonly_sqlite import SQLiteConnection, open_readonly

ROOT = Path(__file__).resolve().parents[1]
READERS = (
    "scripts/agent_runtime/acpx_discuss.py",
    "scripts/ai_agent_bridge/_citation_check.py",
    "scripts/ai_agent_bridge/_inbox_watch.py",
    "scripts/ai_agent_bridge/_opencode.py",
    "scripts/api/fleet_router.py",
    "scripts/api/fleet_workers_collect.py",
    "scripts/api/runtime_router.py",
    "scripts/entire_context/reconcile.py",
    "scripts/entire_context/resolvers.py",
    "scripts/fleet_comms/cold_start_board.py",
    "scripts/fleet_comms/efficiency_metrics.py",
    "scripts/fleet_comms/legacy_broker_report.py",
    "scripts/orchestration/slot_routing.py",
    "scripts/orchestration/task_family/codex_state.py",
    "scripts/review/seeds/score.py",
    "scripts/verification/bench_check_text.py",
    "scripts/verification/check_text.py",
    "scripts/verification/verify_antonenko_citations.py",
    "scripts/verification/vesum.py",
)


@pytest.mark.parametrize("reader", READERS)
@pytest.mark.parametrize("missing", ["scripts", "sqlite3"])
def test_helper_fallback_only_handles_missing_scripts(reader, missing):
    """An internal dependency error must never select the legacy import path."""
    tree = ast.parse((ROOT / reader).read_text())
    block = next(
        node for node in tree.body
        if isinstance(node, ast.Try)
        and any(isinstance(child, ast.ImportFrom) and child.module == "scripts.lib.readonly_sqlite"
                for child in node.body)
    )
    attempted = []

    def controlled_import(name, *args, **kwargs):
        attempted.append(name)
        if name == "scripts.lib.readonly_sqlite":
            raise ModuleNotFoundError(name=missing)
        if name == "lib.readonly_sqlite":
            return SimpleNamespace(
                SQLiteConnection=SQLiteConnection, open_readonly=open_readonly, is_sqlite_connection=object(),
            )
        return builtins.__import__(name, *args, **kwargs)

    namespace = {"__builtins__": {**vars(builtins), "__import__": controlled_import}}
    code = compile(ast.Module(body=[block], type_ignores=[]), reader, "exec")
    if missing == "scripts":
        exec(code, namespace)
        assert namespace["open_readonly"] is open_readonly
        assert attempted == ["scripts.lib.readonly_sqlite", "lib.readonly_sqlite"]
    else:
        with pytest.raises(ModuleNotFoundError) as error:
            exec(code, namespace)
        assert error.value.name == missing
        assert attempted == ["scripts.lib.readonly_sqlite"]


@pytest.mark.parametrize("reader, function", [
    ("scripts/ai_agent_bridge/_inbox_watch.py", "open_readonly_db"),
    ("scripts/fleet_comms/legacy_broker_report.py", "_open_read_only"),
])
def test_reader_opens_exact_file_and_refuses_writes_and_attach(tmp_path, reader, function):
    """Exercise the actual opener without importing unrelated service dependencies."""
    db = tmp_path / "observer?#% evidence.db"
    with closing(sqlite3.connect(db)) as connection:
        connection.execute("CREATE TABLE evidence (value TEXT)")
        connection.execute("INSERT INTO evidence VALUES ('intended')")
        connection.commit()
    before = db.read_bytes()
    tree = ast.parse((ROOT / reader).read_text())
    definition = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == function)
    namespace = {
        "open_readonly": open_readonly, "sqlite3": sqlite3, "SQLiteConnection": SQLiteConnection,
        "Path": Path,
    }
    exec(compile(ast.Module(body=[definition], type_ignores=[]), reader, "exec"), namespace)
    with closing(namespace[function](db)) as connection:
        assert connection.execute("PRAGMA database_list").fetchone()[2] == str(db)
        assert connection.execute("SELECT value FROM evidence").fetchone()[0] == "intended"
        assert connection.execute("PRAGMA query_only").fetchone()[0] == 1
        with pytest.raises(sqlite3.OperationalError):
            connection.execute("INSERT INTO evidence VALUES ('forbidden')")
        # Disabling query_only cannot remove the underlying mode=ro boundary.
        connection.execute("PRAGMA query_only=OFF")
        with pytest.raises(sqlite3.OperationalError):
            connection.execute("CREATE TABLE forbidden (value TEXT)")
        with pytest.raises(sqlite3.DatabaseError):
            connection.execute("ATTACH DATABASE ':memory:' AS attached")
    assert db.read_bytes() == before


def test_dashboard_broker_is_excluded_from_helper_migration():
    reader = "scripts/api/dashboard_comms.py"
    assert reader not in READERS
    tree = ast.parse((ROOT / reader).read_text())
    assert not any(
        isinstance(node, ast.ImportFrom)
        and node.module in {"scripts.lib.readonly_sqlite", "lib.readonly_sqlite"}
        for node in ast.walk(tree)
    )
    manifest = json.loads((ROOT / "scripts/hygiene/sqlite_reference_allowlist.json").read_text())
    entries = [entry for entry in manifest if entry["path"] == reader]
    assert len(entries) == 1
    assert entries[0]["kind"] == "reader_pending_migration_9662"
    assert entries[0]["reference_count"] == 1
    assert entries[0]["calls"] == []


def test_dashboard_broker_routes_through_monitor_context(tmp_path):
    reader = "scripts/api/dashboard_comms.py"
    tree = ast.parse((ROOT / reader).read_text())
    definition = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "get_broker_db"
    )
    db = tmp_path / "broker.db"
    db.touch()
    connection = SimpleNamespace(row_factory=None)
    connect = Mock(return_value=connection)
    resolved = SimpleNamespace(stores=SimpleNamespace(message_db=SimpleNamespace(path=db, connect=connect)))
    resolve_context = Mock(return_value=resolved)
    namespace = {"sqlite3": sqlite3, "resolve_context": resolve_context, "MonitorContext": SimpleNamespace}
    exec(compile(ast.Module(body=[definition], type_ignores=[]), reader, "exec"), namespace)
    context = object()

    assert namespace["get_broker_db"](context) is connection
    resolve_context.assert_called_once_with(context)
    connect.assert_called_once_with(read_only=True)
    assert connection.row_factory is sqlite3.Row
