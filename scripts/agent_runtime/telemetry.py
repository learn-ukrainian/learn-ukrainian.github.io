"""Dispatch telemetry helpers for agent runtime invocations.

Resolves the observability-only metadata we want to persist for delegated
tasks:

- the effective model string
- the effective effort / reasoning level
- the CLI version

The runtime uses ``resolve_invocation_telemetry()`` after an adapter has
built the exact subprocess argv, so the telemetry reflects what we are
actually about to invoke rather than a guessed default.

``resolve_dispatch_start_telemetry()`` is a best-effort preflight variant
used by ``delegate.py dispatch`` so the task state file already contains the
fields while the task is still spawning/running. The worker backfills the
runtime-resolved values on completion.
"""
from __future__ import annotations

import json
import logging
import re
import subprocess
import tomllib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from .adapters.base import InvocationPlan
from .registry import AGENTS

_logger = logging.getLogger(__name__)
_SEMVER_RE = re.compile(r"(?<![\d.])v?(\d+(?:\.\d+){1,3})(?![\d.])")
_UNKNOWN = "unknown"


@dataclass(frozen=True)
class InvocationTelemetry:
    """Resolved observability metadata for one agent invocation."""

    model: str
    effort: str
    cli_version: str


def _warn_unknown(field: str, agent_name: str, detail: str) -> None:
    _logger.warning(
        "dispatch telemetry for %s could not resolve %s: %s; recording %r",
        agent_name,
        field,
        detail,
        _UNKNOWN,
    )


def _arg_after(cmd: list[str], *flags: str) -> str | None:
    for index, token in enumerate(cmd):
        if token in flags and index + 1 < len(cmd):
            value = str(cmd[index + 1]).strip()
            if value:
                return value
    return None


def _config_override(cmd: list[str], key: str) -> str | None:
    for index, token in enumerate(cmd[:-1]):
        if token != "-c":
            continue
        candidate = str(cmd[index + 1]).strip()
        prefix = f"{key}="
        if candidate.startswith(prefix):
            value = candidate[len(prefix) :].strip().strip("\"'")
            if value:
                return value
    return None


def _extract_semverish(text: str) -> str | None:
    if not text:
        return None
    match = _SEMVER_RE.search(text)
    return match.group(1) if match else None


def _read_json_file(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _read_toml_file(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return None


def _nested_lookup(data: Any, keys: tuple[str, ...]) -> str | None:
    if isinstance(data, dict):
        for key, value in data.items():
            if str(key) in keys and isinstance(value, str) and value.strip():
                return value.strip()
            nested = _nested_lookup(value, keys)
            if nested:
                return nested
    elif isinstance(data, list):
        for item in data:
            nested = _nested_lookup(item, keys)
            if nested:
                return nested
    return None


def _codex_config() -> dict[str, Any]:
    return _read_toml_file(Path.home() / ".codex" / "config.toml") or {}


def _claude_settings() -> dict[str, Any]:
    return _read_json_file(Path.home() / ".claude" / "settings.json") or {}


def _gemini_settings() -> dict[str, Any]:
    candidates = (
        Path.cwd() / ".gemini" / "settings.json",
        Path.home() / ".gemini" / "settings.json",
        Path.home() / ".config" / "gemini" / "settings.json",
    )
    for candidate in candidates:
        data = _read_json_file(candidate)
        if data:
            return data
    return {}


def _default_model_for(agent_name: str) -> str | None:
    entry = AGENTS.get(agent_name, {})
    raw = entry.get("default_model")
    return str(raw).strip() if isinstance(raw, str) and str(raw).strip() else None


def _resolve_model_from_plan(agent_name: str, plan: InvocationPlan) -> str | None:
    del agent_name
    return _arg_after(plan.cmd, "-m", "--model")


def _resolve_effort_from_plan(agent_name: str, plan: InvocationPlan) -> str | None:
    if agent_name == "codex":
        return _config_override(plan.cmd, "model_reasoning_effort")
    if agent_name == "claude":
        return _arg_after(plan.cmd, "--effort")
    if agent_name == "gemini":
        return None
    return None


def _resolve_model_from_defaults(agent_name: str, requested_model: str | None) -> str | None:
    if requested_model:
        return requested_model
    if agent_name == "codex":
        value = _codex_config().get("model")
        return str(value).strip() if isinstance(value, str) and str(value).strip() else None
    if agent_name == "gemini":
        return _nested_lookup(
            _gemini_settings(),
            ("model", "defaultModel", "selectedModel", "modelName", "default_model"),
        )
    if agent_name == "claude":
        return _default_model_for(agent_name)
    return _default_model_for(agent_name)


def _resolve_effort_from_defaults(agent_name: str, requested_effort: str | None) -> str | None:
    if requested_effort:
        return requested_effort
    if agent_name == "codex":
        value = _codex_config().get("model_reasoning_effort")
        return str(value).strip() if isinstance(value, str) and str(value).strip() else None
    if agent_name == "claude":
        value = _claude_settings().get("effortLevel")
        return str(value).strip() if isinstance(value, str) and str(value).strip() else None
    if agent_name == "gemini":
        return _nested_lookup(
            _gemini_settings(),
            ("effort", "effortLevel", "reasoningEffort", "reasoning_effort"),
        )
    return None


def _codex_version_prefix(cmd: list[str]) -> tuple[str, ...]:
    if cmd:
        return (cmd[0],)
    return ("codex",)


def _claude_version_prefix(cmd: list[str]) -> tuple[str, ...]:
    if not cmd:
        return ("claude",)
    if cmd[0] == "npx" and len(cmd) > 1 and not str(cmd[1]).startswith("-"):
        return (cmd[0], cmd[1])
    return (cmd[0],)


def _gemini_version_prefix(cmd: list[str]) -> tuple[str, ...]:
    if cmd:
        return (cmd[0],)
    return ("gemini",)


def _probe_version(prefix: tuple[str, ...]) -> str | None:
    try:
        proc = subprocess.run(
            [*prefix, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except BaseException:
        return None
    combined = f"{proc.stdout or ''}\n{proc.stderr or ''}".strip()
    return _extract_semverish(combined)


@lru_cache(maxsize=1)
def codex_cli_version(prefix: tuple[str, ...] = ("codex",)) -> str | None:
    return _probe_version(prefix)


@lru_cache(maxsize=1)
def gemini_cli_version(prefix: tuple[str, ...] = ("gemini",)) -> str | None:
    return _probe_version(prefix)


@lru_cache(maxsize=1)
def claude_cli_version(prefix: tuple[str, ...] = ("claude",)) -> str | None:
    return _probe_version(prefix)


def _resolve_cli_version(agent_name: str, plan: InvocationPlan | None = None) -> str | None:
    if agent_name == "codex":
        prefix = _codex_version_prefix(plan.cmd) if plan is not None else ("codex",)
        return codex_cli_version(prefix)
    if agent_name == "gemini":
        prefix = _gemini_version_prefix(plan.cmd) if plan is not None else ("gemini",)
        return gemini_cli_version(prefix)
    if agent_name == "claude":
        prefix = _claude_version_prefix(plan.cmd) if plan is not None else ("claude",)
        return claude_cli_version(prefix)
    return None


def resolve_dispatch_start_telemetry(
    *,
    agent_name: str,
    requested_model: str | None,
    requested_effort: str | None,
) -> InvocationTelemetry:
    """Best-effort telemetry for task-state initialization before spawn."""
    model = _resolve_model_from_defaults(agent_name, requested_model)
    if not model:
        _warn_unknown("model", agent_name, "no explicit override or readable default")
        model = _UNKNOWN

    effort = _resolve_effort_from_defaults(agent_name, requested_effort)
    if not effort:
        _warn_unknown("effort", agent_name, "no explicit override or readable default")
        effort = _UNKNOWN

    cli_version = _resolve_cli_version(agent_name)
    if not cli_version:
        _warn_unknown("cli_version", agent_name, "version probe failed")
        cli_version = _UNKNOWN

    return InvocationTelemetry(model=model, effort=effort, cli_version=cli_version)


def resolve_invocation_telemetry(
    *,
    agent_name: str,
    plan: InvocationPlan,
    requested_model: str | None,
    requested_effort: str | None,
) -> InvocationTelemetry:
    """Resolve telemetry from the concrete adapter invocation plan."""
    model = _resolve_model_from_plan(agent_name, plan) or _resolve_model_from_defaults(
        agent_name,
        requested_model,
    )
    if not model:
        _warn_unknown("model", agent_name, "invocation plan had no model flag")
        model = _UNKNOWN

    effort = _resolve_effort_from_plan(agent_name, plan) or _resolve_effort_from_defaults(
        agent_name,
        requested_effort,
    )
    if not effort:
        _warn_unknown("effort", agent_name, "invocation plan had no effort flag")
        effort = _UNKNOWN

    cli_version = _resolve_cli_version(agent_name, plan)
    if not cli_version:
        _warn_unknown("cli_version", agent_name, "version probe failed")
        cli_version = _UNKNOWN

    return InvocationTelemetry(model=model, effort=effort, cli_version=cli_version)


def _reset_version_cache_for_tests() -> None:
    """Clear cached CLI versions. Tests only."""
    codex_cli_version.cache_clear()
    gemini_cli_version.cache_clear()
    claude_cli_version.cache_clear()
