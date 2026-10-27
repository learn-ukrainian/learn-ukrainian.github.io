"""Construct a provider environment without inherited infrastructure credentials."""

import os
import sys
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
_NPM_SHIMS = Path(__file__).resolve().parent / "npm_shims"


def npm_shim_dir() -> Path | None:
    """Share only the npm/npx protection, without importing the legacy runner."""
    runtime = Path(__file__).resolve().parents[1] / "agent_runtime"
    executables = [
        Path(sys.executable), *(_NPM_SHIMS / name for name in ("npm", "npx")),
        *(runtime / "shims" / name for name in ("npm", "npx")),
    ]
    guard = runtime / "npm_guard.py"
    if (all(os.access(path, os.X_OK) and path.is_file() for path in executables)
            and os.access(guard, os.R_OK) and guard.is_file()):
        return _NPM_SHIMS
    return None


def claude_config_dir(account: str, home: str | None = None) -> str:
    """The login directory a Claude account runs in until ``admission.claude_launch`` binds the verified one."""
    suffix = "" if account == "a" else "-b"
    return str(Path(home or os.environ.get("HOME") or str(Path.home())) / f".claude{suffix}")


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
    if spec.agent == "claude":
        env["CLAUDE_CONFIG_DIR"] = claude_config_dir(spec.claude_account or "a", env.get("HOME"))
    shims = npm_shim_dir()
    if shims is not None:
        original_path = os.pathsep.join(
            entry for entry in env.get("PATH", os.defpath).split(os.pathsep)
            if Path(entry).resolve() != shims
            and Path(entry).parts[-3:] != ("scripts", "dispatcher", "npm_shims")
            and Path(entry).resolve().parts[-3:] != ("scripts", "dispatcher", "npm_shims")
        )
        env.update(
            PATH=f"{shims}{os.pathsep}{original_path}", AGENT_ORIGINAL_PATH=original_path,
            AGENT_GIT_SHIM_PYTHON=sys.executable,
        )
    elif any((spec.worktree / name).is_symlink() for name in ("node_modules", "site/node_modules")):
        raise ValueError("npm/npx guard unavailable for shared node_modules links")
    return env
