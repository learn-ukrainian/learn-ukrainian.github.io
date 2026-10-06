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


@pytest.mark.parametrize("writer", lint.load_allowlist(), ids=lambda writer: writer.path)
def test_allowlisted_writer_opens_only_declared_targets(writer):
    assert writer.target_db.strip() and writer.reason.strip()
    assert writer.calls
    assert lint.writer_target_violations((REPO_ROOT / writer.path).read_text(), writer) == []


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
        'import sqlite3\nfactory = sqlite3.connect\nfactory("other.db")',
        "import sqlite3\nclass Reader(sqlite3.Connection): pass",
        "import sqlite3\ndef reader() -> sqlite3.Connection: pass",
        "import sqlite3\nreader(sqlite3.connect)",
        "import sqlite3\ndef reader(): return sqlite3.connect",
        'import sqlite3\nmodules = [sqlite3]\nmodules[0].connect("other.db")',
        'import sqlite3\nAlias = sqlite3\nAlias.connect("other.db")',
        "from sqlite3 import *",
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


def test_writers_cannot_add_or_retarget_opens():
    writer = lint.AllowedWriter(
        "scripts/writer.py", "output.db", "synthetic fixture writer", ("sqlite3.connect('output.db')",)
    )
    assert lint.writer_target_violations('import sqlite3\nsqlite3.connect("output.db")', writer) == []
    assert (
        lint.writer_target_violations(
            'import sqlite3\nclass Writer(sqlite3.Connection): pass\nsqlite3.connect("output.db")', writer
        )
        == []
    )
    for source in (
        'import sqlite3\nsqlite3.connect("sources.db")',
        'import sqlite3\nsqlite3.connect("output.db")\nsqlite3.connect("other.db")',
        'import sqlite3\nsqlite3.connect("output.db")\nfactory = getattr(sqlite3, "connect")',
        'import sqlite3\nsqlite3.connect("output.db"); factory = sqlite3.connect',
        'import sqlite3\nsqlite3.connect("output.db")\nfactory = sqlite3.Connection',
        'import sqlite3\nsqlite3.connect("output.db")\nsqlite3.Connection("other.db")',
    ):
        assert lint.writer_target_violations(source, writer)


def test_stale_writer_and_unreadable_script_fail(tmp_path):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "broken.py").write_text("def invalid(")
    writer = lint.AllowedWriter("scripts/missing.py", "output.db", "synthetic", ("sqlite3.connect('output.db')",))
    violations, unreadable = lint.find_violations(tmp_path, allowlist=(writer,))
    assert violations == ["scripts/missing.py: stale writer allowlist entry"]
    assert unreadable == ["scripts/broken.py"]


def test_tests_can_build_fixtures_without_becoming_script_exemptions(tmp_path):
    path = tmp_path / "tests" / "writer.py"
    path.parent.mkdir()
    path.write_text('import sqlite3\nsqlite3.connect("fixture.db")')
    assert lint.find_violations(tmp_path, allowlist=()) == ([], [])
    ingest = tmp_path / "scripts" / "ingest" / "unregistered.py"
    ingest.parent.mkdir(parents=True)
    ingest.write_text(path.read_text())
    assert lint.find_violations(tmp_path, allowlist=())[0]


def test_cli_reports_failures_and_success(monkeypatch, capsys):
    monkeypatch.setattr(
        lint, "find_violations", lambda: (["scripts/x.py:1: constructor reference"], ["scripts/broken.py"])
    )
    assert lint.main([]) == 1
    assert "constructor reference" in capsys.readouterr().err
    monkeypatch.setattr(lint, "find_violations", lambda: ([], []))
    assert lint.main([]) == 0
    assert "OK:" in capsys.readouterr().out


def test_reader_boundary_is_the_only_constructor_site():
    tree = ast.parse((REPO_ROOT / lint.READER_BOUNDARY).read_text())
    calls = [
        node for node in ast.walk(tree) if isinstance(node, ast.Call) and ast.unparse(node.func) == "sqlite3.connect"
    ]
    assert len(calls) == 1
