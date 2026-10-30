"""End dispatcher workers a test detached, including when the test process is killed.

``spawn_detached_worker`` and the provider ``Popen`` both use ``start_new_session``,
so the worker and its fake provider are their own sessions. The dispatch command
then exits and they are reparented to pid 1. The sandbox teardown used to
``cancel`` only a supervisor that was still the recorded process. That signal
never runs when pytest-timeout's thread method stops the test with ``os._exit``,
and it never reaches a provider whose supervisor was already killed. Both keep
running (the ``blocked`` stub waits forever).

Fixture teardown kills every process started from the test's temporary directory,
and the session leader's group when that process still leads it. The scan repeats,
because that leader can fork a new session after the snapshot and before the
signal. The root stays armed for the parent-death child until a scan sees nobody.
That child holds the other end of a pipe and does the same kill when the pipe
closes, which is what ``os._exit`` does to the test process.
"""

from __future__ import annotations

import contextlib
import ctypes
import os
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

# prctl(PR_SET_PDEATHSIG) — delivered when the parent exits, including os._exit.
_PR_SET_PDEATHSIG = 1


def _under(path: str, root: str) -> bool:
    path = path.removesuffix(" (deleted)")
    return path == root or path.startswith(root + os.sep)


def _fields(pid: int) -> list[str] | None:
    try:
        text = Path(f"/proc/{pid}/stat").read_text()
    except OSError:
        return None
    parts = text.rsplit(")", 1)
    if len(parts) != 2:
        return None
    fields = parts[1].split()
    return fields or None


def _pid_from_root(pid: int, root: str) -> bool:
    proc = Path(f"/proc/{pid}")
    try:
        cwd = os.readlink(proc / "cwd")
    except OSError:
        cwd = ""
    if _under(cwd, root):
        return True
    try:
        args = (proc / "cmdline").read_bytes().split(b"\0")
    except OSError:
        args = []
    return any(_under(arg.decode("utf-8", "surrogateescape"), root) for arg in args)


def pids_under(root: str, *, skip: set[int] | None = None) -> list[int]:
    """Live pids started from ``root`` (cwd or an argv path)."""
    skip = skip or set()
    found = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        if pid <= 1 or pid in skip:
            continue
        fields = _fields(pid)
        if fields is None or fields[0] == "Z":
            continue
        if _pid_from_root(pid, root):
            found.append(pid)
    return found


def _signal(found: list[int], own_group: int) -> None:
    leaders = []
    followers = []
    for pid in found:
        fields = _fields(pid)
        if fields is None or fields[0] == "Z":
            continue
        pgrp = int(fields[2])
        if pgrp == pid and pgrp != own_group and pgrp > 1:
            leaders.append(pid)
        else:
            followers.append(pid)
    for pid in leaders:
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.killpg(pid, signal.SIGKILL)
    for pid in followers:
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.kill(pid, signal.SIGKILL)
    for pid in found:
        with contextlib.suppress(ChildProcessError):
            os.waitpid(pid, os.WNOHANG)


def reap_root(root: Path | str, *, skip: set[int] | None = None) -> list[int]:
    """SIGKILL processes started from ``root``, including a session forked during the scan.

    One snapshot is not enough. The worker is in that snapshot and can fork a new
    session before the signal lands, and the signal is not visible in ``/proc``
    on the next scan. The pass repeats until a scan sees nobody, or the same
    pids survive several signals. A living group leader takes its group.
    Its group id is still its own pid, so ``killpg`` cannot hit a reused id.
    Followers are signalled individually: their group may be the test process.

    Returns every pid a scan found.
    """
    root = str(Path(root).resolve())
    skip = set(skip or ())
    skip.add(os.getpid())
    own_group = os.getpgrp()
    seen: list[int] = []
    last: set[int] | None = None
    repeats = 0
    while True:
        found = pids_under(root, skip=skip)
        if not found:
            return seen
        current = set(found)
        if current == last:
            repeats += 1
            # An unkillable pid must not hang teardown. A few repeats cover a
            # signal that has not shown up in /proc yet, and a child forked in
            # that window (its pid changes ``current`` and resets the count).
            if repeats >= 4:
                return seen
        else:
            repeats = 0
        last = current
        _signal(found, own_group)
        seen.extend(found)


def _reap_listed(path: str) -> None:
    try:
        text = Path(path).read_text()
    except OSError:
        return
    skip = {os.getpid()}
    for line in text.splitlines():
        root = line.split("\t", 1)[0]
        if root:
            reap_root(root, skip=skip)


def _watch(roots_path: str, parent_fd: int) -> None:
    def _parent_died(_signum, _frame):
        _reap_listed(roots_path)
        os._exit(0)

    signal.signal(signal.SIGTERM, _parent_died)
    ctypes.CDLL(None, use_errno=True).prctl(_PR_SET_PDEATHSIG, signal.SIGTERM, 0, 0, 0)
    if os.getppid() == 1:
        _parent_died(signal.SIGTERM, None)
    with contextlib.suppress(InterruptedError):
        os.read(parent_fd, 1)
    _reap_listed(roots_path)


class Reaper:
    """Tracks test temporary directories and ends processes started from them."""

    def __init__(self, temp: tempfile.TemporaryDirectory[str], roots: Path, proc, write_fd: int):
        self._temp: tempfile.TemporaryDirectory[str] | None = temp
        self.roots = roots
        self._proc = proc
        self._write_fd = write_fd
        self.active: dict[str, str] = {}
        self.history: dict[str, str] = {}

    @classmethod
    def start(cls) -> Reaper:
        from scripts.common.scratch import ensure_scratch_root

        temp = tempfile.TemporaryDirectory(prefix="dispatcher-worker-reap-", dir=ensure_scratch_root())
        try:
            state = Path(temp.name)
            roots = state / "roots"
            roots.write_text("")
            read_fd, write_fd = os.pipe()
            os.set_inheritable(write_fd, False)
            try:
                proc = subprocess.Popen(
                    [sys.executable, str(Path(__file__).resolve()), str(roots), str(read_fd)],
                    pass_fds=(read_fd,),
                    start_new_session=True,
                    cwd=state,
                    stdin=subprocess.DEVNULL,
                )
            except Exception:
                os.close(write_fd)
                raise
            finally:
                os.close(read_fd)
        except Exception:
            temp.cleanup()
            raise
        return cls(temp, roots, proc, write_fd)

    def _flush(self) -> None:
        text = "".join(f"{root}\t{nodeid}\n" for root, nodeid in self.active.items())
        temporary = self.roots.with_name("roots.tmp")
        temporary.write_text(text)
        os.replace(temporary, self.roots)

    def activate(self, root: Path, nodeid: str) -> None:
        resolved = str(root.resolve())
        self.history[resolved] = nodeid
        self.active[resolved] = nodeid
        self._flush()

    def reap(self, root: Path) -> None:
        resolved = str(root.resolve())
        self.history.setdefault(resolved, self.active.get(resolved, resolved))
        skip = {os.getpid(), self._proc.pid}
        reap_root(resolved, skip=skip)
        # A child forked after the last empty scan keeps the root armed for the
        # parent-death watchdog. Dropping it here is how that child survives os._exit.
        if pids_under(resolved, skip=skip):
            return
        self.active.pop(resolved, None)
        self._flush()

    def survivors(self) -> list[tuple[str, int]]:
        skip = {os.getpid(), self._proc.pid}
        seen: set[int] = set()
        found = []
        for root, nodeid in self.history.items():
            for pid in pids_under(root, skip=skip):
                if pid in seen:
                    continue
                seen.add(pid)
                found.append((nodeid, pid))
        return found

    def close(self) -> None:
        if self._write_fd is not None:
            os.close(self._write_fd)
            self._write_fd = None
        proc = self._proc
        self._proc = None
        if proc is not None:
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(proc.pid, signal.SIGKILL)
                proc.wait(timeout=5)
        temp = self._temp
        self._temp = None
        if temp is not None:
            temp.cleanup()

    def finish(self) -> None:
        """Raise when a test left a worker alive, after killing whatever remains."""
        died_early = self._proc is not None and self._proc.poll() is not None
        alive = self.survivors()
        try:
            for root in list(self.history):
                reap_root(root, skip={os.getpid(), self._proc.pid})
        finally:
            self.close()
        if not alive and not died_early:
            return
        parts = []
        if died_early:
            parts.append("dispatcher worker reap died before session end")
        if alive:
            detail = ", ".join(f"{nodeid} pid {pid}" for nodeid, pid in alive)
            parts.append(f"Defect class: a test leaks a detached worker process: {detail}")
        raise AssertionError("; ".join(parts))


if __name__ == "__main__":
    try:
        _watch(sys.argv[1], int(sys.argv[2]))
    finally:
        os._exit(0)
