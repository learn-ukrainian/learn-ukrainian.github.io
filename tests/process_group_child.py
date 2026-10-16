"""Run a test's child command in its own process group and leave nothing behind (#10777).

``subprocess.run(timeout=)`` kills only the direct child, and only when the
calling test is still alive to do it. pytest-timeout's thread method ends an
xdist worker with ``os._exit``, so a collection child it was waiting for kept
running after the worker died, and the pre-push gate refused the push for the
process left in its scope (``scope_cleanup_unverified``).

:func:`run_in_process_group` starts a small supervisor as the leader of a new
session. The supervisor runs the command in that group and kills the whole
group when the test process dies (``PR_SET_PDEATHSIG``, Linux). The caller
kills the group on every exit path, after a timeout, an exception or a normal
exit, while the exited leader is still unreaped, so the group id cannot have
been reused.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import tempfile
import textwrap
import time
from collections.abc import Mapping, Sequence
from contextlib import suppress
from pathlib import Path

_POLL_S = 0.05
_REAP_TIMEOUT_S = 10

# Runs in the child with ``-I``: the parent pid, then the command.
_SUPERVISOR = textwrap.dedent(
    """
    import ctypes
    import os
    import signal
    import subprocess
    import sys


    def kill_group(*_args):
        os.killpg(0, signal.SIGKILL)


    signal.signal(signal.SIGTERM, kill_group)
    signal.signal(signal.SIGHUP, kill_group)
    try:
        # PR_SET_PDEATHSIG (1): SIGTERM here when the test process dies.
        ctypes.CDLL(None, use_errno=True).prctl(1, signal.SIGTERM, 0, 0, 0)
    except (AttributeError, OSError):
        pass
    if os.getppid() != int(sys.argv[1]):
        # The test process died before the death signal was armed.
        kill_group()
    status = subprocess.call(sys.argv[2:])
    if status < 0:
        signal.signal(-status, signal.SIG_DFL)
        os.kill(os.getpid(), -status)
    sys.exit(status)
    """
)


def _exited(pid: int) -> bool:
    """True once ``pid`` has exited; the exit status stays unreaped (``WNOWAIT``)."""
    return os.waitid(os.P_PID, pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is not None


def run_in_process_group(
    args: Sequence[str],
    *,
    timeout: float,
    cwd: Path | str | None = None,
    env: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run ``args`` like ``subprocess.run(args, capture_output=True, text=True, timeout=timeout)``.

    Raises :class:`subprocess.TimeoutExpired` after ``timeout`` seconds, as
    ``subprocess.run`` does. Whatever happens, no process of the command's
    group outlives the call, and none outlives the calling process.
    """
    command = [sys.executable, "-I", "-c", _SUPERVISOR, str(os.getpid()), *args]
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        process = subprocess.Popen(command, cwd=cwd, env=env, stdout=stdout, stderr=stderr, start_new_session=True)
        deadline = time.monotonic() + timeout
        timed_out = False
        try:
            while not _exited(process.pid):
                if time.monotonic() >= deadline:
                    timed_out = True
                    break
                time.sleep(_POLL_S)
        finally:
            # The leader is a zombie or alive here, so its group id is still its own.
            with suppress(ProcessLookupError, PermissionError):
                os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=_REAP_TIMEOUT_S)
        stdout.seek(0)
        stderr.seek(0)
        out = stdout.read().decode("utf-8", "replace")
        err = stderr.read().decode("utf-8", "replace")
    if timed_out:
        raise subprocess.TimeoutExpired(list(args), timeout, output=out, stderr=err)
    return subprocess.CompletedProcess(list(args), process.returncode, out, err)
