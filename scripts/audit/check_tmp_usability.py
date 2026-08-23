"""Detection probe for /tmp usability (#7164).

The job hosts mount ``/tmp`` as a small tmpfs with per-user quotas. When the
quota is exhausted every write fails with EDQUOT (os error 122) — invisible in
``df`` output and otherwise surfacing as unrelated crashes (installer core
dumps, empty logs, dead dispatch forwards). This probe makes that state
visible on the Monitor health surface: tmp usage figures plus a small
write-probe, with EDQUOT classified distinctly from ENOSPC and other errors.

Contract mirrors the other ``scripts/audit/check_*`` canaries: a pure
function returning a plain dict, no side effects beyond creating and removing
one tiny probe file, and no absolute host paths in the result (OPSEC).
"""

from __future__ import annotations

import contextlib
import errno
import os
import shutil
import tempfile
from pathlib import Path

PROBE_BYTES = 4096
_EDQUOT = getattr(errno, "EDQUOT", None)


def _classify_os_error(exc: OSError) -> str:
    """Classify a tmp write failure; EDQUOT (quota) must stay distinct."""
    if _EDQUOT is not None and exc.errno == _EDQUOT:
        return "edquot"
    if exc.errno == errno.ENOSPC:
        return "enospc"
    return f"oserror-{exc.errno}"


DEFAULT_TMP_PROBE_PATH = Path("/tmp")


def probe_tmp_usability(path: Path | None = None) -> dict:
    """Probe tmp usability: volume usage plus a small write test.

    Returns a body-free dict: ``ok``/``writable`` booleans, ``error``
    (None, ``edquot``, ``enospc``, or ``oserror-<n>``), and usage figures
    (``used_pct``, ``free_bytes``). Never raises on OSError — the failure IS
    the signal.
    """
    target = Path(path) if path is not None else DEFAULT_TMP_PROBE_PATH
    result: dict = {
        "ok": True,
        "writable": True,
        "error": None,
        "used_pct": None,
        "free_bytes": None,
    }
    try:
        usage = shutil.disk_usage(target)
    except OSError as exc:
        result.update(ok=False, writable=False, error=_classify_os_error(exc))
        return result
    result["used_pct"] = round(usage.used / usage.total * 100, 1) if usage.total else None
    result["free_bytes"] = usage.free

    probe_path: str | None = None
    try:
        fd, probe_path = tempfile.mkstemp(prefix=".lu-tmp-probe-", dir=target)
        try:
            os.write(fd, b"\0" * PROBE_BYTES)
        finally:
            os.close(fd)
    except OSError as exc:
        result.update(ok=False, writable=False, error=_classify_os_error(exc))
        return result
    finally:
        if probe_path is not None:
            with contextlib.suppress(OSError):
                os.unlink(probe_path)
    return result
