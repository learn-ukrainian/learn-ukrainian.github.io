"""Construct a provider environment without inherited infrastructure credentials."""

import os
from pathlib import Path

from scripts.dispatcher.types import TaskSpec

_CONTEXT = ("PATH", "HOME", "LANG", "TERM", "TMPDIR")
_AUTH = {
    "codex": ("OPENAI_API_KEY", "CODEX_API_KEY", "CODEX_HOME"),
    "claude": ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_API_KEY", "CLAUDE_CONFIG_DIR"),
    "cursor": ("CURSOR_API_KEY",),
    "agy": ("AGY_API_KEY", "AGY_TOKEN", "GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GENERATIVE_AI_API_KEY"),
    "muse": ("MUSE_API_KEY", "MUSE_TOKEN"),
    "opencode": ("DEEPSEEK_API_KEY",),
    "hermes": ("OPENROUTER_API_KEY",),
}


def child_env(spec: TaskSpec) -> dict[str, str]:
    names = _CONTEXT + _AUTH[spec.agent]
    if spec.provider == "openrouter" and spec.agent == "opencode":
        names = (*_CONTEXT, "OPENROUTER_API_KEY")
    env = {name: os.environ[name] for name in names if name in os.environ}
    if spec.agent == "cursor" and not env.get("CURSOR_API_KEY", "").strip():
        from scripts.agent_runtime.adapters.cursor import _load_cursor_api_key_from_env_file

        env.pop("CURSOR_API_KEY", None)
        file_key = _load_cursor_api_key_from_env_file()
        if file_key:
            env["CURSOR_API_KEY"] = file_key
    if spec.agent == "claude" and spec.claude_account:
        suffix = "" if spec.claude_account == "a" else "-b"
        env["CLAUDE_CONFIG_DIR"] = str(Path(env.get("HOME", str(Path.home()))) / f".claude{suffix}")
    env["LU_DISPATCH_TASK_ID"] = spec.task_id
    env["LU_DISPATCH_MODE"] = spec.mode
    return env
