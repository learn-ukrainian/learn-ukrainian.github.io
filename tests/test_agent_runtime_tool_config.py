"""Unit tests for the shared MCP tool_config builder."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime.tool_config import _load_mcp_config, build_mcp_tool_config


@pytest.fixture(autouse=True)
def _clear_mcp_config_cache() -> None:
    _load_mcp_config.cache_clear()
    yield
    _load_mcp_config.cache_clear()


def test_build_mcp_tool_config_claude_with_present_config(tmp_path: Path) -> None:
    config_path = tmp_path / ".mcp.json"
    config_path.write_text("{}", encoding="utf-8")

    tool_config = build_mcp_tool_config(
        "claude",
        allowed_tools="mcp__sources__*",
        mcp_config_path=config_path,
    )

    assert tool_config == {
        "mcp_config_path": str(config_path.resolve()),
        "allowed_tools": "mcp__sources__*",
    }


def test_build_mcp_tool_config_claude_without_config_returns_none(
    tmp_path: Path,
) -> None:
    tool_config = build_mcp_tool_config(
        "claude",
        allowed_tools="mcp__sources__*",
        mcp_config_path=tmp_path / ".mcp.json",
    )

    assert tool_config is None


def test_build_mcp_tool_config_gemini_with_server_list() -> None:
    tool_config = build_mcp_tool_config("gemini", mcp_servers=["sources"])

    assert tool_config == {"mcp_server_names": ["sources"]}


def test_build_mcp_tool_config_gemini_without_servers_returns_none() -> None:
    tool_config = build_mcp_tool_config("gemini")

    assert tool_config is None


def test_build_mcp_tool_config_codex_with_mcp_servers(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / ".mcp.json"
    config_path.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "sources": {"type": "sse", "url": "http://127.0.0.1:8766/sse"},
                    "other": {"type": "sse", "url": "http://127.0.0.1:9999/sse"},
                }
            }
        ),
        encoding="utf-8",
    )

    tool_config = build_mcp_tool_config(
        "codex",
        mcp_servers=["sources"],
        mcp_config_path=config_path,
    )

    assert tool_config == {
        "mcp_servers": {
            "sources": {"type": "sse", "url": "http://127.0.0.1:8766/sse"},
        }
    }


def test_build_mcp_tool_config_codex_without_mcp_servers_key_returns_none(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / ".mcp.json"
    config_path.write_text(json.dumps({"other": "value"}), encoding="utf-8")

    tool_config = build_mcp_tool_config("codex", mcp_config_path=config_path)

    assert tool_config is None


def test_build_mcp_tool_config_unknown_agent_returns_none(tmp_path: Path) -> None:
    config_path = tmp_path / ".mcp.json"
    config_path.write_text("{}", encoding="utf-8")

    tool_config = build_mcp_tool_config(
        "nonexistent",
        mcp_servers=["sources"],
        allowed_tools="mcp__sources__*",
        mcp_config_path=config_path,
    )

    assert tool_config is None
