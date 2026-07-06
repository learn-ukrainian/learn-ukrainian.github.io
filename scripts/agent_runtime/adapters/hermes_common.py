"""Shared helpers for Hermes-backed agent runtime adapters."""
from __future__ import annotations

import logging
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from ..routes import (
    RUNTIME_ROUTE_TOOL_CONFIG_KEY,
    forbidden_glm_error,
    is_forbidden_glm_route,
)
from .base import InvocationPlan

_ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_RATE_LIMIT_RE = re.compile(
    r"rate limit|rate_limit|quota exceeded|too many requests|\bHTTP 429\b|\b429\b",
    re.IGNORECASE,
)
_FALLBACK_LOG_RE = re.compile(
    r"Fallback activated:\s*(?P<requested_model>.*?)\s*(?:\u2192|->)\s*"
    r"(?P<actual_model>[^\s(]+)\s*\((?P<actual_provider>[^)]+)\)",
    re.IGNORECASE,
)
_FALLBACK_STATUS_RE = re.compile(
    r"switching to fallback:\s*(?P<actual_model>\S+)\s+via\s+"
    r"(?P<actual_provider>[A-Za-z0-9_.:-]+)",
    re.IGNORECASE,
)
# Auth-failure path emits provider-first with a spaced slash
# (hermes_cli/cli_agent_setup_mixin.py:65: "⚠️  Primary auth failed —
# switching to fallback: {provider} / {model}"). Provider names never
# contain "/"; models may (e.g. deepseek/deepseek-v3.2), so split on the
# SPACED slash only.
_FALLBACK_AUTH_RE = re.compile(
    r"Primary auth failed\s*[—–-]+\s*switching to fallback:\s*"
    r"(?P<actual_provider>[^\s/]+)\s+/\s+(?P<actual_model>\S+)",
    re.IGNORECASE,
)
# Empty-response retry path (agent/conversation_loop.py:4848/:4853) emits two
# more formats: buffer status "↻ Switched to fallback: {model} ({provider})"
# and logger line "Fallback activated after empty responses: now using
# {model} on {provider}".
_FALLBACK_EMPTY_STATUS_RE = re.compile(
    r"Switched to fallback:\s*(?P<actual_model>\S+)\s*\((?P<actual_provider>[^)]+)\)",
    re.IGNORECASE,
)
_FALLBACK_EMPTY_LOG_RE = re.compile(
    r"Fallback activated after empty responses:\s*now using\s+"
    r"(?P<actual_model>\S+)\s+on\s+(?P<actual_provider>\S+)",
    re.IGNORECASE,
)
# Hermes surfaces provider API failures as the FINAL assistant message on
# stdout with returncode 0, formatted "HTTP {status}: {message}" or
# "HTTP {status} — {title} — Ray {id}" (hermes-agent run_agent.py
# _describe_api_error paths). Such a line is a failed invocation, not
# content: without detection it parses ok=True, ships the error string as
# the response, and the runner failover classifier never runs (probe
# finding 2026-07-06, forced 401 → route 0 reported "ok").
_INBAND_HTTP_ERROR_RE = re.compile(r"^HTTP\s+(?P<status>[45]\d{2})\b")
HERMES_SUBSTITUTION_MARKER = "HERMES_FALLBACK_SUBSTITUTION"
HERMES_GLM_FORBIDDEN_MARKER = "HERMES_GLM_FORBIDDEN"


@dataclass(frozen=True)
class HermesInvocationContext:
    """Non-secret context carried from Hermes plan build into parse."""

    config: dict[str, Any]
    env_overrides: dict[str, str]
    metadata: dict[str, Any]


@dataclass(frozen=True)
class HermesParseFields:
    """Common parsed fields for Hermes adapter-specific ParseResult classes."""

    ok: bool
    response: str
    stderr_excerpt: str | None
    rate_limited: bool
    substitution: dict[str, Any] | None


def strip_ansi(text: str) -> str:
    """Remove terminal control sequences and surrounding whitespace."""
    return _ANSI_RE.sub("", text or "").strip()


def read_hermes_config(path: Path) -> dict[str, Any]:
    """Read a Hermes YAML config without surfacing secrets."""
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return {}
    return data if isinstance(data, dict) else {}


def top_level_agent_effort(config: dict[str, Any]) -> str | None:
    """Return ``agent.reasoning_effort`` from Hermes config, if readable."""
    agent = config.get("agent")
    if not isinstance(agent, dict):
        return None
    effort = agent.get("reasoning_effort")
    if isinstance(effort, str) and effort.strip():
        return effort.strip()
    return None


def sources_mcp_registered(config: dict[str, Any]) -> bool:
    """Return whether Hermes config exposes the project ``sources`` MCP server."""
    servers = config.get("mcp_servers")
    if not isinstance(servers, dict):
        return False
    sources = servers.get("sources")
    if not isinstance(sources, dict):
        return False
    return bool(sources.get("enabled") is not False and sources.get("url"))


def translate_mcp_prefix_for_hermes(prompt: str) -> str:
    """Rewrite ``mcp__sources__X`` to ``mcp_sources_X`` for Hermes routing.

    Empirical finding (2026-05-19 B1 writer bakeoff investigation):
    Hermes registers MCP tools using a single-underscore convention
    (``mcp_sources_search_text``, etc. — visible in
    ``~/.hermes/logs/agent.log``: ``MCP server 'sources' (HTTP):
    registered 33 tool(s): mcp_sources_search_sources, ...``). The
    canonical V7 writer prompt documents tools with double-underscore
    (``mcp__sources__search_text``) — the MCP spec convention used by
    claude / codex. When the prompt teaches one form and the runtime
    registers another, models that parrot prompt names emit tool calls
    Hermes can't dispatch, so no MCP invocation actually fires even
    though ``verification_trace`` blocks declare intent.

    Translating the prompt before handing it to Hermes aligns the two
    conventions without per-writer prompt-template forks. The same fix
    applies to all three Hermes-routed adapters (deepseek/qwen/grok).
    Companion gate-side tolerance shipped in commit ``0fc0f0d427``.
    """
    return prompt.replace("mcp__sources__", "mcp_sources_")


def hermes_home_from_tool_config(tool_config: dict | None) -> tuple[Path, bool]:
    """Resolve the Hermes home directory and whether it was caller-supplied."""
    raw_home = (tool_config or {}).get("hermes_home")
    if raw_home:
        return Path(str(raw_home)).expanduser().resolve(), True
    env_home = os.environ.get("HERMES_HOME")
    if env_home:
        return Path(env_home).expanduser().resolve(), False
    return (Path.home() / ".hermes").resolve(), False


def _normalize_route_part(value: Any) -> str:
    return str(value or "").strip()


def resolve_hermes_requested_route(
    *,
    tool_config: dict | None,
    default_provider: str,
    requested_model: str,
    provider_forced: bool = False,
) -> tuple[str, str, bool]:
    """Apply a runner-level provider/model override for Hermes lanes."""
    raw_route = (tool_config or {}).get(RUNTIME_ROUTE_TOOL_CONFIG_KEY)
    if not isinstance(raw_route, dict):
        return default_provider, requested_model, provider_forced

    provider = _normalize_route_part(raw_route.get("provider")) or default_provider
    route_model = _normalize_route_part(raw_route.get("model")) or requested_model
    return provider, route_model, True


def _fallback_entries(config: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract fallback route entries from Hermes config shape variants."""
    entries: list[dict[str, Any]] = []
    raw_entries = config.get("fallback_providers")
    if isinstance(raw_entries, list):
        for raw_entry in raw_entries:
            if isinstance(raw_entry, dict):
                entries.append(dict(raw_entry))
            elif isinstance(raw_entry, str) and raw_entry.strip():
                entries.append({"provider": raw_entry.strip()})
    elif isinstance(raw_entries, dict):
        for provider, raw_entry in raw_entries.items():
            if isinstance(raw_entry, dict):
                entry = dict(raw_entry)
                entry.setdefault("provider", provider)
                entries.append(entry)
            elif isinstance(raw_entry, str) and raw_entry.strip():
                entries.append({"provider": provider, "model": raw_entry.strip()})
            else:
                entries.append({"provider": provider})

    fallback_model = config.get("fallback_model")
    if isinstance(fallback_model, str) and fallback_model.strip():
        entries.append({"model": fallback_model.strip()})
    return entries


def _configured_model_route(config: dict[str, Any]) -> tuple[str | None, str | None]:
    model_config = config.get("model")
    if not isinstance(model_config, dict):
        return None, None
    provider = model_config.get("provider")
    model = model_config.get("default") or model_config.get("model")
    return (
        provider.strip() if isinstance(provider, str) and provider.strip() else None,
        model.strip() if isinstance(model, str) and model.strip() else None,
    )


def _raise_for_forbidden_glm_routes(
    *,
    requested_provider: str,
    requested_model: str,
    config: dict[str, Any],
    provider_forced: bool,
) -> None:
    if is_forbidden_glm_route(requested_provider, requested_model):
        raise ValueError(
            forbidden_glm_error(
                provider=requested_provider,
                model=requested_model,
                source="requested route",
            )
        )

    configured_provider, configured_model = _configured_model_route(config)
    if (
        not provider_forced
        and configured_provider
        and is_forbidden_glm_route(
            configured_provider,
            requested_model or configured_model,
        )
    ):
        raise ValueError(
            forbidden_glm_error(
                provider=configured_provider,
                model=requested_model or configured_model,
                source="Hermes model.provider",
            )
        )

    for entry in _fallback_entries(config):
        provider = entry.get("provider")
        model = entry.get("model") or requested_model
        if is_forbidden_glm_route(provider, model):
            raise ValueError(
                forbidden_glm_error(
                    provider=provider,
                    model=model,
                    source="Hermes fallback_providers",
                )
            )


def build_hermes_invocation_context(
    *,
    tool_config: dict | None,
    requested_provider: str,
    requested_model: str,
    provider_forced: bool = False,
) -> HermesInvocationContext:
    """Build non-secret Hermes context and enforce pre-launch route guards."""
    hermes_home, caller_supplied_home = hermes_home_from_tool_config(tool_config)
    config_path = hermes_home / "config.yaml"
    config = read_hermes_config(config_path)
    _raise_for_forbidden_glm_routes(
        requested_provider=requested_provider,
        requested_model=requested_model,
        config=config,
        provider_forced=provider_forced,
    )

    log_path = hermes_home / "logs" / "agent.log"
    try:
        log_offset = log_path.stat().st_size
    except OSError:
        log_offset = 0

    env_overrides = {"HERMES_HOME": str(hermes_home)} if caller_supplied_home else {}
    metadata = {
        "hermes": {
            "requested_provider": requested_provider,
            "requested_model": requested_model,
            "config_path": str(config_path),
            "log_path": str(log_path),
            "log_offset": log_offset,
            "isolated_home": caller_supplied_home,
        }
    }
    return HermesInvocationContext(
        config=config,
        env_overrides=env_overrides,
        metadata=metadata,
    )


def _hermes_metadata(plan: InvocationPlan | None) -> dict[str, Any] | None:
    if plan is None:
        return None
    metadata = getattr(plan, "metadata", None)
    if not isinstance(metadata, dict):
        return None
    hermes = metadata.get("hermes")
    return hermes if isinstance(hermes, dict) else None


def _read_log_since_offset(log_path: Path, offset: int) -> str:
    try:
        size = log_path.stat().st_size
        start = offset if 0 <= offset <= size else 0
        with log_path.open("r", encoding="utf-8", errors="replace") as handle:
            handle.seek(start)
            return handle.read()
    except OSError:
        return ""


def _fallback_match(text: str) -> tuple[str, str] | None:
    matches: list[tuple[str, str]] = []
    # All patterns verified verbatim against hermes-agent source
    # (chat_completion_helpers.py:1484/:1488, cli_agent_setup_mixin.py:65,
    # conversation_loop.py:4848/:4853). Keep the families in sync with
    # upstream when Hermes is updated.
    fallback_patterns = (
        _FALLBACK_LOG_RE,
        _FALLBACK_STATUS_RE,
        _FALLBACK_AUTH_RE,
        _FALLBACK_EMPTY_STATUS_RE,
        _FALLBACK_EMPTY_LOG_RE,
    )
    for pattern in fallback_patterns:
        for match in pattern.finditer(text):
            matches.append((
                match.group("actual_provider").strip(),
                match.group("actual_model").strip(),
            ))
    return matches[-1] if matches else None


def resolve_hermes_substitution(
    *,
    stdout: str,
    stderr: str,
    plan: InvocationPlan | None,
) -> dict[str, Any] | None:
    """Resolve requested vs actual Hermes route from plan metadata and logs."""
    metadata = _hermes_metadata(plan)
    if metadata is None:
        return None

    requested_provider = _normalize_route_part(metadata.get("requested_provider"))
    requested_model = _normalize_route_part(metadata.get("requested_model"))
    actual_provider = requested_provider
    actual_model = requested_model
    source = "requested"

    log_path_raw = metadata.get("log_path")
    log_offset_raw = metadata.get("log_offset")
    if isinstance(log_path_raw, str) and log_path_raw:
        try:
            log_offset = int(log_offset_raw or 0)
        except (TypeError, ValueError):
            log_offset = 0
        log_text = _read_log_since_offset(Path(log_path_raw), log_offset)
        log_match = _fallback_match(log_text)
        if log_match is not None:
            actual_provider, actual_model = log_match
            source = "hermes-agent.log"

    output_match = _fallback_match(f"{stdout or ''}\n{stderr or ''}")
    if output_match is not None:
        actual_provider, actual_model = output_match
        source = "captured-output"

    substituted = (
        bool(actual_provider or actual_model)
        and (
            actual_provider != requested_provider
            or actual_model != requested_model
        )
    )
    return {
        "requested_provider": requested_provider,
        "requested_model": requested_model,
        "actual_provider": actual_provider,
        "actual_model": actual_model,
        "substituted": substituted,
        "source": source,
        "marker": HERMES_SUBSTITUTION_MARKER if substituted else None,
    }


def emit_hermes_substitution_marker(
    substitution: dict[str, Any] | None,
    *,
    logger: logging.Logger,
) -> None:
    """Emit a loud marker for Hermes fallback substitution."""
    if not substitution or not substitution.get("substituted"):
        return
    message = (
        f"{HERMES_SUBSTITUTION_MARKER}: "
        f"{substitution.get('requested_provider')}/"
        f"{substitution.get('requested_model')} -> "
        f"{substitution.get('actual_provider')}/"
        f"{substitution.get('actual_model')} "
        f"source={substitution.get('source')}"
    )
    logger.warning(message)
    print(message, file=sys.stderr)


def hermes_glm_guard_error(substitution: dict[str, Any] | None) -> str | None:
    """Return hard-fail text if the resolved actual route is zai/GLM."""
    if not substitution:
        return None
    provider = substitution.get("actual_provider")
    model = substitution.get("actual_model")
    if not is_forbidden_glm_route(provider, model):
        return None
    return forbidden_glm_error(
        provider=provider,
        model=model,
        source="Hermes actual route",
    )


def _inband_provider_error(response: str) -> tuple[str, str] | None:
    """Return ``(error_line, status)`` when stdout is an in-band HTTP error.

    Deliberately conservative to avoid eating legitimate content: the whole
    stripped response must be ONE line, at most 600 chars (hermes truncates
    the provider message to ≤500), and start with ``HTTP 4xx``/``HTTP 5xx``.
    A multi-line answer that merely discusses an HTTP status stays ok=True.
    """
    candidate = response.strip()
    if not candidate or "\n" in candidate or len(candidate) > 600:
        return None
    match = _INBAND_HTTP_ERROR_RE.match(candidate)
    if match is None:
        return None
    return candidate, match.group("status")


def build_hermes_parse_fields(
    *,
    stdout: str,
    stderr: str,
    returncode: int,
    plan: InvocationPlan | None,
    logger: logging.Logger,
) -> HermesParseFields:
    """Parse common Hermes stdout/stderr and attach substitution metadata."""
    response = strip_ansi(stdout)
    clean_stderr = strip_ansi(stderr)
    rate_limited = returncode != 0 and bool(_RATE_LIMIT_RE.search(clean_stderr))
    substitution = resolve_hermes_substitution(
        stdout=stdout,
        stderr=stderr,
        plan=plan,
    )
    emit_hermes_substitution_marker(substitution, logger=logger)

    guard_error = hermes_glm_guard_error(substitution)
    if guard_error is not None:
        return HermesParseFields(
            ok=False,
            response="",
            stderr_excerpt=guard_error[:500],
            rate_limited=False,
            substitution=substitution,
        )

    inband_error = _inband_provider_error(response) if returncode == 0 else None
    if inband_error is not None:
        error_text, status = inband_error
        return HermesParseFields(
            ok=False,
            response="",
            stderr_excerpt=error_text[:500],
            rate_limited=rate_limited or status == "429",
            substitution=substitution,
        )

    ok = returncode == 0 and bool(response) and not rate_limited
    stderr_excerpt = None if ok else (clean_stderr or response or None)
    return HermesParseFields(
        ok=ok,
        response=response if ok else "",
        stderr_excerpt=stderr_excerpt[:500] if stderr_excerpt else None,
        rate_limited=rate_limited,
        substitution=substitution,
    )
