"""Shared MCP tool_config builders for agent_runtime callers."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_MCP_CONFIG_PATH = _REPO_ROOT / ".mcp.json"
_AGY_APP_DATA_ENV = "AGY_APP_DATA_DIR"
_DEFAULT_AGY_CONFIG_DIRS = (
    "~/.gemini/config",
    "~/.gemini/antigravity-cli",
)
_AGY_MCP_CLI_TIMEOUT_SECONDS = 30
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
    """Normalize caller-facing agent labels to runtime adapter names.

    Order is load-bearing: ``grok-build`` and ``grok-hermes`` must be matched
    before the bare ``grok`` prefix, otherwise the permanent alias and the
    demoted Hermes seat both collapse into the native seat.
    """
    from .agent_identity import (
        HERMES_GROK_SEAT,
        NATIVE_GROK_SEAT,
        is_hermes_grok_seat,
        is_native_grok_seat,
        normalize_seat,
    )

    if agent.startswith("claude"):
        return "claude"
    if agent.startswith("gemini"):
        return "gemini"
    if agent.startswith("codex"):
        return "codex"
    # Order-sensitive: longer / more-specific grok* prefixes first.
    if agent.startswith("grok-build") or is_native_grok_seat(agent):
        return NATIVE_GROK_SEAT
    if agent.startswith("grok-hermes") or is_hermes_grok_seat(agent):
        return HERMES_GROK_SEAT
    if agent.startswith("grok"):
        # Bare / versioned labels such as "grok-4.6-tools" → native seat.
        return NATIVE_GROK_SEAT
    if agent.startswith("glm"):
        return "glm"
    if agent.startswith("hermes-deepseek"):
        return "hermes-deepseek"
    if agent.startswith("deepseek"):
        return "deepseek"
    if agent.startswith("qwen"):
        return "glm"
    if agent.startswith("agy"):
        return "agy"
    if agent.startswith("cursor"):
        return "cursor"
    if agent.startswith("kimi"):
        return "kimi"
    normalized = normalize_seat(agent)
    if normalized in {
        "claude",
        "gemini",
        "codex",
        NATIVE_GROK_SEAT,
        HERMES_GROK_SEAT,
        "deepseek",
        "hermes-deepseek",
        "glm",
        "qwen",
        "agy",
        "cursor",
        "kimi",
    }:
        return normalized
    return None


def _resolved_mcp_config_path(mcp_config_path: Path | None) -> Path:
    """Return the configured `.mcp.json` path, defaulting to repo root."""
    return (mcp_config_path or _DEFAULT_MCP_CONFIG_PATH).resolve()


def _resolved_agy_mcp_config_path() -> Path:
    """Return agy's global Antigravity MCP config path."""
    app_data_dir = os.environ.get(_AGY_APP_DATA_ENV)
    if app_data_dir:
        return (Path(app_data_dir).expanduser() / "mcp_config.json").resolve()

    candidates = [
        (Path(config_dir).expanduser() / "mcp_config.json").resolve()
        for config_dir in _DEFAULT_AGY_CONFIG_DIRS
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


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
    command = str(server_config.get("command") or "").strip()
    if server_type == "sse":
        return False
    if url.rstrip("/").endswith("/sse"):
        return False
    return bool(url or command)


def _agy_server_is_usable(server_config: Any) -> bool:
    """Return true for Antigravity HTTP or stdio MCP server entries.

    ``serverUrl`` is the field the agy CLI reads and the shape
    ``agy mcp add --type http`` writes. ``httpUrl`` / ``url`` are foreign
    (Claude/Gemini-format) spellings kept for back-compat only: the CLI lists
    such an entry as a dead ``stdio`` server with no command, so config-level
    usability is NOT proof the tools are visible — writer dispatch must also
    pass :func:`assert_agy_mcp_catalog_visible`.
    """
    if not isinstance(server_config, dict):
        return False
    if server_config.get("disabled") is True:
        return False
    return any(
        str(server_config.get(field) or "").strip()
        for field in ("serverUrl", "httpUrl", "url", "command")
    )


class AgyMcpCatalogError(RuntimeError):
    """The agy CLI's MCP catalog cannot expose a required server's tools."""


def _agy_binary() -> str:
    return shutil.which("agy") or str(Path.home() / ".local/bin/agy")


def _run_agy_mcp(args: list[str]) -> str:
    cmd = [_agy_binary(), "mcp", *args]
    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=_AGY_MCP_CLI_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AgyMcpCatalogError(f"`agy mcp {args[0]}` could not run: {exc}") from exc
    if completed.returncode != 0:
        raise AgyMcpCatalogError(
            f"`agy mcp {args[0]}` exited {completed.returncode}: "
            f"{(completed.stderr or completed.stdout).strip()[:500]}"
        )
    return completed.stdout


def agy_mcp_catalog() -> dict[str, dict[str, str]]:
    """Parse ``agy mcp list`` into ``{name: {type, status, target}}``.

    This is the catalog the CLI actually loads for ``agy -p``; unlike
    ``mcp_config.json`` it cannot be satisfied by a field the CLI ignores.
    ``target`` is empty for the dead-stdio row a foreign ``httpUrl`` produces.
    """
    catalog: dict[str, dict[str, str]] = {}
    for line in _run_agy_mcp(["list"]).splitlines():
        parts = line.split()
        if len(parts) < 3 or parts[0] == "NAME":
            continue
        catalog[parts[0]] = {
            "type": parts[1].lower(),
            "status": parts[2].lower(),
            "target": " ".join(parts[3:]),
        }
    return catalog


def _agy_catalog_problem(entry: dict[str, str] | None, url: str | None) -> str | None:
    """Return why a catalog row cannot serve tools, or ``None`` when it can."""
    if entry is None:
        return "not registered"
    if entry["status"] != "enabled":
        return f"status={entry['status']}"
    if not entry["target"]:
        return f"{entry['type']} entry with no command/URL (foreign `httpUrl` config shape)"
    if url is not None and (entry["type"] != "http" or entry["target"] != url):
        return f"{entry['type']} {entry['target']!r}, expected http {url!r}"
    return None


def _repo_mcp_server_url(server_name: str, mcp_config_path: Path | None = None) -> str | None:
    data = _load_mcp_config(_resolved_mcp_config_path(mcp_config_path)) or {}
    servers = data.get("mcpServers")
    server = servers.get(server_name) if isinstance(servers, dict) else None
    url = str(server.get("url") or "").strip() if isinstance(server, dict) else ""
    return url or None


def register_agy_mcp_http_server(server_name: str, url: str) -> bool:
    """Idempotently register ``server_name`` as an HTTP server in agy's catalog.

    Returns ``True`` when ``agy mcp add`` ran, ``False`` when the catalog was
    already correct. Raises :class:`AgyMcpCatalogError` if the catalog is still
    wrong afterwards.
    """
    if _agy_catalog_problem(agy_mcp_catalog().get(server_name), url) is None:
        return False
    _run_agy_mcp(["add", "--type", "http", server_name, url])
    problem = _agy_catalog_problem(agy_mcp_catalog().get(server_name), url)
    if problem is not None:
        raise AgyMcpCatalogError(
            f"`agy mcp add --type http {server_name} {url}` ran but the catalog "
            f"still shows {server_name!r} as {problem}. Recovery: inspect "
            "`agy mcp list` / `agy mcp remove`, then re-run the register helper."
        )
    return True


def assert_agy_mcp_catalog_visible(
    server_names: list[str],
    *,
    mcp_config_path: Path | None = None,
) -> dict[str, dict[str, str]]:
    """Fail closed unless every server is a live row in ``agy mcp list``.

    A server with a URL in the repo ``.mcp.json`` must be listed as ``http`` on
    exactly that URL. Returns the verified catalog rows.
    """
    catalog = agy_mcp_catalog()
    problems = {
        name: problem
        for name in server_names
        if (problem := _agy_catalog_problem(catalog.get(name), _repo_mcp_server_url(name, mcp_config_path)))
    }
    if problems:
        details = "; ".join(f"{name}: {problem}" for name, problem in problems.items())
        raise AgyMcpCatalogError(
            f"agy MCP catalog cannot expose required tools ({details}). "
            "`agy -p` would run with no mcp__<server>__* tools. Recovery: "
            "re-run the register helper — "
            "`scripts.agent_runtime.tool_config.ensure_agy_mcp_catalog([...])` "
            "or `agy mcp add --type http <name> <url>` — then check `agy mcp list`."
        )
    return {name: catalog[name] for name in server_names}


def ensure_agy_mcp_catalog(
    server_names: list[str],
    *,
    mcp_config_path: Path | None = None,
) -> dict[str, Any]:
    """Register repo-known HTTP servers in agy's catalog, then verify it.

    Writer-path preflight: idempotent self-heal followed by the fail-closed
    catalog check. Returns ``{"registered": [...], "catalog": {...}}``.
    """
    registered = [
        name
        for name in server_names
        if (url := _repo_mcp_server_url(name, mcp_config_path)) and register_agy_mcp_http_server(name, url)
    ]
    catalog = assert_agy_mcp_catalog_visible(server_names, mcp_config_path=mcp_config_path)
    return {"registered": registered, "catalog": catalog}


def _agy_mcp_servers(
    mcp_config_path: Path,
    requested_servers: list[str] | None,
) -> tuple[dict[str, list[str]] | None, dict[str, Any]]:
    """Return agy's requested MCP server names plus resolution diagnostics."""
    requested = list(requested_servers or [])

    data = _load_mcp_config(mcp_config_path)
    if not data:
        return None, _basic_diagnostics(
            mcp_config_path=mcp_config_path,
            requested_servers=requested,
            resolved_servers=None,
            resolution_status="config_empty",
        )

    servers = data.get("mcpServers")
    if not isinstance(servers, dict) or not servers:
        return None, _basic_diagnostics(
            mcp_config_path=mcp_config_path,
            requested_servers=requested,
            resolved_servers=None,
            resolution_status="config_empty",
        )

    usable_server_names = [
        server_name
        for server_name, server_config in servers.items()
        if _agy_server_is_usable(server_config)
    ]
    if not requested or not usable_server_names:
        return None, _basic_diagnostics(
            mcp_config_path=mcp_config_path,
            requested_servers=requested,
            resolved_servers=None,
            resolution_status="config_empty",
            missing_server_names=requested,
        )

    usable_servers = set(usable_server_names)
    selected = [server_name for server_name in requested if server_name in usable_servers]
    missing = [server_name for server_name in requested if server_name not in usable_servers]
    if not selected:
        return None, _basic_diagnostics(
            mcp_config_path=mcp_config_path,
            requested_servers=requested,
            resolved_servers=None,
            resolution_status="servers_not_found",
            missing_server_names=missing,
        )

    return {"mcp_server_names": selected}, _basic_diagnostics(
        mcp_config_path=mcp_config_path,
        requested_servers=requested,
        resolved_servers=selected,
        resolution_status="ok",
        missing_server_names=missing,
    )


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
        # agy enables MCP through the global Antigravity config, not a
        # per-invocation CLI flag. The CLI's HTTP field is `serverUrl` (what
        # `agy mcp add --type http` writes); a Claude-format `httpUrl` entry
        # resolves here but lists as a dead stdio server, so writer dispatch
        # additionally runs `ensure_agy_mcp_catalog` (#7994). The adapter still
        # receives resolved names for parity and observability, and
        # MCP_TOOLS_NEVER_INVOKED remains the runtime backstop.
        return _agy_mcp_servers(_resolved_agy_mcp_config_path(), mcp_servers)

    if canonical_agent == "kimi":
        # Kimi Code 0.26 reads any MCP configuration from its own persisted
        # profile and exposes no per-invocation MCP selector. Do not silently
        # hand it Codex-shaped `.mcp.json` config. Requested servers therefore
        # fail closed until a scoped Kimi MCP contract is implemented.
        kimi_config_path = Path.home() / ".kimi-code" / "config.toml"
        return None, _basic_diagnostics(
            mcp_config_path=kimi_config_path,
            requested_servers=mcp_servers,
            resolved_servers=None,
            resolution_status="servers_not_found" if mcp_servers else "config_empty",
            missing_server_names=mcp_servers,
        )

    if canonical_agent in ("grok-hermes", "deepseek", "hermes-deepseek", "qwen"):
        # Hermes-backed seats (grok-hermes / DeepSeek / ask-hermes /
        # Qwen): tool_config translation is identical (Hermes reads MCP
        # servers from ~/.hermes/config.yaml, not from the per-call payload).
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

    if canonical_agent in ("grok", "glm"):
        # Native grok CLI seat and glm read MCP servers from local config / environment.
        # The adapter only needs the requested names for observability and to opt into non-interactive approval.
        if not mcp_servers:
            return None, _basic_diagnostics(
                mcp_config_path=Path.home() / f".{canonical_agent}" / "mcp.json",
                requested_servers=mcp_servers,
                resolved_servers=None,
                resolution_status="config_empty",
            )
        return (
            {
                "always_approve": True,
                "mcp_server_names": mcp_servers,
            },
            _basic_diagnostics(
                mcp_config_path=Path.home() / f".{canonical_agent}" / "mcp.json",
                requested_servers=mcp_servers,
                resolved_servers=mcp_servers,
                resolution_status="ok",
            ),
        )

    if canonical_agent == "cursor":
        # For Phase 2, the workspace value defaults to cwd of the subprocess.
        # Diagnostic config_path should point at {cwd}/.cursor/mcp.json
        # (not repo .mcp.json).
        workspace_mcp_path = Path.cwd() / ".cursor" / "mcp.json"
        return (
            {
                "output_format": "stream-json",
                "approve_mcps": True,
                "mcp_config_path": str(resolved_config_path),
                "mcp_server_names": mcp_servers,
            },
            _basic_diagnostics(
                mcp_config_path=workspace_mcp_path,
                requested_servers=mcp_servers,
                resolved_servers=mcp_servers,
                resolution_status="ok" if mcp_servers else "config_empty",
            ),
        )

    codex_servers, diagnostics = _codex_mcp_servers(resolved_config_path, mcp_servers)
    return ({"mcp_servers": codex_servers} if codex_servers else None), diagnostics
