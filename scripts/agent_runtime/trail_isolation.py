"""Fail-closed weak-driver tool isolation for TrailSpec sessions.

The trail executor, not a weak model, owns command execution.  This module
builds the private MCP configuration and adapter-specific admission profile
used when callers request ``tool_config={"trail_isolation": ...}``.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRAIL_MCP_SERVER_NAME = "trail"
TRAIL_TOOL_NAMES: tuple[str, ...] = ("trail_status", "trail_step", "trail_summon")
KIMICC_TRAIL_TOOLS: tuple[str, ...] = tuple(
    f"mcp__{TRAIL_MCP_SERVER_NAME}__{name}" for name in TRAIL_TOOL_NAMES
)
GROK_TRAIL_TOOLS: tuple[str, ...] = tuple(
    f"{TRAIL_MCP_SERVER_NAME}__{name}" for name in TRAIL_TOOL_NAMES
)
GROK_TRAIL_DENY_TOOLS: tuple[str, ...] = (
    "Bash",
    "Write",
    "Edit",
    "MultiEdit",
    "NotebookEdit",
    "Read",
    "Glob",
    "Grep",
    "LS",
    "WebFetch",
    "WebSearch",
)


class TrailIsolationError(ValueError):
    """Raised when a requested weak-driver boundary cannot be proven."""


@dataclass
class TrailIsolationLaunch:
    """Parent-owned temporary MCP configuration for one isolated invocation."""

    tool_config: dict[str, Any]
    root: Path

    def cleanup(self) -> None:
        """Remove the per-invocation config after the agent exits."""
        shutil.rmtree(self.root, ignore_errors=True)


def trail_isolation_requested(tool_config: Mapping[str, Any] | None) -> bool:
    """Return whether a caller requested the trail isolation profile."""
    if not tool_config or "trail_isolation" not in tool_config:
        return False
    return tool_config["trail_isolation"] is not None and tool_config["trail_isolation"] is not False


def _tool_csv(tool_names: tuple[str, ...]) -> str:
    return ",".join(tool_names)


def _profile_for_agent(agent_name: str, tool_config: Mapping[str, Any]) -> str:
    if agent_name in {"grok", "grok-build"}:
        return "grok"
    if agent_name == "kimi":
        if tool_config.get("harness") != "kimicc":
            raise TrailIsolationError(
                "trail isolation refused for native Kimi: the native CLI cannot prove tool admission; use harness='kimicc'"
            )
        return "kimicc"
    if agent_name == "glm":
        raise TrailIsolationError(
            "trail isolation refused for GLM: the opencode adapter ignores tool restrictions"
        )
    if agent_name == "grok-hermes":
        raise TrailIsolationError(
            "trail isolation refused for grok-hermes: this harness cannot prove trail tool admission"
        )
    raise TrailIsolationError(
        f"trail isolation refused for {agent_name!r}: this harness cannot prove trail tool admission"
    )


def _write_private_mcp_config(root: Path) -> Path:
    """Write the sole admitted stdio MCP server without using ambient config."""
    python_bin = PROJECT_ROOT / ".venv" / "bin" / "python"
    mcp_server = PROJECT_ROOT / "scripts" / "orchestration" / "trails" / "trail_mcp.py"
    if not python_bin.is_file() or not os.access(python_bin, os.X_OK):
        raise TrailIsolationError(f"trail isolation requires executable {python_bin}")
    if not mcp_server.is_file():
        raise TrailIsolationError(f"trail isolation MCP server missing: {mcp_server}")

    config_path = root / ".mcp.json"
    payload = {
        "mcpServers": {
            TRAIL_MCP_SERVER_NAME: {
                "command": str(python_bin),
                "args": [str(mcp_server)],
            }
        }
    }
    descriptor = os.open(
        config_path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
        0o400,
    )
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=True, separators=(",", ":"))
        handle.write("\n")
    config_path.chmod(0o400)
    return config_path


def prepare_trail_isolation(
    *,
    agent_name: str,
    mode: str,
    tool_config: Mapping[str, Any] | None,
) -> TrailIsolationLaunch | None:
    """Provision the exact three-tool profile or refuse before any spawn.

    The caller may select only the profile and, for Kimi, the KimiCC harness.
    Ambient MCP configuration and caller-provided allow/deny lists are never
    merged into a weak-driver invocation.
    """
    if not trail_isolation_requested(tool_config):
        return None
    if mode != "read-only":
        raise TrailIsolationError("trail isolation requires mode='read-only'")

    supplied = dict(tool_config or {})
    allowed_input_keys = {"trail_isolation", "harness"}
    unexpected = sorted(set(supplied) - allowed_input_keys)
    if unexpected:
        raise TrailIsolationError(
            f"trail isolation refuses caller-supplied tool configuration: {unexpected}"
        )
    requested = supplied.get("trail_isolation")
    if requested is not True and not isinstance(requested, dict):
        raise TrailIsolationError("trail_isolation must be true or a configuration object")

    profile = _profile_for_agent(agent_name, supplied)
    root = Path(tempfile.mkdtemp(prefix="agent-runtime-trail-isolation-"))
    root.chmod(0o700)
    try:
        mcp_config_path = _write_private_mcp_config(root)
        tool_names = KIMICC_TRAIL_TOOLS if profile == "kimicc" else GROK_TRAIL_TOOLS
        configured: dict[str, Any] = {
            "trail_isolation": True,
            "mcp_config_path": str(mcp_config_path),
            "allowed_tools": _tool_csv(tool_names),
            "tools": _tool_csv(tool_names),
            "strict_mcp_config": True,
            "setting_sources": "",
            "trail_isolation_cwd": str(root),
        }
        if profile == "kimicc":
            configured["harness"] = "kimicc"
        return TrailIsolationLaunch(tool_config=configured, root=root)
    except BaseException:
        shutil.rmtree(root, ignore_errors=True)
        raise


def assert_trail_isolation_config(tool_config: Mapping[str, Any], *, profile: str) -> Path:
    """Validate that an adapter received the parent-produced exact profile."""
    if profile not in {"grok", "kimicc"}:
        raise TrailIsolationError(f"unknown trail isolation profile {profile!r}")
    expected_tools = GROK_TRAIL_TOOLS if profile == "grok" else KIMICC_TRAIL_TOOLS
    expected_csv = _tool_csv(expected_tools)
    if tool_config.get("trail_isolation") is not True:
        raise TrailIsolationError("trail isolation profile marker is missing")
    for key in ("allowed_tools", "tools"):
        if tool_config.get(key) != expected_csv:
            raise TrailIsolationError(f"trail isolation {key} is not the exact three-tool allowlist")
    if tool_config.get("strict_mcp_config") is not True or tool_config.get("setting_sources") != "":
        raise TrailIsolationError("trail isolation requires strict MCP config and no ambient setting sources")

    root_value = tool_config.get("trail_isolation_cwd")
    config_value = tool_config.get("mcp_config_path")
    if not isinstance(root_value, str) or not isinstance(config_value, str):
        raise TrailIsolationError("trail isolation private MCP configuration is missing")
    root = Path(root_value)
    config_path = Path(config_value)
    try:
        resolved_root = root.resolve(strict=True)
        resolved_config = config_path.resolve(strict=True)
    except OSError as exc:
        raise TrailIsolationError("trail isolation private MCP configuration is unreadable") from exc
    if root.is_symlink() or config_path.is_symlink() or resolved_config != resolved_root / ".mcp.json":
        raise TrailIsolationError("trail isolation MCP configuration path is invalid")
    try:
        payload = json.loads(resolved_config.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TrailIsolationError("trail isolation MCP configuration is invalid JSON") from exc
    servers = payload.get("mcpServers") if isinstance(payload, dict) else None
    server = servers.get(TRAIL_MCP_SERVER_NAME) if isinstance(servers, dict) else None
    expected_python = PROJECT_ROOT / ".venv" / "bin" / "python"
    expected_server = PROJECT_ROOT / "scripts" / "orchestration" / "trails" / "trail_mcp.py"
    if not isinstance(server, dict) or set(servers) != {TRAIL_MCP_SERVER_NAME}:
        raise TrailIsolationError("trail isolation MCP configuration exposes an unexpected server")
    if server.get("command") != str(expected_python) or server.get("args") != [str(expected_server)]:
        raise TrailIsolationError("trail isolation MCP server command is not parent-owned")
    return resolved_root
