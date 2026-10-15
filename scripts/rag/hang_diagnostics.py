"""Thread dumps for a hung sources MCP server, and their retention (#10674).

The standalone server registers a ``faulthandler`` dump on ``SIGUSR1`` at
startup. ``faulthandler`` writes every thread's Python stack from inside the
signal handler without taking the GIL, so it still works when every thread,
including the event loop, is blocked on a lock. The call governor
(``scripts/rag/call_governor.py``) also writes ``slow-call-*.txt`` stacks
there for a call that runs too long.

The dump directory is ``LU_SOURCES_DUMP_DIR`` when set, otherwise
``batch_state/sources-dumps`` under the project root. The directory is ignored
by Git and owner-only. Stacks carry file names, line numbers and function
names, never argument values. Each writer calls ``prune_dump_dir`` after it
creates its file, so the directory stays bounded without any other process.
"""

from __future__ import annotations

import contextlib
import faulthandler
import os
import signal
from collections.abc import Mapping
from pathlib import Path
from typing import TextIO

DUMP_DIR_ENV = "LU_SOURCES_DUMP_DIR"
DEFAULT_DUMP_SUBDIR = Path("batch_state") / "sources-dumps"
DUMP_SIGNAL = signal.SIGUSR1
SLOW_CALL_PREFIX = "slow-call-"
DEFAULT_KEEP_DUMPS = 20
DEFAULT_MAX_DUMP_BYTES = 8 * 1024 * 1024

# faulthandler keeps its own reference, but the file object must stay open for
# the life of the process; keep one here too so it is never collected.
_DUMP_FILE: TextIO | None = None


def resolve_dump_dir(project_root: Path, environ: Mapping[str, str] | None = None) -> Path:
    environ = os.environ if environ is None else environ
    override = environ.get(DUMP_DIR_ENV, "").strip()
    return Path(override) if override else project_root / DEFAULT_DUMP_SUBDIR


def faulthandler_log_path(dump_dir: Path, pid: int) -> Path:
    return dump_dir / f"faulthandler-{pid}.log"


def ensure_dump_dir(dump_dir: Path) -> Path:
    dump_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(dump_dir, 0o700)
    return dump_dir


def prune_dump_dir(
    dump_dir: Path,
    *,
    keep: int | None = None,
    max_bytes: int | None = None,
    proc_root: Path = Path("/proc"),
) -> list[Path]:
    """Bound the dump directory; return what was removed.

    Keeps the newest ``keep`` slow-call dumps, then drops the oldest until
    the slow-call dumps total at most ``max_bytes`` (the newest is always
    kept), and removes the ``faulthandler-<pid>.log`` of processes that no
    longer exist. Defaults resolve at call time.
    """
    keep = DEFAULT_KEEP_DUMPS if keep is None else keep
    max_bytes = DEFAULT_MAX_DUMP_BYTES if max_bytes is None else max_bytes
    removed: list[Path] = []
    # The names carry a UTC stamp, so name order is age order.
    slow_calls = sorted(path for path in dump_dir.glob(f"{SLOW_CALL_PREFIX}*.txt") if path.is_file())
    for path in slow_calls[: max(0, len(slow_calls) - keep)]:
        path.unlink(missing_ok=True)
        removed.append(path)
    kept = slow_calls[max(0, len(slow_calls) - keep) :]
    sizes = [path.stat().st_size if path.exists() else 0 for path in kept]
    total = sum(sizes)
    for path, size in zip(kept[:-1], sizes, strict=False):
        if total <= max_bytes:
            break
        path.unlink(missing_ok=True)
        removed.append(path)
        total -= size
    for log in dump_dir.glob("faulthandler-*.log"):
        pid = log.stem.removeprefix("faulthandler-")
        if pid.isdigit() and not (proc_root / pid).exists():
            log.unlink(missing_ok=True)
            removed.append(log)
    return removed


def install_signal_dump(dump_dir: Path, *, signum: int = DUMP_SIGNAL) -> Path:
    """Register an all-thread stack dump on ``signum`` and on fatal signals.

    Returns the per-process log the dumps are appended to. The log starts
    empty (a reused pid's old log is dropped) and logs of dead processes are
    pruned, so the directory stays bounded.
    """
    global _DUMP_FILE
    ensure_dump_dir(dump_dir)
    path = faulthandler_log_path(dump_dir, os.getpid())
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_APPEND, 0o600)
    with contextlib.suppress(OSError):
        prune_dump_dir(dump_dir)
    handle = os.fdopen(fd, "a", encoding="utf-8")
    faulthandler.register(signum, file=handle, all_threads=True, chain=False)
    # A SIGABRT or a crash leaves the same evidence in the same file.
    faulthandler.enable(file=handle, all_threads=True)
    if _DUMP_FILE is not None and _DUMP_FILE is not handle:
        _DUMP_FILE.close()
    _DUMP_FILE = handle
    return path
