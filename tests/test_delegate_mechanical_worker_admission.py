"""#10079: persisted dispatcher typing reaches worker admission without a provider call."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import delegate
from scripts.agent_runtime import target_admission
from scripts.agent_runtime.kimi_admission import KimiAdmissionRefused
from scripts.agent_runtime.target_admission import ReviewAdmissionRefused, mechanical_scope_digest

HAIKU = "claude-haiku-5-5"
TASK = "mechanical-worker-10079"
OWNED = "tests/test_example.py"


@pytest.fixture
def dispatched(tmp_path, monkeypatch):
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    for key in tuple(delegate.os.environ):
        if key.startswith("GIT_"):
            monkeypatch.delenv(key)
    repo = tmp_path / "repo"
    repo.mkdir()
    for command in (
        ["init", "-q", "-b", "main"],
        ["config", "user.name", "Test"],
        ["config", "user.email", "test@example.com"],
        ["config", "core.hooksPath", "/dev/null"],
    ):
        subprocess.run(["git", *command], cwd=repo, check=True, capture_output=True, timeout=10)
    (repo / OWNED).parent.mkdir()
    (repo / OWNED).write_text("def test_example():\n    assert True\n")
    for command in (["add", "."], ["commit", "-qm", "base"]):
        subprocess.run(["git", *command], cwd=repo, check=True, capture_output=True, timeout=10)
    args = delegate.build_parser().parse_args([
        "dispatch", "--agent", "claude", "--model", HAIKU, "--task-id", TASK,
        "--prompt", "Classify this test as flaky or real.", "--mode", "read-only",
        "--research-task-family", "mechanical_classification", "--research-role", "classification",
        "--research-track", "infra-harness", "--research-owned-path", OWNED,
    ])
    refusal, target = delegate._admit_dispatch_target(
        args, agent="claude", trees=lambda: delegate._kimi_worktree_trees(repo),
    )
    assert refusal is None and target.model == HAIKU
    record = {"task_id": TASK, "status": "spawning", "mode": args.mode,
              "mechanical_task": delegate._mechanical_task_scope(args, admitted=True)}
    state_path = delegate._state_path(TASK)
    delegate._write_state_atomic(state_path, record)
    return repo, args, state_path


def test_persistence_uses_the_admitted_inputs_even_if_dispatch_args_change(dispatched):
    _repo, args, state_path = dispatched
    admitted = json.loads(state_path.read_text())["mechanical_task"]
    args.research_task_family = "readonly_recon"
    args.prompt = "Changed after admission"
    assert delegate._mechanical_task_scope(args, admitted=True) == admitted


def test_dispatch_refuses_inputs_changed_during_admission(dispatched, monkeypatch):
    repo, args, _state_path = dispatched
    resolve = target_admission.resolve_and_admit

    def change_after_gate(*positional, **kwargs):
        result = resolve(*positional, **kwargs)
        args.research_task_family = "readonly_recon"
        return result

    monkeypatch.setattr(target_admission, "resolve_and_admit", change_after_gate)
    refusal, target = delegate._admit_dispatch_target(
        args, agent="claude", trees=lambda: delegate._kimi_worktree_trees(repo),
    )
    assert target is None and "admission inputs changed during dispatch" in refusal


def test_prompt_file_dispatch_reaches_worker_from_persisted_reference(dispatched):
    repo, args, state_path = dispatched
    prompt = repo / "prompt.md"
    prompt.write_text("Classify this test.")
    args.prompt_file = str(prompt)
    args.owned_path = [OWNED]
    refusal, target = delegate._admit_dispatch_target(
        args, agent="claude", trees=lambda: delegate._kimi_worktree_trees(repo),
    )
    assert refusal is None and target.model == HAIKU
    scope = delegate._mechanical_task_scope(args, admitted=True)
    assert scope["paths"] == [OWNED, OWNED]  # Preserve both dispatcher ownership inputs.
    saved = json.loads(state_path.read_text())
    saved["mechanical_task"] = scope
    delegate._write_state_atomic(state_path, saved)
    refusal, target = delegate._kimi_worker_refusal(
        TASK, agent="claude", model=HAIKU, mode="read-only", cwd=repo, review=False,
    )
    assert refusal is None and target.model == HAIKU
    args.prompt_file = str(repo / "missing.md")
    refusal, target = delegate._admit_dispatch_target(
        args, agent="claude", trees=lambda: delegate._kimi_worktree_trees(repo),
    )
    assert target is None and "task input unavailable at prompt file" in refusal


def test_eligible_dispatch_and_worker_receive_identical_inputs(dispatched, monkeypatch):
    repo, args, _state_path = dispatched
    resolve = target_admission.resolve_and_admit
    seen = []

    def capture(*args, **kwargs):
        seen.append(kwargs)
        return resolve(*args, **kwargs)

    monkeypatch.setattr(target_admission, "resolve_and_admit", capture)
    refusal, target = delegate._kimi_worker_refusal(
        TASK, agent="claude", model=HAIKU, mode="read-only", cwd=repo, review=False,
    )
    assert refusal is None and target.model == HAIKU
    assert {key: seen[0][key] for key in (
        "task_family", "task_role", "mode", "paths", "review", "language_lane", "research_track", "task_prompt",
    )} == {
        "task_family": args.research_task_family, "task_role": args.research_role,
        "mode": args.mode, "paths": [OWNED], "review": False, "language_lane": False,
        "research_track": args.research_track, "task_prompt": args.prompt,
    }


@pytest.mark.parametrize("change", ["missing-family", "classification-write", "tampered-family", "tampered-mode"])
def test_worker_refuses_invalid_or_tampered_record_with_typed_terminal_cause(dispatched, monkeypatch, change):
    repo, _args, state_path = dispatched
    record = json.loads(state_path.read_text())
    mode = "read-only"
    if change == "missing-family":
        record.pop("mechanical_task")
    elif change == "classification-write":
        mode = record["mode"] = record["mechanical_task"]["mode"] = "workspace-write"
        record["mechanical_task"]["sha256"] = mechanical_scope_digest(record["mechanical_task"])
    elif change == "tampered-mode":
        mode = "workspace-write"
    else:
        # Both families are eligible: re-running policy alone would miss this tamper.
        record["mechanical_task"]["family"] = "readonly_recon"
    delegate._write_state_atomic(state_path, record)

    def never_started(*_args, **_kwargs):
        pytest.fail("refused admission reached runtime setup")

    monkeypatch.setattr(delegate.signal, "signal", never_started)
    monkeypatch.setattr(delegate, "_advisory_worker_refusal", never_started)
    assert delegate._run_worker(
        TASK, "claude", "worker argv is not task authority", mode, str(repo), HAIKU, 30,
    ) == 1
    terminal = json.loads(state_path.read_text())
    assert terminal["status"] == "failed"
    assert terminal["failure_reason"] == terminal["last_error"] == "mechanical_admission_refused"
    assert terminal["returncode_reason"] == "mechanical_admission_refused"
    assert terminal["finished_at"] and terminal["exit_code"] == 1
    assert terminal["stderr_excerpt"].startswith("MECHANICAL_TASK_REFUSED:")
    assert "worker_process_dead" not in state_path.read_text()


@pytest.mark.parametrize("exception,code", [
    (ReviewAdmissionRefused("review policy refused"), "review_admission_refused"),
    (KimiAdmissionRefused("Kimi policy refused"), "kimi_admission_refused"),
])
def test_other_typed_admission_refusals_are_terminal(dispatched, monkeypatch, exception, code):
    repo, _args, state_path = dispatched

    def refuse(*_args, **_kwargs):
        raise exception

    monkeypatch.setattr(target_admission, "resolve_and_admit", refuse)
    refusal, target = delegate._kimi_worker_refusal(
        TASK, agent="claude", model=HAIKU, mode="read-only", cwd=repo, review=False,
    )
    assert target is None and refusal == code
    record = json.loads(state_path.read_text())
    assert record["status"] == "failed" and record["failure_reason"] == code
    assert record["stderr_excerpt"] == str(exception)


def test_refusal_without_record_does_not_create_one(tmp_path, monkeypatch):
    tasks = tmp_path / "absent-tasks"
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    refusal, target = delegate._kimi_worker_refusal(
        TASK, agent="claude", model=HAIKU, mode="read-only", cwd=tmp_path, review=False,
    )
    assert refusal == "mechanical_admission_refused" and target is None
    assert not tasks.exists()


def test_worker_rechecks_owned_content_after_dispatch(dispatched):
    repo, _args, state_path = dispatched
    (repo / OWNED).write_bytes(b"\xff")
    refusal, target = delegate._kimi_worker_refusal(
        TASK, agent="claude", model=HAIKU, mode="read-only", cwd=repo, review=False,
    )
    assert refusal == "mechanical_admission_refused" and target is None
    assert "owned content" in json.loads(state_path.read_text())["stderr_excerpt"]
