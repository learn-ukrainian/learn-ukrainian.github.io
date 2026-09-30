"""A git worktree and tool_config a Kimi adapter test uses to pass the coding-only gate."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from scripts.agent_runtime.kimi_admission import OWNED_PATHS_KEY

OWNED_FILE = "site/src/components/Widget.tsx"


def admitted_tool_config(worktree: Path, tool_config: dict | None = None) -> dict:
    """Make ``worktree`` a committed repo owning one Cyrillic-free UI file; return ``tool_config`` declaring it."""
    if not (worktree / ".git").exists():
        env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        env.update(
            GIT_AUTHOR_NAME="t",
            GIT_AUTHOR_EMAIL="t@example.com",
            GIT_COMMITTER_NAME="t",
            GIT_COMMITTER_EMAIL="t@example.com",
        )
        target = worktree / OWNED_FILE
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("export const Widget = () => null;\n", encoding="utf-8")
        for args in (["init", "-q"], ["add", OWNED_FILE], ["commit", "-q", "-m", "base"]):
            subprocess.run(["git", *args], cwd=worktree, env=env, check=True, capture_output=True, timeout=30)
    return {**(tool_config or {}), OWNED_PATHS_KEY: [OWNED_FILE]}
