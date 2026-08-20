#!/usr/bin/env python3
"""Probe the tunneled job-host Monitor for notebook driver launchers.

Drivers prefer the job-host plane at loopback (the persistent tunnel). If that
Monitor is down, launchers must still start on the notebook — they must not
enable the retired local sqlite. This module never prints host aliases or
occupancy env.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any, Literal

ENV_SKIP = "LU_SKIP_PLANE_TUNNEL_CHECK"
_MONITOR_DEFAULT = "http://127.0.0.1:8765"

PlaneStatus = Literal["ok", "degraded", "skipped"]


def _monitor_base() -> str:
    return os.environ.get("DELEGATE_MONITOR_API", _MONITOR_DEFAULT).rstrip("/")


def _get_json(path: str, *, timeout: float) -> dict[str, Any]:
    url = f"{_monitor_base()}{path}"
    with urllib.request.urlopen(url, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("monitor payload is not an object")
    return payload


def check_driver_plane(*, timeout: float = 2.0) -> tuple[PlaneStatus, str]:
    """Return launcher posture for the job-host plane.

    ``ok`` — loopback Monitor is the job-host observer.
    ``degraded`` — VPS/tunnel unreachable; start on the notebook anyway.
    ``skipped`` — hermetic tests opted out.
    """
    if os.environ.get(ENV_SKIP, "").strip() == "1":
        return "skipped", "plane probe skipped"
    try:
        health = _get_json("/api/health", timeout=timeout)
        fleet = _get_json("/api/fleet/health", timeout=timeout)
    except (
        OSError,
        TimeoutError,
        urllib.error.URLError,
        json.JSONDecodeError,
        ValueError,
        UnicodeDecodeError,
    ):
        return (
            "degraded",
            "job-host Monitor unreachable on loopback; starting on notebook. "
            "Fleet sqlite stays retired until the tunnel is back.",
        )
    if str(health.get("status") or "") != "ok":
        return (
            "degraded",
            "job-host Monitor health is not ok; starting on notebook. "
            "Fleet sqlite stays retired until the tunnel is back.",
        )
    schema = fleet.get("schema") if isinstance(fleet.get("schema"), dict) else {}
    if schema.get("db_exists") is not True:
        return (
            "degraded",
            "job-host fleet db is not visible; starting on notebook. "
            "Fleet sqlite stays retired until the tunnel is back.",
        )
    return "ok", "job-host plane reachable on loopback"


def format_launcher_line(status: PlaneStatus, reason: str) -> str:
    if status == "ok":
        return f"plane: {reason}"
    if status == "skipped":
        return f"plane: {reason}"
    return f"⚠️  plane fallback: {reason}"


def main(argv: list[str] | None = None) -> int:
    del argv
    status, reason = check_driver_plane()
    print(format_launcher_line(status, reason), file=sys.stderr if status == "degraded" else sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
