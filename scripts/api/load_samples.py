"""Bounded, command-name-only load attribution for the Monitor (#10715)."""

from __future__ import annotations

import fcntl
import json
import math
import os
import re
import time
from collections import deque
from datetime import UTC, datetime
from pathlib import Path

import psutil

from scripts.common import test_slots

THRESHOLD_ENV = "LU_LOAD_SAMPLE_THRESHOLD"
DEFAULT_THRESHOLD = 20.0
MAX_SAMPLES = 500
MIN_INTERVAL_S = 60
CPU_INTERVAL_S = 0.1
SCHEMA = "load-samples.v1"
_NAME = re.compile(r"[A-Za-z0-9_+.-]{1,64}")


def threshold() -> float:
    """Reject malformed configuration without echoing the supplied value."""
    value = float(os.environ.get(THRESHOLD_ENV, str(DEFAULT_THRESHOLD)))
    if not math.isfinite(value) or value < 0:
        raise ValueError("invalid load sample threshold")
    return value


def top_processes() -> list[dict]:
    """Measure a shared CPU interval; never request arguments, executable paths or environments.

    psutil's first nonblocking CPU observation is meaningless, so prime every
    process and wait once for all of them. Percentages use one CPU as 100%.
    """
    processes = []
    for process in psutil.process_iter(attrs=["name"]):
        try:
            process.cpu_percent(None)
            processes.append(process)
        except psutil.Error:
            continue
    time.sleep(CPU_INTERVAL_S)
    rows = []
    for process in processes:
        try:
            cpu = process.cpu_percent(None)
            name = process.info["name"]
        except psutil.Error:
            continue
        if not math.isfinite(cpu) or cpu < 0:
            continue
        rows.append(
            {
                "name": name if isinstance(name, str) and _NAME.fullmatch(name) else "unknown",
                "cpu_percent": round(cpu, 1),
            }
        )
    return sorted(rows, key=lambda row: (-row["cpu_percent"], row["name"]))[:5]


def _read(path: Path) -> list[dict]:
    try:
        with path.open(encoding="utf-8") as stream:
            return [json.loads(line) for line in deque(stream, maxlen=MAX_SAMPLES)]
    except FileNotFoundError:
        return []


def sample(batch_state_dir: Path) -> bool:
    """Called by the existing Monitor periodic collector, off the event loop.

    A shared lock and persisted timestamp enforce the interval across Monitor
    workers and restarts. An atomic replacement leaves readers a complete ring.
    """
    loads = os.getloadavg()
    if loads[0] <= threshold():
        return False
    directory = batch_state_dir / "load-samples"
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (directory / "collector.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return False
        path = directory / "samples.jsonl"
        rows = _read(path)
        now = time.time()
        if rows and now - datetime.fromisoformat(rows[-1]["timestamp"]).timestamp() < MIN_INTERVAL_S:
            return False
        processes = top_processes()
        slots = test_slots.status()
        rows.append(
            {
                "timestamp": datetime.fromtimestamp(now, UTC).isoformat(),
                "load_averages": list(loads),
                "top_processes": processes,
                "top_cpu_percent": round(sum(row["cpu_percent"] for row in processes), 1),
                "test_slots": {
                    "holders": [{"task_id": row["task_id"], "slots": row["slots"]} for row in slots["holders"]],
                    "error": slots["error"]["reason"] if slots["error"] else None,
                    "enabled": slots["enabled"],
                },
            }
        )
        temporary = directory / "samples.tmp"
        with temporary.open("w", encoding="utf-8") as stream:
            for row in rows[-MAX_SAMPLES:]:
                stream.write(json.dumps(row, allow_nan=False) + "\n")
        os.replace(temporary, path)
        return True


def tail(batch_state_dir: Path, limit: int) -> dict:
    """Read existing samples only; absence is an empty ring, errors stay path-free."""
    try:
        rows = _read(batch_state_dir / "load-samples" / "samples.jsonl")
    except (OSError, ValueError):
        return {"schema": SCHEMA, "samples": [], "error": "load_samples_unavailable"}
    return {"schema": SCHEMA, "samples": rows[-max(1, min(limit, MAX_SAMPLES)) :], "error": None}
