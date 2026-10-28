"""Change-only cto alert for the disk reap watermark (#10871).

The scheduled worktree cleanup calls :func:`check_and_alert` after its sweep
with the disk usage of the filesystem holding ``.worktrees/``. The first
reading at or above ``DISPATCH_DISK_REAP_USED_PERCENT`` posts one report to the
cto Fleet Comms channel and records the disk as above; later readings stay
quiet while it stays above. A reading below the watermark clears the record, so
the next crossing alerts again. A publish that fails leaves the record unchanged
so the next run retries.
The locked transaction persists the exact message and a per-crossing key before
publishing, so state I/O failures replay Fleet's existing durable publication.

It reuses the backup alert's publisher and state files
(:mod:`scripts.orchestration.backup_failure_alert`) rather than adding a bus.
"""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from scripts.orchestration import backup_failure_alert as alerts
from scripts.orchestration import dispatch_admission as admission

STATE_NAME = "disk-watermark-alert.json"
_ABOVE = "above"


def alert_message(probe: admission.DiskProbe, limits: admission.Thresholds, now: str) -> str:
    return (
        f"[{alerts.SENDER}] {probe.text()} on the .worktrees filesystem at {now}, still at or above the reap "
        f"watermark of {limits.disk_reap_used_percent:g}% after the scheduled worktree cleanup. New write "
        f"dispatches are refused at {limits.disk_refuse_used_percent:g}%.\n"
        "Act: remove settled dispatch worktrees with "
        "`python -m scripts.orchestration.worktree_claims remove` and clear other disk use.\n"
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

    Raises ``ValueError`` for invalid thresholds, ``OSError`` for state I/O and
    :class:`~scripts.orchestration.backup_failure_alert.AlertError` when the
    publish fails. An unreadable disk changes nothing.
    """
    limits = limits or admission.load_thresholds()
    path = state_dir / STATE_NAME
    with alerts.state_lock(path):
        return _check_locked(path, project_root, limits, probe, publish, now)


def _check_locked(
    path: Path,
    project_root: Path,
    limits: admission.Thresholds,
    probe: admission.DiskProbe | None,
    publish: alerts.Publisher | None,
    now: str | None,
) -> str:
    probe = probe or admission.probe_disk()
    used = probe.used_percent
    if used is None:
        return f"disk watermark alert skipped: {probe.text()}"
    send = publish or alerts.fleet_comms_publisher(project_root)
    alerts.finish_pending(path, send)
    already_above = alerts.read_state(path).get("state") == _ABOVE
    if used < limits.disk_reap_used_percent:
        if already_above:
            alerts.clear_state(path)
            return f"disk {used:.1f}% used is below the reap watermark; alert re-armed"
        return f"disk {used:.1f}% used is below the reap watermark"
    if already_above:
        return f"disk {used:.1f}% used is above the reap watermark; already reported, not re-posting"
    stamp = now or alerts.utc_now()
    alerts.publish_transition(
        path,
        send,
        alert_message(probe, limits, stamp),
        f"lu-disk-watermark:{uuid4().hex}",
        {"state": _ABOVE, "since_utc": stamp},
    )
    return f"disk {used:.1f}% used crossed the reap watermark; reported to the {alerts.CHANNEL} channel"
