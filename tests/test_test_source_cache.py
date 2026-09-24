"""Regression tests for identity-keyed static source caching."""

from __future__ import annotations

import ast
from pathlib import Path

from scripts.ci.test_source_cache import parse_test_source, read_test_source


def test_read_test_source_refreshes_after_path_replacement(tmp_path: Path) -> None:
    source_path = tmp_path / "test_sample.py"
    source_path.write_text("value = 'A'\n", encoding="utf-8")
    assert read_test_source(source_path) == "value = 'A'\n"

    source_path.unlink()
    source_path.write_text("value = 'replacement B'\n", encoding="utf-8")

    assert read_test_source(source_path) == "value = 'replacement B'\n"


def test_parse_test_source_refreshes_after_path_replacement(tmp_path: Path) -> None:
    source_path = tmp_path / "test_sample.py"
    source_path.write_text("value = 'A'\n", encoding="utf-8")
    first_tree = parse_test_source(source_path)
    assert isinstance(first_tree.body[0], ast.Assign)
    assert isinstance(first_tree.body[0].value, ast.Constant)
    assert first_tree.body[0].value.value == "A"

    source_path.unlink()
    source_path.write_text("value = 'replacement B'\n", encoding="utf-8")

    replacement_tree = parse_test_source(source_path)
    assert isinstance(replacement_tree.body[0], ast.Assign)
    assert isinstance(replacement_tree.body[0].value, ast.Constant)
    assert replacement_tree.body[0].value.value == "replacement B"
