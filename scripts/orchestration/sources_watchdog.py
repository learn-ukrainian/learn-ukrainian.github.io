#!/usr/bin/env python3
"""Supervised health probe for the sources MCP server (#10674).

The sources server has hung with every thread blocked on a lock while systemd
kept reporting the unit active, because a hung process neither exits nor
fails. This probe runs from ``learn-ukrainian-sources-watchdog.timer`` every
15 seconds and acts only on a sustained failure of a running unit:

1. ``/health`` must answer 200 with ``{"status": "ok"}`` within the probe
   timeout. Three consecutive failures (about 45 s) of the same main process
   make a sustained failure; a new main process starts a fresh count.
2. Evidence first: an incident directory under the dump directory receives a
   ``/proc`` snapshot (thread states and wait channels, socket states on the
   service port, the accept backlog), a ``py-spy dump --native`` when py-spy
   is installed and allowed to attach, and the server's own all-thread Python
   stacks, triggered with ``SIGUSR1`` (see ``scripts/rag/hang_diagnostics.py``).
3. Then, immediately before signalling, a second ``/health`` probe and a
   second read of the unit's main process (pid and start time). If the server
   recovered while the dump ran, or the unit now runs another process or is
   no longer active, the restart is aborted and recorded as such.
4. Otherwise the restart: ``SIGKILL`` to the unit (a process blocked on the
   GIL never runs its ``SIGTERM`` handler) and ``systemctl --user start``,
   then a bounded wait for ``/health``.
5. One Fleet Comms report to ``cto`` per incident, through the existing
   ``sre-timers`` publisher. An incident stays open until the service has been
   healthy for ``--incident-quiet-seconds`` after its last restart.

No restart loop: at most ``--max-restarts`` restarts in ``--restart-window``
seconds, counted from a rolling restart history kept apart from incidents, so
closing an incident does not refill the budget; beyond that the probe only
logs. Each restart is written to that history, durably, before the kill, so a
run stopped mid-restart still counts. The report names the incident directory,
never its path; the full path stays in the state file and the service log. A
unit that is not active (stopped by an operator, crashed and left to systemd's
``Restart=``) is never touched. The only unit this tool probes,
dumps or restarts is ``learn-ukrainian-sources.service``; any other name is
refused before any action.

Without ``--apply`` the probe reports what it would do and changes nothing.
``dump --pid N`` captures an incident dump on demand (forced-hang drills).
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, NamedTuple
from urllib.parse import urlsplit

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.rag.hang_diagnostics import (
    DUMP_SIGNAL,
    ensure_dump_dir,
    faulthandler_log_path,
    resolve_dump_dir,
)

UNIT = "learn-ukrainian-sources.service"
# The units this tool may probe, dump or restart. Checked where the action
# happens, not only in argument parsing.
ALLOWED_UNITS = frozenset({UNIT})
HEALTH_URL = "http://127.0.0.1:8766/health"
STATE_FILE = "watchdog-state.json"
INCIDENT_PREFIX = "incident-"
SLOW_CALL_PREFIX = "slow-call-"
DEFAULT_FAILURES_TO_ACT = 3
DEFAULT_PROBE_TIMEOUT_S = 5.0
DEFAULT_MAX_RESTARTS = 3
DEFAULT_RESTART_WINDOW_S = 3600
DEFAULT_STARTUP_GRACE_S = 60
DEFAULT_INCIDENT_QUIET_S = 600
DEFAULT_RECOVERY_WAIT_S = 90
DEFAULT_KEEP_INCIDENTS = 20
STACK_WAIT_S = 5.0
PY_SPY_TIMEOUT_S = 30

TCP_STATES = {
    "01": "ESTAB",
    "02": "SYN-SENT",
    "03": "SYN-RECV",
    "04": "FIN-WAIT-1",
    "05": "FIN-WAIT-2",
    "06": "TIME-WAIT",
    "07": "CLOSE",
    "08": "CLOSE-WAIT",
    "09": "LAST-ACK",
    "0A": "LISTEN",
    "0B": "CLOSING",
}


class WatchdogError(RuntimeError):
    """A probe step could not run."""


class UnitState(NamedTuple):
    """A unit's state and the identity of its main process."""

    active: str
    sub: str
    pid: int
    # ExecMainStartTimestampMonotonic (µs): tells a new process from an old
    # one even if the kernel reuses the pid.
    started: int


def require_sources_unit(unit: str) -> None:
    if unit not in ALLOWED_UNITS:
        raise WatchdogError(f"refusing unit {unit!r}: this watchdog acts only on {', '.join(sorted(ALLOWED_UNITS))}")


def utc_stamp(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


# --- probes ---------------------------------------------------------------


def probe_health(url: str, timeout: float) -> tuple[bool, str]:
    started = time.monotonic()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read(4096)
            status = response.status
    except (urllib.error.URLError, OSError, ValueError) as error:
        return False, f"{type(error).__name__}: {error} after {time.monotonic() - started:.1f}s"
    elapsed = time.monotonic() - started
    if status != 200:
        return False, f"HTTP {status} after {elapsed:.1f}s"
    try:
        payload = json.loads(body)
    except ValueError:
        return False, f"non-JSON body after {elapsed:.1f}s"
    if not isinstance(payload, dict) or payload.get("status") != "ok":
        return False, f"status not ok after {elapsed:.1f}s"
    return True, f"ok in {elapsed:.3f}s"


def systemd_unit_state(unit: str) -> UnitState:
    """Return the state of a user unit and the identity of its main process."""
    require_sources_unit(unit)
    result = subprocess.run(
        ["systemctl", "--user", "show", "-p", "ActiveState,SubState,MainPID,ExecMainStartTimestampMonotonic", unit],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if result.returncode != 0:
        raise WatchdogError(f"systemctl show {unit} exited {result.returncode}: {result.stderr.strip()}")
    values = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)

    def number(name: str) -> int:
        try:
            return int(values.get(name, "0"))
        except ValueError:
            return 0

    return UnitState(
        values.get("ActiveState", ""),
        values.get("SubState", ""),
        number("MainPID"),
        number("ExecMainStartTimestampMonotonic"),
    )


def systemd_kill_and_start(unit: str) -> str:
    """SIGKILL the unit's processes, then start it again."""
    require_sources_unit(unit)
    steps = (
        ["systemctl", "--user", "kill", "--signal=SIGKILL", unit],
        ["systemctl", "--user", "start", unit],
    )
    for command in steps:
        result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=120)
        if result.returncode != 0:
            raise WatchdogError(f"{' '.join(command[2:])} exited {result.returncode}: {result.stderr.strip()}")
    return "killed and started"


def wait_healthy(
    url: str,
    timeout: float,
    deadline_s: float,
    *,
    probe: Callable[[str, float], tuple[bool, str]] = probe_health,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> tuple[bool, str]:
    started = clock()
    detail = "not probed"
    while clock() - started < deadline_s:
        ok, detail = probe(url, timeout)
        if ok:
            return True, f"healthy {clock() - started:.0f}s after restart"
        sleep(2.0)
    return False, f"still unhealthy {deadline_s:.0f}s after restart ({detail})"


# --- evidence -------------------------------------------------------------


def parse_proc_net_tcp(text: str, port: int) -> tuple[dict[str, int], int | None]:
    """Count TCP states of sockets bound to ``port`` and the LISTEN backlog."""
    counts: dict[str, int] = {}
    backlog: int | None = None
    for line in text.splitlines()[1:]:
        fields = line.split()
        if len(fields) < 5 or ":" not in fields[1]:
            continue
        try:
            local_port = int(fields[1].rsplit(":", 1)[1], 16)
        except ValueError:
            continue
        if local_port != port:
            continue
        state = TCP_STATES.get(fields[3].upper(), fields[3])
        counts[state] = counts.get(state, 0) + 1
        if state == "LISTEN":
            with contextlib.suppress(IndexError, ValueError):
                backlog = (backlog or 0) + int(fields[4].split(":")[1], 16)
    return counts, backlog


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError as error:
        return f"<unreadable: {type(error).__name__}>"


def proc_snapshot(pid: int, port: int, proc_root: Path = Path("/proc")) -> str:
    lines = [f"== threads of pid {pid} (tid comm state wchan)"]
    task_dir = proc_root / str(pid) / "task"
    try:
        tids = sorted(task_dir.iterdir(), key=lambda path: int(path.name))
    except (OSError, ValueError) as error:
        tids = []
        lines.append(f"<no task list: {type(error).__name__}>")
    for tid_dir in tids:
        stat = _read(tid_dir / "stat")
        # The state follows the parenthesised comm, which may itself hold spaces.
        state = stat.rsplit(")", 1)[1].split()[0] if ")" in stat else "?"
        lines.append(f"{tid_dir.name} {_read(tid_dir / 'comm')} state={state} wchan={_read(tid_dir / 'wchan')}")
    total: dict[str, int] = {}
    backlog: int | None = None
    for name in ("tcp", "tcp6"):
        try:
            text = (proc_root / "net" / name).read_text(encoding="utf-8")
        except OSError:
            continue
        counts, listen_backlog = parse_proc_net_tcp(text, port)
        for state, count in counts.items():
            total[state] = total.get(state, 0) + count
        if listen_backlog is not None:
            backlog = (backlog or 0) + listen_backlog
    lines.append(f"== socket states on port {port}")
    lines.extend(f"{count:6d} {state}" for state, count in sorted(total.items()))
    lines.append(f"== accept backlog (LISTEN rx_queue): {backlog if backlog is not None else 'unknown'}")
    status = _read(proc_root / str(pid) / "status")
    lines.append("== status")
    lines.extend(line for line in status.splitlines() if line.split(":")[0] in {"State", "Threads", "VmRSS", "SigCgt"})
    return "\n".join(lines) + "\n"


def handles_signal(pid: int, signum: int, proc_root: Path = Path("/proc")) -> bool:
    """True when ``pid`` has a handler installed for ``signum`` (SigCgt mask)."""
    for line in _read(proc_root / str(pid) / "status").splitlines():
        if line.startswith("SigCgt:"):
            try:
                mask = int(line.split(":", 1)[1].strip(), 16)
            except ValueError:
                return False
            return bool(mask & (1 << (signum - 1)))
    return False


def capture_python_stacks(
    pid: int,
    dump_dir: Path,
    *,
    proc_root: Path = Path("/proc"),
    wait_s: float = STACK_WAIT_S,
    send: Callable[[int, int], None] = os.kill,
) -> str:
    """Ask the server's faulthandler for every thread's stack; return the new text.

    The signal is sent only when that pid registered the handler: the default
    action of ``SIGUSR1`` would terminate the process.
    """
    log = faulthandler_log_path(dump_dir, pid)
    if not log.is_file():
        return f"<no faulthandler log for pid {pid}: server started without the dump handler>\n"
    if not handles_signal(pid, DUMP_SIGNAL, proc_root):
        return f"<pid {pid} has no {DUMP_SIGNAL.name} handler; signal not sent>\n"
    offset = log.stat().st_size
    send(pid, DUMP_SIGNAL)
    deadline = time.monotonic() + wait_s
    size = offset
    while time.monotonic() < deadline:
        time.sleep(0.2)
        current = log.stat().st_size
        if current > offset and current == size:
            break
        size = current
    with log.open("rb") as handle:
        handle.seek(offset)
        new = handle.read()
    if not new:
        return f"<pid {pid} wrote no stacks within {wait_s:.0f}s>\n"
    return new.decode("utf-8", errors="replace")


def capture_py_spy(pid: int, *, timeout: int = PY_SPY_TIMEOUT_S) -> str | None:
    binary = shutil.which("py-spy")
    if binary is None:
        return None
    try:
        result = subprocess.run(
            [binary, "dump", "--pid", str(pid), "--native"],
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return f"<py-spy failed: {type(error).__name__}: {error}>\n"
    return f"exit={result.returncode}\n{result.stdout}\n{result.stderr}"


def _write_private(path: Path, text: str, *, sync: bool = False) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(text)
        if sync:
            handle.flush()
            os.fsync(handle.fileno())


def capture_incident_dump(
    pid: int,
    dump_dir: Path,
    port: int,
    now: float,
    *,
    reason: str,
    proc_root: Path = Path("/proc"),
    keep: int = DEFAULT_KEEP_INCIDENTS,
) -> Path:
    """Write one incident directory; return it. Order: /proc, py-spy, stacks."""
    ensure_dump_dir(dump_dir)
    stamp = datetime.fromtimestamp(now, UTC).strftime("%Y%m%dT%H%M%SZ")
    incident = dump_dir / f"{INCIDENT_PREFIX}{stamp}-pid{pid}"
    incident.mkdir(mode=0o700, exist_ok=True)
    _write_private(incident / "proc.txt", proc_snapshot(pid, port, proc_root))
    py_spy = capture_py_spy(pid)
    if py_spy is not None:
        _write_private(incident / "py-spy.txt", py_spy)
    stacks = capture_python_stacks(pid, dump_dir, proc_root=proc_root)
    _write_private(incident / "python-stacks.txt", stacks)
    summary = {
        "captured_utc": utc_stamp(now),
        "pid": pid,
        "port": port,
        "reason": reason,
        "py_spy": py_spy is not None,
        "python_stacks": not stacks.startswith("<"),
    }
    _write_private(incident / "summary.json", json.dumps(summary, indent=2, sort_keys=True) + "\n")
    prune_dump_dir(dump_dir, keep=keep, proc_root=proc_root)
    return incident


def prune_dump_dir(dump_dir: Path, *, keep: int, proc_root: Path = Path("/proc")) -> list[Path]:
    """Keep the newest ``keep`` incidents and slow-call dumps; drop logs of dead pids."""
    removed: list[Path] = []
    incidents = sorted(path for path in dump_dir.glob(f"{INCIDENT_PREFIX}*") if path.is_dir())
    for path in incidents[: max(0, len(incidents) - keep)]:
        shutil.rmtree(path)
        removed.append(path)
    # The server's own slow-call dumps (scripts/rag/call_governor.py) rotate here too.
    slow_calls = sorted(path for path in dump_dir.glob(f"{SLOW_CALL_PREFIX}*.txt") if path.is_file())
    for path in slow_calls[: max(0, len(slow_calls) - keep)]:
        path.unlink(missing_ok=True)
        removed.append(path)
    for log in dump_dir.glob("faulthandler-*.log"):
        pid = log.stem.removeprefix("faulthandler-")
        if pid.isdigit() and not (proc_root / pid).exists():
            log.unlink(missing_ok=True)
            removed.append(log)
    return removed


# --- state machine --------------------------------------------------------


@dataclass
class Config:
    unit: str = UNIT
    health_url: str = HEALTH_URL
    dump_dir: Path = field(default_factory=lambda: resolve_dump_dir(PROJECT_ROOT))
    failures_to_act: int = DEFAULT_FAILURES_TO_ACT
    probe_timeout: float = DEFAULT_PROBE_TIMEOUT_S
    max_restarts: int = DEFAULT_MAX_RESTARTS
    restart_window: float = DEFAULT_RESTART_WINDOW_S
    startup_grace: float = DEFAULT_STARTUP_GRACE_S
    incident_quiet: float = DEFAULT_INCIDENT_QUIET_S
    recovery_wait: float = DEFAULT_RECOVERY_WAIT_S
    apply: bool = False

    @property
    def port(self) -> int:
        return urlsplit(self.health_url).port or 80


@dataclass
class Host:
    """Side effects, injectable for tests."""

    probe: Callable[[str, float], tuple[bool, str]] = probe_health
    unit_state: Callable[[str], UnitState] = systemd_unit_state
    restart: Callable[[str], str] = systemd_kill_and_start
    capture: Callable[..., Path] = capture_incident_dump
    wait_healthy: Callable[[str, float, float], tuple[bool, str]] = wait_healthy
    publish: Callable[[str, str], None] | None = None
    now: Callable[[], float] = time.time


def read_state(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def write_state(path: Path, state: Mapping[str, Any]) -> None:
    """Replace the state file atomically and durably (file, then directory, fsynced)."""
    ensure_dump_dir(path.parent)
    temporary = path.with_name(f".{path.name}.tmp")
    _write_private(temporary, json.dumps(state, indent=2, sort_keys=True) + "\n", sync=True)
    os.replace(temporary, path)
    directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def incident_message(config: Config, incident: Mapping[str, Any], dump: str, action: str) -> str:
    """The cto report. ``dump`` is the incident directory's name only: the
    report leaves the host, and the dump directory may be a private path."""
    return (
        f"[sre-timers] {config.unit} HUNG: /health failed {config.failures_to_act} consecutive probes "
        f"(last: {incident.get('last_failure', 'unknown')}).\n"
        f"Incident {incident['id']} opened {utc_stamp(incident['opened'])}; pid {incident.get('pid')}.\n"
        f"Dump captured: {dump}\n"
        f"Action: {action}\n"
        f"Self-heal budget: {config.max_restarts} restarts per {config.restart_window / 60:.0f} min; "
        "one report per incident (#10674).\n"
    )


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _flush_notification(incident: dict[str, Any], publish: Callable[[str, str], None] | None) -> str:
    message = incident.get("pending_message")
    if incident.get("notified") or not message:
        return ""
    if publish is None:
        return "notification skipped (no publisher)"
    try:
        publish(message, f"lu-sources-watchdog:{incident['id']}")
    except Exception as error:
        return f"notification failed, will retry: {error}"
    incident["notified"] = True
    incident.pop("pending_message", None)
    return "cto notified"


def _identity(unit: UnitState) -> dict[str, int]:
    return {"pid": unit.pid, "started": unit.started}


def _restart_history(state: Mapping[str, Any], now: float, window: float) -> list[float]:
    """Restarts inside the rolling window. Kept apart from incidents (#10674)."""
    stamps = state.get("restart_history")
    if not isinstance(stamps, list):
        return []
    return [float(stamp) for stamp in stamps if isinstance(stamp, int | float) and now - stamp < window]


def _recheck_before_signal(config: Config, host: Host, unit: UnitState) -> str | None:
    """Why the restart must not happen now, or None when it still must.

    The dump can take half a minute. A server that recovered meanwhile, or a
    unit an operator restarted or stopped meanwhile, is not killed.
    """
    ok, detail = host.probe(config.health_url, config.probe_timeout)
    if ok:
        return f"restart aborted: recovered (/health {detail} after the dump)"
    try:
        current = host.unit_state(config.unit)
    except (WatchdogError, OSError, subprocess.TimeoutExpired) as error:
        return f"restart aborted: unverified ({config.unit} state unreadable: {error})"
    if current.active != "active" or _identity(current) != _identity(unit):
        return (
            f"restart aborted: changed ({config.unit} is now {current.active}/{current.sub} "
            f"pid {current.pid} started {current.started}; the failing process was pid {unit.pid} "
            f"started {unit.started})"
        )
    return None


def run_once(config: Config, host: Host) -> str:
    require_sources_unit(config.unit)
    state_path = config.dump_dir / STATE_FILE
    state = read_state(state_path)
    now = host.now()
    notes: list[str] = []
    incident = state.get("incident")
    if isinstance(incident, dict) and config.apply:
        note = _flush_notification(incident, host.publish)
        if note:
            notes.append(note)

    ok, detail = host.probe(config.health_url, config.probe_timeout)
    if ok:
        state["failures"] = 0
        state.pop("failing", None)
        state["last_ok"] = now
        if (
            isinstance(incident, dict)
            and incident.get("notified")
            and now - float(incident.get("last_restart", incident.get("opened", now))) >= config.incident_quiet
        ):
            state.pop("incident", None)
            notes.append(f"incident {incident['id']} closed")
        if config.apply:
            write_state(state_path, state)
        return "; ".join([f"healthy ({detail})", *notes])

    unit = host.unit_state(config.unit)
    if unit.active != "active" or unit.pid <= 0:
        state["failures"] = 0
        state.pop("failing", None)
        if config.apply:
            write_state(state_path, state)
        return (
            f"unhealthy ({detail}) but {config.unit} is {unit.active}/{unit.sub}; "
            "systemd owns a stopped or crashed unit"
        )
    if now < float(state.get("grace_until", 0)):
        if config.apply:
            write_state(state_path, state)
        return f"unhealthy ({detail}) within startup grace"

    # Failures count per main process: a process an operator started between
    # two probes is not killed for its predecessor's failures.
    same_process = state.get("failing") == _identity(unit)
    failures = (int(state.get("failures", 0)) if same_process else 0) + 1
    state["failures"] = failures
    state["failing"] = _identity(unit)
    if failures < config.failures_to_act:
        if config.apply:
            write_state(state_path, state)
        return f"unhealthy ({detail}); failure {failures}/{config.failures_to_act}"

    if not isinstance(incident, dict):
        incident = {"id": f"{datetime.fromtimestamp(now, UTC):%Y%m%dT%H%M%SZ}", "opened": now}
    incident["pid"] = unit.pid
    incident["last_failure"] = detail
    history = _restart_history(state, now, config.restart_window)
    state["restart_history"] = history
    if len(history) >= config.max_restarts:
        exhausted = f"restart budget exhausted ({len(history)} in {config.restart_window:.0f}s); no dump, no restart"
        state["failures"] = 0
        if not config.apply:
            return f"unhealthy ({detail}); {exhausted}"
        # The budget outlives incidents, so a new incident can open with it
        # spent: report that hang too, once, rather than stay silent.
        if not incident.get("notified"):
            incident["pending_message"] = incident_message(config, incident, "none", exhausted)
        state["incident"] = incident
        write_state(state_path, state)
        note = _flush_notification(incident, host.publish)
        write_state(state_path, state)
        return "; ".join(part for part in (f"unhealthy ({detail}); {exhausted}", note) if part)
    if not config.apply:
        return f"unhealthy ({detail}); would dump pid {unit.pid}, restart {config.unit} and notify cto"

    dump = host.capture(unit.pid, config.dump_dir, config.port, now, reason=detail)
    # The full locator stays in the local state and log; the report names the
    # incident directory only.
    incident["dump"] = str(dump)
    state["failures"] = 0
    aborted = _recheck_before_signal(config, host, unit)
    if aborted is not None:
        action, outcome = aborted, "not restarted"
        state.pop("failing", None)
    else:
        # Charge the budget durably before the kill. A run stopped during the
        # restart or the recovery wait (TimeoutStartSec, an operator, a crash)
        # still counts against --max-restarts. A charge is never refunded, not
        # even when the run stopped before the kill went out: a later run cannot
        # tell whether it did, so the charge ages out of --restart-window like
        # any restart.
        state["restart_history"] = [*history, now]
        incident["last_restart"] = now
        state["grace_until"] = now + config.startup_grace
        if not incident.get("notified"):
            incident["pending_message"] = incident_message(
                config, incident, dump.name, "restart begun; the watchdog stopped before it recorded the outcome"
            )
        state["incident"] = incident
        write_state(state_path, state)
        try:
            restart_detail = host.restart(config.unit)
            healthy, recovery = host.wait_healthy(config.health_url, config.probe_timeout, config.recovery_wait)
            action = f"{restart_detail}; {recovery}"
        except (WatchdogError, OSError, subprocess.TimeoutExpired) as error:
            healthy, action = False, f"restart failed: {error}"
        outcome = "recovered" if healthy else "NOT recovered"
    if not incident.get("notified"):
        incident["pending_message"] = incident_message(config, incident, dump.name, action)
    state["incident"] = incident
    write_state(state_path, state)
    note = _flush_notification(incident, host.publish)
    write_state(state_path, state)
    return "; ".join(part for part in (f"sustained failure: dump {_relative(dump)}; {action}; {outcome}", note) if part)


# --- CLI ------------------------------------------------------------------


def default_publisher() -> Callable[[str, str], None]:
    from scripts.orchestration.backup_failure_alert import fleet_comms_publisher

    return fleet_comms_publisher(PROJECT_ROOT)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--dump-dir", type=Path, default=None, help="default: $LU_SOURCES_DUMP_DIR or batch_state/sources-dumps"
    )
    parser.add_argument("--health-url", default=HEALTH_URL)
    sub = parser.add_subparsers(dest="command", required=True)
    once = sub.add_parser("run-once", help="probe once; on a sustained failure dump, restart and notify")
    once.add_argument("--unit", default=UNIT, choices=sorted(ALLOWED_UNITS))
    once.add_argument("--apply", action="store_true", help="act; without it, report only")
    once.add_argument("--failures-to-act", type=int, default=DEFAULT_FAILURES_TO_ACT)
    once.add_argument("--probe-timeout", type=float, default=DEFAULT_PROBE_TIMEOUT_S)
    once.add_argument("--max-restarts", type=int, default=DEFAULT_MAX_RESTARTS)
    once.add_argument("--restart-window", type=float, default=DEFAULT_RESTART_WINDOW_S)
    once.add_argument("--startup-grace", type=float, default=DEFAULT_STARTUP_GRACE_S)
    once.add_argument("--incident-quiet-seconds", type=float, default=DEFAULT_INCIDENT_QUIET_S)
    once.add_argument("--recovery-wait", type=float, default=DEFAULT_RECOVERY_WAIT_S)
    dump = sub.add_parser("dump", help="capture an incident dump of a pid now (no restart, no notification)")
    dump.add_argument("--pid", type=int, required=True)
    dump.add_argument("--reason", default="manual dump")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    dump_dir = args.dump_dir or resolve_dump_dir(PROJECT_ROOT)
    port = urlsplit(args.health_url).port or 80
    if args.command == "dump":
        incident = capture_incident_dump(args.pid, dump_dir, port, time.time(), reason=args.reason)
        print(f"dump written: {incident}")
        return 0
    config = Config(
        unit=args.unit,
        health_url=args.health_url,
        dump_dir=dump_dir,
        failures_to_act=max(1, args.failures_to_act),
        probe_timeout=args.probe_timeout,
        max_restarts=max(0, args.max_restarts),
        restart_window=args.restart_window,
        startup_grace=args.startup_grace,
        incident_quiet=args.incident_quiet_seconds,
        recovery_wait=args.recovery_wait,
        apply=args.apply,
    )
    host = Host(publish=default_publisher() if args.apply else None)
    try:
        print(run_once(config, host))
    except WatchdogError as error:
        print(f"watchdog error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
