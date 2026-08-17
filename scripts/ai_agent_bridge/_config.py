"""Shared constants and environment configuration for the AI Agent Bridge."""

import os
import shutil
import sys
from pathlib import Path

from ._env import build_agent_env

# Bootstrap import path for scripts.* from any cwd
_local_repo_root = Path(__file__).resolve().parents[2]
if str(_local_repo_root) not in sys.path:
    sys.path.insert(0, str(_local_repo_root))

from scripts.common.repo_root import resolve_repo_root

# Repo root for path resolution
REPO_ROOT = Path(os.environ.get("AB_REPO_ROOT", str(Path(__file__).parent.parent.parent)))

PRIMARY_REPO_ROOT = resolve_repo_root(Path(__file__), 2)

# Database path (same as MCP server uses)
DB_PATH = Path(
    os.environ.get(
        "AB_DB_PATH",
        str(PRIMARY_REPO_ROOT / ".mcp" / "servers" / "message-broker" / "messages.db"),
    )
)
PID_DIR = Path(
    os.environ.get(
        "AB_PID_DIR",
        str(PRIMARY_REPO_ROOT / ".mcp" / "servers" / "message-broker" / "pids"),
    )
)

# Resolve CLI paths at import time (before detached children lose PATH)
# Prefer the local native `claude` binary (#4875: the npm package became a
# native-installer shim — `npx @latest` exits rc=1 with "Error: claude native
# binary not installed" and empty stdout, killing every bridge Claude call at
# spawn). npx stays as the fallback for machines without a native install.
# Second probe: the default native install target ~/.local/bin/claude covers
# callers whose PATH omits it (mirrors start-claude.sh:33; review-4881).
_CLAUDE_BIN = shutil.which("claude") or (
    str(Path.home() / ".local/bin/claude") if (Path.home() / ".local/bin/claude").is_file() else None
)
CLAUDE_CMD = [_CLAUDE_BIN] if _CLAUDE_BIN else ["npx", "@anthropic-ai/claude-code@latest"]
AGY_CLI = shutil.which("agy") or str(Path.home() / ".local/bin/agy")
GEMINI_CLI = shutil.which("gemini") or "gemini"
CODEX_CLI = shutil.which("codex") or "codex"


def default_gemini_model() -> str:
    """Resolve the default Gemini model from environment or ACP registry pin (#6959).

    Resolution chain:
    1. ``AB_GEMINI_MODEL`` environment override.
    2. AGY seat pin from the live ACP participant registry (``agent_runtime.adapters.acpx.ACPX_SUPPORTED_PARTICIPANTS``).

    Raises RuntimeError if neither is configured (fails loudly rather than pinning
    a stale literal fallback).
    """
    env_override = os.environ.get("AB_GEMINI_MODEL")
    if env_override:
        return env_override

    try:
        from ._acp_compat import registered_participant_model

        pin = registered_participant_model("agy")
        if pin:
            return pin
    except Exception:
        pass

    raise RuntimeError(
        "No default Gemini model configured: 'AB_GEMINI_MODEL' is unset and "
        "the ACP participant registry ('agy') has no model pin."
    )


def __getattr__(name: str):
    if name == "GEMINI_DEFAULT_MODEL":
        return default_gemini_model()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# Snapshot environment for passing to detached children. Use a narrow env so
# background bridge processes do not inherit shell tokens that agents can print.
# Set GEMINI_SESSION so .bashrc disables hostile aliases (eza, bat, zoxide)
_PARENT_ENV = build_agent_env(os.environ, repo_root=REPO_ROOT)
_PARENT_ENV["GEMINI_SESSION"] = "1"
_PIPELINE_ENV_KEY = os.environ.get("AB_PIPELINE_ENV_KEY", "LEARN_UKRAINIAN_PIPELINE")
_PARENT_ENV[_PIPELINE_ENV_KEY] = "1"  # Suppress inbox hooks during pipeline runs

# Model availability cache: {model: (available: bool, timestamp: float)}
# Avoids burning API quota on repeated checks within the same session.
_MODEL_CACHE: dict[str, tuple[bool, float]] = {}
_MODEL_CACHE_TTL = 3600  # 1 hour — re-check after this

# GitHub comment/body limit is 65,536 chars. Use 64K with 1.5K safety margin for headers.
GH_CHAR_LIMIT = 64000
