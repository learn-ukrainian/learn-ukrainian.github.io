#!/usr/bin/env python3
"""Put the shared gh shim first for Bash and Cursor Shell tools; routing only."""

from __future__ import annotations

import contextlib
import json
import os
import shlex
import sys
from collections.abc import Iterator
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))


def _shell_words(command: str) -> list[str]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";|&()\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    lexer.commenters = ""
    return list(lexer)


def _redirect_words(command: str) -> Iterator[str]:
    from shell_redirects import _split_scopes
    from shell_shlex import preprocess_shell_command

    pending = False
    # Scan the complete command so quotes keep their state across newlines.
    for kind, raw in _split_scopes(preprocess_shell_command(command)):
        if kind == "text":
            words = _shell_words(raw)
            if pending and words:
                if words[0] == "\n":
                    raise ValueError("missing redirect operand")
                words.pop(0)
                pending = False
            yield from words
        elif pending:
            raise ValueError("missing redirect operand")
        elif kind == "redirect":
            pending = True
        else:
            yield raw
    if pending:
        raise ValueError("missing redirect operand")


def invokes_gh(command: str) -> bool:
    """Recognize command positions, common wrappers and nested shell -c forms."""
    try:
        # Keep the original whole-command lexer as the primary detection path.
        for lexer in (_shell_words(command), _redirect_words(command)):
            expecting_command = True
            shell = False
            shell_script = False
            wrapper = False
            for word in lexer:
                if shell_script:
                    if invokes_gh(word):
                        return True
                    shell_script = False
                    expecting_command = False
                elif word and all(char in ";|&()\n" for char in word):
                    expecting_command = True
                    shell = False
                    wrapper = False
                elif shell and word.startswith("-") and not word.startswith("--") and "c" in word[1:]:
                    shell_script = True
                elif expecting_command:
                    if "=" in word or word in {
                        "env",
                        "command",
                        "exec",
                        "sudo",
                        "time",
                        "timeout",
                        "xargs",
                        "if",
                        "then",
                        "elif",
                        "while",
                        "until",
                        "do",
                        "!",
                    }:
                        wrapper = word in {"time", "timeout", "xargs", "env", "sudo"} or wrapper
                        continue
                    if Path(word).name == "gh":
                        return True
                    if Path(word).name in {"bash", "sh", "zsh", "dash"}:
                        shell = True
                        expecting_command = False
                    elif wrapper or word.startswith("-") or word.replace(".", "").isdigit():
                        continue
                    else:
                        expecting_command = False
    except ValueError:
        return True
    return False


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        from tool_names import is_shell_tool

        if not is_shell_tool(payload.get("tool_name")):
            return 0
        root = next(parent for parent in Path(__file__).resolve().parents if (parent / "scripts/opsec").is_dir())
        sys.path.insert(0, str(root))
        from scripts.opsec.prepublish import PublishBlocked, real_gh

        command = payload.get("tool_input", {}).get("command", "")
        if not invokes_gh(command):
            return 0
        shim = str(root / "scripts/agent_runtime/shims")
        if os.environ.get("PATH", "").split(os.pathsep)[0] == shim:
            return 0
        prefix = "export PATH=" + shlex.quote(str(root / "scripts/agent_runtime/shims")) + ':"$PATH"; '
        with contextlib.suppress(PublishBlocked):
            prefix += "export AGENT_REAL_GH=" + shlex.quote(real_gh(os.environ)) + "; "
        updated = dict(payload.get("tool_input", {}))
        updated["command"] = prefix + command
        result = {"hookSpecificOutput": {"hookEventName": "PreToolUse", "updatedInput": updated}}
        print(json.dumps(result))
        return 0
    except Exception:
        print("OPSEC: Bash publishing shim could not be installed.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
