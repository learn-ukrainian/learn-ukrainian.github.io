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
    else:
        assert entry.kind == "reader_pending_migration_9662"
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
    (tmp_path / "tests" / "writer.py").write_text('import sqlite3\nsqlite3.connect("fixture.db")')
    assert lint.find_violations(tmp_path, ()) == ([], [])
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


def test_github_client_cache_is_a_declared_non_source_database():
    entry = next(item for item in lint.load_allowlist() if item.path == "scripts/common/github_client.py")
    assert entry.kind == "writer"
    assert entry.target_db == "GitHub client cache"
    assert "sources.db" not in entry.target_db
    assert "vesum.db" not in entry.target_db
    assert entry.calls == ("sqlite3.connect(path, timeout=5)",)
    source = (REPO_ROOT / entry.path).read_text()
    assert lint.classify_source(source, entry.path)
    assert lint.writer_target_violations(source, entry) == []


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
    assert lint.find_violations(tmp_path, ()) == ([], [])
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
