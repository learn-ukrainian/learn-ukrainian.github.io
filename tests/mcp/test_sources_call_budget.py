"""Sources MCP call-budget contract: cached DB identity, compact payloads, input errors."""

from __future__ import annotations

import asyncio
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCES_SERVER_PATH = PROJECT_ROOT / ".mcp" / "servers" / "sources" / "server.py"


@pytest.fixture
def server_module():
    spec = importlib.util.spec_from_file_location("sources_server_call_budget", SOURCES_SERVER_PATH)
    srv = importlib.util.module_from_spec(spec)
    sys.modules["sources_server_call_budget"] = srv
    spec.loader.exec_module(srv)
    return srv


def _run(coro):
    return asyncio.run(coro)


def test_vesum_source_version_matches_file_bytes_and_evidence_id_is_stable(server_module, tmp_path, monkeypatch):
    """An unchanged DB keeps today's digest, so the evidence id does not move."""
    from learn_ukrainian_v4_runtime.v4_canonical_authority_store import immutable_evidence_identifier

    db = tmp_path / "vesum.db"
    payload = b"vesum-bytes-v1"
    db.write_bytes(payload)
    monkeypatch.setattr("scripts.rag.config.VESUM_DB_PATH", db)
    server_module._FILE_HASH_CACHE.clear()

    expected = hashlib.sha256(payload).hexdigest()
    first = server_module._vesum_source_version()
    assert first == expected
    with patch("builtins.open", side_effect=AssertionError("unchanged DB must not be re-hashed")):
        second = server_module._vesum_source_version()
    assert second == first

    typed = {"word": "фікстура", "matches": []}
    pinned = immutable_evidence_identifier(namespace="vesum", source_version=expected, typed_result=typed)
    cached = immutable_evidence_identifier(namespace="vesum", source_version=second, typed_result=typed)
    assert cached == pinned
    assert cached.startswith("vesum:")


def test_replaced_db_changes_source_version(server_module, tmp_path, monkeypatch):
    from learn_ukrainian_v4_runtime.v4_canonical_authority_store import immutable_evidence_identifier

    db = tmp_path / "vesum.db"
    db.write_bytes(b"vesum-bytes-v1")
    monkeypatch.setattr("scripts.rag.config.VESUM_DB_PATH", db)
    server_module._FILE_HASH_CACHE.clear()
    first = server_module._vesum_source_version()

    replacement = tmp_path / "replacement.db"
    replacement.write_bytes(b"vesum-bytes-v2")
    os.replace(replacement, db)

    second = server_module._vesum_source_version()
    assert second != first
    assert second == hashlib.sha256(b"vesum-bytes-v2").hexdigest()
    typed = {"word": "фікстура", "matches": []}
    assert immutable_evidence_identifier(
        namespace="vesum", source_version=first, typed_result=typed
    ) != immutable_evidence_identifier(namespace="vesum", source_version=second, typed_result=typed)


def test_mcp_server_identity_reuses_keyed_file_hash(server_module, tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    (data / "sources.db").write_bytes(b"sources-db")
    (data / "vesum.db").write_bytes(b"vesum-db")
    server_module._FILE_HASH_CACHE.clear()
    with patch.object(server_module, "PROJECT_ROOT", tmp_path):
        first = _run(server_module.handle_mcp_server_identity({}))
        with patch("builtins.open", side_effect=AssertionError("identity hashes must come from the cache")):
            second = _run(server_module.handle_mcp_server_identity({}))
    assert first[0].text == second[0].text
    payload = json.loads(first[0].text)
    assert payload["sources_db_sha256"] == hashlib.sha256(b"sources-db").hexdigest()
    assert payload["vesum_db_sha256"] == hashlib.sha256(b"vesum-db").hexdigest()


def test_verify_stress_summary_is_one_line_and_result_is_kept(server_module):
    payload = {
        "input": "замок",
        "status": "ambiguous",
        "matches": [
            {"stressed_form": "за\u0301мок", "vowel_indices": [1], "required_tags": ["upos=NOUN"]},
            {"stressed_form": "замо\u0301к", "vowel_indices": [3], "required_tags": ["upos=NOUN"]},
        ],
        "source": {"dictionary": "ukrainian-word-stress (ULIF-derived)"},
    }
    with patch("scripts.verification.stress.verify_stress", return_value=payload):
        content, outcome = _run(server_module.handle_verify_stress({"word": "замок"}))
    assert outcome["result"] == payload
    assert outcome["hits"] == payload["matches"]
    assert outcome["summary_prose"] == content[0].text
    assert "\n" not in content[0].text
    assert not content[0].text.lstrip().startswith("{")
    assert json.dumps(payload, ensure_ascii=False) not in content[0].text


def test_inspect_words_hoists_shared_provenance(server_module):
    class _Inspection:
        def __init__(self, word: str):
            self.word = word
            self.status = type("Status", (), {"value": "CLEAN"})()
            self.effective_markers: list[str] = []
            self.clean_analyses = [{"lemma": word, "pos": "noun", "tags": "noun"}]
            self.marked_analyses: list[dict] = []

        def as_dict(self):
            return {
                "word": self.word,
                "status": "CLEAN",
                "clean_analyses": self.clean_analyses,
                "marked_analyses": [],
                "effective_markers": [],
                "source_locations": ["forms_all"],
                "source_version": "version-once",
                "pipeline_identity": {"pipeline": "vesum", "step": "inspect"},
            }

    words = ["кіт", "вода"]
    results = {word: _Inspection(word) for word in words}
    with patch("scripts.verification.vesum.inspect_words", return_value=results):
        content = _run(server_module.handle_inspect_words({"words": words}))
    text = content[0].text
    assert text.count("version-once") == 1
    assert text.count('"pipeline"') == 1
    raw = text.split("Raw payload:\n", 1)[1]
    payload = json.loads(raw)
    assert payload["source_version"] == "version-once"
    assert payload["pipeline_identity"] == {"pipeline": "vesum", "step": "inspect"}
    assert payload["words"]["кіт"]["clean_analyses"] == [{"lemma": "кіт", "pos": "noun", "tags": "noun"}]
    assert "source_version" not in payload["words"]["кіт"]
    assert "pipeline_identity" not in payload["words"]["вода"]


def test_query_pravopys_empty_topic_is_a_structured_error(server_module):
    content, envelope = _run(server_module.handle_query_pravopys({"topic": ""}))
    assert envelope["status"] == "error"
    assert envelope["error_code"] == "invalid_input"
    assert "topic" in content[0].text
    assert "Expected arguments: topic." in content[0].text
    assert "KeyError" not in content[0].text

    missing, missing_envelope = _run(server_module.handle_query_pravopys({}))
    assert missing_envelope["error_code"] == "invalid_input"
    assert "Expected arguments: topic." in missing[0].text


def test_query_sum20_missing_word_is_a_structured_error(server_module):
    content = _run(server_module.handle_query_sum20({}))
    payload = json.loads(content[0].text)
    assert payload["status"] == "error"
    assert payload["error_code"] == "invalid_input"
    assert payload["expected_arguments"] == ["word"]
    assert "KeyError" not in content[0].text

    blank = _run(server_module.handle_query_sum20({"word": "   "}))
    assert json.loads(blank[0].text)["error_code"] == "invalid_input"


def test_every_sources_tool_advertises_read_only(server_module):
    tools = _run(server_module.list_tools())
    assert tools
    for tool in tools:
        annotations = tool.annotations
        assert annotations is not None, tool.name
        assert annotations.read_only_hint is True, tool.name
        assert annotations.destructive_hint is False, tool.name


def test_verify_stresses_tool_documents_the_cap(server_module):
    tools = _run(server_module.list_tools())
    tool = next(item for item in tools if item.name == "verify_stresses")
    assert tool.input_schema["required"] == ["words"]
    assert "pos" in tool.input_schema["properties"]
    assert "500" in tool.description
