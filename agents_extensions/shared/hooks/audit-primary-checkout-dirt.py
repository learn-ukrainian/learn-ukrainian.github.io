#!/usr/bin/env python3
"""Shell-call audit — detect and attribute primary-checkout dirt (#11253).

``guard-primary-checkout-write.py`` refuses writes it can read in the command
text. A launched script can still write into the primary checkout unseen, for
example by ``cd``-ing there and redirecting to a relative path. This hook
closes that observation gap for every shell call. The payload's
``hook_event_name`` selects the phase:

* PreToolUse snapshots ``git status`` of each protected primary checkout that
  owns the payload cwd or the project directory.
* PostToolUse (and Claude's PostToolUseFailure, where Claude routes a non-zero
  exit) compares again. Paths dirty now but not before are recorded with the
  command, session and tool-use ids outside the repository, and the hook exits
  2 so the agent sees the paths, the command and the cleanup command for
  exactly those files (``scripts.hygiene.primary_dirt_cleanup``).

The hook refuses nothing: the call already ran when the post phase fires, and
a failing snapshot must not stall a session, so both phases fail open. An
internal error in the post phase exits 1, which the harness shows as a hook
error.
Dispatch still refuses a dirty primary (``scripts/delegate.py``); this hook
makes the dirt attributable and removable without the operator override.
Threat model and cost: ``scripts/guardrails/primary_dirt_audit.py``.
"""

from __future__ import annotations

import json
import os
import shlex
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Don't write __pycache__ next to deployed hooks (#9108).
sys.dont_write_bytecode = True

from tool_names import is_shell_tool

MAX_LISTED = 20
# The phase comes from the payload, so the wired command stays a plain hook path.
PHASES = {"PreToolUse": "pre", "PostToolUse": "post", "PostToolUseFailure": "post"}


def _repo_root() -> Path | None:
    here = Path(__file__).resolve()
    for candidate in (here.parent, *here.parents):
        if (candidate / "scripts" / "guardrails" / "primary_dirt_audit.py").exists():
            return candidate
    return None


def _load_audit(root: Path):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from scripts.guardrails import primary_dirt_audit

    return primary_dirt_audit


def _tool_input(payload: dict) -> dict:
    for key in ("tool_input", "arguments", "input", "params"):
        value = payload.get(key)
        if isinstance(value, dict):
            return value
    return {}


def _payload_cwd(payload: dict) -> str:
    # Same precedence as guard-primary-checkout-write: the tool's own working
    # directory outranks the session cwd of the hook envelope.
    tool_input = _tool_input(payload)
    cwd = (
        tool_input.get("cwd")
        or tool_input.get("workdir")
        or tool_input.get("working_directory")
        or payload.get("cwd")
        or payload.get("working_directory")
    )
    return str(cwd) if cwd else os.getcwd()


def _report(records: list[dict], session_id: str) -> str:
    lines: list[str] = []
    for record in records:
        entries = record["entries"]
        lines.append(
            f"PRIMARY CHECKOUT DIRTIED during this shell call (audit-primary-checkout-dirt, #11253): "
            f"{len(entries)} path(s) became dirty in the protected primary checkout {record['primary_root']} "
            "between the snapshots before and after it."
        )
        lines.append(f"  command: {record['command']}{' [truncated]' if record['command_truncated'] else ''}")
        lines.append(f"  cwd: {record['cwd']}")
        for entry in entries[:MAX_LISTED]:
            lines.append(f"    {entry['xy']} {entry['path']}")
        if len(entries) > MAX_LISTED:
            lines.append(f"    ... and {len(entries) - MAX_LISTED} more (see the record)")
        lines.append(f"  attribution record: {record['record_id']}")
        lines.append(
            "  The tool output above this message is unchanged; the call already ran. Remove the untracked "
            "files this call created (only those; dry run first, then --apply):"
        )
        lines.append(
            "    .venv/bin/python -m scripts.hygiene.primary_dirt_cleanup "
            f"--session {shlex.quote(session_id)} --record {shlex.quote(record['record_id'])} [--apply]"
        )
        if any(entry["kind"] == "tracked" for entry in entries):
            lines.append(
                "  Tracked changes are not removed by that command; restore them deliberately "
                "(for example `git -C <primary> checkout -- <path>`) after checking nobody else made them."
            )
        lines.append(
            "  Fix the cause: write scratch output to absolute paths outside the primary checkout or "
            "inside your dispatch worktree; never cd into the primary before a relative write."
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except (ValueError, RecursionError):
        return 0
    if not isinstance(payload, dict):
        return 0
    phase = PHASES.get(str(payload.get("hook_event_name") or ""))
    if phase is None:
        return 0
    tool_name = str(payload.get("tool_name") or "")
    if not is_shell_tool(tool_name):
        return 0
    session_id = payload.get("session_id")
    tool_use_id = payload.get("tool_use_id")
    if not isinstance(session_id, str) or not session_id or not isinstance(tool_use_id, str) or not tool_use_id:
        return 0

    cwd = _payload_cwd(payload)
    repo_root = _repo_root()
    if repo_root is None:
        if phase == "post":
            sys.stderr.write("audit-primary-checkout-dirt: audit library not found; this call was not audited.\n")
            return 1
        return 0
    candidates = [cwd, os.environ.get("CLAUDE_PROJECT_DIR") or str(repo_root)]

    if phase == "pre":
        try:
            audit = _load_audit(repo_root)
            state = audit.state_dir()
            audit.collect_stale_snapshots(state)
            audit.take_snapshot(state, session_id, tool_use_id, candidates)
        except Exception:
            return 0
        return 0

    try:
        audit = _load_audit(repo_root)
        command = _tool_input(payload).get("command")
        result = audit.finish_call(
            audit.state_dir(),
            session_id=session_id,
            tool_use_id=tool_use_id,
            command=command if isinstance(command, str) else "",
            cwd=cwd,
            hook_event=str(payload.get("hook_event_name") or ""),
            tool_name=tool_name,
            candidates=candidates,
        )
    except Exception as exc:
        sys.stderr.write(f"audit-primary-checkout-dirt: this call was not audited: {type(exc).__name__}: {exc}\n")
        return 1

    if result["records"]:
        message = _report(result["records"], session_id)
        for root, reason in result["unaudited"].items():
            message += f"  also not audited: {root}: {reason}\n"
        sys.stderr.write(message)
        return 2
    if result["unaudited"]:
        for root, reason in result["unaudited"].items():
            sys.stderr.write(f"audit-primary-checkout-dirt: primary checkout {root} not audited: {reason}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
