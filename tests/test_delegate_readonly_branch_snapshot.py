"""#10404: direct branch reviews preserve occupied author checkouts."""

from __future__ import annotations

from pathlib import Path

from scripts.orchestration.dead_worker_state import capture_worker_identity, worker_liveness


def _fake_worker_pid() -> int:
    """Return a PID above the kernel's allocatable range (#11406).

    A fabricated PID inside ``pid_max`` can alias a live process. Launch then
    records that process's start time, ``worker_liveness`` reports the fake
    worker alive, and its own terminal record blocks settle as an active
    claim. PIDs above ``pid_max`` are never allocated, so there is no alias.
    """
    try:
        return int(Path("/proc/sys/kernel/pid_max").read_text(encoding="ascii").strip()) + 1000
    except (OSError, ValueError):
        return 5_000_000


def test_fabricated_worker_pid_cannot_alias_a_live_process():
    """#11406: a fake worker PID inside ``pid_max`` can be a live process and block its own settle.

    ``_settle_worktree_reap`` exempts the settling task's own record only when
    ``_worker_blocks_release`` sees no live worker. A fabricated PID that
    aliases a live process makes ``worker_liveness`` report the fake worker
    alive, so the record written as ``done`` still claims the snapshot it
    created and removal is skipped. The fabricated PID must therefore sit
    outside the kernel's allocatable range.
    """
    pid = _fake_worker_pid()
    pid_max = int(Path("/proc/sys/kernel/pid_max").read_text(encoding="ascii").strip())
    assert pid > pid_max, f"fabricated worker pid {pid} can alias a live process (pid_max={pid_max})"
    assert worker_liveness({"pid": pid, "worker_identity": capture_worker_identity(pid)}) is False
