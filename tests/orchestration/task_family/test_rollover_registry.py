from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from scripts.orchestration import rollover_registry_cli, task_identity
from scripts.orchestration.task_family import rollover
from scripts.orchestration.task_family import rollover_registry as registry


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _lease(
    *,
    agent: str = "codex",
    lineage: str = "lineage-a1",
    rollover_id: str = "rollover-r1",
    source: str = "source-1",
    replacement: str | None = None,
    status: str = "pending_start",
    prepared_at: str = "2026-07-16T09:00:00Z",
) -> dict:
    family_id, operation_id = rollover.transition_identity(
        lineage_id=lineage,
        generation=1,
        rollover_id=rollover_id,
    )
    native_status = "awaiting_native_create"
    if replacement:
        native_status = "replacement_created_bound"
    identity = task_identity.build_identity(
        repository=task_identity.DEFAULT_REPOSITORY,
        stream_epic=4707,
        stream_epic_url=None,
        github_issue_number=5296,
        github_issue_url=None,
        semantic_title=f"Registry test {lineage}",
        task_family="thread-rollover",
        role=agent,
        predecessor_task_id=source,
        replacement_task_id=None,
        lineage_id=lineage,
        generation=1,
        terminal_goal="merge",
    )
    title_transition = task_identity.new_title_transition(
        harness=task_identity.default_harness(agent),
        visible_title_value=identity["visible_title"],
        prepared_at=prepared_at,
    )
    if replacement:
        identity, title_transition = task_identity.bind_replacement(
            identity,
            title_transition,
            replacement_task_id=replacement,
            evidence="Exact replacement binding fixture.",
            now=prepared_at,
        )
        if title_transition["native_title_supported"]:
            identity, title_transition = task_identity.record_title_acknowledgement(
                identity,
                title_transition,
                replacement_task_id=replacement,
                succeeded=True,
                evidence="Exact native title acknowledgement fixture.",
                error="",
                now=prepared_at,
            )
            identity, title_transition = task_identity.record_title_readback(
                identity,
                title_transition,
                replacement_task_id=replacement,
                observed_title=identity["visible_title"],
                succeeded=True,
                evidence="Exact native title readback fixture.",
                error="",
                now=prepared_at,
            )
        if status == "resumed":
            identity = task_identity.mark_resumed(
                identity,
                title_transition,
                replacement_task_id=replacement,
            )
        elif status == "started":
            identity = task_identity.mark_confirmed(
                identity,
                title_transition,
                replacement_task_id=replacement,
            )
    result = {
        "schema_version": 2,
        "agent": agent,
        "lineage_id": lineage,
        "rollover_id": rollover_id,
        "active": {
            "thread_id": source,
            "automation_id": "automation-1",
            "generation": 0,
            "lineage_id": lineage,
            "started_at": prepared_at,
            "last_seen_at": prepared_at,
        },
        "replacement": {
            "rollover_id": rollover_id,
            "lineage_id": lineage,
            "generation": 1,
            "status": status,
            "prepared_at": prepared_at,
            "thread_id": replacement if status == "started" else None,
            "resumed_thread_id": replacement if status == "resumed" else None,
            "display": {
                "title": identity["visible_title"],
                "title_source": "task_identity_v1",
            },
            "identity": identity,
            "title_transition": title_transition,
            "tracking": {"stream_epic": 4707, "github_issue": 5296},
            "native_lifecycle": {
                "family_id": family_id,
                "operation_id": operation_id,
                "source_thread_id": source,
                "replacement_thread_id": replacement,
                "status": native_status,
            },
            "runtime_path": f".agent/thread-rollovers/{agent}/{lineage}/generation-0001/{rollover_id}",
            "handoff_path": f".agent/thread-rollovers/{agent}/{lineage}/generation-0001/{rollover_id}/handoff.md",
            "bootstrap_prompt_path": f".agent/thread-rollovers/{agent}/{lineage}/generation-0001/{rollover_id}/bootstrap.md",
            "semantic_snapshot_path": f".agent/thread-rollovers/{agent}/{lineage}/generation-0001/{rollover_id}/semantic-snapshot.json",
            "strict_probe_path": f".agent/thread-rollovers/{agent}/{lineage}/generation-0001/{rollover_id}/strict-probe.json",
            "strict_questions_path": f".agent/thread-rollovers/{agent}/{lineage}/generation-0001/{rollover_id}/strict-questions.json",
            "strict_answers_path": f".agent/thread-rollovers/{agent}/{lineage}/generation-0001/{rollover_id}/strict-answers.json",
            "strict_verdict_path": f".agent/thread-rollovers/{agent}/{lineage}/generation-0001/{rollover_id}/strict-verdict.json",
            "canary_proof_path": f".agent/thread-rollovers/{agent}/{lineage}/generation-0001/{rollover_id}/canary-pass.json",
        },
        "cleanup": {
            "old_automation_ready_to_delete": status == "started",
            "reason": "test",
        },
        "updated_at": prepared_at,
    }
    if status == "started":
        result["replacement"]["confirmed_at"] = prepared_at
        result["replacement"]["strict_verdict"] = {"verdict": "PASS", "correct": 10, "k": 10}
        result["replacement"]["canary_proof"] = {"status": "PASS"}
    return result


def _persist_lease(root: Path, lease: dict) -> Path:
    path = root / ".agent" / "thread-rollovers" / lease["agent"] / lease["lineage_id"] / "lease.json"
    _write_json(path, lease)
    return path


def _sync(root: Path, lease: dict) -> dict:
    path = _persist_lease(root, lease)
    return registry.sync_from_lease(root, path, lease)


def _bound_identity_updates(record: dict, replacement_task_id: str) -> dict:
    identity, title_transition = task_identity.bind_replacement(
        record["task_identity"],
        record["title_transition"],
        replacement_task_id=replacement_task_id,
        evidence="Exact native replacement fixture.",
        now="2026-07-16T10:00:00Z",
    )
    if title_transition["native_title_supported"]:
        identity, title_transition = task_identity.record_title_acknowledgement(
            identity,
            title_transition,
            replacement_task_id=replacement_task_id,
            succeeded=True,
            evidence="Exact native title acknowledgement fixture.",
            error="",
            now="2026-07-16T10:00:00Z",
        )
        identity, title_transition = task_identity.record_title_readback(
            identity,
            title_transition,
            replacement_task_id=replacement_task_id,
            observed_title=identity["visible_title"],
            succeeded=True,
            evidence="Exact native title readback fixture.",
            error="",
            now="2026-07-16T10:00:00Z",
        )
    return {"task_identity": identity, "title_transition": title_transition}


def _native_snapshot(record: dict, *, replacement_id: str | None, title: str | None = None) -> dict:
    key = record["key"]
    identity = record["task_identity"]
    title_transition = record["title_transition"]
    visible_title = identity["visible_title"]
    confirmed = record["confirmation"]["state"] == "confirmed"
    return {
        "agent": key["agent"],
        "lineage_id": key["lineage_id"],
        "rollover_id": key["rollover_id"],
        "captured_at": "2026-07-16T10:00:00Z",
        "source": {
            "thread_id": identity["predecessor_task_id"],
            "archived": False,
        },
        "replacement": {
            "created": replacement_id is not None,
            "thread_id": replacement_id,
            "title": title or visible_title,
        },
        "title_receipt": {
            "supported": title_transition["native_title_supported"],
            "replacement_thread_id": replacement_id,
            "readback_confirmed": True,
            "intended_title": visible_title,
            "readback_title": visible_title,
            **(
                {"receipt_path": "evidence/title-readback.json"}
                if title_transition["native_title_supported"]
                else {"fallback_receipt_path": "evidence/title-fallback.json"}
            ),
        },
        "confirmation": {
            "confirmed": confirmed,
            "replacement_thread_id": replacement_id if confirmed else None,
            "proof_path": "evidence/confirmation.json" if confirmed else None,
        },
        "heartbeat": {
            "automation_id": record["heartbeat"]["automation_id"],
            "retired": False,
            "cleanup_authorized": False,
        },
        "evidence_paths": ["evidence/native-app-snapshot.json"],
    }


def _disposition_proof(record: dict, *, reason: str = "operator adjudication") -> dict:
    return {
        **record["key"],
        "captured_at": "2026-07-16T10:00:00Z",
        "reason": reason,
        "assertions": {
            "not_confirmed_active": True,
            "no_valid_replacement_owns_lineage": True,
            "no_unrecorded_native_create": True,
            "no_active_heartbeat_dependency": True,
            "selected_exact_ids_match": True,
        },
        "evidence_paths": ["evidence/operator-adjudication.json"],
    }


def _cleanup_proof(record: dict) -> dict:
    return {
        **record["key"],
        "captured_at": "2026-07-16T10:00:00Z",
        "reason": "exact successor and native cleanup proved",
        "assertions": {
            "confirmed_successor_exact": True,
            "predecessor_archived_exact": True,
            "heartbeat_retirement_authorized": True,
            "heartbeat_retired_exact": True,
            "selected_exact_ids_match": True,
        },
        "evidence_paths": ["evidence/archive.json", "evidence/automation-retired.json"],
    }


def _persist_proof_evidence(root: Path, proof: dict) -> dict:
    for path in proof["evidence_paths"]:
        _write_json(root / path, {"kind": "test_evidence", "path": path})
    return proof


def _persist_snapshot_evidence(root: Path, snapshot: dict) -> dict:
    paths = list(snapshot["evidence_paths"])
    for container, key in (
        (snapshot["title_receipt"], "receipt_path"),
        (snapshot["title_receipt"], "fallback_receipt_path"),
        (snapshot["confirmation"], "proof_path"),
        (snapshot["source"], "archive_receipt_path"),
        (snapshot["heartbeat"], "retirement_receipt_path"),
    ):
        value = container.get(key)
        if isinstance(value, str):
            paths.append(value)
    for path in paths:
        _write_json(root / path, {"kind": "test_evidence", "path": path})
    return snapshot


def test_four_pending_rollovers_allow_each_exact_selector(tmp_path: Path) -> None:
    leases = [
        _lease(lineage=f"lineage-a{index}", rollover_id=f"rollover-r{index}", source=f"source-{index}")
        for index in range(1, 5)
    ]
    for lease in leases:
        _sync(tmp_path, lease)

    records, errors = registry.scan_records(tmp_path)
    assert errors == []
    assert len([record for record in records if registry.is_live_pending(record)]) == 4
    selected = registry.select_exact(records, source_thread_id="source-3")
    assert [record["key"]["rollover_id"] for record in selected] == ["rollover-r3"]
    selected = registry.select_exact(records, lineage_id="lineage-a4", rollover_id="rollover-r4")
    assert [record["task_identity"]["predecessor_task_id"] for record in selected] == ["source-4"]


def test_cli_script_entrypoint_runs_from_repo_root(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    result = subprocess.run(
        [
            str(repo_root / ".venv/bin/python"),
            str(repo_root / "scripts/orchestration/rollover_registry_cli.py"),
            "--repo-root",
            str(tmp_path),
            "audit",
        ],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["counts"]["total"] == 0


@pytest.mark.parametrize("agent", ["codex", "claude", "gemini", "orchestrator"])
def test_supported_agents_share_one_registry_contract(tmp_path: Path, agent: str) -> None:
    record = _sync(
        tmp_path,
        _lease(agent=agent, lineage=f"lineage-{agent}", rollover_id=f"rollover-{agent}"),
    )

    assert record["schema_version"] == registry.REGISTRY_SCHEMA_VERSION
    assert record["key"] == {
        "agent": agent,
        "lineage_id": f"lineage-{agent}",
        "rollover_id": f"rollover-{agent}",
    }


def test_generic_cli_is_fail_closed_with_actionable_candidates(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    for index in range(1, 5):
        _sync(
            tmp_path,
            _lease(lineage=f"lineage-c{index}", rollover_id=f"rollover-c{index}", source=f"source-c{index}"),
        )

    returncode = rollover_registry_cli.main(["--repo-root", str(tmp_path), "detect", "--agent", "codex"])
    payload = json.loads(capsys.readouterr().out)

    assert returncode == 2
    assert payload["error"] == "multiple_live_pending_rollovers"
    assert payload["mutation_allowed"] is False
    assert len(payload["candidates"]) == 4
    assert all(
        {"title", "issue", "epic", "lineage_id", "rollover_id", "state", "age_seconds", "next_safe_action"}
        <= candidate.keys()
        for candidate in payload["candidates"]
    )


def test_generic_cli_refuses_single_candidate_when_another_source_is_corrupt(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _sync(tmp_path, _lease(lineage="lineage-only-visible", rollover_id="rollover-only-visible"))
    corrupt = registry.registry_root(tmp_path) / "codex" / "lineage-hidden" / "rollover-hidden" / "record.json"
    _write_json(corrupt, {"schema_version": 999})

    returncode = rollover_registry_cli.main(["--repo-root", str(tmp_path), "detect", "--agent", "codex"])
    payload = json.loads(capsys.readouterr().out)

    assert returncode == 2
    assert payload["error"] == "inconsistent_or_corrupt_rollover_sources"
    assert payload["mutation_allowed"] is False
    assert len(payload["candidates"]) == 1
    assert payload["registry_errors"][0]["path"].endswith("record.json")


def test_exact_cli_selector_ignores_unrelated_pending(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    for index in range(1, 5):
        _sync(
            tmp_path,
            _lease(lineage=f"lineage-e{index}", rollover_id=f"rollover-e{index}", source=f"source-e{index}"),
        )

    returncode = rollover_registry_cli.main(
        [
            "--repo-root",
            str(tmp_path),
            "detect",
            "--source-thread-id",
            "source-e3",
            "--lineage-id",
            "lineage-e3",
            "--rollover-id",
            "rollover-e3",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert returncode == 0
    assert payload["candidate"]["rollover_id"] == "rollover-e3"
    assert payload["unrelated_live_pending"] == 3


def test_wrong_lineage_rollover_pairing_finds_no_record(tmp_path: Path) -> None:
    _sync(tmp_path, _lease(lineage="lineage-a1", rollover_id="rollover-r1", source="source-1"))
    _sync(tmp_path, _lease(lineage="lineage-a2", rollover_id="rollover-r2", source="source-2"))
    records, _ = registry.scan_records(tmp_path)

    assert registry.select_exact(records, lineage_id="lineage-a1", rollover_id="rollover-r2") == []


def test_confirmed_rollover_is_not_live_and_requires_cleanup(tmp_path: Path) -> None:
    record = _sync(
        tmp_path,
        _lease(
            lineage="lineage-f039",
            rollover_id="rollover-f039",
            source="source-f039",
            replacement="replacement-f039",
            status="started",
        ),
    )

    assert record["state"] == registry.RolloverState.CONFIRMED.value
    assert record["strict_recall"] == {
        "state": "passed",
        "score": 10,
        "verdict_path": (
            ".agent/thread-rollovers/codex/lineage-f039/generation-0001/"
            "rollover-f039/strict-verdict.json"
        ),
    }
    assert not registry.is_live_pending(record)
    audit = registry.audit_fleet(tmp_path, now=datetime(2026, 7, 16, 10, tzinfo=UTC))
    assert audit["entries"][0]["classification"] == "confirmed but incompletely cleaned"


def test_incident_shape_allows_exact_aef219_and_leaves_unrelated_packets_untouched(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    confirmed = _sync(
        tmp_path,
        _lease(
            lineage="lineage-f039",
            rollover_id="rollover-f039",
            source="source-f039",
            replacement="replacement-f039",
            status="started",
        ),
    )
    target = _sync(
        tmp_path,
        _lease(
            lineage="lineage-4ad435086af0f3a1111550d8",
            rollover_id="rollover-aef219c119ed4141919c2e7fd90860a8",
            source="source-aef219",
        ),
    )
    unrelated = [
        _sync(
            tmp_path,
            _lease(
                lineage=f"lineage-unrelated-{index}",
                rollover_id=f"rollover-unrelated-{index}",
                source=f"source-unrelated-{index}",
            ),
        )
        for index in range(1, 4)
    ]

    rc = rollover_registry_cli.main(
        [
            "--repo-root",
            str(tmp_path),
            "detect",
            "--agent",
            "codex",
            "--source-thread-id",
            "source-aef219",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    audit = registry.audit_fleet(tmp_path)

    assert rc == 0
    assert payload["candidate"]["rollover_id"] == target["key"]["rollover_id"]
    assert audit["counts"]["live_pending"] == 4
    assert not registry.is_live_pending(confirmed)
    for packet in unrelated:
        current = registry.load_record(tmp_path, **packet["key"])
        assert current["state"] == registry.RolloverState.AWAITING_NATIVE_CREATE.value


def _retire_native_plan(lease: dict) -> dict:
    """Model a lease whose unsatisfiable legacy native plan was retired at migration."""
    retired = lease["replacement"].pop("native_lifecycle")
    lease["replacement"]["native_lifecycle_retired"] = {
        **retired,
        "status": "retired_non_native_harness",
        "retired_at": "2026-07-16T12:00:00Z",
        "reason": "legacy native plan is unsatisfiable on a harness without a native adapter",
    }
    return lease


def test_retired_non_native_lease_projects_prepared_not_awaiting_native_create(tmp_path: Path) -> None:
    lease = _retire_native_plan(
        _lease(
            agent="claude-infra",
            lineage="lineage-retired-unbound",
            rollover_id="rollover-retired-unbound",
            source="source-retired-unbound",
        )
    )

    record = _sync(tmp_path, lease)

    assert lease["replacement"]["title_transition"]["native_title_supported"] is False
    assert record["state"] == registry.RolloverState.PREPARED.value


def test_retired_non_native_lease_with_bound_fallback_projects_replacement_created(tmp_path: Path) -> None:
    lease = _retire_native_plan(
        _lease(
            agent="claude-infra",
            lineage="lineage-retired-bound",
            rollover_id="rollover-retired-bound",
            source="source-retired-bound",
            replacement="replacement-fallback-bound",
        )
    )

    record = _sync(tmp_path, lease)

    assert lease["replacement"]["title_transition"]["state"] == "fallback_recorded"
    assert record["state"] == registry.RolloverState.REPLACEMENT_CREATED.value


def test_stale_age_is_read_only_and_never_deletes_packet(tmp_path: Path) -> None:
    record = _sync(
        tmp_path,
        _lease(
            lineage="lineage-stale",
            rollover_id="rollover-stale",
            prepared_at="2026-07-01T00:00:00Z",
        ),
    )
    path = registry.record_path(tmp_path, **record["key"])
    before = path.read_bytes()

    audit = registry.audit_fleet(
        tmp_path,
        stale_hours=12,
        now=datetime(2026, 7, 16, 10, tzinfo=UTC),
    )

    assert audit["entries"][0]["classification"] == "stale and requiring operator adjudication"
    assert path.read_bytes() == before


def test_authoritative_reconciliation_records_unrecorded_successor_once(tmp_path: Path) -> None:
    record = _sync(tmp_path, _lease(lineage="lineage-unrecorded", rollover_id="rollover-unrecorded"))
    snapshot = _native_snapshot(record, replacement_id="replacement-authoritative")
    _persist_snapshot_evidence(tmp_path, snapshot)
    report = registry.reconcile_snapshot(record, snapshot)
    assert report["proposed_transitions"] == [registry.RolloverState.REPLACEMENT_CREATED.value]

    receipt = registry.apply_reconciliation(tmp_path, record=record, snapshot=snapshot)
    repeated = registry.apply_reconciliation(tmp_path, record=record, snapshot=snapshot)
    receipt_path = next(registry.record_path(tmp_path, **record["key"]).parent.glob("reconciliation/*/receipt.json"))
    receipt_path.unlink()
    crash_retry = registry.apply_reconciliation(tmp_path, record=record, snapshot=snapshot)
    current = registry.load_record(tmp_path, **record["key"])

    assert receipt == repeated
    assert crash_retry["snapshot_digest"] == receipt["snapshot_digest"]
    assert current["task_identity"]["replacement_task_id"] == "replacement-authoritative"
    assert current["state"] == registry.RolloverState.REPLACEMENT_CREATED.value


def test_reconciliation_never_infers_creation_from_title(tmp_path: Path) -> None:
    record = _sync(tmp_path, _lease(lineage="lineage-title", rollover_id="rollover-title"))
    snapshot = _native_snapshot(record, replacement_id=None, title=record["task_identity"]["visible_title"])

    report = registry.reconcile_snapshot(record, snapshot)

    assert report["proposed_transitions"] == []
    assert report["consistent"] is False
    assert "title receipt cannot exist" in " ".join(report["discrepancies"])
    assert record["state"] == registry.RolloverState.AWAITING_NATIVE_CREATE.value


def test_reconciliation_applies_exact_confirm_archive_and_retire_boundaries(tmp_path: Path) -> None:
    record = _sync(
        tmp_path,
        _lease(
            lineage="lineage-reconciled-cleanup",
            rollover_id="rollover-reconciled-cleanup",
            replacement="replacement-reconciled-cleanup",
            status="resumed",
        ),
    )
    for state in (registry.RolloverState.STRICT_RECALL_PASSED, registry.RolloverState.CANARY_PASSED):
        record = registry.transition(tmp_path, **record["key"], state=state, reason="exact test proof")
    snapshot = _native_snapshot(record, replacement_id=record["task_identity"]["replacement_task_id"])
    snapshot["confirmation"] = {
        "confirmed": True,
        "replacement_thread_id": record["task_identity"]["replacement_task_id"],
        "proof_path": "evidence/confirmation.json",
    }
    snapshot["source"] |= {
        "archived": True,
        "archive_receipt_path": "evidence/archive.json",
    }
    snapshot["heartbeat"] |= {
        "retired": True,
        "cleanup_authorized": True,
        "retirement_receipt_path": "evidence/heartbeat-retirement.json",
    }
    _persist_snapshot_evidence(tmp_path, snapshot)

    report = registry.reconcile_snapshot(record, snapshot)
    receipt = registry.apply_reconciliation(tmp_path, record=record, snapshot=snapshot)
    current = registry.load_record(tmp_path, **record["key"])

    assert report["consistent"] is True
    assert report["proposed_transitions"] == [
        registry.RolloverState.CONFIRMED.value,
        registry.RolloverState.PREDECESSOR_ARCHIVED.value,
        registry.RolloverState.HEARTBEAT_RETIRED.value,
    ]
    assert receipt["applied_transitions"] == report["proposed_transitions"]
    assert current["state"] == registry.RolloverState.HEARTBEAT_RETIRED.value
    assert set(report["receipt_paths"]) <= set(current["receipts"])


def test_reconciliation_rejects_missing_authoritative_confirmation(tmp_path: Path) -> None:
    record = _sync(
        tmp_path,
        _lease(
            lineage="lineage-confirmed-mismatch",
            rollover_id="rollover-confirmed-mismatch",
            replacement="replacement-confirmed-mismatch",
            status="started",
        ),
    )
    snapshot = _native_snapshot(record, replacement_id=record["task_identity"]["replacement_task_id"])
    snapshot["confirmation"] = {
        "confirmed": False,
        "replacement_thread_id": None,
        "proof_path": None,
    }

    report = registry.reconcile_snapshot(record, snapshot)

    assert report["consistent"] is False
    assert "authoritative confirmation proof is absent" in " ".join(report["discrepancies"])


def test_reconciliation_rejects_cross_lineage_snapshot(tmp_path: Path) -> None:
    record = _sync(tmp_path, _lease(lineage="lineage-one", rollover_id="rollover-one"))
    snapshot = _native_snapshot(record, replacement_id="replacement-one")
    snapshot["lineage_id"] = "lineage-other"

    with pytest.raises(ValueError, match="exact IDs"):
        registry.reconcile_snapshot(record, snapshot)


def test_reconciliation_rejects_title_receipt_for_another_replacement(tmp_path: Path) -> None:
    record = _sync(
        tmp_path,
        _lease(
            lineage="lineage-title-receipt",
            rollover_id="rollover-title-receipt",
            replacement="replacement-title-receipt",
            status="resumed",
        ),
    )
    snapshot = _native_snapshot(record, replacement_id="replacement-title-receipt")
    snapshot["title_receipt"]["replacement_thread_id"] = "replacement-other"

    report = registry.reconcile_snapshot(record, snapshot)

    assert report["consistent"] is False
    assert "title receipt does not identify the exact native replacement" in report["discrepancies"]


def test_reconciliation_rejects_archival_without_exact_confirmation(tmp_path: Path) -> None:
    record = _sync(tmp_path, _lease(lineage="lineage-archive", rollover_id="rollover-archive"))
    snapshot = _native_snapshot(record, replacement_id="replacement-archive")
    snapshot["source"]["archived"] = True
    snapshot["source"]["archive_receipt_path"] = "evidence/archive.json"

    result = registry.reconcile_snapshot(record, snapshot)

    assert result["consistent"] is False
    assert "predecessor archival lacks exact confirmed-successor proof" in result["discrepancies"]


def test_reconciliation_rejects_premature_heartbeat_cleanup_authorization(tmp_path: Path) -> None:
    record = _sync(tmp_path, _lease(lineage="lineage-premature", rollover_id="rollover-premature"))
    snapshot = _native_snapshot(record, replacement_id="replacement-premature")
    snapshot["heartbeat"]["cleanup_authorized"] = True

    result = registry.reconcile_snapshot(record, snapshot)

    assert result["consistent"] is False
    assert "cleanup authorization precedes" in " ".join(result["discrepancies"])


def test_projection_rejects_duplicate_successor_for_exact_rollover(tmp_path: Path) -> None:
    first = _lease(
        lineage="lineage-duplicate",
        rollover_id="rollover-duplicate",
        replacement="replacement-one",
        status="resumed",
    )
    _sync(tmp_path, first)
    duplicate = _lease(
        lineage="lineage-duplicate",
        rollover_id="rollover-duplicate",
        replacement="replacement-two",
        status="resumed",
    )

    with pytest.raises(ValueError, match="replacement_task_id conflicts"):
        _sync(tmp_path, duplicate)


def test_supersede_requires_proof_plan_and_idempotent_apply(tmp_path: Path) -> None:
    record = _sync(tmp_path, _lease(lineage="lineage-sup", rollover_id="rollover-sup"))
    bad_proof = _disposition_proof(record)
    bad_proof["assertions"]["no_unrecorded_native_create"] = False
    with pytest.raises(ValueError, match="no_unrecorded_native_create"):
        registry.create_maintenance_plan(
            tmp_path,
            record=record,
            action=registry.MaintenanceAction.SUPERSEDE,
            proof=bad_proof,
        )

    plan = registry.create_maintenance_plan(
        tmp_path,
        record=record,
        action=registry.MaintenanceAction.SUPERSEDE,
        proof=_persist_proof_evidence(tmp_path, _disposition_proof(record)),
    )
    receipt = registry.apply_maintenance_plan(tmp_path, plan_path=Path(plan["plan_path"]))
    Path(tmp_path / plan["plan_path"]).parent.joinpath("receipt.json").unlink()
    crash_retry = registry.apply_maintenance_plan(tmp_path, plan_path=Path(plan["plan_path"]))

    assert receipt["final_state"] == registry.RolloverState.SUPERSEDED.value
    assert crash_retry["final_state"] == registry.RolloverState.SUPERSEDED.value
    assert not registry.is_live_pending(registry.load_record(tmp_path, **record["key"]))


def test_maintenance_refuses_non_durable_evidence_paths(tmp_path: Path) -> None:
    record = _sync(tmp_path, _lease(lineage="lineage-evidence", rollover_id="rollover-evidence"))

    with pytest.raises(ValueError, match="does not exist as durable evidence"):
        registry.create_maintenance_plan(
            tmp_path,
            record=record,
            action=registry.MaintenanceAction.SUPERSEDE,
            proof=_disposition_proof(record),
        )


def test_maintenance_apply_revalidates_action_target_semantics(tmp_path: Path) -> None:
    record = _sync(tmp_path, _lease(lineage="lineage-forged", rollover_id="rollover-forged"))
    plan = registry.create_maintenance_plan(
        tmp_path,
        record=record,
        action=registry.MaintenanceAction.SUPERSEDE,
        proof=_persist_proof_evidence(tmp_path, _disposition_proof(record)),
    )
    plan_path = tmp_path / plan["plan_path"]
    forged = json.loads(plan_path.read_text(encoding="utf-8"))
    forged["target_states"] = [registry.RolloverState.ABANDONED_WITH_PROOF.value]
    unsigned = dict(forged)
    unsigned.pop("digest")
    forged["digest"] = registry.sha256_digest(unsigned)
    _write_json(plan_path, forged)

    with pytest.raises(ValueError, match="target states do not match"):
        registry.apply_maintenance_plan(tmp_path, plan_path=plan_path)

    assert registry.load_record(tmp_path, **record["key"])["state"] == record["state"]


def test_blocked_packet_is_visible_but_not_mutation_authorized(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    record = _sync(
        tmp_path,
        _lease(
            lineage="lineage-blocked-resume",
            rollover_id="rollover-blocked-resume",
            replacement="replacement-blocked-resume",
            status="resumed",
        ),
    )
    registry.transition(
        tmp_path,
        **record["key"],
        state=registry.RolloverState.BLOCKED,
        reason="exact title proof missing",
    )

    detect_rc = rollover_registry_cli.main(
        [
            "--repo-root",
            str(tmp_path),
            "detect",
            "--lineage-id",
            record["key"]["lineage_id"],
            "--rollover-id",
            record["key"]["rollover_id"],
        ]
    )
    detected = json.loads(capsys.readouterr().out)
    resume_rc = rollover_registry_cli.main(
        [
            "--repo-root",
            str(tmp_path),
            "resume-exact",
            "--lineage-id",
            record["key"]["lineage_id"],
            "--rollover-id",
            record["key"]["rollover_id"],
            "--replacement-thread-id",
            "replacement-blocked-resume",
        ]
    )

    assert detect_rc == 0
    assert detected["mutation_allowed"] is False
    assert resume_rc == 2
    assert "requires reconciliation or maintenance" in capsys.readouterr().out


def test_failed_native_boundary_projects_as_blocked(tmp_path: Path) -> None:
    lease = _lease(lineage="lineage-native-failed", rollover_id="rollover-native-failed")
    lease["replacement"]["native_lifecycle"]["status"] = "title_readback_failed"

    record = _sync(tmp_path, lease)

    assert record["state"] == registry.RolloverState.BLOCKED.value
    assert record["last_successful_boundary"] == registry.RolloverState.AWAITING_NATIVE_CREATE.value
    assert record["blocking_reason"] == "native rollover boundary blocked: title_readback_failed"
    assert registry.allows_exact_progress(record) is False


def test_existing_registry_projects_new_native_failure_as_blocked(tmp_path: Path) -> None:
    lease = _lease(lineage="lineage-new-failure", rollover_id="rollover-new-failure")
    _sync(tmp_path, lease)
    lease["replacement"]["native_lifecycle"]["status"] = "native_create_failed"

    blocked = _sync(tmp_path, lease)

    assert blocked["state"] == registry.RolloverState.BLOCKED.value
    assert blocked["last_successful_boundary"] == registry.RolloverState.AWAITING_NATIVE_CREATE.value
    assert blocked["blocking_reason"] == "native rollover boundary blocked: native_create_failed"
    assert registry.allows_exact_progress(blocked) is False


def test_blocked_packet_cannot_be_cleared_at_the_same_boundary(tmp_path: Path) -> None:
    record = _sync(
        tmp_path,
        _lease(
            lineage="lineage-blocked-boundary",
            rollover_id="rollover-blocked-boundary",
            replacement="replacement-blocked-boundary",
            status="resumed",
        ),
    )
    registry.transition(
        tmp_path,
        **record["key"],
        state=registry.RolloverState.BLOCKED,
        reason="authoritative proof missing",
    )

    with pytest.raises(ValueError, match="authoritative proof beyond"):
        registry.transition(
            tmp_path,
            **record["key"],
            state=registry.RolloverState.RESUMED,
            reason="unproved unblock",
        )


def test_cli_rejects_wrong_exact_plan_before_mutation(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    selected = _sync(tmp_path, _lease(lineage="lineage-selected", rollover_id="rollover-selected"))
    other = _sync(tmp_path, _lease(lineage="lineage-other", rollover_id="rollover-other"))
    plan = registry.create_maintenance_plan(
        tmp_path,
        record=other,
        action=registry.MaintenanceAction.SUPERSEDE,
        proof=_persist_proof_evidence(tmp_path, _disposition_proof(other)),
    )

    rc = rollover_registry_cli.main(
        [
            "--repo-root",
            str(tmp_path),
            "supersede-exact",
            "--lineage-id",
            selected["key"]["lineage_id"],
            "--rollover-id",
            selected["key"]["rollover_id"],
            "--apply",
            "--plan-file",
            plan["plan_path"],
        ]
    )

    assert rc == 2
    assert "exact IDs do not match the selected registry record" in capsys.readouterr().out
    current = registry.load_record(tmp_path, **other["key"])
    assert current["state"] == registry.RolloverState.AWAITING_NATIVE_CREATE.value


def test_abandonment_refuses_confirmed_active_rollover(tmp_path: Path) -> None:
    record = _sync(
        tmp_path,
        _lease(
            lineage="lineage-confirmed",
            rollover_id="rollover-confirmed",
            replacement="replacement-confirmed",
            status="started",
        ),
    )

    with pytest.raises(ValueError, match="confirmed active"):
        registry.create_maintenance_plan(
            tmp_path,
            record=record,
            action=registry.MaintenanceAction.ABANDON,
            proof=_disposition_proof(record),
        )


def test_finish_cleanup_requires_exact_confirmation_and_heartbeat_proof(tmp_path: Path) -> None:
    record = _sync(
        tmp_path,
        _lease(
            lineage="lineage-cleanup",
            rollover_id="rollover-cleanup",
            replacement="replacement-cleanup",
            status="started",
        ),
    )
    plan = registry.create_maintenance_plan(
        tmp_path,
        record=record,
        action=registry.MaintenanceAction.FINISH_CLEANUP,
        proof=_persist_proof_evidence(tmp_path, _cleanup_proof(record)),
    )

    receipt = registry.apply_maintenance_plan(tmp_path, plan_path=Path(plan["plan_path"]))
    current = registry.load_record(tmp_path, **record["key"])

    assert receipt["final_state"] == registry.RolloverState.HEARTBEAT_RETIRED.value
    assert current["predecessor_archival"]["state"] == "archived"
    assert current["heartbeat"]["state"] == "retired"
    assert registry.classify(
        current,
        now=datetime(2026, 7, 16, 10, tzinfo=UTC),
        stale_after=timedelta(hours=24),
    ) is registry.AuditClassification.CONFIRMED_FULLY_CLEANED


def test_one_lineage_confirmation_never_authorizes_another_cleanup(tmp_path: Path) -> None:
    first = _sync(
        tmp_path,
        _lease(
            lineage="lineage-cleanup-one",
            rollover_id="rollover-cleanup-one",
            replacement="replacement-cleanup-one",
            status="started",
        ),
    )
    second = _sync(
        tmp_path,
        _lease(
            lineage="lineage-cleanup-two",
            rollover_id="rollover-cleanup-two",
            replacement="replacement-cleanup-two",
            status="started",
        ),
    )

    with pytest.raises(ValueError, match="exact IDs"):
        registry.create_maintenance_plan(
            tmp_path,
            record=second,
            action=registry.MaintenanceAction.FINISH_CLEANUP,
            proof=_cleanup_proof(first),
        )


def test_migration_preserves_legacy_paths_and_proofs(tmp_path: Path) -> None:
    lease = _lease(lineage="lineage-migrate", rollover_id="rollover-migrate")
    lease_path = _persist_lease(tmp_path, lease)
    proof_path = lease_path.parent / "generation-0001" / "rollover-migrate" / "legacy-proof.json"
    _write_json(proof_path, {"status": "legacy-proof"})
    lease["replacement"]["canary_proof_path"] = proof_path.relative_to(tmp_path).as_posix()
    _write_json(lease_path, lease)

    plan = registry.migrate_existing(tmp_path, apply=False, evidence="")
    applied = registry.migrate_existing(tmp_path, apply=True, evidence="operator-approved non-destructive import")
    record = registry.load_record(
        tmp_path,
        agent="codex",
        lineage_id="lineage-migrate",
        rollover_id="rollover-migrate",
    )

    assert plan["mode"] == "plan"
    assert applied["written"] == 1
    assert lease_path.relative_to(tmp_path).as_posix() in record["evidence_paths"]
    assert proof_path.relative_to(tmp_path).as_posix() in record["evidence_paths"]
    assert any("non-destructive registry migration" in event["reason"] for event in record["history"])


def test_task_family_migration_preserves_blocked_state_after_exact_binding(tmp_path: Path) -> None:
    operation_root = (
        tmp_path
        / ".agent"
        / "task-families"
        / "rollover-lineage-plan-blocked"
        / "operations"
        / "operation-plan-blocked"
    )
    plan_path = operation_root / "rollover-plan.json"
    _write_json(
        plan_path,
        {
            "agent": "codex",
            "family_id": "rollover-lineage-plan-blocked",
            "operation_id": "operation-plan-blocked",
            "lineage_id": "lineage-plan-blocked",
            "rollover_id": "rollover-plan-blocked",
            "source_thread_id": "source-plan-blocked",
            "generation": 1,
            "intended_title": "INFRA #5296 — Fleet rollover registry",
        },
    )
    _write_json(operation_root / "state.json", {"state": "blocked", "details": {"status": "title_failed"}})
    _write_json(operation_root / "rollover-binding.json", {"replacement_thread_id": "replacement-plan-blocked"})

    records, errors = registry.discover_legacy_records(tmp_path)
    record = records[("codex", "lineage-plan-blocked", "rollover-plan-blocked")]

    assert errors == []
    assert record["state"] == registry.RolloverState.BLOCKED.value
    assert record["last_successful_boundary"] == registry.RolloverState.REPLACEMENT_CREATED.value
    assert record["task_identity"]["replacement_task_id"] == "replacement-plan-blocked"
    assert registry.allows_exact_progress(record) is False


def test_corrupt_registry_entry_is_classified_without_hiding_valid_entries(tmp_path: Path) -> None:
    _sync(tmp_path, _lease(lineage="lineage-valid", rollover_id="rollover-valid"))
    corrupt = registry.registry_root(tmp_path) / "codex" / "lineage-corrupt" / "rollover-corrupt" / "record.json"
    _write_json(corrupt, {"schema_version": 999})

    audit = registry.audit_fleet(tmp_path)

    assert audit["counts"]["total"] == 2
    assert audit["counts"]["corrupt"] == 1
    assert any(
        entry["classification"] == registry.AuditClassification.INCONSISTENT_CORRUPT.value for entry in audit["entries"]
    )
    assert audit["errors"][0]["path"].endswith("record.json")


def test_audit_classifies_packet_with_corrupt_referenced_lease_once(tmp_path: Path) -> None:
    record = _sync(tmp_path, _lease(lineage="lineage-corrupt-lease", rollover_id="rollover-corrupt-lease"))
    (tmp_path / record["lease_path"]).write_text("{not-json\n", encoding="utf-8")

    audit = registry.audit_fleet(tmp_path)

    assert audit["counts"] == {"total": 1, "live_pending": 0, "corrupt": 1}
    assert audit["entries"][0]["classification"] == registry.AuditClassification.INCONSISTENT_CORRUPT.value
    assert audit["entries"][0]["source_errors"][0]["path"] == record["lease_path"]


def test_audit_fails_closed_on_corrupt_referenced_task_family_receipt(tmp_path: Path) -> None:
    lease = _lease(lineage="lineage-corrupt-receipt", rollover_id="rollover-corrupt-receipt")
    record = _sync(tmp_path, lease)
    native = lease["replacement"]["native_lifecycle"]
    receipt_path = (
        tmp_path
        / ".agent"
        / "task-families"
        / native["family_id"]
        / "operations"
        / native["operation_id"]
        / "receipt.json"
    )
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text("{not-json\n", encoding="utf-8")

    audit = registry.audit_fleet(tmp_path)

    assert audit["counts"] == {"total": 1, "live_pending": 0, "corrupt": 1}
    assert audit["entries"][0]["classification"] == registry.AuditClassification.INCONSISTENT_CORRUPT.value
    assert audit["entries"][0]["source_errors"][0]["path"] == record["lease_path"]
    assert "receipt.json" in audit["entries"][0]["source_errors"][0]["error"]


def test_exact_selector_refuses_corrupt_authoritative_record(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    record = _sync(tmp_path, _lease(lineage="lineage-corrupt-exact", rollover_id="rollover-corrupt-exact"))
    _write_json(registry.record_path(tmp_path, **record["key"]), {"schema_version": 999})

    rc = rollover_registry_cli.main(
        [
            "--repo-root",
            str(tmp_path),
            "detect",
            "--source-thread-id",
            record["task_identity"]["predecessor_task_id"],
        ]
    )

    assert rc == 2
    assert "corrupt durable source" in capsys.readouterr().out


def test_record_source_errors_includes_referenced_evidence_paths(tmp_path: Path) -> None:
    record = _sync(tmp_path, _lease(lineage="lineage-source-error", rollover_id="rollover-source-error"))
    record["evidence_paths"].append("evidence/corrupt-receipt.json")
    source_error = {"path": "evidence/corrupt-receipt.json", "error": "invalid JSON"}

    assert registry.record_source_errors(tmp_path, record, [source_error]) == [source_error]


def test_transition_cannot_skip_required_boundaries(tmp_path: Path) -> None:
    record = _sync(tmp_path, _lease(lineage="lineage-boundary", rollover_id="rollover-boundary"))

    with pytest.raises(ValueError, match="cannot skip"):
        registry.transition(
            tmp_path,
            **record["key"],
            state=registry.RolloverState.CONFIRMED,
            reason="invalid direct confirmation",
        )


def test_native_task_family_paths_reject_traversal(tmp_path: Path) -> None:
    lease = _lease(lineage="lineage-path", rollover_id="rollover-path")
    lease["replacement"]["native_lifecycle"]["operation_id"] = "../outside"
    lease_path = _persist_lease(tmp_path, lease)

    with pytest.raises(ValueError, match="path-safe component"):
        registry.sync_from_lease(tmp_path, lease_path, lease)

    assert not (tmp_path / ".agent" / "task-families" / "outside").exists()


def test_registry_storage_rejects_symlink_escape(tmp_path: Path) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    agent_root = tmp_path / ".agent"
    agent_root.mkdir()
    (agent_root / "thread-rollover-registry").symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="inside the repository state root"):
        registry.record_path(
            tmp_path,
            agent="codex",
            lineage_id="lineage-symlink",
            rollover_id="rollover-symlink",
        )


def test_registry_record_rejects_absolute_evidence_path(tmp_path: Path) -> None:
    record = _sync(tmp_path, _lease(lineage="lineage-path-proof", rollover_id="rollover-path-proof"))
    record["evidence_paths"] = ["/tmp/untrusted-proof.json"]

    with pytest.raises(ValueError, match="repository-relative"):
        registry.validate_record(record)


def test_stale_lease_projection_cannot_regress_a_blocked_boundary(tmp_path: Path) -> None:
    lease = _lease(lineage="lineage-blocked", rollover_id="rollover-blocked")
    record = _sync(tmp_path, lease)
    created = registry.transition(
        tmp_path,
        **record["key"],
        state=registry.RolloverState.REPLACEMENT_CREATED,
        reason="native successor recorded",
        updates=_bound_identity_updates(record, "replacement-blocked"),
    )
    blocked = registry.transition(
        tmp_path,
        **record["key"],
        state=registry.RolloverState.BLOCKED,
        reason="awaiting exact title proof",
    )

    projected = registry.sync_from_lease(
        tmp_path,
        tmp_path / blocked["lease_path"],
        lease,
    )

    assert created["last_successful_boundary"] == registry.RolloverState.REPLACEMENT_CREATED.value
    assert projected["state"] == registry.RolloverState.BLOCKED.value
    assert projected["last_successful_boundary"] == registry.RolloverState.REPLACEMENT_CREATED.value
    assert projected["native_creation"]["state"] == "replacement_created"


def test_stale_terminal_projection_cannot_supersede_a_created_replacement(tmp_path: Path) -> None:
    lease = _lease(lineage="lineage-stale-terminal", rollover_id="rollover-stale-terminal")
    record = _sync(tmp_path, lease)
    created = registry.transition(
        tmp_path,
        **record["key"],
        state=registry.RolloverState.REPLACEMENT_CREATED,
        reason="native successor recorded",
        updates=_bound_identity_updates(record, "replacement-stale-terminal"),
    )
    native = lease["replacement"]["native_lifecycle"]
    task_state_path = (
        tmp_path
        / ".agent"
        / "task-families"
        / native["family_id"]
        / "operations"
        / native["operation_id"]
        / "state.json"
    )
    _write_json(task_state_path, {"state": "completed", "details": {"status": "superseded_before_native_create"}})

    projected = registry.sync_from_lease(tmp_path, tmp_path / created["lease_path"], lease)

    assert projected["state"] == registry.RolloverState.REPLACEMENT_CREATED.value
    assert projected["last_successful_boundary"] == registry.RolloverState.REPLACEMENT_CREATED.value
    assert not any(event["state"] == registry.RolloverState.SUPERSEDED.value for event in projected["history"])


def test_cold_cleanup_failure_preserves_confirmed_non_live_state(tmp_path: Path) -> None:
    lease = _lease(
        lineage="lineage-cold-blocked",
        rollover_id="rollover-cold-blocked",
        replacement="replacement-cold-blocked",
        status="started",
    )
    lease["replacement"]["native_lifecycle"]["status"] = "archive_authorization_blocked"

    record = _sync(tmp_path, lease)

    assert record["state"] == registry.RolloverState.CONFIRMED.value
    assert record["last_successful_boundary"] == registry.RolloverState.CONFIRMED.value
    assert record["blocking_reason"].startswith("native rollover boundary blocked")
    assert registry.is_live_pending(record) is False


def test_catchup_to_confirmed_preserves_cleanup_blocker_in_fleet_summary(tmp_path: Path) -> None:
    _sync(
        tmp_path,
        _lease(
            lineage="lineage-confirmed-catchup",
            rollover_id="rollover-confirmed-catchup",
            replacement="replacement-confirmed-catchup",
            status="resumed",
        ),
    )
    started = _lease(
        lineage="lineage-confirmed-catchup",
        rollover_id="rollover-confirmed-catchup",
        replacement="replacement-confirmed-catchup",
        status="started",
    )
    started["replacement"]["native_lifecycle"]["status"] = "archive_authorization_blocked"

    record = _sync(tmp_path, started)
    audit = registry.audit_fleet(tmp_path)

    assert record["state"] == registry.RolloverState.CONFIRMED.value
    assert registry.is_live_pending(record) is False
    assert record["blocking_reason"] == "native rollover boundary blocked: archive_authorization_blocked"
    assert audit["entries"][0]["blocking_reason"] == record["blocking_reason"]


def test_every_success_boundary_is_idempotent_after_crash_retry(tmp_path: Path) -> None:
    record = _sync(tmp_path, _lease(lineage="lineage-retry", rollover_id="rollover-retry"))
    boundaries = (
        registry.RolloverState.REPLACEMENT_CREATED,
        registry.RolloverState.RESUMED,
        registry.RolloverState.STRICT_RECALL_PASSED,
        registry.RolloverState.CANARY_PASSED,
        registry.RolloverState.CONFIRMED,
        registry.RolloverState.PREDECESSOR_ARCHIVED,
        registry.RolloverState.HEARTBEAT_RETIRED,
    )

    for boundary in boundaries:
        operation_id = f"retry-{boundary.value.lower()}"
        updates = (
            _bound_identity_updates(record, "replacement-retry")
            if boundary is registry.RolloverState.REPLACEMENT_CREATED
            else None
        )
        first = registry.transition(
            tmp_path,
            **record["key"],
            state=boundary,
            reason="boundary crash retry",
            operation_id=operation_id,
            updates=updates,
        )
        second = registry.transition(
            tmp_path,
            **record["key"],
            state=boundary,
            reason="boundary crash retry",
            operation_id=operation_id,
        )

        assert first == second
        assert sum(event.get("operation_id") == operation_id for event in second["history"]) == 1
