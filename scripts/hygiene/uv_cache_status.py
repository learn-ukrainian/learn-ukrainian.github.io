#!/usr/bin/env python3
"""Measure uv cache size and growth without deleting cache content (#10827).

Threat model: accidental misconfiguration and cooperative concurrent writers.
Exactly one owner, the keeper, invokes --record-history on its own cadence.
Status readers never write history, locks or temporary files. Both modes use
an explicitly supplied keeper state directory, validated before any writes.
Recording serializes cooperative invocations and atomically replaces history.

Symlink retargeting after validation stays bound to the opened directory, but
moving that directory, adding hard links, or adding a hard link and unlinking
the original name during a write is outside this threat model. These are the
four recorded race classes. Restrictive permissions, directory descriptors and
atomic rename do not prevent hostile same-user relocation or aliasing.

UV_CACHE_DIR / XDG_CACHE_HOME select the cache. --state-dir or
LU_DRIVER_STATUS_STATE_DIR must name the keeper's configured state_dir.
LU_UV_CACHE_WARN_GB (10) and LU_UV_CACHE_GROWTH_WARN_GB (2) set warnings.
LU_UV_CACHE_SCAN_TIMEOUT_S (8) bounds du; LU_UV_CACHE_LOCK_TIMEOUT_S (2)
bounds cooperative lock retries. A synchronous filesystem call can outlast a
deadline. History samples are at least 10 minutes apart and retained one week.
See docs/runbooks/tmp-retention.md for the host wiring contract and limits.
"""

from __future__ import annotations

import argparse
import contextlib
import errno
import fcntl
import json
import math
import os
import signal
import stat
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import NamedTuple

REPO_ROOT = Path(__file__).resolve().parents[2]

# Ensure repo scripts/ is importable when invoked as a file path.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

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
    """The history directory (or its lock file) may not be written where it is."""


def uv_cache_dir() -> Path:
    """Resolve the uv cache directory the way uv does (no subprocess)."""
    explicit = os.environ.get("UV_CACHE_DIR")
    if explicit:
        return Path(explicit).expanduser()
    xdg = os.environ.get("XDG_CACHE_HOME")
    base = Path(xdg).expanduser() if xdg else Path.home() / ".cache"
    return base / "uv"


def state_dir() -> Path | None:
    explicit = os.environ.get("LU_DRIVER_STATUS_STATE_DIR")
    return Path(explicit).expanduser() if explicit else None


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

    ``du`` counts hardlinks once and never follows symlinks below ``root``;
    ``root`` itself is followed (``-H``), so a symlinked cache is measured
    where it points rather than as the link. It runs in its own process group; on timeout the group is killed while the
    leader is still unreaped (so its id cannot have been reused) and
    ``ScanTimeout`` is raised. Any error from ``du``, including an unreadable
    directory that would make the total partial, raises ``MeasurementError``.
    """
    if timeout_s is None:
        timeout_s = scan_timeout_seconds()
    try:
        process = subprocess.Popen(
            ["du", "-skH", "--", str(root)],
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


class HistoryUnavailable(Exception):
    """No usable history can be read; this must not look like zero growth."""


def read_history(dir_fd: int | None) -> list[dict[str, float]]:
    """Read valid finite samples, oldest first; missing or unusable history is explicit."""
    if dir_fd is None:
        raise HistoryUnavailable("state directory unavailable")
    try:
        fd = os.open(HISTORY_FILENAME, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=dir_fd)
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise HistoryUnavailable("history is not a regular file")
            with os.fdopen(os.dup(fd), encoding="utf-8") as handle:
                lines = jsonl_lines(handle.read())
        finally:
            os.close(fd)
    except (OSError, UnicodeDecodeError):
        raise HistoryUnavailable("history missing or unreadable") from None
    samples: list[dict[str, float]] = []
    for line in lines:
        try:
            row = json.loads(line)
            ts, size = float(row["ts"]), float(row["bytes"])
        except (ValueError, KeyError, TypeError):
            continue
        if math.isfinite(ts) and math.isfinite(size) and ts >= 0 and size >= 0:
            samples.append({"ts": ts, "bytes": size})
    if not samples:
        raise HistoryUnavailable("history has no usable samples")
    return sorted(samples, key=lambda sample: sample["ts"])


def _lock_history(lock_fd: int, deadline: float, timeout_s: float) -> None:
    """Take the exclusive history lock, never blocking past the monotonic ``deadline``."""
    while True:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return
        except BlockingIOError:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise HistoryBusy(timeout_s) from None
            time.sleep(min(LOCK_RETRY_SECONDS, remaining))


def _require_single_link(fd: int, what: str) -> None:
    """Refuse the open file ``fd`` when it has another name, which may lie inside the cache."""
    if os.fstat(fd).st_nlink != 1:
        raise HistoryLocationError(f"the {what} has more than one link")


def _open_lock(dir_fd: int, deadline: float, timeout_s: float) -> tuple[int, bool]:
    """Open a regular, unaliased lock with a bounded retry deadline."""
    base = os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC
    name = HISTORY_FILENAME + LOCK_SUFFIX
    while True:
        try:
            fd, created = os.open(name, base | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=dir_fd), True
        except FileExistsError:
            try:
                fd, created = os.open(name, base, dir_fd=dir_fd), False
            except FileNotFoundError:
                # Removed between the two opens; try to create it again while time remains.
                if time.monotonic() >= deadline:
                    raise HistoryBusy(timeout_s) from None
                continue
            except OSError as error:
                if error.errno == errno.ELOOP:
                    raise HistoryLocationError("the history lock file is a symlink") from None
                if error.errno == errno.EISDIR:
                    raise HistoryLocationError("the history lock file is not a regular file") from None
                raise
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise HistoryLocationError("the history lock file is not a regular file")
            _require_single_link(fd, "history lock file")
        except HistoryLocationError:
            if created:
                _unlink_if_same(name, fd, dir_fd)
            os.close(fd)
            raise
        return fd, created


def _unlink_if_same(name: str, fd: int, dir_fd: int) -> None:
    """Remove ``name`` from ``dir_fd`` only while it is still the file open as ``fd``."""
    with contextlib.suppress(OSError):
        held = os.fstat(fd)
        current = os.stat(name, dir_fd=dir_fd, follow_symlinks=False)
        if (current.st_dev, current.st_ino) == (held.st_dev, held.st_ino):
            os.unlink(name, dir_fd=dir_fd)


def record_sample(
    dir_fd: int,
    now: float,
    size: int,
    *,
    lock_timeout_s: float | None = None,
) -> list[dict[str, float]]:
    """Keeper-only atomic update, serialized against cooperative invocations.

    The caller validates and opens its configured directory once before entry.
    No concurrent actor may move, unlink, or alias the directory or its files.
    """
    if lock_timeout_s is None:
        lock_timeout_s = lock_timeout_seconds()
    deadline = time.monotonic() + lock_timeout_s
    lock_fd, _ = _open_lock(dir_fd, deadline, lock_timeout_s)
    try:
        _lock_history(lock_fd, deadline, lock_timeout_s)
        try:
            history = read_history(dir_fd)
        except HistoryUnavailable:
            history = []
        if any(abs(now - sample["ts"]) < MIN_SAMPLE_INTERVAL_SECONDS for sample in history):
            return history
        history.append({"ts": now, "bytes": float(size)})
        history = sorted(
            (sample for sample in history if now - sample["ts"] <= RETENTION_SECONDS),
            key=lambda sample: sample["ts"],
        )
        payload = "".join(
            json.dumps({"ts": sample["ts"], "bytes": int(sample["bytes"])}) + "\n" for sample in history
        ).encode("utf-8")
        tmp_name = f".{HISTORY_FILENAME}.{os.getpid()}.{os.urandom(6).hex()}.tmp"
        fd = os.open(
            tmp_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=dir_fd
        )
        try:
            try:
                view = memoryview(payload)
                while view:
                    written = os.write(fd, view)
                    if written == 0:
                        raise OSError("history write made no progress")
                    view = view[written:]
                os.fsync(fd)
            finally:
                os.close(fd)
            os.replace(tmp_name, HISTORY_FILENAME, src_dir_fd=dir_fd, dst_dir_fd=dir_fd)
            os.fsync(dir_fd)
        finally:
            with contextlib.suppress(FileNotFoundError):
                os.unlink(tmp_name, dir_fd=dir_fd)
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
    for root, destination in ((cache.absolute(), history_dir.absolute()), (cache.resolve(), history_dir.resolve())):
        if destination == root or root in destination.parents:
            return True
    return False


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


class BoundHistoryDir(NamedTuple):
    """An opened history directory and the resolved path it was opened at."""

    fd: int
    path: Path


def validate_history_files(dir_fd: int) -> None:
    """Refuse preconfigured file aliases before creating any lock or temporary file."""
    for name, label in ((HISTORY_FILENAME, "history file"), (HISTORY_FILENAME + LOCK_SUFFIX, "history lock file")):
        try:
            info = os.stat(name, dir_fd=dir_fd, follow_symlinks=False)
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode):
            raise HistoryLocationError(f"the {label} is a symlink")
        if not stat.S_ISREG(info.st_mode):
            raise HistoryLocationError(f"the {label} is not a regular file")
        if info.st_nlink != 1:
            raise HistoryLocationError(f"the {label} has more than one link")


def open_history_dir(cache: Path, history_dir: Path, *, create: bool) -> BoundHistoryDir | None:
    """Validate configuration once and bind all operations to one directory.

    Ancestor identities also catch cache directory aliases. No location polling
    or hostile same-user mutation guarantee is made after this boundary.
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
    if history_inside_cache(cache, history_dir):
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
        bound = BoundHistoryDir(fd, resolved)
        validate_history_files(fd)
    except OSError as error:
        os.close(fd)
        raise HistoryLocationError(f"the history directory could not be opened safely ({error.strerror})") from None
    except BaseException:
        os.close(fd)
        raise
    return bound


def build_status(
    *,
    cache: Path,
    history_dir_fd: int | None,
    now: float,
    size_fn: SizeFn | None = None,
    record: bool = False,
) -> dict[str, object]:
    """Measure and render status; only an explicit keeper call records history."""
    if not cache.is_dir():
        return {"present": False, "cache": str(cache), "warnings": []}
    try:
        size = (size_fn or measure_bytes)(cache)
    except ScanTimeout as timeout:
        return {"present": True, "cache": str(cache), "unavailable": str(timeout), "warnings": []}
    except (MeasurementError, OSError) as error:
        return {"present": True, "cache": str(cache), "error": str(error), "warnings": []}
    history: list[dict[str, float]] = []
    history_state: dict[str, object] = {}
    try:
        if record and history_dir_fd is not None:
            history = record_sample(history_dir_fd, now, size)
        else:
            history = read_history(history_dir_fd)
    except HistoryBusy as busy:
        history_state["history_busy"] = str(busy)
    except (HistoryUnavailable, OSError):
        history_state["history_unavailable"] = True
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
        **history_state,
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
    growth = status["growth_bytes"]
    if "history_busy" in status:
        growth_text = f"history busy ({status['history_busy']}); no sample recorded"
    elif "history_unavailable" in status:
        growth_text = "growth n/a (history unavailable)"
    elif growth is None:
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
    parser = argparse.ArgumentParser(
        description="Measure uv cache size and growth without deleting cache content.\n"
        "Use status mode for readers; reserve --record-history for the keeper's cadence.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python -m scripts.hygiene.uv_cache_status --state-dir "$KEEPER_STATE_DIR"
  .venv/bin/python -m scripts.hygiene.uv_cache_status --record-history --state-dir "$KEEPER_STATE_DIR"
  .venv/bin/python -m scripts.hygiene.uv_cache_status --json
Outputs: status on stdout. Only --record-history creates the state directory,
  uv-cache-size.jsonl, its lock and temporary files beside history. No cache deletion.
Exit codes: 0 status printed, including timeout, unavailable history or busy lock;
  2 unsafe history configuration or recording without an explicit state directory.
Related: docs/runbooks/tmp-retention.md; #10827.
""",
    )
    parser.add_argument("--json", action="store_true", help="print JSON instead of a status line (default: line)")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--record-history", action="store_true", help="keeper-only history update (default: read-only)")
    modes.add_argument("--no-record", action="store_true", help="explicit read-only status (the default)")
    parser.add_argument(
        "--state-dir",
        type=Path,
        help="keeper state_dir, e.g. ./keeper-state (default: LU_DRIVER_STATUS_STATE_DIR; otherwise unavailable)",
    )
    args = parser.parse_args(argv)
    cache = uv_cache_dir()
    history_dir = args.state_dir.expanduser() if args.state_dir is not None else state_dir()
    if args.record_history and history_dir is None:
        print(
            "UV CACHE: refusing to run: --record-history requires --state-dir or LU_DRIVER_STATUS_STATE_DIR",
            file=sys.stderr,
        )
        return 2
    bound: BoundHistoryDir | None = None
    try:
        if history_dir is not None:
            bound = open_history_dir(cache, history_dir, create=args.record_history and cache.is_dir())
        status = build_status(
            cache=cache,
            history_dir_fd=None if bound is None else bound.fd,
            now=time.time(),
            record=args.record_history,
        )
    except (HistoryLocationError, OSError, RuntimeError) as refusal:
        # Never include configured paths or raw OS diagnostics in status output.
        reason = str(refusal) if isinstance(refusal, HistoryLocationError) else "history configuration unavailable"
        print(f"UV CACHE: refusing to run: {reason} (LU_DRIVER_STATUS_STATE_DIR)", file=sys.stderr)
        return 2
    finally:
        if bound is not None:
            os.close(bound.fd)
    if args.json:
        safe = {key: value for key, value in status.items() if key != "cache"}
        print(json.dumps(safe, indent=1))
    else:
        print(format_line(status))
    return 0


if __name__ == "__main__":
    sys.exit(main())
