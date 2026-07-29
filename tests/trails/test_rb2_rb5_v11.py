"""Contract tests for the RB-2/RB-5 TrailSpec v1.1 migrations."""

from __future__ import annotations

import copy
import os
import re
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts.orchestration.trails.closure import TrailClosureGate
from scripts.orchestration.trails.executor import DefaultReceiptPredicateEvaluator, TrailExecutor
from scripts.orchestration.trails.models import CommandExecution, ExitClass
from scripts.orchestration.trails.store import TrailStore
from scripts.orchestration.validate_trailspec import PROJECT_ROOT, validate_trailspec

RB2_PATH = PROJECT_ROOT / "scripts/config/trails/rb2-dispatch-loop.trail.yaml"
RB5_PATH = PROJECT_ROOT / "scripts/config/trails/rb5-session-close.trail.yaml"

# Mirrors scripts.delegate._RUNTIME_TMP_TERMINAL_STATUSES, the dispatch task-status vocabulary.
DELEGATE_TERMINAL_STATUSES = {
    "done",
    "timeout",
    "needs_finalize",
    "no_deliverable",
    "failed",
    "crashed",
    "rate_limited",
    "cancelled",
    "dry_run",
}


def _load(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _commands(spec: dict[str, Any]) -> list[dict[str, Any]]:
    return [step["command"] for step in spec["steps"]]


@pytest.mark.parametrize(
    ("path", "trail_id", "steps"),
    [(RB2_PATH, "rb2-dispatch-loop", 24), (RB5_PATH, "rb5-session-close", 18)],
)
def test_migrated_trails_validate_v11(path: Path, trail_id: str, steps: int) -> None:
    """Each migration is execution-eligible and has the expected v1.1 identity."""
    result = validate_trailspec(spec_path=path)
    assert result["ok"] is True
    assert result["spec"]["trail_id"] == trail_id
    assert result["spec"]["version"] == "1.0.0"
    assert result["spec"]["steps_count"] == steps
    assert result["spec"]["execution_eligible"] is True
    assert len(result["spec"]["trail_hash"]) == 64


@pytest.mark.parametrize("path", [RB2_PATH, RB5_PATH])
def test_every_command_binds_the_runner_invocation(path: Path) -> None:
    """All commands receive the durable invocation ID through their environment."""
    for command in _commands(_load(path)):
        assert command["environment"]["TRAIL_INVOCATION_ID"] == "{invocation_id}"


@pytest.mark.parametrize("path", [RB2_PATH, RB5_PATH])
def test_each_transition_has_one_receipt_only_predicate(path: Path) -> None:
    """Every transition identifies one distinct predicate over its command receipt."""
    for step in _load(path)["steps"]:
        predicate_ids = []
        for transition in step["transitions"].values():
            evidence = transition["evidence"]
            predicate_ids.append(evidence["predicate_id"])
            assert evidence["clauses"]
            assert {clause["source"] for clause in evidence["clauses"]} == {"command_receipt"}
        assert len(predicate_ids) == len(set(predicate_ids))


def test_finalize_settle_matches_delegate_terminal_status_vocabulary() -> None:
    """The status case arms accept delegate.py's underscore-form terminal states."""
    spec = _load(RB2_PATH)
    finalize_settle = next(step for step in spec["steps"] if step["step_id"] == "finalize_settle")
    command = finalize_settle["command"]["argv"][2]
    matched_statuses = {
        status
        for case_arm in re.findall(r'(?:case "\$S" in|;;)\s*([^)]*)\)\s*echo', command)
        for status in case_arm.split("|")
        if status != "*"
    }

    assert matched_statuses == DELEGATE_TERMINAL_STATUSES


def _assert_rb2_cleanup_is_non_force(spec: dict[str, Any]) -> None:
    command = next(
        step["command"] for step in spec["steps"] if step["step_id"] == "cleanup_failed_worktree"
    )
    argv = command["argv"]
    assert "--force" not in argv
    assert "-D" not in argv
    assert "--force" not in " ".join(argv)
    assert " branch -D " not in f" {' '.join(argv)} "
    assert command["mutation_class"] == "local-write"


def test_rb2_cleanup_never_force_deletes_or_removes_the_branch() -> None:
    """Cleanup is non-force worktree removal; failed branches remain for forensics."""
    spec = _load(RB2_PATH)
    _assert_rb2_cleanup_is_non_force(spec)
    cleanup = next(step for step in spec["steps"] if step["step_id"] == "cleanup_failed_worktree")
    assert cleanup["transitions"]["worktree_removed"]["target"] == "observe_cleanup"
    assert cleanup["command"]["argv"][:2] == ["sh", "-c"]


def test_negative_rb2_readding_force_fails_only_the_cleanup_guard() -> None:
    """Mutation check: reintroducing force removal trips the dedicated cleanup guard."""
    spec = _load(RB2_PATH)
    cleanup = next(step for step in spec["steps"] if step["step_id"] == "cleanup_failed_worktree")
    cleanup["command"]["argv"][2] = cleanup["command"]["argv"][2].replace(
        "git worktree remove", "git worktree remove --force"
    )
    with pytest.raises(AssertionError):
        _assert_rb2_cleanup_is_non_force(spec)


def test_mutations_always_have_a_distinct_reobservation_step() -> None:
    """Mutating commands never claim state themselves; a different observe step follows."""
    checks = {
        RB2_PATH: {
            "drain_slot_inbox": "observe_slot_inbox",
            "dispatch_worker": "observe_dispatch_state",
            "override_dispatch": "observe_override_dispatch",
            "cleanup_failed_worktree": "observe_cleanup",
            "dispatch_retry": "observe_retry_dispatch",
        },
        RB5_PATH: {
            "drain_slot_inbox": "observe_slot_inbox",
            "readiness_snapshot": "tree_clean_check",
            "fetch_primary_state": "primary_ahead_check",
            "worktree_receipt": "observe_worktree_count",
            "final_inbox_recheck": "observe_final_inbox",
        },
    }
    for path, pairs in checks.items():
        steps = {step["step_id"]: step for step in _load(path)["steps"]}
        for mutation_id, observe_id in pairs.items():
            mutation = steps[mutation_id]
            assert mutation["command"]["mutation_class"] in {"local-write", "remote-mutation"}
            assert observe_id != mutation_id
            assert steps[observe_id]["command"]["mutation_class"] == "observe"
            assert observe_id in {
                transition["target"] for transition in mutation["transitions"].values()
            }


def test_former_judgment_and_summon_nodes_are_observe_or_stop() -> None:
    """Former human/judgment nodes only accept a receipt observation or route to STOP."""
    former_judgment_nodes = {
        RB2_PATH: {"author_brief", "approve_override", "await_settle"},
        RB5_PATH: {"apply_deliveries", "resolve_inflight", "sweep_judgment", "write_handoff"},
    }
    for path, step_ids in former_judgment_nodes.items():
        steps = {step["step_id"]: step for step in _load(path)["steps"]}
        for step_id in step_ids:
            step = steps[step_id]
            assert step["command"]["mutation_class"] == "observe"
            command_text = " ".join(step["command"]["argv"])
            assert "echo approved" not in command_text
            assert "echo written" not in command_text
            assert any(
                transition["target"].startswith("STOP-")
                for transition in step["transitions"].values()
            )


def _rb2_step(spec: dict[str, Any], step_id: str) -> dict[str, Any]:
    return next(step for step in spec["steps"] if step["step_id"] == step_id)


def _run_rb2_shell_step(
    step: dict[str, Any], tmp_path: Path, environment: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        step["command"]["argv"],
        cwd=tmp_path,
        env={**os.environ, **environment},
        check=False,
        text=True,
        capture_output=True,
    )


def _matching_transition_labels(
    step: dict[str, Any], *, actor_outcome: str, exit_code: int
) -> list[str]:
    return DefaultReceiptPredicateEvaluator().matching_labels(
        step, {"actor_outcome": actor_outcome, "exit_code": exit_code}
    )


def _write_fake_delegate(tmp_path: Path) -> None:
    fake_python = tmp_path / ".venv/bin/python"
    fake_python.parent.mkdir(parents=True)
    fake_python.write_text(
        "#!/bin/sh\nprintf '%s\\n' \"$FAKE_DISPATCH_OUTPUT\"\nexit \"$FAKE_DISPATCH_EXIT\"\n",
        encoding="utf-8",
    )
    fake_python.chmod(0o755)


def _write_fake_gh(tmp_path: Path) -> Path:
    fake_gh = tmp_path / "bin/gh"
    fake_gh.parent.mkdir(parents=True)
    fake_gh.write_text(
        "#!/bin/sh\nprintf '%s\\n' \"$FAKE_GH_OUTPUT\"\nexit \"$FAKE_GH_EXIT\"\n",
        encoding="utf-8",
    )
    fake_gh.chmod(0o755)
    return fake_gh.parent


def _write_fake_tee(tmp_path: Path) -> Path:
    fake_tee = tmp_path / "bin/tee"
    fake_tee.parent.mkdir(parents=True)
    fake_tee.write_text(
        "#!/bin/sh\nexit \"$FAKE_TEE_EXIT\"\n",
        encoding="utf-8",
    )
    fake_tee.chmod(0o755)
    return fake_tee.parent


def _assert_dispatch_failure_routes_by_token(spec: dict[str, Any]) -> None:
    dispatch = _rb2_step(spec, "dispatch_worker")
    assert dispatch["transitions"]["dispatch_failed"]["evidence"]["clauses"] == [
        {
            "source": "command_receipt",
            "field": "actor_outcome",
            "op": "eq",
            "value": "dispatch-failed",
        }
    ]
    assert _matching_transition_labels(
        dispatch, actor_outcome="dispatch-failed", exit_code=17
    ) == ["dispatch_failed"]


def test_rb2_benign_overlap_refusal_reaches_approval_or_concurrency_stop(
    tmp_path: Path,
) -> None:
    """A logged benign refusal reaches approval; missing or denied approval stops safely."""
    spec = _load(RB2_PATH)
    dispatch = _rb2_step(spec, "dispatch_worker")
    observe_dispatch = _rb2_step(spec, "observe_dispatch_state")
    approve_override = _rb2_step(spec, "approve_override")
    _write_fake_delegate(tmp_path)
    environment = {
        "TASK_ID": "overlap-task",
        "LANE": "grok",
        "BRIEF_PATH": "brief.md",
        "OVERLAP_REASON": "approved-reason",
        "FAKE_DISPATCH_OUTPUT": "No actual path overlap was found",
        "FAKE_DISPATCH_EXIT": "1",
    }

    benign_refusal = _run_rb2_shell_step(dispatch, tmp_path, environment)

    assert benign_refusal.returncode == 0
    assert benign_refusal.stdout == "dispatched\n"
    assert (
        tmp_path / "batch_state/rb2-dispatch-overlap-task.log"
    ).read_text(encoding="utf-8") == "No actual path overlap was found\n"
    observed_refusal = _run_rb2_shell_step(observe_dispatch, tmp_path, environment)
    assert observed_refusal.stdout == "overlap-refused\n"
    assert observe_dispatch["transitions"]["overlap_refused"]["target"] == "approve_override"

    missing_approval = _run_rb2_shell_step(approve_override, tmp_path, environment)
    assert missing_approval.stdout == "override-receipt-missing\n"
    assert (
        approve_override["transitions"]["override_receipt_missing"]["target"]
        == "STOP-concurrency-conflict"
    )
    receipt = tmp_path / "batch_state/rb2-overlap-overlap-task.receipt"
    receipt.write_text("task_id=overlap-task\nreason=denied\n", encoding="utf-8")
    denied_approval = _run_rb2_shell_step(approve_override, tmp_path, environment)
    assert denied_approval.stdout == "override-receipt-invalid\n"
    assert (
        approve_override["transitions"]["override_receipt_invalid"]["target"]
        == "STOP-concurrency-conflict"
    )


def test_rb2_dispatch_wrappers_log_combined_output_and_route_failure_tokens(
    tmp_path: Path,
) -> None:
    """Both wrappers retain output, and dispatch failure selects its token transition."""
    spec = _load(RB2_PATH)
    dispatch = _rb2_step(spec, "dispatch_worker")
    override = _rb2_step(spec, "override_dispatch")
    _write_fake_delegate(tmp_path)
    environment = {
        "TASK_ID": "failed-task",
        "LANE": "grok",
        "BRIEF_PATH": "brief.md",
        "OVERLAP_REASON": "approved-reason",
        "FAKE_DISPATCH_OUTPUT": "ordinary failure",
        "FAKE_DISPATCH_EXIT": "17",
    }

    failed_dispatch = _run_rb2_shell_step(dispatch, tmp_path, environment)
    failed_override = _run_rb2_shell_step(override, tmp_path, environment)

    assert failed_dispatch.returncode == 17
    assert failed_dispatch.stdout == "dispatch-failed\n"
    assert _matching_transition_labels(
        dispatch, actor_outcome=failed_dispatch.stdout.strip(), exit_code=failed_dispatch.returncode
    ) == ["dispatch_failed"]
    assert failed_override.returncode == 17
    assert failed_override.stdout == "override-dispatch-failed\n"
    assert (tmp_path / "batch_state/rb2-dispatch-failed-task.log").read_text(
        encoding="utf-8"
    ) == "ordinary failure\n"
    assert (tmp_path / "batch_state/rb2-override-dispatch-failed-task.log").read_text(
        encoding="utf-8"
    ) == "ordinary failure\n"


def test_rb2_dispatch_emits_failure_token_for_setup_and_tee_errors(tmp_path: Path) -> None:
    """Setup and log-capture failures preserve status and select dispatch_failed."""
    spec = _load(RB2_PATH)
    dispatch = _rb2_step(spec, "dispatch_worker")
    environment = {
        "TASK_ID": "setup-task",
        "LANE": "grok",
        "BRIEF_PATH": "brief.md",
        "FAKE_DISPATCH_OUTPUT": "success",
        "FAKE_DISPATCH_EXIT": "0",
    }

    (tmp_path / "batch_state").write_text("not a directory\n", encoding="utf-8")
    setup_failure = _run_rb2_shell_step(dispatch, tmp_path, environment)
    assert setup_failure.returncode == 1
    assert setup_failure.stdout == "dispatch-failed\n"
    assert _matching_transition_labels(
        dispatch, actor_outcome=setup_failure.stdout.strip(), exit_code=setup_failure.returncode
    ) == ["dispatch_failed"]

    tee_tmp_path = tmp_path / "tee-failure"
    tee_tmp_path.mkdir()
    _write_fake_delegate(tee_tmp_path)
    fake_bin = _write_fake_tee(tee_tmp_path)
    tee_failure = _run_rb2_shell_step(
        dispatch,
        tee_tmp_path,
        {**environment, "PATH": f"{fake_bin}:{os.environ['PATH']}", "FAKE_TEE_EXIT": "2"},
    )
    assert tee_failure.returncode == 2
    assert tee_failure.stdout == "dispatch-failed\n"
    assert _matching_transition_labels(
        dispatch, actor_outcome=tee_failure.stdout.strip(), exit_code=tee_failure.returncode
    ) == ["dispatch_failed"]


def test_rb2_dispatch_failure_token_pin_rejects_the_old_exit_code_predicate() -> None:
    """Mutation check: reintroducing exit-code 1 makes the status-17 pin fail."""
    spec = _load(RB2_PATH)
    _assert_dispatch_failure_routes_by_token(spec)

    mutated = copy.deepcopy(spec)
    mutated_dispatch = _rb2_step(mutated, "dispatch_worker")
    mutated_dispatch["transitions"]["dispatch_failed"]["evidence"]["clauses"].append(
        {"source": "command_receipt", "field": "exit_code", "op": "eq", "value": 1}
    )

    mutated_selection = _matching_transition_labels(
        mutated_dispatch, actor_outcome="dispatch-failed", exit_code=17
    )
    assert mutated_selection == []
    with pytest.raises(AssertionError):
        assert mutated_selection == ["dispatch_failed"]


@pytest.mark.parametrize(
    ("gh_output", "gh_exit", "expected_outcome"),
    [
        ("network unavailable", "1", "deliverable-check-failed"),
        ("[]", "0", "no-pr"),
        ("not JSON", "0", "deliverable-check-failed"),
    ],
)
def test_rb2_deliverable_probes_distinguish_pr_absence_from_check_failures(
    tmp_path: Path, gh_output: str, gh_exit: str, expected_outcome: str
) -> None:
    """All settle paths fail closed unless gh returns validated JSON with no PRs."""
    spec = _load(RB2_PATH)
    fake_bin = _write_fake_gh(tmp_path)
    environment = {
        "TASK_ID": "deliverable-task",
        "LANE": "grok",
        "FAKE_GH_OUTPUT": gh_output,
        "FAKE_GH_EXIT": gh_exit,
        "PATH": f"{fake_bin}:{os.environ['PATH']}",
    }

    for step_id in (
        "verify_deliverable_success",
        "verify_deliverable_timeout",
        "verify_deliverable_attention",
    ):
        step = _rb2_step(spec, step_id)
        result = _run_rb2_shell_step(step, tmp_path, environment)

        assert result.returncode == 0
        assert result.stdout == f"{expected_outcome}\n"
        selected = _matching_transition_labels(
            step, actor_outcome=result.stdout.strip(), exit_code=result.returncode
        )
        expected_label = expected_outcome.replace("-", "_")
        assert selected == [expected_label]
        if expected_outcome == "deliverable-check-failed":
            assert step["transitions"][expected_label]["target"] == "STOP-precondition-failed"


class _TerminalSource:
    source_id = "fleet-bridge"
    source_kind = "bridge"

    def __init__(self, *, lease_current: bool = True) -> None:
        self.lease_current = lease_current
        self.calls = 0

    def reobserve_terminal(
        self,
        *,
        run: Any,
        terminal_command_receipt: dict[str, Any],
        terminal_step_receipt: dict[str, Any],
    ) -> dict[str, Any]:
        self.calls += 1
        return {
            "observation_id": "rb5-close-observation",
            "observed_at": "2026-07-29T00:00:00Z",
            "run_id": run.run_id,
            "trail_id": run.trail_id,
            "trail_hash": run.trail_hash,
            "terminal_outcome": run.terminal_outcome,
            "lease_id": "lease-rb5",
            "lease_generation": 1,
            "fencing_token": "fence-rb5",
            "pr_head": None,
            "lease_current": self.lease_current,
            "terminal_observed": True,
        }


class _InvalidTerminalAuthority(_TerminalSource):
    """A provisioned source that returns unusable closure authority evidence."""

    def reobserve_terminal(
        self,
        *,
        run: Any,
        terminal_command_receipt: dict[str, Any],
        terminal_step_receipt: dict[str, Any],
    ) -> dict[str, Any]:
        self.calls += 1
        return {"observation_id": "invalid-authority"}


def _rb5_terminal_fixture() -> dict[str, Any]:
    """Use RB-5's actual terminal observation with a direct test entry point."""
    spec = _load(RB5_PATH)
    terminal = copy.deepcopy(next(step for step in spec["steps"] if step["step_id"] == "close_declaration"))
    terminal["transitions"] = {
        "closure_inputs_observed": {
            **terminal["transitions"]["closure_inputs_observed"],
            "target": "closed_handoff_written",
        }
    }
    return {
        **{key: copy.deepcopy(spec[key]) for key in ("schema_version", "trail_id", "version", "title", "seats", "parameters", "stop_codes", "terminal_outcomes")},
        "steps": [terminal],
    }


def _rb5_executor(tmp_path: Path, source: _TerminalSource) -> TrailExecutor:
    seats = tmp_path / "fleet.yaml"
    seats.write_text(
        yaml.safe_dump(
            {"endpoints": [{"name": name, "state": "live"} for name in _load(RB5_PATH)["seats"]]}
        ),
        encoding="utf-8",
    )
    store = TrailStore(tmp_path / "runs.sqlite3", tmp_path / "receipts")
    return TrailExecutor(
        store,
        project_root=tmp_path,
        seat_registry_path=seats,
        command_runner=lambda command, cwd: CommandExecution(0, "closure-inputs-observed", ""),
        closure_gate=TrailClosureGate(store, source),
    )


def _terminal_rb5_run(executor: TrailExecutor, tmp_path: Path) -> str:
    path = tmp_path / "rb5-terminal.trail.yaml"
    path.write_text(yaml.safe_dump(_rb5_terminal_fixture(), sort_keys=False), encoding="utf-8")
    begun = executor.begin(
        trail_path=path,
        seat="grok",
        task_family="infra-orchestration",
        params={"handoff_agent": "grok", "handoff_file": "handoff.md"},
    )
    assert begun.run_id is not None
    terminal = executor.step(run_id=begun.run_id, expected_step="close_declaration")
    assert terminal.outcome == "terminal"
    return begun.run_id


def test_rb5_terminal_step_delegates_closure_to_executor_close(tmp_path: Path) -> None:
    """RB-5's terminal observation does not close; TrailExecutor.close performs closure."""
    source = _TerminalSource()
    executor = _rb5_executor(tmp_path, source)
    run_id = _terminal_rb5_run(executor, tmp_path)

    before = executor.store.get_run(run_id)
    closed = executor.close(run_id=run_id)

    assert before.closure_state == "open"
    assert closed.exit_class == ExitClass.OK
    assert closed.outcome == "closed"
    assert source.calls == 1


def test_rb5_close_refuses_invalid_chain_without_reobservation(tmp_path: Path) -> None:
    """A malformed receipt projection parks RB-5 closure before terminal re-observation."""
    source = _TerminalSource()
    executor = _rb5_executor(tmp_path, source)
    run_id = _terminal_rb5_run(executor, tmp_path)
    invocation = executor.store.list_invocations(run_id)[0]
    projection = executor.store.projection_path(
        run_id=run_id, filename=f"command-000000-{invocation['invocation_id']}.json"
    )
    projection.write_text("{}\n", encoding="utf-8")

    result = executor.close(run_id=run_id)

    assert result.exit_class == ExitClass.STOP_PARKED
    assert result.outcome == "closure_parked"
    assert source.calls == 0


def test_rb5_close_parks_a_stale_lease(tmp_path: Path) -> None:
    """Closure re-observation rejects stale lease evidence for this RB-5 terminal."""
    source = _TerminalSource(lease_current=False)
    executor = _rb5_executor(tmp_path, source)
    run_id = _terminal_rb5_run(executor, tmp_path)

    result = executor.close(run_id=run_id)

    assert result.exit_class == ExitClass.STOP_PARKED
    assert result.outcome == "closure_parked"
    assert executor.store.get_run(run_id).closure_state == "parked"


def test_rb5_close_requires_a_provisioned_closure_authority(tmp_path: Path) -> None:
    """Without a closure re-observer, local receipts cannot authorize close."""
    source = _TerminalSource()
    executor = _rb5_executor(tmp_path, source)
    run_id = _terminal_rb5_run(executor, tmp_path)
    executor.closure_gate = None

    result = executor.close(run_id=run_id)

    assert result.exit_class == ExitClass.INVALID
    assert result.outcome == "closure_unavailable"
    assert source.calls == 0


def test_rb5_close_parks_invalid_closure_authority_evidence(tmp_path: Path) -> None:
    """Malformed re-observed closure authority evidence cannot close the RB-5 run."""
    source = _InvalidTerminalAuthority()
    executor = _rb5_executor(tmp_path, source)
    run_id = _terminal_rb5_run(executor, tmp_path)

    result = executor.close(run_id=run_id)

    assert result.exit_class == ExitClass.STOP_PARKED
    assert result.outcome == "closure_parked"
    assert executor.store.get_run(run_id).closure_state == "parked"
