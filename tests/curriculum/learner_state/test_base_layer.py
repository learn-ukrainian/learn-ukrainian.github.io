"""Tests for base layer contract and resolution (issue #8414).

Fixtures are built in test code using tiny synthetic YAML files.
No fixture writes Ukrainian forms beyond placeholders and canonical lemmas
copied from the brief (e.g. 'у' and 'в').
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from scripts.curriculum.learner_state import codes
from scripts.curriculum.learner_state.base_layer import BaseLayerError, resolve_base_ids

pytestmark = pytest.mark.reads_content


def _write_yaml(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def test_base_layer_clean_join(tmp_path: Path) -> None:
    req = {
        "request_schema": 1,
        "level": "a1",
        "words": [
            {"lemma": "base-lemma-1", "pos": "pron", "want": "new"},
            {"lemma": "base-lemma-2", "pos": "prep", "want": "new"},
        ],
    }
    words = {
        "evidence_schema": 1,
        "level": "a1",
        "built_with": {
            "mcp_commit": "0" * 40,
            "sources_db": "0" * 64,
            "vesum": "0" * 64,
            "trie": "0" * 64,
            "ulif_forms": "0" * 64,
        },
        "words": [
            {"id": "W-001", "lemma": "base-lemma-1", "pos": "pron"},
            {"id": "W-002", "lemma": "base-lemma-2", "pos": "prep"},
        ],
    }
    req_path = tmp_path / "_base.request.yaml"
    words_path = tmp_path / "_words.yaml"
    _write_yaml(req_path, req)
    _write_yaml(words_path, words)

    ids = resolve_base_ids("a1", base_request_path=req_path, words_path=words_path)
    assert ids == ("W-001", "W-002")


def test_base_layer_euphonic_variants_u_and_v(tmp_path: Path) -> None:
    """VESUM treats euphonic partners as separate lemmas: у and в both pass."""
    req = {
        "request_schema": 1,
        "level": "a1",
        "words": [
            {"lemma": "у", "pos": "prep", "want": "new", "note": "preposition"},
            {"lemma": "в", "pos": "prep", "want": "new", "note": "euphonic partner of у"},
        ],
    }
    words = {
        "evidence_schema": 1,
        "level": "a1",
        "built_with": {
            "mcp_commit": "0" * 40,
            "sources_db": "0" * 64,
            "vesum": "0" * 64,
            "trie": "0" * 64,
            "ulif_forms": "0" * 64,
        },
        "words": [
            {"id": "W-010", "lemma": "у", "pos": "prep"},
            {"id": "W-020", "lemma": "в", "pos": "prep"},
        ],
    }
    req_path = tmp_path / "_base.request.yaml"
    words_path = tmp_path / "_words.yaml"
    _write_yaml(req_path, req)
    _write_yaml(words_path, words)

    ids = resolve_base_ids("a1", base_request_path=req_path, words_path=words_path)
    assert ids == ("W-010", "W-020")


def test_base_layer_disambiguation_with_entry(tmp_path: Path) -> None:
    """When word store has multiple records for (lemma, pos), entry is required to disambiguate."""
    req = {
        "request_schema": 1,
        "level": "a1",
        "words": [
            {
                "lemma": "ambig-word",
                "pos": "noun",
                "entry": {"source": "vesum", "entry_id": 42},
                "want": "new",
            }
        ],
    }
    words = {
        "evidence_schema": 1,
        "level": "a1",
        "built_with": {
            "mcp_commit": "0" * 40,
            "sources_db": "0" * 64,
            "vesum": "0" * 64,
            "trie": "0" * 64,
            "ulif_forms": "0" * 64,
        },
        "words": [
            {"id": "W-001", "lemma": "ambig-word", "pos": "noun", "entry": {"source": "vesum", "entry_id": 42}},
            {"id": "W-002", "lemma": "ambig-word", "pos": "noun", "entry": {"source": "vesum", "entry_id": 99}},
        ],
    }
    req_path = tmp_path / "_base.request.yaml"
    words_path = tmp_path / "_words.yaml"
    _write_yaml(req_path, req)
    _write_yaml(words_path, words)

    ids = resolve_base_ids("a1", base_request_path=req_path, words_path=words_path)
    assert ids == ("W-001",)


def test_base_layer_unresolved_when_multiple_matches_without_entry(tmp_path: Path) -> None:
    req = {
        "request_schema": 1,
        "level": "a1",
        "words": [{"lemma": "ambig-word", "pos": "noun", "want": "new"}],
    }
    words = {
        "evidence_schema": 1,
        "level": "a1",
        "built_with": {
            "mcp_commit": "0" * 40,
            "sources_db": "0" * 64,
            "vesum": "0" * 64,
            "trie": "0" * 64,
            "ulif_forms": "0" * 64,
        },
        "words": [
            {"id": "W-001", "lemma": "ambig-word", "pos": "noun", "entry": {"source": "vesum", "entry_id": 42}},
            {"id": "W-002", "lemma": "ambig-word", "pos": "noun", "entry": {"source": "vesum", "entry_id": 99}},
        ],
    }
    req_path = tmp_path / "_base.request.yaml"
    words_path = tmp_path / "_words.yaml"
    _write_yaml(req_path, req)
    _write_yaml(words_path, words)

    with pytest.raises(BaseLayerError) as exc_info:
        resolve_base_ids("a1", base_request_path=req_path, words_path=words_path)
    assert exc_info.value.code == codes.BASE_LAYER_UNRESOLVED
    assert "matched 2 records" in exc_info.value.message


def test_base_layer_unresolved_when_zero_matches(tmp_path: Path) -> None:
    req = {
        "request_schema": 1,
        "level": "a1",
        "words": [{"lemma": "missing-word", "pos": "noun", "want": "new"}],
    }
    words = {
        "evidence_schema": 1,
        "level": "a1",
        "built_with": {
            "mcp_commit": "0" * 40,
            "sources_db": "0" * 64,
            "vesum": "0" * 64,
            "trie": "0" * 64,
            "ulif_forms": "0" * 64,
        },
        "words": [
            {"id": "W-001", "lemma": "other-word", "pos": "noun"},
        ],
    }
    req_path = tmp_path / "_base.request.yaml"
    words_path = tmp_path / "_words.yaml"
    _write_yaml(req_path, req)
    _write_yaml(words_path, words)

    with pytest.raises(BaseLayerError) as exc_info:
        resolve_base_ids("a1", base_request_path=req_path, words_path=words_path)
    assert exc_info.value.code == codes.BASE_LAYER_UNRESOLVED
    assert "matched 0 records" in exc_info.value.message


def test_base_layer_missing_when_request_file_not_found(tmp_path: Path) -> None:
    req_path = tmp_path / "_base.request.yaml"
    words_path = tmp_path / "_words.yaml"
    _write_yaml(words_path, {"words": []})

    with pytest.raises(BaseLayerError) as exc_info:
        resolve_base_ids("a1", base_request_path=req_path, words_path=words_path)
    assert exc_info.value.code == codes.BASE_LAYER_MISSING


def test_base_layer_missing_when_words_file_not_found(tmp_path: Path) -> None:
    req_path = tmp_path / "_base.request.yaml"
    words_path = tmp_path / "_words.yaml"
    _write_yaml(req_path, {"words": [{"lemma": "x", "pos": "y", "want": "new"}]})

    with pytest.raises(BaseLayerError) as exc_info:
        resolve_base_ids("a1", base_request_path=req_path, words_path=words_path)
    assert exc_info.value.code == codes.BASE_LAYER_MISSING


def test_base_layer_missing_when_request_has_empty_words(tmp_path: Path) -> None:
    req_path = tmp_path / "_base.request.yaml"
    words_path = tmp_path / "_words.yaml"
    _write_yaml(req_path, {"request_schema": 1, "level": "a1", "words": []})
    _write_yaml(words_path, {"evidence_schema": 1, "level": "a1", "words": []})

    with pytest.raises(BaseLayerError) as exc_info:
        resolve_base_ids("a1", base_request_path=req_path, words_path=words_path)
    assert exc_info.value.code == codes.BASE_LAYER_MISSING


def test_base_layer_fails_on_bare_lemma_id(tmp_path: Path) -> None:
    req = {
        "request_schema": 1,
        "level": "a1",
        "words": [{"lemma": "bare-test", "pos": "noun", "want": "new"}],
    }
    words = {
        "evidence_schema": 1,
        "level": "a1",
        "built_with": {
            "mcp_commit": "0" * 40,
            "sources_db": "0" * 64,
            "vesum": "0" * 64,
            "trie": "0" * 64,
            "ulif_forms": "0" * 64,
        },
        "words": [
            {"id": "bare_lemma_instead_of_id", "lemma": "bare-test", "pos": "noun"},
        ],
    }
    req_path = tmp_path / "_base.request.yaml"
    words_path = tmp_path / "_words.yaml"
    _write_yaml(req_path, req)
    _write_yaml(words_path, words)

    with pytest.raises(BaseLayerError) as exc_info:
        resolve_base_ids("a1", base_request_path=req_path, words_path=words_path)
    assert exc_info.value.code == codes.BARE_LEMMA
