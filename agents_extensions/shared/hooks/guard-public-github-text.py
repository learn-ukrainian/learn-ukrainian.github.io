#!/usr/bin/env python3
"""Put the shared gh shim first for Claude Bash tools; literal checks warn only."""

from __future__ import annotations

import contextlib
import json
import os
import shlex
import sys
from pathlib import Path


def invokes_gh(command: str) -> bool:
    """Recognize gh at command positions, leaving ordinary prefix rules intact."""
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";|&()")
        lexer.whitespace_split = True
        expecting_command = True
        for word in lexer:
            if word and all(char in ";|&()" for char in word):
                expecting_command = True
            elif expecting_command:
                if "=" in word or word in {"env", "command", "exec", "sudo"}:
                    continue
                if Path(word).name == "gh":
                    return True
                expecting_command = False
    except ValueError:
        pass
    return False


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if payload.get("tool_name") != "Bash":
            return 0
        root = next(parent for parent in Path(__file__).resolve().parents if (parent / "scripts/opsec").is_dir())
        sys.path.insert(0, str(root))
        from scripts.opsec.prepublish import PublishBlocked, check_texts, real_gh

        command = payload.get("tool_input", {}).get("command", "")
        if not invokes_gh(command):
            return 0
        # Early warning only: the final argv/files/stdin are enforced by the shim.
        warning = ""
        if "gh" in command:
            try:
                words = shlex.split(command)
                literals = [
                    words[i + 1] for i, word in enumerate(words[:-1]) if word in {"--title", "--body", "--comment"}
                ]
                if literals:
                    check_texts("unknown", literals, environment={})
            except PublishBlocked as exc:
                warning = str(exc)
            except ValueError:
                pass
        prefix = "export PATH=" + shlex.quote(str(root / "scripts/agent_runtime/shims")) + ':"$PATH"; '
        with contextlib.suppress(PublishBlocked):
            prefix += "export AGENT_REAL_GH=" + shlex.quote(real_gh(os.environ)) + "; "
        updated = dict(payload.get("tool_input", {}))
        updated["command"] = prefix + command
        result = {"hookSpecificOutput": {"hookEventName": "PreToolUse", "updatedInput": updated}}
        if warning:
            result["systemMessage"] = warning
        print(json.dumps(result))
        return 0
    except Exception:
        print("OPSEC: Bash publishing shim could not be installed.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
