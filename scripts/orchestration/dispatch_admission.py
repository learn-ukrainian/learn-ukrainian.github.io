"""Host admission for write-capable delegate dispatches (#8645 part A).

On 2026-09-24 a global OOM on the dispatch host killed the infra driver
and eight workers; nothing read memory or CPU before admitting a worker
(``docs/bug-autopsies/2026-09-24-dispatch-fanout-oom.md``). ``dispatch.py
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
  used plus available). Admission only measures, refuses and alerts; it
  never removes anything (each task's worktree is removed by the dispatcher
  at settlement). At or above ``DISPATCH_DISK_REFUSE_USED_PERCENT`` (default
  90) a new write dispatch is refused. A disk refusal is a hard stop:
  ``--force-admission`` overrides the other checks, never this one. A
  dispatch that reuses an existing worktree skips the disk check. Paths in
  probe and alert details are redacted. At or above
  ``DISPATCH_DISK_ALERT_USED_PERCENT`` (default 75) one alert is posted to
  the epics Fleet Comms channel per :data:`DISK_ALERT_INTERVAL_S`; the state
  file lives beside the admission lock. ``DISPATCH_DISK_REAP_USED_PERCENT``
  (default 85) is the watermark at which the scheduled worktree cleanup
  alerts the cto channel (:mod:`scripts.orchestration.disk_watermark_alert`);
  it must be strictly below the refuse watermark, otherwise reading the
  thresholds raises :class:`DiskWatermarkConfigError` (#10871). A disk probe
  that fails, or an alert that fails, never refuses on its own: the reason
  is logged and shown.
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

Before its costly preflights, a dispatch that would spawn on this host calls
:func:`precheck`: memory and load only, and able only to refuse,
so an overloaded host turns a dispatch away cheaply (#10799). It steps aside
for a full disk, whose hard stop stays with :func:`evaluate`.
Both paths append bounded PSI shadow observations (#10802); candidate PSI
decisions never change any enforcement check. See ``admission_shadow``.

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
import subprocess
import sys
import time
import urllib.parse
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

if __package__ in (None, ""):  # run as a file: put the repository root on sys.path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.common import test_slots
from scripts.orchestration import admission_shadow, pool_headroom, task_record_store, worktree_prep
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
ENV_DISK_REAP_USED_PERCENT = "DISPATCH_DISK_REAP_USED_PERCENT"
ENV_DISK_REFUSE_USED_PERCENT = "DISPATCH_DISK_REFUSE_USED_PERCENT"
ENV_DISK_ALERT_USED_PERCENT = "DISPATCH_DISK_ALERT_USED_PERCENT"
_DEFAULT_WORKER_MEM_RESERVE_GIB = 2.5
_DEFAULT_MAX_TEST_SLOT_QUEUE = 4
_DEFAULT_DISK_REAP_USED_PERCENT = 85.0
_DEFAULT_DISK_REFUSE_USED_PERCENT = 90.0
_DEFAULT_DISK_ALERT_USED_PERCENT = 75.0

# Disk alert (#10776): one post per interval; a failed post is retried after
# the shorter backoff. The state file sits beside the admission lock and has
# no ``.json`` suffix, so task-record scans never read it.
DISK_ALERT_STATE_NAME = "dispatch-admission-disk-alert.state"
DISK_ALERT_INTERVAL_S = 6 * 3600.0
DISK_ALERT_RETRY_S = 15 * 60.0
DISK_ALERT_CHANNEL = "epics"
DISK_ALERT_SENDER = "dispatch-admission"
DISK_ALERT_PUBLISH_TIMEOUT_S = 30.0

# The disk guard protects worktree creation; a dispatch that reuses an
# existing worktree adds no checkout and skips it.
DISK_GUARD_REUSE_SKIP = "dispatch reuses an existing worktree"

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
    ENV_DISK_REAP_USED_PERCENT,
    ENV_DISK_REFUSE_USED_PERCENT,
    ENV_DISK_ALERT_USED_PERCENT,
)

# Pid-less ``spawning`` record naming the dispatcher that holds an admitted
# slot until the worker exists (#8717).
ADMISSION_HOLD_KEY = "admission_hold"
ORPHANED_HOLD_REASON = "dispatch_died_after_admission"

_GIB = 1024**3
_ACTIVE_STATUS_MARKERS = tuple(f'"{status}"'.encode() for status in sorted(ACTIVE_STATUSES))


class AdmissionLockTimeout(RuntimeError):
    """Another dispatch held the host admission lock for too long."""


class DiskWatermarkConfigError(ValueError):
    """The cto alert watermark is not strictly below the refuse watermark (#10871)."""


@dataclass(frozen=True)
class Thresholds:
    max_live_write_workers: int
    min_mem_available_gib: float
    max_load_per_cpu: float
    worker_mem_reserve_gib: float = _DEFAULT_WORKER_MEM_RESERVE_GIB
    max_test_slot_queue: int = _DEFAULT_MAX_TEST_SLOT_QUEUE
    disk_reap_used_percent: float = _DEFAULT_DISK_REAP_USED_PERCENT
    disk_refuse_used_percent: float = _DEFAULT_DISK_REFUSE_USED_PERCENT
    disk_alert_used_percent: float = _DEFAULT_DISK_ALERT_USED_PERCENT


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
class DiskCheck:
    """The disk measurement admission decided on, and what it did about it."""

    probe: DiskProbe
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
        if self.alert is not None:
            text += f" [{self.alert}]"
        return text


@dataclass(frozen=True)
class SlotQueueProbe:
    """Runs waiting for host test slots, or why the count is unknown (``skipped``)."""

    depth: int | None = None
    pool_size: int | None = None
    skipped: str | None = None
    holders: tuple[dict[str, Any], ...] = ()
    queued: tuple[dict[str, Any], ...] = ()


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
    psi_shadow: dict[str, Any] | None = None

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
        # A skipped pool check is shown with its reason: dispatch.py configures
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
        if self.psi_shadow is not None:
            shadow = self.psi_shadow
            parts.append(
                f"PSI shadow {shadow['psi']['decision']} (calibration only; "
                f"{shadow['persistence']}; CPU ownership unknown, unattributed load unknown)"
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
        if self.disk_refused:
            return (
                f"dispatch admission refused for a {self.mode} worker: {'; '.join(self.failures)}. "
                "Free space on the .worktrees filesystem (remove settled dispatch worktrees "
                "with `python -m scripts.orchestration.worktree_claims remove`) and retry; --force-admission cannot override a full disk."
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
            "disk_reap_used_percent": limits.disk_reap_used_percent if limits else None,
            "disk_refuse_used_percent": limits.disk_refuse_used_percent if limits else None,
            "disk_alert_used_percent": limits.disk_alert_used_percent if limits else None,
            "disk_check_skipped": disk.probe.skipped if disk else None,
            "disk_alert": disk.alert if disk else None,
            "disk_refused": self.disk_refused,
            "swept_crashed": list(self.dead_task_ids) if self.swept else [],
            "psi_shadow": self.psi_shadow,
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
        disk_reap_used_percent=float(config.DISPATCH_DISK_REAP_USED_PERCENT),
        disk_refuse_used_percent=float(config.DISPATCH_DISK_REFUSE_USED_PERCENT),
        disk_alert_used_percent=float(config.DISPATCH_DISK_ALERT_USED_PERCENT),
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
    for name in (ENV_DISK_REAP_USED_PERCENT, ENV_DISK_REFUSE_USED_PERCENT, ENV_DISK_ALERT_USED_PERCENT):
        if _env_number(env, name, 0.0, integer=False) > 100:
            raise ValueError(f"{name}={env[name]!r} must be a percentage of at most 100")
    limits = Thresholds(
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
        disk_reap_used_percent=_env_number(
            env, ENV_DISK_REAP_USED_PERCENT, defaults.disk_reap_used_percent, integer=False
        ),
        disk_refuse_used_percent=_env_number(
            env, ENV_DISK_REFUSE_USED_PERCENT, defaults.disk_refuse_used_percent, integer=False
        ),
        disk_alert_used_percent=_env_number(
            env, ENV_DISK_ALERT_USED_PERCENT, defaults.disk_alert_used_percent, integer=False
        ),
    )
    validate_disk_watermarks(limits)
    return limits


def validate_disk_watermarks(limits: Thresholds) -> None:
    """Raise :class:`DiskWatermarkConfigError` unless the cto alert is strictly below refuse (#10871).

    Equal or inverted values would refuse dispatches before the scheduled
    cleanup warned the cto channel, so the settings are rejected when read.
    """
    if limits.disk_reap_used_percent >= limits.disk_refuse_used_percent:
        raise DiskWatermarkConfigError(
            f"{ENV_DISK_REAP_USED_PERCENT}={limits.disk_reap_used_percent:g} must be below "
            f"{ENV_DISK_REFUSE_USED_PERCENT}={limits.disk_refuse_used_percent:g}"
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
    return SlotQueueProbe(
        depth=int(report["queue_depth"]), pool_size=int(report["pool_size"]),  # type: ignore[call-overload]
        holders=tuple(report["holders"][:admission_shadow.MAX_ATTRIBUTED]),  # type: ignore[index, arg-type]
        queued=tuple(report["queue"][:admission_shadow.MAX_ATTRIBUTED]),  # type: ignore[index, arg-type]
    )


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
# A word holding percent escapes (``%2Fhome%2Fx``, ``file%3A%2F%2F%2Fx``).
_PERCENT_ENCODED_WORD = re.compile(r"[^\s'\"(),;\[\]<>]*%[0-9A-Fa-f]{2}[^\s'\"(),;\[\]<>]*")
# Decoding rounds for nested escapes (``%252F`` is ``%2F`` is ``/``).
_PERCENT_DECODE_ROUNDS = 3
REDACTED_PATH = "<path>"


def _redact_encoded_word(match: re.Match[str]) -> str:
    word = decoded = match.group(0)
    for _ in range(_PERCENT_DECODE_ROUNDS):
        decoded, previous = urllib.parse.unquote(decoded), decoded
        if decoded == previous:
            break
    return REDACTED_PATH if _PATH_IN_TEXT.search(decoded) else word


def redact_paths(text: str) -> str:
    """``text`` with absolute and home paths replaced by :data:`REDACTED_PATH`.

    Probe and alert details are printed, kept in task records and
    published to Fleet Comms; host paths must not reach any of them. A word
    whose percent-decoded form holds a path is replaced whole, so an
    URL-encoded path is redacted too.
    """
    return _PATH_IN_TEXT.sub(REDACTED_PATH, _PERCENT_ENCODED_WORD.sub(_redact_encoded_word, text))


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
        lines.append(
            "Act: remove settled dispatch worktrees with "
            "`python -m scripts.orchestration.worktree_claims remove` and clear other disk use. "
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


def check_disk(limits: Thresholds) -> tuple[DiskCheck, str | None]:
    """Measure the disk; return the check and any failure.

    Only a disk at or above ``disk_refuse_used_percent`` fails: the check is
    then ``refused``, a hard stop. An unreadable disk passes; the reason is
    logged and shown.
    """
    probe = probe_disk()
    used = probe.used_percent
    if used is None:
        log = _logger.debug if probe.skipped == TEST_HOST_POOL_SKIP else _logger.warning
        log("dispatch admission: disk check skipped: %s", probe.skipped)
        return DiskCheck(probe=probe), None
    check = DiskCheck(probe=probe)
    if used < limits.disk_refuse_used_percent:
        return check, None
    return replace(check, refused=True), (
        f"{probe.text()} on the .worktrees filesystem is at or above the refuse threshold of "
        f"{limits.disk_refuse_used_percent:g}% ({ENV_DISK_REFUSE_USED_PERCENT}={limits.disk_refuse_used_percent:g})"
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


def iter_active_records(tasks_dir: Path) -> Iterator[tuple[Path, dict[str, Any]]]:
    """Every hot ``running`` or ``spawning`` task record, as stored.

    Each record file is read once and parsed only when its bytes name an
    active status, so terminal history costs a read, not a JSON parse.
    Snapshot sidecars are never loaded. Unreadable or malformed records are
    skipped.
    """
    for path in task_record_store.iter_task_records(tasks_dir, include_archive=False):
        try:
            raw = path.read_bytes()
        except OSError:
            continue
        if not any(marker in raw for marker in _ACTIVE_STATUS_MARKERS):
            continue
        try:
            state = json.loads(raw)
        except ValueError:
            continue
        if isinstance(state, dict) and state.get("status") in ACTIVE_STATUSES:
            yield path, state


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
    for path, state in iter_active_records(tasks_dir):
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


def host_failures(probe: HostProbe, limits: Thresholds) -> list[str]:
    """The memory-floor and load-limit failures for ``probe``; an unknown value never fails."""
    failures: list[str] = []
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
    return failures


def observe_pressure(
    probe: HostProbe,
    limits: Thresholds,
    *,
    phase: str,
    decision: AdmissionDecision | None = None,
    record: bool = True,
) -> dict[str, Any]:
    """Shadow the CPU gate using only already collected attribution (#10802).

    No task/pool/slot scan is added to the cheap path. These snapshots identify
    participants, not measured CPU owners; unattributed load is always unknown.
    """
    try:
        load = probe.load_per_cpu
        slots = decision.slots if decision else None
        pool = decision.pool if decision else None
        memory = pool.memory if pool else None
        live = decision.live_task_ids if decision and phase == "evaluate" else None
        context = {
            "phase": phase,
            "current_admission_decision": "unknown" if decision is None else "admit" if decision.admitted else "refuse",
            "override_outcome": "unknown: shadow observes checks before force overrides",
            "load_per_cpu": load,
            "load_limit": limits.max_load_per_cpu,
            "load_decision": "unknown" if load is None else "refuse" if load > limits.max_load_per_cpu else "admit",
            "attribution": {
                "live_task_ids": (
                    [admission_shadow.label(t) for t in live[:admission_shadow.MAX_ATTRIBUTED]]
                    if live is not None else None
                ),
                "live_task_count": len(live) if live is not None else None,
                "pool_nonreclaimable_bytes": memory.nonreclaimable if memory else None,
                "pool_limit_bytes": memory.limit if memory else None,
                "test_slot_queue_depth": slots.depth if slots else None,
                "test_slot_pool_size": slots.pool_size if slots else None,
                "test_slot_holders": [
                    {"task_id": admission_shadow.label(h.get("task_id")), "slots": h.get("slots")}
                    for h in slots.holders[:admission_shadow.MAX_ATTRIBUTED]
                ] if slots and slots.depth is not None else None,
                "test_slot_waiters": [
                    {"task_id": admission_shadow.label(h.get("task_id"))}
                    for h in slots.queued[:admission_shadow.MAX_ATTRIBUTED]
                ] if slots and slots.depth is not None else None,
                "cpu_ownership": "unknown: existing snapshots do not measure CPU shares",
                "unattributed_load": "unknown: no per-actor CPU measurement",
                "missing_attribution": "unknown: not collected on cheap path or unavailable",
                "limit": admission_shadow.MAX_ATTRIBUTED,
            },
        }
        pressure = admission_shadow.read_pressure(PROC_ROOT)
        directory = os.environ.get(admission_shadow.DIRECTORY_ENV)
        # Match the existing host-probe seam: tests opt into a private store.
        persistence = (
            "unknown: test journal not configured"
            if "PYTEST_CURRENT_TEST" in os.environ and directory is None
            else "unknown: report-only evaluation" if not record else None
        )
        if persistence is not None:
            return {
                **context,
                "pressure": pressure,
                "psi": admission_shadow.transition(pressure, {}, time.time()),
                "persistence": persistence,
            }
        root = Path(directory) if directory else primary_checkout() / "batch_state" / "admission-shadow"
        return admission_shadow.observe(root, pressure, context)
    except Exception as exc:  # optional diagnostics must never abort admission
        return {
            "phase": phase,
            "psi": {"decision": "unknown", "low_since": None, "reason": "observer_error"},
            "persistence": "unknown: observer_error",
            "observer_error": type(exc).__name__,
        }


def precheck(mode: str, *, thresholds: Thresholds | None = None) -> AdmissionDecision | None:
    """A refusal when this host's memory or load already fails, else ``None`` (#10799).

    Refusal-only: it reads the thresholds, ``/proc`` and the disk usage,
    plus bounded PSI shadow journal state (no task record, sweep, pool or slot probe),
    so dispatch can refuse an overloaded host before its costly preflights.
    The refusal carries the failure text :func:`evaluate` gives. A disk at or
    above its refuse threshold steps aside: :func:`evaluate` keeps its hard
    stop (#10776). ``None`` (an exempt mode,
    memory and load pass or are unknown, or a full disk) admits nothing:
    :func:`evaluate` under :func:`admission_lock` stays the decision. Invalid
    threshold environment variables raise ``ValueError``.
    """
    if mode not in WRITE_CAPABLE_MODES:
        return None
    limits = thresholds or load_thresholds()
    probe = probe_host()
    failures = host_failures(probe, limits)
    if not failures:
        observe_pressure(probe, limits, phase="precheck")
        return None
    disk_used = probe_disk().used_percent
    if disk_used is not None and disk_used >= limits.disk_refuse_used_percent:
        observe_pressure(probe, limits, phase="precheck")
        return None
    decision = AdmissionDecision(
        mode=mode, exempt=False, admitted=False, thresholds=limits, probe=probe, failures=tuple(failures)
    )
    return replace(decision, psi_shadow=observe_pressure(probe, limits, phase="precheck", decision=decision))


def evaluate(
    mode: str,
    tasks_dir: Path,
    *,
    pid_alive: Callable[[int], bool] | None = None,
    record_liveness: Callable[[dict[str, Any]], bool | None] | None = None,
    on_dead: Callable[[Path, dict[str, Any]], None] | None = None,
    thresholds: Thresholds | None = None,
    disk_guard: bool = True,
    record_shadow: bool = True,
) -> AdmissionDecision:
    """Decide whether a ``mode`` dispatch may start a worker on this host now.

    ``on_dead`` receives every active record whose pid is dead or whose
    dispatcher is provably gone (the caller marks it ``crashed``); without it
    the records are only reported. The disk is only measured; only the
    refuse watermark refuses. Report-only callers pass ``record_shadow=False`` to keep PSI diagnostics
    without reading or writing journal state or changing the admission decision.
    ``disk_guard=False``
    (a dispatch that reuses an existing worktree) skips the disk check and
    the alert. Invalid threshold environment variables raise
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
    failures.extend(host_failures(probe, limits))
    pool = probe_pool(limits.worker_mem_reserve_gib)
    if pool.skipped is not None:
        # WARNING, not INFO: callers such as dispatch.py configure no logging,
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
        disk, disk_failure = check_disk(limits)
    if disk_failure is not None:
        failures.append(disk_failure)
    disk_used = disk.probe.used_percent
    if disk_used is not None and disk_used >= limits.disk_alert_used_percent:
        alert = maybe_alert_disk(tasks_dir, disk, limits, refused=disk_failure is not None)
        disk = replace(disk, alert=alert)
    decision = AdmissionDecision(
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
    return replace(
        decision,
        psi_shadow=observe_pressure(probe, limits, phase="evaluate", decision=decision, record=record_shadow),
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
