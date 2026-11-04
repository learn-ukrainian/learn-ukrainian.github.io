"""Thread dumps for a hung sources MCP server (#10674).

The standalone server registers a ``faulthandler`` dump on ``SIGUSR1`` at
startup. ``faulthandler`` writes every thread's Python stack from inside the
signal handler without taking the GIL, so it still works when every thread,
including the event loop, is blocked on a lock. The watchdog
(``scripts/orchestration/sources_watchdog.py``) sends the signal and copies
the new bytes into an incident directory before it restarts the service.

Both sides find the dump directory the same way: ``LU_SOURCES_DUMP_DIR`` when
set, otherwise ``batch_state/sources-dumps`` under the project root. The
directory is ignored by Git and owner-only. Stacks carry file names, line
numbers and function names, never argument values.
"""

from __future__ import annotations

import faulthandler
import os
from pathlib import Path
from typing import TextIO

from scripts.curriculum import readiness_gates

# faulthandler keeps its own reference, but the file object must stay open for
# the life of the process; keep one here too so it is never collected.
_DUMP_FILE: TextIO | None = None


def install_signal_dump(dump_dir: Path, *, signum: int = readiness_gates.DUMP_SIGNAL) -> Path:
    """Register an all-thread stack dump on ``signum`` and on fatal signals.

    Returns the per-process log the dumps are appended to.
    """
    global _DUMP_FILE
    readiness_gates.ensure_dump_dir(dump_dir)
    path = readiness_gates.faulthandler_log_path(dump_dir, os.getpid())
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    handle = os.fdopen(fd, "a", encoding="utf-8")
    faulthandler.register(signum, file=handle, all_threads=True, chain=False)
    # A watchdog SIGABRT or a crash leaves the same evidence in the same file.
    faulthandler.enable(file=handle, all_threads=True)
    if _DUMP_FILE is not None and _DUMP_FILE is not handle:
        _DUMP_FILE.close()
    _DUMP_FILE = handle
    return path
