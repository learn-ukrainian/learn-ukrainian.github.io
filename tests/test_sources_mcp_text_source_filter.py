import asyncio
import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SOURCES_SERVER_PATH = Path(__file__).resolve().parents[1] / ".mcp" / "servers" / "sources" / "server.py"


@pytest.fixture
def server_module():
    spec = importlib.util.spec_from_file_location("sources_server", SOURCES_SERVER_PATH)
    srv = importlib.util.module_from_spec(spec)
    sys.modules["sources_server"] = srv
    spec.loader.exec_module(srv)
    return srv


def _run(coro):
    return asyncio.run(coro)


class TestSearchTextSourceFilter:
    def test_search_text_tool_schema_includes_source_file(self, server_module):
        tools = _run(server_module.list_tools())
        tool = next(t for t in tools if t.name == "search_text")
        props = tool.input_schema["properties"]
        assert "source_file" in props
        assert props["source_file"]["type"] == "string"
        assert "exact textbook source file" in props["source_file"]["description"]

    def test_handle_search_text_passes_source_file(self, server_module):
        args = {"query": "test query", "source_file": "antonenko-davydovych-yak-my-hovorymo"}
        with patch("wiki.sources_db.search_textbooks") as mock_search:
            mock_search.return_value = [{"title": "Title", "text": "Hit", "chunk_id": "1"}]
            result = _run(server_module.handle_search_text(args))

            mock_search.assert_called_once()
            _, kwargs = mock_search.call_args
            assert kwargs.get("source_file") == "antonenko-davydovych-yak-my-hovorymo"
            assert "**Source file**" in result[0].text

    def test_handle_search_text_backward_compatibility(self, server_module):
        args = {"query": "test query"}
        with patch("wiki.sources_db.search_textbooks") as mock_search:
            mock_search.return_value = [{"title": "Title", "text": "Hit", "chunk_id": "1"}]
            _run(server_module.handle_search_text(args))

            mock_search.assert_called_once()
            _, kwargs = mock_search.call_args
            assert kwargs.get("source_file") is None


class TestSearchTextbooksSourceFilter:
    def test_search_textbooks_with_source_file_only(self):
        from wiki.sources_db import search_textbooks
        with patch("wiki.sources_db._fts_search") as mock_fts:
            mock_fts.return_value = [{"title": "Title", "text": "Hit", "chunk_id": "1", "source_file": "antonenko-davydovych-yak-my-hovorymo"}]
            results = search_textbooks({"query"}, source_file="antonenko-davydovych-yak-my-hovorymo")
            mock_fts.assert_called_once()
            _, kwargs = mock_fts.call_args
            assert "AND s.source_file = ?" in kwargs["extra_where"]
            assert kwargs["extra_params"] == ("antonenko-davydovych-yak-my-hovorymo",)
            assert len(results) == 1

    def test_search_textbooks_with_subject_and_source_file(self):
        from wiki.sources_db import search_textbooks
        with patch("wiki.sources_db._fts_search") as mock_fts, patch("wiki.sources_db._table_columns") as mock_columns:
            mock_columns.return_value = {"subject", "source_file"}
            mock_fts.return_value = [{"title": "Title", "text": "Hit", "chunk_id": "1", "source_file": "antonenko-davydovych-yak-my-hovorymo"}]
            # ukrmova is a valid canonical subject
            results = search_textbooks({"query"}, subject="ukrmova", source_file="antonenko-davydovych-yak-my-hovorymo")
            mock_fts.assert_called_once()
            _, kwargs = mock_fts.call_args
            assert "AND s.subject = ? AND s.source_file = ?" in kwargs["extra_where"]
            assert kwargs["extra_params"] == ("ukrmova", "antonenko-davydovych-yak-my-hovorymo")

    def test_search_textbooks_no_cross_source_leakage(self):
        from wiki.sources_db import search_textbooks
        with patch("wiki.sources_db._fts_search") as mock_fts:
            mock_fts.return_value = [
                {
                    "title": "Expected",
                    "text": "Long enough expected source text for the result filter.",
                    "chunk_id": "1",
                    "source_file": "antonenko-davydovych-yak-my-hovorymo",
                },
                {
                    "title": "Foreign",
                    "text": "Long enough foreign source text that must never leak.",
                    "chunk_id": "2",
                    "source_file": "different-source",
                },
            ]
            results = search_textbooks(
                {"query"}, source_file="antonenko-davydovych-yak-my-hovorymo"
            )
            assert [result["source_file"] for result in results] == [
                "antonenko-davydovych-yak-my-hovorymo"
            ]

    def test_source_file_is_normalized_before_query(self):
        from wiki.sources_db import search_textbooks
        with patch("wiki.sources_db._fts_search") as mock_fts:
            mock_fts.return_value = []
            search_textbooks(
                {"query"}, source_file=" `antonenko-davydovych-yak-my-hovorymo` "
            )
            assert mock_fts.call_args.kwargs["extra_params"] == (
                "antonenko-davydovych-yak-my-hovorymo",
            )

    def test_empty_supplied_source_file_fails_closed(self):
        from wiki.sources_db import search_textbooks
        with patch("wiki.sources_db._fts_search") as mock_fts:
            assert search_textbooks({"query"}, source_file="  ") == []
            mock_fts.assert_not_called()

    def test_empty_results_when_source_file_has_no_matches(self):
        from wiki.sources_db import search_textbooks
        with patch("wiki.sources_db._fts_search") as mock_fts:
            mock_fts.return_value = []
            results = search_textbooks({"query"}, source_file="antonenko-davydovych-yak-my-hovorymo")
            assert results == []
