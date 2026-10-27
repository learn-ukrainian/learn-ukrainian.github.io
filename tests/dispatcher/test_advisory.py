"""Bounded workers must pass sealed-envelope admission before any paid launch."""

import json
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
    monkeypatch.setattr(worker, "start", Mock(side_effect=lambda spec, record, prompt, _: store.create(record, prompt)))
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
