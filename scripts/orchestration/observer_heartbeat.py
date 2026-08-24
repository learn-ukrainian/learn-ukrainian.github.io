#!/usr/bin/env python3
"""Post loopback observer presence without a RAM lease (#7063, #7075).

Callers are the Cursor driver launcher, Mac GUI supervision, and the notebook
session-marker sweep. Never prints host aliases, IPs, occupancy env, or
summaries.
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
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from scripts.api.occupancy_local import resolve_launcher_host_id
from scripts.api.occupancy_sanitize import CLOUD_OBSERVER_HOST_ID, opaque_host_id, safe_field
from scripts.api.telemetry.transcript_tokens import read_session_record, session_context_telemetry
from scripts.orchestration.session_markers import iter_session_markers

DEFAULT_MONITOR = "http://127.0.0.1:8765"
ALLOWED_AGENTS = frozenset({"grok-bot", "qa-engineer", "cursor", "codex", "claude"})
ALLOWED_STATUSES = frozenset({"working", "blocked", "idle"})
MAX_TELEMETRY_TOKENS = 10_000_000
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
    task_id: str | None = None,
    status: str = "working",
    epic: str | None = None,
    summary: str | None = None,
    host_id: str | None = None,
    instance_id: str | None = None,
    ctx_tokens: int | None = None,
    window_tokens: int | None = None,
    base: str | None = None,
    opener: Any = None,
) -> dict[str, Any]:
    if agent not in ALLOWED_AGENTS:
        raise HeartbeatError("unknown observer agent")
    if agent == "claude" and host_id is None:
        raise HeartbeatError("unknown observer agent")
    if status not in ALLOWED_STATUSES:
        raise HeartbeatError("invalid status")
    if task_id is not None and safe_field(task_id, role="task_id") is None:
        raise HeartbeatError("invalid task id")
    if host_id is not None and host_id != CLOUD_OBSERVER_HOST_ID and not opaque_host_id(host_id):
        raise HeartbeatError("invalid host id")
    if instance_id is not None and safe_field(instance_id, role="task_id") is None:
        raise HeartbeatError("invalid instance id")
    for token_name, token_value in (("ctx_tokens", ctx_tokens), ("window_tokens", window_tokens)):
        if token_value is not None and (
            isinstance(token_value, bool)
            or not isinstance(token_value, int)
            or token_value < 0
            or token_value > MAX_TELEMETRY_TOKENS
        ):
            raise HeartbeatError(f"invalid {token_name}")
    payload: dict[str, Any] = {
        "agent": agent,
        "kind": "observer",
        "status": status,
    }
    if task_id is not None:
        payload["task_id"] = task_id
    if epic:
        payload["epic"] = epic
    if summary:
        payload["summary"] = summary
    if host_id is not None:
        payload["host_id"] = host_id
    if instance_id is not None:
        payload["instance_id"] = instance_id
    if ctx_tokens is not None:
        payload["ctx_tokens"] = ctx_tokens
    if window_tokens is not None:
        payload["window_tokens"] = window_tokens
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
    response_host = data.get("host_id")
    acknowledged_host = None
    if response_host == CLOUD_OBSERVER_HOST_ID:
        acknowledged_host = CLOUD_OBSERVER_HOST_ID
    elif host_id is not None and response_host == host_id:
        acknowledged_host = host_id
    result: dict[str, Any] = {
        "agent": agent,
        "task_id": task_id,
        "status": status,
        "host_id": acknowledged_host,
    }
    if instance_id is not None:
        result["instance_id"] = instance_id
    return result


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
    if agent not in {"cursor", "codex"}:
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


def _default_reporter_host_id() -> str | None:
    """Return a configured opaque host id, omitting the legacy local token."""
    try:
        resolved = resolve_launcher_host_id()
        if resolved == CLOUD_OBSERVER_HOST_ID or resolved == "mac-operator":
            return resolved
        from scripts.api.occupancy import parse_host_id_map

        return resolved if resolved in parse_host_id_map().values() else None
    except Exception:
        return None


def _marker_telemetry(
    marker_instance_id: str,
    *,
    repo_root: Path,
) -> tuple[int | None, int | None]:
    context_tokens: int | None = None
    window_tokens: int | None = None
    try:
        telemetry = session_context_telemetry(repo_root, marker_instance_id)
        if telemetry is not None and 0 <= telemetry.tokens <= MAX_TELEMETRY_TOKENS:
            context_tokens = telemetry.tokens
    except Exception:
        pass
    try:
        record = read_session_record(repo_root, marker_instance_id)
    except Exception:
        record = None
    if isinstance(record, dict):
        for key in (
            "actual_context_window_tokens",
            "effective_context_window_tokens",
            "expected_context_window_tokens",
            "observed_context_window_tokens",
        ):
            value = record.get(key)
            if isinstance(value, int) and not isinstance(value, bool) and 0 < value <= MAX_TELEMETRY_TOKENS:
                window_tokens = value
                break
    return context_tokens, window_tokens


def sweep_session_markers(
    *,
    repo_root: Path | str | None = None,
    marker_root: Path | str | None = None,
    host_id: str | None = None,
    base: str | None = None,
    opener: Any = None,
    now: Any = None,
    pid_alive: Callable[[int], bool] | None = None,
) -> list[dict[str, Any]]:
    """Post one working heartbeat for each fresh local session marker."""
    effective_root = Path(repo_root) if repo_root is not None else Path.cwd()
    reporter_host_id = host_id if host_id is not None else _default_reporter_host_id()
    results: list[dict[str, Any]] = []
    for marker in iter_session_markers(root=marker_root, now=now, pid_alive=pid_alive):
        ctx_tokens, window_tokens = _marker_telemetry(marker.instance_id, repo_root=effective_root)
        safe_epic = safe_field(marker.epic, role="agent") if marker.epic else None
        try:
            row = post_observer_presence(
                agent=marker.agent,
                task_id=marker.task_id,
                status="working",
                epic=safe_epic,
                summary="Notebook session",
                host_id=reporter_host_id,
                instance_id=marker.instance_id,
                ctx_tokens=ctx_tokens,
                window_tokens=window_tokens,
                base=base,
                opener=opener,
            )
        except Exception:
            # A single malformed or temporarily unavailable session must not
            # suppress the GUI sweep that follows in the same LaunchAgent run.
            continue
        results.append(row)
    return results


def sweep_mac_gui_presence(
    *,
    base: str | None = None,
    opener: Any = None,
    process_lines: Sequence[str] | None = None,
    runner: Callable[[], Sequence[str]] | None = None,
    cursor_task_id: str = "cursor-gui",
    codex_task_id: str = "codex-gui",
    status: str = "idle",
    host_id: str | None = None,
) -> list[dict[str, Any]]:
    """Detect live Mac GUI sessions and post observer heartbeat with status=idle.

    If a GUI is not running, no heartbeat is posted (omitted).
    """
    del status  # GUI process existence is never evidence of a working task.
    live_agents = detect_live_gui_agents(process_lines=process_lines, runner=runner)
    reporter_host_id = host_id if host_id is not None else _default_reporter_host_id()
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
            status="idle",
            summary="GUI session",
            host_id=reporter_host_id,
            instance_id="gui",
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
        try:
            reporter_host_id = _default_reporter_host_id()
            marker_results = sweep_session_markers(
                repo_root=args.repo_root,
                opener=opener,
                host_id=reporter_host_id,
            )
            gui_results = sweep_mac_gui_presence(
                opener=opener,
                process_lines=process_lines,
                runner=runner,
                cursor_task_id=args.cursor_task_id,
                codex_task_id=args.codex_task_id,
                host_id=reporter_host_id,
            )
            results = marker_results + gui_results
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
