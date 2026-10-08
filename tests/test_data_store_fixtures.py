"""Exercise the actual data plugin in isolated pytest processes (#9981)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.storage.topology import StoreBinding

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def _run_plugin(tmp_path: Path, code: str, *, workers: int = 0, required: bool = False):
    (tmp_path / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    (tmp_path / "conftest.py").write_text(
        f"import sys\nsys.path.insert(0, {str(PLUGIN_ROOT)!r})\n"
        "pytest_plugins = ['tests.data_store_fixtures']\n",
        encoding="utf-8",
    )
    (tmp_path / "test_input.py").write_text(code, encoding="utf-8")
    summary = tmp_path / "summary.md"
    summary.write_text("existing summary\n", encoding="utf-8")
    env = {**os.environ, "LU_SOURCES_DB": str(tmp_path / "absent.db"),
           "LU_VESUM_DB": str(tmp_path / "absent.db"), "GITHUB_STEP_SUMMARY": str(summary)}
    env.pop("LU_PYTEST_NEEDS_ARTIFACT_COLLECTED", None)
    command = [sys.executable, "-m", "pytest", "-c", str(tmp_path / "pytest.ini"),
               str(tmp_path / "test_input.py"), "-q"]
    if workers:
        command.extend(["-n", str(workers)])
    if required:
        command.append("--require-data")
    result = subprocess.run(command, cwd=tmp_path, env=env, capture_output=True, text=True, timeout=90)
    return result, summary.read_text(encoding="utf-8")


@pytest.mark.parametrize("workers", [0, 2])
@pytest.mark.parametrize("required", [False, True])
def test_unavailable_inputs_are_visible_and_required_inputs_fail(tmp_path, workers, required):
    result, summary = _run_plugin(tmp_path, '''
import pytest
@pytest.mark.data_tier("sources")
def test_sources():
    pytest.fail("test body ran without sources")
@pytest.mark.data_tier("vesum")
def test_vesum():
    pytest.fail("test body ran without vesum")
def test_factory(data_store_factory):
    data_store_factory("sources")
    pytest.fail("test body ran without sources")
''', workers=workers, required=required)
    assert result.returncode == (1 if required else 0), result.stdout + result.stderr
    assert "data tests not run" in result.stdout
    assert summary.startswith("existing summary\n")
    assert summary.count("### data tests not run") == 1
    for name, store in [("test_sources", "sources"), ("test_vesum", "vesum"), ("test_factory", "sources")]:
        line = f"test_input.py::{name}: store={store} reason=store_missing"
        assert line in result.stdout
        assert summary.count(f"`test_input.py::{name}`: store={store} reason=store_missing") == 1
    assert str(tmp_path) not in summary
    if required:
        assert "2 errors" in result.stdout and "1 failed" in result.stdout
    else:
        assert "3 skipped" in result.stdout


def test_other_skip_keeps_its_message_and_is_visible_under_xdist(tmp_path):
    result, summary = _run_plugin(tmp_path, '''
import pytest
@pytest.mark.data_tier("sources")
@pytest.mark.skip(reason="needs_artifact: fixture deliberately withheld")
def test_artifact(data_store_factory):
    pytest.fail("artifact gate did not run")
''', workers=2, required=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "test_input.py::test_artifact: store=sources reason=needs_artifact" in result.stdout
    assert "reason=needs_artifact" in summary
    assert "reason=store_missing" not in summary


def test_valid_input_runs_and_has_no_not_run_section(tmp_path):
    result, summary = _run_plugin(tmp_path, '''
import sqlite3
from scripts.storage.topology import StoreBinding

def test_valid(data_store_factory, tmp_path):
    path = tmp_path / "input.sqlite"
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE witness (id INTEGER)")
    found = data_store_factory("sources", binding=StoreBinding("sources", path), required_sqlite_tables=("witness",))
    assert found == path
''', workers=2, required=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 passed" in result.stdout
    assert "data tests not run" not in result.stdout
    assert summary == "existing summary\n"


@pytest.mark.parametrize("invalid_kind,reason", [("table", "sqlite_tables_missing:witness"),
                                                ("corrupt", "sqlite_unreadable")])
def test_unusable_sqlite_inputs_have_typed_path_free_reasons(tmp_path, invalid_kind, reason):
    code = '''
import sqlite3
from scripts.storage.topology import StoreBinding

def test_input(data_store_factory, tmp_path):
    path = tmp_path / "input.sqlite"
    if KIND == "table":
        with sqlite3.connect(path) as conn:
            conn.execute("CREATE TABLE unrelated (id INTEGER)")
    else:
        path.write_bytes(b"invalid sqlite")
    data_store_factory("sources", binding=StoreBinding("sources", path), required_sqlite_tables=("witness",))
'''.replace("KIND", repr(invalid_kind))
    result, summary = _run_plugin(tmp_path, code, workers=2)
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"store=sources reason={reason}" in result.stdout
    assert f"store=sources reason={reason}" in summary
    assert "input.sqlite" not in summary


def test_injection_is_resolved_each_call_and_does_not_replace_normal_binding(
    tmp_path, monkeypatch, data_store_factory
):
    from scripts.storage import topology

    calls = []
    actual = topology.resolve_store

    def spy(store, **kwargs):
        calls.append(kwargs.get("binding"))
        return actual(store, **kwargs)

    monkeypatch.setattr(topology, "resolve_store", spy)
    db = tmp_path / "fixture.sqlite"
    import sqlite3
    with sqlite3.connect(db) as connection:
        connection.execute("CREATE TABLE witness (id INTEGER)")
    binding = StoreBinding("sources", db)
    assert data_store_factory("sources", binding=binding) == db
    monkeypatch.setenv("LU_SOURCES_DB", str(tmp_path / "absent.sqlite"))
    with pytest.raises(pytest.skip.Exception, match="store_missing"):
        data_store_factory("sources")
    assert calls == [binding, None]
