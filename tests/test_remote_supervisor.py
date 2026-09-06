"""Stdlib remote client and CLI output/fail-closed contract."""

from __future__ import annotations

import io
import json
import urllib.error
from pathlib import Path

import pytest

from agents_extensions.shared.session_streams.model import LeaseHolder
from scripts.session_supervisor import main
from scripts.session_supervisor.remote import RemoteEpicClient, RemoteSupervisorError, RemoteUnreachableError


class _Response:
    def __init__(self, payload: dict[str, object], status: int = 200) -> None:
        self.payload = payload
        self.status = status

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *_args: object) -> None:
        return None


def _lease_payload() -> dict[str, object]:
    return {
        "stream_id": "epic:7178",
        "session_id": "session-client",
        "lease_id": "lease-client",
        "state": "active",
        "generation": 1,
        "fencing_token": 1,
        "heartbeat_at": "2026-08-23T00:00:00Z",
        "expires_at": "2026-08-23T00:15:00Z",
        "ttl_seconds": 900,
        "version": 1,
        "holder": {
            "agent": "codex",
            "harness": "codex-cli",
            "instance_id": "client-instance",
            "process_id": 1234,
            "holder_kind": "process",
            "host_id": "client-host",
            "task_id": None,
        },
    }


def test_remote_claim_preflights_health_and_emits_one_json_document(monkeypatch, capsys) -> None:
    calls: list[str] = []

    def opener(request: object, timeout: int = 0) -> _Response:
        del timeout
        path = str(getattr(request, "full_url", "")).split("8765", 1)[-1]
        calls.append(path)
        if path.startswith("/api/epics/v1/health"):
            return _Response({"schema": "remote-epic-lifecycle.v1", "ok": True})
        if path.startswith("/api/epics/v1/epic:7178/claim"):
            return _Response(
                {
                    "schema": "remote-epic-lifecycle.v1",
                    "stream_id": "epic:7178",
                    "lease": _lease_payload(),
                    "digest": {
                        "stream_id": "epic:7178",
                        "limit": 20,
                        "high_water_entry_id": 0,
                        "pinned": [],
                        "recent": [],
                    },
                }
            )
        return _Response(
            {
                "schema": "remote-epic-lifecycle.v1",
                "stream_id": "epic:7178",
                "lease": _lease_payload(),
                "session_state": "open",
                "digest": {"stream_id": "epic:7178", "limit": 20, "high_water_entry_id": 0, "pinned": [], "recent": []},
            }
        )

    monkeypatch.setattr("urllib.request.urlopen", opener)
    # allow-hardcoded-epic: remote supervisor request fixture
    assert (
        main(
            [
                "claim",
                "--role",
                "driver",
                "--stream",
                "epic:7178",
                "--agent",
                "codex",
                "--harness",
                "codex-cli",
                "--instance-id",
                "client-instance",
                "--process-id",
                "1234",
                "--host-id",
                "client-host",
                "--lineage-id",
                "client-lineage",
            ]
        )
        == 0
    )
    output = capsys.readouterr()
    assert json.loads(output.out)["schema"] == "session-supervisor-bootstrap.v1"
    assert calls[0].startswith("/api/epics/v1/health")
    assert any(
        path.startswith("/api/epics/v1/epic:7178/claim") for path in calls
    )  # allow-hardcoded-epic: remote supervisor request fixture


def test_remote_claim_fail_closed_without_api_and_does_not_post() -> None:
    calls: list[str] = []

    def opener(request: object, timeout: int = 0) -> _Response:
        del timeout
        calls.append(str(getattr(request, "method", "")))
        raise urllib.error.URLError("offline")

    client = RemoteEpicClient(opener=opener)
    try:
        client.claim(
            stream_id="epic:7178",
            holder=LeaseHolder("codex", "codex-cli", "offline", process_id=1, host_id="offline-host"),
            lineage_id="offline-lineage",
        )
    except RemoteUnreachableError:
        pass
    else:  # pragma: no cover - assertion branch
        raise AssertionError("unreachable Monitor API must refuse the claim")
    assert calls == ["GET"]


def test_remote_claim_missing_epics_route_explains_deployment_remedy() -> None:
    def opener(request: object, timeout: int = 0) -> _Response:
        del timeout
        raise urllib.error.HTTPError(
            str(getattr(request, "full_url", "")),
            404,
            "Not Found",
            {},
            io.BytesIO(b'{"detail":"Not Found"}'),
        )

    client = RemoteEpicClient(opener=opener)
    with pytest.raises(
        RemoteSupervisorError,
        match=r"missing route /api/epics/v1/health.*deploy a Monitor build that includes /api/epics/v1",
    ):
        client.claim(
            stream_id="epic:7178",
            holder=LeaseHolder("codex", "codex-cli", "missing-route", process_id=1, host_id="missing-host"),
            lineage_id="missing-route-lineage",
        )


def test_remote_claim_fail_closed_when_health_is_unhealthy() -> None:
    calls: list[str] = []

    def opener(request: object, timeout: int = 0) -> _Response:
        del timeout
        calls.append(str(getattr(request, "method", "")))
        return _Response({"schema": "remote-epic-lifecycle.v1", "ok": False})

    client = RemoteEpicClient(opener=opener)
    with pytest.raises(RemoteSupervisorError, match="health check failed"):
        client.claim(
            stream_id="epic:7178",
            holder=LeaseHolder("codex", "codex-cli", "unhealthy", process_id=1, host_id="unhealthy-host"),
            lineage_id="unhealthy-lineage",
        )
    assert calls == ["GET"]


def test_local_flag_warns_and_keeps_stdout_as_one_json_document(tmp_path: Path, capsys) -> None:
    # allow-hardcoded-epic: local supervisor request fixture
    assert (
        main(
            [
                "--local",
                "--db",
                str(tmp_path / "local.sqlite3"),
                "open",
                "--role",
                "driver",
                "--stream",
                "epic:7178",
                "--agent",
                "codex",
                "--harness",
                "codex-cli",
                "--instance-id",
                "local-instance",
                "--process-id",
                "1234",
                "--lineage-id",
                "local-lineage",
            ]
        )
        == 0
    )
    output = capsys.readouterr()
    assert "LOCAL-ONLY LEASE — not visible to the fleet" in output.err
    json.loads(output.out)


@pytest.mark.parametrize("mismatch", ["fencing_token", "session_id", "released", "missing"])
def test_successor_capsule_refuses_lost_live_authority(tmp_path: Path, mismatch) -> None:
    from scripts.session_supervisor import SessionSupervisor
    from scripts.session_supervisor.remote import RemoteLeaseLostError

    original = _lease_payload()
    current = _lease_payload()
    current["state"] = "active"
    if mismatch == "released":
        current["state"] = "released"
    elif mismatch == "fencing_token":
        current["fencing_token"] = 2
    elif mismatch == "session_id":
        current["session_id"] = "successor-session"
    client = RemoteEpicClient(opener=lambda *a, **kw: _Response({
        "lease": None if mismatch == "missing" else current,
        "digest": {"stream_id": "epic:7178", "limit": 20, "pinned": [], "recent": []},
    }))
    holder = LeaseHolder(agent="codex", harness="cli", instance_id="fixture", process_id=1234)
    lease = client._lease_from_response(original, holder)
    supervisor = SessionSupervisor(None, repo_root=tmp_path, remote=client)
    with pytest.raises(RemoteLeaseLostError):
        supervisor.build_capsule(role="driver", stream_id=lease.stream_id, lease=lease)


def test_remote_successor_real_api_cycle_preserves_handoff_and_fences_predecessor(tmp_path: Path) -> None:
    from agents_extensions.shared.session_streams.db import SessionStreamDatabase
    from agents_extensions.shared.session_streams.store import SessionStreamStore
    from scripts.session_supervisor import SessionSupervisor, SupervisorError
    from scripts.session_supervisor.remote import RemoteLeaseLostError
    from tests.epics_monitor_stub import epics_monitor_stub

    store = SessionStreamStore(SessionStreamDatabase(tmp_path / "cycle.sqlite3"))
    first = LeaseHolder("codex", "cli", "predecessor", process_id=1234, host_id="fixture-host")
    second = LeaseHolder("codex", "cli", "successor", process_id=5678, host_id="other-fixture")
    with epics_monitor_stub(store) as base:
        supervisor = SessionSupervisor(store, repo_root=tmp_path, remote=RemoteEpicClient(base=base))
        lease = supervisor.open_driver(role="driver", stream_id="epic:7178", holder=first, lineage_id="cycle", ttl_seconds=900)
        entry = supervisor.handoff_driver(role="driver", lease=lease, entry_type="state", body="Prepared continuity: verify outstanding work before dispatch.", idempotency_key="cycle-handoff")
        before = store.dump_stream(lease.stream_id)
        with pytest.raises(RemoteSupervisorError, match="live session"):
            supervisor.open_driver(role="driver", stream_id=lease.stream_id, holder=second, lineage_id="cycle", ttl_seconds=900)
        with pytest.raises(SupervisorError, match="remote recovery"):
            supervisor.recover_expired_driver(role="driver", stream_id=lease.stream_id, holder=second)
        assert store.dump_stream(lease.stream_id) == before
        assert supervisor.close_driver(role="driver", lease=lease) == "closed"
        successor = supervisor.open_driver(role="driver", stream_id=lease.stream_id, holder=second, lineage_id="cycle", ttl_seconds=900)
        capsule = supervisor.build_capsule(role="driver", stream_id=lease.stream_id, lease=successor)
        assert successor.generation == lease.generation + 1
        assert any(item.entry_id == entry["entry"]["entry_id"] for item in capsule.digest.recent)
        with pytest.raises(RemoteLeaseLostError):
            supervisor.close_driver(role="driver", lease=lease)
        with pytest.raises(RemoteLeaseLostError):
            supervisor.build_capsule(role="driver", stream_id=lease.stream_id, lease=lease)
        assert supervisor.close_driver(role="driver", lease=successor) == "closed"


@pytest.fixture
def supervisory_cycle(tmp_path):
    from agents_extensions.shared.session_streams.db import SessionStreamDatabase
    from agents_extensions.shared.session_streams.store import SessionStreamStore
    from scripts.fleet_comms.authority import AuthorityService
    from scripts.session_supervisor import SessionSupervisor
    from tests.epics_monitor_stub import epics_monitor_stub

    store = SessionStreamStore(SessionStreamDatabase(tmp_path / "wake.sqlite3"))
    with AuthorityService(root=tmp_path / "fleet") as service, epics_monitor_stub(store) as base:
        supervisor = SessionSupervisor(None, repo_root=tmp_path, remote=RemoteEpicClient(base=base))
        yield service, supervisor


def _supervisory_event(service, *, action="restart", generation=1, key="restart-event"):
    from scripts.ai_agent_bridge._inbox_watch import supervisory_recipient

    return service.publish_message(
        sender="fixture-operator", recipients=(supervisory_recipient("epic:7178"),),
        body=json.dumps({"schema": "supervisory-wake.v1", "action": action,
                         "stream_id": "epic:7178", "generation": generation}),
        kind="supervisory-request", correlation_id="fixture-cycle", idempotency_key=key,
    ).delivery_ids[0]


def _open_supervisory_driver(supervisor, *, instance="predecessor", session_id=None):
    return supervisor.open_driver(
        role="driver", stream_id="epic:7178",
        holder=LeaseHolder("codex", "cli", instance, process_id=1234, host_id="fixture-host"),
        lineage_id="wake-cycle", ttl_seconds=900, session_id=session_id,
    )


def test_supervisory_duplicate_wake_never_starts_second_live_driver(supervisory_cycle):
    from unittest.mock import Mock

    from scripts.ai_agent_bridge._inbox_watch import supervisory_launch_plan, wake_driver_once

    service, supervisor = supervisory_cycle
    lease = _open_supervisory_driver(supervisor)
    did = _supervisory_event(service, action="wake")
    assert _supervisory_event(service, action="wake") == did
    start = Mock()
    for _ in range(2):
        assert supervisory_launch_plan(service, supervisor.remote, did, lease.stream_id) is None
        assert not wake_driver_once(service, supervisor.remote, stream_id=lease.stream_id,
                                    launcher=Path("start-codex-driver.sh"), epic="fixture", run=start)
    start.assert_not_called()
    with pytest.raises(RemoteSupervisorError, match="live session"):
        _open_supervisory_driver(supervisor, instance="duplicate")
    assert service.supervisory_delivery_status(did) == "queued"
    assert supervisor.close_driver(role="driver", lease=lease) == "closed"


def test_supervisory_consumed_released_generation_starts_exactly_one_successor(supervisory_cycle):
    from datetime import UTC, datetime, timedelta
    from types import SimpleNamespace

    from scripts.ai_agent_bridge._inbox_watch import (
        consume_supervisory_event,
        supervisory_launch_plan,
        wake_driver_once,
    )

    service, supervisor = supervisory_cycle
    lease = _open_supervisory_driver(supervisor)
    did = _supervisory_event(service)
    now = datetime.now(UTC)
    request = consume_supervisory_event(service, supervisor, lease, now=now.isoformat())
    assert request.delivery_id == did
    assert service.supervisory_delivery_status(did) == "live_driver_consumed"
    assert supervisory_launch_plan(service, supervisor.remote, did, lease.stream_id) is None
    assert supervisor.close_driver(role="driver", lease=lease) == "closed"
    plan = supervisory_launch_plan(service, supervisor.remote, did, lease.stream_id)
    assert plan == request
    starts = []

    def start(argv, *, env, check):
        assert argv == ["start-codex-driver.sh", "--epic", "fixture"]
        assert env["SESSION_SUPERVISOR_WAKE_DELIVERY"] == did
        assert not any(name.startswith("SESSION_STREAM_") for name in env)
        starts.append(_open_supervisory_driver(
            supervisor, instance="successor", session_id=plan.successor_session_id,
        ))
        return SimpleNamespace(returncode=0)

    assert wake_driver_once(service, supervisor.remote, stream_id=lease.stream_id,
                            launcher=Path("start-codex-driver.sh"), epic="fixture", run=start)
    assert not wake_driver_once(service, supervisor.remote, stream_id=lease.stream_id,
                                launcher=Path("start-codex-driver.sh"), epic="fixture", run=start)
    successor, = starts
    assert successor.generation == lease.generation + 1
    assert supervisory_launch_plan(service, supervisor.remote, did, lease.stream_id) is None
    # Reclamation is via the delivery API's TTL/fence, never a copied old token.
    consume_supervisory_event(service, supervisor, successor, now=(now + timedelta(seconds=61)).isoformat())
    assert service.supervisory_delivery_status(did) == "acted_on"
    assert service.get_delivery(did).fence_token == 2
    assert supervisor.close_driver(role="driver", lease=successor) == "closed"
    assert supervisory_launch_plan(service, supervisor.remote, did, lease.stream_id) is None
    assert not wake_driver_once(service, supervisor.remote, stream_id=lease.stream_id,
                                launcher=Path("start-codex-driver.sh"), epic="fixture", run=start)
    assert len(starts) == 1


def test_supervisory_clean_release_without_preparation_cannot_restart(supervisory_cycle):
    from scripts.ai_agent_bridge._inbox_watch import supervisory_launch_plan

    service, supervisor = supervisory_cycle
    lease = _open_supervisory_driver(supervisor)
    did = _supervisory_event(service)
    assert supervisor.close_driver(role="driver", lease=lease) == "closed"
    assert supervisory_launch_plan(service, supervisor.remote, did, lease.stream_id) is None


def test_supervisory_stale_envelope_cannot_consume_or_prepare(supervisory_cycle):
    from scripts.ai_agent_bridge._inbox_watch import consume_supervisory_event
    from scripts.session_supervisor.remote import RemoteLeaseLostError

    service, supervisor = supervisory_cycle
    lease = _open_supervisory_driver(supervisor)
    did = _supervisory_event(service)
    assert supervisor.close_driver(role="driver", lease=lease) == "closed"
    successor = _open_supervisory_driver(supervisor, instance="successor")
    with pytest.raises(RemoteLeaseLostError):
        consume_supervisory_event(service, supervisor, lease)
    assert service.supervisory_delivery_status(did) == "queued"
    assert supervisor.close_driver(role="driver", lease=successor) == "closed"


@pytest.mark.parametrize("released_before_crash", [False, True])
def test_prepared_restart_survives_process_loss_without_early_takeover(
    tmp_path, monkeypatch, released_before_crash,
):
    from datetime import timedelta
    from types import SimpleNamespace

    from agents_extensions.shared.session_streams.db import SessionStreamDatabase
    from agents_extensions.shared.session_streams.model import utc_now
    from agents_extensions.shared.session_streams.store import SessionStreamStore
    from scripts.ai_agent_bridge._inbox_watch import consume_supervisory_event, wake_driver_once
    from scripts.fleet_comms.authority import AuthorityService
    from scripts.session_supervisor import SessionSupervisor
    from tests.epics_monitor_stub import epics_monitor_stub

    now = utc_now()
    monkeypatch.setattr("scripts.api.epics_router.utc_now", lambda: now)
    monkeypatch.setattr("agents_extensions.shared.session_streams.store.utc_now", lambda: now)
    database = tmp_path / "restart.sqlite3"
    fleet_root = tmp_path / "fleet"
    store = SessionStreamStore(SessionStreamDatabase(database))
    with AuthorityService(root=fleet_root) as service, epics_monitor_stub(store) as base:
        supervisor = SessionSupervisor(None, repo_root=tmp_path, remote=RemoteEpicClient(base=base))
        predecessor = _open_supervisory_driver(supervisor)
        did = _supervisory_event(service)
        request = consume_supervisory_event(service, supervisor, predecessor, now=now.isoformat())
        assert request is not None and request.delivery_id == did
        if released_before_crash:
            assert supervisor.close_driver(role="driver", lease=predecessor) == "closed"

    # Drop both clients and reopen both databases. No desktop, external driver,
    # or provider is involved; only the established lifecycle primitives run.
    store = SessionStreamStore(SessionStreamDatabase(database))
    with AuthorityService(root=fleet_root) as service, epics_monitor_stub(store) as base:
        supervisor = SessionSupervisor(None, repo_root=tmp_path, remote=RemoteEpicClient(base=base))
        starts = []

        def start(_argv, *, env, check):
            assert env["SESSION_SUPERVISOR_WAKE_DELIVERY"] == did
            assert check is False
            starts.append(_open_supervisory_driver(
                supervisor, instance="successor", session_id=request.successor_session_id,
            ))
            return SimpleNamespace(returncode=0)

        wake_args = dict(stream_id=predecessor.stream_id, launcher=Path("start-codex-driver.sh"),
                         epic="fixture", run=start)
        if not released_before_crash:
            before = store.dump_stream(predecessor.stream_id)
            assert not wake_driver_once(service, supervisor.remote, **wake_args)
            assert starts == []
            assert store.dump_stream(predecessor.stream_id) == before
            # Advance the API clock past TTL; never simulate expiry by force release.
            now += timedelta(seconds=901)

        assert wake_driver_once(service, supervisor.remote, **wake_args)
        successor, = starts
        assert successor.generation == predecessor.generation + 1
        capsule = supervisor.build_capsule(role="driver", stream_id=successor.stream_id, lease=successor)
        assert sum(entry.body == request.prepared_body for entry in capsule.digest.recent) == 1
        assert consume_supervisory_event(
            service, supervisor, successor, now=(now + timedelta(seconds=61)).isoformat(),
        ) is None
        assert service.supervisory_delivery_status(did) == "acted_on"
        assert supervisor.close_driver(role="driver", lease=successor) == "closed"
        assert not wake_driver_once(service, supervisor.remote, **wake_args)
        assert len(starts) == 1
        sessions = store.dump_stream(predecessor.stream_id)["sessions"]
        assert len(sessions) == 2
        assert [session["state"] for session in sessions] == ["closed", "closed"]
        assert store.session_state(predecessor.stream_id, predecessor.session_id).value == (
            "closed" if released_before_crash else "expired"
        )


@pytest.mark.parametrize("damage", ["missing", "mismatched"])
def test_supervisory_wake_refuses_event_file_database_drift(supervisory_cycle, damage):
    from unittest.mock import Mock

    from scripts.ai_agent_bridge._inbox_watch import supervisory_launch_plan, wake_driver_once
    from scripts.fleet_comms.artifacts import ArtifactStoreError

    service, supervisor = supervisory_cycle
    lease = _open_supervisory_driver(supervisor)
    assert supervisor.close_driver(role="driver", lease=lease) == "closed"
    did = _supervisory_event(service, action="wake", generation=lease.generation)
    assert supervisory_launch_plan(service, supervisor.remote, did, lease.stream_id) is not None
    delivery = service.get_delivery(did)
    message = service.get_message(delivery.message_id)
    artifact = service.store.get(message.body_artifact_id)
    before = supervisor.remote.stream("epic:7178")
    if damage == "missing":
        artifact.blob_path.rename(artifact.blob_path.with_suffix(".unavailable"))
    else:
        # Keep valid JSON and byte length: the database's SHA must detect this.
        payload = artifact.blob_path.read_bytes()
        changed = payload.replace(b'"generation": 1', b'"generation": 2')
        assert changed != payload and len(changed) == len(payload)
        artifact.blob_path.write_bytes(changed)
    start = Mock(side_effect=AssertionError("corrupt event must not reach the launcher"))
    with pytest.raises(ArtifactStoreError, match=r"missing blob|blob digest mismatch"):
        wake_driver_once(service, supervisor.remote, stream_id="epic:7178",
                         launcher=Path("start-codex-driver.sh"), epic="fixture", run=start)
    start.assert_not_called()
    assert service.get_delivery(did) == delivery
    assert supervisor.remote.stream("epic:7178") == before


def test_successor_preserves_real_worker_needs_finalize(supervisory_cycle, tmp_path, monkeypatch):
    import signal
    import subprocess
    import sys
    from datetime import UTC, datetime, timedelta
    from types import SimpleNamespace

    from scripts import delegate
    from scripts.ai_agent_bridge._inbox_watch import consume_supervisory_event
    from scripts.fleet_comms.authority import AuthorityService

    repo = tmp_path / "worker"
    repo.mkdir()
    for args in (["init", "-b", "main"], ["-c", "user.name=Fixture", "-c",
                 "user.email=fixture@example.invalid", "commit", "--allow-empty", "-m", "fixture"],
                 ["update-ref", "refs/remotes/origin/main", "HEAD"]):
        subprocess.run(["git", *args], cwd=repo, env=delegate._sanitized_git_env(),
                       check=True, capture_output=True, timeout=10)
    monkeypatch.setattr(delegate, "_REPO_ROOT", repo)
    monkeypatch.setattr(delegate, "_TASKS_DIR", tmp_path / "tasks")
    monkeypatch.setattr(delegate, "_emit_terminal_dispatch_event", lambda **kwargs: None)
    # Host diagnostics are outside this fixture; settlement and Git checks stay real.
    for module in ("primary", "node_modules", "venv", "worktree_cleanup"):
        monkeypatch.setattr(
            f"scripts.audit.check_{module}_integrity.check_{module}_integrity",
            lambda *args, **kwargs: (True, "fixture-only"),
        )
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))

    def synthetic_provider(_agent, _prompt, **kwargs):
        # Execute a child that really leaves work uncommitted. The lifecycle
        # result comes from its exit code; no worker completion result is mocked.
        child = subprocess.run(
            [sys.executable, "-c", "from pathlib import Path; Path('work.txt').write_text('retain me')"],
            cwd=kwargs["cwd"], check=False, capture_output=True, text=True, timeout=10,
        )
        return SimpleNamespace(ok=child.returncode == 0, returncode=child.returncode,
                               response=child.stdout, stderr_excerpt=child.stderr, rate_limited=False)

    monkeypatch.setattr("agent_runtime.runner.invoke", synthetic_provider)
    state_path = delegate._state_path("held-out-worker")
    delegate._write_state_atomic(state_path, {
        "task_id": "held-out-worker", "worktree_path": str(repo), "worktree_base": "main",
        "cli_version": "synthetic",
    })
    service, supervisor = supervisory_cycle
    job = service.enqueue_request(recipient="worker", body="synthetic work", idempotency_key="held-out-worker")
    job_lease = service.claim_job(job.job_id, "fixture-worker")
    predecessor = _open_supervisory_driver(supervisor)
    did = _supervisory_event(service)
    now = datetime.now(UTC)
    request = consume_supervisory_event(service, supervisor, predecessor, now=now.isoformat())
    assert request is not None
    previous_handler = signal.getsignal(signal.SIGTERM)
    try:
        assert delegate._run_worker(
            task_id="held-out-worker", agent="codex", prompt="synthetic work",
            mode="workspace-write", cwd_str=str(repo), model="gpt-6-astra", hard_timeout=10,
        ) == 1
    finally:
        signal.signal(signal.SIGTERM, previous_handler)
    settled = json.loads(state_path.read_text())
    assert settled["status"] == "needs_finalize"
    assert settled["worktree_dirty_on_exit"] is True
    assert settled["commits_ahead"] == 0
    assert settled["returncode"] == 0
    before = state_path.read_bytes()
    # Publish measured settlement, not a fabricated worker "done" response.
    # Transport completion must retain the distinct needs_finalize outcome.
    service.finish_job(job.job_id, worker_id="fixture-worker", fence_token=job_lease.fence_token,
                       state="complete", result=before)

    assert supervisor.close_driver(role="driver", lease=predecessor) == "closed"
    successor = _open_supervisory_driver(
        supervisor, instance="successor", session_id=request.successor_session_id,
    )
    # Reopen the message database as a successor would, then consume the delayed
    # delivery. Its restart acknowledgment must not finalize the worker's work.
    with AuthorityService(root=service.store.root) as reopened:
        assert consume_supervisory_event(
            reopened, supervisor, successor, now=(now + timedelta(seconds=61)).isoformat(),
        ) is None
        assert reopened.supervisory_delivery_status(did) == "acted_on"
        assert reopened.read_job_result(job.job_id) == before
        assert json.loads(reopened.read_job_result(job.job_id))["needs_finalize"] is True
    assert state_path.read_bytes() == before
    assert (repo / "work.txt").read_text() == "retain me"
    assert delegate._worktree_is_dirty(repo) is True
    assert supervisor.close_driver(role="driver", lease=successor) == "closed"


def test_delayed_event_after_successor_exit_cannot_restart_again(supervisory_cycle):
    from datetime import UTC, datetime, timedelta
    from types import SimpleNamespace
    from unittest.mock import Mock

    from scripts.ai_agent_bridge._inbox_watch import consume_supervisory_event, wake_driver_once
    from scripts.fleet_comms.authority import AuthorityService

    service, supervisor = supervisory_cycle
    predecessor = _open_supervisory_driver(supervisor)
    did = _supervisory_event(service)
    now = datetime.now(UTC)
    request = consume_supervisory_event(service, supervisor, predecessor, now=now.isoformat())
    assert request is not None
    assert supervisor.close_driver(role="driver", lease=predecessor) == "closed"
    starts = []

    def start(_argv, **_kwargs):
        successor = _open_supervisory_driver(
            supervisor, instance="short-lived-successor", session_id=request.successor_session_id,
        )
        starts.append(successor)
        assert supervisor.close_driver(role="driver", lease=successor) == "closed"
        return SimpleNamespace(returncode=0)

    args = dict(stream_id=predecessor.stream_id, launcher=Path("start-codex-driver.sh"), epic="fixture")
    assert wake_driver_once(service, supervisor.remote, **args, run=start)
    # The successor exited before claiming the delivery. No live-holder check
    # or terminal acknowledgment can prevent a duplicate now: the generation must.
    with AuthorityService(root=service.store.root) as reopened:
        assert reopened.supervisory_delivery_status(did) == "live_driver_consumed"
        forbidden_start = Mock(side_effect=AssertionError("delayed delivery repeated a restart"))
        assert not wake_driver_once(reopened, supervisor.remote, **args, run=forbidden_start)
        forbidden_start.assert_not_called()
        later = _open_supervisory_driver(supervisor, instance="independent-later-driver")
        assert later.generation == starts[0].generation + 1
        assert consume_supervisory_event(
            reopened, supervisor, later, now=(now + timedelta(seconds=61)).isoformat(),
        ) is None
        assert reopened.supervisory_delivery_status(did) == "refused"
        assert supervisor.close_driver(role="driver", lease=later) == "closed"
    assert len(starts) == 1
