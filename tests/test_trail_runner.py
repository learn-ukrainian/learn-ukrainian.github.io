"""Regression tests for the P3 SQLite TrailSpec runner ledger and executor."""

from __future__ import annotations

import hashlib
import json
import threading
import uuid
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

from scripts.orchestration.trail_runner import main as trail_runner_main
from scripts.orchestration.trails.executor import TrailExecutor, redact_and_bound_output
from scripts.orchestration.trails.models import (
    CommandExecution,
    ExitClass,
    InjectedCrash,
    TrailRunResult,
)
from scripts.orchestration.trails.store import TrailStore


def _trail(
    *,
    command: dict | None = None,
    transitions: dict | None = None,
    blocked_on: dict | None = None,
    schema_version: str = "trailspec.v1.1",
) -> dict:
    if schema_version == "trailspec.v1":
        return {
            "schema_version": "trailspec.v1",
            "trail_id": "legacy-runner-fixture",
            "version": "1.0.0",
            "title": "legacy fixture",
            "seats": ["grok-daily"],
            "stop_codes": ["STOP-unknown"],
            "terminal_outcomes": ["done"],
            "steps": [
                {
                    "step_id": "inspect",
                    "intent": "inspection only",
                    "command": None,
                    "evidence_predicate": None,
                    "transitions": {"inspected": "done"},
                    "kind": "summon",
                }
            ],
        }
    return {
        "schema_version": "trailspec.v1.1",
        "trail_id": "runner-fixture",
        "version": "1.1.0",
        "title": "runner fixture",
        "seats": ["grok-daily"],
        "parameters": {},
        "stop_codes": ["STOP-unknown"],
        "terminal_outcomes": ["done"],
        "steps": [
            {
                "step_id": "start",
                "intent": "run one bounded command",
                "command": command
                or {
                    "adapter": "shell",
                    "argv": ["sh", "-c", "printf accepted"],
                    "environment": {"TRAIL_INVOCATION_ID": "{invocation_id}"},
                    "timeout_seconds": 30,
                    "mutation_class": "observe",
                    "outcome_decoder": {"source": "stdout-token"},
                },
                "transitions": transitions
                or {
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
                                },
                                {
                                    "source": "command_receipt",
                                    "field": "exit_code",
                                    "op": "eq",
                                    "value": 0,
                                },
                            ],
                        },
                    }
                },
                "blocked_on": blocked_on,
            }
        ],
    }


def _write_trail(tmp_path: Path, payload: dict) -> Path:
    path = tmp_path / "runner.trail.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def _executor(tmp_path: Path, **kwargs) -> TrailExecutor:
    seat_registry = tmp_path / "fleet.yaml"
    seat_registry.write_text(
        yaml.safe_dump({"endpoints": [{"name": "grok-daily", "state": "live"}]}),
        encoding="utf-8",
    )
    store = TrailStore(tmp_path / "runs.sqlite3", tmp_path / "receipts")
    return TrailExecutor(
        store,
        project_root=tmp_path,
        seat_registry_path=seat_registry,
        **kwargs,
    )


def _begin(executor: TrailExecutor, path: Path) -> str:
    result = executor.begin(
        trail_path=path,
        seat="grok-daily",
        task_family="infra-orchestration",
        params={},
    )
    assert result.exit_class == ExitClass.OK
    assert result.run_id is not None
    return result.run_id


def test_step_pre_records_uuid_and_binds_invocation_environment(tmp_path: Path) -> None:
    observed: list[tuple[str, str, str]] = []
    executor: TrailExecutor

    def runner(command: dict, cwd: Path) -> CommandExecution:
        invocations = executor.store.list_invocations(run_id)
        assert len(invocations) == 1
        invocation = invocations[0]
        uuid.UUID(invocation["invocation_id"])
        assert invocation["status"] == "prepared"
        observed.append(
            (
                invocation["invocation_id"],
                command["environment"]["TRAIL_INVOCATION_ID"],
                command["argv"][-1],
            )
        )
        return CommandExecution(exit_code=0, stdout="accepted", stderr="")

    typed_command = {
        "adapter": "typed-primitive",
        "argv": ["trail-primitive", "observe", "--invocation-id", "{invocation_id}"],
        "environment": {"TRAIL_INVOCATION_ID": "{invocation_id}"},
        "timeout_seconds": 30,
        "mutation_class": "observe",
        "outcome_decoder": {"source": "stdout-token"},
    }
    executor = _executor(tmp_path, command_runner=runner)
    run_id = _begin(executor, _write_trail(tmp_path, _trail(command=typed_command)))

    result = executor.step(run_id=run_id, expected_step="start")

    assert result.exit_class == ExitClass.OK
    assert result.outcome == "terminal"
    assert observed[0][0] == observed[0][1] == observed[0][2]
    assert executor.verify_chain(run_id=run_id).exit_class == ExitClass.OK


def test_step_refuses_skipped_repeated_or_invented_cursor_without_movement(tmp_path: Path) -> None:
    executor = _executor(tmp_path)
    run_id = _begin(executor, _write_trail(tmp_path, _trail()))

    refused = executor.step(run_id=run_id, expected_step="invented")
    status = executor.status(run_id=run_id)

    assert refused.exit_class == ExitClass.DEVIATION_REFUSED
    assert status.cursor_step == "start"
    assert executor.store.list_invocations(run_id) == []


def test_nonterminal_transition_advances_cursor_and_chain(tmp_path: Path) -> None:
    payload = _trail()
    payload["steps"][0]["transitions"]["accepted"]["target"] = "finish"
    finish = json.loads(json.dumps(payload["steps"][0]))
    finish["step_id"] = "finish"
    finish["intent"] = "terminal re-observation"
    finish["transitions"]["accepted"]["target"] = "done"
    payload["steps"].append(finish)
    executor = _executor(
        tmp_path,
        command_runner=lambda command, cwd: CommandExecution(0, "accepted", ""),
    )
    run_id = _begin(executor, _write_trail(tmp_path, payload))

    advanced = executor.step(run_id=run_id, expected_step="start")
    terminal = executor.step(run_id=run_id, expected_step="finish")

    assert advanced.exit_class == ExitClass.OK
    assert advanced.outcome == "advanced"
    assert advanced.cursor_step == "finish"
    assert terminal.outcome == "terminal"
    assert executor.verify_chain(run_id=run_id).exit_class == ExitClass.OK


def test_duplicate_explicit_idempotency_key_returns_prior_result_without_reexecution(
    tmp_path: Path,
) -> None:
    calls = 0

    def runner(command: dict, cwd: Path) -> CommandExecution:
        nonlocal calls
        calls += 1
        return CommandExecution(exit_code=0, stdout="accepted", stderr="")

    executor = _executor(tmp_path, command_runner=runner)
    run_id = _begin(executor, _write_trail(tmp_path, _trail()))

    first = executor.step(run_id=run_id, expected_step="start", idempotency_key="client-key")
    replay = executor.step(run_id=run_id, expected_step="start", idempotency_key="client-key")

    assert first.to_dict() == replay.to_dict()
    assert calls == 1


@pytest.mark.parametrize("window", ["before-spawn", "after-spawn", "after-side-effect"])
def test_crash_windows_park_indeterminate_and_never_replay(
    tmp_path: Path, window: str
) -> None:
    calls = 0
    effect = tmp_path / f"{window}.effect"

    def runner(command: dict, cwd: Path) -> CommandExecution:
        nonlocal calls
        calls += 1
        if window == "after-spawn":
            raise InjectedCrash("simulated crash after spawn")
        if window == "after-side-effect":
            effect.write_text("side effect occurred", encoding="utf-8")
            raise InjectedCrash("simulated crash after side effect")
        return CommandExecution(exit_code=0, stdout="accepted", stderr="")

    def fault_hook(stage: str, prepared) -> None:
        if window == "before-spawn" and stage == "after_prepared_before_spawn":
            raise InjectedCrash("simulated crash before spawn")

    executor = _executor(tmp_path, command_runner=runner, fault_hook=fault_hook)
    run_id = _begin(executor, _write_trail(tmp_path, _trail()))

    with pytest.raises(InjectedCrash):
        executor.step(run_id=run_id, expected_step="start")
    resumed_process = _executor(tmp_path, command_runner=runner)
    result = resumed_process.step(run_id=run_id, expected_step="start")

    assert result.exit_class == ExitClass.INDETERMINATE
    assert resumed_process.status(run_id=run_id).state == "parked"
    assert calls == (0 if window == "before-spawn" else 1)
    assert effect.exists() is (window == "after-side-effect")


def test_timeout_receipt_can_take_an_explicit_timeout_transition(tmp_path: Path) -> None:
    timeout_transition = {
        "timed_out": {
            "target": "done",
            "evidence": {
                "predicate_id": "timed-out",
                "clauses": [
                    {
                        "source": "command_receipt",
                        "field": "actor_outcome",
                        "op": "eq",
                        "value": "timeout",
                    },
                    {
                        "source": "command_receipt",
                        "field": "exit_code",
                        "op": "eq",
                        "value": 124,
                    },
                ],
            },
        }
    }
    executor = _executor(
        tmp_path,
        command_runner=lambda command, cwd: CommandExecution(
            exit_code=124, stdout="", stderr="timed out", timed_out=True
        ),
    )
    run_id = _begin(executor, _write_trail(tmp_path, _trail(transitions=timeout_transition)))

    result = executor.step(run_id=run_id, expected_step="start")

    assert result.exit_class == ExitClass.OK
    receipt = executor.store.list_invocations(run_id)[0]["command_receipt"]
    assert receipt["exit_code"] == 124
    assert receipt["actor_outcome"] == "timeout"


def test_receipt_output_is_bounded_redacted_and_never_stores_raw_secret(tmp_path: Path) -> None:
    secret = "top-secret-not-in-receipt"
    executor = _executor(
        tmp_path,
        command_runner=lambda command, cwd: CommandExecution(
            exit_code=0,
            stdout="accepted",
            stderr=f"Authorization: Bearer {secret}",
        ),
    )
    run_id = _begin(executor, _write_trail(tmp_path, _trail()))

    assert executor.step(run_id=run_id, expected_step="start").exit_class == ExitClass.OK
    receipt = executor.store.list_invocations(run_id)[0]["command_receipt"]

    assert secret not in json.dumps(receipt)
    assert receipt["stderr_digest"] == hashlib.sha256(
        redact_and_bound_output(f"Authorization: Bearer {secret}").encode("utf-8")
    ).hexdigest()


@pytest.mark.parametrize("multiple", [False, True])
def test_zero_and_multiple_predicate_matches_park_stop_unknown(
    tmp_path: Path, multiple: bool
) -> None:
    transitions = {
        "accepted_one": {
            "target": "done",
            "evidence": {
                "predicate_id": "accepted-one",
                "clauses": [
                    {
                        "source": "command_receipt",
                        "field": "actor_outcome",
                        "op": "eq",
                        "value": "accepted" if multiple else "not-accepted",
                    }
                ],
            },
        }
    }
    if multiple:
        transitions["accepted_two"] = {
            "target": "done",
            "evidence": {
                "predicate_id": "accepted-two",
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
    executor = _executor(
        tmp_path,
        command_runner=lambda command, cwd: CommandExecution(0, "accepted", ""),
    )
    run_id = _begin(executor, _write_trail(tmp_path, _trail(transitions=transitions)))

    result = executor.step(run_id=run_id, expected_step="start")

    assert result.exit_class == ExitClass.STOP_PARKED
    assert result.data["stop_code"] == "STOP-unknown"
    assert len(executor.store.list_summons(run_id)) == 1


def test_blocked_step_atomically_parks_and_creates_summon(tmp_path: Path) -> None:
    blocked_on = {
        "id": "operator-approval",
        "reason": "approval is required",
        "stop_code": "STOP-unknown",
    }
    executor = _executor(tmp_path)
    run_id = _begin(executor, _write_trail(tmp_path, _trail(blocked_on=blocked_on)))

    result = executor.step(run_id=run_id, expected_step="start")
    summons = executor.store.list_summons(run_id)

    assert result.exit_class == ExitClass.BLOCKED_PARKED
    assert result.state == "parked"
    assert len(summons) == 1
    assert summons[0]["state"] == "blocked"


def test_v1_is_inspection_only_and_execution_or_closure_is_refused(tmp_path: Path) -> None:
    executor = _executor(tmp_path)
    run_id = _begin(executor, _write_trail(tmp_path, _trail(schema_version="trailspec.v1")))

    step = executor.step(run_id=run_id, expected_step="inspect")
    close = executor.close(run_id=run_id)

    assert executor.status(run_id=run_id).state == "inspection"
    assert step.exit_class == ExitClass.INVALID
    assert close.exit_class == ExitClass.INVALID
    assert executor.verify_chain(run_id=run_id).exit_class == ExitClass.OK


def test_resume_refuses_raw_local_json_authority_receipt(tmp_path: Path) -> None:
    executor = _executor(tmp_path)
    run_id = _begin(executor, _write_trail(tmp_path, _trail()))
    local_receipt = tmp_path / "approval.json"
    local_receipt.write_text("{}", encoding="utf-8")

    result = executor.resume(run_id=run_id, authority_receipt_id=str(local_receipt))

    assert result.exit_class == ExitClass.INVALID
    assert result.outcome == "authority_receipt_refused"


def test_verify_chain_detects_tampered_projection(tmp_path: Path) -> None:
    executor = _executor(tmp_path)
    run_id = _begin(executor, _write_trail(tmp_path, _trail()))
    assert executor.step(run_id=run_id, expected_step="start").exit_class == ExitClass.OK
    invocation = executor.store.list_invocations(run_id)[0]
    receipt_path = executor.store.projection_path(
        run_id=run_id,
        filename=f"command-000000-{invocation['invocation_id']}.json",
    )
    receipt_path.write_text("{}\n", encoding="utf-8")

    result = executor.verify_chain(run_id=run_id)

    assert result.exit_class == ExitClass.INVALID
    assert result.outcome == "chain_invalid"


def test_cli_emits_one_schema_valid_json_object_and_exit_classes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    trail_path = _write_trail(tmp_path, _trail())
    params_path = tmp_path / "params.json"
    params_path.write_text("{}", encoding="utf-8")
    executor = _executor(tmp_path)

    exit_code = trail_runner_main(
        [
            "begin",
            "--trail",
            str(trail_path),
            "--seat",
            "grok-daily",
            "--task-family",
            "infra-orchestration",
            "--params",
            str(params_path),
        ],
        executor=executor,
    )
    output_lines = capsys.readouterr().out.splitlines()
    schema = json.loads(
        (Path(__file__).parents[1] / "agents_extensions/shared/schemas/trail-run-result.v1.schema.json").read_text(
            encoding="utf-8"
        )
    )

    assert exit_code == 0
    assert len(output_lines) == 1
    Draft202012Validator(schema).validate(json.loads(output_lines[0]))


def test_cli_verbs_keep_the_exit_class_and_one_object_contract(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    trail_path = _write_trail(tmp_path, _trail())
    params_path = tmp_path / "params.json"
    params_path.write_text("{}", encoding="utf-8")
    executor = _executor(tmp_path)
    begin_args = [
        "begin",
        "--trail",
        str(trail_path),
        "--seat",
        "grok-daily",
        "--task-family",
        "infra-orchestration",
        "--params",
        str(params_path),
    ]
    assert trail_runner_main(begin_args, executor=executor) == ExitClass.OK
    run_id = json.loads(capsys.readouterr().out)["run_id"]

    cases = [
        (["status", "--run-id", run_id], ExitClass.OK),
        (["step", "--run-id", run_id, "--expected-step", "start"], ExitClass.OK),
        (["verify-chain", "--run-id", run_id], ExitClass.OK),
        (["resume", "--run-id", run_id, "--authority-receipt-id", "approval-1"], ExitClass.INVALID),
        (["close", "--run-id", run_id], ExitClass.INVALID),
    ]
    for argv, expected_exit in cases:
        assert trail_runner_main(argv, executor=executor) == expected_exit
        lines = capsys.readouterr().out.splitlines()
        assert len(lines) == 1
        payload = json.loads(lines[0])
        assert payload["exit_class"] == expected_exit


def test_cursor_race_stops_second_claimant_without_a_second_command(tmp_path: Path) -> None:
    command_started = threading.Event()
    allow_first_to_finish = threading.Event()
    calls = 0

    def runner(command: dict, cwd: Path) -> CommandExecution:
        nonlocal calls
        calls += 1
        command_started.set()
        assert allow_first_to_finish.wait(timeout=5)
        return CommandExecution(0, "accepted", "")

    executor = _executor(tmp_path, command_runner=runner)
    run_id = _begin(executor, _write_trail(tmp_path, _trail()))
    first_result: list[TrailRunResult] = []

    def first_claimant() -> None:
        first_result.append(executor.step(run_id=run_id, expected_step="start"))

    thread = threading.Thread(target=first_claimant)
    thread.start()
    assert command_started.wait(timeout=5)
    second = executor.step(run_id=run_id, expected_step="start")
    allow_first_to_finish.set()
    thread.join(timeout=5)

    assert second.exit_class == ExitClass.INDETERMINATE
    assert calls == 1
    assert executor.status(run_id=run_id).state == "parked"
    assert first_result
    assert first_result[0].exit_class == ExitClass.INDETERMINATE
