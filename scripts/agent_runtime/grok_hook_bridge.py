#!/usr/bin/env python3
"""Translate a Grok PreToolUse event for the existing fleet guard scripts.

Grok sends camelCase tool fields and native tool names. The tracked guards
consume Claude-shaped fields. This bridge preserves the original payload and
adds the shape the guards require; an unreadable event or missing guard denies.
Reviewer sessions and write sessions both enter through this bridge.

The guard argument is either a tracked guard path in this checkout, run
directly, or the project interpreter followed by one of the tracked guards that
need it. The Claude adapter emits that second form; any other path,
interpreter, guard or extra argument denies.

The driver profile supplies ``--driver MATCHER`` instead. That entrypoint
uses the same guard groups as write workers and requires the launcher's native
session UUID. Its guards retain their own structured-input contracts; unknown
events and truncated inputs deny before any guard is run.
"""

from __future__ import annotations

import json
import os
import shlex
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


# Must match ``PROJECT_PYTHON_GUARDS`` in ``adapters/claude.py``; a test pins the
# two sets together. The bridge does not import the adapter: it runs on every
# guarded tool call.
PROJECT_PYTHON_GUARDS = frozenset({"guard-pr-merge.py", "guard-admin-merge.py", "guard-branch-switch-in-main.py"})
# The deployed wrapper is translated away by the adapter; it is never a guard.
_PROJECT_PYTHON_HOOK_WRAPPER = "run-project-python-hook.sh"


class GuardInvocationError(ValueError):
    """The guard argument is neither a guard path nor a pinned invocation."""


def _project_interpreter(source_root: Path) -> Path:
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))
    from scripts.common.repo_root import project_interpreter

    return project_interpreter(source_root)


def guard_argv(command: str) -> list[str]:
    """Return the argv for one guard path or one pinned interpreter invocation.

    The argument is split into shell words first, so quoting and escaping never
    change how it is classified; an unreadable argument denies.
    """
    try:
        argv = shlex.split(command)
    except ValueError as exc:
        raise GuardInvocationError("unreadable fleet guard invocation") from exc
    source_root = Path(__file__).resolve().parents[2]
    hooks_dir = source_root / "agents_extensions/shared/hooks"
    if len(argv) == 1:
        guard = Path(argv[0])
        if guard != hooks_dir / guard.name or guard.name == _PROJECT_PYTHON_HOOK_WRAPPER:
            raise GuardInvocationError("only tracked fleet guards may run")
        if not guard.is_file():
            raise GuardInvocationError("fleet guard unavailable")
        return argv
    if len(argv) != 2:
        raise GuardInvocationError("one fleet guard path or pinned interpreter invocation required")
    python_bin, guard = (Path(arg) for arg in argv)
    if guard.name not in PROJECT_PYTHON_GUARDS or guard != hooks_dir / guard.name:
        raise GuardInvocationError("only tracked parser guards may run under the project interpreter")
    if not guard.is_file():
        raise GuardInvocationError("fleet guard unavailable")
    if python_bin != _project_interpreter(source_root):
        raise GuardInvocationError("fleet guard interpreter is not the project interpreter")
    return argv


def _translate(payload: dict, *, strict: bool = True) -> dict:
    """Translate native fields, retaining each driver's guard input contract."""
    if payload.get("hookEventName", payload.get("hook_event_name")) not in {"PreToolUse", "pre_tool_use"}:
        raise ValueError("invalid PreToolUse event")
    tool_name = _TOOL_NAMES.get(payload.get("toolName"))
    tool_input = payload.get("toolInput")
    if payload.get("toolInputTruncated") or tool_name is None:
        raise ValueError("unknown or truncated tool payload")
    if strict and not isinstance(tool_input, dict):
        raise ValueError("unknown tool payload")
    if strict and tool_name == "Bash" and not isinstance(tool_input.get("command"), str):
        raise ValueError("shell command unavailable")
    translated = dict(payload)
    translated["tool_name"] = tool_name
    translated["tool_input"] = dict(tool_input) if isinstance(tool_input, dict) else tool_input
    if isinstance(translated["tool_input"], dict):
        translated["tool_input"].setdefault("cwd", payload.get("cwd"))
    return translated


def _driver_main(matcher: str) -> int:
    """Run one shared guard group only for the launcher's native session UUID.

    Workers, reviews and native child sessions may inherit driver environment
    variables, but their native session id cannot match this launch binding.
    No lease is acquired, inspected or changed here.
    """
    session_id = os.environ.get("LU_GROK_DRIVER_SESSION_ID")
    if not session_id:
        return 0
    raw = sys.stdin.read()
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("invalid PreToolUse event")
    if payload.get("sessionId") != session_id:
        if not payload.get("sessionId"):
            raise ValueError("driver event session unavailable")
        return 0
    if os.environ.get("SESSION_STREAM_AGENT") != "grok" or os.environ.get("SESSION_STREAM_HARNESS") != "grok-tui":
        raise ValueError("driver launcher identity unavailable")
    source_root = Path(__file__).resolve().parents[2]
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))
    from scripts.agent_runtime.adapters.grok_build import _fleet_guard_groups

    groups = _fleet_guard_groups(publish_guard=False, native_aliases=True)
    group = next((group for group in groups if group["matcher"] == matcher), None)
    if group is None:
        raise ValueError("unknown driver guard group")
    translated = _translate(payload, strict=False)
    outputs = []
    for hook in group["hooks"]:
        argv = guard_argv(hook["command"])
        # All Python guards use the shared interpreter, including guards whose
        # worker invocation is an executable path with a generic shebang.
        if len(argv) == 1 and Path(argv[0]).suffix == ".py":
            argv.insert(0, str(_project_interpreter(source_root)))
        result = subprocess.run(
            argv,
            input=json.dumps(translated),
            text=True,
            check=False,
            timeout=max(15, int(hook.get("timeout", 5))),
            capture_output=True,
        )
        sys.stderr.write(result.stderr)
        if result.returncode != 0:
            return 2
        # In particular, retain the publishing guard's updatedInput decision.
        if result.stdout.strip():
            outputs.append(result.stdout.strip())
    for output in outputs:
        print(output)
    return 0


def main() -> int:
    try:
        if len(sys.argv) == 3 and sys.argv[1] == "--driver":
            return _driver_main(sys.argv[2])
        if len(sys.argv) != 2:
            raise ValueError("one fleet guard path required")
        argv = guard_argv(sys.argv[1])
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise ValueError("invalid PreToolUse event")
        translated = _translate(payload)
        result = subprocess.run(argv, input=json.dumps(translated), text=True, check=False, timeout=10)
        return 0 if result.returncode == 0 else 2
    except (
        OSError,
        ValueError,
        TypeError,
        RuntimeError,
        RecursionError,
        ImportError,
        KeyError,
        subprocess.TimeoutExpired,
    ) as exc:
        detail = f": {exc}" if isinstance(exc, GuardInvocationError) else ""
        print(f"BLOCKED by grok hook bridge: {type(exc).__name__}{detail}.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
