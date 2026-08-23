#!/usr/bin/env python3
"""Post loopback observer presence without a RAM lease (#7063, #7075).

Callers are the Cursor driver launcher and the same helper for a GUI Cursor
driver session. Never prints host aliases, IPs, occupancy env, or summaries.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from collections.abc import Callable, Sequence
from typing import Any
from urllib.parse import urlparse

DEFAULT_MONITOR = "http://127.0.0.1:8765"
ALLOWED_AGENTS = frozenset({"grok-bot", "qa-engineer", "cursor", "codex"})
ALLOWED_STATUSES = frozenset({"working", "blocked", "idle"})
RENEW_AFTER_S = 8 * 60


class HeartbeatError(ValueError):
    """Loopback URL or payload rejected before POST."""


def _loopback_monitor_url(raw: str) -> str:
    try:
        parsed = urlparse(raw)
        host = parsed.hostname
        port = parsed.port
    except ValueError:
        raise HeartbeatError("monitor URL must be http loopback") from None
    if parsed.scheme != "http" or parsed.path not in {"", "/"}:
        raise HeartbeatError("monitor URL must be http loopback")
    if host in {"localhost", "127.0.0.1"}:
        return f"http://127.0.0.1:{port or 8765}"
    raise HeartbeatError("monitor URL must be http loopback")


def presence_url(base: str | None = None) -> str:
    raw = (base if base is not None else os.environ.get("LU_MONITOR_LOOPBACK", DEFAULT_MONITOR)).strip()
    return _loopback_monitor_url(raw) + "/api/observer/presence"


def post_observer_presence(
    *,
    agent: str,
    task_id: str,
    status: str = "working",
    epic: str | None = None,
    summary: str | None = None,
    base: str | None = None,
    opener: Any = None,
) -> dict[str, Any]:
    if agent not in ALLOWED_AGENTS:
        raise HeartbeatError("unknown observer agent")
    if status not in ALLOWED_STATUSES:
        raise HeartbeatError("invalid status")
    payload: dict[str, str] = {
        "agent": agent,
        "kind": "observer",
        "task_id": task_id,
        "status": status,
    }
    if epic:
        payload["epic"] = epic
    if summary:
        payload["summary"] = summary
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        presence_url(base),
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    urlopen = urllib.request.urlopen if opener is None else opener
    try:
        with urlopen(request, timeout=5) as resp:
            raw_body = resp.read().decode("utf-8")
        data = json.loads(raw_body)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise urllib.error.URLError("unreachable") from exc
    except json.JSONDecodeError:
        raise HeartbeatError("presence response was not an object") from None
    if not isinstance(data, dict):
        raise HeartbeatError("presence response was not an object")
    return {
        "agent": agent,
        "task_id": task_id,
        "status": status,
        "host_id": "cloud-observer" if data.get("host_id") == "cloud-observer" else None,
    }


def is_gui_process_for_agent(agent: str, command_line: str) -> bool:
    """Return True if command_line indicates a running GUI process for agent."""
    cmd = command_line.strip()
    if not cmd:
        return False
    if agent == "cursor":
        if "Cursor.app" in cmd:
            return True
        basename = cmd.rsplit("/", 1)[-1]
        return basename in {"Cursor", "Cursor Helper"} or basename.startswith("Cursor Helper ")
    if agent == "codex":
        if "Codex.app" in cmd:
            return True
        basename = cmd.rsplit("/", 1)[-1]
        return basename in {"Codex", "Codex Helper", "codex-ui"} or basename.startswith("Codex Helper ")
    return False


def _list_running_processes(runner: Callable[[], Sequence[str]] | None = None) -> list[str]:
    if runner is not None:
        return list(runner())
    try:
        proc = subprocess.run(
            ["/bin/ps", "-ax", "-o", "comm"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        if proc.returncode != 0:
            return []
        return [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    except Exception:
        return []


def detect_mac_gui_session(
    agent: str,
    *,
    process_lines: Sequence[str] | None = None,
    runner: Callable[[], Sequence[str]] | None = None,
) -> bool:
    """Detect whether a Mac GUI session is alive for agent without claiming a lease."""
    if agent not in ALLOWED_AGENTS:
        raise HeartbeatError("unknown observer agent")
    lines = process_lines if process_lines is not None else _list_running_processes(runner)
    return any(is_gui_process_for_agent(agent, line) for line in lines)


def detect_live_gui_agents(
    *,
    process_lines: Sequence[str] | None = None,
    runner: Callable[[], Sequence[str]] | None = None,
) -> list[str]:
    """Detect which allowed GUI observer agents are currently running."""
    lines = process_lines if process_lines is not None else _list_running_processes(runner)
    found: list[str] = []
    for agent in ("cursor", "codex"):
        if any(is_gui_process_for_agent(agent, line) for line in lines):
            found.append(agent)
    return found


def sweep_mac_gui_presence(
    *,
    base: str | None = None,
    opener: Any = None,
    process_lines: Sequence[str] | None = None,
    runner: Callable[[], Sequence[str]] | None = None,
    cursor_task_id: str = "cursor-gui",
    codex_task_id: str = "codex-gui",
    status: str = "idle",
) -> list[dict[str, Any]]:
    """Detect live Mac GUI sessions and post observer heartbeat with status=idle.

    If a GUI is not running, no heartbeat is posted (omitted).
    """
    live_agents = detect_live_gui_agents(process_lines=process_lines, runner=runner)
    task_map = {
        "cursor": cursor_task_id,
        "codex": codex_task_id,
    }
    results: list[dict[str, Any]] = []
    for agent in live_agents:
        task_id = task_map.get(agent, f"{agent}-gui")
        row = post_observer_presence(
            agent=agent,
            task_id=task_id,
            status=status,
            summary=f"{agent} mac gui observer heartbeat",
            base=base,
            opener=opener,
        )
        results.append(row)
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Post loopback observer presence (#7075, #7104).")
    parser.add_argument("--agent")
    parser.add_argument("--task-id")
    parser.add_argument("--status")
    parser.add_argument("--epic")
    parser.add_argument("--summary")
    parser.add_argument(
        "--mac-gui",
        action="store_true",
        help="Detect running Mac GUI sessions (Cursor/Codex) and post idle heartbeats",
    )
    parser.add_argument("--cursor-task-id", default="cursor-gui")
    parser.add_argument("--codex-task-id", default="codex-gui")
    parser.add_argument("--repo-root", help=argparse.SUPPRESS)
    return parser


def main(
    argv: list[str] | None = None,
    *,
    opener: Any = None,
    process_lines: Sequence[str] | None = None,
    runner: Callable[[], Sequence[str]] | None = None,
) -> int:
    args = build_parser().parse_args(argv)
    if args.mac_gui:
        status = args.status if args.status is not None else "idle"
        try:
            results = sweep_mac_gui_presence(
                opener=opener,
                process_lines=process_lines,
                runner=runner,
                cursor_task_id=args.cursor_task_id,
                codex_task_id=args.codex_task_id,
                status=status,
            )
        except HeartbeatError as exc:
            print(f"observer-heartbeat: {exc}", file=sys.stderr)
            return 2
        except Exception:
            print("observer-heartbeat: monitor unreachable", file=sys.stderr)
            return 1
        if not results:
            print("observer-heartbeat: no live mac gui sessions detected")
            return 0
        for row in results:
            print(f"observer-heartbeat: agent={row['agent']} task_id={row['task_id']} status={row['status']}")
        return 0

    if not args.agent or not args.task_id:
        print("observer-heartbeat: --agent and --task-id are required (or use --mac-gui)", file=sys.stderr)
        return 2

    status = args.status if args.status is not None else "working"
    try:
        post_observer_presence(
            agent=args.agent,
            task_id=args.task_id,
            status=status,
            epic=args.epic,
            summary=args.summary,
            opener=opener,
        )
    except HeartbeatError as exc:
        print(f"observer-heartbeat: {exc}", file=sys.stderr)
        return 2
    except Exception:
        print("observer-heartbeat: monitor unreachable", file=sys.stderr)
        return 1
    print(f"observer-heartbeat: agent={args.agent} task_id={args.task_id} status={status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
