#!/usr/bin/env python3
"""Probe the production Monitor plane on loopback for driver launchers.

Drivers prefer the one production Linux Monitor at loopback. If that Monitor
is down, launchers must still start on the Mac — they must not enable the
retired local sqlite. This module never prints host aliases or occupancy env.
"""

from __future__ import annotations

import argparse
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
    return os.environ.get(
        "LU_MONITOR_LOOPBACK",
        os.environ.get("DELEGATE_MONITOR_API", _MONITOR_DEFAULT),
    ).rstrip("/")


def _get_json(path: str, *, timeout: float) -> dict[str, Any]:
    url = f"{_monitor_base()}{path}"
    with urllib.request.urlopen(url, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("monitor payload is not an object")
    return payload


def check_driver_plane(*, timeout: float = 2.0) -> tuple[PlaneStatus, str]:
    """Return launcher posture for the production Monitor plane.

    ``ok`` — loopback Monitor is the production Linux plane.
    ``degraded`` — production Monitor/tunnel unreachable; start on the Mac anyway.
    ``skipped`` — hermetic tests opted out.
    """
    if os.environ.get(ENV_SKIP, "").strip() == "1":
        return "skipped", "plane probe skipped"
    try:
        health = _get_json("/api/health", timeout=timeout)
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
            "production Monitor unreachable on loopback; starting on Mac. "
            "Fleet sqlite stays retired until the tunnel is back.",
        )
    if str(health.get("status") or "") != "ok":
        return (
            "degraded",
            "production Monitor health is not ok; starting on Mac. "
            "Fleet sqlite stays retired until the tunnel is back.",
        )
    # The fleet-health schema is not a reachability signal. In authority mode,
    # a typed ``authority_unsupported_component`` refusal reports db_exists as
    # false by design because the production plane is backed by Postgres.
    return "ok", "production plane reachable on loopback"


def format_launcher_line(status: PlaneStatus, reason: str) -> str:
    if status == "ok":
        return f"plane: {reason}"
    if status == "skipped":
        return f"plane: {reason}"
    return f"⚠️  plane fallback: {reason}"


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        prog="plane_tunnel_gate.py",
        description=(
            "Probe the production Monitor on loopback before Mac driver launch.\n"
            "Use it to warn when the plane is down; do not use it to start a "
            "second Monitor or reopen retired Mac sqlite."
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/orchestration/plane_tunnel_gate.py\n"
            "  LU_SKIP_PLANE_TUNNEL_CHECK=1 .venv/bin/python scripts/orchestration/plane_tunnel_gate.py\n\n"
            "Outputs:\n"
            "  Prints a one-line plane status. Degraded probes still exit 0 so "
            "drivers start on the Mac; they never reopen retired sqlite.\n\n"
            "Exit codes:\n"
            "  0 after a probe (ok, degraded, or skipped); 2 on CLI misuse.\n\n"
            "Related:\n"
            "  Dispatch: scripts/orchestration/job_host_exec.py\n"
            "  Fleet: scripts/lib/fleet_comms_cold_start.sh\n"
            "  Issue: #7177\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    parser.parse_args(argv)
    status, reason = check_driver_plane()
    print(format_launcher_line(status, reason), file=sys.stderr if status == "degraded" else sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
