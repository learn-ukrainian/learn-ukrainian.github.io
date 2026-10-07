"""RB-1 §9 structural SQLite boundary over scripts/ (#9609).

No caller/path dataflow analysis: constructors cannot be referenced outside
explicit writer files and the single tested reader helper. Code built from
strings (exec) is out of scope. Tests build their own fixture DBs; a separate
regression checks the shared pytest hook forbids real data/*.db writable opens.
"""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

import pytest

from scripts.hygiene import lint_source_db_writable_connects as lint

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.repo_wide
def test_repo_has_no_unallowlisted_writable_source_db_connect():
    violations, unreadable = lint.find_violations()
    assert violations == [], "\n".join(violations)
    skipped = subprocess.run(
        ["git", "ls-files", "-t", "--", "scripts"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    ).stdout.splitlines()
    assert set(unreadable) <= {line[2:] for line in skipped if line.startswith("S ")}, unreadable


@pytest.mark.parametrize("entry", lint.load_allowlist(), ids=lambda entry: entry.path)
def test_allowlisted_references_have_pinned_counts_and_declared_targets(entry):
    source = (REPO_ROOT / entry.path).read_text()
    assert len(lint.classify_source(source, entry.path)) == entry.reference_count
    assert entry.reason.strip()
    if entry.kind == "writer":
        assert entry.target_db and entry.calls
        assert lint.writer_target_violations(source, entry) == []
    elif entry.kind == "store_resolver":
        assert entry.path == "scripts/storage/topology.py"
        assert set(entry.functions) == {"resolve_store", "resolve_active_sources_db"}
        assert entry.reference_count == 0
    else:
        assert entry.kind in {"reader_pending_migration_9662", "fixture_factory"}
        assert entry.target_db is None
        calls = [
            ast.unparse(n)
            for n in ast.walk(ast.parse(source))
            if isinstance(n, ast.Call) and ast.unparse(n.func) == "sqlite3.connect"
        ]
        assert calls == list(entry.calls)


FORBIDDEN = (
    [
        f"import {module}\nvalue = {module}.{name}"
        for module in sorted(lint.SQLITE_MODULES)
        for name in sorted(lint.CONSTRUCTORS)
    ]
    + [
        f"import {module} as db\nvalue = db.{name}"
        for module in sorted(lint.SQLITE_MODULES)
        for name in sorted(lint.CONSTRUCTORS)
    ]
    + [
        f"from {module} import {name} as hidden"
        for module in sorted(lint.SQLITE_MODULES)
        for name in sorted(lint.CONSTRUCTORS)
    ]
    + [f"import {module} as db\ngetattr(db, name)" for module in sorted(lint.SQLITE_MODULES)]
    + [
        "from sqlite3 import dbapi2 as db\nfactory = db.Connection",
        "import sqlite3 as db\nfactory = db.dbapi2.connect",
        "import sqlite3 as db\nalias = db\nfactory = alias.dbapi2.Connection",
        'import sqlite3\nfactory = sqlite3.connect\nfactory("other.db")',
        "import sqlite3\nclass Reader(sqlite3.Connection): pass",
        "import sqlite3\ndef reader() -> sqlite3.Connection: pass",
        "import sqlite3\nreader(sqlite3.connect)",
        "import sqlite3\ndef reader(): return sqlite3.connect",
        'import sqlite3\nmodules = [sqlite3]\nmodules[0].connect("other.db")',
        'import sqlite3\nAlias = sqlite3\nAlias.connect("other.db")',
        "from sqlite3 import *",
        "from scripts.lib.readonly_sqlite import sqlite3 as db; db.connect(path)",
        "import anywhere as m; m.sqlite3.connect(path)",
        "import anywhere as m; db = m.sqlite3; db.connect(path)",
        'import sys; sys.modules["sqlite3"].connect(path)',
        'import sys as s; db = s.modules["sqlite3"]; db.connect(path)',
        'import pkgutil; pkgutil.resolve_name("sqlite3:connect")(path)',
        'import pkgutil as p; p.resolve_name("sqlite3:Connection")(path)',
        'from pkgutil import resolve_name as r; r("sqlite3:connect")(path)',
        'import pkgutil; pkgutil.resolve_name("sqli" + "te3:connect")(path)',
        'import importlib\nimportlib.import_module("sqli" + "te3").connect(path)',
        "import importlib\ndb = importlib.import_module(name)\ndb.connect(path)",
        'import importlib\ndb = importlib.import_module("sqlite3")\ndb.Connection(path)',
        'import sqlite3\nconn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)',
        'import sqlite3\nconn = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)',
        'import sqlite3\nconn = sqlite3.connect("cache.db")',
        'import sqlite3\nclass Outer:\n class Reader:\n  def read(self, path="cache.db"):\n   return sqlite3.connect(path)\n Reader = Reader()\nOuter.Reader.read("sources.db")',
    ]
    + [
        f"{loader}({module!r})"
        for loader in ("__import__", "importlib.import_module")
        for module in sorted(lint.SQLITE_MODULES)
    ]
    + [
        'import importlib as loader\nloader.import_module("sqlite3")',
        'from importlib import import_module as loader\nloader("_sqlite3")',
        'from builtins import __import__ as loader\nname = "sqlite3"\nloader(name)',
        'import builtins as loader\nname = "_sqlite3"\nloader.__import__(name)',
    ]
)


@pytest.mark.parametrize("source", FORBIDDEN)
def test_any_constructor_reference_fails_in_injected_scripts(source, tmp_path):
    path = tmp_path / "scripts" / "injected.py"
    path.parent.mkdir()
    path.write_text(source)
    violations, unreadable = lint.find_violations(tmp_path, allowlist=())
    assert unreadable == []
    assert violations and all("scripts/injected.py:" in finding for finding in violations)


@pytest.mark.parametrize(
    "source",
    [
        "import sqlite3\nrow = sqlite3.Row\nraise sqlite3.OperationalError()",
        'import importlib\nmodule = importlib.import_module("json")',
        "from scripts.lib.readonly_sqlite import open_readonly\nconn = open_readonly(path)",
        'def connect(path): pass\nconnect("cache.db")',
        '# sqlite3.connect(path)\nexample = "sqlite3.Connection"',
    ],
)
def test_unrelated_syntax_passes(source):
    assert lint.classify_source(source, "scripts/reader.py") == []


def test_same_line_constructor_references_are_counted_separately():
    assert len(lint.classify_source("import sqlite3\na = sqlite3.connect; b = sqlite3.connect", "scripts/x.py")) == 2
    assert len(lint.classify_source("from sqlite3 import connect, Connection", "scripts/x.py")) == 2


def test_imported_and_assigned_alias_uses_are_references():
    assert len(lint.classify_source("from sqlite3 import connect as c\nc(path)", "scripts/x.py")) == 2
    assert len(lint.classify_source("import sqlite3\nfactory = sqlite3.connect\nfactory(path)", "scripts/x.py")) == 2


@pytest.mark.parametrize("kind", ["writer", "reader_pending_migration_9662"])
def test_new_connect_in_allowlisted_file_fails_even_on_same_line(tmp_path, kind):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    source = 'import sqlite3\nsqlite3.connect("output.db")'
    path = scripts / "existing.py"
    path.write_text(source)
    entry = lint.AllowedReference(
        "scripts/existing.py",
        1,
        kind,
        "output.db" if kind == "writer" else None,
        "synthetic fixture",
        ("sqlite3.connect('output.db')",),
    )
    assert lint.find_violations(tmp_path, (entry,)) == ([], [])
    path.write_text(source + '; sqlite3.connect("sources.db")')
    violations, unreadable = lint.find_violations(tmp_path, (entry,))
    assert unreadable == []
    assert any("pinned 1 references, found 2" in v for v in violations)


def test_writer_retargeting_fails_without_count_increase(tmp_path):
    (tmp_path / "scripts").mkdir()
    path = tmp_path / "scripts" / "writer.py"
    path.write_text('import sqlite3\nsqlite3.connect("sources.db")')
    entry = lint.AllowedReference(
        "scripts/writer.py", 1, "writer", "output.db", "fixture", ("sqlite3.connect('output.db')",)
    )
    assert lint.find_violations(tmp_path, (entry,))[0]


def test_stale_entry_and_unreadable_script_fail(tmp_path):
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "broken.py").write_text("def invalid(")
    entry = lint.AllowedReference("scripts/missing.py", 1, "reader_pending_migration_9662", None, "fixture")
    violations, unreadable = lint.find_violations(tmp_path, (entry,))
    assert violations == ["scripts/missing.py: stale reference allowlist entry"]
    assert unreadable == ["scripts/broken.py"]


def test_tests_are_not_script_exemptions(tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "writer.py").write_text('import sqlite3\ndef factory(tmp_path): return sqlite3.connect(tmp_path / "sources.db")')
    assert lint.find_violations(tmp_path, ()) == ([], [])
    (tmp_path / "tests" / "writer.py").write_text('import sqlite3\ndef read(): return sqlite3.connect("data/sources.db")')
    assert any("raw_store_constructor" in v for v in lint.find_violations(tmp_path, ())[0])
    (tmp_path / "scripts" / "ingest").mkdir(parents=True)
    (tmp_path / "scripts" / "ingest" / "new.py").write_text('import sqlite3\nsqlite3.connect("sources.db")')
    assert lint.find_violations(tmp_path, ())[0]


def test_cli_reports_failures_and_success(monkeypatch, capsys):
    monkeypatch.setattr(lint, "find_violations", lambda: (["scripts/x.py:1: constructor reference"], []))
    assert lint.main([]) == 1
    assert "constructor reference" in capsys.readouterr().err
    monkeypatch.setattr(lint, "find_violations", lambda: ([], []))
    assert lint.main([]) == 0
    assert "OK:" in capsys.readouterr().out


def test_reader_boundary_has_one_open():
    tree = ast.parse((REPO_ROOT / lint.READER_BOUNDARY).read_text())
    assert sum(isinstance(n, ast.Call) and ast.unparse(n.func) == "sqlite3.connect" for n in ast.walk(tree)) == 1


@pytest.mark.parametrize("ignored", [False, True])
def test_scan_includes_untracked_injected_scripts(tmp_path, ignored):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True, timeout=30)
    (tmp_path / "scripts").mkdir()
    if ignored:
        (tmp_path / ".gitignore").write_text("scripts/injected.py\n")
    (tmp_path / "scripts" / "injected.py").write_text('import sqlite3\nsqlite3.connect("sources.db")')
    assert lint.find_violations(tmp_path, ())[0]


def test_allowlist_schema_rejects_duplicates_and_unclassified_entries(tmp_path, monkeypatch):
    import json

    path = tmp_path / "allowlist.json"
    monkeypatch.setattr(lint, "REFERENCE_MANIFEST", path)
    entry = dict(
        path="scripts/x.py", reference_count=1, kind="reader_pending_migration_9662", target_db=None, reason="fixture"
    )
    path.write_text(json.dumps([entry, entry]))
    with pytest.raises(ValueError, match="duplicate"):
        lint.load_allowlist()
    for change in (
        {"kind": "unknown"},
        {"reference_count": 0},
        {"reason": ""},
        {"kind": "writer"},
        {"path": "scripts/../x.py"},
        {"target_db": "sources.db"},
    ):
        path.write_text(json.dumps([{**entry, **change}]))
        with pytest.raises(ValueError, match="invalid"):
            lint.load_allowlist()


# Existing source ingest/build/cache/migration writers; adding one requires an explicit inventory review.
SOURCE_INGEST_BUILD_WRITERS = {
    "scripts/audit/sum11_sovietization_scan.py",
    "scripts/etymology/extract_cognate_forms.py",
    "scripts/etymology/recover_latin_cognates.py",
    "scripts/ingest/antonenko_full_book_ingest.py",
    "scripts/ingest/apply_zno_annotations.py",
    "scripts/ingest/backfill_lesson_sections.py",
    "scripts/ingest/backfill_school_textbook_orphans.py",
    "scripts/ingest/dictionary_ingest.py",
    "scripts/ingest/esum_load.py",
    "scripts/ingest/goroh_etymology_ingest.py",
    "scripts/ingest/incremental_historical_source_ingest.py",
    "scripts/ingest/incremental_textbook_ingest.py",
    "scripts/ingest/ohoiko_books_ingest.py",
    "scripts/ingest/ohoiko_to_jsonl.py",
    "scripts/ingest/ohoiko_verbs_ingest.py",
    "scripts/ingest/owned_books_ingest.py",
    "scripts/ingest/pohribnyi_pronunciation_ingest.py",
    "scripts/ingest/pravopys_2019_ingest.py",
    "scripts/ingest/private_teacher_lessons_ingest.py",
    "scripts/ingest/resource_catalogue_ingest.py",
    "scripts/ingest/slovnyk_me_ingest.py",
    "scripts/ingest/sum20_official_ingest.py",
    "scripts/ingest/sum20_quarantine_unverified.py",
    "scripts/ingest/ua_gec_ingest.py",
    "scripts/ingest/ulp_lesson_notes_ingest.py",
    "scripts/ingest/ulp_to_jsonl.py",
    "scripts/ingest/wiktionary_etymology_ingest.py",
    "scripts/ingest/zno_ingest.py",
    "scripts/lexicon/load_relation_candidates.py",
    "scripts/lexicon/migrate_sum11_sovietization.py",
    "scripts/lexicon/runner/ulif_forms.py",
    "scripts/lexicon/sum20_lookup.py",
    "scripts/lexicon/teacher_deck.py",
    "scripts/lexicon/tools/import_ulif_dump.py",
    "scripts/lexicon/tools/migrate_ulif_raw.py",
    "scripts/migrations/2026-05-15-add-author-uk-to-textbooks.py",
    "scripts/migrations/2026-07-06-add-subject-to-textbooks.py",
    "scripts/projects/open_model_data/phase3_saint_sophia_db_reconciliation.py",
    "scripts/projects/open_model_data/phase3_vspu_db_cutover.py",
    "scripts/rag/migrate_add_literary_source_url.py",
    "scripts/rag/scrape_wikisource.py",
    "scripts/wiki/build_sources_db.py",
    "scripts/wiki/extract_sections.py",
    "scripts/wiki/fetch_wikipedia.py",
    "scripts/wiki/migrate_external_chunks.py",
    "scripts/wiki/restore_literary_metadata.py",
    "scripts/wiki/rollback_sections.py",
    "scripts/wiki/sources_db.py",
    "scripts/wiki/ukrainian_wiki_corpus.py",
}


def test_only_listed_source_ingest_build_writers_declare_protected_databases():
    actual = {
        entry.path
        for entry in lint.load_allowlist()
        if entry.kind == "writer" and any(name in entry.target_db for name in ("sources.db", "vesum.db"))
    }
    assert actual == SOURCE_INGEST_BUILD_WRITERS


def test_migrated_vesum_reader_cannot_switch_to_writable(tmp_path):
    rel_path = "scripts/verification/vesum.py"
    assert rel_path not in {entry.path for entry in lint.load_allowlist()}
    source = (REPO_ROOT / rel_path).read_text()
    path = tmp_path / rel_path
    path.parent.mkdir(parents=True)
    path.write_text(source)
    assert lint.classify_source(source, rel_path) == []
    assert 'open_readonly(resolved_path.resolve(), check_same_thread=False)' in source
    path.write_text(
        source.replace(
            'open_readonly(resolved_path.resolve(), check_same_thread=False)',
            "sqlite3.connect(str(resolved_path))",
        )
    )
    violations, unreadable = lint.find_violations(tmp_path, ())
    assert not unreadable
    assert any("constructor reference" in v for v in violations)


@pytest.mark.parametrize("source", [
    "from pathlib import Path as P\nROOT = P(__file__).parents[1]\ndb = ROOT / 'data' / 'sources.db'",
    "import os\ndb = os.path.join(PROJECT_ROOT, 'data', 'vesum.db')",
    "db = f'{REPO_ROOT}/data/vesum_shadow_release.db'",
    "stem = 'sou'\nother = 'unrelated'\ntail = 'rces.db'\ndb = f'{ROOT}/data/{stem}{tail}'",
    "stem = 'sources'\ndb = f'{ROOT}/data/{stem}.db'",
    "db = ROOT / 'data' / ('sour' + 'ces.db')",
    "db = str(ROOT) + '/data/' + 'sources' + '.db'",
    "import os\ndb = os.environ['LU_VESUM_DB']",
    "import os\ndb = os.getenv('LU_' + 'SOURCES_DB')",
])
@pytest.mark.parametrize("tree", ["scripts", "tests"])
def test_repository_store_construction_forms(source, tree):
    assert any(f.kind == 'store_path' for f in lint.classify_store_source(source, f'{tree}/new.py'))


@pytest.mark.parametrize("source", [
    "import sqlite3\nsqlite3.connect('data/sources.db')",
    "from sqlite3 import connect as c\ndb = REPO_ROOT / 'data' / 'vesum.db'\nc(db)",
    "import sqlite3\nalias = sqlite3\nalias.connect('sources.db')",
    "import sqlite3 as sql\ndb = ROOT / 'data' / 'vesum_shadow_release.db'\nfactory = sql.Connection\nfactory(str(db))",
])
def test_raw_store_constructor_forms(source):
    assert any(f.kind == 'raw_store_constructor' for f in lint.classify_store_source(source, 'scripts/new.py'))


@pytest.mark.parametrize("source", [
    "import sqlite3\nconn = sqlite3.connect('fixture.db')",
    "from scripts.lib.readonly_sqlite import open_readonly as ro\nconn = ro(db)",
    "from scripts.storage.topology import resolve_store as resolve\ndef present(): return resolve('sources')\npytestmark = pytest.mark.skipif(not present(), reason='missing')",
    "from scripts.lib.readonly_sqlite import open_readonly\ndef present(): return open_readonly(db)\n@pytest.mark.skipif(present(), reason='missing')\ndef test_x(): pass",
])
def test_import_access_forms_and_helper_calls(source):
    assert any(f.kind == 'test_import_access' for f in lint.classify_store_source(source, 'tests/new.py'))
    assert not any(f.kind == 'test_import_access' for f in lint.classify_store_source(source, 'scripts/new.py'))


def test_live_collection_helpers_in_base_census():
    import json
    entries = json.loads(lint.BASELINE.read_text())['entries']
    paths = {e['path'] for e in entries if e['kind'] == 'test_import_access'}
    assert {'tests/test_esum_search.py', 'tests/audit/test_antonenko_prose_narrowing.py'} <= paths


def test_baseline_identity_survives_lines_but_counts_occurrences():
    source = "db = ROOT / 'data' / 'sources.db'\ndb = ROOT / 'data' / 'sources.db'"
    original = lint.classify_store_source(source, 'scripts/x.py')
    assert original == lint.classify_store_source('\n# comment\n' + source, 'scripts/x.py')
    assert [f.occurrence for f in original] == [0, 1]


def test_ratchet_rejects_missing_and_new_entries(tmp_path, monkeypatch):
    import json
    (tmp_path / 'tests').mkdir()
    path = tmp_path / 'tests/x.py'
    source = "def test_x(): return ROOT / 'data' / 'sources.db'"
    path.write_text(source)
    baseline = tmp_path / 'baseline.json'
    baseline.write_text(json.dumps({'entries': [f.__dict__ for f in lint.classify_store_source(source, 'tests/x.py')]}))
    monkeypatch.setattr(lint, 'REPO_ROOT', tmp_path)
    monkeypatch.setattr(lint, 'BASELINE', baseline)
    assert lint.find_violations(tmp_path, ()) == ([], [])
    path.write_text(source.replace('sources.db', 'vesum.db'))
    violations, _ = lint.find_violations(tmp_path, ())
    assert any('stale baseline' in v for v in violations)
    assert any('store_path' in v and 'stale' not in v for v in violations)


def test_resolver_allowlist_is_narrow(tmp_path, monkeypatch):
    import json
    path = tmp_path / 'allowlist.json'
    monkeypatch.setattr(lint, 'REFERENCE_MANIFEST', path)
    row = dict(path='scripts/storage/topology.py', reference_count=0, kind='store_resolver',
               target_db=None, reason='sanctioned', functions=['resolve_store'])
    path.write_text(json.dumps([row]))
    assert lint.load_allowlist()[0].functions == ('resolve_store',)
    for change in ({'path': 'scripts/new.py'}, {'functions': ['default_repository_root']},
                   {'calls': ['sqlite3.connect(path)']}, {'reference_count': 1}):
        path.write_text(json.dumps([{**row, **change}]))
        with pytest.raises(ValueError, match='invalid'):
            lint.load_allowlist()


def test_fixture_factory_allowlist_requires_tests_and_pinned_calls(tmp_path, monkeypatch):
    import json
    path = tmp_path / 'allowlist.json'
    monkeypatch.setattr(lint, 'REFERENCE_MANIFEST', path)
    row = dict(path='tests/factory.py', reference_count=1, kind='fixture_factory',
               target_db=None, reason='synthetic', calls=['sqlite3.connect(path)'])
    path.write_text(json.dumps([row]))
    assert lint.load_allowlist()[0].kind == 'fixture_factory'
    for change in ({'path': 'scripts/factory.py'}, {'calls': []}, {'target_db': 'sources.db'}):
        path.write_text(json.dumps([{**row, **change}]))
        with pytest.raises(ValueError, match='invalid'):
            lint.load_allowlist()


@pytest.mark.parametrize("source", [
    "db = tmp_path / 'data/sources.db'",
    "def test_read(checkouts):\n    primary, worker = checkouts\n    return primary / 'data' / 'sources.db'",
    "def test_read(custom_directory): return custom_directory / 'sources.db'",
    "def test_read(tmp_path_factory): return tmp_path_factory.mktemp('db') / 'vesum.db'",
])
def test_fixture_roots_are_not_store_builders(source):
    assert lint.classify_store_source(source, 'tests/new.py') == []


def test_baseline_cannot_grow_or_change_freeze(tmp_path, monkeypatch):
    import json
    from types import SimpleNamespace
    path = tmp_path / 'baseline.json'
    (tmp_path / '.git').mkdir()
    previous = {'base_commit': 'base', 'entries': []}
    path.write_text(json.dumps(previous))
    monkeypatch.setattr(lint, 'REPO_ROOT', tmp_path)
    monkeypatch.setattr(lint, 'BASELINE', path)
    monkeypatch.setattr(lint.subprocess, 'run', lambda *a, **k: SimpleNamespace(
        returncode=0, stdout=json.dumps(previous)))
    assert lint.baseline_policy_violations(tmp_path) == []
    path.write_text(json.dumps({**previous, 'base_commit': 'changed'}))
    assert lint.baseline_policy_violations(tmp_path)
    finding = lint.classify_store_source("db = ROOT / 'data' / 'sources.db'", 'tests/x.py')[0]
    path.write_text(json.dumps({**previous, 'entries': [finding.__dict__]}))
    assert lint.baseline_policy_violations(tmp_path)



def test_resolver_kind_only_exempts_builder_expressions(tmp_path):
    path = tmp_path / 'scripts/storage/topology.py'
    path.parent.mkdir(parents=True)
    source = "def resolve_store(): return ROOT / 'data' / 'sources.db'"
    entry = lint.AllowedReference(str(path.relative_to(tmp_path)), 0, 'store_resolver', None,
                                  'sanctioned', functions=('resolve_store',))
    path.write_text(source)
    assert lint.find_violations(tmp_path, (entry,)) == ([], [])
    path.write_text(source.replace('resolve_store', 'other_function'))
    assert any('store_path' in v for v in lint.find_violations(tmp_path, (entry,))[0])
    path.write_text(source + "\nimport sqlite3\ndef read(): return sqlite3.connect('sources.db')")
    assert any('constructor reference' in v for v in lint.find_violations(tmp_path, (entry,))[0])



def test_fixture_sibling_cannot_hide_repository_path():
    source = "check(ROOT / 'data' / 'sources.db', tmp_path)"
    assert any(f.kind == 'store_path' for f in lint.classify_store_source(source, 'tests/new.py'))
    source = "import sqlite3\ndb = choose(ROOT / 'data' / 'sources.db', tmp_path)\nsqlite3.connect(db)"
    assert any(f.kind == 'raw_store_constructor' for f in lint.classify_store_source(source, 'tests/new.py'))
    assert any(f.kind == 'store_path' for f in lint.classify_store_source("db = Path('data') / 'sources.db'", 'tests/new.py'))


def test_helper_accesses_are_individually_ratcheted():
    source = "from scripts.lib.readonly_sqlite import open_readonly\ndef present():\n    open_readonly(db)\npytestmark = pytest.mark.skipif(present(), reason='missing')"
    before = lint.classify_store_source(source, 'tests/new.py')
    after = lint.classify_store_source(source.replace('    open_readonly(db)',
        '    open_readonly(db)\n    open_readonly(other)'), 'tests/new.py')
    assert len(before) == 1 and len(after) == 2
    assert set(before) < set(after)
    assert before[0].scope == 'present'



def test_cached_base_inputs_do_not_hide_changes_or_removed_entries(tmp_path, monkeypatch):
    import json
    path = tmp_path / 'tests/x.py'
    path.parent.mkdir()
    source = "def read(): return ROOT / 'data' / 'sources.db'"
    path.write_text(source)
    original = lint.classify_store_source
    entry = original(source, 'tests/x.py')[0]
    payload = dict(base_commit='base', file_counts={'tests/x.py': 1}, entries=[entry.__dict__])
    baseline = tmp_path / 'baseline.json'
    baseline.write_text(json.dumps(payload))
    monkeypatch.setattr(lint, 'BASELINE', baseline)
    monkeypatch.setattr(lint, 'REPO_ROOT', tmp_path)
    monkeypatch.setattr(lint, 'base_blob_ids', lambda *args: {'tests/x.py': lint.source_blob_id(source)})
    scans = []
    def counted(source, path):
        scans.append(path)
        return original(source, path)
    monkeypatch.setattr(lint, 'classify_store_source', counted)
    assert lint.find_violations(tmp_path, ()) == ([], [])
    assert scans == []
    baseline.write_text(json.dumps({**payload, 'entries': []}))
    assert lint.find_violations(tmp_path, ())[0]
    assert scans == ['tests/x.py']
    scans.clear()
    baseline.write_text(json.dumps(payload))
    path.write_text(source.replace('sources.db', 'vesum.db'))
    assert lint.find_violations(tmp_path, ())[0]
    assert scans == ['tests/x.py']


def test_base_blob_ids_include_tracked_sparse_paths(tmp_path):
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True, timeout=30)
    path = tmp_path / 'scripts/x.py'
    path.parent.mkdir()
    source = "db = ROOT / 'data' / 'sources.db'\n"
    path.write_text(source)
    subprocess.run(['git', 'add', 'scripts/x.py'], cwd=tmp_path, check=True, timeout=30)
    subprocess.run(['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                    'commit', '-qm', 'Fixture'], cwd=tmp_path, check=True, timeout=30)
    subprocess.run(['git', 'update-index', '--skip-worktree', 'scripts/x.py'], cwd=tmp_path, check=True, timeout=30)
    path.unlink()
    assert lint.base_blob_ids(tmp_path, 'HEAD') == {'scripts/x.py': lint.source_blob_id(source)}
    assert lint.base_blob_ids(tmp_path / 'no-git', 'HEAD') == {}


@pytest.mark.parametrize('source', [
    "from scripts.rag.config import DATA_DIR\nDB = DATA_DIR / 'sources.db'",
    "from scripts.storage.paths import DATA_ROOT\nDB = DATA_ROOT / 'vesum.db'",
    "import os\nDB = os.path.join(DATA_DIR, 'vesum.db')",
    "DB = config.DATA_DIR / 'vesum.db'",
    "DB = helper('data', 'sources.db')",
    "DB = helper('prefix', 'data', 'sources.db')",
    "DB = helper('data', 'sources.db', mode='ro')",
    "DB = _resolve_shared_data_file('data', 'vesum.db')",
    "DB = (ROOT / 'data' / 'x').with_name('sources.db')",
    "DB = anchor.with_name('vesum_shadow_release.db')",
    "DB = (anchor / 'sources').with_suffix('.db')",
    "DB = anchor + '/vesum.db'",
    "DB = data_dir / 'vesum.db'",
])
@pytest.mark.parametrize('tree', ['scripts', 'tests'])
def test_unresolved_store_builders_fail_full_lint(tmp_path, source, tree):
    path = tmp_path / tree / 'new.py'
    path.parent.mkdir()
    path.write_text(source)
    violations, unreadable = lint.find_violations(tmp_path, ())
    assert unreadable == []
    assert any('store_path' in v for v in violations), violations


@pytest.mark.parametrize('expression', [
    "os.path.join(directory, 'data', 'sources.db')",
    "helper(directory, 'data', 'sources.db')",
    "(directory / 'x').with_name('vesum.db')",
    "(directory / 'sources').with_suffix('.db')",
    "str(directory) + '/vesum_shadow_fixture.db'",
])
def test_fixture_store_builders_stay_clean(expression):
    source = f"def test_read(directory):\n    DB = {expression}"
    assert lint.classify_store_source(source, 'tests/new.py') == []


def test_absent_base_scans_every_file_and_rejects_new_builders(tmp_path, monkeypatch):
    import json
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True, timeout=30)
    path = tmp_path / 'tests/x.py'
    path.parent.mkdir()
    path.write_text("DB = DATA_DIR / 'sources.db'")
    baseline = tmp_path / 'baseline.json'
    entries = [f.__dict__ for f in lint.classify_store_source(path.read_text(), 'tests/x.py')]
    baseline.write_text(json.dumps(dict(base_commit='0' * 40, entries=entries,
                                       file_counts={'tests/x.py': 1})))
    monkeypatch.setattr(lint, 'REPO_ROOT', tmp_path)
    monkeypatch.setattr(lint, 'BASELINE', baseline)
    assert lint.base_blob_ids(tmp_path, '0' * 40) == {}
    assert lint.find_violations(tmp_path, ()) == ([], [])
    path.write_text(path.read_text() + "\nDB = helper('data', 'vesum.db')")
    violations, unreadable = lint.find_violations(tmp_path, ())
    assert unreadable == []
    assert len(violations) == 1 and 'store_path' in violations[0]


@pytest.mark.parametrize('path,scope', [
    ('scripts/rag/scrape_wikisource.py', '<module>'),
    ('scripts/build/vocab_gen.py', '<module>'),
    ('scripts/api/admin_router.py', 'disk_usage'),
])
def test_anchor_and_helper_base_sites_are_in_census(path, scope):
    assert any(f.path == path and f.kind == 'store_path' and f.scope == scope
               for f in lint.baseline_entries())


@pytest.mark.parametrize('landed,reproduced', [(False, True), (True, True), (False, False)])
def test_initial_census_correction_requires_unlanded_exact_reproduction(tmp_path, monkeypatch, landed, reproduced):
    import json
    from types import SimpleNamespace
    (tmp_path / '.git').mkdir()
    path = tmp_path / 'baseline.json'
    previous = dict(base_commit='base', entries=[], file_counts={})
    entry = lint.classify_store_source("DB = DATA_DIR / 'sources.db'", 'scripts/x.py')[0].__dict__
    current = dict(base_commit='base', entries=[entry], file_counts={'scripts/x.py': 1})
    path.write_text(json.dumps(current))
    monkeypatch.setattr(lint, 'REPO_ROOT', tmp_path)
    monkeypatch.setattr(lint, 'BASELINE', path)
    def git_run(args, **kwargs):
        return SimpleNamespace(returncode=0, stdout=(
            'tracked baseline' if landed else '') if args[1] == 'ls-tree' else json.dumps(previous))
    monkeypatch.setattr(lint.subprocess, 'run', git_run)
    monkeypatch.setattr(lint, 'census', lambda *args: current if reproduced else previous)
    assert bool(lint.baseline_policy_violations(tmp_path)) == (landed or not reproduced)
    path.write_text(json.dumps({**current, 'base_commit': 'different'}))
    assert lint.baseline_policy_violations(tmp_path)
