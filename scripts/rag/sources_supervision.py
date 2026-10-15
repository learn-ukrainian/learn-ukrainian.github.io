"""systemd readiness and watchdog pings for the standalone sources MCP server (#10674).

``packaging/systemd/learn-ukrainian-sources.service`` runs the server as
``Type=notify`` with ``WatchdogSec=``. This module speaks the notification
protocol with the standard library only (sd_notify(3): one datagram per
message to ``$NOTIFY_SOCKET``, a path or a Linux abstract socket written
``@name``) and decides when the server is alive enough to say so:

- ``READY=1`` goes out once, after uvicorn is listening and one health probe
  has completed;
- ``WATCHDOG=1`` goes out only after a probe completes inside its deadline.

A probe is one small coroutine run on the serving event loop. It enters the
real call governor as a tool call would, then looks up one form on the
shared VESUM connection through the governor's executor, taking the same
connection lock every VESUM tool takes. That connection is where the server
deadlocked (a Python callback ran under SQLite's connection mutex with the
GIL released). A blocked event loop, a governor whose slots are all held by
stuck work, or a held connection lock therefore all stop the pings, and
systemd kills the server after ``WatchdogSec``.

At most one probe is outstanding: no new probe starts until the previous
probe's executor job has finished, so a stuck lock never piles up blocked
probe jobs. A probe that finishes after its deadline does not count.

Outside systemd (no ``$NOTIFY_SOCKET``) nothing here runs. The stdio server
never calls it.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import logging
import os
import re
import socket
import threading
import time
from collections.abc import Callable, Mapping, MutableMapping
from dataclasses import dataclass
from pathlib import Path

PROBE_TOOL = "_watchdog_probe"
# An ASCII token that is never a VESUM form: the lookup touches the index
# and the shared connection, and its (empty) result is not used.
PROBE_FORM = "watchdog-probe"
NOTIFY_ENV = ("NOTIFY_SOCKET", "WATCHDOG_USEC", "WATCHDOG_PID")
# Without a watchdog the probe only gates READY=1.
READY_PROBE_INTERVAL_S = 5.0
READY_PROBE_DEADLINE_S = 30.0
_USEC_INFINITY = 2**64 - 1
_DIGITS = re.compile(r"[0-9]+")

LOGGER_NAME = "sources.supervision"


def default_logger() -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(name)s %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


@dataclass(frozen=True)
class NotifyTarget:
    """Where and how often to notify; ``watchdog_usec`` is None when no watchdog applies."""

    address: str
    watchdog_usec: int | None


def notify_target(environ: Mapping[str, str], pid: int, logger: logging.Logger | None = None) -> NotifyTarget | None:
    """Read the notification settings systemd passed to this process.

    Returns None outside systemd. ``WATCHDOG_USEC`` must be a positive
    integer; ``WATCHDOG_PID``, when set, must name this process, otherwise
    the watchdog belongs to another process up the tree (sd_watchdog_enabled(3)).
    """
    logger = logger or default_logger()
    path = environ.get("NOTIFY_SOCKET", "")
    if not path:
        return None
    if path[0] == "@":
        address = "\0" + path[1:]
    elif path[0] == "/":
        address = path
    else:
        # vsock and other families are not used by a host service manager.
        logger.warning("sd_notify disabled: unsupported NOTIFY_SOCKET address family")
        return None
    usec_raw = environ.get("WATCHDOG_USEC")
    if usec_raw is None:
        return NotifyTarget(address, None)
    if not _DIGITS.fullmatch(usec_raw) or not 0 < int(usec_raw) < _USEC_INFINITY:
        logger.warning("watchdog disabled: WATCHDOG_USEC is not a positive integer")
        return NotifyTarget(address, None)
    pid_raw = environ.get("WATCHDOG_PID")
    if pid_raw is not None and not (_DIGITS.fullmatch(pid_raw) and int(pid_raw) == pid):
        return NotifyTarget(address, None)
    return NotifyTarget(address, int(usec_raw))


def take_notify_target(
    environ: MutableMapping[str, str] | None = None, pid: int | None = None, logger: logging.Logger | None = None
) -> NotifyTarget | None:
    """Read the settings, then remove them so child processes never inherit them."""
    environ = os.environ if environ is None else environ
    target = notify_target(environ, os.getpid() if pid is None else pid, logger)
    for name in NOTIFY_ENV:
        environ.pop(name, None)
    return target


class Notifier:
    """Send sd_notify datagrams to one target; failures are logged, never raised."""

    def __init__(self, target: NotifyTarget, logger: logging.Logger | None = None) -> None:
        self.target = target
        self.logger = logger or default_logger()
        self._failed = False

    def send(self, message: str) -> bool:
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM | socket.SOCK_CLOEXEC) as sock:
                sock.connect(self.target.address)
                sock.sendall(message.encode("ascii"))
        except OSError as error:
            if not self._failed:
                self.logger.warning("sd_notify send failed: %s", type(error).__name__)
                self._failed = True
            return False
        self._failed = False
        return True


def vesum_probe(db_path: str | Path | None = None) -> None:
    """Look up one form on the shared VESUM connection, as the VESUM tools do.

    ``get_vesum_connection`` takes the module's connection lock and hands out
    the connection every worker thread shares; the query then waits for
    SQLite's connection mutex. Without a VESUM database no tool can hold
    that connection, so a missing file is not a failure.
    """
    from scripts.verification.vesum import get_vesum_connection

    try:
        with get_vesum_connection(db_path) as conn:
            conn.execute("SELECT 1 FROM forms WHERE word_form = ? LIMIT 1", (PROBE_FORM,)).fetchone()
    except FileNotFoundError:
        return


class HealthPinger:
    """One thread that probes the serving loop and notifies systemd.

    ``ready`` says whether the server is listening. ``governor`` is the
    server's :class:`~scripts.rag.call_governor.CallGovernor`; ``operation``
    is the blocking check run on its executor. The probe interval is a
    quarter of the watchdog timeout and its deadline half of it, so a healthy
    server pings at least twice per timeout and a probe that starts late but
    meets its deadline still lands inside the timeout.
    """

    def __init__(
        self,
        notifier: Notifier,
        loop: asyncio.AbstractEventLoop,
        governor: object,
        *,
        ready: Callable[[], bool],
        operation: Callable[[], None] = vesum_probe,
        clock: Callable[[], float] = time.monotonic,
        logger: logging.Logger | None = None,
        on_ready: Callable[[], None] | None = None,
    ) -> None:
        self.notifier = notifier
        self.loop = loop
        self.governor = governor
        self.ready = ready
        self.operation = operation
        self.clock = clock
        self.logger = logger or default_logger()
        self.on_ready = on_ready
        usec = notifier.target.watchdog_usec
        self.watchdog = usec is not None
        self.interval = usec / 4e6 if usec is not None else READY_PROBE_INTERVAL_S
        self.deadline = usec / 2e6 if usec is not None else READY_PROBE_DEADLINE_S
        self.ready_sent = False
        self.probes_started = 0
        self._idle = threading.Event()
        self._idle.set()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> HealthPinger:
        self._thread = threading.Thread(target=self._run, name="sources-watchdog-pinger", daemon=True)
        self._thread.start()
        return self

    def stop(self, timeout: float = 5.0) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout)

    def _run(self) -> None:
        while not self._stop.is_set() and not self.ready():
            self._stop.wait(0.05)
        while not self._stop.is_set():
            began = self.clock()
            if self.probe_once():
                if not self.ready_sent:
                    if self.on_ready is not None:
                        self.on_ready()
                    self.ready_sent = self.notifier.send("READY=1")
                    if self.ready_sent:
                        self.logger.info(
                            "sd_notify ready watchdog=%s interval_s=%.1f deadline_s=%.1f",
                            "on" if self.watchdog else "off",
                            self.interval,
                            self.deadline,
                        )
                if self.ready_sent and not self.watchdog:
                    return
                if self.ready_sent and self.watchdog:
                    self.notifier.send("WATCHDOG=1")
            self._stop.wait(max(0.0, self.interval - (self.clock() - began)))

    def probe_once(self) -> bool:
        """Run one probe; True only for a completion inside the deadline."""
        if not self._idle.is_set():
            self.logger.warning("watchdog_probe outcome=still_running")
            return False
        self._idle.clear()
        began = self.clock()
        try:
            future = asyncio.run_coroutine_threadsafe(self._probe(), self.loop)
        except RuntimeError:
            self._idle.set()
            return False
        self.probes_started += 1
        try:
            future.result(timeout=self.deadline)
        except TimeoutError:
            if not future.done():
                self.logger.warning("watchdog_probe outcome=deadline deadline_s=%.1f", self.deadline)
                return False
            self.logger.warning("watchdog_probe outcome=error error=TimeoutError")
            return False
        except Exception as error:
            code = getattr(error, "code", type(error).__name__)
            self.logger.warning("watchdog_probe outcome=error error=%s", code)
            return False
        return self.clock() - began <= self.deadline

    async def _probe(self) -> None:
        job_started = False

        async def call() -> None:
            nonlocal job_started
            job_started = True
            try:
                await asyncio.to_thread(self.operation)
            finally:
                # The executor job has ended: the next probe may start.
                self._idle.set()

        try:
            await self.governor.run(PROBE_TOOL, call)  # type: ignore[attr-defined]
        finally:
            if not job_started:
                self._idle.set()


# systemd.exec(5): ProtectHome=yes makes these inaccessible and empty.
PROTECT_HOME_HIDDEN = (Path("/home"), Path("/root"), Path("/run/user"))


def protect_home_conflicts(repo_root: Path) -> list[tuple[str, Path]]:
    """What the unit needs that ``ProtectHome=yes`` would hide.

    The unit runs ``@REPO_ROOT@/.venv/bin/python`` in ``@REPO_ROOT@``; a
    virtual environment's interpreter is a symlink to its base interpreter,
    whose directory ``pyvenv.cfg`` names as ``home``. Paths are resolved.
    """
    needed = [("checkout", repo_root.resolve()), ("interpreter", (repo_root / ".venv" / "bin" / "python").resolve())]
    with contextlib.suppress(OSError):
        for line in (repo_root / ".venv" / "pyvenv.cfg").read_text(encoding="utf-8").splitlines():
            key, _, value = line.partition("=")
            if key.strip() == "home" and value.strip():
                needed.append(("base interpreter", Path(value.strip()).resolve()))
    return [
        (label, path)
        for label, path in needed
        if any(path == hidden or hidden in path.parents for hidden in PROTECT_HOME_HIDDEN)
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check that learn-ukrainian-sources.service can run from a checkout under ProtectHome=yes.",
        epilog=(
            'Example: .venv/bin/python -m scripts.rag.sources_supervision check-paths --repo-root "$(pwd -P)"\n'
            "Exit codes: 0 every path is visible; 1 ProtectHome=yes would hide one (each is listed); 2 usage."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check-paths", help="list what ProtectHome=yes would hide from the unit")
    check.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args(argv)
    conflicts = protect_home_conflicts(args.repo_root)
    for label, path in conflicts:
        print(f"hidden by ProtectHome=yes: {label} {path}")
    if not conflicts:
        print("visible under ProtectHome=yes: checkout, interpreter and base interpreter")
    return 1 if conflicts else 0


def start_supervision(
    server: object,
    governor: object,
    *,
    on_ready: Callable[[], None] | None = None,
    environ: MutableMapping[str, str] | None = None,
    logger: logging.Logger | None = None,
) -> HealthPinger | None:
    """Start pinging for a uvicorn ``server`` on the running loop; None outside systemd."""
    target = take_notify_target(environ, logger=logger)
    if target is None:
        return None
    pinger = HealthPinger(
        Notifier(target, logger),
        asyncio.get_running_loop(),
        governor,
        ready=lambda: bool(getattr(server, "started", False)),
        logger=logger,
        on_ready=on_ready,
    )
    return pinger.start()


if __name__ == "__main__":
    raise SystemExit(main())
