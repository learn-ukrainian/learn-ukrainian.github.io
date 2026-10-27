"""Bounded workers must pass sealed-envelope admission before any paid launch."""

import json
import subprocess
from pathlib import Path
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


# Ports from tests/test_research_registry_p3.py and test_task_lifecycle_carriers.py.
from scripts.dispatcher import prompt_context
from scripts.orchestration import task_identity, task_lifecycle
from scripts.research import consumption
from scripts.research import registry as reg
from tests.test_research_registry_p3 import _make_record, _write_registry
from tests.test_research_registry_p3 import reg_root as reg_root


def test_delegate_state_never_persists_research_null():
    # ADR-011 P3 default compatibility: a no-flags dispatch, a disabled registry,
    # or a degraded injection all resolve research_state to None; the persisted
    # state dict must OMIT the "research" key entirely — never "research": null.
    delegate = prompt_context
    base_state = {"task_id": "t", "status": "spawning"}

    no_flags = delegate._with_optional_research_state(dict(base_state), None)
    assert "research" not in no_flags
    assert no_flags == base_state

    with_context = delegate._with_optional_research_state(
        dict(base_state), {"pointer_ids": ["r1"], "filtered_etag": "e", "dropped_ids": [], "context_fingerprint": "f"}
    )
    assert with_context["research"] == {
        "pointer_ids": ["r1"], "filtered_etag": "e", "dropped_ids": [], "context_fingerprint": "f",
    }



def test_delegate_injection_is_pointer_only_and_persists_safely(reg_root, monkeypatch):
    delegate = prompt_context
    monkeypatch.setattr(reg, "_ROOT_OVERRIDE", reg_root)
    monkeypatch.setattr(delegate, "_REPO_ROOT", reg_root)
    _write_registry(
        reg_root,
        [
            _make_record(
                reg_root,
                "cefr",
                routing={"roles": ["quality"], "task_families": ["difficulty-gate"]},
            )
        ],
    )
    surfaced: list[tuple[str, dict]] = []
    monkeypatch.setattr(consumption, "emit_event", lambda t, p, **k: surfaced.append((t, p)))

    ctx = reg.normalize_context("quality", "difficulty-gate", None, [])
    block, state = delegate._resolve_research_injection(ctx, "task-9")

    # pointer-only prompt block: ids + fetch instruction, never a digest body
    assert "cefr" in block and "/api/knowledge/record/{id}" in block
    assert "Paraphrase-only" not in block
    # persistence allowlist: ids / etag / dropped / fingerprint only
    assert set(state) == {"pointer_ids", "filtered_etag", "dropped_ids", "context_fingerprint"}
    assert state["pointer_ids"] == ["cefr"]
    assert "owned_paths" not in state and "role" not in state
    # a surface (not consumption) event was emitted for the injected pointer
    assert surfaced == [
        (consumption.SURFACED_EVENT, {"task_id": "task-9", "research_id": "cefr", "surface": "dispatch"})
    ]



@pytest.mark.parametrize("fresh", [False, True], ids=["rollover", "fresh"])
def test_delegate_loads_validated_carrier_and_prompt(tmp_path: Path, fresh: bool) -> None:
    path = _lifecycle_file(tmp_path, fresh=fresh)

    carrier, prompt = prompt_context._load_task_lifecycle_carrier(str(path))

    assert carrier is not None
    assert carrier["state_file"] == str(path.resolve())
    assert carrier["identity"]["github_issue_number"] == 42
    assert "authoritative carrier" in prompt
    assert carrier["lifecycle_id"] in prompt
    assert carrier["identity"] == task_lifecycle.load_lifecycle(path)["identity"]
    if fresh:
        assert carrier["identity"]["task_id"] == "native-driver-42"
        assert "native-driver-42" in prompt



NOW = "2026-07-16T10:00:00Z"

def _lifecycle_file(tmp_path: Path, *, fresh: bool = False) -> Path:
    thread = (
        {"fresh_task_id": "native-driver-42", "lifecycle_state": "active"}
        if fresh else {
            "predecessor_task_id": "thread-old",
            "replacement_task_id": "thread-new",
            "lineage_id": "lineage-closeout",
            "generation": 1,
            "lifecycle_state": "confirmed",
        }
    )
    identity = task_identity.build_identity(
        repository="org/repo",
        stream_epic=10,
        stream_epic_url=None,
        github_issue_number=42,
        github_issue_url=None,
        semantic_title="Enforce task closeout",
        task_family="infrastructure",
        role="implementer",
        terminal_goal="merge",
        **thread,
    )
    body = "- [ ] **AC-IMPL** — Implementation is verified.\n"
    policy = {
        "AC-IMPL": {
            "due_state": "IMPLEMENTATION_READY",
            "required_evidence": ["test"],
        }
    }
    ledger = task_lifecycle.build_lifecycle(
        identity,
        author_family="codex",
        ac_snapshot=task_lifecycle.build_ac_snapshot(body, policy, finalized_at=NOW),
        required_checks=["CI Gate"],
        now=NOW,
    )
    path = tmp_path / "task-lifecycle.json"
    task_lifecycle.write_lifecycle(path, ledger)
    return path
