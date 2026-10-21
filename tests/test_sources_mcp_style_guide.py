"""Tests for Sources MCP search_style_guide description and completeness metadata.

Issue #8792.
"""

from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
_MCP_SOURCES_PATH = REPO_ROOT / ".mcp" / "servers" / "sources" / "server.py"

_spec = importlib.util.spec_from_file_location("mcp_sources_server", _MCP_SOURCES_PATH)
assert _spec and _spec.loader
_mcp_sources = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mcp_sources)


def test_antonenko_completeness_notes_accuracy() -> None:
    """Verify COMPLETENESS_NOTES accurately reflects 342 structured entries and full textbook text."""
    note = _mcp_sources.COMPLETENESS_NOTES.get("antonenko_davydovych", "")
    assert "342 structured entries in style_guide" in note
    assert "169-section" in note
    assert "antonenko-davydovych-yak-my-hovorymo" in note
    assert "279" not in note
    assert "incomplete" not in note
    assert "46%" not in note


def test_search_style_guide_tool_description() -> None:
    """Verify search_style_guide tool description contains accurate corpus counts and surfaces."""
    tools = asyncio.run(_mcp_sources.list_tools())
    tool_map = {t.name: t for t in tools}
    assert "search_style_guide" in tool_map
    desc = tool_map["search_style_guide"].description
    assert "342 structured discussion entries" in desc
    assert "169-section book text is also indexed in textbooks" in desc
    assert "antonenko-davydovych-yak-my-hovorymo" in desc
    assert "279" not in desc
    assert "46%" not in desc
    assert "54%" not in desc
    assert "ukrlib.com.ua" not in desc
