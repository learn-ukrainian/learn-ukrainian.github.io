"""End-to-end local coverage for P6 receipt issuance and Monitor retrieval."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from fastapi import FastAPI
from fastapi.testclient import TestClient

from scripts.api import rail_approval_router
from scripts.orchestration import rail_approval
from scripts.orchestration import rail_path_guard as guard

NOW = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)
HEAD = "c" * 40
TASK = "rail-p8-trail-migration"
PATH = "scripts/config/trails/rb1.trail.yaml"


def _monitor_get(client: TestClient):
    """Route the production Monitor client seam into a local in-process API."""

    def fetch(path: str):
        response = client.get(path)
        return response.status_code, response.text, {}

    return fetch


def test_operator_cli_issue_monitor_fetch_and_exact_binding(
    tmp_path, monkeypatch, capsys
) -> None:
    """Issue → Monitor API fetch → exact allow; foreign and expired remain deny."""
    registry = rail_approval.RailApprovalReceiptRegistry(tmp_path / "receipts.json")
    monkeypatch.setattr(rail_approval, "RailApprovalReceiptRegistry", lambda: registry)

    exit_code = rail_approval.main(
        [
            "issue",
            "--task-id",
            TASK,
            "--head-sha",
            HEAD,
            "--owned-path",
            PATH,
            "--issuer",
            "operator",
            "--ttl-hours",
            "1",
        ]
    )

    assert exit_code == 0
    issued = json.loads(capsys.readouterr().out)
    assert issued["issuer"] == "operator"
    assert registry.fetch(issued["receipt_id"]) == issued

    app = FastAPI()
    app.include_router(rail_approval_router.router, prefix="/api/rail-approvals")
    monkeypatch.setattr(rail_approval_router, "get_rail_approval_registry", lambda: registry)
    client = TestClient(app)
    served = client.get(f"/api/rail-approvals/{issued['receipt_id']}")
    assert served.status_code == 200
    assert served.json() == issued

    assert isinstance(
        guard.build_production_rail_approval_receipt_resolver().store,
        guard.MonitorRailApprovalReceiptStore,
    )
    monitor_store = guard.MonitorRailApprovalReceiptStore(get=_monitor_get(client))
    resolver = guard.ApprovedRailApprovalReceiptResolver(monitor_store)
    receipt = resolver.fetch(issued["receipt_id"])
    issued_at = datetime.fromisoformat(issued["issued_at"].replace("Z", "+00:00"))
    expires_at = datetime.fromisoformat(issued["expires_at"].replace("Z", "+00:00"))
    allowed = guard.decide_rail_path_mutation(
        task_id=TASK,
        candidate_paths=[PATH],
        head_sha=HEAD,
        receipt=receipt,
        now=lambda: issued_at,
    )
    foreign = guard.decide_rail_path_mutation(
        task_id="another-task",
        candidate_paths=[PATH],
        head_sha=HEAD,
        receipt=receipt,
        now=lambda: issued_at,
    )

    assert allowed.allowed is True
    assert allowed.reason == "rail_approval_verified"
    assert foreign.allowed is False
    assert foreign.reason == "rail_approval_task_mismatch"

    expired_resolver = guard.ApprovedRailApprovalReceiptResolver(
        monitor_store,
        now=lambda: expires_at + timedelta(seconds=1),
    )
    expired = guard.decide_rail_path_mutation_with_production_receipt(
        task_id=TASK,
        candidate_paths=[PATH],
        head_sha=HEAD,
        receipt_id=issued["receipt_id"],
        resolver=expired_resolver,
        now=lambda: expires_at + timedelta(seconds=1),
    )

    assert expired.allowed is False
    assert expired.reason == "expired_rail_approval_receipt"


def test_receipt_registry_refuses_overwriting_an_issued_receipt(tmp_path) -> None:
    registry = rail_approval.RailApprovalReceiptRegistry(tmp_path / "receipts.json")
    receipt = rail_approval.create_rail_approval_receipt(
        task_id=TASK,
        head_sha=HEAD,
        owned_paths=[PATH],
        issuer="advisor",
        ttl_hours=1,
        now=lambda: NOW,
        receipt_id="rail-approval-fixture",
    )
    registry.issue(receipt)

    try:
        registry.issue(receipt)
    except rail_approval.RailApprovalStoreError as exc:
        assert "already exists" in str(exc)
    else:  # pragma: no cover - this must never become an overwrite allow
        raise AssertionError("receipt registry allowed an issued receipt to be overwritten")
