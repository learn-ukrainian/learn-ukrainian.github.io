"""Read-only harness boundaries preserve exact paths and refuse mutation (#9662)."""

from __future__ import annotations

import ast
import builtins
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
from lu_machinery.common.repo_root import machinery_path
from lu_machinery.lib.readonly_sqlite import SQLiteConnection, open_readonly

ROOT = Path(__file__).resolve().parents[1]
READERS = (
    "scripts/agent_runtime/acpx_discuss.py",
    "scripts/ai_agent_bridge/_citation_check.py",
    "scripts/ai_agent_bridge/_inbox_watch.py",
    "scripts/ai_agent_bridge/_opencode.py",
    "scripts/api/fleet_router.py",
    "scripts/api/fleet_workers_collect.py",
    "scripts/api/runtime_router.py",
    "scripts/fleet_comms/authority.py",
    "scripts/fleet_comms/cold_start_board.py",
    "scripts/fleet_comms/efficiency_metrics.py",
    "scripts/fleet_comms/legacy_broker_report.py",
    "scripts/orchestration/task_family/codex_state.py",
)
# Product readers (scripts/review/integration_check.py and scripts/verification/{bench_check_text,
# check_text,verify_antonenko_citations,vesum}.py) import the installed lu_machinery release
# directly (#13030): it is importable in every flavor, so they hold no fallback block to check.


@pytest.mark.parametrize("reader", READERS)
@pytest.mark.parametrize("missing", ["scripts", "sqlite3"])
def test_helper_fallback_only_handles_missing_scripts(reader, missing):
    """Installed readers propagate missing dependencies instead of selecting a legacy import."""
    source = machinery_path(reader.removeprefix("scripts/")).read_text()
    tree = ast.parse(source)
    imports = [node for node in tree.body if isinstance(node, ast.ImportFrom)
               and node.module == "lu_machinery.lib.readonly_sqlite"]
    assert imports, reader
    attempted = []

    def controlled_import(name, *args, **kwargs):
        attempted.append(name)
        raise ModuleNotFoundError(name=missing)

    namespace = {"__builtins__": {**vars(builtins), "__import__": controlled_import}}
    code = compile(ast.Module(body=imports, type_ignores=[]), reader, "exec")
    with pytest.raises(ModuleNotFoundError) as error:
        exec(code, namespace)
    assert error.value.name == missing
    assert attempted == ["lu_machinery.lib.readonly_sqlite"]


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
    tree = ast.parse((machinery_path(reader.removeprefix("scripts/")) if reader in READERS else ROOT / reader).read_text())
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
