"""Shared MCP tool_config builders for agent_runtime callers."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_MCP_CONFIG_PATH = _REPO_ROOT / ".mcp.json"


def _canonical_agent_name(agent: str) -> str | None:
    """Normalize caller-facing agent labels to runtime adapter names."""
    if agent.startswith("claude"):
        return "claude"
    if agent.startswith("gemini"):
        return "gemini"
    if agent.startswith("codex"):
        return "codex"
    return None


def _resolved_mcp_config_path(mcp_config_path: Path | None) -> Path:
    """Return the configured `.mcp.json` path, defaulting to repo root."""
    return (mcp_config_path or _DEFAULT_MCP_CONFIG_PATH).resolve()


@lru_cache(maxsize=1)
def _load_mcp_config(mcp_config_path: Path) -> dict[str, Any] | None:
    """Load `.mcp.json` once per process for Codex MCP config shaping."""
    try:
        raw = json.loads(mcp_config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return raw if isinstance(raw, dict) else None


def _codex_mcp_servers(
    mcp_config_path: Path,
    requested_servers: list[str] | None,
) -> dict[str, Any] | None:
    """Return Codex's nested `mcp_servers` config, optionally filtered."""
    data = _load_mcp_config(mcp_config_path)
    if not data:
        return None

    servers = data.get("mcpServers")
    if not isinstance(servers, dict) or not servers:
        return None

    if not requested_servers:
        return servers

    selected = {
        server_name: servers[server_name]
        for server_name in requested_servers
        if server_name in servers
    }
    return selected or None


def build_mcp_tool_config(
    agent: str,
    *,
    mcp_servers: list[str] | None = None,
    allowed_tools: str | None = None,
    mcp_config_path: Path | None = None,
) -> dict | None:
    """Build adapter-appropriate tool_config dict for MCP access.

    Returns ``None`` when the requested agent cannot be configured for MCP.
    Gemini also returns ``None`` when no server names are requested.
    """
    canonical_agent = _canonical_agent_name(agent)
    if canonical_agent is None:
        return None

    resolved_config_path = _resolved_mcp_config_path(mcp_config_path)

    if canonical_agent == "claude":
        if not allowed_tools or not resolved_config_path.exists():
            return None
        return {
            "mcp_config_path": str(resolved_config_path),
            "allowed_tools": allowed_tools,
        }

    if canonical_agent == "gemini":
        if not mcp_servers:
            return None
        return {"mcp_server_names": mcp_servers}

    codex_servers = _codex_mcp_servers(resolved_config_path, mcp_servers)
    return {"mcp_servers": codex_servers} if codex_servers else None
