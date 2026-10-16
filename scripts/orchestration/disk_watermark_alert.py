"""Change-only cto alert for the disk reap watermark (#10871).

The scheduled worktree cleanup calls :func:`check_and_alert` after its sweep
with the disk usage of the filesystem holding ``.worktrees/``. The first
reading at or above ``DISPATCH_DISK_REAP_USED_PERCENT`` posts one report to the
cto Fleet Comms channel and records the disk as above; later readings stay
quiet while it stays above. A reading below the watermark clears the record, so
the next crossing alerts again. A publish that fails leaves the record unchanged
so the next run retries.

It reuses the backup alert's publisher and state files
(:mod:`scripts.orchestration.backup_failure_alert`) rather than adding a bus.
"""

from __future__ import annotations

from pathlib import Path

from scripts.orchestration import backup_failure_alert as alerts
from scripts.orchestration import dispatch_admission as admission

STATE_NAME = "disk-watermark-alert.json"
_ABOVE = "above"


def alert_message(probe: admission.DiskProbe, limits: admission.Thresholds, now: str) -> str:
    return (
        f"[{alerts.SENDER}] {probe.text()} on the .worktrees filesystem at {now}, still at or above the reap "
        f"watermark of {limits.disk_reap_used_percent:g}% after the scheduled worktree cleanup. New write "
        f"dispatches are refused at {limits.disk_refuse_used_percent:g}%.\n"
        "Act: reap settled dispatch worktrees with the common reaper and clear other disk use.\n"
        f"Change-only: no further alert until usage falls below {limits.disk_reap_used_percent:g}% and crosses again.\n"
    )


def check_and_alert(
    state_dir: Path,
    project_root: Path,
    *,
    limits: admission.Thresholds | None = None,
    probe: admission.DiskProbe | None = None,
    publish: alerts.Publisher | None = None,
    now: str | None = None,
) -> str:
    """Alert once per crossing of the reap watermark; return what happened.

    Raises ``ValueError`` for invalid thresholds and
    :class:`~scripts.orchestration.backup_failure_alert.AlertError` when the
    publish fails. An unreadable disk changes nothing.
    """
    limits = limits or admission.load_thresholds()
    probe = probe or admission.probe_disk()
    used = probe.used_percent
    if used is None:
        return f"disk watermark alert skipped: {probe.text()}"
    path = state_dir / STATE_NAME
    already_above = alerts.read_state(path).get("state") == _ABOVE
    if used < limits.disk_reap_used_percent:
        if already_above:
            path.unlink(missing_ok=True)
            return f"disk {used:.1f}% used is below the reap watermark; alert re-armed"
        return f"disk {used:.1f}% used is below the reap watermark"
    if already_above:
        return f"disk {used:.1f}% used is above the reap watermark; already reported, not re-posting"
    stamp = now or alerts.utc_now()
    send = publish or alerts.fleet_comms_publisher(project_root)
    send(alert_message(probe, limits, stamp), f"lu-disk-watermark:{stamp}")
    alerts.write_state(path, {"state": _ABOVE, "since_utc": stamp})
    return f"disk {used:.1f}% used crossed the reap watermark; reported to the {alerts.CHANNEL} channel"
