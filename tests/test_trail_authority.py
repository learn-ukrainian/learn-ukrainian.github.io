"""P4 authority receipts: external re-fetch, state binding, and replay refusal."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts.orchestration.trails import authority as authority_module
from scripts.orchestration.trails.authority import (
    ApprovedAuthorityReceiptResolver,
    AuthorityReceiptError,
)
from scripts.orchestration.trails.executor import TrailExecutor, TrailPredicatesDecisionTableEvaluator
from scripts.orchestration.trails.models import CommandExecution, DeviationRefusedError, ExitClass
from scripts.orchestration.trails.store import TrailStore


def _trail(*, terminal: bool = False) -> dict[str, Any]:
    target = "done" if terminal else "STOP-unknown"
    return {
        "schema_version": "trailspec.v1.1",
        "trail_id": "authority-fixture",
        "version": "1.1.0",
        "title": "authority fixture",
        "seats": ["grok-daily"],
        "parameters": {},
        "stop_codes": ["STOP-unknown"],
        "terminal_outcomes": ["done"],
        "steps": [
            {
                "step_id": "start",
                "intent": "observe one token",
                "command": {
                    "adapter": "shell",
                    "argv": ["sh", "-c", "printf accepted"],
                    "environment": {"TRAIL_INVOCATION_ID": "{invocation_id}"},
                    "timeout_seconds": 30,
                    "mutation_class": "observe",
                    "outcome_decoder": {"source": "stdout-token"},
                },
                "transitions": {
                    "accepted": {
                        "target": target,
                        "evidence": {
                            "predicate_id": "accepted-outcome",
                            "clauses": [
                                {
                                    "source": "command_receipt",
                                    "field": "actor_outcome",
                                    "op": "eq",
                                    "value": "accepted",
                                }
                            ],
                        },
                    }
                },
            }
        ],
    }


def _write_trail(tmp_path: Path, trail: dict[str, Any]) -> Path:
    path = tmp_path / "authority.trail.yaml"
    path.write_text(yaml.safe_dump(trail, sort_keys=False), encoding="utf-8")
    return path


class _AuthoritySource:
    source_id = "fleet-api"
    source_kind = "api"

    def __init__(self, receipts: dict[str, dict[str, Any]]) -> None:
        self.receipts = receipts
        self.calls: list[str] = []

    def fetch_authority_receipt(self, receipt_id: str) -> dict[str, Any]:
        self.calls.append(receipt_id)
        return copy.deepcopy(self.receipts[receipt_id])


class _TypedFailingAuthoritySource(_AuthoritySource):
    def fetch_authority_receipt(self, receipt_id: str) -> dict[str, Any]:
        raise AuthorityReceiptError("authority source revoked this receipt")


class _LeaseObserver:
    def __init__(self) -> None:
        self.current: dict[str, Any] = {}

    def observe_lease(self, run) -> dict[str, Any]:
        return copy.deepcopy(self.current)


class _ResolverWithoutSourceIdentity:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def fetch(self, authority_receipt_id: str, run) -> dict[str, Any]:
        self.calls.append(authority_receipt_id)
        return {}


def _executor(
    tmp_path: Path,
    *,
    authority_resolver: ApprovedAuthorityReceiptResolver | None = None,
) -> TrailExecutor:
    seats = tmp_path / "fleet.yaml"
    seats.write_text(
        yaml.safe_dump({"endpoints": [{"name": "grok-daily", "state": "live"}]}),
        encoding="utf-8",
    )
    return TrailExecutor(
        TrailStore(tmp_path / "runs.sqlite3", tmp_path / "receipts"),
        project_root=tmp_path,
        seat_registry_path=seats,
        command_runner=lambda command, cwd: CommandExecution(0, "accepted", ""),
        authority_resolver=authority_resolver,
    )


def _begin_and_park(executor: TrailExecutor, tmp_path: Path) -> str:
    begun = executor.begin(
        trail_path=_write_trail(tmp_path, _trail()),
        seat="grok-daily",
        task_family="infra-orchestration",
        params={},
    )
    assert begun.run_id is not None
    parked = executor.step(run_id=begun.run_id, expected_step="start")
    assert parked.exit_class == ExitClass.STOP_PARKED
    return begun.run_id


def _receipt(executor: TrailExecutor, run_id: str) -> dict[str, Any]:
    run = executor.store.get_run(run_id)
    summon = executor.store.list_summons(run_id)[0]
    return {
        "schema_version": "trail-authority-receipt.v1",
        "receipt_id": "approval-1",
        "issuer": "operator-seat",
        "issued_at": "2026-07-28T00:00:00Z",
        "expires_at": "2030-07-28T00:00:00Z",
        "action": "resume",
        "run_id": run.run_id,
        "trail_id": run.trail_id,
        "trail_version": run.trail_version,
        "trail_hash": run.trail_hash,
        "summon_id": summon["summon_id"],
        "stop_code": summon["stop_code"],
        "step_id": run.cursor_step_id,
        "cursor_generation": run.cursor_generation,
        "lease_id": "lease-1",
        "lease_generation": 4,
        "fencing_token": "fence-4",
        "pr_head": None,
    }


def test_resume_refetches_and_consumes_one_state_bound_external_receipt(tmp_path: Path) -> None:
    lease = _LeaseObserver()
    source = _AuthoritySource({})
    resolver = ApprovedAuthorityReceiptResolver(
        source,
        lease,
        approved_issuers={"operator-seat"},
    )
    executor = _executor(tmp_path, authority_resolver=resolver)
    run_id = _begin_and_park(executor, tmp_path)
    receipt = _receipt(executor, run_id)
    source.receipts[receipt["receipt_id"]] = receipt
    lease.current = {
        "run_id": run_id,
        "step_id": "start",
        "lease_id": "lease-1",
        "lease_generation": 4,
        "fencing_token": "fence-4",
        "pr_head": None,
    }

    result = executor.resume(run_id=run_id, authority_receipt_id="approval-1")

    assert result.exit_class == ExitClass.STOP_PARKED
    assert result.outcome == "authority_verified_parked"
    assert source.calls == ["approval-1"]
    assert executor.store.get_run(run_id).state == "parked"
    assert executor.store.list_summons(run_id)[0]["authority_receipt_id"] == "approval-1"
    assert [row["receipt_id"] for row in executor.store.list_authority_receipts(run_id)] == [
        "approval-1"
    ]
    assert executor.store.list_authority_receipts(run_id)[0]["source_id"] == "fleet-api"

    replay = executor.resume(run_id=run_id, authority_receipt_id="approval-1")

    assert replay.exit_class == ExitClass.INVALID
    assert replay.outcome == "authority_receipt_refused"
    assert len(executor.store.list_authority_receipts(run_id)) == 1


def test_local_path_and_stale_lease_are_refused_without_consuming_a_summon(tmp_path: Path) -> None:
    lease = _LeaseObserver()
    source = _AuthoritySource({})
    resolver = ApprovedAuthorityReceiptResolver(
        source,
        lease,
        approved_issuers={"operator-seat"},
    )
    executor = _executor(tmp_path, authority_resolver=resolver)
    run_id = _begin_and_park(executor, tmp_path)
    before = executor.store.list_summons(run_id)
    local_receipt = tmp_path / "approval.json"
    local_receipt.write_text("{}", encoding="utf-8")

    local = executor.resume(run_id=run_id, authority_receipt_id=str(local_receipt))

    assert local.exit_class == ExitClass.INVALID
    assert local.outcome == "authority_receipt_refused"
    assert source.calls == []
    assert executor.store.list_summons(run_id) == before

    receipt = _receipt(executor, run_id)
    source.receipts[receipt["receipt_id"]] = receipt
    lease.current = {
        "run_id": run_id,
        "step_id": "start",
        "lease_id": "lease-1",
        "lease_generation": 3,
        "fencing_token": "fence-3",
        "pr_head": None,
    }

    stale = executor.resume(run_id=run_id, authority_receipt_id="approval-1")

    assert stale.exit_class == ExitClass.INVALID
    assert stale.outcome == "authority_receipt_refused"
    assert executor.store.list_summons(run_id) == before
    assert executor.store.list_authority_receipts(run_id) == []


def test_resume_refuses_a_resolver_without_stable_external_source_identity(tmp_path: Path) -> None:
    resolver = _ResolverWithoutSourceIdentity()
    executor = _executor(tmp_path, authority_resolver=resolver)  # type: ignore[arg-type]
    run_id = _begin_and_park(executor, tmp_path)

    result = executor.resume(run_id=run_id, authority_receipt_id="approval-1")

    assert result.exit_class == ExitClass.INVALID
    assert result.outcome == "authority_receipt_refused"
    assert result.error == "approved authority resolver lacks a stable external source_id"
    assert resolver.calls == []
    assert executor.store.list_authority_receipts(run_id) == []


def test_unapproved_issuer_is_a_mutation_honest_refusal(tmp_path: Path) -> None:
    lease = _LeaseObserver()
    source = _AuthoritySource({})
    resolver = ApprovedAuthorityReceiptResolver(
        source,
        lease,
        approved_issuers={"operator-seat"},
    )
    executor = _executor(tmp_path, authority_resolver=resolver)
    run_id = _begin_and_park(executor, tmp_path)
    receipt = _receipt(executor, run_id)
    receipt["issuer"] = "forged-local-issuer"
    source.receipts[receipt["receipt_id"]] = receipt
    lease.current = {
        "run_id": run_id,
        "step_id": "start",
        "lease_id": "lease-1",
        "lease_generation": 4,
        "fencing_token": "fence-4",
        "pr_head": None,
    }

    result = executor.resume(run_id=run_id, authority_receipt_id="approval-1")

    assert result.exit_class == ExitClass.INVALID
    assert result.outcome == "authority_receipt_refused"
    assert executor.store.get_run(run_id).state == "parked"
    assert executor.store.list_authority_receipts(run_id) == []


def test_authority_revalidation_preserves_typed_source_failure_detail(tmp_path: Path) -> None:
    source = _TypedFailingAuthoritySource({})
    resolver = ApprovedAuthorityReceiptResolver(
        source,
        _LeaseObserver(),
        approved_issuers={"operator-seat"},
    )
    executor = _executor(tmp_path, authority_resolver=resolver)
    run_id = _begin_and_park(executor, tmp_path)

    with pytest.raises(AuthorityReceiptError, match="authority source revoked this receipt"):
        resolver.revalidate(_receipt(executor, run_id))


def test_authority_schema_validator_loads_once_without_caching_receipt_payloads(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executor = _executor(tmp_path)
    run_id = _begin_and_park(executor, tmp_path)
    receipt = _receipt(executor, run_id)
    schema_path = authority_module.AUTHORITY_RECEIPT_SCHEMA_PATH

    class _CountingSchemaPath:
        reads = 0

        def read_text(self, *, encoding: str) -> str:
            self.reads += 1
            return schema_path.read_text(encoding=encoding)

    counter = _CountingSchemaPath()
    monkeypatch.setattr(authority_module, "AUTHORITY_RECEIPT_SCHEMA_PATH", counter)
    monkeypatch.setattr(authority_module, "_AUTHORITY_RECEIPT_VALIDATOR", None)

    assert authority_module.validate_authority_receipt_data(receipt) == receipt
    assert authority_module.validate_authority_receipt_data(receipt) == receipt
    assert counter.reads == 1


def test_executor_table_seam_parks_p2_unknown_without_running_a_command(tmp_path: Path) -> None:
    executor = _executor(tmp_path)
    begun = executor.begin(
        trail_path=_write_trail(tmp_path, _trail(terminal=True)),
        seat="grok-daily",
        task_family="infra-orchestration",
        params={},
    )
    assert begun.run_id is not None

    result = executor.evaluate_decision_table(
        run_id=begun.run_id,
        expected_step="start",
        table_id="queue-pick",
        facts={
            "is_foreign_lane": False,
            "has_sibling_pr": False,
            "queue_order_derivable": True,
            "dependencies_merged": False,
        },
    )

    assert result.exit_class == ExitClass.STOP_PARKED
    assert result.data == {"table_id": "queue-pick", "stop_code": "STOP-unknown"}
    assert executor.store.list_invocations(begun.run_id) == []
    assert len(executor.store.list_summons(begun.run_id)) == 1


def test_executor_table_stop_race_returns_typed_deviation_refusal(tmp_path: Path) -> None:
    executor = _executor(tmp_path)
    begun = executor.begin(
        trail_path=_write_trail(tmp_path, _trail(terminal=True)),
        seat="grok-daily",
        task_family="infra-orchestration",
        params={},
    )
    assert begun.run_id is not None

    def _raced_park_stop(**kwargs: Any) -> None:
        raise DeviationRefusedError("cursor changed before decision-table STOP parking")

    executor.store.park_stop = _raced_park_stop  # type: ignore[method-assign]
    result = executor.evaluate_decision_table(
        run_id=begun.run_id,
        expected_step="start",
        table_id="queue-pick",
        facts={
            "is_foreign_lane": False,
            "has_sibling_pr": False,
            "queue_order_derivable": True,
            "dependencies_merged": False,
        },
    )

    assert result.exit_class == ExitClass.DEVIATION_REFUSED
    assert result.outcome == "deviation_refused"
    assert result.state == "active"
    assert result.cursor_step == "start"


def test_decision_table_file_is_loaded_only_when_the_seam_is_used(tmp_path: Path) -> None:
    evaluator = TrailPredicatesDecisionTableEvaluator(tmp_path / "missing-decision-tables.yaml")

    assert evaluator.tables is None
    with pytest.raises(FileNotFoundError):
        evaluator.evaluate("queue-pick", {})
