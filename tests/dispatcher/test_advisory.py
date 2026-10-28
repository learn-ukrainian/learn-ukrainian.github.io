"""Bounded workers must pass sealed-envelope admission before any paid launch."""

import json
import os
import subprocess
from unittest.mock import Mock

import pytest

from scripts.agent_runtime import bounded_advisory as advisory
from scripts.dispatcher import checks, cli, git, store, worker


@pytest.fixture
def launch(tmp_path, monkeypatch):
    (tmp_path / "docs").mkdir()
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    monkeypatch.setattr(git, "resolve_repo", lambda _: (tmp_path, dict(key="public", github="example/public")))
    monkeypatch.setattr(git, "worktree_plan", lambda *a: (tmp_path, "codex/worker", "a" * 40))
    monkeypatch.setattr(git, "create_worktree", Mock())
    monkeypatch.setattr(checks, "check_resources", lambda _: None)
    monkeypatch.setattr(worker, "start", Mock(side_effect=lambda spec, record, prompt, _: store.create(
        {**record, "pid": os.getpid(), "process_start": worker._identity(os.getpid())}, prompt,
    )))
    return ["dispatch", "--agent", "sol", "--model", "gpt-6-luna", "--task-id", "worker",
            "--prompt", "Inspect the assigned document", "--owned-path", "docs/example.md"]


@pytest.mark.parametrize("model", ["gpt-6-luna", "openai/gpt-6-luna-high", "gemini-3.8-flash-high"])
def test_missing_envelope_refuses_before_side_effects(launch, capsys, tmp_path, model):
    """Defect class: bounded catalog routes bypass advice and start paid execution."""
    launch[launch.index("--model") + 1] = model
    assert cli.main(launch) == 2
    assert "BOUNDED_ENVELOPE_REQUIRED" in capsys.readouterr().err
    worker.start.assert_not_called()
    git.create_worktree.assert_not_called()
    assert not (tmp_path / "tasks").exists()


@pytest.mark.parametrize("model", ["gpt-6-luna", "gemini-3.8-flash-high"])
@pytest.mark.parametrize("defect,reason", [
    (None, None), ("incomplete", "ADVISORY_ENVELOPE_INCOMPLETE"),
    ("binding", "ADVISORY_BINDING_MISMATCH"), ("seal", "ADVISORY_SEAL_MISMATCH"),
    ("paths", "ADVISORY_OWNED_PATHS_MISMATCH"),
])
def test_sealed_envelope_admission_and_record(launch, capsys, tmp_path, defect, reason, model):
    """Defect classes: incomplete, foreign, edited or scope-mismatched envelopes are accepted."""
    launch[launch.index("--model") + 1] = model
    assert cli.main([*launch, "--print-advisory-binding"]) == 0
    binding = capsys.readouterr().out.strip()
    worker.start.assert_not_called()
    git.create_worktree.assert_not_called()
    assert not (tmp_path / "tasks").exists()
    envelope = dict(task_contract="Inspect one document", owned_paths=["docs/example.md"],
                    acceptance_evidence=["Report findings"], constraints=["Escalate scope changes"],
                    risk_boundaries=["Do not edit code"], escalation_triggers=["Ambiguous scope"],
                    max_changed_files=1, max_non_test_loc=20, dispatch_args_sha256=binding)
    if defect == "incomplete":
        del envelope["acceptance_evidence"]
    if defect == "paths":
        envelope["owned_paths"] = ["docs/other.md"]
    result = "```advisory-envelope\n" + json.dumps(envelope) + "\n```\n"
    path = store.record_path("advisor")
    path.parent.mkdir()
    path.with_suffix(".result").write_text(result)
    policy = advisory.bounded_execution_policy()
    path.write_text(json.dumps(dict(
        task_id="advisor", status="done", mode="read-only", model=policy.advisor_model_id,
        advisory_role=policy.advisor_role, advisory_route=advisory.ADVISOR_ROUTE,
        advisory_binding_sha256=binding, result_file=str(path.with_suffix(".result")), run_nonce="advisor-run",
        advisory_seal=advisory.seal_advisor_result(result, model=policy.advisor_model_id, run_nonce="advisor-run"),
    )))
    if defect == "binding":
        launch[launch.index("--prompt") + 1] = "Different instructions"
    if defect == "seal":
        path.with_suffix(".result").write_text(result + "changed")
    assert cli.main([*launch, "--advisory-task", "advisor"]) == (2 if reason else 0)
    if reason:
        assert reason in capsys.readouterr().err
        worker.start.assert_not_called()
        git.create_worktree.assert_not_called()
        assert not store.record_path("worker").exists()
    else:
        record = store.read("worker")
        assert record["advisory_envelope"]["advisor_task_id"] == "advisor"
        assert record["advisory_envelope"]["dispatch_args_sha256"] == binding
        assert record["advisory_envelope"]["owned_paths"] == ["docs/example.md"]
        worker.start.assert_called_once()


@pytest.mark.parametrize("model", ["gpt-6.1-sol", "gemini-3.8-flash-high"])
def test_non_bounded_model_needs_no_advisory(launch, model):
    """Defect class: bounded admission accidentally refuses Sol or exempt Ukrainian Flash work."""
    launch[launch.index("--model") + 1] = model
    if model == "gemini-3.8-flash-high":
        launch = [*launch[:-2], "--research-task-family", "ukrainian-authoring"]
    assert cli.main(launch) == 0
    assert "advisory_envelope" not in store.read("worker")


@pytest.mark.parametrize("mode,profile,family,path,admitted", [
    ("read-only", "ukrainian", "ukrainian-review", "scripts/audit/generate_practice_deck.py", True),
    ("read-only", "ukrainian", "practice", "docs/example.md", True),
    ("workspace-write", "ukrainian", "ukrainian-review", "scripts/audit/generate_practice_deck.py", False),
    ("read-only", "code", "practice", "scripts/audit/generate_practice_deck.py", False),
])
def test_flash_ukrainian_review_of_record_is_admitted_only_read_only(
    launch, capsys, tmp_path, mode, profile, family, path, admitted,
):
    """Defect class: a read-only Ukrainian review of a mixed PR is refused for naming its real family or code paths."""
    (tmp_path / "scripts/audit").mkdir(parents=True)
    launch[launch.index("--model") + 1] = "gemini-3.8-flash-high"
    launch[launch.index("--owned-path") + 1] = path
    launch += ["--mode", mode, "--review-profile", profile, "--research-task-family", family]
    assert cli.main(launch) == (0 if admitted else 2)
    if admitted:
        assert "advisory_envelope" not in store.read("worker")
    else:
        assert "BOUNDED_ENVELOPE_REQUIRED" in capsys.readouterr().err
        worker.start.assert_not_called()


@pytest.mark.parametrize("complete", [False, True])
@pytest.mark.parametrize("model", ["gpt-6-luna", "claude-haiku-5-5", "haiku"])
def test_driver_brief_exception_requires_acceptance_command(launch, complete, capsys, tmp_path, model):
    """Defect class: concrete or alias models bypass brief validation or reject valid bounded implementation."""
    if model != "gpt-6-luna":
        launch[launch.index("--agent") + 1] = "claude"
    launch[launch.index("--model") + 1] = model
    launch += ["--research-role", "implementation", "--research-task-family", "bounded_implementation",
               "--mode", "workspace-write"]
    if complete:
        (tmp_path / "docs/example.md").write_text("Assigned document")
        for command in (("init",), ("remote", "add", "origin", "git@github.com:example/public.git"),
                        ("-c", "user.name=Stub", "-c", "user.email=stub@example.invalid",
                                    "commit", "--allow-empty", "-m", "fixture")):
            subprocess.run(["git", "-C", str(tmp_path), *command], check=True, capture_output=True, timeout=30)
        launch += ["--verify-command", "test -f docs/example.md"]
    assert cli.main(launch) == (0 if complete else 2)
    if complete:
        assert store.read("worker")["driver_brief"]["owned_paths"] == ["docs/example.md"]
    else:
        assert "BOUNDED_DRIVER_BRIEF_REFUSED" in capsys.readouterr().err
        worker.start.assert_not_called()


@pytest.mark.parametrize("flags,reason", [
    (["--advisory-role", "review_budget_extension"], "required together"),
    (["--advisory-binding", "e" * 64], "required together"),
    (["--advisory-role", "consequential_advisory", "--advisory-binding", "e" * 64], "not a catalog advisory_roles"),
    (["--advisory-role", "review_budget_extension", "--advisory-binding", "E" * 64], "lowercase sha256"),
    (["--advisory-role", "review_budget_extension", "--advisory-binding", "e" * 64, "--mode", "workspace-write"],
     "runs read-only"),
])
def test_advisory_role_dispatch_refuses_unbound_or_writable_decisions(launch, capsys, flags, reason):
    """Defect class: an advisory decision runs unbound, writable, or under a role the catalog does not define."""
    launch[launch.index("--model") + 1] = "gpt-6.1-sol"
    assert cli.main([*launch[:-2], *flags]) == 2
    assert reason in capsys.readouterr().err
    worker.start.assert_not_called()


def test_advisory_role_dispatch_runs_only_on_a_native_harness(launch, capsys):
    """Defect: a runtime-reported harness seals the requested model, not the one that ran (review F1)."""
    launch[launch.index("--agent") + 1] = "cursor"
    launch[launch.index("--model") + 1] = "gpt-6.1-sol"
    assert cli.main([*launch[:-2], "--advisory-role", "review_budget_extension", "--advisory-binding", "e" * 64]) == 2
    assert "native harness" in capsys.readouterr().err
    worker.start.assert_not_called()


def test_advisory_role_dispatch_records_role_route_and_binding(launch):
    """Defect: dispatch v2 records no advisory role or binding, so no consumer can find a bound decision."""
    launch[launch.index("--model") + 1] = "gpt-6.1-sol"
    digest = "e" * 64
    assert cli.main([*launch[:-2], "--advisory-role", "review_budget_extension", "--advisory-binding", digest]) == 0
    record = store.read("worker")
    assert (record["advisory_role"], record["advisory_route"], record["advisory_binding_sha256"]) == (
        "review_budget_extension", "advisory_roles.review_budget_extension", digest,
    )


def test_worker_seals_an_advisory_decision_as_written(tmp_path):
    """Defect: the finish-time seal was lost with the legacy launcher, so every advisory result reads as unsealed."""
    result = tmp_path / "advisor.result"
    text = 'Decision follows.\n\n```budget-extension\n{"decision": "APPROVE"}\n```\n'
    result.write_text(text)
    record = dict(advisory_role="review_budget_extension", model="gpt-6.1-sol", run_nonce="advisor-run")
    worker._seal_advisory_result(record, result)
    assert record[advisory.SEAL_FIELD] == advisory.seal_advisor_result(
        text, model="gpt-6.1-sol", run_nonce="advisor-run", fence="budget-extension",
    )
    assert record[advisory.SEAL_FIELD]["envelope_sha256"] == advisory.canonical_sha256({"decision": "APPROVE"})
    # A role the catalog no longer defines leaves the result unsealed, never the record unsettled.
    unknown = dict(advisory_role="retired_role", model="gpt-6.1-sol", run_nonce="advisor-run")
    worker._seal_advisory_result(unknown, result)
    assert advisory.SEAL_FIELD not in unknown and unknown["advisory_seal_error"].startswith("KeyError")
