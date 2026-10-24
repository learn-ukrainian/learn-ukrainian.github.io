"""AI Agent Bridge - Multi-agent communication bridge via MCP Message Broker.

This package provides bidirectional communication between AI agents (Gemini, Claude)
using a shared SQLite database.

Configuration:
- ``AB_REPO_ROOT``: defaults to the package's containing repo root.
- ``AB_DB_PATH``: defaults to ``{REPO_ROOT}/.mcp/servers/message-broker/messages.db``.
- ``AB_PID_DIR``: defaults to ``{REPO_ROOT}/.mcp/servers/message-broker/pids``.
- ``AB_CONTEXT_DIR``: defaults to ``{REPO_ROOT}/docs/agent-channels``.
- ``AB_WAKE_DIR``: defaults to ``{REPO_ROOT}/.agent/wake``.
- ``AB_MONITOR_URL``: defaults to empty string (Monitor API disabled).
- ``AB_GEMINI_MODEL``: defaults to the AGY seat pin from the ACP participant registry.
- ``AB_PIPELINE_ENV_KEY``: defaults to ``LEARN_UKRAINIAN_PIPELINE``.

All public functions are re-exported here for backward compatibility.
"""

import sys
from importlib import import_module
from pathlib import Path

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

# Re-export everything that was previously importable from ai_agent_bridge
from ._broker import (
    _git_status_snapshot,
    _is_task_locked,
    _remove_pid_file,
    _validate_file_writes,
    _write_pid_file,
    bridge_status,
    broker_cleanup,
)
from ._config import (
    _MODEL_CACHE,
    _MODEL_CACHE_TTL,
    _PARENT_ENV,
    AGY_CLI,
    CLAUDE_CMD,
    CODEX_CLI,
    DB_PATH,
    GEMINI_CLI,
    GH_CHAR_LIMIT,
    PID_DIR,
    REPO_ROOT,
    default_gemini_model,
)
from ._db import get_db, get_session, init_db, set_session
from ._github import (
    _format_review_chunk,
    _gh_comment,
    _post_review_to_github,
    _split_content,
)
from ._messaging import (
    _extract_issue_number,
    acknowledge,
    acknowledge_all,
    check_inbox,
    detect_sender,
    get_conversation,
    read_message,
    send_message,
    send_to_codex,
    send_to_gemini,
)
from ._prompts import build_claude_prompt, build_codex_prompt, build_gemini_prompt

# Metadata-only inbox callers need the canonical aliases, not execution code.
_EXECUTION_EXPORTS = {
    "ask_claude": "_claude",
    "process_for_claude": "_claude",
    "interactive_mode": "_cli",
    "main": "_cli",
    "process_all_claude": "_cli",
    "process_all_gemini": "_cli",
    "ask_codex": "_codex",
    "process_all_codex": "_codex",
    "process_for_codex": "_codex",
    "ask_gemini": "_gemini",
    "process_and_respond": "_gemini",
    "ask_grok_build": "_grok_build",
    "process_for_grok_build": "_grok_build",
    "_detect_model_error": "_model",
    "check_model": "_model",
}

__all__ = [
    "AGY_CLI",
    "CLAUDE_CMD",
    "CODEX_CLI",
    "DB_PATH",
    "GEMINI_CLI",
    "GEMINI_DEFAULT_MODEL",
    "GH_CHAR_LIMIT",
    "PID_DIR",
    "REPO_ROOT",
    "_MODEL_CACHE",
    "_MODEL_CACHE_TTL",
    "_PARENT_ENV",
    "_detect_model_error",
    "_extract_issue_number",
    "_format_review_chunk",
    "_gh_comment",
    "_git_status_snapshot",
    "_is_task_locked",
    "_post_review_to_github",
    "_remove_pid_file",
    "_split_content",
    "_validate_file_writes",
    "_write_pid_file",
    "acknowledge",
    "acknowledge_all",
    "ask_claude",
    "ask_codex",
    "ask_gemini",
    "ask_grok_build",
    "bridge_status",
    "broker_cleanup",
    "build_claude_prompt",
    "build_codex_prompt",
    "build_gemini_prompt",
    "check_inbox",
    "check_model",
    "default_gemini_model",
    "detect_sender",
    "get_conversation",
    "get_db",
    "get_session",
    "init_db",
    "interactive_mode",
    "main",
    "process_all_claude",
    "process_all_codex",
    "process_all_gemini",
    "process_and_respond",
    "process_for_claude",
    "process_for_codex",
    "process_for_grok_build",
    "read_message",
    "send_message",
    "send_to_codex",
    "send_to_gemini",
    "set_session",
]


def __getattr__(name: str):
    if name == "GEMINI_DEFAULT_MODEL":
        from ._config import default_gemini_model

        return default_gemini_model()
    if module := _EXECUTION_EXPORTS.get(name):
        value = getattr(import_module(f".{module}", __name__), name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
