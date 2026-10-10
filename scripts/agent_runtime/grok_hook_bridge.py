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
process binding. All native conversations and subagents inherit it; unknown
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
    "monitor": "Bash",
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


def _translate(payload: dict, *, driver: bool = False) -> dict:
    """Translate native fields, retaining each driver's guard input contract."""
    if payload.get("hookEventName", payload.get("hook_event_name")) not in {"PreToolUse", "pre_tool_use"}:
        raise ValueError("invalid PreToolUse event")
    tool_name = _TOOL_NAMES.get(payload.get("toolName"))
    tool_input = payload.get("toolInput")
    if payload.get("toolInputTruncated") or tool_name is None:
        raise ValueError("unknown or truncated tool payload")
    if not isinstance(tool_input, dict):
        raise ValueError("unknown tool payload")
    if tool_name == "Bash" and not isinstance(tool_input.get("command"), str):
        raise ValueError("shell command unavailable")
    translated = dict(payload)
    translated["tool_name"] = tool_name
    translated["tool_input"] = dict(tool_input)
    translated["tool_input"].setdefault("cwd", (tool_input.get("workdir") if driver else None) or payload.get("cwd"))
    return translated


def _guard_output(raw: str, payload: dict) -> str:
    """Keep guard-only cwd context out of a native tool-input rewrite."""
    output = json.loads(raw)
    if not isinstance(output, dict):
        raise ValueError("guard output must be an object")
    specific = output.get("hookSpecificOutput", {})
    if not isinstance(specific, dict):
        raise ValueError("guard hook output must be an object")
    if "updatedInput" in specific:
        updated = specific["updatedInput"]
        if not isinstance(updated, dict):
            raise ValueError("guard rewrite must be an object")
        specific["updatedInput"] = {key: updated[key] for key in payload["toolInput"] if key in updated}
    return json.dumps(output)


def _driver_main(matcher: str) -> int:
    """Enforce shared guards for every session in a bound driver process tree.

    Dispatched workers and reviewers scrub the binding through env_unsets.
    No lease is acquired, inspected or changed here.
    """
    if not os.environ.get("LU_GROK_DRIVER_SESSION_ID"):
        return 0
    payload = json.load(sys.stdin)
    if not isinstance(payload, dict):
        raise ValueError("invalid PreToolUse event")
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
    translated = _translate(payload, driver=True)
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
            outputs.append(_guard_output(result.stdout, payload))
    for output in outputs:
        print(output)
    return 0


def _driver_preflight(source_root: Path) -> int:
    """Require native trust and discovery of the byte-exact deployed profile."""
    remedy = "Run npm run agents:deploy in this checkout, then retry."
    try:
        inspection = json.load(sys.stdin)
        if not isinstance(inspection, dict):
            raise ValueError("inspection is not an object")
    except (ValueError, TypeError) as exc:
        raise ValueError(
            "Grok driver preflight: grok inspect --json returned invalid output; rerun grok inspect --json."
        ) from exc
    inspected_root = inspection.get("projectRoot")
    if (
        not isinstance(inspected_root, str)
        or not inspected_root
        or not Path(inspected_root).is_absolute()
        or Path(inspected_root).resolve() != source_root.resolve()
    ):
        raise ValueError(
            "Grok driver preflight: projectRoot does not resolve to the launcher checkout. "
            "Unset project/config environment overrides and rerun grok inspect --json in this checkout, then retry."
        )
    if inspection.get("projectTrusted") is not True:
        raise ValueError(
            "Grok driver preflight: folder is not trusted. Run grok in this checkout and accept the folder-trust prompt, then retry."
        )
    source = source_root / "agents_extensions/grok/hooks/driver.json"
    deployed = source_root / ".grok/hooks/driver.json"
    if not source.is_file() or not deployed.is_file():
        raise ValueError(f"Grok driver preflight: driver profile is missing. {remedy}")
    if source.read_bytes() != deployed.read_bytes():
        raise ValueError(f"Grok driver preflight: deployed driver profile differs from its source. {remedy}")
    expected = json.loads(source.read_bytes())["hooks"]["PreToolUse"]
    discovered = inspection.get("hooks")
    if not isinstance(discovered, list):
        raise ValueError(f"Grok driver preflight: pre_tool_use hooks are missing. {remedy}")
    for group in expected:
        if not any(
            isinstance(hook, dict)
            and hook.get("event") == "pre_tool_use"
            and hook.get("hookType") == "command"
            and hook.get("matcher") == group["matcher"]
            and hook.get("target") == group["hooks"][0]["command"]
            and hook.get("source") == {"type": "project", "path": str(deployed.parent)}
            and hook.get("compatibilityStatus", "enabled") == "enabled"
            for hook in discovered
        ):
            raise ValueError(
                f"Grok driver preflight: pre_tool_use matcher {group['matcher']} is missing or disabled. {remedy}"
            )
    return 0


def main() -> int:
    if sys.argv[1:] == ["--help"]:
        print(
            "Usage: grok_hook_bridge.py GUARD | --driver MATCHER | --driver-preflight ROOT\n"
            "Translate native Grok PreToolUse stdin JSON and run tracked fleet guards.\n"
            "Use as a native hook bridge or launcher preflight, never to launch a provider.\n"
            "--driver requires launcher identity; --driver-preflight reads inspection stdin JSON.\n"
            "Outputs: guard stdout/stderr; preflight only validates, writes no files.\n"
            "Exit codes: 0 allowed; 2 denied or invalid input.\n"
            "Related: docs/runbooks/grok-session-canary.md\n"
            "Example: grok_hook_bridge.py --driver 'Bash|run_terminal_command|run_terminal_cmd|monitor'"
        )
        return 0
    try:
        if len(sys.argv) == 3 and sys.argv[1] in {"--driver", "--driver-preflight"}:
            try:
                if sys.argv[1] == "--driver-preflight":
                    return _driver_preflight(Path(sys.argv[2]))
                return _driver_main(sys.argv[2])
            except Exception as exc:
                detail = f": {exc}" if sys.argv[1] == "--driver-preflight" else ""
                print(f"BLOCKED by grok hook bridge: {type(exc).__name__}{detail}.", file=sys.stderr)
                return 2
        if len(sys.argv) != 2:
            raise ValueError("one fleet guard path required")
        argv = guard_argv(sys.argv[1])
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise ValueError("invalid PreToolUse event")
        translated = _translate(payload)
        result = subprocess.run(argv, input=json.dumps(translated), text=True, check=False, timeout=10, capture_output=True)
        sys.stderr.write(result.stderr or "")
        if result.returncode != 0:
            return 2
        if result.stdout and result.stdout.strip():
            print(_guard_output(result.stdout, payload))
        return 0
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
