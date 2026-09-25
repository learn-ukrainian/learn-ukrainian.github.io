"""Host admission for write-capable delegate dispatches (#8645 part A).

On 2026-09-24 a global OOM on the 15 GB / 8-core host killed the infra driver
and eight workers; nothing read memory or CPU before admitting a worker
(``docs/bug-autopsies/2026-09-24-dispatch-fanout-oom.md``). ``delegate.py
dispatch`` and ``scripts.fleet.capacity_pick`` both call :func:`evaluate`, so
the admission line an operator reads is the decision dispatch makes.

A write-capable dispatch (``workspace-write``, ``danger``) is admitted only when
every check passes. Read-only dispatches are exempt.

* **Live write workers below the cap.** A worker is live when its record says
  ``spawning``/``running``, its mode is write-capable and its pid is alive. A
  ``spawning`` record without a pid holds a slot while the dispatcher that owns
  it is alive when it names that dispatcher: an admission hold
  (``admission_hold``, published under the lock before any worktree side
  effect) or a worktree reservation (``worktree_prep``, which lives as long as
  a slow ``git worktree add``, up to 900 s). Any other pid-less ``spawning``
  record holds a slot for :data:`PIDLESS_SPAWNING_GRACE_S`: dispatch publishes
  the record, then writes the Popen pid. A ``started_at`` more than
  :data:`PIDLESS_CLOCK_SKEW_S` in the future holds no slot (logged), so a bad
  clock cannot pin one. A dead pid, or a pid-less record whose dispatcher is
  provably gone, never holds a slot; the caller may sweep it to ``crashed``
  through ``on_dead``.
* **``MemAvailable``** from ``/proc/meminfo`` at or above the floor.
* **CPU:** the 1-minute load average divided by ``os.cpu_count()`` at or below
  the limit.

Without ``/proc`` (macOS) memory and CPU are ``unknown`` and only the cap is
enforced; the admission line says so. Thresholds default to the constants in
``scripts/config.py`` and are overridden by the environment variable of the
same name.

The check alone is a snapshot, so dispatch runs it again under
:func:`admission_lock` and publishes an admission hold before releasing the
lock: two concurrent dispatches cannot both take the last slot. The hold is
published before the worktree is created, so a refusal leaves no worktree and
no task record (#8717); the dispatch's later records replace it in place and
keep the slot until the worker's pid is written.

Stdlib-only apart from sibling helpers, so capacity_pick and delegate can
import it cheaply.
"""

from __future__ import annotations

import contextlib
import fcntl
import json
import logging
import os
import time
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.orchestration import task_record_store, worktree_prep

_logger = logging.getLogger(__name__)

WRITE_CAPABLE_MODES = frozenset({"workspace-write", "danger"})
ACTIVE_STATUSES = frozenset({"running", "spawning"})
PIDLESS_SPAWNING_GRACE_S = 120.0
PIDLESS_CLOCK_SKEW_S = 30.0
LOCK_FILE_NAME = "dispatch-admission.lock"
DEFAULT_LOCK_TIMEOUT_S = 60.0
PROC_ROOT = Path("/proc")

ENV_MAX_LIVE_WRITE_WORKERS = "DISPATCH_MAX_LIVE_WRITE_WORKERS"
ENV_MIN_MEM_AVAILABLE_GIB = "DISPATCH_MIN_MEM_AVAILABLE_GIB"
ENV_MAX_LOAD_PER_CPU = "DISPATCH_MAX_LOAD_PER_CPU"

# Pid-less ``spawning`` record naming the dispatcher that holds an admitted
# slot until the worker exists (#8717).
ADMISSION_HOLD_KEY = "admission_hold"
ORPHANED_HOLD_REASON = "dispatch_died_after_admission"

_GIB = 1024**3
_ACTIVE_STATUS_MARKERS = tuple(f'"{status}"'.encode() for status in sorted(ACTIVE_STATUSES))


class AdmissionLockTimeout(RuntimeError):
    """Another dispatch held the host admission lock for too long."""


@dataclass(frozen=True)
class Thresholds:
    max_live_write_workers: int
    min_mem_available_gib: float
    max_load_per_cpu: float


@dataclass(frozen=True)
class HostProbe:
    mem_available_bytes: int | None
    load1: float | None
    cpu_count: int | None
    proc_available: bool

    @property
    def mem_available_gib(self) -> float | None:
        return None if self.mem_available_bytes is None else self.mem_available_bytes / _GIB

    @property
    def load_per_cpu(self) -> float | None:
        if self.load1 is None or not self.cpu_count:
            return None
        return self.load1 / self.cpu_count


@dataclass(frozen=True)
class AdmissionDecision:
    mode: str
    exempt: bool
    admitted: bool
    thresholds: Thresholds | None = None
    probe: HostProbe | None = None
    live_task_ids: tuple[str, ...] = ()
    dead_task_ids: tuple[str, ...] = ()
    swept: bool = False
    failures: tuple[str, ...] = field(default_factory=tuple)

    @property
    def live_write_workers(self) -> int:
        return len(self.live_task_ids)

    def summary(self) -> str:
        """Measured value against threshold for every check, in one clause list."""
        if self.exempt or self.thresholds is None or self.probe is None:
            return f"mode {self.mode} is exempt (read-only dispatches are not admission-checked)"
        limits = self.thresholds
        probe = self.probe
        parts = [f"live write workers {self.live_write_workers}/{limits.max_live_write_workers}"]
        mem = probe.mem_available_gib
        parts.append(
            f"MemAvailable {mem:.1f} GiB (floor {limits.min_mem_available_gib:g} GiB)"
            if mem is not None
            else "MemAvailable unknown"
        )
        load = probe.load_per_cpu
        parts.append(
            f"load {load:.2f} per CPU (limit {limits.max_load_per_cpu:.2f})" if load is not None else "load unknown"
        )
        text = ", ".join(parts)
        if not probe.proc_available:
            text += " — /proc is not available on this platform, so only the worker cap is enforced"
        if self.dead_task_ids:
            verb = "marked crashed" if self.swept else "dead pid, not counted"
            text += f"; {len(self.dead_task_ids)} record(s) {verb}: {', '.join(self.dead_task_ids[:5])}"
            if len(self.dead_task_ids) > 5:
                text += " …"
        return text

    def refusal_line(self) -> str:
        """One line: the failed checks with value and threshold, and how to override."""
        return (
            f"dispatch admission refused for a {self.mode} worker: {'; '.join(self.failures)}. "
            "Wait for a worker to finish or for the host to recover, raise the threshold through the named "
            'environment variable, or pass --force-admission "<reason>" to override.'
        )

    def to_record(self, *, force_reason: str | None = None) -> dict[str, Any]:
        """Task-record snapshot: what admission saw, and any override."""
        limits = self.thresholds
        probe = self.probe
        mem = probe.mem_available_gib if probe else None
        load = probe.load_per_cpu if probe else None
        return {
            "checked_at": datetime.now(UTC).isoformat(),
            "admitted": self.admitted,
            "forced": force_reason is not None and not self.admitted,
            "force_reason": force_reason,
            "failures": list(self.failures),
            "live_write_workers": self.live_write_workers,
            "max_live_write_workers": limits.max_live_write_workers if limits else None,
            "mem_available_gib": round(mem, 2) if mem is not None else None,
            "min_mem_available_gib": limits.min_mem_available_gib if limits else None,
            "load1": probe.load1 if probe else None,
            "cpu_count": probe.cpu_count if probe else None,
            "load_per_cpu": round(load, 3) if load is not None else None,
            "max_load_per_cpu": limits.max_load_per_cpu if limits else None,
            "proc_available": probe.proc_available if probe else None,
            "swept_crashed": list(self.dead_task_ids) if self.swept else [],
        }


def config_defaults() -> Thresholds:
    try:
        from scripts import config
    except ImportError:  # pragma: no cover - flat script path
        import config  # type: ignore[no-redef]

    return Thresholds(
        max_live_write_workers=int(config.DISPATCH_MAX_LIVE_WRITE_WORKERS),
        min_mem_available_gib=float(config.DISPATCH_MIN_MEM_AVAILABLE_GIB),
        max_load_per_cpu=float(config.DISPATCH_MAX_LOAD_PER_CPU),
    )


def _env_number(env: Mapping[str, str], name: str, default: float, *, integer: bool) -> float:
    raw = env.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw) if integer else float(raw)
    except ValueError:
        kind = "a whole number" if integer else "a number"
        raise ValueError(f"{name}={raw!r} is not {kind}") from None
    if value < 0 or value != value:  # negative or NaN
        raise ValueError(f"{name}={raw!r} must be zero or more")
    return value


def load_thresholds(environ: Mapping[str, str] | None = None) -> Thresholds:
    """Config defaults, each overridden by its environment variable. Invalid values raise ``ValueError``."""
    env = os.environ if environ is None else environ
    defaults = config_defaults()
    return Thresholds(
        max_live_write_workers=int(
            _env_number(env, ENV_MAX_LIVE_WRITE_WORKERS, defaults.max_live_write_workers, integer=True)
        ),
        min_mem_available_gib=_env_number(
            env, ENV_MIN_MEM_AVAILABLE_GIB, defaults.min_mem_available_gib, integer=False
        ),
        max_load_per_cpu=_env_number(env, ENV_MAX_LOAD_PER_CPU, defaults.max_load_per_cpu, integer=False),
    )


def _read_mem_available_bytes(meminfo: Path) -> int | None:
    try:
        text = meminfo.read_text(encoding="ascii", errors="replace")
    except OSError:
        return None
    for line in text.splitlines():
        if line.startswith("MemAvailable:"):
            fields = line.split()
            try:
                return int(fields[1]) * 1024  # /proc/meminfo reports kB (KiB)
            except (IndexError, ValueError):
                return None
    return None


def _read_load1(loadavg: Path) -> float | None:
    try:
        return float(loadavg.read_text(encoding="ascii").split()[0])
    except (OSError, IndexError, ValueError):
        return None


def read_host(proc_root: Path) -> HostProbe:
    """Read ``MemAvailable`` and the 1-minute load average under ``proc_root``; ``None`` where unknown."""
    if not proc_root.is_dir():
        return HostProbe(mem_available_bytes=None, load1=None, cpu_count=os.cpu_count(), proc_available=False)
    return HostProbe(
        mem_available_bytes=_read_mem_available_bytes(proc_root / "meminfo"),
        load1=_read_load1(proc_root / "loadavg"),
        cpu_count=os.cpu_count(),
        proc_available=True,
    )


def probe_host() -> HostProbe:
    """This host's probe, read from ``/proc``. The one seam tests replace."""
    return read_host(PROC_ROOT)


def process_alive(pid: int) -> bool:
    """Signal-0 probe; a pid owned by another user still counts as alive."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _parse_pid(raw: Any) -> int | None:
    if isinstance(raw, bool):
        return None
    if isinstance(raw, int):
        return raw if raw > 0 else None
    if isinstance(raw, str) and raw.strip().isdigit():
        value = int(raw.strip())
        return value if value > 0 else None
    return None


def _age_s(started_at: Any, now: datetime) -> float | None:
    if not isinstance(started_at, str) or not started_at:
        return None
    try:
        started = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
    except ValueError:
        return None
    if started.tzinfo is None:
        started = started.replace(tzinfo=UTC)
    return (now - started).total_seconds()


def new_admission_hold(run_nonce: str) -> dict[str, Any]:
    """This dispatcher's claim on an admitted slot: run, pid and ``/proc`` start time."""
    owner = worktree_prep.process_identity(os.getpid())
    return {
        "run_nonce": run_nonce,
        "owner_pid": owner["pid"],
        "owner_start": owner["start"],
        "admitted_at": datetime.now(UTC).isoformat(),
    }


def is_admission_hold_record(record: Mapping[str, Any]) -> bool:
    """True for a pid-less record carrying this run's :data:`ADMISSION_HOLD_KEY`."""
    hold = record.get(ADMISSION_HOLD_KEY)
    return (
        "pid" in record
        and record["pid"] is None
        and isinstance(hold, dict)
        and isinstance(record.get("run_nonce"), str)
        and hold.get("run_nonce") == record.get("run_nonce")
    )


def is_orphaned_admission_hold(record: dict[str, Any]) -> bool:
    """True for an active admission hold whose dispatcher is provably gone.

    Dispatch replaces the hold with its full record before the worker starts;
    a dispatcher that dies first leaves a hold nothing else will finish. A
    record that also carries ``worktree_prep`` is judged by
    :func:`worktree_prep.is_orphaned_prep_record` instead.
    """
    hold = record.get(ADMISSION_HOLD_KEY)
    return (
        record.get("status") in ACTIVE_STATUSES
        and "worktree_prep" not in record
        and is_admission_hold_record(record)
        and worktree_prep.process_gone(hold.get("owner_pid"), hold.get("owner_start"))  # type: ignore[union-attr]
    )


def _dispatcher_owner(record: dict[str, Any]) -> dict[str, Any] | None:
    """The dispatcher block a pid-less record names as its owner, if any."""
    prep = record.get("worktree_prep")
    if isinstance(prep, dict):
        return prep
    hold = record.get(ADMISSION_HOLD_KEY)
    return hold if isinstance(hold, dict) else None


def is_orphaned_pidless_record(record: dict[str, Any]) -> bool:
    """True when a pid-less worktree reservation or admission hold has lost its dispatcher."""
    return worktree_prep.is_orphaned_prep_record(record) or is_orphaned_admission_hold(record)


@dataclass(frozen=True)
class WorkerScan:
    live_task_ids: tuple[str, ...]
    dead: tuple[tuple[Path, dict[str, Any]], ...]


def scan_task_records(
    tasks_dir: Path,
    *,
    pid_alive: Callable[[int], bool] | None = None,
    now: datetime | None = None,
) -> WorkerScan:
    """Live write workers, and every active record (any mode) whose owner is gone.

    The owner is the worker pid, or for a pid-less worktree reservation or
    admission hold the dispatcher that wrote it (proof per
    :func:`is_orphaned_pidless_record`).
    """
    alive = pid_alive or process_alive
    clock = now or datetime.now(UTC)
    live: list[str] = []
    dead: list[tuple[Path, dict[str, Any]]] = []
    for path in task_record_store.iter_task_records(tasks_dir, include_archive=False):
        try:
            raw = path.read_bytes()
        except OSError:
            continue
        # Most records are terminal; skip the JSON parse for them.
        if not any(marker in raw for marker in _ACTIVE_STATUS_MARKERS):
            continue
        try:
            state = json.loads(raw)
        except ValueError:
            continue
        if not isinstance(state, dict) or state.get("status") not in ACTIVE_STATUSES:
            continue
        task_id = str(state.get("task_id") or path.stem)
        write_capable = state.get("mode") in WRITE_CAPABLE_MODES
        pid = _parse_pid(state.get("pid"))
        if pid is None:
            if is_orphaned_pidless_record(state):
                dead.append((path, state))
                continue
            if not write_capable or state.get("status") != "spawning":
                continue
            owner = _dispatcher_owner(state)
            owner_pid = _parse_pid(owner.get("owner_pid")) if owner is not None else None
            if owner_pid is not None:
                # Held while the dispatcher lives, however long its worktree
                # add runs. A missing pid is proof it is gone even on a host
                # without /proc, where only the pid can be checked.
                if alive(owner_pid):
                    live.append(task_id)
                continue
            age = _age_s(state.get("started_at"), clock)
            if age is not None and age < -PIDLESS_CLOCK_SKEW_S:
                _logger.warning(
                    "dispatch admission: pidless spawning record %s has started_at %.0f s in the future; not counted",
                    task_id,
                    -age,
                )
            elif age is not None and age <= PIDLESS_SPAWNING_GRACE_S:
                live.append(task_id)
            continue
        if alive(pid):
            if write_capable:
                live.append(task_id)
        else:
            dead.append((path, state))
    return WorkerScan(live_task_ids=tuple(live), dead=tuple(dead))


def evaluate(
    mode: str,
    tasks_dir: Path,
    *,
    pid_alive: Callable[[int], bool] | None = None,
    on_dead: Callable[[Path, dict[str, Any]], None] | None = None,
    thresholds: Thresholds | None = None,
) -> AdmissionDecision:
    """Decide whether a ``mode`` dispatch may start a worker on this host now.

    ``on_dead`` receives every active record whose pid is dead or whose
    dispatcher is provably gone (the caller marks it ``crashed``); without it
    the records are only reported. Invalid threshold
    environment variables raise ``ValueError``.
    """
    if mode not in WRITE_CAPABLE_MODES:
        return AdmissionDecision(mode=mode, exempt=True, admitted=True)
    limits = thresholds or load_thresholds()
    scan = scan_task_records(tasks_dir, pid_alive=pid_alive)
    if on_dead is not None:
        for path, state in scan.dead:
            on_dead(path, state)
    probe = probe_host()
    failures: list[str] = []
    live = len(scan.live_task_ids)
    if live >= limits.max_live_write_workers:
        failures.append(
            f"live write workers {live}/{limits.max_live_write_workers} reached the cap "
            f"({ENV_MAX_LIVE_WRITE_WORKERS}={limits.max_live_write_workers})"
        )
    mem = probe.mem_available_gib
    if mem is not None and mem < limits.min_mem_available_gib:
        failures.append(
            f"MemAvailable {mem:.1f} GiB is below the floor of {limits.min_mem_available_gib:g} GiB "
            f"({ENV_MIN_MEM_AVAILABLE_GIB}={limits.min_mem_available_gib:g})"
        )
    load = probe.load_per_cpu
    if load is not None and load > limits.max_load_per_cpu:
        failures.append(
            f"load {load:.2f} per CPU (1-minute load {probe.load1:.2f} on {probe.cpu_count} CPU{'' if probe.cpu_count == 1 else 's'}) is above the "
            f"limit of {limits.max_load_per_cpu:.2f} ({ENV_MAX_LOAD_PER_CPU}={limits.max_load_per_cpu:g})"
        )
    return AdmissionDecision(
        mode=mode,
        exempt=False,
        admitted=not failures,
        thresholds=limits,
        probe=probe,
        live_task_ids=scan.live_task_ids,
        dead_task_ids=tuple(str(state.get("task_id") or path.stem) for path, state in scan.dead),
        swept=on_dead is not None,
        failures=tuple(failures),
    )


@contextlib.contextmanager
def admission_lock(tasks_dir: Path, *, timeout_s: float = DEFAULT_LOCK_TIMEOUT_S) -> Iterator[None]:
    """Host-wide exclusive lock around count → check → record publication."""
    tasks_dir.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(tasks_dir / LOCK_FILE_NAME, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        deadline = time.monotonic() + timeout_s
        while True:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise AdmissionLockTimeout(
                        f"another dispatch held {tasks_dir / LOCK_FILE_NAME} for more than {timeout_s:g}s"
                    ) from None
                time.sleep(0.05)
        try:
            yield
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
    finally:
        os.close(descriptor)
