"""Fixture-only legacy successor disposition for Refs #10921."""

from __future__ import annotations

import json
import subprocess
import sys
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


@pytest.fixture
def case(tmp_path, monkeypatch):
    monkeypatch.setattr(psutil, "process_iter", lambda: iter(()))
    lease = _lease(
        agent="codex-infra", lineage="lineage-6aa06d47a68be265bcd2dc34",
        rollover_id="rollover-13c2b164a91f485197c369c5c6a0432e", replacement=THREAD, status="resumed",
    )
    lease["replacement"].pop("native_lifecycle")
    lease["replacement"].update(th.replacement_packet_paths(
        "codex-infra", lease["lineage_id"], 1, lease["rollover_id"],
    ))
    lease["replacement"]["source_checkout"] = {"full_head": "a" * 40, "clean": True}
    lease["replacement"]["canary_challenge"] = "c" * 64
    lease["replacement"]["display"]["title_source"] = lease["replacement"]["identity"]["migration"]["source"]
    record = _sync(tmp_path, lease)
    proof = {
        **record["key"], "captured_at": "2026-10-17T11:00:00Z", "reason": "operator legacy disposition (#10921)",
        "assertions": {"selected_exact_ids_match": True}, "evidence_paths": [record["lease_path"]],
        "operator_disposition": {
            "authority": "operator", "actor_agent": "codex", "actor_host_id": "fixture-host",
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
    before = registry.record_path(case.root, **case.record["key"]).read_bytes()
    with subprocess.Popen(
        ["codex", "-c", "import sys; sys.stdin.read()", THREAD], executable=sys.executable, stdin=subprocess.PIPE,
    ) as child:
        monkeypatch.setattr(psutil, "process_iter", lambda: iter([psutil.Process(child.pid)]))
        try:
            with pytest.raises(ValueError, match="live codex process found"):
                _plan(case) if phase == "plan" else _apply(case, plan)
        finally:
            child.communicate(timeout=10)
    assert registry.record_path(case.root, **case.record["key"]).read_bytes() == before


@pytest.mark.parametrize("phase", ["plan", "apply", "retry"])
def test_positive_successor_heartbeat_refuses_legacy_disposition(case, phase):
    plan = _plan(case) if phase != "plan" else None
    if phase == "retry":
        _apply(case, plan)
    before = registry.record_path(case.root, **case.record["key"]).read_bytes()
    _write_json(case.root / th.default_thread_lease_path("codex-infra"), {
        "owner_thread_id": THREAD, "heartbeat_at": "2026-10-17T11:01:00Z",
    })
    with pytest.raises(ValueError, match="positive heartbeat found"):
        _plan(case) if phase == "plan" else _apply(case, plan)
    assert registry.record_path(case.root, **case.record["key"]).read_bytes() == before


def test_foreign_thread_heartbeat_does_not_veto_exact_disposition(case):
    _write_json(case.root / th.default_thread_lease_path("codex-infra"), {
        "owner_thread_id": "other-thread", "heartbeat_at": "2026-10-17T11:01:00Z",
    })
    assert _apply(case, _plan(case))["final_state"] == "ABANDONED_WITH_PROOF"


@pytest.mark.parametrize("field,value", [
    ("authority", "agent"), ("actor_agent", ""), ("actor_host_id", ""), ("replacement_thread_id", "other"),
])
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
    command = ["--repo-root", str(case.root), "dispose-legacy-resumed-exact", "--agent", "codex-infra",
               "--lineage-id", case.record["key"]["lineage_id"], "--rollover-id", case.record["key"]["rollover_id"]]
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


@pytest.mark.parametrize("field,value", [("agent", "codex-devops"), ("lineage_id", "lineage-other"),
                                         ("rollover_id", "rollover-other")])
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


def test_unavailable_process_probe_refuses_legacy_disposition(case, monkeypatch):
    class UnreadableProcess:
        def oneshot(self):
            raise psutil.AccessDenied(123)

    monkeypatch.setattr(psutil, "process_iter", lambda: iter([UnreadableProcess()]))
    with pytest.raises(ValueError, match="process probe unavailable"):
        _plan(case)


@pytest.mark.parametrize("kind", ["malformed", "symlink"])
def test_unreadable_heartbeat_refuses_legacy_disposition(case, kind):
    path = case.root / th.default_thread_lease_path("codex-infra")
    if kind == "malformed":
        path.write_text("not json")
    else:
        path.symlink_to(case.root / case.record["lease_path"])
    with pytest.raises(ValueError):
        _plan(case)
