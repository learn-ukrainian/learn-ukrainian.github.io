"""Operator constants for the evidence tools. Each value carries its reason and its override.

Nothing here is tuned in a PR without a recorded decision; the environment
overrides exist for the live pilot and for tests, not for silent drift.
"""

from __future__ import annotations

import os

# A pinned snapshot keeps the WAL from being checkpointed past its read mark, so
# `data/sources.db-wal` grows for as long as one evidence session runs while the
# ULIF walk commits. The steady-state WAL is ~16 MB and the live file is 9.4 GB;
# 4 GiB is far above any honest session and well below the free-disk floor, so
# a stalled or runaway reader is stopped before it can fill the data volume.
# Decision: #8527 critique SHOULD 1, taken by the driver 2026-09-24.
WAL_CEILING_BYTES = 4 * 1024**3
WAL_CEILING_ENV = "LU_EVIDENCE_WAL_CEILING_BYTES"

# The walk needs room to commit and a checkpoint needs room to fold the WAL back;
# below 10 GiB free on the volume that holds sources.db the reader releases its
# snapshot rather than compete with the writer for the last of the disk.
# Decision: #8527 critique SHOULD 1, taken by the driver 2026-09-24.
FREE_DISK_FLOOR_BYTES = 10 * 1024**3
FREE_DISK_FLOOR_ENV = "LU_EVIDENCE_FREE_DISK_FLOOR_BYTES"


def _limit(env_name: str, default: int) -> int:
    raw = os.environ.get(env_name)
    if raw is None or not raw.strip():
        return default
    value = int(raw)
    if value < 0:
        raise ValueError(f"{env_name} must be a non-negative byte count, got {raw!r}")
    return value


def wal_ceiling_bytes() -> int:
    """Current WAL ceiling: the environment override or the recorded default."""
    return _limit(WAL_CEILING_ENV, WAL_CEILING_BYTES)


def free_disk_floor_bytes() -> int:
    """Current free-disk floor: the environment override or the recorded default."""
    return _limit(FREE_DISK_FLOOR_ENV, FREE_DISK_FLOOR_BYTES)
