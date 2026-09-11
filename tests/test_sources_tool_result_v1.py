"""Contract tests for sources.tool-result.v1 envelopes (#7954)."""

from __future__ import annotations

import asyncio
import importlib.util
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

SOURCES_SERVER_PATH = Path(__file__).resolve().parents[1] / ".mcp" / "servers" / "sources" / "server.py"


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


class TestVerifyWordEnvelope:
    def test_found_exposes_integer_match_count(self, server_module):
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
