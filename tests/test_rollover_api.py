"""Read-only API coverage for the fleet rollover registry."""

from __future__ import annotations

from fastapi.testclient import TestClient

import scripts.api.rollover_router as rollover_router
from scripts.api.main import app
from scripts.orchestration import task_identity
from scripts.orchestration.task_family import rollover_registry as registry

client = TestClient(app, raise_server_exceptions=False)


def _record(
    *,
    lineage_id: str = "lineage-api",
    rollover_id: str = "rollover-api",
    source_thread_id: str = "source-api",
) -> dict:
    identity = task_identity.build_identity(
        repository=task_identity.DEFAULT_REPOSITORY,
        stream_epic=4707,
        stream_epic_url=None,
        github_issue_number=5296,
        github_issue_url=None,
        semantic_title="Fleet rollover registry",
        task_family="thread-rollover",
        role="codex",
        predecessor_task_id=source_thread_id,
        replacement_task_id=None,
        lineage_id=lineage_id,
        generation=1,
        terminal_goal="merge",
    )
    return {
        "schema_version": registry.REGISTRY_SCHEMA_VERSION,
        "key": {"agent": "codex", "lineage_id": lineage_id, "rollover_id": rollover_id},
        "task_identity": identity,
        "title_transition": task_identity.new_title_transition(
            harness="codex-app",
            visible_title_value=identity["visible_title"],
            prepared_at="2026-07-16T09:00:00Z",
        ),
        "state": registry.RolloverState.AWAITING_NATIVE_CREATE.value,
        "last_successful_boundary": registry.RolloverState.PREPARED.value,
        "native_creation": {"state": "awaiting_native_create", "family_id": None, "operation_id": None},
        "strict_recall": {"state": "pending", "score": None, "verdict_path": None},
        "canary": {"state": "pending", "proof_path": None},
        "confirmation": {"state": "pending", "confirmed_at": None, "confirmed_by": None},
        "predecessor_archival": {"state": "pending"},
        "heartbeat": {
            "automation_id": "automation-api",
            "state": "active_or_unknown",
            "cleanup_authorized": False,
        },
        "timestamps": {
            "prepared_at": "2026-07-16T09:00:00Z",
            "updated_at": "2026-07-16T09:00:00Z",
        },
        "lease_path": None,
        "packet_paths": {},
        "evidence_paths": ["evidence/prepare.json"],
        "receipts": [],
        "history": [],
        "blocking_reason": None,
        "terminal_reason": None,
        "last_reconciliation": None,
    }


def test_rollover_audit_route_is_read_only_and_uses_live_repo_root(monkeypatch, tmp_path):
    captured = {}

    def fake_audit(root, *, stale_hours=registry.DEFAULT_STALE_HOURS):
        captured["root"] = root
        captured["stale_hours"] = stale_hours
        return {
            "schema_version": 1,
            "generated_at": "2026-07-16T10:00:00Z",
            "counts": {"total": 1, "live_pending": 1, "corrupt": 0},
            "entries": [registry.candidate_summary(_record())],
            "errors": [],
            "mutation_allowed": False,
        }

    monkeypatch.setattr(rollover_router, "LIVE_REPO_ROOT", tmp_path)
    monkeypatch.setattr(rollover_router.registry, "audit_fleet", fake_audit)

    response = client.get("/api/rollovers")

    assert response.status_code == 200
    assert response.json()["mutation_allowed"] is False
    assert captured == {"root": tmp_path, "stale_hours": registry.DEFAULT_STALE_HOURS}


def test_rollover_audit_rejects_invalid_agent_filter(monkeypatch):
    monkeypatch.setattr(
        rollover_router.registry,
        "audit_fleet",
        lambda _root, *, stale_hours: {
            "counts": {"total": 0, "live_pending": 0, "corrupt": 0},
            "entries": [],
            "errors": [],
        },
    )

    response = client.get("/api/rollovers?agent=../codex")

    assert response.status_code == 400


def test_rollover_exact_selector_ignores_unrelated_pending_records(monkeypatch):
    selected = _record()
    unrelated = _record(
        lineage_id="lineage-other",
        rollover_id="rollover-other",
        source_thread_id="source-other",
    )
    monkeypatch.setattr(rollover_router.registry, "scan_records", lambda _root: ([selected, unrelated], []))

    response = client.get("/api/rollovers?source_thread_id=source-api")

    assert response.status_code == 200
    payload = response.json()
    assert payload["entry"]["lineage_id"] == "lineage-api"
    assert payload["classification"] == registry.AuditClassification.AWAITING_NATIVE_ACTION.value
    assert payload["mutation_allowed"] is False


def test_rollover_exact_selector_fails_closed_when_ambiguous(monkeypatch):
    first = _record()
    second = _record(
        lineage_id="lineage-other",
        rollover_id="rollover-other",
        source_thread_id="source-api",
    )
    monkeypatch.setattr(rollover_router.registry, "scan_records", lambda _root: ([first, second], []))

    response = client.get("/api/rollovers?source_thread_id=source-api")

    assert response.status_code == 409
    assert len(response.json()["detail"]["matches"]) == 2


def test_rollover_exact_selector_surfaces_corrupt_authoritative_record(monkeypatch, tmp_path):
    record = _record()
    corrupt_path = registry.record_path(tmp_path, **record["key"]).relative_to(tmp_path).as_posix()
    monkeypatch.setattr(rollover_router, "LIVE_REPO_ROOT", tmp_path)
    monkeypatch.setattr(
        rollover_router.registry,
        "scan_records",
        lambda _root: ([record], [{"path": corrupt_path, "error": "malformed record"}]),
    )

    response = client.get("/api/rollovers?source_thread_id=source-api")

    assert response.status_code == 409
    assert "corrupt durable source" in response.json()["detail"]["error"]


def test_rollover_orient_projection_exposes_only_actionable_entries(monkeypatch, tmp_path):
    actionable = {
        **registry.candidate_summary(_record()),
        "live_pending": True,
        "classification": registry.AuditClassification.AWAITING_NATIVE_ACTION.value,
    }
    finished = {**actionable, "live_pending": False, "classification": registry.AuditClassification.SUPERSEDED.value}
    monkeypatch.setattr(rollover_router, "LIVE_REPO_ROOT", tmp_path)
    monkeypatch.setattr(
        rollover_router.registry,
        "audit_fleet",
        lambda _root: {
            "generated_at": "2026-07-16T10:00:00Z",
            "counts": {"total": 2, "live_pending": 1, "corrupt": 0},
            "entries": [actionable, finished],
            "errors": [],
        },
    )

    payload = rollover_router.collect_rollover_orient_data()

    assert payload["actionable"] == [actionable]
    assert payload["counts"]["total"] == 2
