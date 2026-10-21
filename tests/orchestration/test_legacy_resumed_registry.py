"""Fixture-only legacy successor disposition for Refs #10921."""

from __future__ import annotations

import json
import os
import selectors
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import psutil
import pytest

from scripts.orchestration import rollover_registry_cli as cli
from scripts.orchestration import thread_handoff as th
from scripts.orchestration.task_family import rollover_registry as registry
from tests.orchestration.task_family.test_rollover_registry import _lease, _sync, _write_json

ACTION = registry.MaintenanceAction.DISPOSE_LEGACY_RESUMED
THREAD = "01a130e0-b3f1-7021-891b-96d9abc65cf8"
_SUCCESSOR_READY_TIMEOUT = 10
_SUCCESSOR_CLEANUP_TIMEOUT = 2


@pytest.fixture
def case(tmp_path, monkeypatch):
    monkeypatch.setattr(psutil, "process_iter", lambda: iter(()))
    lease = _lease(
        agent="codex-infra",
        lineage="lineage-6aa06d47a68be265bcd2dc34",
        rollover_id="rollover-13c2b164a91f485197c369c5c6a0432e",
        replacement=THREAD,
        status="resumed",
    )
    lease["replacement"].pop("native_lifecycle")
    lease["replacement"].update(
        th.replacement_packet_paths(
            "codex-infra",
            lease["lineage_id"],
            1,
            lease["rollover_id"],
        )
    )
    lease["replacement"]["source_checkout"] = {"full_head": "a" * 40, "clean": True}
    lease["replacement"]["canary_challenge"] = "c" * 64
    lease["replacement"]["display"]["title_source"] = lease["replacement"]["identity"]["migration"]["source"]
    record = _sync(tmp_path, lease)
    proof = {
        **record["key"],
        "captured_at": "2026-10-17T11:00:00Z",
        "reason": "operator legacy disposition (#10921)",
        "assertions": {"selected_exact_ids_match": True},
        "evidence_paths": [record["lease_path"]],
        "operator_disposition": {
            "authority": "operator",
            "actor_agent": "codex",
            "actor_host_id": "fixture-host",
            "replacement_thread_id": THREAD,
        },
    }
    return SimpleNamespace(root=tmp_path, record=record, proof=proof)


def _plan(case):
    return registry.create_maintenance_plan(case.root, record=case.record, action=ACTION, proof=case.proof)


def _apply(case, plan):
    return registry.apply_maintenance_plan(case.root, plan_path=Path(plan["plan_path"]))


def _record(case):
    return registry.load_record(case.root, **case.record["key"])


def _registry_bytes(case):
    return {
        path.relative_to(case.root): path.read_bytes()
        for path in registry.registry_root(case.root).rglob("*")
        if path.is_file()
    }


@contextmanager
def _successor_process(*, name="codex", thread=THREAD):
    deadline = time.monotonic() + _SUCCESSOR_READY_TIMEOUT
    child = subprocess.Popen(
        [name, "-c", "import sys; print('ready', flush=True); sys.stdin.read()", thread],
        executable=sys.executable,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    primary_error = None
    try:
        # Popen can return while exec still exposes an empty /proc cmdline.
        with selectors.DefaultSelector() as selector:
            selector.register(child.stdout, selectors.EVENT_READ)
            assert selector.select(max(0, deadline - time.monotonic())), "successor readiness deadline"
            assert child.stdout.readline() == b"ready\n"
        yield child
    except BaseException as error:
        primary_error = error
        raise
    finally:
        cleanup_deadline = time.monotonic() + _SUCCESSOR_CLEANUP_TIMEOUT
        try:
            if primary_error is not None:
                child.kill()
            try:
                # Reserve half the cleanup budget for kill and reap on failure.
                child.communicate(timeout=max(0, cleanup_deadline - time.monotonic()) / 2)
            except BaseException:
                child.kill()
                child.wait(timeout=max(0, cleanup_deadline - time.monotonic()))
                raise
        except BaseException as cleanup_error:
            if primary_error is None:
                raise
            primary_error.add_note(f"successor cleanup failed: {cleanup_error!r}")
        finally:
            child.stdin.close()
            child.stdout.close()


@pytest.mark.parametrize(
    "failure",
    [
        "readiness_timeout",
        "early_exit",
        "body_exception",
        "communication_failure",
        "unresponsive",
        "body_and_communication_failure",
        "success",
    ],
)
def test_successor_process_bounds_cleanup_and_preserves_failure(monkeypatch, failure):
    module = sys.modules[__name__]
    monkeypatch.setattr(module, "_SUCCESSOR_READY_TIMEOUT", 0.5)
    monkeypatch.setattr(module, "_SUCCESSOR_CLEANUP_TIMEOUT", 0.8)
    primary = RuntimeError("original yielded-body failure")
    communication_error = OSError("synthetic communication failure")
    popen = subprocess.Popen
    children = []
    cleanup_started = []
    code = "import sys; print('ready', flush=True); sys.stdin.read()"
    if failure == "early_exit":
        code = "raise SystemExit(7)"
    elif failure == "readiness_timeout":
        code = "import time; time.sleep(30)"
    elif failure == "unresponsive":
        code = "import time; print('ready', flush=True); time.sleep(30)"

    def spawn(args, **kwargs):
        args = list(args)
        args[2] = code
        child = popen(args, **kwargs)
        children.append((child, child.kill))
        communicate = child.communicate

        def communicate_or_fail(*args, **kwargs):
            cleanup_started.append(time.monotonic())
            if failure in {"communication_failure", "body_and_communication_failure"}:
                raise communication_error
            return communicate(*args, **kwargs)

        monkeypatch.setattr(child, "communicate", communicate_or_fail)
        return child

    monkeypatch.setattr(subprocess, "Popen", spawn)
    started = time.monotonic()
    observed = None
    try:
        try:
            with _successor_process() as child:
                assert child.poll() is None
                if failure in {"body_exception", "body_and_communication_failure"}:
                    raise primary
        except BaseException as error:
            observed = error
        finished = time.monotonic()
        assert len(children) == 1
        child = children[0][0]
        # Inspect before any rescue cleanup or poll() could reap the child.
        assert child.returncode is not None
        with pytest.raises(ChildProcessError):
            os.waitpid(child.pid, os.WNOHANG)
        assert child.stdin.closed
        assert child.stdout.closed
        assert cleanup_started
        assert finished - cleanup_started[0] < module._SUCCESSOR_CLEANUP_TIMEOUT
        assert finished - started < module._SUCCESSOR_READY_TIMEOUT + module._SUCCESSOR_CLEANUP_TIMEOUT
        if failure in {"body_exception", "body_and_communication_failure"}:
            assert observed is primary
            if failure == "body_and_communication_failure":
                assert primary.__notes__ == [f"successor cleanup failed: {communication_error!r}"]
        elif failure == "communication_failure":
            assert observed is communication_error
        elif failure == "readiness_timeout":
            assert isinstance(observed, AssertionError)
            assert "successor readiness deadline" in str(observed)
        elif failure == "early_exit":
            assert isinstance(observed, AssertionError)
            assert child.returncode == 7
        elif failure == "unresponsive":
            assert isinstance(observed, subprocess.TimeoutExpired)
        else:
            assert observed is None
            assert child.returncode == 0
    finally:
        for child, kill in children:
            if child.poll() is None:
                kill()
            child.wait(timeout=1)
            child.stdin.close()
            child.stdout.close()


@pytest.mark.parametrize("authority", ["operator", "cto"])
def test_legacy_disposition_stops_exact_lineage_resumed_detection(case, capsys, authority):
    case.proof["operator_disposition"]["authority"] = authority
    lease_path = case.root / case.record["lease_path"]
    before = lease_path.read_bytes()
    detect = ["--repo-root", str(case.root), "detect", "--agent", "codex-infra"]
    assert th.main(detect) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "resumed"
    plan = _plan(case)
    assert _record(case)["state"] == "RESUMED"
    receipt = _apply(case, plan)
    assert receipt["final_state"] == "ABANDONED_WITH_PROOF"
    assert _record(case)["last_successful_boundary"] == "RESUMED"
    assert _record(case)["heartbeat"]["state"] == "active_or_unknown"
    assert _apply(case, plan) == receipt
    assert plan["proof"]["operator_disposition"] == case.proof["operator_disposition"]
    assert th.main(detect) == 0
    detected = json.loads(capsys.readouterr().out)
    assert detected["status"] == "none"
    assert detected["excluded_terminal"] == [{**case.record["key"], "state": "ABANDONED_WITH_PROOF"}]
    assert lease_path.read_bytes() == before


@pytest.mark.parametrize("phase", ["plan", "apply", "retry"])
def test_live_successor_process_refuses_legacy_disposition(case, monkeypatch, phase):
    plan = _plan(case) if phase != "plan" else None
    if phase == "retry":
        _apply(case, plan)
    before = _registry_bytes(case)
    with _successor_process() as child:
        process = psutil.Process(child.pid)
        assert process.cmdline()[0] == "codex"
        assert process.cmdline()[-1] == THREAD
        assert process.status() != psutil.STATUS_ZOMBIE
        assert child.poll() is None
        monkeypatch.setattr(psutil, "process_iter", lambda: iter([process]))
        with pytest.raises(ValueError, match="live codex process found"):
            _plan(case) if phase == "plan" else _apply(case, plan)
    assert _registry_bytes(case) == before


@pytest.mark.parametrize("phase", ["plan", "apply", "retry"])
@pytest.mark.parametrize("name,thread", [("other-cli", THREAD), ("codex", "other-thread")])
def test_nonmatching_live_process_does_not_veto_legacy_disposition(case, monkeypatch, phase, name, thread):
    plan = _plan(case) if phase != "plan" else None
    if phase == "retry":
        _apply(case, plan)
    with _successor_process(name=name, thread=thread) as child:
        process = psutil.Process(child.pid)
        assert process.cmdline()[0] == name
        assert process.cmdline()[-1] == thread
        assert child.poll() is None
        monkeypatch.setattr(psutil, "process_iter", lambda: iter([process]))
        result = _plan(case) if phase == "plan" else _apply(case, plan)
    if phase == "plan":
        result = _apply(case, result)
    assert result["final_state"] == "ABANDONED_WITH_PROOF"


@pytest.mark.parametrize("phase", ["plan", "apply", "retry"])
def test_dead_matching_process_does_not_veto_legacy_disposition(case, monkeypatch, phase):
    plan = _plan(case) if phase != "plan" else None
    if phase == "retry":
        _apply(case, plan)
    with _successor_process() as child:
        process = psutil.Process(child.pid)
    assert child.returncode == 0
    with pytest.raises(psutil.NoSuchProcess):
        process.cmdline()
    monkeypatch.setattr(psutil, "process_iter", lambda: iter([process]))
    result = _plan(case) if phase == "plan" else _apply(case, plan)
    if phase == "plan":
        result = _apply(case, result)
    assert result["final_state"] == "ABANDONED_WITH_PROOF"


@pytest.mark.parametrize("phase", ["plan", "apply", "retry"])
def test_positive_successor_heartbeat_refuses_legacy_disposition(case, phase):
    plan = _plan(case) if phase != "plan" else None
    if phase == "retry":
        _apply(case, plan)
    before = _registry_bytes(case)
    _write_json(
        case.root / th.default_thread_lease_path("codex-infra"),
        {
            "owner_thread_id": THREAD,
            "heartbeat_at": "2026-10-17T11:01:00Z",
        },
    )
    with pytest.raises(ValueError, match="positive heartbeat found"):
        _plan(case) if phase == "plan" else _apply(case, plan)
    assert _registry_bytes(case) == before


def test_foreign_thread_heartbeat_does_not_veto_exact_disposition(case):
    _write_json(
        case.root / th.default_thread_lease_path("codex-infra"),
        {
            "owner_thread_id": "other-thread",
            "heartbeat_at": "2026-10-17T11:01:00Z",
        },
    )
    assert _apply(case, _plan(case))["final_state"] == "ABANDONED_WITH_PROOF"


@pytest.mark.parametrize(
    "field,value",
    [
        ("authority", "agent"),
        ("actor_agent", ""),
        ("actor_host_id", ""),
        ("replacement_thread_id", "other"),
    ],
)
def test_legacy_disposition_requires_exact_operator_attribution(case, field, value):
    case.proof["operator_disposition"][field] = value
    with pytest.raises(ValueError):
        _plan(case)
    assert _record(case)["state"] == "RESUMED"


@pytest.mark.parametrize("state", ["exited", "running", "unknown"])
def test_supervisor_runtime_excludes_legacy_disposition(case, state):
    _write_json(case.root / ".agent/claudex-supervisors/fixture/runtime.json", {"session_id": THREAD, "state": state})
    with pytest.raises(ValueError, match="has a supervisor runtime"):
        _plan(case)


@pytest.mark.parametrize("field,value", [("state", "CONFIRMED"), ("native_creation", {"state": "replacement_created"})])
def test_nonlegacy_or_nonresumed_record_is_refused(case, field, value):
    case.record[field] = value
    with pytest.raises(ValueError, match="legacy RESUMED"):
        _plan(case)


@pytest.mark.parametrize("crash_target", ["record.json", "receipt.json"])
def test_legacy_retry_recovers_interrupted_publication(case, monkeypatch, crash_target):
    plan = _plan(case)
    original = registry.atomic_write_json
    crashed = False

    def interrupted(path, payload):
        nonlocal crashed
        if path.name == crash_target and not crashed:
            crashed = True
            raise OSError("synthetic crash")
        original(path, payload)

    monkeypatch.setattr(registry, "atomic_write_json", interrupted)
    with pytest.raises(OSError, match="synthetic crash"):
        _apply(case, plan)
    assert _apply(case, plan)["final_state"] == "ABANDONED_WITH_PROOF"
    assert sum(event.get("operation_id") == plan["digest"] for event in _record(case)["history"]) == 1


def test_legacy_cli_plan_apply_and_help(case, capsys):
    proof_path = case.root / "operator-proof.json"
    _write_json(proof_path, case.proof)
    command = [
        "--repo-root",
        str(case.root),
        "dispose-legacy-resumed-exact",
        "--agent",
        "codex-infra",
        "--lineage-id",
        case.record["key"]["lineage_id"],
        "--rollover-id",
        case.record["key"]["rollover_id"],
    ]
    assert cli.main([*command, "--plan", "--proof-file", str(proof_path)]) == 0
    plan = json.loads(capsys.readouterr().out)
    assert cli.main([*command, "--apply", "--plan-file", plan["plan_path"]]) == 0
    assert json.loads(capsys.readouterr().out)["final_state"] == "ABANDONED_WITH_PROOF"
    with pytest.raises(SystemExit) as exc:
        cli.main(["dispose-legacy-resumed-exact", "--help"])
    assert exc.value.code == 0
    help_text = capsys.readouterr().out
    assert "operator_disposition" in help_text
    assert "positive thread heartbeat" in help_text


@pytest.mark.parametrize(
    "field,value", [("agent", "codex-devops"), ("lineage_id", "lineage-other"), ("rollover_id", "rollover-other")]
)
def test_legacy_proof_for_another_exact_key_is_refused(case, field, value):
    case.proof[field] = value
    with pytest.raises(ValueError, match="exact IDs"):
        _plan(case)
    assert not list(case.root.rglob("plan.json"))


def test_runtime_appearing_after_plan_refuses_apply(case):
    plan = _plan(case)
    _write_json(case.root / ".agent/claudex-supervisors/fixture/runtime.json", {"session_id": THREAD})
    with pytest.raises(ValueError, match="has a supervisor runtime"):
        _apply(case, plan)
    assert _record(case)["state"] == "RESUMED"


def test_legacy_apply_refuses_changed_record(case):
    plan = _plan(case)
    current = _record(case)
    current["heartbeat"]["automation_id"] = "changed"
    _write_json(registry.record_path(case.root, **case.record["key"]), current)
    with pytest.raises(ValueError, match="record changed"):
        _apply(case, plan)
    assert _record(case) == current


@pytest.mark.parametrize("phase", ["plan", "apply", "retry"])
@pytest.mark.parametrize("error", [psutil.AccessDenied(123), OSError("synthetic process probe failure")])
def test_unavailable_process_probe_refuses_legacy_disposition(case, monkeypatch, phase, error):
    plan = _plan(case) if phase != "plan" else None
    if phase == "retry":
        _apply(case, plan)
    before = _registry_bytes(case)

    class UnreadableProcess:
        def oneshot(self):
            raise error

    monkeypatch.setattr(psutil, "process_iter", lambda: iter([UnreadableProcess()]))
    with pytest.raises(ValueError, match="process probe unavailable"):
        _plan(case) if phase == "plan" else _apply(case, plan)
    assert _registry_bytes(case) == before


@pytest.mark.parametrize("phase", ["plan", "apply", "retry"])
@pytest.mark.parametrize("kind", ["malformed", "non-object", "symlink"])
def test_unreadable_heartbeat_refuses_legacy_disposition(case, kind, phase):
    plan = _plan(case) if phase != "plan" else None
    if phase == "retry":
        _apply(case, plan)
    before = _registry_bytes(case)
    path = case.root / th.default_thread_lease_path("codex-infra")
    if kind == "malformed":
        path.write_text("not json")
    elif kind == "non-object":
        path.write_text("[]")
    else:
        path.symlink_to(case.root / case.record["lease_path"])
    with pytest.raises(ValueError):
        _plan(case) if phase == "plan" else _apply(case, plan)
    assert _registry_bytes(case) == before
