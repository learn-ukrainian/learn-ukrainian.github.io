"""P4 closure: re-observe terminal state before the one SQLite closure commit."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from scripts.orchestration.trails import closure as closure_module
from scripts.orchestration.trails.closure import ClosureError, TrailClosureGate
from scripts.orchestration.trails.executor import TrailExecutor
from scripts.orchestration.trails.models import CommandExecution, ExitClass
from scripts.orchestration.trails.store import TrailStore


def _trail(*, pr_bound: bool = False) -> dict[str, Any]:
    return {
        "schema_version": "trailspec.v1.1",
        "trail_id": "closure-fixture",
        "version": "1.1.0",
        "title": "closure fixture",
        "seats": ["grok-daily"],
        "parameters": {"pr_head": "string"} if pr_bound else {},
        "stop_codes": ["STOP-unknown"],
        "terminal_outcomes": ["done"],
        "steps": [
            {
                "step_id": "observe-terminal",
                "intent": "terminal re-observation",
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
                        "target": "done",
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


class _TerminalSource:
    source_id = "fleet-bridge"
    source_kind = "bridge"

    def __init__(self, *, lease_current: bool = True, pr_head: str | None = None) -> None:
        self.lease_current = lease_current
        self.pr_head = pr_head
        self.calls = 0

    def reobserve_terminal(
        self,
        *,
        run,
        terminal_command_receipt: dict[str, Any],
        terminal_step_receipt: dict[str, Any],
    ) -> dict[str, Any]:
        self.calls += 1
        return {
            "observation_id": "observe-1",
            "observed_at": "2026-07-28T00:00:00Z",
            "run_id": run.run_id,
            "trail_id": run.trail_id,
            "trail_hash": run.trail_hash,
            "terminal_outcome": run.terminal_outcome,
            "lease_id": "lease-1",
            "lease_generation": 4,
            "fencing_token": "fence-4",
            "pr_head": self.pr_head,
            "lease_current": self.lease_current,
            "terminal_observed": True,
        }


class _CommitThenFailGate(TrailClosureGate):
    """Simulate a second closer committing while this closer loses its response."""

    def close(self, **kwargs):
        super().close(**kwargs)
        raise ClosureError("this closer lost the concurrent commit response")


class _TypedFailingTerminalSource(_TerminalSource):
    def reobserve_terminal(
        self,
        *,
        run,
        terminal_command_receipt: dict[str, Any],
        terminal_step_receipt: dict[str, Any],
    ) -> dict[str, Any]:
        raise ClosureError("terminal bridge revoked the observation")


def _executor(tmp_path: Path, source: _TerminalSource) -> TrailExecutor:
    tmp_path.mkdir(parents=True, exist_ok=True)
    seats = tmp_path / "fleet.yaml"
    seats.write_text(
        yaml.safe_dump({"endpoints": [{"name": "grok-daily", "state": "live"}]}),
        encoding="utf-8",
    )
    store = TrailStore(tmp_path / "runs.sqlite3", tmp_path / "receipts")
    return TrailExecutor(
        store,
        project_root=tmp_path,
        seat_registry_path=seats,
        command_runner=lambda command, cwd: CommandExecution(0, "accepted", ""),
        closure_gate=TrailClosureGate(store, source),
    )


def _terminal_run(
    executor: TrailExecutor,
    tmp_path: Path,
    *,
    pr_head: str | None = None,
) -> str:
    trail_path = tmp_path / "closure.trail.yaml"
    trail_path.write_text(
        yaml.safe_dump(_trail(pr_bound=pr_head is not None), sort_keys=False),
        encoding="utf-8",
    )
    begun = executor.begin(
        trail_path=trail_path,
        seat="grok-daily",
        task_family="infra-orchestration",
        params={"pr_head": pr_head} if pr_head is not None else {},
    )
    assert begun.run_id is not None
    terminal = executor.step(run_id=begun.run_id, expected_step="observe-terminal")
    assert terminal.outcome == "terminal"
    return begun.run_id


def test_close_commits_once_and_terminal_replay_does_not_reobserve(tmp_path: Path) -> None:
    source = _TerminalSource()
    executor = _executor(tmp_path, source)
    run_id = _terminal_run(executor, tmp_path)

    first = executor.close(run_id=run_id)
    replay = executor.close(run_id=run_id)

    assert first.exit_class == ExitClass.OK
    assert first.outcome == "closed"
    assert replay.to_dict() == first.to_dict()
    assert source.calls == 1
    assert executor.store.get_run(run_id).closure_state == "closed"
    assert executor.store.get_closure(run_id) is not None
    assert executor.store.projection_path(run_id=run_id, filename="closure.json").is_file()


def test_stale_lease_parks_closure_atomically_without_changing_terminal_state(tmp_path: Path) -> None:
    source = _TerminalSource(lease_current=False)
    executor = _executor(tmp_path, source)
    run_id = _terminal_run(executor, tmp_path)

    result = executor.close(run_id=run_id)

    run = executor.store.get_run(run_id)
    assert result.exit_class == ExitClass.STOP_PARKED
    assert result.outcome == "closure_parked"
    assert run.state == "terminal"
    assert run.closure_state == "parked"
    summons = executor.store.list_summons(run_id)
    assert len(summons) == 1
    assert summons[0]["state"] == "closure"
    assert executor.store.get_closure(run_id) is None

    source.lease_current = True
    retried = executor.close(run_id=run_id)

    assert retried.exit_class == ExitClass.OK
    assert executor.store.get_run(run_id).closure_state == "closed"
    assert source.calls == 2


def test_closure_preserves_a_typed_terminal_source_failure_detail(tmp_path: Path) -> None:
    source = _TypedFailingTerminalSource()
    executor = _executor(tmp_path, source)
    run_id = _terminal_run(executor, tmp_path)

    result = executor.close(run_id=run_id)

    assert result.exit_class == ExitClass.STOP_PARKED
    assert result.error == "terminal bridge revoked the observation"
    assert executor.store.get_run(run_id).closure_state == "parked"


def test_closure_schema_validator_loads_once_without_caching_attestations(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = _TerminalSource()
    executor = _executor(tmp_path, source)
    run_id = _terminal_run(executor, tmp_path)
    attestation = executor.close(run_id=run_id).data["attestation"]
    schema_path = closure_module.CLOSURE_ATTESTATION_SCHEMA_PATH

    class _CountingSchemaPath:
        reads = 0

        def read_text(self, *, encoding: str) -> str:
            self.reads += 1
            return schema_path.read_text(encoding=encoding)

    counter = _CountingSchemaPath()
    monkeypatch.setattr(closure_module, "CLOSURE_ATTESTATION_SCHEMA_PATH", counter)
    monkeypatch.setattr(closure_module, "_CLOSURE_ATTESTATION_VALIDATOR", None)

    assert closure_module.validate_closure_attestation_data(attestation) == attestation
    assert closure_module.validate_closure_attestation_data(attestation) == attestation
    assert counter.reads == 1


def test_stale_head_and_incomplete_projection_refuse_with_terminal_closure_parking(
    tmp_path: Path,
) -> None:
    fresh_source = _TerminalSource(pr_head="a" * 40)
    fresh_executor = _executor(tmp_path / "fresh", fresh_source)
    fresh_run_id = _terminal_run(fresh_executor, tmp_path / "fresh", pr_head="a" * 40)

    fresh = fresh_executor.close(run_id=fresh_run_id)

    assert fresh.exit_class == ExitClass.OK
    assert fresh.data["attestation"]["pr_head"] == "a" * 40

    head_source = _TerminalSource(pr_head="b" * 40)
    head_executor = _executor(tmp_path / "head", head_source)
    head_run_id = _terminal_run(head_executor, tmp_path / "head", pr_head="a" * 40)

    stale_head = head_executor.close(run_id=head_run_id)

    assert stale_head.exit_class == ExitClass.STOP_PARKED
    assert head_executor.store.get_run(head_run_id).closure_state == "parked"

    chain_source = _TerminalSource()
    chain_executor = _executor(tmp_path / "chain", chain_source)
    chain_run_id = _terminal_run(chain_executor, tmp_path / "chain")
    invocation = chain_executor.store.list_invocations(chain_run_id)[0]
    command_path = chain_executor.store.projection_path(
        run_id=chain_run_id,
        filename=f"command-000000-{invocation['invocation_id']}.json",
    )
    command_path.write_text("{}\n", encoding="utf-8")

    incomplete = chain_executor.close(run_id=chain_run_id)

    assert incomplete.exit_class == ExitClass.STOP_PARKED
    assert incomplete.outcome == "closure_parked"
    assert chain_source.calls == 0
    assert chain_executor.store.get_run(chain_run_id).state == "terminal"
    assert chain_executor.store.get_run(chain_run_id).closure_state == "parked"


def test_projection_failure_after_commit_keeps_closed_result_and_retries_later(tmp_path: Path) -> None:
    source = _TerminalSource()
    executor = _executor(tmp_path, source)
    run_id = _terminal_run(executor, tmp_path)
    projection = executor.store.projection_path(run_id=run_id, filename="closure.json")
    projection.parent.mkdir(parents=True, exist_ok=True)
    projection.write_text("{}\n", encoding="utf-8")

    committed = executor.close(run_id=run_id)

    assert committed.exit_class == ExitClass.OK
    assert committed.outcome == "closed"
    assert committed.error is not None
    assert executor.store.get_run(run_id).closure_state == "closed"
    assert source.calls == 1

    projection.unlink()
    replay = executor.close(run_id=run_id)

    assert replay.exit_class == ExitClass.OK
    assert replay.error is None
    assert source.calls == 1
    assert projection.is_file()


def test_concurrent_committed_closure_is_reported_as_closed_not_refused(tmp_path: Path) -> None:
    source = _TerminalSource()
    executor = _executor(tmp_path, source)
    executor.closure_gate = _CommitThenFailGate(executor.store, source)
    run_id = _terminal_run(executor, tmp_path)

    result = executor.close(run_id=run_id)

    assert result.exit_class == ExitClass.OK
    assert result.outcome == "closed"
    assert executor.store.get_run(run_id).closure_state == "closed"
    assert executor.store.get_closure(run_id) is not None
    assert executor.store.projection_path(run_id=run_id, filename="closure.json").is_file()
