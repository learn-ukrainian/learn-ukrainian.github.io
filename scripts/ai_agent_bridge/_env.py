"""Environment helpers for agent subprocesses.

Agent CLIs execute shell commands. Anything inherited in their environment can
be printed by an agent command and then copied into comments or logs, so bridge
children should get a narrow environment by default.
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from pathlib import Path

_SAFE_ENV_KEYS = {
    "HOME",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "LOGNAME",
    "PATH",
    "PWD",
    "SHELL",
    "SHLVL",
    "SSH_AUTH_SOCK",
    "TERM",
    "TMPDIR",
    "USER",
    "XDG_CACHE_HOME",
    "XDG_CONFIG_HOME",
    "XDG_DATA_HOME",
}

_SAFE_ENV_PREFIXES = (
    "AB_",
    "CODEX_",
    "CLAUDE_",
    "GEMINI_",
    "GROK_",
    "KIMI_",
    "LEARN_UKRAINIAN_",
    "PYTHON",
)

_SECRET_KEY_RE = re.compile(
    r"(?:^|_)(?:TOKEN|SECRET|PASSWORD|PASS|API_?KEY|ACCESS_?KEY|PRIVATE_?KEY|CREDENTIALS?)(?:_|$)"
)

_BLOCKED_KEYS = {
    "ANTHROPIC_API_KEY",
    "CODEX_API_KEY",
    "GEMINI_API_KEY",
    "GH_TOKEN",
    "GITHUB_PERSONAL_ACCESS_TOKEN",
    "GITHUB_TOKEN",
    "GOOGLE_API_KEY",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "GOOGLE_GENERATIVE_AI_API_KEY",
    "OPENAI_API_KEY",
}


def is_secret_env_key(key: str) -> bool:
    """Return True for env var names that usually carry secrets."""
    upper = key.upper()
    return upper in _BLOCKED_KEYS or bool(_SECRET_KEY_RE.search(upper))


def build_agent_env(
    source: Mapping[str, str] | None = None,
    *,
    repo_root: Path | None = None,
) -> dict[str, str]:
    """Build a narrow env for agent/bridge subprocesses.

    This keeps ordinary runtime variables and project-specific flags while
    dropping token-shaped variables. Provider API keys should be injected only
    by the adapter invocation that specifically requires them.
    """
    raw = dict(os.environ if source is None else source)
    env: dict[str, str] = {}

    for key, value in raw.items():
        if is_secret_env_key(key):
            continue
        if key in _SAFE_ENV_KEYS or key.startswith(_SAFE_ENV_PREFIXES):
            env[key] = value

    if repo_root is not None:
        venv_bin = str(repo_root / ".venv" / "bin")
        env["PATH"] = f"{venv_bin}:{env.get('PATH', raw.get('PATH', ''))}"

    env.setdefault("PATH", raw.get("PATH", ""))
    env.setdefault("HOME", raw.get("HOME", str(Path.home())))
    env.setdefault("SHELL", raw.get("SHELL", "/bin/bash"))
    env["PYTHONUNBUFFERED"] = "1"
    return env
