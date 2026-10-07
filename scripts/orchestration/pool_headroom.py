"""Shared ``lu.slice`` pool headroom from cgroup v2 counters (#9975).

``lu.slice`` is the capped memory pool that drivers and dispatch workers share
(``packaging/systemd/lu.slice``: ``MemoryHigh=24G``, ``MemoryMax=26G``, #9624).
``lu-dispatch.slice`` can show several GiB free while drivers hold the same
pool, so dispatch admission and the nightly data tier also check the pool.

Raw ``memory.current`` counts page cache, which the kernel reclaims before it
throttles at ``memory.high``; on an idle host that overstates use by several
GiB. Use here is non-reclaimable: ``memory.current`` minus ``active_file`` and
``inactive_file`` from ``memory.stat``. Shared memory (tmpfs, shm) sits on the
anon LRU lists, so it stays counted.

A new write worker fits when the pool's non-reclaimable use plus a per-worker
reserve stays at or below ``memory.high`` (``memory.max`` when ``high`` is
unset). Missing or unreadable cgroup files (CI, macOS, a host without the pool)
skip the check with a reason; nothing here raises on a missing file.

Stdlib-only.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

CGROUP_ROOT = Path("/sys/fs/cgroup")
POOL_SLICE = "lu.slice"
# Same override name as scripts/ops/lu_slice_apply.sh.
ENV_LU_SLICE_CGROUP = "LU_SLICE_CGROUP"

_GIB = 1024**3


@dataclass(frozen=True)
class SliceMemory:
    """One sample of a slice's cgroup memory counters, in bytes."""

    current: int
    file_cache: int
    high: int | None
    max: int | None

    @property
    def nonreclaimable(self) -> int:
        return max(self.current - self.file_cache, 0)

    @property
    def limit(self) -> int | None:
        """``memory.high``, or ``memory.max`` when ``high`` is unset; ``None`` when uncapped."""
        return self.high if self.high is not None else self.max

    @property
    def limit_name(self) -> str:
        return "MemoryHigh" if self.high is not None else "MemoryMax"


@dataclass(frozen=True)
class PoolCheck:
    """Whether one more worker of ``reserve_bytes`` fits under the pool limit."""

    reserve_bytes: int
    memory: SliceMemory | None = None
    skipped: str | None = None

    @property
    def headroom_bytes(self) -> int | None:
        if self.memory is None or self.memory.limit is None:
            return None
        return self.memory.limit - self.memory.nonreclaimable

    @property
    def fits(self) -> bool:
        headroom = self.headroom_bytes
        return headroom is None or self.reserve_bytes <= headroom

    def clause(self) -> str:
        """Measured pool use against its limit, for an admission line."""
        if self.memory is None:
            return f"{POOL_SLICE} pool check skipped ({self.skipped or 'no sample'})"
        used = self.memory.nonreclaimable / _GIB
        cache = self.memory.file_cache / _GIB
        limit = self.memory.limit
        if limit is None:
            return f"{POOL_SLICE} {used:.1f} GiB non-cache (+{cache:.1f} GiB file cache, no limit)"
        return (
            f"{POOL_SLICE} {used:.1f}/{limit / _GIB:.1f} GiB non-cache "
            f"(+{cache:.1f} GiB file cache; worker reserve {self.reserve_bytes / _GIB:g} GiB)"
        )

    def failure(self) -> str:
        """Refusal text with value and threshold; meaningful only when not :attr:`fits`."""
        memory = self.memory
        if memory is None or memory.limit is None:
            return f"{POOL_SLICE} pool headroom unknown"
        return (
            f"{POOL_SLICE} non-cache use {memory.nonreclaimable / _GIB:.1f} GiB plus a "
            f"{self.reserve_bytes / _GIB:g} GiB worker reserve exceeds {memory.limit_name} "
            f"{memory.limit / _GIB:.1f} GiB"
        )


def default_pool_cgroup(environ: Mapping[str, str] | None = None) -> Path:
    """This user's ``lu.slice`` cgroup directory, or ``$LU_SLICE_CGROUP``."""
    env = os.environ if environ is None else environ
    override = env.get(ENV_LU_SLICE_CGROUP, "").strip()
    if override:
        return Path(override)
    uid = os.getuid()
    return CGROUP_ROOT / f"user.slice/user-{uid}.slice/user@{uid}.service" / POOL_SLICE


def cgroup_dir(control_group: str | None) -> Path | None:
    """Directory for a systemd ``ControlGroup`` value; ``None`` when absent or unsafe."""
    if not control_group or not control_group.startswith("/") or ".." in control_group.split("/"):
        return None
    return CGROUP_ROOT / control_group.lstrip("/")


def file_cache_bytes(directory: Path) -> int | None:
    """``active_file + inactive_file`` from ``memory.stat``; ``None`` when unreadable."""
    try:
        text = (directory / "memory.stat").read_text(encoding="ascii", errors="replace")
    except OSError:
        return None
    stats: dict[str, int] = {}
    for line in text.splitlines():
        fields = line.split()
        if len(fields) == 2 and fields[0] in {"active_file", "inactive_file"}:
            try:
                stats[fields[0]] = int(fields[1])
            except ValueError:
                return None
    if len(stats) != 2:
        return None
    return stats["active_file"] + stats["inactive_file"]


def _read_limit(path: Path) -> int | None:
    """A ``memory.high``/``memory.max`` value; ``max``, missing or invalid is ``None``."""
    try:
        raw = path.read_text(encoding="ascii").strip()
    except OSError:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def read_slice_memory(directory: Path) -> SliceMemory | str:
    """Sample a slice's counters, or a reason string when they cannot be read."""
    name = directory.name or str(directory)
    try:
        raw = (directory / "memory.current").read_text(encoding="ascii").strip()
    except OSError as exc:
        return f"{name} memory.current unavailable: {exc.strerror or type(exc).__name__}"
    try:
        current = int(raw)
    except ValueError:
        return f"{name} memory.current is not a number"
    cache = file_cache_bytes(directory)
    if cache is None:
        return f"{name} memory.stat has no active_file/inactive_file"
    return SliceMemory(
        current=current,
        file_cache=cache,
        high=_read_limit(directory / "memory.high"),
        max=_read_limit(directory / "memory.max"),
    )


def check_pool(reserve_bytes: int, directory: Path | None = None) -> PoolCheck:
    """Whether one more worker of ``reserve_bytes`` fits in ``lu.slice`` now. Never raises on missing files."""
    sample = read_slice_memory(directory if directory is not None else default_pool_cgroup())
    if isinstance(sample, str):
        return PoolCheck(reserve_bytes=reserve_bytes, skipped=sample)
    return PoolCheck(reserve_bytes=reserve_bytes, memory=sample)
