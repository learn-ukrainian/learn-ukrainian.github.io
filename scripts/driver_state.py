"""Pinned per-epic driver state: who am I, what epic, which goals.

Long-running driver sessions lose their launch prompt when the harness
compacts context: the epic binding and the current goals lived only in the
first user turn. This module keeps them in a small local state file that the
harness re-reads on every model call, so compaction cannot drop them.

State file: ``<repo>/.claude/<epic>-epic/DRIVER-STATE.md`` (gitignored local
state, next to the epic's driver handoffs). The launcher exports
``LU_DRIVER_STATE_FILE`` for driver sessions; without it, nothing is injected.

Commands::

    .venv/bin/python -m scripts.driver_state whoami     # epic, seat, model, next step
    .venv/bin/python -m scripts.driver_state goals      # full pinned state
    .venv/bin/python -m scripts.driver_state path [--epic E]
    .venv/bin/python -m scripts.driver_state init --epic E [--force]
    .venv/bin/python -m scripts.driver_state agy-hook   # AGY PreInvocation hook (stdin JSON)

The ``agy-hook`` command implements the AGY ``PreInvocation`` contract: it
reads the hook payload on stdin and prints ``{"injectSteps": [{"ephemeralMessage":
...}]}``. An ephemeral message is transient (not stored in the transcript), so
it is re-injected before every model call and survives any compaction. The
hook is fail-open: any problem prints ``{}`` and never blocks the agent.
Standard library only, so it runs from a linked worktree without a venv.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

STATE_ENV = "LU_DRIVER_STATE_FILE"
STATE_NAME = "DRIVER-STATE.md"
MAX_INJECT_CHARS = 6000

TEMPLATE = """# Driver state: {epic}

<!-- Pinned driver state. Re-injected before every model call (AGY hook).
     Keep it short (under ~4 KB). Update Goals/Next as work lands. -->

## Epic
- Stream: {epic}
- Seat: driver (one per stream; the launcher owns the lease)
- Handoff: .claude/{epic}-epic/ (read the newest driver handoff on cold start)

## Current goals (bounded, each with a definition of done)
1. <goal> — DONE WHEN: <observable, tool-checkable condition>

## Hard rules
- Never self-merge; landing order is cross-family review at the exact head, then CI Gate, then the merge queue.
- No secrets or deployment details in the public repo.

## Next step
- <single next action>
"""


def _repo_root(start: Path | None = None) -> Path:
    start = start or Path.cwd()
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=start,
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        ).stdout.strip()
        if out:
            return Path(out)
    except (OSError, subprocess.SubprocessError):
        pass
    return start


def state_path(epic: str | None = None, root: Path | None = None) -> Path | None:
    """Resolve the state file: explicit epic wins, then the launcher env."""
    if epic:
        return (root or _repo_root()) / ".claude" / f"{epic}-epic" / STATE_NAME
    env = os.environ.get(STATE_ENV, "").strip()
    if env:
        return Path(env)
    session_epic = os.environ.get("SESSION_EPIC", "").strip()
    if session_epic:
        return (root or _repo_root()) / ".claude" / f"{session_epic}-epic" / STATE_NAME
    return None


def _state_root(path: Path) -> Path:
    # <root>/.claude/<epic>-epic/DRIVER-STATE.md -> <root>
    return path.resolve().parent.parent.parent


def _read_state(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if len(text) > MAX_INJECT_CHARS:
        text = text[:MAX_INJECT_CHARS].rsplit("\n", 1)[0] + "\n[... state truncated; run `goals` for the full file]\n"
    return text


def _section(text: str, title: str) -> list[str]:
    lines, inside = [], False
    for line in text.splitlines():
        if line.startswith("## "):
            inside = line[3:].strip().lower().startswith(title.lower())
            continue
        if inside and line.strip():
            lines.append(line)
    return lines


def render_injection(text: str, path: Path) -> str:
    return (
        "PINNED DRIVER STATE (re-injected every model call; authoritative over any "
        "compacted summary). You are the driver for the epic below. Re-orient from it "
        "before acting; update the file when a goal lands. Full file: "
        f"{path.name} under .claude/; CLI: `.venv/bin/python -m scripts.driver_state whoami|goals`.\n\n" + text.strip()
    )


def cmd_agy_hook(stdin_text: str) -> dict:
    path = state_path() if os.environ.get(STATE_ENV, "").strip() else None
    if path is None or not path.is_file():
        return {}
    try:
        payload = json.loads(stdin_text) if stdin_text.strip() else {}
    except json.JSONDecodeError:
        payload = {}
    workspaces = payload.get("workspacePaths") or []
    if workspaces:
        root = _state_root(path)
        resolved = set()
        for item in workspaces:
            try:
                resolved.add(Path(item).resolve())
            except (OSError, RuntimeError):
                continue
        # A worker in another checkout inherits env but must not get driver goals.
        if root not in resolved:
            return {}
    return {"injectSteps": [{"ephemeralMessage": render_injection(_read_state(path), path)}]}


def cmd_whoami(path: Path | None) -> int:
    epic = os.environ.get("SESSION_EPIC", "") or "(unset)"
    seat = os.environ.get("SESSION_HANDOFF_AGENT", "") or "(unset)"
    print(f"epic: {epic}")
    print(f"seat: {seat}")
    if path is None:
        print("state: (no LU_DRIVER_STATE_FILE / SESSION_EPIC; not a driver session)")
        return 1
    print(f"state: {path}")
    if not path.is_file():
        print("state file missing; create it with: init --epic <epic>")
        return 1
    text = path.read_text(encoding="utf-8")
    for title in ("Epic", "Next step"):
        body = _section(text, title)
        if body:
            print(f"{title.lower()}:")
            print("\n".join(body))
    goals = _section(text, "Current goals")
    if goals:
        print("goals:")
        print("\n".join(goals))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="driver_state",
        description="Pinned per-epic driver state (survives context compaction).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("whoami", help="Print epic, seat, goals and next step.")
    sub.add_parser("goals", help="Print the full pinned state file.")
    p_path = sub.add_parser("path", help="Print the state file path.")
    p_path.add_argument("--epic")
    p_init = sub.add_parser("init", help="Write a template state file for an epic.")
    p_init.add_argument("--epic", required=True)
    p_init.add_argument("--force", action="store_true", help="Overwrite an existing file.")
    sub.add_parser("agy-hook", help="AGY PreInvocation hook: stdin payload -> injectSteps JSON.")
    args = parser.parse_args(argv)

    if args.cmd == "agy-hook":
        try:
            result = cmd_agy_hook(sys.stdin.read())
        except Exception:  # hook must never block the agent loop
            result = {}
        sys.stdout.write(json.dumps(result))
        return 0
    if args.cmd == "whoami":
        return cmd_whoami(state_path())
    if args.cmd == "goals":
        path = state_path()
        if path is None or not path.is_file():
            print("no pinned driver state (see: whoami)", file=sys.stderr)
            return 1
        sys.stdout.write(path.read_text(encoding="utf-8"))
        return 0
    if args.cmd == "path":
        path = state_path(args.epic)
        if path is None:
            print("no epic: pass --epic or run inside a driver session", file=sys.stderr)
            return 1
        print(path)
        return 0
    if args.cmd == "init":
        path = state_path(args.epic)
        assert path is not None
        if path.exists() and not args.force:
            print(f"exists: {path} (use --force to overwrite)", file=sys.stderr)
            return 1
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(TEMPLATE.format(epic=args.epic), encoding="utf-8")
        print(path)
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
