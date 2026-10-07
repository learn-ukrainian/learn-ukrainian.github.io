"""Narrow false-positive fixes preserve real path and import-access findings."""
import pytest

from scripts.hygiene import lint_source_db_writable_connects as lint


def test_logical_identifiers_and_diagnostics_not_paths():
    for expression in ('f"{rowId} is not in sources.db"', 'f"sqlite://data/vesum.db#{table}"'):
        source = f'rowId = ROOT / "anything"\ntable = "entries"\nmessage = {expression}'
        assert lint.classify_store_source(source, 'scripts/example.py') == []


def test_real_paths_remain_findings():
    for expression in ('ROOT / "data" / "sources.db"', 'ROOT / "data" / "vesum.db"',
                       'f"file:{ROOT}/data/vesum.db?mode=ro"', 'f"{ROOT}/data/sources.db"'):
        assert lint.classify_store_source(f'path = {expression}', 'scripts/example.py')


@pytest.mark.parametrize('source', [
    'from scripts.storage.topology import resolve_store_for_write as writer\nwriter("sources", intent="update")',
    'import scripts.storage.topology as stores\nstores.resolve_store_for_write("vesum", intent="create")',
    'from scripts.storage.topology import resolve_store_for_write\nwriter = resolve_store_for_write\nwriter("sources", intent="update")',
])
def test_aliased_write_resolver_at_collection_is_refused(source):
    assert any(row.kind == 'test_import_access' for row in lint.classify_store_source(source, 'tests/example.py'))


def test_resolver_declaration_does_not_exempt_constructor(tmp_path):
    root = tmp_path
    (root / 'scripts' / 'storage').mkdir(parents=True)
    path = root / 'scripts' / 'storage' / 'topology.py'
    path.write_text('import sqlite3\ndef resolve_store_for_write():\n return sqlite3.connect("other.db")\n')
    entry = lint.AllowedReference('scripts/storage/topology.py', 0, 'store_resolver', None,
                                 'location only', functions=('resolve_store_for_write',))
    violations, _ = lint.find_violations(root, (entry,))
    assert any('constructor reference' in value for value in violations)
