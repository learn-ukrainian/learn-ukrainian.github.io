"""Unit tests for the shared MCP tool_config builder."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime.tool_config import (
    _codex_sanitize_server_config,
    _load_mcp_config,
    build_mcp_tool_config,
)


@pytest.fixture(autouse=True)
def _clear_mcp_config_cache() -> None:
    _load_mcp_config.cache_clear()
    yield
    _load_mcp_config.cache_clear()


def test_build_mcp_tool_config_claude_with_present_config(tmp_path: Path) -> None:
    config_path = tmp_path / ".mcp.json"
    config_path.write_text("{}", encoding="utf-8")

    tool_config, diagnostics = build_mcp_tool_config(
        "claude",
        allowed_tools="mcp__sources__*",
        mcp_config_path=config_path,
    )

    assert tool_config == {
        "mcp_config_path": str(config_path.resolve()),
        "allowed_tools": "mcp__sources__*",
    }
    assert diagnostics["resolution_status"] == "ok"


def test_build_mcp_tool_config_claude_without_config_returns_none(
    tmp_path: Path,
) -> None:
    tool_config, diagnostics = build_mcp_tool_config(
        "claude",
        allowed_tools="mcp__sources__*",
        mcp_config_path=tmp_path / ".mcp.json",
    )

    assert tool_config is None
    assert diagnostics["resolution_status"] == "config_missing"


def test_build_mcp_tool_config_gemini_with_server_list() -> None:
    tool_config, diagnostics = build_mcp_tool_config("gemini", mcp_servers=["sources"])

    assert tool_config == {"mcp_server_names": ["sources"]}
    assert diagnostics["resolution_status"] == "ok"


def test_build_mcp_tool_config_gemini_without_servers_returns_none() -> None:
    tool_config, diagnostics = build_mcp_tool_config("gemini")

    assert tool_config is None
    assert diagnostics["resolution_status"] == "config_empty"


@pytest.mark.parametrize("agent", ["grok", "grok-build"])
def test_build_mcp_tool_config_native_grok_uses_native_config(agent: str) -> None:
    tool_config, diagnostics = build_mcp_tool_config(
        agent,
        mcp_servers=["sources"],
    )

    assert tool_config == {
        "always_approve": True,
        "mcp_server_names": ["sources"],
    }
    assert diagnostics["config_path"] == str(Path.home() / ".grok" / "mcp.json")
    assert diagnostics["resolution_status"] == "ok"


def test_build_mcp_tool_config_grok_hermes_uses_hermes_config() -> None:
    tool_config, diagnostics = build_mcp_tool_config(
        "grok-hermes",
        mcp_servers=["sources"],
    )

    assert tool_config == {"hermes_mcp_servers": ["sources"]}
    assert diagnostics["config_path"] == str(Path.home() / ".hermes" / "config.yaml")
    assert diagnostics["resolution_status"] == "ok"


def test_codex_tool_config_strips_claude_format_type_field(
    tmp_path: Path,
) -> None:
    """codex CLI doesn't recognize `type` - it must be stripped (#1812)."""
    config_path = tmp_path / ".mcp.json"
    config_path.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "sources": {
                        "type": "streamable-http",
                        "url": "http://127.0.0.1:8766/mcp",
                    },
                    "other": {
                        "type": "streamable-http",
                        "url": "http://127.0.0.1:9999/mcp",
                    },
                }
            }
        ),
        encoding="utf-8",
    )

    tool_config, diagnostics = build_mcp_tool_config(
        "codex",
        mcp_servers=["sources"],
        mcp_config_path=config_path,
    )

    assert tool_config is not None
    assert "mcp_servers" in tool_config
    sources_cfg = tool_config["mcp_servers"]["sources"]
    assert sources_cfg["url"] == "http://127.0.0.1:8766/mcp"
    assert "type" not in sources_cfg, (
        "codex tool_config must not include the Claude-format `type` field; "
        f"got {sources_cfg!r}. See #1812."
    )
    assert diagnostics["resolution_status"] == "ok"


def test_codex_sanitize_server_config_drops_unknown_fields() -> None:
    raw = {
        "url": "http://127.0.0.1:8766/mcp",
        "type": "streamable-http",
        "transport": "http",
        "headers": {"X-Foo": "bar"},
    }

    sanitized = _codex_sanitize_server_config(raw)

    assert sanitized == {"url": "http://127.0.0.1:8766/mcp"}


def test_codex_sanitize_server_config_preserves_codex_fields() -> None:
    raw = {
        "command": "/usr/local/bin/some-mcp",
        "args": ["--port", "9000"],
        "env": {"FOO": "bar"},
        "bearer_token_env_var": "MY_TOKEN",
        "type": "stdio",
    }

    sanitized = _codex_sanitize_server_config(raw)

    assert sanitized == {
        "command": "/usr/local/bin/some-mcp",
        "args": ["--port", "9000"],
        "env": {"FOO": "bar"},
        "bearer_token_env_var": "MY_TOKEN",
    }


def test_build_mcp_tool_config_codex_accepts_stdio_server(
    tmp_path: Path,
) -> None:
    """Stdio MCP servers such as Headroom must not be dropped."""
    config_path = tmp_path / ".mcp.json"
    config_path.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "headroom": {
                        "type": "stdio",
                        "command": "headroom",
                        "args": ["mcp", "serve"],
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    tool_config, diagnostics = build_mcp_tool_config(
        "codex",
        mcp_servers=["headroom"],
        mcp_config_path=config_path,
    )

    assert tool_config == {
        "mcp_servers": {
            "headroom": {
                "command": "headroom",
                "args": ["mcp", "serve"],
            }
        }
    }
    assert diagnostics["resolution_status"] == "ok"
    assert diagnostics["resolved_servers"] == ["headroom"]


def test_build_mcp_tool_config_codex_rejects_stale_sse_stdio_type(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / ".mcp.json"
    config_path.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "legacy": {
                        "type": "sse",
                        "command": "legacy-mcp",
                        "args": [],
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    tool_config, diagnostics = build_mcp_tool_config(
        "codex",
        mcp_servers=["legacy"],
        mcp_config_path=config_path,
    )

    assert tool_config is None
    assert diagnostics["resolution_status"] == "servers_not_found"
    assert diagnostics["missing_server_names"] == ["legacy"]


def test_build_mcp_tool_config_codex_without_mcp_servers_key_returns_none(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / ".mcp.json"
    config_path.write_text(json.dumps({"other": "value"}), encoding="utf-8")

    tool_config, diagnostics = build_mcp_tool_config(
        "codex",
        mcp_config_path=config_path,
    )

    assert tool_config is None
    assert diagnostics["resolution_status"] == "config_empty"


def test_build_mcp_tool_config_unknown_agent_returns_none(tmp_path: Path) -> None:
    config_path = tmp_path / ".mcp.json"
    config_path.write_text("{}", encoding="utf-8")

    tool_config, diagnostics = build_mcp_tool_config(
        "nonexistent",
        mcp_servers=["sources"],
        allowed_tools="mcp__sources__*",
        mcp_config_path=config_path,
    )

    assert tool_config is None
    assert diagnostics["resolution_status"] == "servers_not_found"
