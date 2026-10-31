"""Construct a provider environment without inherited infrastructure credentials."""

import os
import sys
from pathlib import Path

from scripts.agent_runtime.read_only_tmp import dispatch_lease
from scripts.common.task_store_paths import tasks_dir
from scripts.dispatcher.types import TaskSpec

# LU_SENSE_PROOF_DIR is a host path with no secret in the name; pack-verify reads the proofs inside it.
_CONTEXT = ("PATH", "HOME", "LANG", "TERM", "TMPDIR", "LU_SENSE_PROOF_DIR")
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


def claude_config_dir(account: str, home: str | None = None) -> str | None:
    """The login directory a Claude account runs in until ``admission.claude_launch`` binds the verified one.

    An API-key label's directory exists only in its private binding (C-2643), so the read-only policy
    check before launch examines that directory; an unbound one is ``None``, and admission refuses it.
    """
    from scripts.agent_runtime.attempt_boundary import (
        CLAUDE_API_KEY_ACCOUNT_LABELS,
        ClaudeAccountRefused,
        load_claude_account_binding,
    )

    if account in CLAUDE_API_KEY_ACCOUNT_LABELS:
        try:
            return str(load_claude_account_binding(account).config_dir)
        except ClaudeAccountRefused:
            return None
    suffix = "" if account == "a" else "-b"
    return str(Path(home or os.environ.get("HOME") or str(Path.home())) / f".claude{suffix}")


def child_env(spec: TaskSpec) -> dict[str, str]:
    source = os.environ
    if spec.agent == "codex":
        from scripts.agent_runtime.codex_accounts import codex_account_env

        source = codex_account_env(spec.codex_account, source)
    names = _CONTEXT + _AUTH[spec.agent]
    if spec.provider == "openrouter" and spec.agent == "opencode":
        names = (*_CONTEXT, "OPENROUTER_API_KEY")
    env = {name: source[name] for name in names if name in source}
    if spec.agent == "cursor" and not env.get("CURSOR_API_KEY", "").strip():
        from scripts.agent_runtime.adapters.cursor import _load_cursor_api_key_from_env_file

        env.pop("CURSOR_API_KEY", None)
        file_key = _load_cursor_api_key_from_env_file()
        if file_key:
            env["CURSOR_API_KEY"] = file_key
    if spec.agent == "claude" and spec.claude_account:
        config_dir = claude_config_dir(spec.claude_account, env.get("HOME"))
        if config_dir is None:
            env.pop("CLAUDE_CONFIG_DIR", None)
        else:
            env["CLAUDE_CONFIG_DIR"] = config_dir
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
    env.update(
        LEARN_UKRAINIAN_DISPATCH_TASK_ID=spec.task_id,
        LEARN_UKRAINIAN_DISPATCH_AGENT=spec.agent,
        LU_TASKS_DIR=str(tasks_dir().resolve()),
    )
    if spec.agent == "codex" and spec.mode == "read-only":
        # Its sandbox leaves no writable temp, so git, gh and pytest need this lease; the worker creates it.
        env["TMPDIR"] = str(dispatch_lease(spec.task_id))
    if spec.mode == "read-only":
        # Restrict explicit URLs too; a worktree or ref snapshot cannot observe an arbitrary remote push.
        env["GIT_ALLOW_PROTOCOL"] = "file"
    return env
