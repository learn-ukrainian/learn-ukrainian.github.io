"""Tests for the MCP RAG server (.mcp/servers/rag/server.py).

Covers:
- Tool listing returns all expected tools with correct schemas
- Tool dispatch routes to correct handlers
- SSE mode uses stateless=True (fix for initialization handshake issue)
- verify_word / verify_words handlers return correct format
- Error handling for unknown tools
"""

import asyncio
import inspect
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add the server directory to path so we can import it
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".mcp" / "servers" / "rag"))


@pytest.fixture
def server_module():
    """Import the server module fresh."""
    if "server" in sys.modules:
        del sys.modules["server"]
    import server as srv
    return srv


def _run(coro):
    """Run an async coroutine synchronously."""
    return asyncio.run(coro)


class TestListTools:
    """Test that list_tools returns all expected tools with valid schemas."""

    def test_returns_all_tools(self, server_module):
        tools = _run(server_module.list_tools())
        tool_names = {t.name for t in tools}

        expected = {
            "search_text", "search_images", "search_literary",
            "get_full_text", "get_chunk_context", "collection_stats",
            "verify_word", "verify_words", "verify_lemma",
            "query_wikipedia", "query_grac", "query_ulif",
            "query_r2u", "query_pravopys", "query_cefr_level",
            "search_style_guide", "search_definitions", "search_etymology",
            "search_idioms", "search_synonyms", "translate_en_uk",
        }
        assert tool_names == expected

    def test_all_tools_have_input_schema(self, server_module):
        tools = _run(server_module.list_tools())
        for tool in tools:
            assert tool.inputSchema is not None, f"{tool.name} missing inputSchema"
            assert tool.inputSchema.get("type") == "object", f"{tool.name} schema not object type"

    def test_verify_word_schema(self, server_module):
        tools = _run(server_module.list_tools())
        vw = next(t for t in tools if t.name == "verify_word")
        assert "word" in vw.inputSchema["required"]
        assert "word" in vw.inputSchema["properties"]

    def test_verify_words_schema(self, server_module):
        tools = _run(server_module.list_tools())
        vw = next(t for t in tools if t.name == "verify_words")
        assert "words" in vw.inputSchema["required"]
        props = vw.inputSchema["properties"]["words"]
        assert props["type"] == "array"
        assert props["items"]["type"] == "string"


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

    def test_verify_words_dispatches(self, server_module):
        with patch.object(server_module, "handle_verify_words", new_callable=AsyncMock) as mock:
            mock.return_value = [MagicMock(text="ok")]
            _run(server_module.call_tool("verify_words", {"words": ["тест"]}))
            mock.assert_called_once_with({"words": ["тест"]})

    def test_handler_exception_returns_error_text(self, server_module):
        with patch.object(server_module, "handle_verify_word", new_callable=AsyncMock) as mock:
            mock.side_effect = RuntimeError("test error")
            result = _run(server_module.call_tool("verify_word", {"word": "тест"}))
            assert len(result) == 1
            assert "RuntimeError" in result[0].text
            assert "test error" in result[0].text


class TestVerifyWordHandler:
    """Test verify_word handler formatting."""

    def test_not_found(self, server_module):
        with patch("rag.query.verify_word", return_value=[]):
            result = _run(server_module.handle_verify_word({"word": "взяйте"}))
            assert "NOT FOUND" in result[0].text

    def test_found(self, server_module):
        mock_matches = [{"lemma": "читати", "pos": "verb", "tags": "verb:imperf:impr:s:2"}]
        with patch("rag.query.verify_word", return_value=mock_matches):
            result = _run(server_module.handle_verify_word({"word": "читай"}))
            assert "читати" in result[0].text
            assert "verb" in result[0].text
            assert "1 match" in result[0].text

    def test_passes_pos_filter(self, server_module):
        with patch("rag.query.verify_word", return_value=[]) as mock:
            _run(server_module.handle_verify_word({"word": "тест", "pos_filter": "noun"}))
            mock.assert_called_once_with("тест", "noun")


class TestVerifyWordsHandler:
    """Test verify_words handler formatting."""

    def test_batch_results(self, server_module):
        mock_results = {
            "стій": [{"lemma": "стояти", "pos": "verb", "tags": "verb:imperf:impr:s:2"}],
            "взяйте": [],
        }
        with patch("rag.query.verify_words", return_value=mock_results):
            result = _run(server_module.handle_verify_words({"words": ["стій", "взяйте"]}))
            text = result[0].text
            assert "Found: 1/2" in text
            assert "**стій** — FOUND" in text
            assert "**взяйте** — NOT FOUND" in text


class TestSSEStateless:
    """Test that SSE mode uses stateless=True to avoid initialization handshake issues."""

    def test_main_sse_passes_stateless(self, server_module):
        """Verify the SSE handler calls server.run with stateless=True.

        This is critical: without stateless=True, Claude Code's SSE client
        fails with 'Received request before initialization was complete'
        because it doesn't send the MCP initialize handshake.
        """
        source = inspect.getsource(server_module.main_sse)
        assert "stateless=True" in source, (
            "main_sse must pass stateless=True to server.run() — "
            "without it, SSE clients that skip the initialize handshake "
            "get -32602 errors on every tool call"
        )
