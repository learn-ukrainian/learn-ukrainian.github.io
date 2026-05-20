"""Shared MCP tool_config builders for agent_runtime callers."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_MCP_CONFIG_PATH = _REPO_ROOT / ".mcp.json"
_RESOLUTION_STATUSES = {"ok", "config_missing", "config_empty", "servers_not_found"}
_CODEX_MCP_SERVER_FIELDS = frozenset(
    {
        "url",
        "command",
        "args",
        "env",
        "bearer_token_env_var",
    }
)


def _canonical_agent_name(agent: str) -> str | None:
    """Normalize caller-facing agent labels to runtime adapter names."""
    if agent.startswith("claude"):
        return "claude"
    if agent.startswith("gemini"):
        return "gemini"
    if agent.startswith("codex"):
        return "codex"
    if agent.startswith("grok"):
        return "grok"
    if agent.startswith("deepseek"):
        return "deepseek"
    if agent.startswith("qwen"):
        return "qwen"
    if agent.startswith("agy"):
        return "agy"
    return None


def _resolved_mcp_config_path(mcp_config_path: Path | None) -> Path:
    """Return the configured `.mcp.json` path, defaulting to repo root."""
    return (mcp_config_path or _DEFAULT_MCP_CONFIG_PATH).resolve()


def _codex_sanitize_server_config(server_config: dict) -> dict:
    """Drop fields codex CLI's mcp_servers schema does not recognize.

    `.mcp.json` includes Claude-format fields, notably `type` such as
    `type="streamable-http"`. Codex CLI auto-detects HTTP transport from the
    URL scheme and does not have `type` in its `mcp_servers.<name>.*` schema;
    passing the unknown field silently breaks server registration on the codex
    side and leaves the model with no MCP tools.
    """
    return {k: v for k, v in server_config.items() if k in _CODEX_MCP_SERVER_FIELDS}


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
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Return Codex's nested `mcp_servers` config plus resolution diagnostics."""
    requested = list(requested_servers or [])

    def diagnostics(
        *,
        resolved_servers: list[str] | None = None,
        resolution_status: str,
        missing_server_names: list[str] | None = None,
    ) -> dict[str, Any]:
        assert resolution_status in _RESOLUTION_STATUSES
        return {
            "requested_servers": requested,
            "resolved_servers": resolved_servers or [],
            "config_path": str(mcp_config_path),
            "resolution_status": resolution_status,
            "missing_server_names": missing_server_names or [],
        }

    data = _load_mcp_config(mcp_config_path)
    if not data:
        return None, diagnostics(resolution_status="config_missing")

    servers = data.get("mcpServers")
    if not isinstance(servers, dict) or not servers:
        return None, diagnostics(resolution_status="config_empty")

    usable_servers = {
        server_name: server_config
        for server_name, server_config in servers.items()
        if _codex_server_is_usable(server_config)
    }

    if not requested:
        if usable_servers:
            return (
                {
                    name: _codex_sanitize_server_config(cfg)
                    for name, cfg in usable_servers.items()
                },
                diagnostics(
                    resolved_servers=list(usable_servers),
                    resolution_status="ok",
                ),
            )
        return None, diagnostics(
            resolution_status="servers_not_found",
            missing_server_names=list(servers),
        )

    selected = {
        server_name: _codex_sanitize_server_config(usable_servers[server_name])
        for server_name in requested
        if server_name in usable_servers
    }
    missing = [server_name for server_name in requested if server_name not in selected]
    if not selected:
        return None, diagnostics(
            resolution_status="servers_not_found",
            missing_server_names=missing,
        )
    return selected, diagnostics(
        resolved_servers=list(selected),
        resolution_status="ok",
        missing_server_names=missing,
    )


def _codex_server_is_usable(server_config: Any) -> bool:
    """Reject known-stale Codex MCP endpoint shapes before dispatch."""
    if not isinstance(server_config, dict):
        return False
    server_type = str(server_config.get("type") or "").strip().lower()
    url = str(server_config.get("url") or "").strip()
    if server_type == "sse":
        return False
    if url.rstrip("/").endswith("/sse"):
        return False
    return bool(url)


def _basic_diagnostics(
    *,
    mcp_config_path: Path,
    requested_servers: list[str] | None,
    resolved_servers: list[str] | None,
    resolution_status: str,
    missing_server_names: list[str] | None = None,
) -> dict[str, Any]:
    assert resolution_status in _RESOLUTION_STATUSES
    return {
        "requested_servers": list(requested_servers or []),
        "resolved_servers": list(resolved_servers or []),
        "config_path": str(mcp_config_path),
        "resolution_status": resolution_status,
        "missing_server_names": list(missing_server_names or []),
    }


def build_mcp_tool_config(
    agent: str,
    *,
    mcp_servers: list[str] | None = None,
    allowed_tools: str | None = None,
    mcp_config_path: Path | None = None,
) -> tuple[dict | None, dict[str, Any]]:
    """Build adapter-appropriate tool_config dict for MCP access.

    Returns ``(None, diagnostics)`` when the requested agent cannot be
    configured for MCP. Gemini also returns ``None`` when no server names are
    requested.
    """
    resolved_config_path = _resolved_mcp_config_path(mcp_config_path)
    canonical_agent = _canonical_agent_name(agent)
    if canonical_agent is None:
        return None, _basic_diagnostics(
            mcp_config_path=resolved_config_path,
            requested_servers=mcp_servers,
            resolved_servers=None,
            resolution_status="servers_not_found",
            missing_server_names=mcp_servers,
        )

    if canonical_agent == "claude":
        if not allowed_tools or not resolved_config_path.exists():
            return None, _basic_diagnostics(
                mcp_config_path=resolved_config_path,
                requested_servers=mcp_servers,
                resolved_servers=None,
                resolution_status=(
                    "config_missing"
                    if not resolved_config_path.exists()
                    else "config_empty"
                ),
            )
        return (
            {
                "mcp_config_path": str(resolved_config_path),
                "allowed_tools": allowed_tools,
            },
            _basic_diagnostics(
                mcp_config_path=resolved_config_path,
                requested_servers=mcp_servers,
                resolved_servers=mcp_servers,
                resolution_status="ok",
            ),
        )

    if canonical_agent == "gemini":
        if not mcp_servers:
            return None, _basic_diagnostics(
                mcp_config_path=resolved_config_path,
                requested_servers=mcp_servers,
                resolved_servers=None,
                resolution_status="config_empty",
            )
        return (
            {"mcp_server_names": mcp_servers},
            _basic_diagnostics(
                mcp_config_path=resolved_config_path,
                requested_servers=mcp_servers,
                resolved_servers=mcp_servers,
                resolution_status="ok",
            ),
        )

    if canonical_agent == "agy":
        # agy 1.0.0 has no per-invocation MCP flag (Phase 2 follow-up).
        # We mirror the Gemini path's diagnostics shape so the upstream
        # `_runtime_tool_config` validator does not fail-fast at dispatch
        # time; the lack of MCP wiring then surfaces at runtime as
        # MCP_TOOLS_NEVER_INVOKED, which is the precise + intended signal
        # for the seminar-writer bakeoff. The adapter itself ignores
        # `mcp_server_names`; we pass it through for parity / debuggability.
        if not mcp_servers:
            return None, _basic_diagnostics(
                mcp_config_path=resolved_config_path,
                requested_servers=mcp_servers,
                resolved_servers=None,
                resolution_status="config_empty",
            )
        return (
            {"mcp_server_names": mcp_servers},
            _basic_diagnostics(
                mcp_config_path=resolved_config_path,
                requested_servers=mcp_servers,
                resolved_servers=mcp_servers,
                resolution_status="ok",
            ),
        )

    if canonical_agent in ("grok", "deepseek", "qwen"):
        # Grok, DeepSeek, and Qwen route through Hermes; tool_config translation
        # is identical (Hermes reads MCP servers from ~/.hermes/config.yaml,
        # not from the per-call payload). Diagnostics point at the same file.
        if not mcp_servers:
            return None, _basic_diagnostics(
                mcp_config_path=Path.home() / ".hermes" / "config.yaml",
                requested_servers=mcp_servers,
                resolved_servers=None,
                resolution_status="config_empty",
            )
        return (
            {"hermes_mcp_servers": mcp_servers},
            _basic_diagnostics(
                mcp_config_path=Path.home() / ".hermes" / "config.yaml",
                requested_servers=mcp_servers,
                resolved_servers=mcp_servers,
                resolution_status="ok",
            ),
        )

    codex_servers, diagnostics = _codex_mcp_servers(resolved_config_path, mcp_servers)
    return ({"mcp_servers": codex_servers} if codex_servers else None), diagnostics
