"""Public writer entry points preserve transactions and close before lock release."""

import contextlib
import sqlite3

import pytest

from scripts.ingest import dictionary_ingest as writer
from scripts.storage import generations, topology


class Adapter:
    source = "fixture"

    def __init__(self):
        self.connection = None

    def parse(self, text):
        return [text]

    def ensure_schema(self, connection):
        self.connection = connection
        connection.execute("CREATE TABLE IF NOT EXISTS proof(value TEXT)")

    def insert_row(self, connection, row):
        connection.execute("INSERT INTO proof VALUES (?)", (row,))
        return True

    def rebuild_fts(self, connection):
        pass


def test_public_cli_help_exposes_creation_declarations(capsys):
    with pytest.raises(SystemExit) as stopped:
        writer.main(["--help"])
    assert stopped.value.code == 0
    help_text = capsys.readouterr().out
    assert "--db-role {active,staging,shadow}" in help_text
    assert "--create-db" in help_text


def test_public_ingest_requires_declared_creation_and_dry_run_creates_nothing(tmp_path):
    path = tmp_path / "output.db"
    source = tmp_path / "input.txt"
    source.write_text("preserved")
    with pytest.raises(ValueError, match="store_missing"):
        writer.ingest(Adapter(), source, path, dry_run=False, force=False)
    assert not path.exists()
    writer.ingest(Adapter(), source, path, dry_run=True, force=False, db_role="staging", create=True)
    assert not path.exists()
    writer.ingest(Adapter(), source, path, dry_run=False, force=False, db_role="staging", create=True)
    writer.ingest(Adapter(), source, path, dry_run=False, force=False)
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT value FROM proof").fetchall() == [("preserved",), ("preserved",)]


def test_live_writer_connection_closes_before_lock_release(tmp_path, monkeypatch):
    root = tmp_path / "primary"
    (root / ".git").mkdir(parents=True)
    (root / "data").mkdir()
    path = root / "data" / "sources.db"
    sqlite3.connect(path).close()
    source = tmp_path / "input.txt"
    source.write_text("committed")
    monkeypatch.setattr(topology, "live_store_path", lambda: path)
    monkeypatch.setattr(writer, "__file__", str(root / "scripts/ingest/dictionary_ingest.py"))
    adapter = Adapter()

    @contextlib.contextmanager
    def observed(request):
        with generations.store_writer(request) as selected:
            yield selected
            with pytest.raises(sqlite3.ProgrammingError, match="closed"):
                adapter.connection.execute("SELECT 1")
    monkeypatch.setattr(writer, "store_writer", observed)
    writer.ingest(adapter, source, path, dry_run=False, force=False)
    from scripts.lib.readonly_sqlite import open_readonly

    with open_readonly(path) as connection:
        assert connection.execute("SELECT value FROM proof").fetchall() == [("committed",)]
