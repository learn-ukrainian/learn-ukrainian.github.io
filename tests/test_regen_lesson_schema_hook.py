"""Coverage for the lesson-schema pre-commit regeneration path."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest
import yaml
from lu_machinery.pre_commit import product_entry, regen_lesson_schema

from scripts.build import generate_lesson_schema

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def entry_file(tmp_path):
    path = tmp_path / "pre_commit_entry_points.v1.json"
    document = {
        "schema": product_entry.SCHEMA,
        "schema_version": 1,
        "origin": product_entry.ENTRY_POINTS_REL,
        "entry_points": {"test-hook": {"entry_point": "scripts.build.generate_lesson_schema:main", "argv": []}},
    }
    path.write_text(json.dumps(document))
    return path


@pytest.mark.parametrize("name", [None, "sqlite3:main", "scripts.Bad:main", ".scripts.build:main", "scripts/a:main", "scripts.a", "scripts.a:main\n"])
def test_pre_commit_loader_keeps_entry_grammar_refusals(entry_file, name):
    document = json.loads(entry_file.read_text())
    document["entry_points"]["test-hook"]["entry_point"] = name
    entry_file.write_text(json.dumps(document))
    with pytest.raises(product_entry.EntryPointError):
        product_entry.load_entry_point("test-hook", entry_file)


@pytest.mark.parametrize("raw", [
    b"\xff", b"{", b"[]", b"{}",
    (b'{"schema":"learn-ukrainian.pre-commit-entry-points","schema":"learn-ukrainian.pre-commit-entry-points",'
     b'"schema_version":1,"origin":"scripts/build/pre_commit_entry_points.v1.json",'
     b'"entry_points":{"test-hook":{"entry_point":"scripts.build.generate_lesson_schema:main","argv":[]}}}'),
    b'{"number":NaN}', b'{"number":Infinity}',
])
def test_pre_commit_loader_keeps_strict_json_refusals(entry_file, raw):
    entry_file.write_bytes(raw)
    with pytest.raises(product_entry.EntryPointError):
        product_entry.load_entry_point("test-hook", entry_file)


@pytest.mark.parametrize("field,value", [
    ("schema", "wrong"), ("schema_version", True), ("schema_version", 2),
    ("origin", "wrong"), ("entry_points", []), ("extra", 0),
])
def test_pre_commit_loader_keeps_document_refusals(entry_file, field, value):
    document = json.loads(entry_file.read_text())
    document[field] = value
    entry_file.write_text(json.dumps(document))
    with pytest.raises(product_entry.EntryPointError):
        product_entry.load_entry_point("test-hook", entry_file)


@pytest.mark.parametrize("entry", [
    {}, [], {"entry_point": "scripts.build:main", "argv": "bad"},
    {"entry_point": "scripts.build:main", "argv": [1]},
    {"entry_point": "scripts.build:main", "argv": [], "extra": 1},
])
def test_pre_commit_loader_refuses_malformed_siblings(entry_file, entry):
    document = json.loads(entry_file.read_text())
    document["entry_points"]["sibling"] = entry
    entry_file.write_text(json.dumps(document))
    with pytest.raises(product_entry.EntryPointError):
        product_entry.load_entry_point("test-hook", entry_file)


def test_pre_commit_loader_refuses_missing_hook_and_wrong_filename(entry_file):
    with pytest.raises(product_entry.EntryPointError, match="no entry point"):
        product_entry.load_entry_point("missing", entry_file)
    other = entry_file.with_name("wrong.json")
    entry_file.rename(other)
    with pytest.raises(product_entry.EntryPointError, match="origin and file name"):
        product_entry.load_entry_point("test-hook", other)


@pytest.mark.parametrize("kind", ["missing", "directory", "symlink", "oversized", "open-error", "changed", "read-oversized"])
def test_pre_commit_loader_keeps_file_refusals(entry_file, monkeypatch, kind):
    if kind == "oversized":
        entry_file.write_bytes(b" " * (product_entry.MAX_BYTES + 1))
    elif kind == "read-oversized":
        entry_file.write_bytes(b" " * (product_entry.MAX_BYTES + 1))
        original = os.lstat
        monkeypatch.setattr(product_entry.os, "lstat", lambda path: SimpleNamespace(st_mode=original(path).st_mode, st_size=1, st_dev=original(path).st_dev, st_ino=original(path).st_ino))
    elif kind == "changed":
        original_fstat = os.fstat
        monkeypatch.setattr(product_entry.os, "fstat", lambda fd: SimpleNamespace(st_mode=original_fstat(fd).st_mode, st_dev=-1, st_ino=-1))
    elif kind == "open-error":
        def refuse(*args, **kwargs):
            raise PermissionError("refused")
        monkeypatch.setattr(product_entry.os, "open", refuse)
    else:
        entry_file.unlink()
        if kind == "directory":
            entry_file.mkdir()
        elif kind == "symlink":
            target = entry_file.with_suffix(".target")
            target.write_text("{}")
            entry_file.symlink_to(target)
    with pytest.raises(product_entry.EntryPointError):
        product_entry.load_entry_point("test-hook", entry_file)


def test_pre_commit_loader_refuses_foreign_cache(entry_file, monkeypatch, tmp_path):
    entry = product_entry.load_entry_point("test-hook", entry_file)
    monkeypatch.setattr(product_entry, "load_entry_point", lambda hook: entry)
    foreign = ModuleType(entry.module)
    foreign.__file__ = str(tmp_path / "foreign.py")
    monkeypatch.setitem(sys.modules, entry.module, foreign)
    with pytest.raises(ImportError, match="not a file in this checkout"):
        product_entry.run_entry_point("test-hook")


@pytest.mark.parametrize("result", [None, True, "0"])
def test_pre_commit_loader_keeps_integer_result_check(entry_file, monkeypatch, result):
    entry = product_entry.load_entry_point("test-hook", entry_file)
    monkeypatch.setattr(product_entry, "load_entry_point", lambda hook: entry)
    monkeypatch.setattr(generate_lesson_schema, "main", lambda argv: result)
    with pytest.raises(product_entry.EntryPointError, match="not an exit code"):
        product_entry.run_entry_point("test-hook")


@pytest.mark.parametrize("function", [None, 1])
def test_pre_commit_loader_keeps_callable_check(entry_file, monkeypatch, function):
    entry = product_entry.load_entry_point("test-hook", entry_file)
    monkeypatch.setattr(product_entry, "load_entry_point", lambda hook: entry)
    monkeypatch.setattr(generate_lesson_schema, "main", function)
    with pytest.raises(product_entry.EntryPointError, match="has no callable"):
        product_entry.run_entry_point("test-hook")


def _lesson_schema_hook() -> dict[str, object]:
    config = yaml.safe_load((REPO_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
    for repo in config["repos"]:
        for hook in repo["hooks"]:
            if hook["id"] == "lesson-schema-drift":
                return hook
    raise AssertionError("lesson-schema-drift hook is missing")


def test_regen_lesson_schema_uses_canonical_generator(monkeypatch, capsys):
    calls: list[list[str]] = []

    def fake_main(argv: list[str]) -> int:
        calls.append(argv)
        return 0

    monkeypatch.setattr(generate_lesson_schema, "main", fake_main)

    assert regen_lesson_schema.main() == 0
    assert calls == [[]]
    assert capsys.readouterr().out == "Lesson schema written: docs/lesson-schema.yaml\n"


def test_lesson_schema_hook_regenerates_for_all_schema_inputs():
    hook = _lesson_schema_hook()

    assert hook["pass_filenames"] is False
    assert hook["stages"] == ["pre-commit"]
    assert "lu_machinery.pre_commit.regen_lesson_schema" in hook["entry"]
    assert "git diff --exit-code docs/lesson-schema.yaml" in hook["entry"]

    pattern = hook["files"]
    schema_inputs = [
        path.relative_to(REPO_ROOT).as_posix()
        for path in generate_lesson_schema.discover_components(generate_lesson_schema.COMPONENTS_DIR)
    ]
    schema_inputs.extend(
        [
            "scripts/build/generate_lesson_schema.py",
            "scripts/build/lesson_schema_extractor.mjs",
            "scripts/pipeline/config_tables.py",
            "docs/lesson-contract.md",
        ]
    )

    assert all(re.fullmatch(pattern, path) for path in schema_inputs)
    assert not re.fullmatch(pattern, "site/src/pages/index.astro")
