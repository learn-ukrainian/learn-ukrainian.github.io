import asyncio
import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import patch

import pytest

from tests.pohribnyi_schema import open_schema_copy

SOURCES_SERVER_PATH = Path(__file__).resolve().parents[1] / ".mcp" / "servers" / "sources" / "server.py"


@pytest.fixture(autouse=True)
def optional_dependency_stubs(monkeypatch):
    if importlib.util.find_spec("requests") is None:
        stub = types.ModuleType("requests")

        class RequestException(Exception):
            pass

        def unexpected_network_call(*_args, **_kwargs):
            raise AssertionError("source-filter tests must not make network calls")

        stub.RequestException = RequestException
        stub.get = unexpected_network_call
        monkeypatch.setitem(sys.modules, "requests", stub)

    dense_rerank_stub = types.ModuleType("wiki.dense_rerank")
    dense_rerank_stub._get_tokenizer = lambda: None
    dense_rerank_stub.dense_rerank_enabled = lambda *_args, **_kwargs: False
    dense_rerank_stub.rerank_candidates = lambda candidates, *_args, **_kwargs: candidates
    dense_rerank_stub.rerank_sections = lambda sections, *_args, **_kwargs: sections
    monkeypatch.setitem(sys.modules, "wiki.dense_rerank", dense_rerank_stub)

    if importlib.util.find_spec("mcp") is None:
        mcp_module = types.ModuleType("mcp")
        server_module = types.ModuleType("mcp.server")
        stdio_module = types.ModuleType("mcp.server.stdio")
        types_module = types.ModuleType("mcp.types")

        class Server:
            def __init__(self, *_args, **_kwargs):
                pass

        class Content:
            def __init__(self, **values):
                self.__dict__.update(values)

        class Tool(Content):
            def __init__(self, *, inputSchema, **values):
                super().__init__(**values)
                self.input_schema = inputSchema

        server_module.Server = Server
        stdio_module.stdio_server = None
        for name in (
            "CallToolRequestParams",
            "CallToolResult",
            "ListToolsResult",
            "TextContent",
        ):
            setattr(types_module, name, Content)
        types_module.Tool = Tool
        monkeypatch.setitem(sys.modules, "mcp", mcp_module)
        monkeypatch.setitem(sys.modules, "mcp.server", server_module)
        monkeypatch.setitem(sys.modules, "mcp.server.stdio", stdio_module)
        monkeypatch.setitem(sys.modules, "mcp.types", types_module)


@pytest.fixture
def server_module():
    spec = importlib.util.spec_from_file_location("sources_server", SOURCES_SERVER_PATH)
    srv = importlib.util.module_from_spec(spec)
    sys.modules["sources_server"] = srv
    spec.loader.exec_module(srv)
    return srv


def _run(coro):
    return asyncio.run(coro)


class TestSearchTextbooksSourceFilter:

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


@pytest.mark.parametrize("include", [False, True, "false"])
def test_mcp_retained_transcriptions_require_explicit_request(server_module, tmp_path, monkeypatch, include):
    import sqlite3

    from wiki import sources_db

    conn = open_schema_copy(tmp_path / "sources.db")
    conn.row_factory = sqlite3.Row
    conn.execute("ALTER TABLE textbooks ADD COLUMN transcription_status TEXT")
    conn.executemany(
        "INSERT INTO textbooks(chunk_id,title,text,source_file,transcription_status) VALUES (?,?,?,?,?)",
        [("old", "fixture", "fixture " * 50, "fixture", "superseded"),
         ("clean", "fixture", "fixture " * 50, "fixture", "adjudicated")],
    )
    monkeypatch.setattr(sources_db, "_get_conn", lambda: conn)
    try:
        tools = _run(server_module.list_tools())
        for name in ("search_text", "get_chunk_context"):
            schema = next(t for t in tools if t.name == name).input_schema
            assert schema["properties"]["include_superseded"] == {
                "type": "boolean", "default": False,
                "description": schema["properties"]["include_superseded"]["description"],
            }
        args = {"query": "fixture"}
        if include is not False:
            args["include_superseded"] = include
        content, _ = _run(server_module.handle_search_text(args))
        assert ("**Chunk ID**: `old`" in content[0].text) == (include is True)
        assert "**Chunk ID**: `clean`" in content[0].text
        args = {"chunk_id": "old"}
        if include is not False:
            args["include_superseded"] = include
        content, _ = _run(server_module.handle_get_chunk_context(args))
        assert ("fixture" in content[0].text) == (include is True)
    finally:
        conn.close()
