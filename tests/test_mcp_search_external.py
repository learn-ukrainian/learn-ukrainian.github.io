"""Tests for the MCP search_external handler."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".mcp" / "servers" / "sources"))


@pytest.fixture
def server_module():
    if "server" in sys.modules:
        del sys.modules["server"]
    import server as srv
    return srv


def _run(coro):
    return asyncio.run(coro)


def test_call_tool_dispatches_search_external(server_module):
    with patch.object(server_module, "handle_search_external", new_callable=AsyncMock) as mock:
        mock.return_value = [MagicMock(text="ok")]
        _run(server_module.call_tool("search_external", {"query": "козаки"}))
        mock.assert_called_once_with({"query": "козаки"})


def test_handle_search_external_formats_chunk_output(server_module):
    hits = [{
        "chunk_id": "ext-realna_istoria-demo-003",
        "source_name": "Реальна Історія",
        "speaker": "Акім Галімов",
        "register_tag": "interview",
        "decolonization_tag": "strong",
        "quality_tier": 1,
        "publish_date": "2023-08-14",
        "url": "https://youtube.com/watch?v=demo",
        "text": "Короткий фрагмент про козаків.",
    }]
    with patch("wiki.sources_db.search_external", return_value=hits):
        result = _run(server_module.handle_search_external({"query": "козаки"}))

    text = result[0].text
    assert "[Chunk ext-realna_istoria-demo-003]" in text
    assert "Channel: Реальна Історія | Speaker: Акім Галімов | Register: interview" in text
    assert "Decolonization: strong | Quality: 1 | Published: 2023-08-14" in text
    assert "URL: https://youtube.com/watch?v=demo" in text
    assert "Короткий фрагмент про козаків." in text


def test_handle_search_external_passes_filters(server_module):
    with patch("wiki.sources_db.search_external", return_value=[]) as mock:
        _run(server_module.handle_search_external({
            "query": "козаки",
            "track": "hist",
            "channel": "realna_istoria",
            "register": "interview",
            "decolonization": "strong",
            "min_quality_tier": 1,
            "max_results": 7,
        }))

    args, kwargs = mock.call_args
    assert args[0] == {"козаки"}
    assert kwargs == {
        "max_total": 7,
        "channel": "realna_istoria",
        "register": "interview",
        "decolonization": "strong",
        "min_quality_tier": 1,
        "track": "hist",
    }


def test_handle_search_external_track_changes_result_order(server_module):
    plain_hits = [
        {"chunk_id": "ext-ulp-001", "source_name": "Ukrainian Lessons Podcast", "speaker": "Anna Ohoiko",
         "register_tag": "scripted", "decolonization_tag": "moderate", "quality_tier": 1,
         "publish_date": "", "url": "https://example.test/ulp", "text": "ULP"},
        {"chunk_id": "ext-realna-001", "source_name": "Реальна Історія", "speaker": "Акім Галімов",
         "register_tag": "interview", "decolonization_tag": "strong", "quality_tier": 1,
         "publish_date": "", "url": "https://example.test/realna", "text": "Realna"},
    ]
    hist_hits = list(reversed(plain_hits))

    def _fake_search(_keywords, **kwargs):
        return hist_hits if kwargs.get("track") == "hist" else plain_hits

    with patch("wiki.sources_db.search_external", side_effect=_fake_search):
        plain = _run(server_module.handle_search_external({"query": "козаки"}))[0].text
        hist = _run(server_module.handle_search_external({"query": "козаки", "track": "hist"}))[0].text

    assert plain.index("[Chunk ext-ulp-001]") < plain.index("[Chunk ext-realna-001]")
    assert hist.index("[Chunk ext-realna-001]") < hist.index("[Chunk ext-ulp-001]")
