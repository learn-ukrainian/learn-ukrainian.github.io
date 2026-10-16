"""Host admission for write-capable delegate dispatches (#8645 part A).

On 2026-09-24 a global OOM on the dispatch host killed the infra driver
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
* **Shared pool headroom (#9975).** ``lu.slice`` is the capped pool drivers and
  workers share. Its non-reclaimable use (``memory.current`` minus file cache
  from ``memory.stat``) plus a per-worker reserve must stay at or below its
  ``memory.high``. Missing cgroup files (CI, macOS) skip this check; the reason
  is logged and recorded (:mod:`scripts.orchestration.pool_headroom`).
* **Host test-slot queue (#10662).** Worker pytest runs and the pre-push gate
  wait in one FIFO queue for host test slots (:mod:`scripts.common.test_slots`).
  More waiting runs than ``DISPATCH_MAX_TEST_SLOT_QUEUE`` means the host's CPUs
  are already spoken for, so no new worker starts. A disabled or unreadable
  pool skips this check; the reason is shown.
* **Disk (#10776).** The filesystem holding the primary checkout's
  ``.worktrees/`` directory, in percent used as ``df`` reports it (used over
  used plus available). Below ``DISPATCH_DISK_REFUSE_USED_PERCENT`` (default
  85) the check passes. At or above it, a caller that passes ``reaper`` (the
  real dispatch, through :func:`run_disk_reaper`) calls the common reaper's
  ``reap_clean_pushed(dry_run=False)`` once, which removes clean, fully pushed,
  idle dispatch worktrees; the disk is measured again and the dispatch is
  refused if it is still at or above the threshold. The refusal names the
  percent used, the free GiB and the reaper outcome: trees removed and MB
  freed, the most frequent skip reasons, a busy reaper lock or the reaper's
  own refusal, or "reaper unavailable" when it cannot run. The reaper runs
  in a child process killed after ``DISPATCH_DISK_REAPER_TIMEOUT_S`` (default
  90 s; "reaper timed out"). One attempt runs per host at a time: a dispatch
  that does not get the attempt lock, or that arrives within
  ``DISPATCH_DISK_REAPER_COOLDOWN_S`` (default 600 s) of an attempt that freed
  nothing, does not run it and reports the recorded outcome. A disk refusal
  is a hard stop: ``--force-admission`` overrides the other checks, never
  this one. A dispatch that reuses an existing worktree skips the disk check.
  Paths in reaper, probe and alert details are redacted. A caller without
  a reaper (status queries, dry runs, the locked recheck) only measures. At or
  above ``DISPATCH_DISK_ALERT_USED_PERCENT`` (default 80) one alert is posted
  to the epics Fleet Comms channel per :data:`DISK_ALERT_INTERVAL_S`; the
  state file lives beside the admission lock. A disk probe that fails, or an
  alert that fails, never refuses: the reason is logged and shown.
* **Slice use is reported, not enforced.** When ``lu-dispatch.slice`` is
  active, the admission line adds its current memory against ``MemoryMax``.
  An inactive or missing slice omits that clause. The floor and the caps
  above do not change.

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
import math
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Iterator, Mapping
from dataclasses import asdict, dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.common import test_slots
from scripts.orchestration import pool_headroom, task_record_store, worktree_prep
from scripts.orchestration.dispatch_isolation import slice_usage_clause

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
ENV_WORKER_MEM_RESERVE_GIB = "DISPATCH_WORKER_MEM_RESERVE_GIB"
ENV_MAX_TEST_SLOT_QUEUE = "DISPATCH_MAX_TEST_SLOT_QUEUE"
ENV_DISK_REFUSE_USED_PERCENT = "DISPATCH_DISK_REFUSE_USED_PERCENT"
ENV_DISK_ALERT_USED_PERCENT = "DISPATCH_DISK_ALERT_USED_PERCENT"
ENV_DISK_REAPER_COOLDOWN_S = "DISPATCH_DISK_REAPER_COOLDOWN_S"
ENV_DISK_REAPER_TIMEOUT_S = "DISPATCH_DISK_REAPER_TIMEOUT_S"
_DEFAULT_WORKER_MEM_RESERVE_GIB = 2.5
_DEFAULT_MAX_TEST_SLOT_QUEUE = 4
_DEFAULT_DISK_REFUSE_USED_PERCENT = 85.0
_DEFAULT_DISK_ALERT_USED_PERCENT = 80.0

# Disk alert (#10776): one post per interval; a failed post is retried after
# the shorter backoff. The state file sits beside the admission lock and has
# no ``.json`` suffix, so task-record scans never read it.
DISK_ALERT_STATE_NAME = "dispatch-admission-disk-alert.state"
DISK_ALERT_INTERVAL_S = 6 * 3600.0
DISK_ALERT_RETRY_S = 15 * 60.0
DISK_ALERT_CHANNEL = "epics"
DISK_ALERT_SENDER = "dispatch-admission"
DISK_ALERT_PUBLISH_TIMEOUT_S = 30.0

# The reaper seam (#10776 → #10778). :func:`run_disk_reaper` imports this
# module lazily and calls ``reap_clean_pushed(repo_root=<primary checkout>,
# dry_run=False, lock_timeout_s=DISK_REAPER_LOCK_TIMEOUT_S)``, which removes
# only clean, fully pushed, idle dispatch worktrees and returns a
# ``CleanPushedReport`` (``removed``, ``skipped``, ``freed_mb``, ``lock_busy``,
# ``refusal``). A missing module or function is "reaper unavailable".
REAPER_MODULE = "scripts.orchestration.reap_worktrees"
REAPER_FUNCTION = "reap_clean_pushed"
# How long a dispatch waits for another reaper run's lock before giving up.
DISK_REAPER_LOCK_TIMEOUT_S = 5.0
# One reaper attempt per host at a time (#10776). The attempt lock is taken
# without waiting: a dispatch that does not get it, or that arrives within the
# cooldown of an attempt that freed nothing, does not run the reaper and
# reports the recorded outcome. Both files sit beside the admission lock.
DISK_REAPER_ATTEMPT_LOCK_NAME = "dispatch-admission-disk-reaper.lock"
DISK_REAPER_STATE_NAME = "dispatch-admission-disk-reaper.state"
DISK_REAPER_COOLDOWN_S = 600.0
# The reaper runs in a child process killed after this many seconds (SIGTERM,
# then SIGKILL after the grace), so a stuck fetch or tree scan cannot hold the
# dispatch. The reaper is crash-safe; its own lock dies with the process.
DISK_REAPER_TIMEOUT_S = 90.0
DISK_REAPER_KILL_GRACE_S = 5.0
# The disk guard protects worktree creation; a dispatch that reuses an
# existing worktree adds no checkout and skips it.
DISK_GUARD_REUSE_SKIP = "dispatch reuses an existing worktree"
_DISK_REAPER_CHILD_FLAG = "--run-disk-reaper"
_MODULE_NAME = "scripts.orchestration.dispatch_admission"
# Distinct skip reasons named in the refusal text, most frequent first.
DISK_REAPER_TOP_SKIP_REASONS = 3
_DISK_REAPER_REASON_CHARS = 80

# Deployment env file with the same variables (``NAME=value`` or
# ``export NAME=value`` lines). Read only for the live environment, after the
# process environment, so a long-running session started before the host set
# its overrides still sees them. ``DISPATCH_ADMISSION_ENV_FILE`` names another
# file; set it to an empty value to read none.
ENV_ADMISSION_FILE = "DISPATCH_ADMISSION_ENV_FILE"
ADMISSION_ENV_FILE_NAME = "dispatch-admission.env"
_THRESHOLD_ENV_NAMES = (
    ENV_MAX_LIVE_WRITE_WORKERS,
    ENV_MIN_MEM_AVAILABLE_GIB,
    ENV_MAX_LOAD_PER_CPU,
    ENV_WORKER_MEM_RESERVE_GIB,
    ENV_MAX_TEST_SLOT_QUEUE,
    ENV_DISK_REFUSE_USED_PERCENT,
    ENV_DISK_ALERT_USED_PERCENT,
    ENV_DISK_REAPER_COOLDOWN_S,
    ENV_DISK_REAPER_TIMEOUT_S,
)

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
    worker_mem_reserve_gib: float = _DEFAULT_WORKER_MEM_RESERVE_GIB
    max_test_slot_queue: int = _DEFAULT_MAX_TEST_SLOT_QUEUE
    disk_refuse_used_percent: float = _DEFAULT_DISK_REFUSE_USED_PERCENT
    disk_alert_used_percent: float = _DEFAULT_DISK_ALERT_USED_PERCENT
    disk_reaper_cooldown_s: float = DISK_REAPER_COOLDOWN_S
    disk_reaper_timeout_s: float = DISK_REAPER_TIMEOUT_S


@dataclass(frozen=True)
class DiskProbe:
    """Usage of the filesystem holding ``.worktrees/``, or why it is unknown (``skipped``)."""

    used_bytes: int | None = None
    free_bytes: int | None = None
    skipped: str | None = None

    @property
    def used_percent(self) -> float | None:
        """Percent used as ``df`` reports it: used over used plus available."""
        if self.used_bytes is None or self.free_bytes is None:
            return None
        usable = self.used_bytes + self.free_bytes
        return 100.0 * self.used_bytes / usable if usable > 0 else None

    @property
    def free_gib(self) -> float | None:
        return None if self.free_bytes is None else self.free_bytes / _GIB

    def text(self) -> str:
        used = self.used_percent
        free = self.free_gib
        if used is None or free is None:
            return f"disk check skipped ({self.skipped or 'no usage reported'})"
        return f"disk {used:.1f}% used, {free:.1f} GiB free"


@dataclass(frozen=True)
class ReaperOutcome:
    """What one reaper attempt did; ``ran`` is False when it could not run or failed."""

    ran: bool
    detail: str
    removed: int = 0
    freed_mb: int = 0
    lock_busy: bool = False


# Called with the primary checkout and the deadline in seconds.
DiskReaper = Callable[[Path, float], ReaperOutcome]


@dataclass(frozen=True)
class DiskCheck:
    """The disk measurement admission decided on, and what it did about it."""

    probe: DiskProbe
    # Set only when the reaper was attempted: the measurement before it ran.
    before_reaper: DiskProbe | None = None
    reaper: ReaperOutcome | None = None
    alert: str | None = None
    # A full-disk refusal is a hard stop: --force-admission never overrides it.
    refused: bool = False

    def clause(self, limits: Thresholds) -> str:
        if self.probe.used_percent is None:
            text = self.probe.text()
        else:
            text = (
                f"{self.probe.text()} (refuse at {limits.disk_refuse_used_percent:g}%, "
                f"alert at {limits.disk_alert_used_percent:g}%)"
            )
        if self.reaper is not None:
            before = self.before_reaper.used_percent if self.before_reaper is not None else None
            was = f", {before:.1f}% before" if before is not None else ""
            text += f" [{self.reaper.detail}{was}]"
        if self.alert is not None:
            text += f" [{self.alert}]"
        return text


@dataclass(frozen=True)
class SlotQueueProbe:
    """Runs waiting for host test slots, or why the count is unknown (``skipped``)."""

    depth: int | None = None
    pool_size: int | None = None
    skipped: str | None = None


@dataclass(frozen=True)
class HostProbe:
    mem_available_bytes: int | None
    load1: float | None
    cpu_count: int | None
    proc_available: bool
    cpu_steal_ticks: int | None = None
    cpu_total_ticks: int | None = None

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
    pool: pool_headroom.PoolCheck | None = None
    slots: SlotQueueProbe | None = None
    disk: DiskCheck | None = None

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
        # Slice use is informational. A missing or inactive slice adds nothing,
        # and it never changes the floor or the caps above.
        slice_use = slice_usage_clause()
        if slice_use:
            parts.append(slice_use)
        # A skipped pool check is shown with its reason: delegate.py configures
        # no logging, so this line is the operator's only visible trace (#9975).
        if self.pool is not None:
            parts.append(self.pool.clause())
        if self.slots is not None:
            parts.append(
                f"test-slot queue check skipped ({self.slots.skipped})"
                if self.slots.depth is None
                else f"test-slot queue {self.slots.depth} (limit {limits.max_test_slot_queue}, "
                f"pool {self.slots.pool_size})"
            )
        if self.disk is not None:
            parts.append(self.disk.clause(limits))
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
        if self.disk_refused:
            return (
                f"dispatch admission refused for a {self.mode} worker: {'; '.join(self.failures)}. "
                "Free space on the .worktrees filesystem (reap settled dispatch worktrees with the common reaper) "
                "and retry; --force-admission cannot override a full disk."
            )
        return (
            f"dispatch admission refused for a {self.mode} worker: {'; '.join(self.failures)}. "
            "Wait for a worker to finish or for the host to recover, raise the threshold through the named "
            'environment variable, or pass --force-admission "<reason>" to override.'
        )

    @property
    def disk_refused(self) -> bool:
        """The disk check refused: a hard stop no force flag or hold condition can turn into an admit."""
        return self.disk is not None and self.disk.refused

    def to_record(self, *, force_reason: str | None = None) -> dict[str, Any]:
        """Task-record snapshot: what admission saw, and any override."""
        limits = self.thresholds
        probe = self.probe
        mem = probe.mem_available_gib if probe else None
        load = probe.load_per_cpu if probe else None
        pool = self.pool
        pool_memory = pool.memory if pool else None
        pool_limit = pool_memory.limit if pool_memory else None
        disk = self.disk
        disk_used = disk.probe.used_percent if disk else None
        disk_free = disk.probe.free_gib if disk else None
        disk_before = disk.before_reaper.used_percent if disk and disk.before_reaper else None
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
            # /proc/stat counters are cumulative; compare two records' deltas
            # to calculate steal share over their interval.
            "cpu_steal_ticks": probe.cpu_steal_ticks if probe else None,
            "cpu_total_ticks": probe.cpu_total_ticks if probe else None,
            "proc_available": probe.proc_available if probe else None,
            "pool_nonreclaimable_gib": round(pool_memory.nonreclaimable / _GIB, 2) if pool_memory else None,
            "pool_file_cache_gib": round(pool_memory.file_cache / _GIB, 2) if pool_memory else None,
            "pool_limit_gib": round(pool_limit / _GIB, 2) if pool_limit is not None else None,
            "worker_mem_reserve_gib": limits.worker_mem_reserve_gib if limits else None,
            "pool_check_skipped": pool.skipped if pool else None,
            "test_slot_queue_depth": self.slots.depth if self.slots else None,
            "max_test_slot_queue": limits.max_test_slot_queue if limits else None,
            "test_slot_queue_skipped": self.slots.skipped if self.slots else None,
            "disk_used_percent": round(disk_used, 2) if disk_used is not None else None,
            "disk_free_gib": round(disk_free, 2) if disk_free is not None else None,
            "disk_refuse_used_percent": limits.disk_refuse_used_percent if limits else None,
            "disk_alert_used_percent": limits.disk_alert_used_percent if limits else None,
            "disk_check_skipped": disk.probe.skipped if disk else None,
            "disk_used_percent_before_reaper": round(disk_before, 2) if disk_before is not None else None,
            "disk_reaper": disk.reaper.detail if disk and disk.reaper else None,
            "disk_alert": disk.alert if disk else None,
            "disk_refused": self.disk_refused,
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
        worker_mem_reserve_gib=float(config.DISPATCH_WORKER_MEM_RESERVE_GIB),
        max_test_slot_queue=int(config.DISPATCH_MAX_TEST_SLOT_QUEUE),
        disk_refuse_used_percent=float(config.DISPATCH_DISK_REFUSE_USED_PERCENT),
        disk_alert_used_percent=float(config.DISPATCH_DISK_ALERT_USED_PERCENT),
        disk_reaper_cooldown_s=float(config.DISPATCH_DISK_REAPER_COOLDOWN_S),
        disk_reaper_timeout_s=float(config.DISPATCH_DISK_REAPER_TIMEOUT_S),
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


def admission_env_file(environ: Mapping[str, str], *, live: bool) -> Path | None:
    """The deployment env file to read, or ``None``.

    ``DISPATCH_ADMISSION_ENV_FILE`` wins (empty means none). Otherwise the live
    environment uses ``$XDG_CONFIG_HOME/learn-ukrainian/dispatch-admission.env``
    (the home config directory when unset); an explicit mapping without the
    variable reads none.
    """
    if ENV_ADMISSION_FILE in environ:
        raw = environ[ENV_ADMISSION_FILE].strip()
        return Path(raw).expanduser() if raw else None
    if not live:
        return None
    base = environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "learn-ukrainian" / ADMISSION_ENV_FILE_NAME


def read_admission_env_file(path: Path | None) -> dict[str, str]:
    """Threshold variables from a deployment env file; missing or unreadable reads as empty."""
    if path is None:
        return {}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    values: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].lstrip()
        name, sep, value = line.partition("=")
        name, value = name.strip(), value.strip()
        if not sep or name not in _THRESHOLD_ENV_NAMES:
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[name] = value
    return values


def load_thresholds(environ: Mapping[str, str] | None = None) -> Thresholds:
    """Config defaults, overridden by the deployment env file, then by the environment.

    Invalid values raise ``ValueError``.
    """
    live = environ is None
    process_env = os.environ if environ is None else environ
    file_env = read_admission_env_file(admission_env_file(process_env, live=live))
    env = {
        **file_env,
        **{k: v for k, v in process_env.items() if k in _THRESHOLD_ENV_NAMES and v.strip()},
    }
    defaults = config_defaults()
    for name in (ENV_DISK_REFUSE_USED_PERCENT, ENV_DISK_ALERT_USED_PERCENT):
        if _env_number(env, name, 0.0, integer=False) > 100:
            raise ValueError(f"{name}={env[name]!r} must be a percentage of at most 100")
    for name in (ENV_DISK_REAPER_COOLDOWN_S, ENV_DISK_REAPER_TIMEOUT_S):
        if not math.isfinite(_env_number(env, name, 1.0, integer=False)):
            raise ValueError(f"{name}={env[name]!r} must be a finite number of seconds")
    if _env_number(env, ENV_DISK_REAPER_TIMEOUT_S, 1.0, integer=False) <= 0:
        raise ValueError(f"{ENV_DISK_REAPER_TIMEOUT_S}={env[ENV_DISK_REAPER_TIMEOUT_S]!r} must be more than zero")
    return Thresholds(
        max_live_write_workers=int(
            _env_number(env, ENV_MAX_LIVE_WRITE_WORKERS, defaults.max_live_write_workers, integer=True)
        ),
        min_mem_available_gib=_env_number(
            env, ENV_MIN_MEM_AVAILABLE_GIB, defaults.min_mem_available_gib, integer=False
        ),
        max_load_per_cpu=_env_number(env, ENV_MAX_LOAD_PER_CPU, defaults.max_load_per_cpu, integer=False),
        worker_mem_reserve_gib=_env_number(
            env, ENV_WORKER_MEM_RESERVE_GIB, defaults.worker_mem_reserve_gib, integer=False
        ),
        max_test_slot_queue=int(_env_number(env, ENV_MAX_TEST_SLOT_QUEUE, defaults.max_test_slot_queue, integer=True)),
        disk_refuse_used_percent=_env_number(
            env, ENV_DISK_REFUSE_USED_PERCENT, defaults.disk_refuse_used_percent, integer=False
        ),
        disk_alert_used_percent=_env_number(
            env, ENV_DISK_ALERT_USED_PERCENT, defaults.disk_alert_used_percent, integer=False
        ),
        disk_reaper_cooldown_s=_env_number(
            env, ENV_DISK_REAPER_COOLDOWN_S, defaults.disk_reaper_cooldown_s, integer=False
        ),
        disk_reaper_timeout_s=_env_number(
            env, ENV_DISK_REAPER_TIMEOUT_S, defaults.disk_reaper_timeout_s, integer=False
        ),
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


def _read_cpu_ticks(stat: Path) -> tuple[int | None, int | None]:
    """Read aggregate /proc/stat steal and total ticks for interval deltas."""
    try:
        with stat.open(encoding="ascii") as handle:
            first_line = handle.readline()
    except (OSError, UnicodeError):
        return None, None
    fields = first_line.split()
    if not fields or fields[0] != "cpu" or len(fields) < 9:
        return None, None
    try:
        ticks = [int(value) for value in fields[1:]]
    except ValueError:
        return None, None
    if any(value < 0 for value in ticks):
        return None, None
    # guest and guest_nice are already included in user and nice by Linux.
    return ticks[7], sum(ticks[:8])


def read_host(proc_root: Path) -> HostProbe:
    """Read memory, load, and aggregate CPU counters; ``None`` where unknown."""
    if not proc_root.is_dir():
        return HostProbe(mem_available_bytes=None, load1=None, cpu_count=os.cpu_count(), proc_available=False)
    steal_ticks, total_ticks = _read_cpu_ticks(proc_root / "stat")
    return HostProbe(
        mem_available_bytes=_read_mem_available_bytes(proc_root / "meminfo"),
        load1=_read_load1(proc_root / "loadavg"),
        cpu_count=os.cpu_count(),
        proc_available=True,
        cpu_steal_ticks=steal_ticks,
        cpu_total_ticks=total_ticks,
    )


def probe_host() -> HostProbe:
    """This host's probe, read from ``/proc``. The one seam tests replace."""
    if (
        os.environ.get("PYTEST_CURRENT_TEST")
        and os.environ.get("LU_TEST_DISPATCH_HEALTHY_HOST") == "1"
        and Path("/proc") == PROC_ROOT
    ):
        return HostProbe(mem_available_bytes=64 * _GIB, load1=0.0, cpu_count=64, proc_available=True)
    return read_host(PROC_ROOT)


TEST_HOST_POOL_SKIP = "test host"


def probe_pool(reserve_gib: float) -> pool_headroom.PoolCheck:
    """Shared ``lu.slice`` headroom for one more worker. The seam pool tests replace.

    Under pytest with the healthy-host fixture, the host's real pool is not
    read unless ``LU_SLICE_CGROUP`` points the test at a fake cgroup.
    """
    reserve = int(reserve_gib * _GIB)
    if (
        os.environ.get("PYTEST_CURRENT_TEST")
        and os.environ.get("LU_TEST_DISPATCH_HEALTHY_HOST") == "1"
        and not os.environ.get(pool_headroom.ENV_LU_SLICE_CGROUP)
    ):
        return pool_headroom.PoolCheck(reserve_bytes=reserve, skipped=TEST_HOST_POOL_SKIP)
    return pool_headroom.check_pool(reserve)


def probe_test_slots() -> SlotQueueProbe:
    """Runs waiting in the host test-slot queue (#10662). The seam slot-queue tests replace.

    Under pytest with the healthy-host fixture, the host's pool is not read unless
    ``LU_TEST_SLOTS_DIR`` points the test at a private pool.
    """
    if (
        os.environ.get("PYTEST_CURRENT_TEST")
        and os.environ.get("LU_TEST_DISPATCH_HEALTHY_HOST") == "1"
        and not os.environ.get(test_slots.DIR_ENV)
    ):
        return SlotQueueProbe(skipped=TEST_HOST_POOL_SKIP)
    report = test_slots.status()
    error = report["error"]
    if error:
        return SlotQueueProbe(skipped=f"{error['reason']}: {error['detail']}")  # type: ignore[index]
    if not report["enabled"]:
        return SlotQueueProbe(skipped="pool disabled")
    return SlotQueueProbe(depth=int(report["queue_depth"]), pool_size=int(report["pool_size"]))  # type: ignore[call-overload]


def primary_checkout() -> Path:
    """The primary checkout that owns ``.worktrees/``, also from a linked worktree."""
    from scripts.common.repo_root import main_checkout_root

    return main_checkout_root(Path(__file__).resolve().parents[2])


def worktrees_disk_path() -> Path:
    """``.worktrees/`` of the primary checkout, or the checkout when it does not exist yet."""
    root = primary_checkout()
    worktrees = root / ".worktrees"
    return worktrees if worktrees.is_dir() else root


# An absolute or home-relative path inside free text: ``/a/b``, ``~/a``,
# ``~user/a``. A slash after a word character (``origin/main``, ``3/4``) is
# not a path start.
_PATH_IN_TEXT = re.compile(r"(?<![\w.\-/~])(?:~[\w.\-]*)?/[^\s'\"(),;\[\]<>]+")
REDACTED_PATH = "<path>"


def redact_paths(text: str) -> str:
    """``text`` with absolute and home paths replaced by :data:`REDACTED_PATH`.

    Reaper, probe and alert details are printed, kept in task records and
    published to Fleet Comms; host paths must not reach any of them.
    """
    return _PATH_IN_TEXT.sub(REDACTED_PATH, text)


def read_disk(path: Path, usage: Callable[[Path], Any] = shutil.disk_usage) -> DiskProbe:
    """``usage(path)`` as a :class:`DiskProbe`; a failure is ``skipped`` with its reason."""
    try:
        result = usage(path)
        used, free = int(result.used), int(result.free)
    except (OSError, AttributeError, TypeError, ValueError) as exc:
        return DiskProbe(skipped=redact_paths(f"disk usage unreadable: {type(exc).__name__}: {exc}"))
    if used < 0 or free < 0 or used + free <= 0:
        return DiskProbe(skipped=f"disk usage invalid: used={used} free={free}")
    return DiskProbe(used_bytes=used, free_bytes=free)


def probe_disk() -> DiskProbe:
    """Usage of the filesystem holding ``.worktrees/``. The seam disk tests replace.

    Under pytest with the healthy-host fixture, the host's disk is not read.
    """
    if os.environ.get("PYTEST_CURRENT_TEST") and os.environ.get("LU_TEST_DISPATCH_HEALTHY_HOST") == "1":
        return DiskProbe(skipped=TEST_HOST_POOL_SKIP)
    try:
        path = worktrees_disk_path()
    except OSError as exc:
        return DiskProbe(skipped=redact_paths(f"worktrees path unresolved: {exc}"))
    return read_disk(path)


def load_reaper_module() -> Any:
    """Import the common reaper lazily; the seam reaper tests replace."""
    from scripts.orchestration import reap_worktrees

    return reap_worktrees


def reap_clean_pushed_once(repo_root: Path) -> ReaperOutcome:
    """Run the common reaper's clean-pushed worktree removal once, in this process (#10778).

    Calls ``reap_clean_pushed(repo_root=repo_root, dry_run=False,
    lock_timeout_s=DISK_REAPER_LOCK_TIMEOUT_S)``, which removes only clean,
    fully pushed, idle dispatch worktrees and gives up after the lock timeout
    when another reaper run holds its lock. A missing module or function, an
    exception or a result without the ``CleanPushedReport`` fields is an
    outcome with ``ran=False`` that names the cause; it never raises.
    Admission runs it only in the child process :func:`run_disk_reaper`
    starts, because the call itself has no overall deadline.
    """
    try:
        module = load_reaper_module()
    except Exception as exc:  # any import failure means the reaper is unavailable
        return ReaperOutcome(ran=False, detail=f"reaper unavailable: {REAPER_MODULE} did not import ({exc})")
    function = getattr(module, REAPER_FUNCTION, None)
    if not callable(function):
        return ReaperOutcome(ran=False, detail=f"reaper unavailable: {REAPER_MODULE}.{REAPER_FUNCTION} is not present")
    try:
        report = function(repo_root=repo_root, dry_run=False, lock_timeout_s=DISK_REAPER_LOCK_TIMEOUT_S)
        return _reaper_outcome(report)
    except Exception as exc:  # the reaper must never crash admission
        return ReaperOutcome(ran=False, detail=f"reaper failed: {type(exc).__name__}: {exc}")


def _reaper_outcome(report: Any) -> ReaperOutcome:
    """Translate a ``CleanPushedReport``; raises when a field is missing or mistyped."""
    removed = len(report.removed)
    skipped = list(report.skipped)
    freed_mb = int(report.freed_mb)
    lock_busy = bool(report.lock_busy)
    refusal = report.refusal
    if refusal is not None:
        what = "did not run: lock busy" if lock_busy else "refused"
        return ReaperOutcome(ran=False, detail=f"reaper {what} ({refusal})", lock_busy=lock_busy)
    detail = f"reaper removed {removed} worktree(s), freed {freed_mb} MB"
    if skipped:
        counts: dict[str, int] = {}
        for outcome in skipped:
            reason = str(getattr(outcome, "reason", "") or "no reason")[:_DISK_REAPER_REASON_CHARS]
            counts[reason] = counts.get(reason, 0) + 1
        top = sorted(counts.items(), key=lambda item: -item[1])[:DISK_REAPER_TOP_SKIP_REASONS]
        detail += f"; skipped {len(skipped)}: " + "; ".join(f"{reason} ({count})" for reason, count in top)
    return ReaperOutcome(ran=True, detail=detail, removed=removed, freed_mb=freed_mb)


def disk_reaper_command(repo_root: Path) -> tuple[list[str], Path]:
    """The child command that runs :func:`reap_clean_pushed_once`, and its working directory.

    The child runs this module from the checkout this code was loaded from,
    with the project interpreter. Raises ``FileNotFoundError`` when no
    project interpreter is found. The seam deadline tests replace.
    """
    from scripts.common.repo_root import project_interpreter

    code_root = Path(__file__).resolve().parents[2]
    interpreter = project_interpreter(code_root)
    return [str(interpreter), "-m", _MODULE_NAME, _DISK_REAPER_CHILD_FLAG, str(repo_root)], code_root


def _signal_group(process: subprocess.Popen[str], signum: int) -> None:
    with contextlib.suppress(ProcessLookupError, PermissionError):
        os.killpg(process.pid, signum)


def _parse_child_outcome(stdout: str) -> ReaperOutcome | None:
    # Split on newlines only: str.splitlines would also split on Unicode line
    # separators inside the JSON record (#9556).
    lines = [line for line in stdout.split("\n") if line.strip()]
    if not lines:
        return None
    try:
        data = json.loads(lines[-1])
    except ValueError:
        return None
    if not isinstance(data, dict):
        return None
    ran, detail = data.get("ran"), data.get("detail")
    removed, freed_mb, lock_busy = data.get("removed"), data.get("freed_mb"), data.get("lock_busy")
    if not (isinstance(ran, bool) and isinstance(detail, str) and isinstance(lock_busy, bool)):
        return None
    if type(removed) is not int or type(freed_mb) is not int:
        return None
    return ReaperOutcome(ran=ran, detail=detail, removed=removed, freed_mb=freed_mb, lock_busy=lock_busy)


def run_disk_reaper(repo_root: Path, timeout_s: float = DISK_REAPER_TIMEOUT_S) -> ReaperOutcome:
    """Run :func:`reap_clean_pushed_once` in a child process with a hard deadline.

    The child gets its own process group. When ``timeout_s`` passes, the group
    gets SIGTERM and, after :data:`DISK_REAPER_KILL_GRACE_S`, SIGKILL, and the
    outcome is "reaper timed out": the caller regains control within about
    ``timeout_s`` plus twice the grace. A child that cannot start, exits
    non-zero or prints no outcome is "reaper failed". Never raises.
    """
    try:
        command, cwd = disk_reaper_command(repo_root)
    except (FileNotFoundError, OSError) as exc:
        return ReaperOutcome(ran=False, detail=f"reaper unavailable: {exc}")
    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
    except OSError as exc:
        return ReaperOutcome(ran=False, detail=f"reaper failed: could not start the reaper process: {exc}")
    try:
        stdout, stderr = process.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        _signal_group(process, signal.SIGTERM)
        try:
            process.communicate(timeout=DISK_REAPER_KILL_GRACE_S)
        except subprocess.TimeoutExpired:
            _signal_group(process, signal.SIGKILL)
            # A descendant that left the group may still hold the pipes: do
            # not wait for them, only for the child itself.
            for stream in (process.stdout, process.stderr):
                if stream is not None:
                    with contextlib.suppress(OSError):
                        stream.close()
            with contextlib.suppress(subprocess.TimeoutExpired):
                process.wait(timeout=DISK_REAPER_KILL_GRACE_S)
        _logger.warning("dispatch admission: disk reaper timed out after %gs; its process group was stopped", timeout_s)
        return ReaperOutcome(ran=False, detail=f"reaper timed out after {timeout_s:g} s and was stopped")
    if process.returncode != 0:
        last = (stderr or "").strip().splitlines()
        return ReaperOutcome(
            ran=False,
            detail=f"reaper failed: the reaper process exited {process.returncode}: {last[-1] if last else 'no output'}",
        )
    outcome = _parse_child_outcome(stdout)
    if outcome is None:
        return ReaperOutcome(ran=False, detail="reaper failed: the reaper process printed no outcome")
    return outcome


def _reaper_child_main(argv: list[str]) -> int:
    """``python -m scripts.orchestration.dispatch_admission --run-disk-reaper <repo_root>``.

    Prints the :class:`ReaperOutcome` as one JSON line on stdout; anything
    the reaper itself prints goes to stderr.
    """
    if len(argv) != 2 or argv[0] != _DISK_REAPER_CHILD_FLAG:
        print(f"usage: python -m {_MODULE_NAME} {_DISK_REAPER_CHILD_FLAG} <repo_root>", file=sys.stderr)
        return 2
    with contextlib.redirect_stdout(sys.stderr):
        outcome = reap_clean_pushed_once(Path(argv[1]))
    print(json.dumps(asdict(outcome), sort_keys=True))
    return 0


def _attempt_reaper(reaper: DiskReaper, timeout_s: float) -> ReaperOutcome:
    try:
        root = primary_checkout()
        outcome = reaper(root, timeout_s)
    except Exception as exc:  # an injected reaper must not crash admission either
        outcome = ReaperOutcome(ran=False, detail=f"reaper failed: {type(exc).__name__}: {exc}")
    if not isinstance(outcome, ReaperOutcome):
        outcome = ReaperOutcome(
            ran=False, detail=f"reaper failed: returned {type(outcome).__name__}, not ReaperOutcome"
        )
    return replace(outcome, detail=redact_paths(outcome.detail))


def _finite_time(state: Mapping[str, Any], key: str) -> float | None:
    """``state[key]`` as epoch seconds; ``None`` when absent. Raises ``ValueError`` when malformed."""
    if key not in state:
        return None
    value = state[key]
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{key} is not a number")
    try:
        number = float(value)
    except OverflowError:
        raise ValueError(f"{key} is out of range") from None
    if not math.isfinite(number):
        raise ValueError(f"{key} is not finite")
    return number


def _read_reaper_state(tasks_dir: Path) -> dict[str, Any] | None:
    """The last recorded attempt, or ``None`` when there is none or it is malformed."""
    try:
        state = json.loads((tasks_dir / DISK_REAPER_STATE_NAME).read_text(encoding="utf-8"))
        if not isinstance(state, dict):
            return None
        last = _finite_time(state, "last_attempt_at")
    except (OSError, ValueError):
        return None
    if last is None or not isinstance(state.get("detail"), str) or not isinstance(state.get("freed"), bool):
        return None
    return {**state, "last_attempt_at": last}


def _write_reaper_state(tasks_dir: Path, state: Mapping[str, Any]) -> None:
    """Replace the state file atomically: dispatches without the attempt lock read it."""
    target = tasks_dir / DISK_REAPER_STATE_NAME
    temporary = tasks_dir / f"{DISK_REAPER_STATE_NAME}.tmp-{os.getpid()}-{threading.get_ident()}"
    try:
        temporary.write_text(json.dumps(dict(state), sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, target)
    except OSError as exc:
        _logger.warning("dispatch admission: disk reaper state not recorded: %s", exc)
        with contextlib.suppress(OSError):
            temporary.unlink()


def _recorded_attempt(state: Mapping[str, Any] | None, clock: float) -> str:
    if state is None:
        return "no earlier attempt recorded"
    age = max(0.0, clock - float(state["last_attempt_at"]))
    return f"reaper attempted {age:.0f} s ago: {state['detail']}"


def attempt_disk_reaper(
    tasks_dir: Path, reaper: DiskReaper, limits: Thresholds, *, now: Callable[[], float] = time.time
) -> ReaperOutcome:
    """Run ``reaper`` at most once per host at a time and once per cooldown (#10776).

    Takes the attempt lock without waiting. A dispatch that does not get it,
    or that finds an attempt within ``limits.disk_reaper_cooldown_s`` that
    freed nothing, does not run the reaper and returns the recorded outcome
    (``ran=False``). An attempt that freed space does not start a cooldown.
    A recorded attempt dated in the future (the clock stepped back) counts
    as just made. Never raises.
    """
    try:
        tasks_dir.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(tasks_dir / DISK_REAPER_ATTEMPT_LOCK_NAME, os.O_CREAT | os.O_RDWR, 0o600)
    except OSError as exc:
        return ReaperOutcome(ran=False, detail=redact_paths(f"reaper not run: attempt lock unavailable ({exc})"))
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            recorded = _recorded_attempt(_read_reaper_state(tasks_dir), now())
            return ReaperOutcome(ran=False, detail=f"reaper attempt in progress in another dispatch; {recorded}")
        except OSError as exc:
            return ReaperOutcome(ran=False, detail=redact_paths(f"reaper not run: attempt lock unavailable ({exc})"))
        state = _read_reaper_state(tasks_dir)
        clock = now()
        if state is not None and not state["freed"]:
            if state["last_attempt_at"] > clock:
                state = {**state, "last_attempt_at": clock}
                _write_reaper_state(tasks_dir, state)
            if clock - state["last_attempt_at"] < limits.disk_reaper_cooldown_s:
                return ReaperOutcome(ran=False, detail=_recorded_attempt(state, clock))
        outcome = _attempt_reaper(reaper, limits.disk_reaper_timeout_s)
        freed = outcome.ran and (outcome.removed > 0 or outcome.freed_mb > 0)
        _write_reaper_state(
            tasks_dir,
            {
                # When the attempt ended, never before it started.
                "last_attempt_at": max(clock, now()),
                "detail": outcome.detail,
                "ran": outcome.ran,
                "removed": outcome.removed,
                "freed_mb": outcome.freed_mb,
                "freed": freed,
            },
        )
        return outcome
    finally:
        os.close(descriptor)


def post_disk_alert(body: str, idempotency_key: str) -> None:
    """Publish one alert to the epics Fleet Comms channel. The seam alert tests replace.

    Raises ``RuntimeError`` naming the cause when the publish fails. Under
    pytest with the healthy-host fixture nothing is published.
    """
    if os.environ.get("PYTEST_CURRENT_TEST") and os.environ.get("LU_TEST_DISPATCH_HEALTHY_HOST") == "1":
        raise RuntimeError("test host: alerts are not published")
    from scripts.common.repo_root import project_interpreter

    root = primary_checkout()
    try:
        interpreter = project_interpreter(root)
    except FileNotFoundError as exc:
        raise RuntimeError(f"fleet_comms publish could not run: {exc}") from exc
    command = [
        str(interpreter),
        "-m",
        "scripts.fleet_comms",
        "channel",
        "publish",
        DISK_ALERT_CHANNEL,
        "-",
        "--sender",
        DISK_ALERT_SENDER,
        "--source",
        DISK_ALERT_SENDER,
        "--kind",
        "report",
        "--idempotency-key",
        idempotency_key,
    ]
    try:
        result = subprocess.run(
            command,
            input=body,
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=DISK_ALERT_PUBLISH_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"fleet_comms publish could not run: {exc}") from exc
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip().splitlines()
        raise RuntimeError(f"fleet_comms publish exited {result.returncode}: {detail[-1] if detail else 'no output'}")


def _read_alert_state(descriptor: int) -> dict[str, Any]:
    os.lseek(descriptor, 0, os.SEEK_SET)
    raw = b""
    while chunk := os.read(descriptor, 65536):
        raw += chunk
    try:
        state = json.loads(raw) if raw.strip() else {}
    except ValueError:
        # An unreadable record must not silence alerts: treat it as none.
        return {}
    return state if isinstance(state, dict) else {}


def _write_alert_state(descriptor: int, state: Mapping[str, Any]) -> None:
    data = (json.dumps(dict(state), sort_keys=True) + "\n").encode()
    os.ftruncate(descriptor, 0)
    os.lseek(descriptor, 0, os.SEEK_SET)
    os.write(descriptor, data)


def _iso_utc(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def maybe_alert_disk(
    tasks_dir: Path,
    check: DiskCheck,
    limits: Thresholds,
    *,
    refused: bool,
    now: float | None = None,
    publish: Callable[[str, str], None] | None = None,
) -> str:
    """Post one epics alert per :data:`DISK_ALERT_INTERVAL_S`; return what happened.

    The state file is locked without waiting: a concurrent admission that holds
    it is already alerting. A failed post is logged and retried after
    :data:`DISK_ALERT_RETRY_S`. A malformed ``posted_at`` or ``failed_at``
    counts as a failed post. A time dated in the future (the clock stepped
    back) counts as now and is stored so, so the window cannot reopen early.
    Nothing here raises.
    """
    clock = time.time() if now is None else now
    send = publish or post_disk_alert
    used = check.probe.used_percent
    free = check.probe.free_gib
    try:
        tasks_dir.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(tasks_dir / DISK_ALERT_STATE_NAME, os.O_CREAT | os.O_RDWR, 0o600)
    except OSError as exc:
        _logger.warning("dispatch admission: disk alert state unavailable: %s", exc)
        return redact_paths(f"epics alert not sent: state unavailable ({exc})")
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return "epics alert in progress in another admission"
        state = _read_alert_state(descriptor)
        try:
            posted = _finite_time(state, "posted_at")
            failed = _finite_time(state, "failed_at")
        except ValueError as exc:
            _logger.warning("dispatch admission: disk alert state malformed: %s", exc)
            _write_alert_state(descriptor, {"failed_at": clock, "last_error": f"alert state malformed: {exc}"})
            return f"epics alert failed: alert state malformed ({exc}); retry after {DISK_ALERT_RETRY_S / 60:g} min"
        if posted is not None and posted > clock:
            state, posted = {**state, "posted_at": clock}, clock
            _write_alert_state(descriptor, state)
        if posted is not None and clock - posted < DISK_ALERT_INTERVAL_S:
            return f"epics alert already posted at {_iso_utc(posted)}"
        if failed is not None and failed > clock:
            state, failed = {**state, "failed_at": clock}, clock
            _write_alert_state(descriptor, state)
        if failed is not None and clock - failed < DISK_ALERT_RETRY_S:
            return f"epics alert failed at {_iso_utc(failed)}; retry after {DISK_ALERT_RETRY_S / 60:g} min"
        verdict = "new write dispatches are REFUSED" if refused else "new write dispatches are still admitted"
        lines = [
            f"[dispatch-admission] disk {used:.1f}% used, {free:.1f} GiB free on the .worktrees filesystem "
            f"at {_iso_utc(clock)} (alert at {limits.disk_alert_used_percent:g}%, "
            f"refuse at {limits.disk_refuse_used_percent:g}%); {verdict}.",
        ]
        if check.reaper is not None:
            lines.append(f"Reaper attempt: {redact_paths(check.reaper.detail)}.")
        lines.append(
            "Act: reap settled dispatch worktrees with the common reaper and clear other disk use. "
            f"Next alert no sooner than {DISK_ALERT_INTERVAL_S / 3600:g} h from now."
        )
        try:
            send("\n".join(lines) + "\n", f"dispatch-admission-disk:{_iso_utc(clock)}")
        except Exception as exc:  # an alert failure never blocks admission
            error = redact_paths(str(exc))
            _logger.warning("dispatch admission: disk alert to %s failed: %s", DISK_ALERT_CHANNEL, error)
            _write_alert_state(descriptor, {**state, "failed_at": clock, "last_error": error[:300]})
            return f"epics alert failed: {error}"
        _write_alert_state(descriptor, {"posted_at": clock, "used_percent": round(used or 0.0, 2)})
        return "epics alert posted"
    except (OSError, ValueError, OverflowError) as exc:
        _logger.warning("dispatch admission: disk alert state unavailable: %s", exc)
        return redact_paths(f"epics alert not sent: state unavailable ({exc})")
    finally:
        os.close(descriptor)


def check_disk(
    limits: Thresholds, *, reaper: DiskReaper | None, tasks_dir: Path | None = None
) -> tuple[DiskCheck, str | None]:
    """Measure the disk, reaping once at the refuse threshold; return the check and any failure.

    With a ``reaper`` the attempt goes through :func:`attempt_disk_reaper`
    (one per host, cooldown, deadline), which keeps its state in
    ``tasks_dir``. A failure sets ``DiskCheck.refused``: a hard stop.
    """
    probe = probe_disk()
    used = probe.used_percent
    if used is None:
        log = _logger.debug if probe.skipped == TEST_HOST_POOL_SKIP else _logger.warning
        log("dispatch admission: disk check skipped: %s", probe.skipped)
        return DiskCheck(probe=probe), None
    if used < limits.disk_refuse_used_percent:
        return DiskCheck(probe=probe), None
    if reaper is None:
        outcome = ReaperOutcome(ran=False, detail="reaper not run in this check")
        check = DiskCheck(probe=probe, before_reaper=None, reaper=outcome)
    else:
        if tasks_dir is None:
            raise ValueError("check_disk needs tasks_dir when it may run the reaper")
        outcome = attempt_disk_reaper(tasks_dir, reaper, limits)
        after = probe_disk()
        check = DiskCheck(probe=after, before_reaper=probe, reaper=outcome)
        after_used = after.used_percent
        if after_used is None:
            _logger.warning("dispatch admission: disk check skipped after the reaper: %s", after.skipped)
            return check, None
        if after_used < limits.disk_refuse_used_percent:
            return check, None
    final = check.probe
    return replace(check, refused=True), (
        f"{final.text()} on the .worktrees filesystem is at or above the refuse threshold of "
        f"{limits.disk_refuse_used_percent:g}% ({ENV_DISK_REFUSE_USED_PERCENT}={limits.disk_refuse_used_percent:g}); "
        f"{outcome.detail}"
    )


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
    from scripts.orchestration.dead_worker_state import capture_worker_identity

    owner = capture_worker_identity(os.getpid(), self_process=True)
    return {
        "run_nonce": run_nonce,
        "owner_pid": owner["pid"],
        "owner_start": owner["start_time"],
        "owner_identity": owner,
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
        and worktree_prep.owner_gone(hold)  # type: ignore[arg-type]
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
    record_liveness: Callable[[dict[str, Any]], bool | None] | None = None,
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
                if "owner_identity" in owner:
                    from scripts.orchestration.dead_worker_state import worker_liveness

                    owner_live = worker_liveness({"pid": owner_pid, "worker_identity": owner["owner_identity"]}) is not False
                else:
                    owner_live = alive(owner_pid)
                if owner_live:
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
        worker_live = record_liveness(state) is not False if record_liveness is not None else alive(pid)
        if worker_live:
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
    record_liveness: Callable[[dict[str, Any]], bool | None] | None = None,
    on_dead: Callable[[Path, dict[str, Any]], None] | None = None,
    thresholds: Thresholds | None = None,
    reaper: DiskReaper | None = None,
    disk_guard: bool = True,
) -> AdmissionDecision:
    """Decide whether a ``mode`` dispatch may start a worker on this host now.

    ``on_dead`` receives every active record whose pid is dead or whose
    dispatcher is provably gone (the caller marks it ``crashed``); without it
    the records are only reported. ``reaper`` (normally
    :func:`run_disk_reaper`) is attempted at most once, through
    :func:`attempt_disk_reaper`, when the disk is at or above the refuse
    threshold; without it the disk is only measured. ``disk_guard=False``
    (a dispatch that reuses an existing worktree) skips the disk check, the
    reaper and the alert. Invalid threshold environment variables raise
    ``ValueError``.
    """
    if mode not in WRITE_CAPABLE_MODES:
        return AdmissionDecision(mode=mode, exempt=True, admitted=True)
    limits = thresholds or load_thresholds()
    scan = scan_task_records(tasks_dir, pid_alive=pid_alive, record_liveness=record_liveness)
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
    pool = probe_pool(limits.worker_mem_reserve_gib)
    if pool.skipped is not None:
        # WARNING, not INFO: callers such as delegate.py configure no logging,
        # so only WARNING and above reach stderr. The admitted line also
        # carries the reason through summary().
        log = _logger.debug if pool.skipped == TEST_HOST_POOL_SKIP else _logger.warning
        log("dispatch admission: shared pool check skipped: %s", pool.skipped)
    elif not pool.fits:
        failures.append(f"{pool.failure()} ({ENV_WORKER_MEM_RESERVE_GIB}={limits.worker_mem_reserve_gib:g})")
    slots = probe_test_slots()
    if slots.depth is not None and slots.depth > limits.max_test_slot_queue:
        failures.append(
            f"test-slot queue {slots.depth} is longer than {limits.max_test_slot_queue} waiting runs "
            f"({ENV_MAX_TEST_SLOT_QUEUE}={limits.max_test_slot_queue})"
        )
    if not disk_guard:
        disk, disk_failure = DiskCheck(probe=DiskProbe(skipped=DISK_GUARD_REUSE_SKIP)), None
    else:
        disk, disk_failure = check_disk(limits, reaper=reaper, tasks_dir=tasks_dir)
    if disk_failure is not None:
        failures.append(disk_failure)
    disk_used = disk.probe.used_percent
    if disk_used is not None and disk_used >= limits.disk_alert_used_percent:
        alert = maybe_alert_disk(tasks_dir, disk, limits, refused=disk_failure is not None)
        disk = replace(disk, alert=alert)
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
        pool=pool,
        slots=slots,
        disk=disk,
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


if __name__ == "__main__":
    raise SystemExit(_reaper_child_main(sys.argv[1:]))
