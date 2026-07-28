"""Mutation-honest tests for layered rail-path authorization (P6 / #5885)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

from scripts.orchestration import rail_path_guard as guard

NOW = datetime(2026, 7, 28, tzinfo=UTC)
HEAD = "a" * 40
OTHER_HEAD = "b" * 40
TASK = "rail-p6-path-guard"
OWNED_RAIL_PATH = "agents_extensions/shared/hooks/guard-pr-merge.py"


class _ReceiptStore:
    source_id = "operator-approval-api"
    source_kind = "api"

    def __init__(self, receipts: dict[str, dict]) -> None:
        self.receipts = receipts

    def fetch_rail_approval_receipt(self, receipt_id: str) -> dict:
        return self.receipts[receipt_id]


class _UnreadableReceiptStore(_ReceiptStore):
    def fetch_rail_approval_receipt(self, receipt_id: str) -> dict:
        raise OSError("approval store unavailable")


class _LocalFileReceiptStore(_ReceiptStore):
    source_kind = "file"


def _receipt(**overrides: object) -> dict:
    receipt = {
        "schema_version": "rail-approval-receipt.v1",
        "receipt_id": "rail-approval-1",
        "issuer": "operator",
        "issued_at": "2026-07-28T00:00:00Z",
        "expires_at": "2026-07-29T00:00:00Z",
        "action": "rail-path-mutation",
        "task_id": TASK,
        "head_sha": HEAD,
        "owned_paths": [OWNED_RAIL_PATH],
    }
    receipt.update(overrides)
    return receipt


def _verified(**overrides: object) -> guard.VerifiedRailApprovalReceipt:
    receipt = _receipt(**overrides)
    resolver = guard.ApprovedRailApprovalReceiptResolver(
        _ReceiptStore({receipt["receipt_id"]: receipt}), now=lambda: NOW
    )
    return resolver.fetch(str(receipt["receipt_id"]))


def _decide(*paths: str, receipt: guard.VerifiedRailApprovalReceipt | None = None, **kwargs):
    return guard.decide_rail_path_mutation(
        task_id=kwargs.pop("task_id", TASK),
        candidate_paths=paths,
        head_sha=kwargs.pop("head_sha", HEAD),
        receipt=receipt,
        now=lambda: NOW,
        **kwargs,
    )


def test_rail_patterns_are_full_path_globs_not_substrings() -> None:
    assert guard.is_rail_path("agents_extensions/shared/rules/model-assignment.md")
    assert guard.is_rail_path("agents_extensions/codex/agents/infra.md")
    assert guard.is_rail_path("scripts/config/trails/rb1.trail.yaml")
    assert guard.is_rail_path("agents_extensions/shared/schemas/trailspec/v2/schema.json")
    assert not guard.is_rail_path("docs/model_catalog.yaml-not-a-rail")
    assert not guard.is_rail_path("docs/notes/agents_extensions/shared/rules.md")


def test_non_rail_paths_are_unaffected_without_receipt() -> None:
    decision = _decide(
        "docs/projects/fleet-trails/rail-system-completion-memo.md",
        task_id="",
        head_sha="not-a-commit",
    )

    assert decision.allowed is True
    assert decision.reason == "non_rail_paths"
    assert decision.rail_paths == ()


def test_rail_path_without_receipt_is_refused() -> None:
    decision = _decide(OWNED_RAIL_PATH)

    assert decision.allowed is False
    assert decision.reason == "rail_approval_receipt_required"
    assert decision.rail_paths == (OWNED_RAIL_PATH,)


def test_valid_receipt_admits_exact_owned_rail_path_and_not_more() -> None:
    receipt = _verified()

    allowed = _decide(OWNED_RAIL_PATH, receipt=receipt)
    extra = _decide("agents_extensions/shared/hooks/guard-admin-merge.py", receipt=receipt)

    assert allowed.allowed is True
    assert allowed.reason == "rail_approval_verified"
    assert extra.allowed is False
    assert extra.reason == "rail_approval_path_mismatch"


@pytest.mark.parametrize(
    "overrides, kwargs, reason",
    [
        ({}, {"task_id": "other-task"}, "rail_approval_task_mismatch"),
        ({}, {"head_sha": OTHER_HEAD}, "rail_approval_head_mismatch"),
    ],
)
def test_bound_receipt_mismatches_are_refused(overrides, kwargs, reason) -> None:
    receipt = _verified(**overrides)

    decision = _decide(OWNED_RAIL_PATH, receipt=receipt, **kwargs)

    assert decision.allowed is False
    assert decision.reason == reason


def test_expired_receipt_is_refused_by_external_resolver() -> None:
    expired = _receipt(
        issued_at="2026-07-27T00:00:00Z",
        expires_at="2026-07-28T00:00:00Z",
    )
    resolver = guard.ApprovedRailApprovalReceiptResolver(
        _ReceiptStore({"rail-approval-1": expired}), now=lambda: NOW
    )

    with pytest.raises(guard.RailApprovalReceiptError, match="has expired"):
        resolver.fetch("rail-approval-1")


def test_forged_or_local_receipts_are_refused_before_decision() -> None:
    forged = _receipt(issuer="self-declared-model-tier")
    with pytest.raises(guard.RailApprovalReceiptError, match="schema violation"):
        guard.ApprovedRailApprovalReceiptResolver(
            _ReceiptStore({"rail-approval-1": forged}), now=lambda: NOW
        ).fetch("rail-approval-1")

    with pytest.raises(guard.RailApprovalReceiptError, match="bridge or API"):
        guard.ApprovedRailApprovalReceiptResolver(_LocalFileReceiptStore({}), now=lambda: NOW)


def test_unreadable_receipt_store_fails_closed() -> None:
    resolver = guard.ApprovedRailApprovalReceiptResolver(
        _UnreadableReceiptStore({}), now=lambda: NOW
    )

    with pytest.raises(guard.RailApprovalReceiptError, match="could not re-fetch"):
        resolver.fetch("rail-approval-1")


@pytest.mark.parametrize(
    "bypass_claim",
    [
        {"X-Agent": "codex/rail-p6-path-guard"},
        {"model": "gpt-5.6-sol"},
        {"self_declared_tier": "advisor"},
    ],
)
def test_identity_strings_never_bypass_rail_receipt(bypass_claim: dict[str, str]) -> None:
    # A caller can label itself anything it wants. The versioned schema refuses
    # these claims, and the decision API does not accept identity as authority.
    forged = _receipt(**bypass_claim)
    resolver = guard.ApprovedRailApprovalReceiptResolver(
        _ReceiptStore({"rail-approval-1": forged}), now=lambda: NOW
    )

    with pytest.raises(guard.RailApprovalReceiptError, match="schema violation"):
        resolver.fetch("rail-approval-1")


def test_missing_rail_classifier_mutation_is_observable(monkeypatch: pytest.MonkeyPatch) -> None:
    """If the deny-list call is removed, this test turns red rather than passing vacuously."""
    assert _decide(OWNED_RAIL_PATH).allowed is False

    monkeypatch.setattr(guard, "is_rail_path", lambda _path: False)

    assert _decide(OWNED_RAIL_PATH).allowed is True


def test_missing_receipt_binding_mutation_is_observable(monkeypatch: pytest.MonkeyPatch) -> None:
    """If task/head/path binding is removed, this test exposes the newly allowed write."""
    receipt = _verified()
    assert _decide(OWNED_RAIL_PATH, receipt=receipt, task_id="other-task").allowed is False

    monkeypatch.setattr(guard, "_receipt_authorizes", lambda _receipt, **_kwargs: None)

    assert _decide(OWNED_RAIL_PATH, receipt=receipt, task_id="other-task").allowed is True


def test_ci_gate_requires_the_shared_rail_path_module() -> None:
    """Removing the CI job/wiring makes this rail-layer contract test fail."""
    workflow_path = Path(__file__).resolve().parents[1] / ".github/workflows/ci.yml"
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    rail_job = workflow["jobs"]["rail-path"]
    run_steps = "\n".join(
        str(step.get("run", "")) for step in rail_job["steps"] if isinstance(step, dict)
    )

    assert "scripts.orchestration.rail_path_guard" in run_steps
    assert "rail-path" in workflow["jobs"]["ci-gate"]["needs"]
