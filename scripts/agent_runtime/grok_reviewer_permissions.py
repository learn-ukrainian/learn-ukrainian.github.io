"""Fail-closed command boundary for native headless Grok reviewers.

Only these literal commands are pre-authorized. They disable Git's optional
writes, pager, filesystem monitor and executable diff/textconv drivers. File
inspection uses the native read/search tools; arbitrary code execution needs
a separate execution-capable task, not a review permission prompt.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

_GIT = "git --no-optional-locks --no-pager -c core.fsmonitor=false -c log.showSignature=false"
GROK_REVIEWER_READ_COMMANDS = (
    f"{_GIT} status --short",
    f"{_GIT} rev-parse HEAD",
    f"{_GIT} log -5 --oneline",
    f"{_GIT} diff --no-ext-diff --no-textconv",
    f"{_GIT} diff --no-ext-diff --no-textconv HEAD",
    f"{_GIT} diff --no-ext-diff --no-textconv origin/main...HEAD",
    f"{_GIT} diff --no-ext-diff --no-textconv --stat origin/main...HEAD",
    f"{_GIT} diff --no-ext-diff --no-textconv --check origin/main...HEAD",
    f"{_GIT} show --no-ext-diff --no-textconv HEAD",
    "pwd",
    "date -u",
)
REFUSAL_CODE = "READ_ONLY_REVIEW_COMMAND_DENIED"
GROK_REVIEWER_TOOLS = ("read_file", "list_dir", "grep", "run_terminal_command")


def reviewer_command_allowed(payload: object) -> bool:
    """Admit a literal read command, never a prefix, wrapper or shell script."""
    if not isinstance(payload, dict) or payload.get("hook_event_name") != "PreToolUse":
        return False
    if payload.get("toolName") not in ("Bash", "run_terminal_command", "run_terminal_cmd"):
        return False
    tool_input = payload.get("toolInput")
    if not isinstance(tool_input, dict):
        return False
    command = tool_input.get("command")
    return isinstance(command, str) and command in GROK_REVIEWER_READ_COMMANDS


def reviewer_tool_allowed(payload: object, review_root: Path) -> bool:
    """Allow only literal commands and tracked reads inside the review checkout."""
    if reviewer_command_allowed(payload):
        return True
    if not isinstance(payload, dict) or payload.get("hook_event_name") != "PreToolUse":
        return False
    tool = payload.get("toolName")
    inputs = payload.get("toolInput")
    if not isinstance(inputs, dict) or not isinstance(tool, str) or tool not in {"read_file", "list_dir", "grep"}:
        return False
    key = {"read_file": "target_file", "list_dir": "target_directory", "grep": "path"}[tool]
    value = inputs.get(key)
    if not isinstance(value, str) or not value or "\x00" in value:
        return False
    try:
        root = review_root.resolve(strict=True)
        target = (root / value).resolve(strict=True)
        relative = target.relative_to(root)
        if any(part in {".git", ".grok", ".ssh", ".aws", ".env"} for part in relative.parts):
            return False
        if tool == "list_dir":
            return target.is_dir()
        if not target.is_file():
            return False
        # Directory searches could include untracked credentials. Grep needs
        # a tracked file; resolving first also rejects symlink escapes.
        result = subprocess.run(
            ["git", "--literal-pathspecs", "--no-optional-locks", "-c", "core.fsmonitor=false", "ls-files",
             "--error-unmatch", "--", relative.as_posix()],
            cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5, check=False,
        )
        return result.returncode == 0
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Deny tools outside the native Grok read-only reviewer contract. "
            "Used as a PreToolUse hook; reads one Grok JSON event from stdin."
        ),
        epilog=(
            "Usage: <project-interpreter> -m scripts.agent_runtime.grok_reviewer_permissions --review-root <checkout> < event.json\n"
            "Outputs: path-free refusal on stderr; no files or network writes.\n"
            "Exit codes: 0 admitted, 2 denied or unreadable event.\n"
            "Related: adapters/grok_build.py; #9987."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--review-root", type=Path, required=True,
                        help="Parent-bound review checkout; tracked reads must remain inside it.")
    args = parser.parse_args()
    try:
        allowed = reviewer_tool_allowed(json.load(sys.stdin), args.review_root)
    except (ValueError, RecursionError, OSError):
        allowed = False
    if allowed:
        return 0
    print(
        f"{REFUSAL_CODE}: read tracked files inside the review checkout (grep needs a file path), "
        "or use the listed literal Git inspection commands. "
        "Continue the review and report unavailable execution evidence; do not use a wrapper.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
