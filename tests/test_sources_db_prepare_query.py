"""Regression tests for scripts/wiki/sources_db.py:_prepare_query.

Bug context: a >255-byte query string (typical for plan-driven textbook
excerpt retrieval) caused Path(query).exists() to raise OSError "File name
too long", which falsely marked textbook references as corpus_missing.
See #1901.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from wiki.sources_db import _prepare_query


def test_long_cyrillic_query_does_not_raise() -> None:
    """A >1 KB Cyrillic query must be treated as a free-text query."""
    long_query = (
        "Караман Grade 10, p.176 Мій ранок Прокидаюся, вмиваюся — "
        "зворотні дієслова та ранкова рутина Діалоги Діалог 1 — Ранкова рутина: "
        "— Коли ти прокидаєшся? — Я прокидаюся о сьомій. — Що ти робиш потім? "
    ) * 6
    assert len(long_query.encode("utf-8")) > 255, "test fixture too short"

    bucket_a, bucket_b, dense = _prepare_query(long_query, track="a1")

    assert isinstance(bucket_a, list)
    assert isinstance(bucket_b, set)
    assert isinstance(dense, str)
    assert dense


def test_existing_path_still_resolved_as_file() -> None:
    """If the query is a real path, the file-as-query branch must still fire."""
    discovery = REPO_ROOT / "curriculum" / "l2-uk-en" / "a1" / "discovery" / "my-morning.yaml"
    if not discovery.exists():
        pytest.skip("discovery fixture missing")

    result = _prepare_query(discovery, track="a1")
    assert result is not None


def test_short_string_query_treated_as_text() -> None:
    """A short string that is not a real path stays a text query."""
    _bucket_a, _bucket_b, dense = _prepare_query("дієслова -ся", track="a1")
    assert dense == "дієслова -ся" or "дієслова" in dense
