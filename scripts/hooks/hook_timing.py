#!/usr/bin/env python3
"""Append one JSONL timing row for a harness hook invocation.

Enable with HOOK_TIMING=1 (or HOOK_TIMING=always). Default log path:
  batch_state/hook-timing.jsonl  (gitignored runtime)

Does not modify tool stdin/stdout contracts beyond passing them through when
used as a wrapper (see run_hook_timed.sh).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LOG = ROOT / "batch_state" / "hook-timing.jsonl"


def timing_enabled() -> bool:
    val = (os.environ.get("HOOK_TIMING") or "").strip().lower()
    return val in {"1", "true", "yes", "always", "on", "force"}


def log_path() -> Path:
    raw = (os.environ.get("HOOK_TIMING_LOG") or "").strip()
    return Path(raw) if raw else DEFAULT_LOG


def append_row(row: dict[str, Any], path: Path | None = None, *, force: bool = False) -> None:
    if not force and not timing_enabled():
        return
    dest = path or log_path()
    dest.parent.mkdir(parents=True, exist_ok=True)
    row = {
        **row,
        "ts": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
    }
    with dest.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def run_wrapped(argv: list[str]) -> int:
    """Run argv as the real hook; log wall ms. stdin is forwarded."""
    if not argv:
        print("run_wrapped: missing command", file=sys.stderr)
        return 2
    event = os.environ.get("HOOK_EVENT_NAME") or ""
    matcher = os.environ.get("HOOK_MATCHER") or ""
    tool = os.environ.get("HOOK_TOOL_NAME") or ""
    stdin = sys.stdin.buffer.read()
    t0 = time.perf_counter()
    proc = subprocess.run(argv, input=stdin, capture_output=True)
    ms = (time.perf_counter() - t0) * 1000.0
    # preserve hook contract: stdout/stderr pass-through
    if proc.stdout:
        sys.stdout.buffer.write(proc.stdout)
    if proc.stderr:
        sys.stderr.buffer.write(proc.stderr)
    append_row(
        {
            "event": event or "unknown",
            "matcher": matcher or None,
            "tool_name": tool or None,
            "command": argv[0],
            "argv_tail": argv[1:6],
            "ms": round(ms, 2),
            "rc": proc.returncode,
            "stdout_bytes": len(proc.stdout or b""),
            "stderr_bytes": len(proc.stderr or b""),
            "harness": os.environ.get("SESSION_HANDOFF_AGENT")
            or os.environ.get("GROK_AGENT")
            or os.environ.get("CLAUDE_CODE")
            or "unknown",
        }
    )
    return int(proc.returncode)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    log_p = sub.add_parser("log", help="Append one timing row (no subprocess)")
    log_p.add_argument("--event", required=True)
    log_p.add_argument("--ms", type=float, required=True)
    log_p.add_argument("--rc", type=int, default=0)
    log_p.add_argument("--matcher", default="")
    log_p.add_argument("--command", default="")
    log_p.add_argument("--tool-name", default="")

    wrap_p = sub.add_parser("wrap", help="Run command and log timing")
    wrap_p.add_argument("command", nargs=argparse.REMAINDER, help="Command after --")

    args = parser.parse_args(argv)
    if args.cmd == "log":
        append_row(
            {
                "event": args.event,
                "matcher": args.matcher or None,
                "tool_name": args.tool_name or None,
                "command": args.command or None,
                "ms": args.ms,
                "rc": args.rc,
            },
            force=True,
        )
        return 0
    if args.cmd == "wrap":
        cmd = list(args.command)
        if cmd and cmd[0] == "--":
            cmd = cmd[1:]
        os.environ.setdefault("HOOK_TIMING", "1")
        return run_wrapped(cmd)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
