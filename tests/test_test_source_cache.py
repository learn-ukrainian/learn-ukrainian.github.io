"""Regression tests for identity-keyed static source caching."""

from __future__ import annotations

from pathlib import Path

from scripts.ci.test_source_cache import read_test_source


def test_read_test_source_refreshes_after_path_replacement(tmp_path: Path) -> None:
    source_path = tmp_path / "test_sample.py"
    source_path.write_text("value = 'A'\n", encoding="utf-8")
    assert read_test_source(source_path) == "value = 'A'\n"

    source_path.unlink()
    source_path.write_text("value = 'replacement B'\n", encoding="utf-8")

    assert read_test_source(source_path) == "value = 'replacement B'\n"
