"""Scanner corrections must not hide real store paths or aliased writer calls."""

from scripts.hygiene import lint_source_db_writable_connects as lint


def test_diagnostic_and_logical_label_are_not_store_constructions(tmp_path):
    source = '''
from pathlib import Path
ROOT = Path(__file__).parent
def check(ref, table):
    return f"{ref['rowId']} is not in sources.db", f"sqlite://data/vesum.db#{table}"
'''
    assert lint.classify_store_source(source, str(tmp_path / "example.py")) == []


def test_real_store_paths_and_sqlite_uris_are_still_caught(tmp_path):
    source = '''
from pathlib import Path
ROOT = Path(__file__).parent
database = ROOT / "data" / "vesum.db"
source = f"file:{ROOT}/data/sources.db?mode=rw"
'''
    assert len(lint.classify_store_source(source, str(tmp_path / "example.py"))) == 2


def test_aliased_writer_resolution_is_collection_time_access():
    source = '''
from scripts.storage.topology import resolve_store_for_write as resolve
alias = resolve
binding = alias("sources", intent="update")
'''
    findings = lint.classify_store_source(source, "tests/example.py")
    assert [(f.kind, f.scope) for f in findings] == [("test_import_access", "<module>")]


def test_write_resolver_scope_never_exempts_raw_constructor():
    source = '''
import sqlite3
def resolve_store_for_write():
    return sqlite3.connect("sources.db")
'''
    assert len(lint.classify_source(source, "scripts/storage/topology.py")) == 1


def test_parser_help_does_not_taint_namespace_but_store_defaults_are_found(tmp_path):
    source = '''
import argparse
from pathlib import Path
ROOT = Path(__file__).parent
parser = argparse.ArgumentParser(description="Ingest notes into data/sources.db")
args = parser.parse_args()
text = ROOT / args.book
sample = len(args.items) // 2
'''
    assert lint.classify_store_source(source, str(tmp_path / "source.py")) == []
    source += "parser.add_argument('--db', default=ROOT / 'data' / 'sources.db')\n"
    assert [f.kind for f in lint.classify_store_source(source, str(tmp_path / "source.py"))] == ["store_path"]
