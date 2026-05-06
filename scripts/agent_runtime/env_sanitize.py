"""Sanitize environment variables for spawned agent CLI processes.

Agent CLIs can run shell commands and inspect ``os.environ`` directly. The
runtime should therefore pass only ordinary process context plus the credential
for the provider being invoked, not the full orchestrator environment.
"""
from __future__ import annotations

import os
import re
from collections.abc import Mapping

_SENSITIVE_NAME_RE = re.compile(
    r"TOKEN|SECRET|PASSWORD|PASSWD|PRIVATE|CREDENTIALS?|API_?KEY|"
    r"ACCESS_?KEY|AUTH|COOKIE",
    re.IGNORECASE,
)

_SENSITIVE_VALUE_RE = re.compile(
    r"(?:"
    r"github_pat_[A-Za-z0-9_]+|"
    r"gh[pousr]_[A-Za-z0-9_]+|"
    r"sk-[A-Za-z0-9_-]+|"
    r"xox[baprs]-[A-Za-z0-9-]+|"
    r"hf_[A-Za-z0-9_]+|"
    r"npm_[A-Za-z0-9_]+|"
    r"AKIA[A-Z0-9]{12,}|"
    r"AIza[A-Za-z0-9_-]+"
    r")"
)

_SAFE_NAME_ALLOWLIST = {
    "AGENT_ALLOW_MERGE",
    "AGENT_NO_MERGE",
    "HOME",
    "LANG",
    "PATH",
    "TMPDIR",
}

_SAFE_NAME_PREFIXES = (
    "AB_",
    "LC_",
    "LU_",
)

_PROVIDER_SECRET_ALLOWLIST = {
    "gemini": {
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "GOOGLE_GENERATIVE_AI_API_KEY",
    },
    "claude": {
        "ANTHROPIC_AUTH_TOKEN",
        "ANTHROPIC_API_KEY",
        "CLAUDE_API_KEY",
        "CLAUDE_CODE_OAUTH_TOKEN",
    },
    "codex": {
        "CODEX_API_KEY",
        "OPENAI_API_KEY",
    },
    "bridge": set(),
}

_PROVIDER_SAFE_NAME_ALLOWLIST = {
    "claude": {
        "CLAUDE_CONFIG_DIR",
    },
    "gemini": {
        "GEMINI_AUTH_MODE",
    },
}


def _normalized_provider(provider: str) -> str:
    """Map runtime provider names to sanitizer policy keys."""
    return provider.removesuffix("-tools").lower()


def _is_safe_name(name: str) -> bool:
    upper = name.upper()
    return upper in _SAFE_NAME_ALLOWLIST or upper.startswith(_SAFE_NAME_PREFIXES)


def _is_provider_secret(name: str, provider: str) -> bool:
    allowed = _PROVIDER_SECRET_ALLOWLIST.get(_normalized_provider(provider), set())
    return name.upper() in allowed


def _is_provider_safe_name(name: str, provider: str) -> bool:
    allowed = _PROVIDER_SAFE_NAME_ALLOWLIST.get(_normalized_provider(provider), set())
    return name.upper() in allowed


def _looks_sensitive_name(name: str) -> bool:
    return bool(_SENSITIVE_NAME_RE.search(name))


def _looks_sensitive_value(value: str) -> bool:
    return bool(_SENSITIVE_VALUE_RE.search(value))


def build_agent_env(
    *,
    provider: str,
    overrides: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Return a scrubbed env for a spawned agent CLI.

    ``overrides`` are applied to the parent environment before sanitization so
    adapter-supplied values are subject to the same policy as inherited values.
    The runner applies explicit ``InvocationPlan.env_unsets`` after this call.
    """
    raw = dict(os.environ)
    raw.update(overrides or {})

    env: dict[str, str] = {}
    for name, value in raw.items():
        if _is_provider_secret(name, provider):
            env[name] = value
            continue

        if _looks_sensitive_value(value):
            continue
        if _is_provider_safe_name(name, provider):
            env[name] = value
            continue
        if _looks_sensitive_name(name):
            continue
        if _is_safe_name(name):
            env[name] = value

    if "PATH" not in env and "PATH" in raw and not _looks_sensitive_value(raw["PATH"]):
        env["PATH"] = raw["PATH"]
    if "HOME" not in env and "HOME" in raw and not _looks_sensitive_value(raw["HOME"]):
        env["HOME"] = raw["HOME"]

    return env
