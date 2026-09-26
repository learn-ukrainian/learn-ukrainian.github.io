"""Byte-compare deterministic Sources handlers to the frozen #8524 golden set."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "sources_golden_set",
    Path(__file__).with_name("sources_golden_set.py"),
)
assert _SPEC is not None and _SPEC.loader is not None
_GOLDEN = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_GOLDEN)

_UNSTABLE_KEYS = frozenset({
    "entry_id",
    "source_version",
    "canonical_jsonl_sha256",
    "evidence_identifiers",
})
_FINGERPRINT_KEYS = frozenset(_GOLDEN._DICTIONARY_FINGERPRINT_KEYS)


def _assert_compared_payload(value: Any) -> None:
    if isinstance(value, dict):
        assert _UNSTABLE_KEYS.isdisjoint(value)
        if isinstance(value.get("id"), int):
            raise AssertionError("sqlite row id left in the compared payload")
        for item in value.values():
            _assert_compared_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _assert_compared_payload(item)
        return
    if isinstance(value, str):
        assert '"entry_id"' not in value
        assert '"source_version"' not in value
        assert "canonical_jsonl_sha256" not in value


def test_committed_golden_set_stores_hashes_not_dictionary_text() -> None:
    from wiki.sources_db import _fold_dict_key

    raw = _GOLDEN.EXPECTED_PATH.read_text(encoding="utf-8")
    payload = json.loads(raw)
    assert "Прозора, безбарвна рідина" not in raw
    assert "втратив свідомість" not in raw
    _assert_compared_payload(payload)
    for word, tools in payload["per_word"].items():
        fingerprint = tools["search_definitions"]
        assert set(fingerprint) == _FINGERPRINT_KEYS
        assert len(fingerprint["text_sha256"]) == 64
        assert isinstance(fingerprint["text_length"], int)
        assert "search_style_guide" not in tools
        assert "query_cefr_level" in tools
        assert "verify_word" in tools
        if fingerprint["hit_count"]:
            assert _fold_dict_key(fingerprint["headword"]) == _fold_dict_key(word)
    assert set(payload["style_guide"]) == set(_GOLDEN.STYLE_GUIDE_PROBES)
    for probe, fingerprint in payload["style_guide"].items():
        assert set(fingerprint) == _FINGERPRINT_KEYS
        assert fingerprint["hit_count"] >= 1
        assert _fold_dict_key(fingerprint["headword"]) == _fold_dict_key(probe)
        assert len(fingerprint["text_sha256"]) == 64


def test_sources_golden_set_matches_frozen_handlers() -> None:
    from wiki.sources_db import SOURCES_DB_PATH

    from scripts.rag.config import VESUM_DB_PATH

    if not SOURCES_DB_PATH.is_file() or not Path(VESUM_DB_PATH).is_file():
        pytest.skip("local data/sources.db or data/vesum.db is not in this checkout")
    assert _GOLDEN.canonical_bytes(_GOLDEN.capture()) == _GOLDEN.EXPECTED_PATH.read_bytes()
