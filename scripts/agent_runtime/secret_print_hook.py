#!/usr/bin/env python3
"""Normalize one native shell event and invoke the shared no-print guard.

This adapter analyses command text without executing it. It does not install
hooks or certify native activation. OpenCode callers must reject exit 2 from
this adapter in their tool.execute.before plugin. Arbitrary programs cannot be
analysed by the shared detector; this is defense-in-depth, not a sandbox.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GUARD_PATH = ROOT / "agents_extensions/shared/hooks/guard-secret-print.py"
HARNESSES = frozenset({"claude", "codex", "grok", "kimi", "cursor", "agy", "hermes", "opencode"})
DEFAULT_TIMEOUT = 5.0
MAX_STDIN_BYTES = 1_048_576
BLOCK_PREFIX = "BLOCKED by guard-secret-print (#M-5): "


class HookParser(argparse.ArgumentParser):
    """Do not echo potentially sensitive arguments on parse failure."""

    def error(self, message: str) -> None:
        raise ValueError("invalid hook options")


def extract_command(harness: str, event: object) -> str | None:
    """Extract the selected dialect; malformed or absent commands deny."""
    if harness not in HARNESSES or not isinstance(event, dict):
        raise ValueError("invalid native hook event")
    if harness == "agy" and "toolCall" in event:
        call = event["toolCall"]
        if not isinstance(call, dict) or not isinstance(call.get("name"), str) or not call["name"]:
            raise ValueError("tool identity unavailable")
        if call["name"] != "run_command":
            return None  # Unrelated events allow; registration matches run_command only.
        args = call.get("args")
        command = args.get("CommandLine") if isinstance(args, dict) else None
    elif harness == "cursor":
        command = event.get("command")
    else:
        tool_input = event.get("toolInput" if harness == "grok" else "tool_input")
        if not isinstance(tool_input, dict):
            raise ValueError("shell input unavailable")
        command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        raise ValueError("shell command unavailable")
    return command


def run_guard(command: str, *, timeout: float = DEFAULT_TIMEOUT, harness: str = "") -> tuple[bool, str]:
    """Return allow/message; transport failures and unexpected output deny."""
    if not math.isfinite(timeout) or not 0 < timeout <= DEFAULT_TIMEOUT:
        return False, BLOCK_PREFIX + "invalid guard deadline.\n"
    try:
        # Direct-file invocation needs the repository root for the shared
        # guard runner and linked-worktree interpreter resolver.
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        from scripts.agent_runtime.codex_hook_policy import run_guard as run_guard_process
        from scripts.common.repo_root import project_interpreter

        if not GUARD_PATH.is_file():
            return False, BLOCK_PREFIX + "shared guard unavailable.\n"
        payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
        if harness == "agy":
            env = dict(os.environ)
            env.pop("LEARN_UK_SECRETS_OK", None)
            result = subprocess.run(
                [str(project_interpreter(ROOT)), str(GUARD_PATH)],
                input=payload,
                text=True,
                capture_output=True,
                check=False,
                timeout=timeout,
                env=env,
            )
        else:
            result = run_guard_process(project_interpreter(ROOT), GUARD_PATH, payload, timeout)
    except subprocess.TimeoutExpired:
        return False, BLOCK_PREFIX + "shared guard deadline exceeded.\n"
    except (OSError, ValueError, UnicodeError):
        return False, BLOCK_PREFIX + "shared guard could not run.\n"
    if getattr(result, "timed_out", False):
        return False, BLOCK_PREFIX + "shared guard deadline exceeded.\n"
    if result.returncode == 0 and not result.stdout and not result.stderr:
        return True, ""
    if result.returncode == 2 and not result.stdout and result.stderr.startswith(BLOCK_PREFIX):
        return False, result.stderr
    return False, BLOCK_PREFIX + "shared guard failed.\n"


def emit_decision(harness: str, allowed: bool, message: str) -> int:
    """Write the native decision without candidate command text."""
    if harness in {"cursor", "agy"}:
        key = "permission" if harness == "cursor" else "decision"
        decision = {key: "allow" if allowed else "deny"}
        if not allowed:
            decision["user_message" if harness == "cursor" else "reason"] = message
        print(json.dumps(decision))
    if not allowed:
        sys.stderr.write(message)
    # AGY exit-code blocking is UNKNOWN. The driver probe must establish
    # whether deny JSON on exit 0 blocks a live run_command.
    return 0 if allowed or harness == "agy" else 2


def main(argv: list[str] | None = None) -> int:
    parser = HookParser(
        description="Check one native shell event with the shared no-print guard.\n"
        "Use as a pre-tool hook; this command does not install harness wiring.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example:\n"
        "  .venv/bin/python scripts/agent_runtime/secret_print_hook.py --harness cursor < event.json\n"
        "Outputs: native decision on stdout when required; denial text on stderr. No files written.\n"
        "Exit codes: AGY returns 0 with allow/deny JSON; others return 0 to allow, 2 to deny.\n"
        "Related: agents_extensions/shared/hooks/guard-secret-print.py",
    )
    parser.add_argument(
        "--harness",
        required=True,
        help="Native input/output dialect: " + ", ".join(sorted(HARNESSES)) + " (e.g. cursor).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help="Guard deadline in seconds, greater than 0 and at most 5 (default: 5; e.g. 1).",
    )
    harness = ""
    args = sys.argv[1:] if argv is None else argv
    # Retain the native denial format even if another option is malformed.
    for index, token in enumerate(args):
        if token == "--harness" and index + 1 < len(args):
            harness = args[index + 1]
        elif token.startswith("--harness="):
            harness = token.split("=", 1)[1]
    try:
        options = parser.parse_args(args)
        harness = options.harness
        raw = sys.stdin.read(MAX_STDIN_BYTES + 1)
        if len(raw.encode("utf-8")) > MAX_STDIN_BYTES:
            raise ValueError("native event too large")
        command = extract_command(harness, json.loads(raw))
        allowed, message = (
            (True, "") if command is None else run_guard(command, timeout=options.timeout, harness=harness)
        )
    except Exception:
        # The native boundary must deny even a dependency or adapter failure.
        allowed, message = False, BLOCK_PREFIX + "native hook could not complete safely.\n"
    return emit_decision(harness, allowed, message)


if __name__ == "__main__":
    raise SystemExit(main())
