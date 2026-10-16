#!/usr/bin/env python3
"""Read-only uv cache size and 24-hour growth line for ``lu-driver-status`` (#10779).

The uv cache grows without bound on a busy host (every resolved wheel and
sdist build stays). This module measures it, keeps a small timestamped size
history, and renders one status line with a warning threshold. It never deletes
anything from the cache; the only file it writes is the size history.

Usage: ``.venv/bin/python -m scripts.hygiene.uv_cache_status [--json] [--no-record]``

Environment (all optional):
- ``UV_CACHE_DIR`` / ``XDG_CACHE_HOME``: where the cache lives (uv's own rules).
- ``LU_DRIVER_STATUS_STATE_DIR``: history directory (default: the driver-keeper
  state directory that ``lu-driver-status`` already reads).
- ``LU_UV_CACHE_WARN_GB``: absolute-size warning threshold (default 10).
- ``LU_UV_CACHE_GROWTH_WARN_GB``: 24-hour growth warning threshold (default 2).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
from collections.abc import Callable
from pathlib import Path

from scripts.common.jsonl import jsonl_lines

HISTORY_FILENAME = "uv-cache-size.jsonl"
WINDOW_SECONDS = 24 * 3600
# Keep a week of samples; the status line only needs the last day.
RETENTION_SECONDS = 7 * 24 * 3600
# One sample per interval at most, so a polling status command cannot bloat the file.
MIN_SAMPLE_INTERVAL_SECONDS = 600
# A baseline younger than this says nothing about growth; report "history building".
MIN_BASELINE_AGE_SECONDS = 3600
DEFAULT_WARN_GB = 10.0
DEFAULT_GROWTH_WARN_GB = 2.0
GIB = 1024**3

SizeFn = Callable[[Path], int]


def uv_cache_dir() -> Path:
    """Resolve the uv cache directory the way uv does (no subprocess)."""
    explicit = os.environ.get("UV_CACHE_DIR")
    if explicit:
        return Path(explicit).expanduser()
    xdg = os.environ.get("XDG_CACHE_HOME")
    base = Path(xdg).expanduser() if xdg else Path.home() / ".cache"
    return base / "uv"


def state_dir() -> Path:
    explicit = os.environ.get("LU_DRIVER_STATUS_STATE_DIR")
    if explicit:
        return Path(explicit).expanduser()
    return Path.home() / ".local/state/learn-ukrainian/driver-keeper"


def tree_size(root: Path) -> int:
    """Allocated bytes under ``root``; symlinks not followed, hardlinks counted once."""
    size = 0
    seen: set[tuple[int, int]] = set()
    pending = [root]
    while pending:
        directory = pending.pop()
        try:
            entries_context = os.scandir(directory)
        except (FileNotFoundError, PermissionError):
            continue
        with entries_context as entries:
            for entry in entries:
                try:
                    if entry.is_dir(follow_symlinks=False):
                        pending.append(Path(entry.path))
                        continue
                    info = entry.stat(follow_symlinks=False)
                except FileNotFoundError:
                    continue
                if info.st_nlink > 1:
                    key = (info.st_dev, info.st_ino)
                    if key in seen:
                        continue
                    seen.add(key)
                size += getattr(info, "st_blocks", 0) * 512 or info.st_size
    return size


def read_history(path: Path) -> list[dict[str, float]]:
    """Return valid ``{"ts", "bytes"}`` samples, oldest first; bad lines are skipped."""
    samples: list[dict[str, float]] = []
    try:
        lines = jsonl_lines(path.read_text(encoding="utf-8"))
    except OSError:
        return samples
    for line in lines:
        try:
            row = json.loads(line)
            ts, size = float(row["ts"]), float(row["bytes"])
        except (ValueError, KeyError, TypeError):
            continue
        samples.append({"ts": ts, "bytes": size})
    samples.sort(key=lambda sample: sample["ts"])
    return samples


def record_sample(path: Path, now: float, size: int) -> list[dict[str, float]]:
    """Append a sample (rate-limited), drop expired ones, and return the history."""
    history = read_history(path)
    if history and 0 <= now - history[-1]["ts"] < MIN_SAMPLE_INTERVAL_SECONDS:
        return history
    history.append({"ts": now, "bytes": float(size)})
    history = [sample for sample in history if now - sample["ts"] <= RETENTION_SECONDS]
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            for sample in history:
                handle.write(json.dumps({"ts": sample["ts"], "bytes": int(sample["bytes"])}) + "\n")
        os.replace(tmp_name, path)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise
    return history


def growth_over_window(history: list[dict[str, float]], now: float, current: int) -> tuple[int, float] | None:
    """Return ``(delta_bytes, span_seconds)`` against the oldest sample inside 24 h.

    ``None`` when no sample at least an hour old exists inside the window yet. The span is the
    real age of the baseline sample, so a short history is never presented as 24 h.
    """
    baseline = next((s for s in history if MIN_BASELINE_AGE_SECONDS <= now - s["ts"] <= WINDOW_SECONDS), None)
    if baseline is None:
        return None
    return int(current - baseline["bytes"]), now - baseline["ts"]


def _gb_from_env(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    return value if 0 <= value < float("inf") else default


def build_status(
    *,
    cache: Path,
    history_path: Path,
    now: float,
    size_fn: SizeFn = tree_size,
    record: bool = True,
) -> dict[str, object]:
    """Measure the cache, update the history, and evaluate the warning thresholds."""
    if not cache.is_dir():
        return {"present": False, "cache": str(cache), "warnings": []}
    size = size_fn(cache)
    history = record_sample(history_path, now, size) if record else read_history(history_path)
    # The sample just recorded is "now"; growth compares against earlier samples only.
    growth = growth_over_window([s for s in history if s["ts"] < now], now, size)
    warn_bytes = _gb_from_env("LU_UV_CACHE_WARN_GB", DEFAULT_WARN_GB) * GIB
    growth_warn_bytes = _gb_from_env("LU_UV_CACHE_GROWTH_WARN_GB", DEFAULT_GROWTH_WARN_GB) * GIB
    warnings: list[str] = []
    if size > warn_bytes:
        warnings.append(f"size above {warn_bytes / GIB:g} GiB")
    if growth is not None and growth[0] > growth_warn_bytes:
        warnings.append(f"growth above {growth_warn_bytes / GIB:g} GiB per 24 h")
    return {
        "present": True,
        "cache": str(cache),
        "bytes": size,
        "growth_bytes": None if growth is None else growth[0],
        "growth_span_seconds": None if growth is None else growth[1],
        "warnings": warnings,
    }


def _gib(value: float) -> str:
    return f"{value / GIB:.2f} GiB"


def format_line(status: dict[str, object]) -> str:
    """One human line; the cache path is intentionally not printed."""
    if not status["present"]:
        return "UV CACHE: not present"
    size = float(status["bytes"])  # type: ignore[arg-type]
    growth = status["growth_bytes"]
    if growth is None:
        growth_text = "growth n/a (history building)"
    else:
        span_h = float(status["growth_span_seconds"]) / 3600  # type: ignore[arg-type]
        window = "24h" if span_h >= 23.5 else f"{span_h:.1f}h"
        growth_text = f"{'+' if growth >= 0 else '-'}{_gib(abs(float(growth)))} over {window}"  # type: ignore[arg-type]
    line = f"UV CACHE: {_gib(size)}, {growth_text}"
    warnings = status["warnings"]
    if warnings:
        line += " [WARN: " + "; ".join(warnings) + "]"  # type: ignore[arg-type]
    return line


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only uv cache size and 24 h growth line.")
    parser.add_argument("--json", action="store_true", help="print the status as JSON")
    parser.add_argument("--no-record", action="store_true", help="do not append a history sample")
    args = parser.parse_args(argv)
    status = build_status(
        cache=uv_cache_dir(),
        history_path=state_dir() / HISTORY_FILENAME,
        now=time.time(),
        record=not args.no_record,
    )
    if args.json:
        safe = {key: value for key, value in status.items() if key != "cache"}
        print(json.dumps(safe, indent=1))
    else:
        print(format_line(status))
    return 0


if __name__ == "__main__":
    sys.exit(main())
