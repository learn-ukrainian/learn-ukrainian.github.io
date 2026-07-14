"""Sanitize environment variables for spawned agent CLI processes.

Agent CLIs can run shell commands and inspect ``os.environ`` directly. The
runtime should therefore pass only ordinary process context plus the credential
for the provider being invoked, not the full orchestrator environment.
"""

from __future__ import annotations

import os
import re
import shutil
import tempfile
from collections.abc import Mapping
from pathlib import Path

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
    "LOGNAME",
    "PATH",
    "TMPDIR",
    "USER",
}

_SAFE_NAME_PREFIXES = (
    "AB_",
    "LC_",
    "LU_",
)

# These are process-control paths, not credentials. A task id such as
# ``task-4956`` contains the substring ``sk-`` and otherwise looks like an
# OpenAI key to the generic value redactor, so keep the tmp lease controls
# before the value-pattern filter. Their names remain narrowly allowlisted.
_SAFE_VALUE_NAME_ALLOWLIST = {
    "TMPDIR",
    "LU_RUNTIME_TMP_ROOT",
}

_PROVIDER_SECRET_ALLOWLIST = {
    "gemini": {
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "GOOGLE_GENERATIVE_AI_API_KEY",
    },
    "claude": {
        "ANTHROPIC_API_KEY",
        "CLAUDE_API_KEY",
        "GH_TOKEN",
    },
    "codex": {
        "CODEX_API_KEY",
        "GH_TOKEN",
        "OPENAI_API_KEY",
    },
    "bridge": {
        "GH_TOKEN",
    },
}

_PROVIDER_SAFE_NAME_ALLOWLIST = {
    "gemini": {
        "GEMINI_AUTH_MODE",
    },
    # CODEX_HOME must reach the codex subprocess so the V7 writer's
    # scoped config (materialized by
    # `linear_pipeline._ensure_codex_writer_home`) actually takes
    # effect. Without this allowlist entry the sanitizer dropped the
    # `env_overrides["CODEX_HOME"]` set by the codex adapter, the
    # subprocess fell back to `~/.codex/config.toml`, and writers
    # discovered the user's globally-registered MCP servers (e.g.
    # `mcp__node_repl__js`) — see writer-isolation #2228 / #2230 +
    # the 2026-05-22 ab ask-codex `codex-node-repl-leak-2026-05-22`
    # diagnosis.
    "codex": {
        "CODEX_HOME",
    },
    "deepseek": {
        "HERMES_HOME",
    },
    "grok": {
        "HERMES_HOME",
    },
    "qwen": {
        "HERMES_HOME",
    },
}


def _normalized_provider(provider: str) -> str:
    """Map runtime provider names to sanitizer policy keys."""
    return provider.removesuffix("-tools").lower()


def _is_safe_name(name: str) -> bool:
    upper = name.upper()
    return upper in _SAFE_NAME_ALLOWLIST or upper.startswith(_SAFE_NAME_PREFIXES)


def _is_safe_value_name(name: str) -> bool:
    return name.upper() in _SAFE_VALUE_NAME_ALLOWLIST


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


def _isolated_git_env(home: str | None) -> dict[str, str]:
    """Git ``--global`` config isolation for spawned agent CLIs (issue #2842).

    A stray ``git config`` write from an agent subprocess can brick git for the
    main checkout AND every linked worktree at once (e.g. ``core.bare true`` on
    the shared config). Point the subprocess's **global** config at a throwaway
    **copy** of the real one, so commit identity (``user.name`` / ``user.email``)
    and other global settings stay readable, but ``git config --global`` writes
    land in the copy instead of the developer's ``~/.gitconfig``.

    Deliberately NOT touched:

    - System config is left intact (no ``GIT_CONFIG_NOSYSTEM``): on this host it
      carries ``credential.helper=osxkeychain`` with no global fallback, so
      disabling it would break agent push/fetch auth — a worse failure than the
      one we're guarding against.
    - Repo-local shared config cannot be guarded by env vars at all; that vector
      is backstopped by the health-endpoint canary
      (``scripts/audit/check_core_bare.py``), which auto-detects + resets drift.

    Never raises: isolation failure must not block spawning an agent.
    """
    try:
        sandbox_dir = Path(tempfile.gettempdir()) / "lu-agent-runtime-git"
        sandbox_dir.mkdir(parents=True, exist_ok=True)
        sandbox_global = sandbox_dir / "agent.gitconfig"
        real_global = Path(
            os.environ.get("GIT_CONFIG_GLOBAL")
            or ((Path(home) if home else Path.home()) / ".gitconfig")
        )
        if real_global.is_file():
            shutil.copyfile(real_global, sandbox_global)
        elif not sandbox_global.exists():
            sandbox_global.write_text("", encoding="utf-8")
        return {"GIT_CONFIG_GLOBAL": str(sandbox_global)}
    except OSError:
        # Copy failed; leave GIT_CONFIG_GLOBAL unset so the agent falls back to
        # the real ~/.gitconfig rather than losing identity entirely.
        return {}


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

        if _is_safe_value_name(name):
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

    # Git-config isolation (#2842) — applied last so it always wins; agents
    # cannot persist a repo-bricking core.bare write into system/global config.
    env.update(_isolated_git_env(env.get("HOME") or raw.get("HOME")))

    return env
