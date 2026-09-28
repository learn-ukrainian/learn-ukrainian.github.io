#!/usr/bin/env python3
"""PreToolUse guard — auto-heals core.bare before git operations (#2842).

Reads the Claude Code hook payload on stdin (JSON with `tool_name` +
`tool_input.command`). If the command invokes `git`, it checks core.bare
and resets it to false if it has drifted to true. This prevents mid-session
git breakages from bubbling up to the agents.

Always exits 0 to allow the actual tool invocation to proceed.
"""
from __future__ import annotations

import json
import shlex
import subprocess
import sys
from contextlib import suppress
from pathlib import Path


def _read_payload() -> dict:
    try:
        return json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return {}


def _bash_command(payload: dict) -> str:
    return ((payload.get("tool_input") or {}).get("command") or "").strip()


def _is_git_command(command: str) -> bool:
    """True if `git` is invoked as the primary command or in a sub-segment."""
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        return False

    return "git" in tokens


def _project_dir() -> Path | None:
    here = Path(__file__).resolve()
    for candidate in (here.parent, *here.parents):
        if (candidate / "scripts" / "common" / "repo_root.py").is_file():
            return candidate
    return None


def main() -> int:
    payload = _read_payload()
    command = _bash_command(payload)

    if not command or not _is_git_command(command):
        return 0

    project_dir = _project_dir()
    if project_dir is None:
        return 0

    script = project_dir / "scripts" / "audit" / "check_core_bare.py"
    try:
        if str(project_dir) not in sys.path:
            sys.path.insert(0, str(project_dir))
        from scripts.common.repo_root import project_interpreter

        python_bin = project_interpreter()
    except Exception:
        return 0

    if script.exists() and python_bin.is_file():
        with suppress(OSError):
            subprocess.run(
                [str(python_bin), str(script), "--repo", str(project_dir), "--fix", "-q"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())
