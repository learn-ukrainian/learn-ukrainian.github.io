#!/usr/bin/env python3
"""Post loopback observer presence without a RAM lease (#7063, #7075).

Callers are the Cursor driver launcher and the same helper for a GUI Cursor
driver session. Never prints host aliases, IPs, occupancy env, or summaries.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urlparse

DEFAULT_MONITOR = "http://127.0.0.1:8765"
ALLOWED_AGENTS = frozenset({"grok-bot", "qa-engineer", "cursor"})
ALLOWED_STATUSES = frozenset({"working", "blocked", "idle"})
RENEW_AFTER_S = 8 * 60


class HeartbeatError(ValueError):
    """Loopback URL or payload rejected before POST."""


def _loopback_monitor_url(raw: str) -> str:
    parsed = urlparse(raw)
    if parsed.scheme != "http" or parsed.path not in {"", "/"}:
        raise HeartbeatError("monitor URL must be http loopback")
    host = parsed.hostname
    try:
        port = parsed.port
    except ValueError:
        raise HeartbeatError("monitor URL must be http loopback") from None
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
    with urlopen(request, timeout=5) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if not isinstance(data, dict):
        raise HeartbeatError("presence response was not an object")
    return {
        "agent": agent,
        "task_id": task_id,
        "status": status,
        "host_id": "cloud-observer" if data.get("host_id") == "cloud-observer" else None,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Post loopback observer presence (#7075).")
    parser.add_argument("--agent", required=True)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--status", default="working")
    parser.add_argument("--epic")
    parser.add_argument("--summary")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        post_observer_presence(
            agent=args.agent,
            task_id=args.task_id,
            status=args.status,
            epic=args.epic,
            summary=args.summary,
        )
    except HeartbeatError as exc:
        print(f"observer-heartbeat: {exc}", file=sys.stderr)
        return 2
    except urllib.error.URLError:
        print("observer-heartbeat: monitor unreachable", file=sys.stderr)
        return 1
    print(f"observer-heartbeat: agent={args.agent} task_id={args.task_id} status={args.status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
