"""Tests for the MCP search_external handler."""

from __future__ import annotations

import asyncio
import json
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
        "title": "Козаки та історія",
        "source_name": "Реальна Історія",
        "channel_id": "realna_istoria",
        "speaker": "Акім Галімов",
        "register_tag": "interview",
        "decolonization_tag": "strong",
        "quality_tier": 1,
        "publish_date": "2023-08-14",
        "duration_s": 900,
        "chunk_start_ts": None,
        "chunk_end_ts": None,
        "video_id": "demo",
        "fts_score": -4.2,
        "adjusted_score": -4.2,
        "url": "https://youtube.com/watch?v=demo",
        "text": "Короткий фрагмент про козаків.",
    }]
    with patch("wiki.sources_db.search_external", return_value=hits):
        result = _run(server_module.handle_search_external({"query": "козаки"}))

    payload = json.loads(result[0].text)
    assert payload[0]["chunk_id"] == "ext-realna_istoria-demo-003"
    assert payload[0]["title"] == "Козаки та історія"
    assert payload[0]["channel_id"] == "realna_istoria"
    assert payload[0]["channel_name"] == "Реальна Історія"
    assert payload[0]["speaker"] == "Акім Галімов"
    assert payload[0]["register_tag"] == "interview"
    assert payload[0]["decolonization_tag"] == "strong"
    assert payload[0]["quality_tier"] == 1
    assert payload[0]["publish_date"] == "2023-08-14"
    assert payload[0]["url"] == "https://youtube.com/watch?v=demo"
    assert payload[0]["text"] == "Короткий фрагмент про козаків."
    assert payload[0]["fts_score"] == -4.2
    assert payload[0]["adjusted_score"] == -4.2


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
        plain = json.loads(_run(server_module.handle_search_external({"query": "козаки"}))[0].text)
        hist = json.loads(_run(server_module.handle_search_external({"query": "козаки", "track": "hist"}))[0].text)

    assert plain[0]["chunk_id"] == "ext-ulp-001"
    assert hist[0]["chunk_id"] == "ext-realna-001"
