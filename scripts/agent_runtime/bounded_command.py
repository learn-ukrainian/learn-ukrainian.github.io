#!/usr/bin/env python3
"""Run one hook subprocess with a hard deadline and process-group cleanup."""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
from contextlib import suppress

TIMEOUT_EXIT_CODE = 124


def run(command: list[str], timeout_seconds: float) -> int:
    """Run ``command`` and kill its process group if the deadline expires."""
    process = subprocess.Popen(command, start_new_session=True)
    try:
        return process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        with suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
        process.wait()
        print(
            f"Session hook command exceeded {timeout_seconds:g}s and was terminated: {command[0]}",
            file=sys.stderr,
        )
        return TIMEOUT_EXIT_CODE


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command
    if command[:1] == ["--"]:
        command = command[1:]
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    if not command:
        parser.error("a command is required after --")
    return run(command, args.timeout)


if __name__ == "__main__":
    raise SystemExit(main())
