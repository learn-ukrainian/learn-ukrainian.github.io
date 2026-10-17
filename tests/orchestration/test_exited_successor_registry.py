"""Synthetic trust-boundary reproducers for the exact exited-successor action."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.orchestration import rollover_registry_cli as cli
from scripts.orchestration import thread_handoff as th
from scripts.orchestration.task_family import rollover_registry as registry
from tests.orchestration.task_family.test_rollover_registry import (
    _cleanup_proof,
    _disposition_proof,
    _lease,
    _persist_proof_evidence,
    _sync,
    _write_json,
)
from tests.orchestration.test_codex_driver_rollover_recovery import _launcher_detection

ACTION = registry.MaintenanceAction.DISPOSE_EXITED_SUCCESSOR
RUN_ID = "a" * 32
RUNTIME = Path(".agent/claudex-supervisors") / RUN_ID / "runtime.json"


@pytest.fixture
def case(tmp_path):
    lease = _lease(agent="codex-infra", replacement="successor-exact", status="started")
    record = _sync(tmp_path, lease)
    runtime = {
        "schema_version": 1,
        "run_id": RUN_ID,
        "state": "exited",
        "created_at": "2026-07-16T08:00:00Z",
        "updated_at": "2026-07-16T10:00:00Z",
        "supervisor_pid": 123,
        "child_pid": 124,
        "launch_generation": 1,
        "command_hash": "b" * 64,
        "profile_id": "synthetic-profile",
        "lead_model_id": "synthetic-lead",
        "subagent_model_id": "synthetic-worker",
        "agent": "codex",
        "epic": "infra",
        "handoff_agent": "codex-infra",
        "session_id": "successor-exact",
        "exit_code": 0,
    }
    _write_json(tmp_path / RUNTIME, runtime)
    proof = {
        **record["key"],
        "captured_at": "2026-07-16T10:01:00Z",
        "reason": "exact launcher exit",
        "assertions": {
            "no_unrecorded_native_create": True,
            "no_active_heartbeat_dependency": True,
            "selected_exact_ids_match": True,
        },
        "evidence_paths": [RUNTIME.as_posix()],
        "successor_exit": {
            "run_id": RUN_ID,
            "replacement_thread_id": "successor-exact",
            "runtime_digest": registry.sha256_digest(runtime),
        },
    }
    return SimpleNamespace(root=tmp_path, record=record, proof=proof, runtime=runtime)


def _plan(case):
    return registry.create_maintenance_plan(case.root, record=case.record, action=ACTION, proof=case.proof)


def _apply(case, plan):
    return registry.apply_maintenance_plan(case.root, plan_path=Path(plan["plan_path"]))


def _record(case):
    return registry.load_record(case.root, **case.record["key"])


def _change_runtime(case, **updates):
    case.runtime.update(updates)
    _write_json(case.root / RUNTIME, case.runtime)
    case.proof["successor_exit"]["runtime_digest"] = registry.sha256_digest(case.runtime)


def test_confirmed_successor_disposition_preserves_lease_and_retries(case):
    lease_path = case.root / case.record["lease_path"]
    before = lease_path.read_bytes()
    plan = _plan(case)
    assert _record(case)["state"] == "CONFIRMED"
    receipt = _apply(case, plan)
    record_bytes = registry.record_path(case.root, **case.record["key"]).read_bytes()
    receipt_bytes = (case.root / plan["plan_path"]).with_name("receipt.json").read_bytes()
    assert receipt["final_state"] == "ABANDONED_WITH_PROOF"
    assert _record(case)["last_successful_boundary"] == "CONFIRMED"
    assert receipt["final_record_digest"] == registry.sha256_digest(_record(case))
    assert _apply(case, plan) == receipt
    assert registry.record_path(case.root, **case.record["key"]).read_bytes() == record_bytes
    assert (case.root / plan["plan_path"]).with_name("receipt.json").read_bytes() == receipt_bytes
    assert lease_path.read_bytes() == before


@pytest.mark.parametrize("status", ["resumed", "started"])
def test_real_detector_and_shell_cold_start_after_exact_disposition(case, status, capsys):
    lease = _lease(
        agent="codex-infra",
        lineage="lineage-detect",
        rollover_id="rollover-detect",
        replacement="successor-exact",
        status=status,
    )
    lease["replacement"].update(th.replacement_packet_paths("codex-infra", "lineage-detect", 1, "rollover-detect"))
    lease["replacement"]["source_checkout"] = {"full_head": "a" * 40, "clean": True}
    lease["replacement"]["canary_challenge"] = "c" * 64
    lease["replacement"]["display"]["title_source"] = lease["replacement"]["identity"]["migration"]["source"]
    case.proof.update({"lineage_id": "lineage-detect", "rollover_id": "rollover-detect"})
    case.record = _sync(case.root, lease)
    packet = SimpleNamespace(root=case.root, agent="codex-infra", handoff=case.root / "no-handoff")
    before = (case.root / case.record["lease_path"]).read_bytes()
    # A confirmed registry can coexist with the earlier resumed lease projection.
    if status == "started":
        lease["replacement"]["status"] = "resumed"
        lease["replacement"]["resumed_thread_id"] = "successor-exact"
        _write_json(case.root / case.record["lease_path"], lease)
        before = (case.root / case.record["lease_path"]).read_bytes()
    assert th.main(["--repo-root", str(case.root), "detect", "--agent", "codex-infra"]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == ("resumed" if status == "resumed" else "none")
    plan = _plan(case)
    _apply(case, plan)
    assert th.main(["--repo-root", str(case.root), "detect", "--agent", "codex-infra"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "none"
    assert result["excluded_terminal"][0]["state"] == "ABANDONED_WITH_PROOF"
    launched = _launcher_detection(packet)
    assert launched.returncode == 0, launched.stderr
    assert "BOUND=\n" in launched.stdout
    assert (case.root / case.record["lease_path"]).read_bytes() == before


@pytest.mark.parametrize(
    "state,exit_code",
    [("running", 0), ("launching", None), ("restarting", 0), ("launch_failed", 1), ("exited", None), ("exited", True)],
)
def test_active_or_unknown_exit_is_refused(case, state, exit_code):
    _change_runtime(case, state=state, exit_code=exit_code)
    with pytest.raises(ValueError):
        _plan(case)
    assert _record(case)["state"] == "CONFIRMED"


@pytest.mark.parametrize(
    "field,value", [("lineage_id", "lineage-other"), ("rollover_id", "rollover-other"), ("agent", "codex-devops")]
)
def test_evidence_for_other_exact_key_is_refused(case, field, value):
    case.proof[field] = value
    with pytest.raises(ValueError, match="exact IDs"):
        _plan(case)


@pytest.mark.parametrize("field", ["session_id", "handoff_agent"])
def test_launcher_evidence_for_other_successor_is_refused(case, field):
    _change_runtime(case, **{field: "other"})
    with pytest.raises(ValueError, match="exact bound successor"):
        _plan(case)


def test_caller_successor_mismatch_is_refused(case):
    case.proof["successor_exit"]["replacement_thread_id"] = "other"
    with pytest.raises(ValueError, match="exact bound successor"):
        _plan(case)


@pytest.mark.parametrize("guard", ["no_unrecorded_native_create", "no_active_heartbeat_dependency"])
def test_existing_disposition_guards_still_bind(case, guard):
    case.proof["assertions"][guard] = False
    with pytest.raises(ValueError, match=guard):
        _plan(case)


@pytest.mark.parametrize("mutation", ["active", "digest", "missing"])
def test_apply_revalidates_durable_exit_evidence(case, mutation):
    plan = _plan(case)
    if mutation == "missing":
        (case.root / RUNTIME).unlink()
    elif mutation == "active":
        _change_runtime(case, state="running")
    else:
        _change_runtime(case, exit_code=1)
    with pytest.raises((OSError, ValueError)):
        _apply(case, plan)
    assert _record(case)["state"] == "CONFIRMED"


@pytest.mark.parametrize("after_receipt", [False, True])
def test_replay_against_changed_record_is_refused(case, after_receipt):
    plan = _plan(case)
    if after_receipt:
        _apply(case, plan)
    current = _record(case)
    current["heartbeat"]["automation_id"] = "changed"
    _write_json(registry.record_path(case.root, **case.record["key"]), current)
    with pytest.raises(ValueError, match="record changed"):
        _apply(case, plan)
    assert _record(case) == current


@pytest.mark.parametrize("crash_target", ["record.json", "receipt.json"])
def test_retry_recovers_crash_without_duplicate_transition(case, monkeypatch, crash_target):
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
    receipt = _apply(case, plan)
    assert receipt["final_state"] == "ABANDONED_WITH_PROOF"
    assert sum(event.get("operation_id") == plan["digest"] for event in _record(case)["history"]) == 1


@pytest.mark.parametrize("action", [registry.MaintenanceAction.SUPERSEDE, registry.MaintenanceAction.ABANDON])
def test_no_legacy_action_or_direct_transition_disposes_confirmed_successor(case, action):
    with pytest.raises(ValueError, match="confirmed active"):
        registry.create_maintenance_plan(
            case.root, record=case.record, action=action, proof=_disposition_proof(case.record)
        )
    target = (
        registry.RolloverState.SUPERSEDED
        if action.value == "supersede"
        else registry.RolloverState.ABANDONED_WITH_PROOF
    )
    with pytest.raises(ValueError, match="confirmed active"):
        registry.transition(case.root, **case.record["key"], state=target, reason="unproved exit")
    assert _record(case)["state"] == "CONFIRMED"


def test_plan_does_not_authorize_direct_transition_without_intent(case):
    plan = _plan(case)
    with pytest.raises(ValueError, match="cannot read durable JSON"):
        registry.transition(
            case.root,
            **case.record["key"],
            state=registry.RolloverState.ABANDONED_WITH_PROOF,
            reason="exit",
            operation_id=plan["digest"],
            maintenance_plan=Path(plan["plan_path"]),
        )
    assert _record(case)["state"] == "CONFIRMED"


@pytest.mark.parametrize("path_kind", ["lease", "copy", "outside", "symlink"])
def test_arbitrary_evidence_paths_cannot_touch_lease(case, path_kind):
    lease_path = case.root / case.record["lease_path"]
    before = lease_path.read_bytes()
    if path_kind == "symlink":
        (case.root / RUNTIME).unlink()
        (case.root / RUNTIME).symlink_to(lease_path)
    else:
        case.proof["evidence_paths"] = [
            {"lease": case.record["lease_path"], "copy": "copy.json", "outside": "../runtime.json"}[path_kind]
        ]
    with pytest.raises(ValueError):
        _plan(case)
    assert lease_path.read_bytes() == before


def test_exact_cli_plan_and_apply_and_wrong_action(case, capsys):
    proof_path = case.root / "exit-proof.json"
    _write_json(proof_path, case.proof)
    common = [
        "--repo-root",
        str(case.root),
        "dispose-exited-successor-exact",
        "--agent",
        "codex-infra",
        "--lineage-id",
        case.record["key"]["lineage_id"],
        "--rollover-id",
        case.record["key"]["rollover_id"],
    ]
    assert cli.main([*common, "--plan", "--proof-file", str(proof_path)]) == 0
    plan = json.loads(capsys.readouterr().out)
    wrong = common.copy()
    wrong[2] = "abandon-exact"
    assert cli.main([*wrong, "--apply", "--plan-file", plan["plan_path"]]) == 2
    assert "action does not match" in capsys.readouterr().out
    assert cli.main([*common, "--apply", "--plan-file", plan["plan_path"]]) == 0
    assert json.loads(capsys.readouterr().out)["final_state"] == "ABANDONED_WITH_PROOF"
    assert cli.main([*common, "--apply", "--plan-file", plan["plan_path"]]) == 0
    assert json.loads(capsys.readouterr().out)["final_state"] == "ABANDONED_WITH_PROOF"


def test_cli_documents_exact_exit_contract(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["dispose-exited-successor-exact", "--help"])
    assert exc.value.code == 0
    help_text = capsys.readouterr().out
    assert "canonical launcher runtime" in help_text
    assert "--proof-file" in help_text


@pytest.mark.parametrize(
    "action",
    [
        registry.MaintenanceAction.ABANDON,
        registry.MaintenanceAction.SUPERSEDE,
        registry.MaintenanceAction.FINISH_CLEANUP,
    ],
)
def test_existing_maintenance_actions_keep_their_behavior(case, action):
    if action is registry.MaintenanceAction.FINISH_CLEANUP:
        proof = _cleanup_proof(case.record)
        expected = "HEARTBEAT_RETIRED"
    else:
        case.record = _sync(case.root, _lease(lineage="lineage-legacy", rollover_id="rollover-legacy"))
        proof = _disposition_proof(case.record)
        expected = "SUPERSEDED" if action.value == "supersede" else "ABANDONED_WITH_PROOF"
    plan = registry.create_maintenance_plan(
        case.root, record=case.record, action=action, proof=_persist_proof_evidence(case.root, proof)
    )
    assert _apply(case, plan)["final_state"] == expected
    assert _apply(case, plan)["final_state"] == expected


def test_extra_proof_fields_are_refused(case):
    case.proof["force"] = True
    with pytest.raises(ValueError, match="unexpected fields"):
        _plan(case)


def test_plan_tamper_is_refused(case):
    plan = _plan(case)
    path = case.root / plan["plan_path"]
    tampered = json.loads(path.read_text())
    tampered["target_states"] = ["SUPERSEDED"]
    _write_json(path, tampered)
    with pytest.raises(ValueError, match="digest mismatch"):
        _apply(case, plan)


def test_exit_older_than_confirmation_is_refused(case):
    _change_runtime(case, updated_at="2026-07-16T08:30:00Z")
    with pytest.raises(ValueError, match="timestamp"):
        _plan(case)


def test_forged_digest_is_refused(case):
    case.proof["successor_exit"]["runtime_digest"] = "0" * 64
    with pytest.raises(ValueError, match="digest changed"):
        _plan(case)


@pytest.mark.parametrize("changed", [False, True])
def test_direct_transition_retry_revalidates_exact_applied_record(case, changed):
    plan = _plan(case)
    _apply(case, plan)
    if changed:
        current = _record(case)
        current["heartbeat"]["automation_id"] = "changed-after-exit"
        _write_json(registry.record_path(case.root, **case.record["key"]), current)
    arguments = {
        **case.record["key"],
        "state": registry.RolloverState.ABANDONED_WITH_PROOF,
        "reason": plan["proof"]["reason"],
        "evidence_paths": plan["proof"]["evidence_paths"],
        "operation_id": plan["digest"],
        "maintenance_plan": Path(plan["plan_path"]),
    }
    if changed:
        with pytest.raises(ValueError, match="exact maintenance plan"):
            registry.transition(case.root, **arguments)
    else:
        assert registry.transition(case.root, **arguments) == _record(case)


def test_direct_transition_cannot_change_plan_bound_evidence(case):
    plan = _plan(case)
    intent_path = (case.root / plan["plan_path"]).with_name("apply-intent.json")
    _write_json(intent_path, registry._maintenance_intent(plan))
    with pytest.raises(ValueError, match="exact maintenance plan"):
        registry.transition(
            case.root,
            **case.record["key"],
            state=registry.RolloverState.ABANDONED_WITH_PROOF,
            reason=plan["proof"]["reason"],
            evidence_paths=[case.record["lease_path"]],
            operation_id=plan["digest"],
            maintenance_plan=Path(plan["plan_path"]),
        )
    assert _record(case)["state"] == "CONFIRMED"
