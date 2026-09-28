#!/usr/bin/env python3
"""Translate a Grok PreToolUse event for the existing fleet guard scripts.

Grok sends camelCase tool fields and native tool names. The tracked guards
consume Claude-shaped fields. This bridge preserves the original payload and
adds the shape the guards require; an unreadable event or missing guard denies.
Reviewer sessions and write sessions both enter through this bridge.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

# Claude matchers auto-expand to some Grok ids (Bash → run_terminal_command,
# Write|Edit|MultiEdit → search_replace). Write sessions also name the
# model-facing ids that expansion does not cover. Unknown ids still deny.
_TOOL_NAMES = {
    "run_terminal_command": "Bash",
    "run_terminal_cmd": "Bash",
    "Bash": "Bash",
    "search_replace": "Edit",
    "hashline_edit": "Edit",
    "write": "Write",
    "Write": "Write",
    "Edit": "Edit",
    "MultiEdit": "MultiEdit",
}


def main() -> int:
    try:
        if len(sys.argv) != 2:
            raise ValueError("one fleet guard path required")
        guard = Path(sys.argv[1])
        if not guard.is_file():
            raise ValueError("fleet guard unavailable")
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict) or payload.get("hook_event_name") != "PreToolUse":
            raise ValueError("invalid PreToolUse event")
        tool_name = _TOOL_NAMES.get(payload.get("toolName"))
        tool_input = payload.get("toolInput")
        if tool_name is None or not isinstance(tool_input, dict):
            raise ValueError("unknown reviewer tool payload")
        if tool_name == "Bash" and not isinstance(tool_input.get("command"), str):
            raise ValueError("shell command unavailable")
        translated = dict(payload)
        translated["tool_name"] = tool_name
        translated["tool_input"] = dict(tool_input)
        translated["tool_input"].setdefault("cwd", payload.get("cwd"))
        result = subprocess.run([str(guard)], input=json.dumps(translated), text=True, check=False, timeout=10)
        return 0 if result.returncode == 0 else 2
    except (OSError, ValueError, TypeError, subprocess.TimeoutExpired) as exc:
        print(f"BLOCKED by grok reviewer hook bridge: {type(exc).__name__}.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
