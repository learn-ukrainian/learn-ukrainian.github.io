"""Byte-compare deterministic Sources handlers to the frozen #8524 golden set."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "sources_golden_set",
    Path(__file__).with_name("sources_golden_set.py"),
)
assert _SPEC is not None and _SPEC.loader is not None
_GOLDEN = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_GOLDEN)


def test_sources_golden_set_matches_frozen_handlers() -> None:
    from wiki.sources_db import SOURCES_DB_PATH

    if not SOURCES_DB_PATH.is_file():
        pytest.skip("local data/sources.db is not in this checkout")
    assert _GOLDEN.canonical_bytes(_GOLDEN.capture()) == _GOLDEN.EXPECTED_PATH.read_bytes()
