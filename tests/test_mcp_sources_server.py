"""Tests for the MCP Sources server (.mcp/servers/sources/server.py).

Historically called the "MCP RAG server" — the current implementation
is SQLite FTS5, not vector RAG, so the server was renamed to `sources`
in the April 2026 rename pass. Tool prefix is mcp__sources__*.

Covers:
- Tool listing returns all expected tools with correct schemas
- Tool dispatch routes to correct handlers
- SSE mode uses stateless=True (fix for initialization handshake issue)
- verify_word / verify_words handlers return correct format
- Error handling for unknown tools
"""

import asyncio
import hashlib
import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
import threading
from pathlib import Path
from typing import ClassVar
from unittest.mock import AsyncMock, MagicMock, patch

import mcp  # noqa: F401  # Declares the Sources wire dependency to the CI fastlane.
import numpy  # noqa: F401  # Declares the Sources runtime dependency to the CI fastlane.
import pymorphy3  # noqa: F401  # Declares the Russian-shadow runtime dependency.
import pymorphy3_dicts_uk  # noqa: F401  # Declares the Ukrainian morphology dictionary.
import pytest
import rapidfuzz  # noqa: F401  # Declares the quote-verification runtime dependency.
import requests  # noqa: F401  # Declares the Sources HTTP dependency to the CI fastlane.
from mcp.types import CallToolRequestParams, TextContent

SOURCES_SERVER_PATH = Path(__file__).resolve().parents[1] / ".mcp" / "servers" / "sources" / "server.py"
VESUM_FIXTURE_VERSION = "a" * 64
VESUM_FIXTURE_MATCH = {"lemma": "читати", "pos": "verb", "tags": "verb:imperf:impr:s:2"}


@pytest.fixture
def server_module():
    """Import the server module fresh."""
    spec = importlib.util.spec_from_file_location("sources_server", SOURCES_SERVER_PATH)
    srv = importlib.util.module_from_spec(spec)
    sys.modules["sources_server"] = srv
    spec.loader.exec_module(srv)
    return srv


def _run(coro):
    """Run an async coroutine synchronously."""
    return asyncio.run(coro)


@pytest.mark.parametrize("stale_db", [False, True])
def test_read_only_dispatch_sources_lookup_leaves_sparse_worktree_clean(server_module, tmp_path, monkeypatch, stale_db):
    """A real sources handler read must not make the dispatch guard fail (#9122)."""
    primary = tmp_path / "primary"
    primary.mkdir()
    subprocess.run(["git", "init", str(primary)], check=True, capture_output=True, timeout=30)
    subprocess.run(["git", "-C", str(primary), "config", "user.email", "test@example.com"], check=True, timeout=30)
    subprocess.run(["git", "-C", str(primary), "config", "user.name", "test"], check=True, timeout=30)
    (primary / "tracked.txt").write_text("fixture\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(primary), "add", "tracked.txt"], check=True, timeout=30)
    subprocess.run(["git", "-C", str(primary), "commit", "-m", "fixture"], check=True, capture_output=True, timeout=30)
    worktree = tmp_path / "dispatch-worktree"
    subprocess.run(
        ["git", "-C", str(primary), "worktree", "add", "--detach", str(worktree), "HEAD"],
        check=True,
        capture_output=True,
        timeout=30,
    )
    worktree_db = worktree / "data" / "sources.db"
    if stale_db:
        worktree_db.parent.mkdir()
        worktree_db.touch()

    db = primary / "data" / "sources.db"
    db.parent.mkdir()
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE textbooks (chunk_id TEXT, title TEXT, text TEXT)")
        conn.execute("CREATE TABLE literary_texts (chunk_id TEXT, title TEXT, text TEXT)")
        conn.execute("INSERT INTO textbooks VALUES ('chunk-1', 'Fixture', 'Source text')")

    tasks = tmp_path / "tasks"
    tasks.mkdir()
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    monkeypatch.setenv("LU_MCP_SOURCES_LOG_DIR", str(tmp_path))
    monkeypatch.delenv("LU_SOURCES_DB", raising=False)
    for key in tuple(os.environ):
        if key.startswith(("GIT_", "PRE_COMMIT")):
            monkeypatch.delenv(key, raising=False)

    monkeypatch.syspath_prepend(str(SOURCES_SERVER_PATH.parents[3] / "scripts"))
    import delegate
    from rag import source_query
    from wiki import sources_db

    monkeypatch.setattr(sources_db, "PROJECT_ROOT", worktree)
    monkeypatch.setattr(sources_db, "SOURCES_DB_PATH", worktree / "data" / "sources.db")
    monkeypatch.setattr(sources_db, "_conn", None)
    task_id = "sources-read-only-lookup"
    state_path = delegate._state_path(task_id)
    delegate._write_state_atomic(state_path, {"task_id": task_id, "cwd": str(worktree)})

    def lookup(*_args, **_kwargs):
        result = _run(
            server_module._on_call_tool(
                None, CallToolRequestParams(name="get_chunk_context", arguments={"chunk_id": "chunk-1"})
            )
        )
        assert result.is_error is False
        assert "Source text" in result.content[0].text
        with patch.object(source_query, "_get") as fetch:
            fetch.return_value.text = "<html>missing WebForms tokens</html>"
            fetch.return_value.raise_for_status.return_value = None
            ulif_result = _run(
                server_module._on_call_tool(
                    None,
                    CallToolRequestParams(
                        name="query_ulif",
                        arguments={"word": "fixture-word", "sections": ["paradigm"]},
                    ),
                )
            )
            assert ulif_result.is_error is False
            assert json.loads(ulif_result.content[0].text)["status"] == "parse_error"
            assert source_query.query_ulif("fixture-word")["status"] == "parse_error"
            fetch.assert_called_once()
        with sqlite3.connect(db) as conn:
            assert conn.execute("SELECT COUNT(*) FROM ulif_dictua_entries").fetchone()[0] == 1
        return type(
            "Result",
            (),
            {
                "ok": True,
                "response": "Source text",
                "stderr_excerpt": None,
                "returncode": 0,
                "rate_limited": False,
                "model": "fixture",
                "effort": "high",
                "cli_version": "fixture",
            },
        )()

    try:
        with patch("agent_runtime.runner.invoke", side_effect=lookup):
            rc = delegate._run_worker(
                task_id=task_id,
                agent="agy",
                prompt="Look up a source.",
                mode="read-only",
                cwd_str=str(worktree),
                model=None,
                hard_timeout=60,
            )
        state = delegate._read_state(state_path)
        assert rc == 0
        assert state["status"] == "done"
        assert state["read_only_mutation_paths"] == []
        if stale_db:
            assert worktree_db.stat().st_size == 0
        else:
            assert not worktree_db.exists()
            assert not worktree_db.parent.exists()
    finally:
        if sources_db._conn is not None:
            sources_db._conn.close()


def test_network_sources_override_has_missing_database_responses(server_module, tmp_path, monkeypatch):
    from wiki import sources_db

    worktree_db = tmp_path / "data" / "sources.db"
    monkeypatch.setattr(sources_db, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(sources_db, "SOURCES_DB_PATH", worktree_db)
    monkeypatch.setattr(sources_db, "_conn", None)
    monkeypatch.setenv("LU_SOURCES_DB", "//unreachable/UkrainianData/sources.db")

    content, envelope = _run(server_module.handle_get_chunk_context({"chunk_id": "fixture"}))
    assert content[0].text == "Sources database not found."
    assert envelope["status"] == "error"
    assert envelope["error_code"] == "sources_db_missing"
    for args in (
        {"word": "fixture", "cache_only": True},
        {"word": "fixture", "sections": ["paradigm"]},
        {"word": "fixture"},
    ):
        ulif_content = _run(server_module.handle_query_ulif(args))
        assert ulif_content[0].text == "Sources database not found."
    assert server_module._lookup_wikipedia_in_db("fixture") is None
    assert not worktree_db.exists()
    assert not worktree_db.parent.exists()


class TestListTools:
    """Test that list_tools returns all expected tools with valid schemas."""

    def test_returns_all_tools(self, server_module):
        tools = _run(server_module.list_tools())
        tool_names = {t.name for t in tools}

        expected = {
            "search_sources",
            "search_text",
            "search_literary",
            "search_external",
            "get_full_text",
            "get_chunk_context",
            "collection_stats",
            "mcp_server_identity",
            "verify_word",
            "verify_source_attribution",
            "verify_words",
            "vet_vocabulary",
            "verify_lemma",
            "verify_quote",
            "check_modern_form",
            "inspect_word",
            "inspect_words",
            "inspect_lemma",
            "verify_stress",
            "verify_stresses",
            "check_text",
            "query_wikipedia",
            "query_grac",
            "query_ulif",
            "query_ulif_synonyms",
            "query_ulif_antonyms",
            "query_ulif_phraseology",
            "query_ulif_records",
            "query_r2u",
            "query_e2u",
            "query_sum20",
            "query_slovnyk_me",
            "query_pravopys",
            "query_cefr_level",
            "search_style_guide",
            "search_definitions",
            "search_grinchenko_1907",
            "search_idioms",
            "search_synonyms",
            "translate_en_uk",
            "search_esum",
            "search_slovnyk_me",
            "search_heritage",
            "check_russian_shadow",
            "search_ua_gec_errors",
        }
        missing = expected - tool_names
        extra = tool_names - expected
        assert not missing, f"missing tools: {missing}"
        assert not extra, (
            f"unexpected tools: {extra}. Update the test expected set — "
            f"adding a tool to the server always requires a test update."
        )
        identity_tool = next(tool for tool in tools if tool.name == "mcp_server_identity")
        assert identity_tool.input_schema["properties"]["include_sources_db_sha256"]["type"] == "boolean"

    def test_all_tools_have_input_schema(self, server_module):
        tools = _run(server_module.list_tools())
        for tool in tools:
            assert tool.input_schema is not None, f"{tool.name} missing input_schema"
            assert tool.input_schema.get("type") == "object", f"{tool.name} schema not object type"

    def test_verify_word_schema(self, server_module):
        tools = _run(server_module.list_tools())
        vw = next(t for t in tools if t.name == "verify_word")
        assert "word" in vw.input_schema["required"]
        assert "word" in vw.input_schema["properties"]

    def test_query_ulif_schema_accepts_structured_sections(self, server_module):
        tools = _run(server_module.list_tools())
        ulif = next(tool for tool in tools if tool.name == "query_ulif")
        sections = ulif.input_schema["properties"]["sections"]
        assert "default" not in sections
        assert sections["items"]["enum"] == [
            "paradigm",
            "synonyms",
            "antonyms",
            "phraseology",
        ]
        assert "When supplied" in sections["description"]


class TestUlifHandlers:
    def test_query_ulif_without_sections_renders_legacy_paradigm(self, server_module):
        paradigm = {"word": "великий", "rows": [["Називний", "великий"]]}
        with patch("rag.source_query.ulif_paradigm", return_value=paradigm) as query:
            result = _run(server_module.handle_query_ulif({"word": "великий"}))

        query.assert_called_once_with("великий")
        assert result[0].text == "Paradigm for 'великий':\n\nНазивний | великий"

    def test_query_ulif_without_sections_renders_legacy_no_result(self, server_module):
        with patch("rag.source_query.ulif_paradigm", return_value=None) as query:
            result = _run(server_module.handle_query_ulif({"word": "відсутнє"}))

        query.assert_called_once_with("відсутнє")
        assert result[0].text == "No ULIF paradigm found for: 'відсутнє'"

    def test_query_ulif_without_sections_unavailable_is_not_no_result(self, server_module):
        """A DictUA outage must not render as 'No ULIF paradigm found' (#9005)."""
        unavailable = {"status": "unavailable", "word": "великий"}
        with patch("rag.source_query.ulif_paradigm", return_value=unavailable):
            result = _run(server_module.handle_query_ulif({"word": "великий"}))

        assert "unavailable" in result[0].text
        assert "No ULIF paradigm found" not in result[0].text

    def test_query_ulif_renders_structured_source_metadata(self, server_module):
        expected = {
            "source_id": "ulif_dictua",
            "official_url": "https://lcorp.ulif.org.ua/dictua",
            "attribution_label": "«Словники України» (Український мовно-інформаційний фонд НАН України)",
            "retrieved_at": "2026-07-15T00:00:00+00:00",
            "content_sha256": "a" * 64,
            "parser_version": "ulif-dictua-v1",
            "status": "ok",
            "sections": {"paradigm": {"rows": [["Називний", "великий"]]}},
        }
        with patch("rag.source_query.query_ulif", return_value=expected) as query:
            result = _run(
                server_module.handle_query_ulif(
                    {
                        "word": "великий",
                        "sections": ["paradigm"],
                    }
                )
            )

        query.assert_called_once_with("великий", ["paradigm"])
        assert json.loads(result[0].text) == expected

    def test_query_ulif_with_explicit_sections_transient_error_is_unavailable(self, server_module):
        """query_ulif with explicit sections renders unavailable prose on outage (#9016)."""
        transient = {
            "status": "transient_error",
            "word": "великий",
            "canonical_headword": "великий",
            "sections": {},
        }
        with patch("rag.source_query.query_ulif", return_value=transient):
            result = _run(
                server_module.handle_query_ulif(
                    {"word": "великий", "sections": ["paradigm"]}
                )
            )

        text = result[0].text
        assert "unavailable" in text
        assert "lcorp.ulif.org.ua" in text
        assert "transient_error" not in text

    @pytest.mark.parametrize(
        "handler_name,query_fn_name",
        [
            ("handle_query_ulif_synonyms", "query_ulif_synonyms"),
            ("handle_query_ulif_antonyms", "query_ulif_antonyms"),
            ("handle_query_ulif_phraseology", "query_ulif_phraseology"),
        ],
    )
    def test_ulif_relation_tools_transient_error_is_unavailable(
        self, server_module, handler_name, query_fn_name
    ):
        """ULIF relation tools render unavailable prose instead of transient_error JSON (#9016)."""
        transient = {
            "status": "transient_error",
            "word": "великий",
            "canonical_headword": "великий",
            "sections": {},
        }
        handler = getattr(server_module, handler_name)
        with patch(f"rag.source_query.{query_fn_name}", return_value=transient):
            result = _run(handler({"word": "великий"}))

        text = result[0].text
        assert "unavailable" in text
        assert "lcorp.ulif.org.ua" in text
        assert "transient_error" not in text


class TestQueryUlifRecordsHandler:
    def test_query_ulif_records_schema(self, server_module):
        tools = _run(server_module.list_tools())
        record_tool = next(t for t in tools if t.name == "query_ulif_records")
        assert record_tool.input_schema["required"] == ["words"]
        assert record_tool.input_schema["properties"]["words"]["type"] == "array"
        assert record_tool.input_schema["properties"]["detail"]["enum"] == ["full", "compact"]

    def test_query_ulif_records_invalid_inputs(self, server_module):
        res1 = _run(server_module.handle_query_ulif_records({}))
        assert "invalid_input" in res1[0].text

        res2 = _run(server_module.handle_query_ulif_records({"words": []}))
        assert "invalid_input" in res2[0].text

        res3 = _run(server_module.handle_query_ulif_records({"words": ["стіл"], "detail": "invalid"}))
        assert "invalid_input" in res3[0].text

    def test_query_ulif_records_full_detail(self, server_module):
        mock_records = [
            {
                "word": "стіл",
                "normalized_query": "стіл",
                "status": "ok",
                "verified": True,
                "entry_count": 1,
                "entries": [
                    {
                        "entry_id": 1,
                        "homonym_index": 1,
                        "canonical_headword": "сті́л",
                        "sections": {
                            "paradigm": [{"rows": [["Називний", "сті́л"]], "raw_html": "<table>...</table>"}],
                        },
                    }
                ],
            }
        ]
        with patch("wiki.sources_db.get_ulif_word_records", return_value=mock_records) as mock_fn:
            result = _run(server_module.handle_query_ulif_records({"words": ["стіл"], "detail": "full"}))
            mock_fn.assert_called_once_with(["стіл"])

        data = json.loads(result[0].text)
        assert data["detail"] == "full"
        assert data["record_count"] == 1
        assert "source" in data
        assert data["source"]["source_id"] == "ulif_dictua"
        assert data["records"][0]["entries"][0]["sections"]["paradigm"][0]["raw_html"] == "<table>...</table>"

    def test_query_ulif_records_compact_detail_strips_raw_html(self, server_module):
        mock_records = [
            {
                "word": "стіл",
                "normalized_query": "стіл",
                "status": "ok",
                "verified": True,
                "entries": [
                    {
                        "entry_id": 1,
                        "sections": {
                            "paradigm": [{"rows": [["Називний", "сті́л"]], "raw_html": "<table>...</table>"}],
                        },
                    }
                ],
            }
        ]
        with patch("wiki.sources_db.get_ulif_word_records", return_value=mock_records):
            result = _run(server_module.handle_query_ulif_records({"words": ["стіл"], "detail": "compact"}))

        data = json.loads(result[0].text)
        assert data["detail"] == "compact"
        assert "detail_note" in data
        assert "raw_html" not in data["records"][0]["entries"][0]["sections"]["paradigm"][0]

    def test_query_ulif_records_truncates_at_200(self, server_module):
        words = [f"word_{i}" for i in range(250)]
        mock_records = [{"word": w, "status": "not_found", "verified": False, "entries": []} for w in words[:200]]
        with patch("wiki.sources_db.get_ulif_word_records", return_value=mock_records) as mock_fn:
            result = _run(server_module.handle_query_ulif_records({"words": words}))
            assert len(mock_fn.call_args[0][0]) == 200

        data = json.loads(result[0].text)
        assert data["record_count"] == 200
        assert "warning" in data
        assert "truncated" in data["warning"]

    def test_search_text_subject_schema(self, server_module):
        tools = _run(server_module.list_tools())
        search_text = next(t for t in tools if t.name == "search_text")
        subject = search_text.input_schema["properties"]["subject"]
        assert subject["enum"] == list(server_module.CANONICAL_TEXTBOOK_SUBJECTS)
        assert "ukrmova" in subject["description"]
        assert "grade" not in search_text.input_schema["properties"]
        assert "trust_tier" not in search_text.input_schema["properties"]
        assert "BGE-M3" not in search_text.description

    def test_search_images_not_in_live_inventory(self, server_module):
        """Image search is deferred; do not advertise a no-op stub (#7026)."""
        tools = _run(server_module.list_tools())
        tool_names = {t.name for t in tools}
        assert "search_images" not in tool_names

    def test_search_literary_schema(self, server_module):
        tools = _run(server_module.list_tools())
        search_literary = next(t for t in tools if t.name == "search_literary")
        assert "work" not in search_literary.input_schema["properties"]
        assert "genre" not in search_literary.input_schema["properties"]
        assert "period" not in search_literary.input_schema["properties"]
        assert search_literary.input_schema["required"] == ["query"]

    def test_get_chunk_context_schema(self, server_module):
        tools = _run(server_module.list_tools())
        chunk_context = next(t for t in tools if t.name == "get_chunk_context")
        assert "window" not in chunk_context.input_schema["properties"]
        assert chunk_context.input_schema["required"] == ["chunk_id"]

    def test_get_full_text_schema(self, server_module):
        tools = _run(server_module.list_tools())
        full_text = next(t for t in tools if t.name == "get_full_text")
        assert "RAG" not in full_text.description
        assert full_text.input_schema["required"] == ["work"]

    def test_collection_stats_schema(self, server_module):
        tools = _run(server_module.list_tools())
        stats = next(t for t in tools if t.name == "collection_stats")
        assert "RAG" not in stats.description

    def test_verify_words_schema(self, server_module):
        tools = _run(server_module.list_tools())
        vw = next(t for t in tools if t.name == "verify_words")
        assert "words" in vw.input_schema["required"]
        props = vw.input_schema["properties"]["words"]
        assert props["type"] == "array"
        assert props["items"]["type"] == "string"

    def test_vet_vocabulary_schema(self, server_module):
        tools = _run(server_module.list_tools())
        tool = next(tool for tool in tools if tool.name == "vet_vocabulary")
        assert tool.input_schema["required"] == ["words"]
        assert tool.input_schema["properties"]["words"]["type"] == "array"
        assert tool.input_schema["properties"]["include_definitions"]["default"] is False
        assert "contrast only" in tool.description

    def test_sum11_tool_description_bans_verification(self, server_module):
        tools = _run(server_module.list_tools())
        definition = next(tool for tool in tools if tool.name == "search_definitions")
        attribution = next(tool for tool in tools if tool.name == "verify_source_attribution")
        synonyms = next(tool for tool in tools if tool.name == "search_synonyms")
        assert definition.description.startswith("Soviet-occupation СУМ-11")
        assert "NEVER a source for meaning, stress, part of speech or word validity" in definition.description
        assert "query_sum20 / ВТС / query_ulif / VESUM / Грінченко" in definition.description
        assert "verification_authority=false" in attribution.description
        assert "search_definitions" not in synonyms.description

    def test_live_sum11_entry_is_labelled_contrast_only(self, server_module):
        hit = {
            "dict_label": "СУМ-11",
            "url": "https://slovnyk.me/dict/sum/тест",
            "text": "historical dictionary text",
        }
        with patch("rag.source_query.slovnyk_me_lookup", return_value=hit):
            result = _run(server_module.handle_query_slovnyk_me({"word": "тест", "dict": "sum"}))
        assert "verification_authority: false" in result[0].text
        assert "contrast only" in result[0].text

    def test_verify_quote_schema(self, server_module):
        tools = _run(server_module.list_tools())
        vq = next(t for t in tools if t.name == "verify_quote")
        assert vq.input_schema["required"] == ["author", "text"]
        assert vq.input_schema["properties"]["min_confidence"]["default"] == 0.80

    def test_verify_source_attribution_schema(self, server_module):
        tools = _run(server_module.list_tools())
        tool = next(t for t in tools if t.name == "verify_source_attribution")
        assert tool.input_schema["required"] == ["source", "claim"]
        assert set(tool.input_schema["properties"]["source"]["enum"]) == {
            "grinchenko_1907",
            "esum",
            "sum11",
            "antonenko_davydovych",
            "literary",
            "heritage",
            "wikipedia",
            "style_guide",
        }

    def test_verify_stress_schema(self, server_module):
        tools = _run(server_module.list_tools())
        tool = next(t for t in tools if t.name == "verify_stress")
        assert tool.input_schema["required"] == ["word"]
        assert "pos" in tool.input_schema["properties"]
        assert "tags" in tool.input_schema["properties"]


class TestLiveSourceUnavailable:
    """An outage (Cloudflare/network/HTTP failure) must never render as a
    false negative ('no entry'/'not found') — see #9005."""

    def test_slovnyk_me_unavailable_is_not_rendered_as_no_entry(self, server_module):
        unavailable = {
            "status": "unavailable",
            "word": "хата",
            "dict": "vts",
            "url": "https://slovnyk.me/dict/vts/хата",
            "challenge": True,
            "http_status": 403,
        }
        with patch("rag.source_query.slovnyk_me_lookup", return_value=unavailable):
            result = _run(server_module.handle_query_slovnyk_me({"word": "хата", "dict": "vts"}))
        text = result[0].text
        assert "unavailable" in text
        assert "No entry found" not in text
        assert "HTTP 403" in text
        assert "Cloudflare challenge detected" in text

    def test_slovnyk_me_200_challenge_renders_unavailable(self, server_module):
        """HTTP 200 Cloudflare challenge renders unavailable with challenge note (#9016)."""
        unavailable = {
            "status": "unavailable",
            "word": "хата",
            "dict": "vts",
            "url": "https://slovnyk.me/dict/vts/хата",
            "challenge": True,
            "http_status": 200,
        }
        with patch("rag.source_query.slovnyk_me_lookup", return_value=unavailable):
            result = _run(server_module.handle_query_slovnyk_me({"word": "хата", "dict": "vts"}))
        text = result[0].text
        assert "unavailable" in text
        assert "No entry found" not in text
        assert "HTTP 200" in text
        assert "Cloudflare challenge detected" in text

    def test_slovnyk_me_not_found_still_renders_no_entry(self, server_module):
        not_found = {"status": "not_found", "word": "жжжнемає", "dict": "vts", "url": "https://slovnyk.me/dict/vts/жжжнемає"}
        with patch("rag.source_query.slovnyk_me_lookup", return_value=not_found):
            result = _run(server_module.handle_query_slovnyk_me({"word": "жжжнемає", "dict": "vts"}))
        assert "No entry found" in result[0].text

    def test_r2u_unavailable_is_not_rendered_as_no_translation(self, server_module):
        from rag.source_query import R2ULookupStatus

        with patch(
            "rag.source_query.r2u_translate_with_status",
            return_value=(R2ULookupStatus.SOURCE_UNAVAILABLE, []),
        ):
            result = _run(server_module.handle_query_r2u({"word": "привет"}))
        assert "unavailable" in result[0].text
        assert "No r2u translation found" not in result[0].text

    def test_r2u_not_found_still_renders_no_translation(self, server_module):
        from rag.source_query import R2ULookupStatus

        with patch(
            "rag.source_query.r2u_translate_with_status",
            return_value=(R2ULookupStatus.NOT_FOUND_WITHIN_VERIFIED_COVERAGE, []),
        ):
            result = _run(server_module.handle_query_r2u({"word": "жжжнемає"}))
        assert "No r2u translation found" in result[0].text

    def test_e2u_unavailable_is_not_rendered_as_no_translation(self, server_module):
        from rag.source_query import E2ULookupStatus

        with patch(
            "rag.source_query.e2u_translate_with_status",
            return_value=(E2ULookupStatus.SOURCE_UNAVAILABLE, []),
        ):
            result = _run(server_module.handle_query_e2u({"word": "house"}))
        assert "unavailable" in result[0].text
        assert "No e2u translation found" not in result[0].text

    def test_e2u_not_found_still_renders_no_translation(self, server_module):
        from rag.source_query import E2ULookupStatus

        with patch(
            "rag.source_query.e2u_translate_with_status",
            return_value=(E2ULookupStatus.NOT_FOUND_WITHIN_VERIFIED_COVERAGE, []),
        ):
            result = _run(server_module.handle_query_e2u({"word": "zzznotaword"}))
        assert "No e2u translation found" in result[0].text

    def test_grac_concordance_unavailable_is_not_rendered_as_no_results(self, server_module):
        with patch("rag.source_query.grac_concordance", return_value=None):
            result = _run(
                server_module.handle_query_grac({"query": "книга", "mode": "concordance"})
            )
        assert "unavailable" in result[0].text
        assert "No concordance results" not in result[0].text

    def test_grac_concordance_not_found_still_renders_no_results(self, server_module):
        with patch("rag.source_query.grac_concordance", return_value=[]):
            result = _run(
                server_module.handle_query_grac({"query": "zzznotaword", "mode": "concordance"})
            )
        assert "No concordance results" in result[0].text

    def test_grac_collocations_unavailable_is_not_rendered_as_no_results(self, server_module):
        with patch("rag.source_query.grac_collocations", return_value=None):
            result = _run(
                server_module.handle_query_grac({"query": "книга", "mode": "collocations"})
            )
        assert "unavailable" in result[0].text
        assert "No collocations found" not in result[0].text

    def test_grac_frequency_unavailable_is_not_rendered_as_zero_freq(self, server_module):
        with patch("rag.source_query.grac_frequency", return_value=None):
            result = _run(
                server_module.handle_query_grac({"query": "книга", "mode": "frequency"})
            )
        assert "unavailable" in result[0].text


class TestCallToolDispatch:
    """Test that call_tool routes to correct handlers."""

    def test_unknown_tool_returns_error(self, server_module):
        result = _run(server_module.call_tool("nonexistent_tool", {}))
        assert len(result) == 1
        assert "Unknown tool" in result[0].text

    def test_verify_word_dispatches(self, server_module):
        with patch.object(server_module, "handle_verify_word", new_callable=AsyncMock) as mock:
            mock.return_value = [MagicMock(text="ok")]
            _run(server_module.call_tool("verify_word", {"word": "тест"}))
            mock.assert_called_once_with({"word": "тест"})

    def test_verify_source_attribution_dispatches(self, server_module):
        with patch.object(server_module, "handle_verify_source_attribution", new_callable=AsyncMock) as mock:
            mock.return_value = [MagicMock(text="ok")]
            args = {"source": "grinchenko_1907", "claim": "коза"}
            _run(server_module.call_tool("verify_source_attribution", args))
            mock.assert_called_once_with(args)

    def test_verify_words_dispatches(self, server_module):
        with patch.object(server_module, "handle_verify_words", new_callable=AsyncMock) as mock:
            mock.return_value = [MagicMock(text="ok")]
            _run(server_module.call_tool("verify_words", {"words": ["тест"]}))
            mock.assert_called_once_with({"words": ["тест"]})

    def test_inspect_word_dispatches(self, server_module):
        with patch.object(server_module, "handle_inspect_word", new_callable=AsyncMock) as mock:
            mock.return_value = [MagicMock(text="ok")]
            _run(server_module.call_tool("inspect_word", {"word": "тест"}))
            mock.assert_called_once_with({"word": "тест"})

    def test_inspect_words_dispatches(self, server_module):
        with patch.object(server_module, "handle_inspect_words", new_callable=AsyncMock) as mock:
            mock.return_value = [MagicMock(text="ok")]
            _run(server_module.call_tool("inspect_words", {"words": ["тест"]}))
            mock.assert_called_once_with({"words": ["тест"]})

    def test_inspect_lemma_dispatches(self, server_module):
        with patch.object(server_module, "handle_inspect_lemma", new_callable=AsyncMock) as mock:
            mock.return_value = [MagicMock(text="ok")]
            _run(server_module.call_tool("inspect_lemma", {"lemma": "тест"}))
            mock.assert_called_once_with({"lemma": "тест"})

    def test_vet_vocabulary_dispatches(self, server_module):
        with patch.object(server_module, "handle_vet_vocabulary", new_callable=AsyncMock) as mock:
            mock.return_value = [MagicMock(text="ok")]
            args = {"words": ["тест"], "include_definitions": True}
            _run(server_module.call_tool("vet_vocabulary", args))
            mock.assert_called_once_with(args)

    def test_verify_quote_dispatches(self, server_module):
        with patch.object(server_module, "handle_verify_quote", new_callable=AsyncMock) as mock:
            mock.return_value = [MagicMock(text="ok")]
            _run(server_module.call_tool("verify_quote", {"author": "Шевченко", "text": "Та в Сибір загнали"}))
            mock.assert_called_once_with({"author": "Шевченко", "text": "Та в Сибір загнали"})

    def test_search_sources_dispatches(self, server_module):
        with patch.object(server_module, "handle_search_sources", new_callable=AsyncMock) as mock:
            mock.return_value = [MagicMock(text="ok")]
            _run(server_module.call_tool("search_sources", {"query": "голосні звуки"}))
            mock.assert_called_once_with({"query": "голосні звуки"})

    def test_search_text_handler_passes_subject_filter(self, server_module):
        hit = {
            "chunk_id": "chunk-1",
            "title": "Родовий відмінок",
            "section_title": "Родовий відмінок",
            "grade": "5",
            "author": "Авраменко",
            "subject": "ukrmova",
            "text": "Родовий відмінок у шкільному підручнику.",
        }
        with patch("wiki.sources_db.search_textbooks", return_value=[hit]) as mock:
            content, _envelope = _run(
                server_module.handle_search_text({"query": "родовий відмінок", "subject": "ukrmova", "limit": 3})
            )

        assert "Subject**: ukrmova" in content[0].text
        mock.assert_called_once()
        args, kwargs = mock.call_args
        assert "родовий" in args[0]
        assert args[1] == 3
        assert kwargs["subject"] == "ukrmova"

    def test_search_grinchenko_1907_dispatches(self, server_module):
        with patch.object(server_module, "handle_dict_search", new_callable=AsyncMock) as mock:
            mock.return_value = [MagicMock(text="ok")]
            _run(server_module.call_tool("search_grinchenko_1907", {"query": "тест"}))
            mock.assert_called_once_with({"query": "тест"}, "grinchenko_dict", "Грінченко")

    def test_search_slovnyk_me_dispatches(self, server_module):
        with patch.object(server_module, "handle_search_slovnyk_me", new_callable=AsyncMock) as mock:
            mock.return_value = [MagicMock(text="ok")]
            _run(server_module.call_tool("search_slovnyk_me", {"query": "тест"}))
            mock.assert_called_once_with({"query": "тест"})

    def test_search_heritage_dispatches(self, server_module):
        with patch.object(server_module, "handle_search_heritage", new_callable=AsyncMock) as mock:
            mock.return_value = [MagicMock(text="ok")]
            _run(server_module.call_tool("search_heritage", {"query": "тест"}))
            mock.assert_called_once_with({"query": "тест"})

    def test_check_modern_form_dispatches(self, server_module):
        with patch.object(server_module, "handle_check_modern_form", new_callable=AsyncMock) as mock:
            mock.return_value = [MagicMock(text="ok")]
            _run(server_module.call_tool("check_modern_form", {"word": "звір"}))
            mock.assert_called_once_with({"word": "звір"})

    def test_verify_stress_dispatches(self, server_module):
        with patch.object(server_module, "handle_verify_stress", new_callable=AsyncMock) as mock:
            mock.return_value = [MagicMock(text="ok")]
            _run(server_module.call_tool("verify_stress", {"word": "замок", "pos": "VERB"}))
            mock.assert_called_once_with({"word": "замок", "pos": "VERB"})

    def test_handler_exception_returns_error_text(self, server_module):
        with patch.object(server_module, "handle_verify_word", new_callable=AsyncMock) as mock:
            mock.side_effect = RuntimeError("test error")
            result = _run(server_module.call_tool("verify_word", {"word": "тест"}))
            assert len(result) == 1
            assert "RuntimeError" in result[0].text
            assert "test error" in result[0].text

    def test_search_esum_placeholder_hint(self, server_module):
        with patch("wiki.sources_db.search_esum", return_value=[]):
            result = _run(server_module.handle_search_esum({"query": "тест"}))
            assert len(result) == 1
            assert '"status": "not_implemented"' in result[0].text
            assert "goroh.pp.ua/Етимологія/тест" in result[0].text

    def test_query_sum20_formats_offline_official_records(self, server_module):
        record = {
            "source_id": "sum20_official",
            "source_record_id": "5",
            "stressed_headword": "АБАЖУ́Р",
            "pos": "ч.",
            "grammar": "а, ч.",
            "attribution_label": (
                "Словник української мови у 20 томах (УМІФ НАН України; "
                "Інститут мовознавства ім. О. О. Потебні НАН України)"
            ),
            "official_url": "https://sum20ua.com/?wordid=5",
            "retrieved_at": "2026-07-15T10:00:00+00:00",
            "content_sha256": "abc123",
            "parser_version": "sum20_official_v1",
            "status": "ok",
            "senses": [{"sense_order": 1, "definition": "Частина світильника", "register_labels": []}],
            "citations": [
                {
                    "citation_text": "На столику стояла свічка під абажуром",
                    "parsed_bib_fields": {"author": "Леся Українка"},
                }
            ],
        }
        with patch("wiki.sources_db.query_sum20", return_value=[record]) as mock:
            result = _run(server_module.handle_query_sum20({"word": "абажур"}))

        mock.assert_called_once_with("абажур")
        text = result[0].text
        assert "https://sum20ua.com/?wordid=5" in text
        assert "Леся Українка" in text
        assert "slovnyk.me" not in text


class TestVerifyWordHandler:
    """Test verify_word handler formatting."""

    def test_not_found(self, server_module):
        with patch("scripts.verification.vesum.verify_word", return_value=[]):
            content, outcome = _run(server_module.handle_verify_word({"word": "взяйте"}))
            assert "NOT FOUND" in content[0].text
            assert outcome["disposition"] == "not_found"
            assert outcome["success"] is False

    def test_found(self, server_module, monkeypatch):
        monkeypatch.setattr(server_module, "_vesum_source_version", lambda: VESUM_FIXTURE_VERSION)
        mock_matches = [VESUM_FIXTURE_MATCH]
        with patch("scripts.verification.vesum.verify_word", return_value=mock_matches):
            content, outcome = _run(server_module.handle_verify_word({"word": "читай"}))
            assert "читати" in content[0].text
            assert "verb" in content[0].text
            assert "1 analysis (1 distinct lemma)" in content[0].text
            assert outcome["disposition"] == "supported"
            assert outcome["success"] is True
            assert outcome["result"] == {
                "word": "читай",
                "pos_filter": None,
                "matches": mock_matches,
            }
            assert outcome["evidence_identifiers"] == [server_module._typed_identifier("vesum", outcome["result"])]

    def test_found_refuses_unversioned_source(self, server_module, monkeypatch):
        monkeypatch.setattr(server_module, "_vesum_source_version", lambda: "vesum-source-unversioned")
        with (
            patch("scripts.verification.vesum.verify_word", return_value=[VESUM_FIXTURE_MATCH]),
            pytest.raises(server_module.v4_handlers.OperationRefused, match="Sources version unproved"),
        ):
            _run(server_module.handle_verify_word({"word": "читай"}))

    def test_passes_pos_filter(self, server_module):
        with patch("scripts.verification.vesum.verify_word", return_value=[]) as mock:
            content, outcome = _run(server_module.handle_verify_word({"word": "тест", "pos_filter": "noun"}))
            mock.assert_called_once_with("тест", "noun")
            assert "NOT FOUND" in content[0].text
            assert outcome["disposition"] == "not_found"
            assert outcome["success"] is False


class TestVerifyWordsHandler:
    """Test verify_words handler formatting."""

    def test_batch_results(self, server_module):
        mock_results = {
            "стій": [{"lemma": "стояти", "pos": "verb", "tags": "verb:imperf:impr:s:2"}],
            "взяйте": [],
        }
        with patch("scripts.verification.vesum.verify_words", return_value=mock_results):
            content, outcome = _run(server_module.handle_verify_words({"words": ["стій", "взяйте"]}))
            text = content[0].text
            assert "Found: 1/2" in text
            assert "**стій** — FOUND" in text
            assert "**взяйте** — NOT FOUND" in text
            assert outcome["disposition"] == "partial"
            assert outcome["success"] is False


class TestCheckModernFormHandler:
    """CI-visible shape guard for handle_check_modern_form (#8402)."""

    def test_found_word_shape(self, server_module, monkeypatch):
        monkeypatch.setattr(server_module, "_vesum_source_version", lambda: VESUM_FIXTURE_VERSION)
        mock_matches = [
            {"lemma": "сонце", "pos": "noun", "tags": "noun:inanim:n:v_naz"},
        ]
        with patch("scripts.verification.vesum.verify_word", return_value=mock_matches):
            result = _run(server_module.handle_check_modern_form({"word": "сонце"}))
        assert isinstance(result, tuple) and len(result) == 2
        content, outcome = result
        assert isinstance(content, list)
        assert len(content) == 1
        assert isinstance(content[0], TextContent)
        data = json.loads(content[0].text)
        assert data["is_modern_codified"] is True
        assert data["has_archaic_form"] is False
        assert data["has_only_archaic_form"] is False
        assert isinstance(outcome, dict)
        assert outcome["tool"] == "check_modern_form"
        assert outcome["disposition"] == "supported"
        assert outcome["success"] is True

    def test_not_found_word_shape(self, server_module):
        with patch("scripts.verification.vesum.verify_word", return_value=[]):
            result = _run(server_module.handle_check_modern_form({"word": "невідоме"}))
        assert isinstance(result, tuple) and len(result) == 2
        content, outcome = result
        assert isinstance(content, list)
        assert len(content) == 1
        assert isinstance(content[0], TextContent)
        data = json.loads(content[0].text)
        assert data["is_modern_codified"] is False
        assert data["has_archaic_form"] is False
        assert data["has_only_archaic_form"] is False
        assert data["error"] == "Word not found in VESUM."
        assert isinstance(outcome, dict)
        assert outcome["tool"] == "check_modern_form"
        assert outcome["disposition"] == "not_found"
        assert outcome["success"] is False

    @pytest.mark.parametrize("invalid_args", [{"word": ""}, {"word": None}, {}, {"word": "   "}])
    def test_invalid_input_shape(self, server_module, invalid_args):
        result = _run(server_module.handle_check_modern_form(invalid_args))
        assert isinstance(result, tuple) and len(result) == 2
        content, outcome = result
        assert isinstance(content, list)
        assert len(content) == 1
        assert isinstance(content[0], TextContent)
        assert isinstance(outcome, dict)
        assert outcome["tool"] == "check_modern_form"
        assert outcome["disposition"] == "invalid_input"
        assert outcome["success"] is False

    def test_archaic_only_shape(self, server_module):
        mock_matches = [
            {"lemma": "старий", "pos": "adj", "tags": "adj:m:v_naz:arch"},
        ]
        with patch("scripts.verification.vesum.verify_word", return_value=mock_matches):
            result = _run(server_module.handle_check_modern_form({"word": "старий"}))
        assert isinstance(result, tuple) and len(result) == 2
        content, outcome = result
        assert isinstance(content, list)
        assert len(content) == 1
        assert isinstance(content[0], TextContent)
        data = json.loads(content[0].text)
        assert data["is_modern_codified"] is False
        assert data["has_archaic_form"] is True
        assert data["has_only_archaic_form"] is True
        assert isinstance(outcome, dict)
        assert outcome["tool"] == "check_modern_form"
        assert outcome["disposition"] == "negative"
        assert outcome["success"] is False


class TestVerifyStressHandler:
    """Test the verify_stress handler wires args through. The text channel is a one-line summary while the structured result keeps the full payload (#6515)."""

    def test_returns_summary_prose_and_retains_structured_result(self, server_module):
        payload = {
            "input": "замок",
            "lookup_key": "замок",
            "status": "ambiguous",
            "matches": [],
            "unresolvable_by_tags": True,
            "source": {"dictionary": "ukrainian-word-stress (ULIF-derived)"},
        }
        with patch("scripts.verification.stress.verify_stress", return_value=payload) as mock:
            content, outcome = _run(server_module.handle_verify_stress({"word": "замок"}))
            mock.assert_called_once_with("замок", None, None)
            assert outcome["result"] == payload
            assert outcome["summary_prose"] == content[0].text
            assert "\n" not in content[0].text
            assert not content[0].text.lstrip().startswith("{")
            assert "замок" in content[0].text
            assert "ambiguous" in content[0].text
            assert outcome["disposition"] == "ambiguous"
            assert outcome["success"] is False

    def test_passes_pos_and_tags(self, server_module):
        with patch("scripts.verification.stress.verify_stress", return_value={}) as mock:
            content, outcome = _run(
                server_module.handle_verify_stress({"word": "замок", "pos": "VERB", "tags": "Number=Sing"})
            )
            mock.assert_called_once_with("замок", "VERB", "Number=Sing")
            assert outcome["result"] == {}
            assert outcome["summary_prose"] == content[0].text
            assert not content[0].text.lstrip().startswith("{")
            assert outcome["disposition"] == "negative"
            assert outcome["success"] is False


@pytest.fixture
def vocabulary_vet_fixtures():
    """One fixture payload for each source that composite vocabulary vetting uses."""
    return {
        "vesum": {
            "кіт": [{"lemma": "кіт", "pos": "noun", "tags": "noun:anim:m:v_naz"}],
            "вигадане": [],
        },
        "cefr": {"кіт": [{"level": "A1"}], "вигадане": []},
        "shadow": {
            "кіт": {
                "matches_russian": False,
                "russian_lemma": None,
                "confidence": 0.0,
            },
            "вигадане": {
                "matches_russian": True,
                "russian_lemma": "выдуманный",
                "confidence": 0.91,
            },
        },
        "definitions": {
            "кіт": [{"definition": "КІТ, кота, ч. Свійська тварина родини котячих."}],
            "вигадане": [],
        },
    }


class TestVetVocabularyHandler:
    def test_reports_all_sources_and_missing_word(self, server_module, vocabulary_vet_fixtures):
        fixtures = vocabulary_vet_fixtures
        with (
            patch("scripts.verification.vesum.verify_words", return_value=fixtures["vesum"]) as verify_words,
            patch("wiki.sources_db.query_cefr_levels", return_value=fixtures["cefr"]) as query_cefr,
            patch(
                "scripts.verification.check_ru_morph.check_russian_patterns_batch",
                return_value=fixtures["shadow"],
            ) as check_shadow,
            patch(
                "wiki.sources_db.search_definitions_batch",
                return_value=fixtures["definitions"],
            ) as search_definitions,
        ):
            result = _run(
                server_module.handle_vet_vocabulary({"words": ["кіт", "вигадане"], "include_definitions": True})
            )

        text = result[0].text
        assert text.splitlines()[0].startswith("verification_authority: false (СУМ-11 excerpts only).")
        assert text.splitlines()[1] == (
            "- **кіт** | VESUM: valid (lemma=кіт, pos=noun, tags=noun:anim:m:v_naz) "
            "| CEFR: A1 | Russian-shadow: not flagged (suspicion only, not a verdict) "
            "| СУМ-11 contrast excerpt (verification_authority: false): КІТ, кота, ч. Свійська тварина родини котячих."
        )
        assert "**вигадане** | VESUM: not found" in text
        assert "Russian-shadow: suspected (suspicion only, not a verdict; russian_lemma=выдуманный" in text
        assert "СУМ-11 contrast excerpt (verification_authority: false): КІТ, кота, ч. Свійська тварина родини котячих." in text
        assert "СУМ-11 contrast excerpt (verification_authority: false): not found" in text
        verify_words.assert_called_once_with(["кіт", "вигадане"])
        query_cefr.assert_called_once_with(["кіт", "вигадане"])
        search_definitions.assert_called_once_with(["кіт", "вигадане"])
        check_shadow.assert_called_once_with(["кіт", "вигадане"], verified_words={"кіт"})

    def test_omits_gloss_without_definitions_toggle(self, server_module, vocabulary_vet_fixtures):
        fixtures = vocabulary_vet_fixtures
        with (
            patch("scripts.verification.vesum.verify_words", return_value=fixtures["vesum"]),
            patch("wiki.sources_db.query_cefr_levels", return_value=fixtures["cefr"]),
            patch(
                "scripts.verification.check_ru_morph.check_russian_patterns_batch",
                return_value=fixtures["shadow"],
            ),
            patch("wiki.sources_db.search_definitions_batch") as search_definitions,
        ):
            result = _run(server_module.handle_vet_vocabulary({"words": ["кіт"]}))

        assert "Gloss:" not in result[0].text
        assert "Russian-shadow: not flagged (suspicion only, not a verdict)" in result[0].text
        search_definitions.assert_not_called()

    def test_honestly_truncates_after_500_words(self, server_module):
        words = [f"слово-{index}" for index in range(501)]
        first_500 = words[:500]
        with (
            patch(
                "scripts.verification.vesum.verify_words", return_value={word: [] for word in first_500}
            ) as verify_words,
            patch("wiki.sources_db.query_cefr_levels", return_value={}),
            patch(
                "scripts.verification.check_ru_morph.check_russian_patterns_batch",
                return_value={word: {"matches_russian": False} for word in first_500},
            ),
        ):
            result = _run(server_module.handle_vet_vocabulary({"words": words}))

        text = result[0].text
        assert text.startswith("Note: received 501 words; processed the first 500 (hard cap).")
        assert "**слово-499**" in text
        assert "**слово-500**" not in text
        verify_words.assert_called_once_with(first_500)


def _shevchenko_quote_hits():
    # Known-good source confirmed with mcp__sources__search_literary:
    # query="загнали в Сибір", chunk_id=d1b5c8a6_c0084, author="Шевченко Т."
    return [
        {
            "chunk_id": "d1b5c8a6_c0084",
            "title": "",
            "author": "Шевченко Т.",
            "year": 1814,
            "source_file": "ukrlib-shevchenko",
            "text": (
                "Що розлили з річку крові\n\nТа в Сибір загнали\n\nСвою шляхту, то вже й годі,\n\nУже й запишались."
            ),
        },
        {
            "chunk_id": "9976239a_c0473",
            "title": "",
            "author": "Шевченко Т.",
            "year": 1961,
            "source_file": "wave10-shevchenko-tvory-t1",
            "text": "Сибір неісходима,\n\nА тюрм, а люду! що й казать!",
        },
        {
            "chunk_id": "other_shevchenko",
            "title": "Садок вишневий коло хати",
            "author": "Т. Г. Шевченко",
            "year": 1847,
            "source_file": "fixture",
            "text": "Садок вишневий коло хати,\n\nХрущі над вишнями гудуть.",
        },
    ]


class TestVerifyQuoteHandler:
    """Test verify_quote fuzzy attribution checks."""

    def test_known_good_shevchenko_line_matches(self, server_module):
        with patch("wiki.sources_db.search_literary", return_value=_shevchenko_quote_hits()):
            result = _run(
                server_module.handle_verify_quote({"author": "Шевченко", "text": "Та в Сибір загнали Свою шляхту"})
            )
        data = json.loads(result[0].text)
        assert data["matched"] is True
        assert data["best_confidence"] >= 0.90
        assert data["matched_lines"][0]["context_chunk_id"] == "d1b5c8a6_c0084"

    def test_fabricated_fused_quote_returns_near_misses(self, server_module):
        with patch("wiki.sources_db.search_literary", return_value=_shevchenko_quote_hits()):
            result = _run(
                server_module.handle_verify_quote({"author": "Шевченко", "text": "Загнали в Сибір неісходиму"})
            )
        data = json.loads(result[0].text)
        assert data["matched"] is False
        assert len(data["matched_lines"]) == 3
        assert data["matched_lines"][0]["confidence"] < 0.80

    def test_author_variants_find_same_line(self, server_module):
        matched_ids = []
        for author in ["Шевченко", "Т. Г. Шевченко", "Тарас Шевченко"]:
            with patch("wiki.sources_db.search_literary", return_value=_shevchenko_quote_hits()):
                result = _run(
                    server_module.handle_verify_quote({"author": author, "text": "Та в Сибір загнали Свою шляхту"})
                )
            data = json.loads(result[0].text)
            assert data["matched"] is True
            matched_ids.append(data["matched_lines"][0]["context_chunk_id"])
        assert matched_ids == ["d1b5c8a6_c0084"] * 3

    def test_empty_text_returns_clean_error(self, server_module):
        result = _run(server_module.call_tool("verify_quote", {"author": "Шевченко", "text": ""}))
        assert "ValueError: text is required" in result[0].text
        assert "Traceback" not in result[0].text


class TestVerifySourceAttributionHandler:
    """Test verify_source_attribution handler routing and verdicts."""

    def test_grinchenko_1907_discusses_koza(self, server_module):
        with patch(
            "wiki.sources_db.search_grinchenko_1907",
            return_value=[{"headword": "коза", "definition": "коза — свійська тварина"}],
        ) as mock:
            result = _run(
                server_module.handle_verify_source_attribution({"source": "grinchenko_1907", "claim": "коза"})
            )

        mock.assert_called_once_with("коза", 5)
        data = json.loads(result[0].text)
        assert data["discusses"] is True
        assert data["evidence_count"] >= 1

    def test_antonenko_fake_claim_returns_completeness_note(self, server_module):
        with patch("wiki.sources_db.search_style_guide", return_value=[]) as mock:
            result = _run(
                server_module.handle_verify_source_attribution(
                    {"source": "antonenko_davydovych", "claim": "thisisdefinitelyfake999"}
                )
            )

        mock.assert_called_once_with("thisisdefinitelyfake999", 5)
        data = json.loads(result[0].text)
        assert data["discusses"] is False
        assert "completeness_note" in data

    def test_sum11_leninizm_discusses_with_sovietization_note(self, server_module):
        with patch(
            "wiki.sources_db.search_definitions",
            return_value=[{"headword": "ленінізм", "definition": "ленінізм — політичне вчення"}],
        ) as mock:
            result = _run(server_module.handle_verify_source_attribution({"source": "sum11", "claim": "ленінізм"}))

        mock.assert_called_once_with("ленінізм", 5)
        data = json.loads(result[0].text)
        assert data["discusses"] is False
        assert data["contrast_match"] is True
        assert data["verification_authority"] is False
        assert data["evidence"][0]["verification_authority"] is False
        assert "contrast only" in data["notice"]
        assert "sovietization_risk" in data["completeness_note"]

    def test_invalid_source_returns_clean_error(self, server_module):
        result = _run(
            server_module.call_tool(
                "verify_source_attribution",
                {"source": "not_a_source", "claim": "коза"},
            )
        )

        assert len(result) == 1
        assert "Invalid source" in result[0].text
        assert "Traceback" not in result[0].text

    def test_empty_claim_returns_clean_error(self, server_module):
        result = _run(
            server_module.call_tool(
                "verify_source_attribution",
                {"source": "grinchenko_1907", "claim": " "},
            )
        )

        assert len(result) == 1
        assert "claim must be a non-empty string" in result[0].text
        assert "Traceback" not in result[0].text

    def test_wikipedia_route_uses_query_wikipedia_handler(self, server_module):
        text = "Wikipedia search: 'тест' — 1 results\n\n1. **Тест** — тестова сторінка"
        with patch.object(server_module, "handle_query_wikipedia", new_callable=AsyncMock) as mock:
            mock.return_value = [MagicMock(text=text)]
            result = _run(
                server_module.handle_verify_source_attribution({"source": "wikipedia", "claim": "тест", "limit": 2})
            )

        mock.assert_called_once_with({"query": "тест", "mode": "search", "limit": 2})
        assert json.loads(result[0].text)["discusses"] is True

    def test_wikipedia_route_failure_returns_completeness_note(self, server_module):
        with patch.object(server_module, "handle_query_wikipedia", new_callable=AsyncMock) as mock:
            mock.side_effect = RuntimeError("network down")
            result = _run(
                server_module.handle_verify_source_attribution({"source": "wikipedia", "claim": "тест", "limit": 2})
            )

        data = json.loads(result[0].text)
        assert data["discusses"] is False
        assert data["evidence_count"] == 0
        assert data["completeness_note"] == "Wikipedia query failed: network down"


class TestSearchSourcesHandler:
    """Test search_sources handler formatting."""

    def test_empty_results(self, server_module):
        with patch("wiki.sources_db.search_sources", return_value=[]):
            content, envelope = _run(server_module.handle_search_sources({"query": "голосні звуки"}))
            assert content[0].text == "No results found."
            assert envelope["status"] == "empty"
            assert envelope["match_count"] == 0
            assert envelope["hits"] == []

    def test_defaults_track_to_empty_string(self, server_module):
        with patch("wiki.sources_db.search_sources", return_value=[]) as mock:
            _run(server_module.handle_search_sources({"query": "голосні звуки"}))
            mock.assert_called_once_with("голосні звуки", track="", limit=10)

    def test_returns_json_payload(self, server_module):
        mock_hits = [
            {
                "chunk_id": "ukwiki:test-1",
                "corpus": "ukrainian_wiki",
                "title": "Голосні звуки",
                "text": "Голосні звуки творяться без перешкод.",
                "final_score": 0.91,
                "ranking": "keyword_rrf",
            }
        ]
        with patch("wiki.sources_db.search_sources", return_value=mock_hits) as mock:
            content, envelope = _run(
                server_module.handle_search_sources({"query": "голосні звуки", "track": "a1", "limit": 5})
            )
            mock.assert_called_once_with("голосні звуки", track="a1", limit=5)
            assert '"corpus": "ukrainian_wiki"' in content[0].text
            assert '"chunk_id": "ukwiki:test-1"' in content[0].text
            assert envelope["status"] == "ok"
            assert envelope["match_count"] == 1
            assert envelope["hits"][0]["chunk_id"] == "ukwiki:test-1"
            assert envelope["hits"][0]["ranking"] == "keyword_rrf"
            assert envelope["ranking"] == "keyword_rrf"

    def test_top_level_ranking_is_mixed_when_hits_differ(self, server_module):
        mock_hits = [
            {"corpus": "textbook_sections", "text": "Textbook hit", "ranking": "dense"},
            {"corpus": "modern_literary", "text": "Literary hit", "ranking": "keyword_rrf"},
        ]
        with patch("wiki.sources_db.search_sources", return_value=mock_hits):
            _, envelope = _run(server_module.handle_search_sources({"query": "слово"}))

        assert envelope["ranking"] == "mixed"

    def test_top_level_ranking_is_omitted_without_hit_metadata(self, server_module):
        archaic_hit = {"corpus": "archaic_literary", "text": "Archaic hit"}
        with patch("wiki.sources_db.search_sources", return_value=[archaic_hit]):
            _, envelope = _run(server_module.handle_search_sources({"query": "слово"}))

        assert "ranking" not in envelope


class TestCheckRussianShadowHandler:
    def test_handle_check_russian_shadow(self, server_module):
        with patch("scripts.verification.vesum.verify_word") as mock_verify_word:

            def mock_vesum(w):
                if w in ["получити", "здача"]:
                    return []
                return [{"lemma": w, "pos": "noun", "tags": ""}]

            mock_verify_word.side_effect = mock_vesum

            args = {"word": "получити", "threshold": 0.7}
            res = _run(server_module.handle_check_russian_shadow(args))

            assert len(res) == 1
            data = json.loads(res[0].text)
            assert data["matches_russian"] is True

            args = {"word": "привіт", "threshold": 0.7}
            res = _run(server_module.handle_check_russian_shadow(args))

            data = json.loads(res[0].text)
            assert data["matches_russian"] is False


_VESUM_DB = Path(__file__).resolve().parents[1] / "data" / "vesum.db"


@pytest.mark.skipif(
    not _VESUM_DB.exists(),
    reason="VESUM DB not present in CI sandbox — run locally for smoke coverage",
)
class TestIntegrationSmoke:
    """Smoke tests using real database (no mocks). Skipped when data/vesum.db absent."""

    def test_smoke_verify_word_archaic(self, server_module):
        """Test verify_word with a word that has an archaic tag."""
        content, outcome = _run(server_module.handle_verify_word({"word": "звір"}))
        assert "**is_archaic**: True" in content[0].text
        assert "**is_archaic**: False" in content[0].text  # Because it has modern forms too
        assert outcome["disposition"] == "supported"
        assert outcome["success"] is True

    def test_smoke_verify_lemma_archaic(self, server_module):
        """Test verify_lemma with a lemma that has archaic forms."""
        content, outcome = _run(server_module.handle_verify_lemma({"lemma": "звір"}))
        assert "has_archaic_forms: True" in content[0].text
        assert "**is_archaic**: True" in content[0].text
        assert outcome["disposition"] == "supported"
        assert outcome["success"] is True

    def test_smoke_check_modern_form_mixed(self, server_module):
        """Test check_modern_form with a word that has both modern and archaic tags."""
        content, outcome = _run(server_module.handle_check_modern_form({"word": "звір"}))
        data = json.loads(content[0].text)
        assert data["is_modern_codified"] is True
        assert data["has_archaic_form"] is True
        assert data["has_only_archaic_form"] is False
        assert outcome["tool"] == "check_modern_form"
        assert outcome["disposition"] == "supported"
        assert outcome["success"] is True

    def test_smoke_check_modern_form_modern_only(self, server_module):
        """Test check_modern_form with a modern-only word."""
        content, outcome = _run(server_module.handle_check_modern_form({"word": "Сибір"}))
        data = json.loads(content[0].text)
        assert data["is_modern_codified"] is True
        assert data["has_archaic_form"] is False
        assert data["has_only_archaic_form"] is False
        assert outcome["tool"] == "check_modern_form"
        assert outcome["disposition"] == "supported"
        assert outcome["success"] is True

    def test_smoke_check_modern_form_archaic_only(self, server_module):
        """Test check_modern_form with an archaic-only word."""
        content, outcome = _run(server_module.handle_check_modern_form({"word": "аби-де"}))
        data = json.loads(content[0].text)
        assert data["is_modern_codified"] is False
        assert data["has_archaic_form"] is True
        assert data["has_only_archaic_form"] is True
        assert outcome["tool"] == "check_modern_form"
        assert outcome["disposition"] == "negative"
        assert outcome["success"] is False


class TestDictSearchQuoteBalance:
    """Test _quote_balanced_clip and handle_dict_search quote balancing (#7026)."""

    def test_clip_short_text_unchanged(self, server_module):
        short = "Короткий текст"
        assert server_module._quote_balanced_clip(short, 500) == short

    def test_clip_without_quotes_adds_ellipsis(self, server_module):
        long_text = "а" * 600
        clipped = server_module._quote_balanced_clip(long_text, 500)
        assert len(clipped) == 501  # 500 + '…'
        assert clipped.endswith("…")

    def test_clip_preserves_guillemets_lookahead(self, server_module):
        # Open quote inside first 500 chars, closing quote within lookahead (at 520)
        base = "Початок " + "а" * 470 + " «цитата на двадцять слів» продовження"
        clipped = server_module._quote_balanced_clip(base, 500)
        assert "«цитата на двадцять слів»" in clipped
        assert clipped.count("«") == clipped.count("»")

    def test_clip_trims_before_unclosed_quote_when_closing_too_far(self, server_module):
        # Open quote at char 480, but closing quote is 300 chars away
        base = "Початок " + "а" * 470 + " «дуже довга цитата " + "б" * 300 + "»"
        clipped = server_module._quote_balanced_clip(base, 500)
        assert "«" not in clipped
        assert clipped.count("«") == clipped.count("»")

    def test_clip_opener_at_cut_start_trimmed_when_unclosed(self, server_module):
        # Opening quote at index 0 when cut is before closing quote (#7026, #7038)
        text = "«" + "а" * 600 + "»"
        clipped = server_module._quote_balanced_clip(text, 100)
        assert "«" not in clipped
        assert clipped.count("«") == clipped.count("»")
        assert clipped == "…"

    def test_clip_nested_unclosed_quotes_iteratively_trimmed(self, server_module):
        # Nested unclosed quotes are iteratively trimmed until balanced (#7026, #7038)
        text = "Початок «перша «друга " + "а" * 600 + "»»"
        clipped = server_module._quote_balanced_clip(text, 100)
        assert "«" not in clipped
        assert clipped.count("«") == clipped.count("»")
        assert clipped == "Початок…"

    def test_handle_dict_search_clips_long_definitions(self, server_module):
        hit = {
            "word": "тест",
            "definition": "Початок " + "а" * 600,
        }
        with patch("wiki.sources_db.search_definitions", return_value=[hit]):
            content, envelope = _run(server_module.handle_dict_search({"query": "тест"}, "sum11", "СУМ-11"))
            text = content[0].text
            assert "Found 1 results" in text
            assert "…" in text
            excerpt = next(line for line in text.splitlines() if line.startswith("- **Contrast excerpt**:"))
            assert len(excerpt) < 530
            assert envelope["schema"] == "sources.tool-result.v1"
            assert envelope["match_count"] == 1
            assert envelope["tool"] == "search_definitions"
            assert envelope["hits"][0]["verification_authority"] is False
            assert "contrast only" in envelope["hits"][0]["notice"]
            assert "verification_authority: false" in text
            assert "**Contrast excerpt**" in text

    def test_handle_dict_search_labels_each_homonym_sense(self, server_module):
        hits = [
            {"word": "За́мок", "sense_gloss": "(населений пункт в Україні)", "definition": "місто"},
            {"word": "за́мок", "sense_gloss": "(будівля)", "definition": "фортеця"},
        ]
        with patch("wiki.sources_db.search_idioms", return_value=hits):
            content, envelope = _run(
                server_module.handle_dict_search({"query": "замок"}, "frazeolohichnyi", "Фразеологічний")
            )
        text = content[0].text
        assert "Found 2 results" in text
        assert "- **Headword**: За́мок" in text
        assert "- **Sense**: (населений пункт в Україні)" in text
        assert "- **Headword**: за́мок" in text
        assert "- **Sense**: (будівля)" in text
        assert envelope["match_count"] == 2

    def test_ulif_relation_tools_render_every_ambiguous_homonym(self, server_module):
        ambiguous = {"status": "ambiguous", "entries": [{"homonym_index": 1}, {"homonym_index": 2}]}
        records = [
            {
                "homonym_index": 1,
                "canonical_headword": "За́мок",
                "sense_gloss": "(населений пункт в Україні)",
                "sections": {"synonyms": [{"terms": [{"text": "МІСТО"}]}]},
            },
            {
                "homonym_index": 2,
                "canonical_headword": "за́мок",
                "sense_gloss": "(будівля)",
                "sections": {"synonyms": [{"terms": [{"text": "КРЕМЛЬ"}]}]},
            },
        ]
        with (
            patch("rag.source_query.query_ulif_synonyms", return_value=ambiguous),
            patch("wiki.sources_db.search_ulif_dictua_sections", return_value=records),
        ):
            content = _run(server_module.handle_query_ulif_synonyms({"word": "замок"}))
        text = content[0].text
        assert "1: За́мок (населений пункт в Україні)" in text
        assert "2: за́мок (будівля)" in text
        assert "КРЕМЛЬ" in text
        assert "МІСТО" in text
        assert '"terms"' in text


def _wikipedia_page_body(text: str) -> str:
    """Article slice after the extract page header."""
    header, _, body = text.partition("\n\n")
    assert "**Next offset**:" in header
    return body


def _wikipedia_header_value(text: str, label: str) -> str:
    prefix = f"**{label}**: "
    for line in text.splitlines():
        if line.startswith(prefix):
            return line[len(prefix):]
    raise AssertionError(f"missing {label} in {text!r}")


def _multi_page_cyrillic_article() -> tuple[str, int, int]:
    """Article whose first nominal page-end falls inside «Київщина».

    Returns the article, the word-boundary cut, and the later paragraph cut.
    The first page's last 20% has no paragraph or sentence boundary. The next
    page has a paragraph break inside its last 20%, and that break is the
    rightmost one in the window.
    """
    page = 1000
    word = "Київщина"
    word_at = 995
    prefix = "мова " * (word_at // len("мова "))
    assert len(prefix) == word_at and prefix.endswith(" ")
    head = prefix + word
    assert head[page - 1].isalpha() and head[page].isalpha()
    assert head[word_at:word_at + len(word)] == word

    # Page 2 starts at word_at. Its nominal end is word_at + page, so the last
    # 20% begins 200 characters earlier. The paragraph cut sits inside that tail.
    paragraph_cut = 1902
    target = paragraph_cut - 2
    sentence = "Речення про мову. "
    span = target - len(head)
    filler = sentence * (span // len(sentence))
    gap_fill = "б" * (span - len(filler))
    middle = filler + gap_fill + "\n\n"
    assert len(head) + len(middle) == paragraph_cut
    hard_end = word_at + page
    quiet = ("абвгд " * 40)[: hard_end - paragraph_cut]
    assert "." not in quiet and "\n" not in quiet and "!" not in quiet and "?" not in quiet
    rest = "Ще одне речення про історію мови. " * 120
    article = head + middle + quiet + rest
    assert paragraph_cut < hard_end < len(article)
    return article, word_at, paragraph_cut


class TestWikipediaExtractPaging:
    """mode=extract returns the article in lossless pages (#8524)."""

    def _memory_cache(self):
        store: dict[tuple[str, str], str] = {}

        def get(mode, title, section=""):
            return store.get((mode, title))

        def put(mode, title, response, section=""):
            store[(mode, title)] = response

        cache = MagicMock()
        cache.get.side_effect = get
        cache.put.side_effect = put
        cache.is_negative.return_value = False
        return cache, store

    def _fetch(self, server_module, body: str, args: dict, *, cache):
        article = {
            "title": "Стаття",
            "url": "https://uk.wikipedia.org/wiki/Стаття",
            "extract": body,
        }
        with (
            patch("rag.wiki_cache.WikiCache", return_value=cache),
            patch("rag.source_query.wikipedia_extract", return_value=article) as extract,
        ):
            content = _run(server_module.handle_query_wikipedia({"query": "Стаття", "mode": "extract", **args}))
        return content[0].text, extract

    def test_tool_schema_documents_paging(self, server_module):
        tools = _run(server_module.list_tools())
        tool = next(item for item in tools if item.name == "query_wikipedia")
        assert (
            "long articles are returned in pages; request the next page with offset=<Next offset>"
            in tool.description
        )
        assert "offset" in tool.input_schema["properties"]
        assert "max_chars" in tool.input_schema["properties"]
        assert tool.input_schema["properties"]["offset"]["default"] == 0
        assert tool.input_schema["properties"]["max_chars"]["default"] == 6000

    def test_pages_concatenate_and_do_not_split_the_cyrillic_word(self, server_module):
        article, word_at, paragraph_cut = _multi_page_cyrillic_article()
        page = server_module._WIKIPEDIA_EXTRACT_PAGE_MIN
        assert article[page - 1].isalpha() and article[page].isalpha()
        assert not article[:page].endswith("Київщина")

        cache, store = self._memory_cache()
        payload = {
            "title": "Стаття",
            "url": "https://uk.wikipedia.org/wiki/Стаття",
            "extract": article,
        }
        offset = 0
        parts: list[str] = []
        cuts: list[int] = []
        with (
            patch("rag.wiki_cache.WikiCache", return_value=cache),
            patch("rag.source_query.wikipedia_extract", return_value=payload) as extract,
        ):
            for _ in range(12):
                content = _run(
                    server_module.handle_query_wikipedia(
                        {
                            "query": "Стаття",
                            "mode": "extract",
                            "offset": offset,
                            "max_chars": page,
                        }
                    )
                )
                text = content[0].text
                assert text.startswith("# Стаття\n**URL**: https://uk.wikipedia.org/wiki/Стаття\n")
                start_s, end_s = _wikipedia_header_value(text, "Chars").split(" of ")[0].split("–")
                assert int(start_s) == offset
                body = _wikipedia_page_body(text)
                parts.append(body)
                nxt = _wikipedia_header_value(text, "Next offset")
                if nxt == "end":
                    assert body == article[offset:]
                    break
                end = int(nxt)
                assert end == int(end_s)
                assert offset < end <= offset + page
                assert body == article[offset:end]
                joined = "".join(parts)
                boundary = len(joined)
                assert article[boundary - 1].isspace() or article[boundary].isspace()
                cuts.append(end)
                offset = end
            else:
                raise AssertionError("paging did not reach the end")
            extract.assert_called_once()

        assert "".join(parts) == article
        assert cuts[0] == word_at
        assert "Київщина" in parts[1]
        assert "Київщина" not in parts[0]
        assert paragraph_cut in cuts
        assert len(parts) >= 3
        cached = store[("extract", "Стаття")]
        assert "**Chars**" not in cached
        assert "**Next offset**" not in cached
        assert "**Truncated**" not in cached
        assert server_module._split_cached_wikipedia_extract(cached)[2] == article

    def test_last_page_reports_end_and_past_the_end_is_empty(self, server_module):
        article, _, _ = _multi_page_cyrillic_article()
        cache, _store = self._memory_cache()
        text, _extract = self._fetch(
            server_module,
            article,
            {"offset": 0, "max_chars": 1000},
            cache=cache,
        )
        assert _wikipedia_header_value(text, "Next offset") != "end"

        past = len(article) + 40
        empty, extract = self._fetch(
            server_module,
            article,
            {"offset": past, "max_chars": 1000},
            cache=cache,
        )
        extract.assert_not_called()
        assert _wikipedia_header_value(empty, "Next offset") == "end"
        assert (
            f"This page is empty: offset {past} is past the end of the article "
            f"({len(article)} characters)."
        ) in empty
        assert "Київщина" not in _wikipedia_page_body(empty)

    def test_sentence_boundary_in_the_last_fifth_ends_the_page(self, server_module):
        prefix = "мова " * 160
        ending = "кінець речення. "
        article = prefix + ending + ("б" * 400)
        cut = server_module._wikipedia_extract_page_end(article, 0, 1000)
        assert cut == len(prefix) + len(ending)
        assert article[cut - 2:cut] == ". "

    def test_max_chars_is_clamped(self, server_module):
        body = "слово " * 5000
        cache, _store = self._memory_cache()
        low, _extract = self._fetch(server_module, body, {"max_chars": 10}, cache=cache)
        default, _extract = self._fetch(server_module, body, {}, cache=cache)
        high, _extract = self._fetch(server_module, body, {"max_chars": 999999}, cache=cache)
        spans = []
        for text in (low, default, high):
            start_s, end_s = _wikipedia_header_value(text, "Chars").split(" of ")[0].split("–")
            spans.append(int(end_s) - int(start_s))
        low_span, default_span, high_span = spans
        assert server_module._WIKIPEDIA_EXTRACT_PAGE_MIN - len("слово ") < low_span <= 1000
        assert low_span > 10
        assert 6000 - len("слово ") < default_span <= 6000
        assert 20000 - len("слово ") < high_span <= 20000
        assert high_span > 6000

    def test_cache_stores_the_full_article_and_serves_any_page(self, server_module):
        article, word_at, _paragraph_cut = _multi_page_cyrillic_article()
        cache, store = self._memory_cache()
        first, extract = self._fetch(
            server_module,
            article,
            {"offset": 0, "max_chars": 1000},
            cache=cache,
        )
        extract.assert_called_once()
        stored = store[("extract", "Стаття")]
        assert stored == server_module._wikipedia_full_extract_text(
            "Стаття",
            "https://uk.wikipedia.org/wiki/Стаття",
            article,
        )
        assert _wikipedia_page_body(first) == article[:word_at]

        later, extract_again = self._fetch(
            server_module,
            article,
            {"offset": word_at, "max_chars": 1000},
            cache=cache,
        )
        extract_again.assert_not_called()
        assert f"**Chars**: {word_at}–" in later
        assert _wikipedia_page_body(later).startswith("Київщина")
        assert store[("extract", "Стаття")] == stored

    def test_legacy_full_article_cache_is_paged_without_a_network_call(self, server_module):
        article, word_at, _paragraph_cut = _multi_page_cyrillic_article()
        legacy = "\n".join(
            ["# Стаття", "**URL**: https://uk.wikipedia.org/wiki/Стаття", "", article]
        )
        with (
            patch("rag.wiki_cache.WikiCache") as cache_cls,
            patch("rag.source_query.wikipedia_extract") as extract,
        ):
            cache_cls.return_value.get.return_value = legacy
            cache_cls.return_value.is_negative.return_value = False
            content = _run(
                server_module.handle_query_wikipedia(
                    {"query": "Стаття", "mode": "extract", "offset": word_at, "max_chars": 1000}
                )
            )
        extract.assert_not_called()
        text = content[0].text
        assert text.split("\n")[2].startswith("**Chars**: ")
        assert "**Truncated**" not in text
        assert _wikipedia_page_body(text).startswith("Київщина")


class TestHealthEndpoint:
    """Test health endpoint contract (#7026)."""

    def test_handle_health_response(self, server_module):
        app = server_module.create_http_app()
        # The HTTP app has two real middleware layers: attempt auth outside
        # the unsupported-method guard. Unwrap both before route inspection.
        while not hasattr(app, "routes"):
            app = app.app
        route_paths = {getattr(r, "path", None) for r in app.routes}
        assert "/health" in route_paths
        assert "/sse" not in route_paths
        assert "/messages/" not in route_paths
        routes = [r for r in app.routes if getattr(r, "path", None) == "/health"]
        assert len(routes) == 1
        health_endpoint = routes[0].endpoint

        response = _run(health_endpoint(None))
        data = json.loads(response.body.decode("utf-8"))
        assert data["status"] == "ok"
        assert "commit_sha" in data
        assert "db_path" in data
        assert "sources.db" in data["db_path"]

    def test_repeated_health_calls_do_not_spawn_git(self, server_module):
        app = server_module.create_http_app()
        while not hasattr(app, "routes"):
            app = app.app
        endpoint = next(route.endpoint for route in app.routes if getattr(route, "path", None) == "/health")
        with patch("subprocess.run") as spawned:
            first = _run(endpoint(None))
            second = _run(endpoint(None))
        assert spawned.call_count == 0
        first_body = json.loads(first.body)
        second_body = json.loads(second.body)
        assert first_body["commit_sha"] == second_body["commit_sha"] == server_module._SERVER_GIT_COMMIT
        assert first_body["commit_sha"]

    def test_git_commit_failure_is_unknown(self, server_module, monkeypatch):
        def boom(*args, **kwargs):
            raise OSError("git missing")

        monkeypatch.setattr("subprocess.run", boom)
        assert server_module._detect_git_commit() == "unknown"


class TestCollectionStatsHandler:
    """Test collection_stats handler (#7026)."""

    def test_handle_collection_stats_dispatches(self, server_module):
        mock_stats = {
            "textbooks": 10,
            "esum_etymology": 20,
            "ua_gec_errors": 30,
            "sum20_articles": 40,
            "slovnyk_me_entries": 50,
            "wikipedia": 60,
        }
        with patch("wiki.sources_db.list_tables", return_value=mock_stats):
            result = _run(server_module.handle_collection_stats({}))
            data = json.loads(result[0].text)
            assert data["esum_etymology"] == 20
            assert data["ua_gec_errors"] == 30
            assert data["sum20_articles"] == 40
            assert data["slovnyk_me_entries"] == 50
            assert data["wikipedia"] == 60


class TestFileHashCaching:
    """Test _sha256_of_file caching, invalidation, replacement, and concurrency (#8221)."""

    def test_sha256_of_file_caches_across_invocations(self, server_module, tmp_path):
        test_file = tmp_path / "test_cache.bin"
        test_file.write_bytes(b"content-version-1")

        h1 = server_module._sha256_of_file(test_file)
        assert len(h1) == 64

        # Calling second time should return from cache without disk I/O
        with patch("builtins.open", side_effect=AssertionError("Should not re-read from disk")):
            h2 = server_module._sha256_of_file(test_file)
            assert h2 == h1

    def test_sha256_of_file_invalidates_on_mtime_change(self, server_module, tmp_path):
        import os

        test_file = tmp_path / "test_mtime.bin"
        test_file.write_bytes(b"data_version_1__")  # 16 bytes
        h1 = server_module._sha256_of_file(test_file)

        # Write same-length content so size remains strictly identical
        test_file.write_bytes(b"data_version_2__")  # 16 bytes
        # Explicitly update mtime by 1 second to isolate mtime invalidation from size
        st = test_file.stat()
        os.utime(test_file, ns=(st.st_atime_ns, st.st_mtime_ns + 1_000_000_000))

        h2 = server_module._sha256_of_file(test_file)
        assert h2 != h1

    def test_sha256_of_file_invalidates_on_replacement_with_preserved_mtime(self, server_module, tmp_path):
        """Atomic replacement with preserved mtime/size must invalidate via inode/ctime (#8221)."""
        import os

        target_file = tmp_path / "target_db.bin"
        replacement_file = tmp_path / "temp_db.bin"

        target_file.write_bytes(b"original_payload")  # 16 bytes
        h1 = server_module._sha256_of_file(target_file)

        # Create replacement file with different content of identical size
        replacement_file.write_bytes(b"replaced_payload")  # 16 bytes
        st_orig = target_file.stat()
        # Preserve original mtime
        os.utime(replacement_file, ns=(st_orig.st_atime_ns, st_orig.st_mtime_ns))

        # Atomic replace (moves replacement into target, altering inode)
        os.replace(replacement_file, target_file)

        h2 = server_module._sha256_of_file(target_file)
        assert h2 != h1

    def test_sha256_of_file_concurrent_cold_calls_deduplicated(self, server_module, tmp_path):
        """Concurrent cold reads must be synchronized by lock and deduplicate disk reads (#8221)."""
        import concurrent.futures

        test_file = tmp_path / "test_concurrent.bin"
        test_file.write_bytes(b"concurrent_payload_content")

        server_module._FILE_HASH_CACHE.clear()

        real_open = open
        open_count = 0
        open_lock = threading.Lock()

        def counting_open(file, *args, **kwargs):
            nonlocal open_count
            if str(test_file) in str(file):
                with open_lock:
                    open_count += 1
            return real_open(file, *args, **kwargs)

        # Run 8 concurrent threads on the same cold file
        with patch("builtins.open", side_effect=counting_open):
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                futures = [executor.submit(server_module._sha256_of_file, test_file) for _ in range(8)]
                results = [f.result() for f in futures]

        assert len(set(results)) == 1
        assert len(results[0]) == 64
        # Proves that despite 8 concurrent callers, disk read was executed exactly once
        assert open_count == 1

    def test_sha256_of_file_waiting_callers_re_stat_inside_lock(self, server_module, tmp_path):
        """Callers waiting on lock must re-stat and cache the latest file state (#8221)."""
        test_file = tmp_path / "test_re_stat.bin"
        test_file.write_bytes(b"initial_state_payload")
        server_module._FILE_HASH_CACHE.clear()

        real_lock = server_module._FILE_HASH_LOCK
        caller_blocked = threading.Event()
        proceed_event = threading.Event()

        class HookedLock:
            def __enter__(self):
                # Caller has completed pre-lock stat and is now entering lock
                caller_blocked.set()
                assert proceed_event.wait(timeout=5.0)
                return real_lock.__enter__()

            def __exit__(self, *args):
                return real_lock.__exit__(*args)

        result_holder: dict[str, str] = {}

        def worker():
            result_holder["hash"] = server_module._sha256_of_file(test_file)

        with patch.object(server_module, "_FILE_HASH_LOCK", HookedLock()):
            t = threading.Thread(target=worker)
            t.start()

            # Wait until worker has completed pre-lock stat and reached lock
            assert caller_blocked.wait(timeout=5.0)

            # Mutate the file on disk while worker is blocked before lock
            test_file.write_bytes(b"mutated_state_payload_updated")
            proceed_event.set()

            t.join(timeout=5.0)
            assert not t.is_alive()

        # Worker re-stated inside lock, hashed mutated payload, and successfully cached it
        mutated_hash = hashlib.sha256(b"mutated_state_payload_updated").hexdigest()
        assert result_holder["hash"] == mutated_hash

        # Assert subsequent call hits cache without disk I/O
        with patch("builtins.open", side_effect=AssertionError("Should hit cache")):
            assert server_module._sha256_of_file(test_file) == mutated_hash


class TestSlovnykMeSearchOutage:
    """#9005: a live slovnyk.me outage in search_slovnyk_me is never rendered as 'No results'."""

    OUTAGE: ClassVar[list[dict]] = [{"dictionary_slug": "vts", "word": "тест", "error": "HTTP 403"}]

    def test_outage_with_no_hits_renders_unavailable(self, server_module):
        with patch("wiki.sources_db.search_slovnyk_me_with_status", return_value=([], self.OUTAGE)):
            result = _run(server_module.handle_search_slovnyk_me({"query": "тест"}))
        assert "UNAVAILABLE" in result[0].text
        assert "vts (HTTP 403)" in result[0].text
        assert "No slovnyk.me results" not in result[0].text

    def test_no_hits_and_no_outage_is_a_real_miss(self, server_module):
        with patch("wiki.sources_db.search_slovnyk_me_with_status", return_value=([], [])):
            result = _run(server_module.handle_search_slovnyk_me({"query": "тест"}))
        assert result[0].text.startswith("No slovnyk.me results")

    def test_hits_with_an_outage_are_marked_partial(self, server_module):
        hit = {"word": "тест", "dictionary_slug": "sum20", "source_url": "https://example.invalid", "text": "x"}
        with patch("wiki.sources_db.search_slovnyk_me_with_status", return_value=([hit], self.OUTAGE)):
            result = _run(server_module.handle_search_slovnyk_me({"query": "тест"}))
        assert "Partial results" in result[0].text
        assert "### Result 1" in result[0].text

    def test_search_slovnyk_me_200_challenge_renders_unavailable(self, server_module, monkeypatch):
        """HTTP 200 Cloudflare challenge during live search fallback reports UNAVAILABLE (#9016)."""
        from wiki import slovnyk_me, sources_db

        challenge_html = "<html><title>Just a moment...</title><body>Checking browser</body></html>"
        monkeypatch.setattr(sources_db, "_search_slovnyk_me_db", lambda *a, **k: [])
        monkeypatch.setattr(
            slovnyk_me.requests,
            "get",
            lambda *a, **k: MagicMock(status_code=200, text=challenge_html, raise_for_status=lambda: None),
        )
        result = _run(server_module.handle_search_slovnyk_me({"query": "тест", "live": True}))
        assert "UNAVAILABLE" in result[0].text
        assert "vts (HTTP 200)" in result[0].text
        assert "No slovnyk.me results" not in result[0].text


class TestWikipediaPravopysHeritageOutage:
    """#9005 r3: Wikipedia, Правопис and heritage outages are reported as unavailable, never as a miss."""

    @pytest.mark.parametrize("mode", ["summary", "search", "extract", "sections", "section"])
    def test_wikipedia_outage_is_unavailable_and_never_negative_cached(self, server_module, mode):
        from rag.source_query import WikipediaUnavailableError

        cache = MagicMock()
        cache.get.return_value = None
        name = {
            "summary": "wikipedia_summary",
            "search": "wikipedia_search",
            "extract": "wikipedia_extract",
            "sections": "wikipedia_sections",
            "section": "wikipedia_section_text",
        }[mode]
        with (
            patch("rag.wiki_cache.WikiCache", return_value=cache),
            patch(f"rag.source_query.{name}", side_effect=WikipediaUnavailableError("HTTP 403")) as fetch,
            patch.object(server_module, "_lookup_wikipedia_in_db", return_value=None),
        ):
            result = _run(server_module.handle_query_wikipedia({"query": "Стаття", "mode": mode, "section": 1}))
        assert fetch.call_args.kwargs.get("raise_unavailable") is True
        assert result[0].text.startswith(server_module.WIKIPEDIA_UNAVAILABLE_PREFIX)
        assert "HTTP 403" in result[0].text
        cache.put_negative.assert_not_called()
        cache.put.assert_not_called()

    def test_stale_negative_wikipedia_cache_revalidates_live(self, server_module, tmp_path):
        """Wikipedia negative-cache entries older than negative TTL are re-validated (#9016)."""
        import time

        from rag.wiki_cache import WikiCache

        db_path = tmp_path / "wiki_cache.db"
        cache = WikiCache(db_path=db_path, negative_ttl=60)
        cache.put_negative("summary", "Стаття")

        # Backdate the negative entry by 120s (> negative_ttl 60s)
        cache._conn.execute(
            "UPDATE wiki_cache SET fetched_at = ?",
            (int(time.time()) - 120,),
        )
        cache._conn.commit()

        article = {
            "title": "Стаття",
            "description": "Опис",
            "url": "https://uk.wikipedia.org/wiki/Стаття",
            "extract": "Текст статті",
        }
        with (
            patch("rag.wiki_cache.WikiCache", return_value=cache),
            patch("rag.source_query.wikipedia_summary", return_value=article) as fetch,
            patch.object(server_module, "_lookup_wikipedia_in_db", return_value=None),
        ):
            result = _run(server_module.handle_query_wikipedia({"query": "Стаття", "mode": "summary"}))

        fetch.assert_called_once()
        assert "(cached)" not in result[0].text
        assert "Текст статті" in result[0].text

    def test_pravopys_outage_is_unavailable(self, server_module):
        unavailable = {"status": "unavailable", "section": 3, "url": "u", "reason": "HTTP 403"}
        with patch("rag.source_query.pravopys_section", return_value=unavailable) as fetch:
            result = _run(server_module.handle_query_pravopys({"topic": "3"}))
        content = result[0] if isinstance(result, tuple) else result
        assert fetch.call_args.kwargs.get("report_unavailable") is True
        assert "UNAVAILABLE" in content[0].text
        assert "No pravopys section found" not in content[0].text

    def _heritage(self, server_module, hits, outages):
        def fake(query, limit, *, include_live_slovnyk, outages=None):
            if outages is not None:
                outages.extend(outage_rows)
            return hits

        outage_rows = outages
        with patch("wiki.sources_db.search_heritage", side_effect=fake):
            return _run(server_module.handle_search_heritage({"query": "тест"}))[0].text

    def test_heritage_outage_with_no_hits_is_unavailable(self, server_module):
        text = self._heritage(server_module, [], [{"dictionary_slug": "vts", "error": "HTTP 403"}])
        assert "UNAVAILABLE" in text and "No heritage evidence found" not in text

    def test_heritage_hits_with_an_outage_are_partial(self, server_module):
        hit = {"source_family": "slovnyk_me", "source": "x", "word": "тест", "score": 1.0}
        text = self._heritage(server_module, [hit], [{"dictionary_slug": "vts", "error": "HTTP 403"}])
        assert "Partial results" in text and "### Evidence 1" in text

    def test_heritage_real_miss_is_unchanged(self, server_module):
        assert self._heritage(server_module, [], []).startswith("No heritage evidence found")

    def test_heritage_200_challenge_is_unavailable(self, server_module):
        text = self._heritage(server_module, [], [{"dictionary_slug": "vts", "error": "HTTP 200"}])
        assert "UNAVAILABLE" in text and "No heritage evidence found" not in text
        assert "vts (HTTP 200)" in text


def test_pravopys_unavailable_envelope_is_an_error_not_empty(server_module):
    """#9005 r4: the structured envelope of an unreachable Правопис is status=error, not the miss status."""
    unavailable = {"status": "unavailable", "section": 3, "url": "u", "reason": "HTTP 403"}
    with patch("rag.source_query.pravopys_section", return_value=unavailable):
        result = _run(server_module.handle_query_pravopys({"topic": "3"}))
    assert isinstance(result, tuple)
    _content, envelope = result
    assert envelope["status"] == "error"
    assert envelope["error_code"] == "source_unavailable"
