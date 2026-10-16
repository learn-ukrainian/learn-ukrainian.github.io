#!/usr/bin/env python3
"""Read-only uv cache size and 24-hour growth line for ``lu-driver-status`` (#10779).

The uv cache grows without bound on a busy host (every resolved wheel and
sdist build stays). This module measures it, keeps a small timestamped size
history, and renders one status line with a warning threshold. It never deletes
anything from the cache; the only files it writes are the size history and its
lock, and never inside the cache.

The size comes from ``du -sk`` in its own process group with a deadline, so a
huge or stalled cache cannot hang the status command; a timeout or a failed
measurement prints an explicit line and records no sample. The history lock is
taken without blocking and retried until its own deadline; when another writer
holds it past that, the line says so and no sample is recorded.

The history directory is resolved and checked once, then held open; every
history read and write is relative to that descriptor, so retargeting a
symlink after the check cannot move the writes into the cache.

Usage: ``.venv/bin/python -m scripts.hygiene.uv_cache_status [--json] [--no-record]``

Environment (all optional):
- ``UV_CACHE_DIR`` / ``XDG_CACHE_HOME``: where the cache lives (uv's own rules).
- ``LU_DRIVER_STATUS_STATE_DIR``: history directory (default: the driver-keeper
  state directory that ``lu-driver-status`` already reads).
- ``LU_UV_CACHE_WARN_GB``: absolute-size warning threshold (default 10).
- ``LU_UV_CACHE_GROWTH_WARN_GB``: 24-hour growth warning threshold (default 2).
- ``LU_UV_CACHE_SCAN_TIMEOUT_S``: measurement deadline in seconds (default 8).
- ``LU_UV_CACHE_LOCK_TIMEOUT_S``: history-lock deadline in seconds (default 2).

Exit codes: 0 status printed (including "size unavailable", "measurement
failed" and "history busy"); 2 refused because the history directory is a
symlink, the cache, or inside it.
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import json
import os
import signal
import stat
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path

from scripts.common.jsonl import jsonl_lines

HISTORY_FILENAME = "uv-cache-size.jsonl"
LOCK_SUFFIX = ".lock"
WINDOW_SECONDS = 24 * 3600
# Keep a week of samples; the status line only needs the last day.
RETENTION_SECONDS = 7 * 24 * 3600
# One sample per interval at most, so a polling status command cannot bloat the file.
MIN_SAMPLE_INTERVAL_SECONDS = 600
# A baseline younger than this says nothing about growth; report "history building".
MIN_BASELINE_AGE_SECONDS = 3600
DEFAULT_WARN_GB = 10.0
DEFAULT_GROWTH_WARN_GB = 2.0
DEFAULT_SCAN_TIMEOUT_S = 8.0
DEFAULT_LOCK_TIMEOUT_S = 2.0
# Pause between non-blocking attempts on a busy history lock.
LOCK_RETRY_SECONDS = 0.05
# After a timeout the killed du gets this long to exit before it is abandoned.
KILL_GRACE_SECONDS = 1.0
GIB = 1024**3

SizeFn = Callable[[Path], int]


class ScanTimeout(Exception):
    """The size measurement did not finish before its deadline."""

    def __init__(self, timeout_s: float) -> None:
        super().__init__(f"scan exceeded {timeout_s:g}s")
        self.timeout_s = timeout_s


class MeasurementError(Exception):
    """The size measurement failed; its result is not a usable sample."""


class HistoryBusy(Exception):
    """Another writer held the history lock past the lock deadline."""

    def __init__(self, timeout_s: float) -> None:
        super().__init__(f"lock held by another writer for {timeout_s:g}s")
        self.timeout_s = timeout_s


class HistoryLocationError(Exception):
    """The history directory is a symlink, the cache, or inside the cache."""


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


def _seconds_from_env(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    return value if 0 < value < float("inf") else default


def scan_timeout_seconds() -> float:
    return _seconds_from_env("LU_UV_CACHE_SCAN_TIMEOUT_S", DEFAULT_SCAN_TIMEOUT_S)


def lock_timeout_seconds() -> float:
    return _seconds_from_env("LU_UV_CACHE_LOCK_TIMEOUT_S", DEFAULT_LOCK_TIMEOUT_S)


def _du_reason(stderr: str) -> str:
    """The error text of du's last message, without the path it names."""
    lines = [line for line in stderr.strip().split("\n") if line.strip()]
    return lines[-1].rsplit(": ", 1)[-1].strip() if lines else "no diagnostic"


def measure_bytes(root: Path, timeout_s: float | None = None) -> int:
    """Allocated bytes under ``root`` via ``du -sk``, within ``timeout_s``.

    ``du`` counts hardlinks once and never follows symlinks below ``root``. It
    runs in its own process group; on timeout the group is killed while the
    leader is still unreaped (so its id cannot have been reused) and
    ``ScanTimeout`` is raised. Any error from ``du``, including an unreadable
    directory that would make the total partial, raises ``MeasurementError``.
    """
    if timeout_s is None:
        timeout_s = scan_timeout_seconds()
    try:
        process = subprocess.Popen(
            ["du", "-sk", "--", str(root)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env={**os.environ, "LC_ALL": "C"},
            start_new_session=True,
        )
    except OSError as error:
        raise MeasurementError(f"du: {error.strerror or error}") from error
    try:
        stdout, stderr = process.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
        # A du stuck in uninterruptible I/O is abandoned rather than waited for.
        with contextlib.suppress(subprocess.TimeoutExpired):
            process.communicate(timeout=KILL_GRACE_SECONDS)
        raise ScanTimeout(timeout_s) from None
    if process.returncode != 0:
        raise MeasurementError(f"du exit {process.returncode}: {_du_reason(stderr)}")
    try:
        return int(stdout.split(None, 1)[0]) * 1024
    except (IndexError, ValueError):
        raise MeasurementError("du printed no size") from None


def read_history(dir_fd: int | None) -> list[dict[str, float]]:
    """Return valid ``{"ts", "bytes"}`` samples, oldest first; bad lines are skipped.

    ``dir_fd`` is the bound history directory (``None``: no history yet).
    """
    samples: list[dict[str, float]] = []
    if dir_fd is None:
        return samples
    try:
        fd = os.open(HISTORY_FILENAME, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=dir_fd)
    except OSError:
        return samples
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            return samples
        with os.fdopen(os.dup(fd), encoding="utf-8") as handle:
            lines = jsonl_lines(handle.read())
    except (OSError, UnicodeDecodeError):
        return samples
    finally:
        os.close(fd)
    for line in lines:
        try:
            row = json.loads(line)
            ts, size = float(row["ts"]), float(row["bytes"])
        except (ValueError, KeyError, TypeError):
            continue
        samples.append({"ts": ts, "bytes": size})
    samples.sort(key=lambda sample: sample["ts"])
    return samples


def _lock_history(lock_fd: int, timeout_s: float) -> None:
    """Take the exclusive history lock, never blocking past ``timeout_s``."""
    deadline = time.monotonic() + timeout_s
    while True:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return
        except BlockingIOError:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise HistoryBusy(timeout_s) from None
            time.sleep(min(LOCK_RETRY_SECONDS, remaining))


def record_sample(dir_fd: int, now: float, size: int, *, lock_timeout_s: float | None = None) -> list[dict[str, float]]:
    """Add a sample (rate-limited), drop expired ones, and return the history.

    Every file operation is relative to ``dir_fd``, the bound history directory
    (see ``open_history_dir``). The read-modify-replace runs under an exclusive
    ``flock`` on a lock file beside the history, so concurrent writers
    serialize and none replaces the file with a copy that lacks another
    writer's newer sample. Raises ``HistoryBusy`` when the lock stays held past
    ``lock_timeout_s`` (default ``LU_UV_CACHE_LOCK_TIMEOUT_S``).
    """
    if lock_timeout_s is None:
        lock_timeout_s = lock_timeout_seconds()
    lock_fd = os.open(
        HISTORY_FILENAME + LOCK_SUFFIX, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=dir_fd
    )
    try:
        _lock_history(lock_fd, lock_timeout_s)
        history = read_history(dir_fd)
        if any(abs(now - sample["ts"]) < MIN_SAMPLE_INTERVAL_SECONDS for sample in history):
            return history
        history.append({"ts": now, "bytes": float(size)})
        history = sorted(
            (sample for sample in history if now - sample["ts"] <= RETENTION_SECONDS),
            key=lambda sample: sample["ts"],
        )
        tmp_name = f".{HISTORY_FILENAME}.{os.getpid()}.{os.urandom(6).hex()}.tmp"
        fd = os.open(
            tmp_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=dir_fd
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                for sample in history:
                    handle.write(json.dumps({"ts": sample["ts"], "bytes": int(sample["bytes"])}) + "\n")
            os.replace(tmp_name, HISTORY_FILENAME, src_dir_fd=dir_fd, dst_dir_fd=dir_fd)
        except BaseException:
            with contextlib.suppress(FileNotFoundError):
                os.unlink(tmp_name, dir_fd=dir_fd)
            raise
        return history
    finally:
        os.close(lock_fd)


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


def history_inside_cache(cache: Path, history_dir: Path) -> bool:
    """True when ``history_dir`` is ``cache`` or lies inside it, symlinks resolved."""
    resolved_cache = cache.resolve()
    resolved_history = history_dir.resolve()
    return resolved_history == resolved_cache or resolved_cache in resolved_history.parents


_DirIdentity = tuple[int, int]
_INSIDE_CACHE = "the history directory is the uv cache or inside it"


def bound_dir_inside_cache(
    chain: list[_DirIdentity], bound_path: Path, cache_identity: _DirIdentity | None, cache_real: Path
) -> bool:
    """True when an opened history directory is the cache or inside it.

    ``chain`` holds the ``(st_dev, st_ino)`` of every directory opened from
    ``/`` down to the history directory; ``bound_path`` is the kernel's path of
    the final descriptor (``/proc/self/fd``). Either view naming the cache is
    enough to refuse.
    """
    if cache_identity is not None and cache_identity in chain:
        return True
    return bound_path == cache_real or cache_real in bound_path.parents


def open_history_dir(cache: Path, history_dir: Path, *, create: bool) -> int | None:
    """Resolve, check and open the history directory once; return its descriptor.

    The configured directory itself must not be a symlink. Its path is resolved
    once, then opened one component at a time from ``/`` with ``O_NOFOLLOW``,
    and every directory on the way is compared with the cache's device and
    inode before anything is created in it (missing components are created
    with mode 0700, only when ``create``). The final descriptor's kernel path
    is checked too. Returns ``None`` when the directory does not exist and
    ``create`` is false. Raises ``HistoryLocationError``, having written
    nothing, when the directory is a symlink, the cache, inside the cache, or
    its path changed while it was being opened.
    """
    if history_dir.is_symlink():
        raise HistoryLocationError("the history directory is a symlink")
    try:
        cache_info = os.stat(cache)
        cache_identity: _DirIdentity | None = (cache_info.st_dev, cache_info.st_ino)
    except OSError:
        cache_identity = None
    cache_real = Path(os.path.realpath(cache))
    resolved = Path(os.path.realpath(history_dir))
    if history_inside_cache(cache, resolved):
        raise HistoryLocationError(_INSIDE_CACHE)
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    fd = os.open("/", flags)
    chain: list[_DirIdentity] = []
    try:
        for part in resolved.parts[1:]:
            info = os.fstat(fd)
            chain.append((info.st_dev, info.st_ino))
            if cache_identity in chain:
                raise HistoryLocationError(_INSIDE_CACHE)
            try:
                next_fd = os.open(part, flags, dir_fd=fd)
            except FileNotFoundError:
                if not create:
                    os.close(fd)
                    return None
                with contextlib.suppress(FileExistsError):
                    os.mkdir(part, 0o700, dir_fd=fd)
                next_fd = os.open(part, flags, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        info = os.fstat(fd)
        chain.append((info.st_dev, info.st_ino))
        if bound_dir_inside_cache(chain, Path(os.readlink(f"/proc/self/fd/{fd}")), cache_identity, cache_real):
            raise HistoryLocationError(_INSIDE_CACHE)
    except OSError as error:
        os.close(fd)
        raise HistoryLocationError(f"the history directory could not be opened safely ({error.strerror})") from None
    except BaseException:
        os.close(fd)
        raise
    return fd


def build_status(
    *,
    cache: Path,
    history_dir_fd: int | None,
    now: float,
    size_fn: SizeFn | None = None,
    record: bool = True,
) -> dict[str, object]:
    """Measure the cache, update the history, and evaluate the warning thresholds.

    ``history_dir_fd`` is the bound history directory (see
    ``open_history_dir``; ``None`` when it does not exist). A timed-out or
    failed measurement returns an ``unavailable`` or ``error`` status and
    records no sample; a busy history lock returns the measurement with
    ``history_busy`` and records no sample.
    """
    if not cache.is_dir():
        return {"present": False, "cache": str(cache), "warnings": []}
    try:
        size = (size_fn or measure_bytes)(cache)
    except ScanTimeout as timeout:
        return {"present": True, "cache": str(cache), "unavailable": str(timeout), "warnings": []}
    except (MeasurementError, OSError) as error:
        return {"present": True, "cache": str(cache), "error": str(error), "warnings": []}
    if record and history_dir_fd is not None:
        try:
            history = record_sample(history_dir_fd, now, size)
        except HistoryBusy as busy:
            return {"present": True, "cache": str(cache), "bytes": size, "history_busy": str(busy), "warnings": []}
    else:
        history = read_history(history_dir_fd)
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
    if "unavailable" in status:
        return f"UV CACHE: size unavailable ({status['unavailable']})"
    if "error" in status:
        return f"UV CACHE: measurement failed ({status['error']})"
    size = float(status["bytes"])  # type: ignore[arg-type]
    if "history_busy" in status:
        return f"UV CACHE: history busy ({status['history_busy']}); {_gib(size)} measured, no sample recorded"
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
    cache, history_dir = uv_cache_dir(), state_dir()
    try:
        history_fd = open_history_dir(cache, history_dir, create=not args.no_record and cache.is_dir())
    except HistoryLocationError as refusal:
        print(f"UV CACHE: refusing to run: {refusal} (LU_DRIVER_STATUS_STATE_DIR)", file=sys.stderr)
        return 2
    try:
        status = build_status(cache=cache, history_dir_fd=history_fd, now=time.time(), record=not args.no_record)
    finally:
        if history_fd is not None:
            os.close(history_fd)
    if args.json:
        safe = {key: value for key, value in status.items() if key != "cache"}
        print(json.dumps(safe, indent=1))
    else:
        print(format_line(status))
    return 0


if __name__ == "__main__":
    sys.exit(main())
