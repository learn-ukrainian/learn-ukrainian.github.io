"""PR-I supervisor contract over a temporary session-stream SQLite database."""

from __future__ import annotations

import os
from dataclasses import replace
from pathlib import Path

import pytest

from agents_extensions.shared.session_streams.db import SessionStreamDatabase
from agents_extensions.shared.session_streams.model import LeaseHolder
from agents_extensions.shared.session_streams.store import LeaseConflictError, SessionStreamStore
from scripts.session_supervisor import LaunchRole, SessionSupervisor, SupervisorError, main, strip_lease_credentials


def _supervisor(tmp_path: Path) -> SessionSupervisor:
    store = SessionStreamStore(SessionStreamDatabase(tmp_path / "streams.sqlite3"))
    return SessionSupervisor(store, repo_root=Path.cwd())


def _holder() -> LeaseHolder:
    return LeaseHolder(
        agent="codex",
        harness="native-codex",
        instance_id="codex-supervisor-test",
        process_id=os.getpid(),
        task_id="5512-pr-i",
    )


def test_driver_open_heartbeat_close_and_capsule_are_fenced(tmp_path: Path) -> None:
    supervisor = _supervisor(tmp_path)
    lease = supervisor.open_driver(
        role=LaunchRole.DRIVER,
        stream_id="epic:4707",
        holder=_holder(),
        lineage_id="lineage-supervisor-test",
        ttl_seconds=300,
    )

    capsule = supervisor.build_capsule(role=LaunchRole.DRIVER, stream_id="epic:4707", lease=lease).as_dict()
    assert capsule["identity"]["stream_id"] == "epic:4707"
    assert capsule["identity"]["lease"]["lease_id"] == lease.lease_id
    assert capsule["identity"]["lease_credentials_exported"] is False
    assert capsule["diagnostics"]["lease_actions"] == "supervisor-only"
    assert capsule["dual_write"]["handoff_paths"]
    assert len(capsule["capsule_sha256"]) == 64

    renewed = supervisor.heartbeat_driver(role="driver", lease=lease)
    with pytest.raises(LeaseConflictError):
        supervisor.heartbeat_driver(role="driver", lease=replace(lease, fencing_token=lease.fencing_token + 1))
    assert supervisor.close_driver(role="driver", lease=renewed) == "closed"


def test_workers_cannot_acquire_or_receive_driver_lease(tmp_path: Path) -> None:
    supervisor = _supervisor(tmp_path)
    with pytest.raises(SupervisorError, match="workers cannot acquire"):
        supervisor.open_driver(
            role=LaunchRole.WORKER,
            stream_id="epic:4707",
            holder=_holder(),
            lineage_id="lineage-worker-refusal",
            ttl_seconds=300,
        )

    lease = supervisor.open_driver(
        role="driver",
        stream_id="epic:4707",
        holder=_holder(),
        lineage_id="lineage-worker-capsule",
        ttl_seconds=300,
    )
    with pytest.raises(SupervisorError, match="cannot receive"):
        supervisor.build_capsule(role="worker", stream_id="epic:4707", lease=lease)

    worker = supervisor.build_capsule(role="worker", stream_id="epic:4707").as_dict()
    assert worker["identity"]["lease"] is None
    with pytest.raises(SupervisorError, match="require an exact"):
        supervisor.build_capsule(role="driver", stream_id="epic:4707")


def test_worker_environment_strips_every_lease_credential() -> None:
    environment = {
        "SESSION_STREAM_LEASE_ID": "lease-private",
        "SESSION_STREAM_FENCING_TOKEN": "7",
        "KEEP_ME": "safe",
    }
    assert strip_lease_credentials(environment) == {"KEEP_ME": "safe"}


def test_open_driver_auto_recovers_expired_dead_holder(tmp_path: Path) -> None:
    """Launcher open must recover claimable crashed sessions without a manual step."""
    from datetime import timedelta

    from agents_extensions.shared.session_streams.model import utc_now

    supervisor = _supervisor(tmp_path)
    dead_pid = 999_999_001
    assert not _pid_alive(dead_pid)

    opened_at = utc_now() - timedelta(hours=7)
    supervisor.store.open_session(
        stream_id="epic:4707",
        holder=LeaseHolder(
            agent="grok",
            harness="grok-tui",
            instance_id="grok-dead-holder",
            process_id=dead_pid,
            task_id="stale",
        ),
        lineage_id="lineage-stale",
        ttl_seconds=300,
        now=opened_at,
    )
    successor = supervisor.open_driver(
        role="driver",
        stream_id="epic:4707",
        holder=LeaseHolder(
            agent="grok",
            harness="grok-tui",
            instance_id="grok-fresh-launcher",
            process_id=os.getpid(),
            task_id="fresh-open",
        ),
        lineage_id="lineage-fresh",
        ttl_seconds=300,
    )
    assert successor.holder.instance_id == "grok-fresh-launcher"
    assert successor.session_id != "session-stale"


def test_open_driver_refuses_live_unexpired_holder(tmp_path: Path) -> None:
    supervisor = _supervisor(tmp_path)
    live = supervisor.open_driver(
        role="driver",
        stream_id="epic:4707",
        holder=_holder(),
        lineage_id="lineage-live",
        ttl_seconds=3600,
    )
    with pytest.raises(SupervisorError, match="already has live session"):
        supervisor.open_driver(
            role="driver",
            stream_id="epic:4707",
            holder=LeaseHolder(
                agent="grok",
                harness="grok-tui",
                instance_id="grok-other",
                process_id=os.getpid(),
            ),
            lineage_id="lineage-other",
            ttl_seconds=300,
        )
    assert supervisor.close_driver(role="driver", lease=live) == "closed"


def test_recover_expired_driver_force_closes_claimable(tmp_path: Path) -> None:
    from datetime import timedelta

    from agents_extensions.shared.session_streams.model import utc_now

    supervisor = _supervisor(tmp_path)
    dead_pid = 999_999_002
    assert not _pid_alive(dead_pid)
    supervisor.store.open_session(
        stream_id="epic:4707",
        holder=LeaseHolder(
            agent="grok",
            harness="grok-tui",
            instance_id="grok-dead-2",
            process_id=dead_pid,
        ),
        lineage_id="lineage-dead-2",
        ttl_seconds=60,
        now=utc_now() - timedelta(hours=2),
    )
    holder = LeaseHolder(
        agent="grok",
        harness="grok-tui",
        instance_id="grok-recover-cli",
        process_id=os.getpid(),
    )
    assert supervisor.recover_expired_driver(
        role="driver", stream_id="epic:4707", holder=holder
    ) is True
    # Second recover finds nothing open.
    assert supervisor.recover_expired_driver(
        role="driver", stream_id="epic:4707", holder=holder
    ) is False


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def test_cli_refuses_worker_open_attempt(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(
        [
            "--db",
            str(tmp_path / "streams.sqlite3"),
            "--repo-root",
            str(Path.cwd()),
            "open",
            "--role",
            "worker",
            "--stream",
            "epic:4707",
            "--agent",
            "agy",
            "--harness",
            "agy-bridge",
            "--instance-id",
            "worker-attempt",
            "--process-id",
            str(os.getpid()),
            "--lineage-id",
            "worker-lineage",
        ]
    )
    assert exit_code == 4
    assert "workers cannot acquire" in capsys.readouterr().err
