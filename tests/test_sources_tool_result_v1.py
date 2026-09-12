"""Contract tests for sources.tool-result.v1 envelopes (#7954)."""

from __future__ import annotations

import asyncio
import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from learn_ukrainian_v4_runtime.tool_result_envelope import (
    SCHEMA_V1,
    build_search_envelope,
    disposition_to_status,
    enrich_typed_outcome,
)
from learn_ukrainian_v4_runtime.v4_canonical_authority_store import immutable_evidence_identifier
from learn_ukrainian_v4_runtime.vesum_presentation import tag_gloss

SOURCES_SERVER_PATH = Path(__file__).resolve().parents[1] / ".mcp" / "servers" / "sources" / "server.py"
VESUM_FIXTURE_VERSION = "a" * 64
SYNII_FIXTURE = Path(__file__).parent / "fixtures" / "vesum_synii_analyses.json"
SYNII_SHA256 = "df5b93dcc2f4e2f882d6cfb3e08c93ae9eeb61fba34fd75987e832a620c9a0b4"


@pytest.fixture
def synii_matches():
    payload = SYNII_FIXTURE.read_bytes()
    assert hashlib.sha256(payload).hexdigest() == SYNII_SHA256
    return json.loads(payload)["matches"]


@pytest.fixture
def server_module():
    """Import the server module fresh."""
    spec = importlib.util.spec_from_file_location("sources_server_v1", SOURCES_SERVER_PATH)
    srv = importlib.util.module_from_spec(spec)
    sys.modules["sources_server_v1"] = srv
    assert spec.loader is not None
    spec.loader.exec_module(srv)
    return srv


def _run(coro):
    return asyncio.run(coro)


class TestEnvelopeHelpers:
    def test_disposition_mapping(self):
        assert disposition_to_status("supported") == "ok"
        assert disposition_to_status("partial") == "ok"
        assert disposition_to_status("not_found") == "empty"
        assert disposition_to_status("negative") == "empty"
        assert disposition_to_status("ambiguous") == "error"
        assert disposition_to_status("invalid_input") == "error"

    def test_enrich_preserves_authority_keys(self):
        outcome = {
            "tool": "verify_word",
            "disposition": "supported",
            "success": True,
            "evidence_identifiers": ["vesum:abc"],
            "result": {"word": "читай", "matches": [{"lemma": "читати"}]},
        }
        enrich_typed_outcome(
            outcome,
            query={"word": "читай"},
            match_count=1,
            hits=[{"lemma": "читати"}],
            summary_prose="prose",
        )
        assert outcome["schema"] == SCHEMA_V1
        assert outcome["status"] == "ok"
        assert outcome["match_count"] == 1
        assert outcome["disposition"] == "supported"
        assert outcome["success"] is True
        assert outcome["evidence_identifiers"] == ["vesum:abc"]
        assert outcome["result"]["word"] == "читай"

    def test_enrich_rejects_count_mismatch(self):
        outcome = {
            "tool": "verify_word",
            "disposition": "supported",
            "success": True,
            "evidence_identifiers": [],
        }
        with pytest.raises(ValueError):
            enrich_typed_outcome(outcome, query={}, match_count=1, hits=[], summary_prose="")

    def test_search_envelope_empty(self):
        env = build_search_envelope(
            tool="search_text", query={"query": "xyz"}, hits=[], summary_prose="No results found."
        )
        assert env["schema"] == SCHEMA_V1
        assert env["status"] == "empty"
        assert env["match_count"] == 0
        assert env["hits"] == []

    def test_partial_zero_hits_is_empty_status(self):
        outcome = {
            "tool": "verify_words",
            "disposition": "partial",
            "success": False,
            "evidence_identifiers": [],
            "result": {"found": 0},
        }
        enrich_typed_outcome(outcome, query={"words": ["a"]}, match_count=0, hits=[], summary_prose="none")
        assert outcome["disposition"] == "partial"
        assert outcome["status"] == "empty"
        assert outcome["match_count"] == 0


class TestVerifyWordEnvelope:
    def test_found_exposes_integer_match_count(self, server_module, monkeypatch):
        monkeypatch.setattr(server_module, "_vesum_source_version", lambda: VESUM_FIXTURE_VERSION)
        mock_matches = [
            {"lemma": "читати", "pos": "verb", "tags": "verb:imperf:inf"},
            {"lemma": "читати", "pos": "verb", "tags": "verb:imperf:pres:s:3"},
        ]
        with patch("scripts.verification.vesum.verify_word", return_value=mock_matches):
            content, outcome = _run(server_module.handle_verify_word({"word": "читай"}))
        assert outcome["schema"] == SCHEMA_V1
        assert outcome["status"] == "ok"
        assert outcome["match_count"] == 2
        assert isinstance(outcome["match_count"], int)
        assert len(outcome["hits"]) == 2
        assert outcome["disposition"] == "supported"
        assert "читай" in content[0].text
        assert outcome["summary_prose"] == content[0].text

    def test_miss_is_empty_envelope(self, server_module):
        with patch("scripts.verification.vesum.verify_word", return_value=[]):
            content, outcome = _run(server_module.handle_verify_word({"word": "взяйте"}))
        assert outcome["schema"] == SCHEMA_V1
        assert outcome["status"] == "empty"
        assert outcome["match_count"] == 0
        assert outcome["hits"] == []
        assert outcome["disposition"] == "not_found"
        assert "NOT FOUND" in content[0].text

    def test_verify_words_all_missing_is_empty_status(self, server_module):
        with patch("scripts.verification.vesum.verify_words", return_value={"а": [], "б": []}):
            content, outcome = _run(server_module.handle_verify_words({"words": ["а", "б"]}))
        assert outcome["disposition"] == "partial"
        assert outcome["status"] == "empty"
        assert outcome["match_count"] == 0
        assert outcome["hits"] == []
        assert "NOT FOUND" in content[0].text

    def test_check_modern_form_archaic_only_empty_hits(self, server_module):
        archaic = [{"lemma": "старий", "pos": "adj", "tags": "adj:m:v_naz:arch"}]
        with patch("scripts.verification.vesum.verify_word", return_value=archaic):
            _content, outcome = _run(server_module.handle_check_modern_form({"word": "старий"}))
        assert outcome["disposition"] == "negative"
        assert outcome["status"] == "empty"
        assert outcome["match_count"] == 0
        assert outcome["hits"] == []
        assert outcome["result"]["has_only_archaic_form"] is True
        assert outcome["supporting_records"]["matches"] == archaic


class TestSearchTextEnvelope:
    def test_empty_search_text(self, server_module):
        with patch("wiki.sources_db.search_textbooks", return_value=[]):
            content, envelope = _run(server_module.handle_search_text({"query": "zzznotfound"}))
        assert content[0].text == "No results found."
        assert envelope["schema"] == SCHEMA_V1
        assert envelope["tool"] == "search_text"
        assert envelope["status"] == "empty"
        assert envelope["match_count"] == 0
        assert envelope["hits"] == []

    def test_hit_search_text(self, server_module):
        hits = [{"chunk_id": "c1", "text": "hello", "title": "T"}]
        with patch("wiki.sources_db.search_textbooks", return_value=hits):
            content, envelope = _run(server_module.handle_search_text({"query": "hello world"}))
        assert envelope["status"] == "ok"
        assert envelope["match_count"] == 1
        assert envelope["hits"][0]["chunk_id"] == "c1"
        assert "Found 1" in content[0].text


def _assert_analysis_contract(content, outcome, analyses, lemmas):
    assert outcome["match_count"] == len(outcome["hits"]) == analyses
    assert type(outcome["lemma_count"]) is int
    assert outcome["lemma_count"] == lemmas
    assert outcome["summary_prose"] == content[0].text
    count_text = f"{analyses} {'analysis' if analyses == 1 else 'analyses'}"
    count_text += f" ({lemmas} distinct {'lemma' if lemmas == 1 else 'lemmas'})"
    assert count_text in content[0].text
    for hit in outcome["hits"]:
        assert {"lemma", "pos", "tags", "is_archaic", "tag_gloss"} <= hit.keys()
        assert hit["tag_gloss"].strip()


@pytest.mark.parametrize("pos_filter,analyses,lemmas", [(None, 6, 2), ("adj", 5, 1), ("verb", 1, 1)])
def test_synii_pinned_lookup(server_module, monkeypatch, tmp_path, synii_matches, pos_filter, analyses, lemmas):
    """Exercise the real SQL lookup with source-attested rows, including POS filtering."""
    import sqlite3

    from scripts.verification import vesum

    db_path = tmp_path / "vesum.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE forms (word_form TEXT, lemma TEXT, pos TEXT, tags TEXT)")
        conn.executemany("INSERT INTO forms VALUES (?, ?, ?, ?)", [
            ("синій", row["lemma"], row["pos"], row["tags"]) for row in synii_matches
        ])
    monkeypatch.setattr(vesum, "VESUM_DB_PATH", db_path)
    monkeypatch.setattr(vesum, "_vesum_conn", None)
    monkeypatch.setattr(vesum, "_vesum_conn_path", None)
    monkeypatch.setattr(server_module, "_vesum_source_version", lambda: SYNII_SHA256)
    try:
        content, outcome = _run(server_module.handle_verify_word({"word": "синій", "pos_filter": pos_filter}))
    finally:
        if vesum._vesum_conn is not None:
            vesum._vesum_conn.close()
    _assert_analysis_contract(content, outcome, analyses, lemmas)
    if pos_filter is None:
        assert outcome["hits"][0]["tag_gloss"] == "adjective; masculine; nominative; positive degree"
        assert outcome["hits"][-1]["tag_gloss"] == "verb; imperfective; imperative; singular; second person"
    expected = {"word": "синій", "pos_filter": pos_filter, "matches": [
        row for row in synii_matches if pos_filter is None or row["pos"] == pos_filter
    ]}
    assert outcome["result"] == expected
    assert outcome["disposition"] == "supported" and outcome["success"] is True
    assert outcome["evidence_identifiers"] == [immutable_evidence_identifier(
        namespace="vesum", source_version=SYNII_SHA256, typed_result=expected,
    )]


@pytest.mark.parametrize("partial", [False, True])
def test_batch_analysis_rows_and_global_lemmas(server_module, monkeypatch, synii_matches, partial):
    # Synthetic second input reuses pinned rows to isolate cross-input counting.
    words = ["синій", "синій", "fixture-second-input"] + (["fixture-miss"] if partial else [])
    matches = {"синій": synii_matches, "fixture-second-input": synii_matches[:3]}
    if partial:
        matches["fixture-miss"] = []
    original = copy.deepcopy(matches)
    monkeypatch.setattr(server_module, "_vesum_source_version", lambda: SYNII_SHA256)
    with patch("scripts.verification.vesum.verify_words", return_value=matches) as lookup:
        content, outcome = _run(server_module.handle_verify_words({"words": words, "pos_filter": None}))
    lookup.assert_called_once_with(words, None)
    _assert_analysis_contract(content, outcome, 9, 2)
    assert [hit["word"] for hit in outcome["hits"]] == ["синій"] * 6 + ["fixture-second-input"] * 3
    expected = {"words": words, "pos_filter": None, "found": 3, "total": len(words), "matches": original}
    assert matches == original
    assert outcome["result"] == expected
    assert outcome["disposition"] == ("partial" if partial else "supported")
    assert outcome["success"] is (not partial)
    assert outcome["evidence_identifiers"] == ([] if partial else [immutable_evidence_identifier(
        namespace="vesum", source_version=SYNII_SHA256, typed_result=expected,
    )])


def test_lemma_hits_preserve_authority_payload(server_module, monkeypatch, synii_matches):
    forms = [{"word_form": "синій", "pos": row["pos"], "tags": row["tags"]} for row in synii_matches[:5]]
    expected_forms = [{**form, "is_archaic": False} for form in forms]
    monkeypatch.setattr(server_module, "_vesum_source_version", lambda: SYNII_SHA256)
    with patch("scripts.verification.vesum.verify_lemma", return_value=forms):
        content, outcome = _run(server_module.handle_verify_lemma({"lemma": "синій"}))
    _assert_analysis_contract(content, outcome, 5, 1)
    expected = {"lemma": "синій", "forms": expected_forms}
    assert outcome["result"] == expected
    assert all(hit["lemma"] == "синій" for hit in outcome["hits"])
    assert outcome["evidence_identifiers"] == [immutable_evidence_identifier(
        namespace="vesum", source_version=SYNII_SHA256, typed_result=expected,
    )]


@pytest.mark.parametrize("tool,args,empty", [
    ("verify_word", {"word": "fixture-miss"}, []),
    ("verify_words", {"words": ["fixture-miss"]}, {"fixture-miss": []}),
    ("verify_lemma", {"lemma": "fixture-miss"}, []),
])
def test_empty_and_invalid_counts(server_module, tool, args, empty):
    handler = getattr(server_module, f"handle_{tool}")
    with patch(f"scripts.verification.vesum.{tool}", return_value=empty) as lookup:
        content, outcome = _run(handler(args))
        _assert_analysis_contract(content, outcome, 0, 0)
        assert outcome["status"] == "empty"
        lookup.reset_mock()
        content, outcome = _run(handler({}))
        _assert_analysis_contract(content, outcome, 0, 0)
        assert outcome["status"] == "error"
        lookup.assert_not_called()


def test_gloss_unknown_and_missing_tokens():
    assert tag_gloss("adj:f:v_dav:future-tag") == "adjective; feminine; dative; unrecognized tag [future-tag]"
    assert tag_gloss(None) == tag_gloss("") == "No morphological tags supplied"
    assert tag_gloss("verb:imperf:impers") == "verb; imperfective; impersonal form"


def test_archaic_hit_gloss(server_module, monkeypatch):
    # Synthetic marker test, not a claim that this pinned modern row is archaic.
    matches = [{"lemma": "fixture", "pos": "adj", "tags": "adj:m:v_naz:arch"}]
    monkeypatch.setattr(server_module, "_vesum_source_version", lambda: VESUM_FIXTURE_VERSION)
    with patch("scripts.verification.vesum.verify_word", return_value=matches):
        content, outcome = _run(server_module.handle_verify_word({"word": "fixture"}))
    _assert_analysis_contract(content, outcome, 1, 1)
    assert outcome["hits"][0]["is_archaic"] is True
    assert "archaic" in outcome["hits"][0]["tag_gloss"]
    assert "tag_gloss" not in matches[0]
