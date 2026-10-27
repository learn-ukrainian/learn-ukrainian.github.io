"""Bounded workers must pass sealed-envelope admission before any paid launch."""

import hashlib
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
    # Selection is side-effect free. Only the created-task spawn path records surfacing.
    assert surfaced == []
    delegate.surface_research({'task_id': 'task-9', 'research': state})
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


def test_dispatch_parses_max_budget_usd_flag():
    parser = cli.build_parser()
    args = parser.parse_args(
        [
            "dispatch",
            "--agent",
            "claude", "--model", "claude-opus-5-5",
            "--task-id",
            "budget-task",
            "--prompt",
            "hi",
            "--max-budget-usd",
            "0.50",
        ]
    )

    assert args.max_budget_usd == 0.5




def test_dispatch_persists_and_forwards_max_budget_usd(launch):
    """Ported from tests/test_delegate.py::test_dispatch_persists_and_forwards_max_budget_usd."""
    from scripts.dispatcher.providers import claude

    launch[launch.index('--agent') + 1] = 'claude'
    launch[launch.index('--model') + 1] = 'claude-opus-5-5'
    assert cli.main([*launch, '--max-budget-usd', '0.50']) == 0
    spec, state, _, _ = worker.start.call_args.args
    assert state['max_budget_usd'] == 0.5
    cmd = claude.build(spec, {}).argv
    assert '--max-budget-usd' in cmd
    assert cmd[cmd.index('--max-budget-usd') + 1] == '0.50'


def test_dispatch_records_the_effective_prompt_and_its_appended_blocks(launch, monkeypatch):
    """Ported from tests/test_delegate.py::test_dispatch_records_the_effective_prompt_and_its_appended_blocks."""
    launch[launch.index('--model') + 1] = 'gpt-6.1-sol'
    launch[launch.index('--prompt') + 1] = 'the source prompt'
    source = hashlib.sha256(b'the source prompt').hexdigest()
    for task_id in ('eff-plain', 'eff-ro'):
        launch[launch.index('--task-id') + 1] = task_id
        assert cli.main(launch) == 0
        spec, state, _, _ = worker.start.call_args.args
        assert state['prompt_sha256'] == source
        assert state['mode'] == 'read-only'
        assert state['prompt_blocks'] == ['rules_core']
        assert state['effective_prompt_sha256'] != source
        assert state['effective_prompt_sha256'] == hashlib.sha256(spec.prompt_file.read_bytes()).hexdigest()

    monkeypatch.setattr(prompt_context, '_load_task_lifecycle_carrier',
                        lambda raw: ({'lifecycle_id': 'L'}, '\n[lifecycle carrier]\n'))
    monkeypatch.setattr(prompt_context, '_build_research_context', lambda args: object())
    monkeypatch.setattr(prompt_context, '_resolve_research_injection',
                        lambda ctx, task_id: ('\n[research]\n', None))
    launch[launch.index('--task-id') + 1] = 'eff-all'
    assert cli.main(launch) == 0
    spec, state, _, _ = worker.start.call_args.args
    worker_prompt = spec.prompt_file.read_bytes().decode()
    assert state['prompt_sha256'] == source
    assert state['prompt_blocks'] == ['rules_core', 'lifecycle', 'research']
    assert state['effective_prompt_sha256'] == hashlib.sha256(worker_prompt.encode()).hexdigest()
    assert state['effective_prompt_sha256'] != source
    assert worker_prompt.startswith('<rules-core')
    assert 'the source prompt\n[lifecycle carrier]\n' in worker_prompt
    assert worker_prompt.endswith('\n[research]\n')
    assert state['task_lifecycle'] == {'lifecycle_id': 'L'}


# Consumption ports use v2-created task records and the unchanged record endpoint.
import os

from scripts.dispatcher.types import TaskSpec
from tests.test_research_registry_p3 import client
from tests.test_research_registry_p3 import emit_sink as emit_sink


@pytest.fixture
def task_store(tmp_path, monkeypatch):
    """Port of tests/test_research_registry_p3.py::task_store using schema-v2 records."""
    from scripts.api import delegate_router

    tasks_dir = tmp_path / 'tasks'
    monkeypatch.setenv('LU_TASKS_DIR', str(tasks_dir))
    monkeypatch.setattr(delegate_router, '_tasks_dir', lambda ctx=None: tasks_dir)

    def _put(task_id, *, status='spawning', pid=None):
        prompt = prompt_context._PromptPath(tasks_dir / (task_id + '.prompt'))
        prompt.content = b'the source prompt'
        spec = TaskSpec(task_id, 'codex', 'gpt-6.1-sol', None, 'read-only', tmp_path,
                        prompt, tasks_dir / (task_id + '.result'))
        record = store.new_record(spec, {'key': 'public', 'github': 'org/repo'}, 'codex/task',
                                  'a' * 40, {'research_owned_path': []})
        record.update(status=status, pid=pid, process_start=worker._identity(pid))
        store.create(record, prompt.content)

    return _put


def test_valid_active_task_emits_consumption_on_200(reg_root, emit_sink, task_store):
    _write_registry(reg_root, [_make_record(reg_root, "r1")])
    task_store("job-1", status="spawning", pid=os.getpid())
    resp = client.get("/api/knowledge/record/r1", params={"task": "job-1"})
    assert resp.status_code == 200
    consumed = [p for t, p in emit_sink if t == consumption.CONSUMED_EVENT]
    assert consumed == [{"task_id": "job-1", "research_id": "r1", "surface": "record", "status": 200}]



def test_cache_backed_304_emits_consumption_after_prior_200(reg_root, emit_sink, task_store):
    # ADR-011 P3: a 304 only counts as consumption when this task already has
    # evidence of a matching prior 200 for this exact record.
    _write_registry(reg_root, [_make_record(reg_root, "r1")])
    task_store("job-1", pid=os.getpid())
    first = client.get("/api/knowledge/record/r1", params={"task": "job-1"})
    etag = first.headers["ETag"]
    resp = client.get(
        "/api/knowledge/record/r1", params={"task": "job-1"}, headers={"If-None-Match": etag}
    )
    assert resp.status_code == 304
    consumed = [p for t, p in emit_sink if t == consumption.CONSUMED_EVENT]
    assert [c["status"] for c in consumed] == [200, 304]



def test_manufactured_304_without_prior_fetch_emits_nothing(reg_root, emit_sink, task_store):
    # A caller can learn a record's content_hash/ETag from the public filtered
    # manifest/pointer projection WITHOUT ever fetching the body. Replaying that
    # publicly-known ETag as If-None-Match under an active task must not
    # manufacture a consumption event — there is no proof the task ever consumed
    # the body. The HTTP response (304) is unaffected regardless of attribution.
    _write_registry(reg_root, [_make_record(reg_root, "r1")])
    task_store("job-1", pid=os.getpid())
    etag = client.get("/api/knowledge/record/r1").headers["ETag"]  # unattributed fetch
    resp = client.get(
        "/api/knowledge/record/r1", params={"task": "job-1"}, headers={"If-None-Match": etag}
    )
    assert resp.status_code == 304
    assert not [p for t, p in emit_sink if t == consumption.CONSUMED_EVENT]



def test_404_is_never_consumption(reg_root, emit_sink, task_store):
    _write_registry(reg_root, [_make_record(reg_root, "r1")])
    task_store("job-1", pid=os.getpid())
    resp = client.get("/api/knowledge/record/does-not-exist", params={"task": "job-1"})
    assert resp.status_code == 404
    assert not [p for t, p in emit_sink if t == consumption.CONSUMED_EVENT]


@pytest.mark.parametrize("boundary", ["dry-run", "resources", "family", "target-moved", "canonical-origin", "spawn"])
def test_research_surfacing_never_precedes_task_creation(reg_root, monkeypatch, boundary):
    """Defect class: refused admissions emit surfaced-pointer events for nonexistent tasks."""
    from scripts.dispatcher import admission, authoring

    tasks = reg_root / "tasks"
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    monkeypatch.setattr(prompt_context, "_REPO_ROOT", reg_root)
    _write_registry(reg_root, [_make_record(reg_root, "cefr", routing={"roles": ["quality"]})])
    monkeypatch.setattr(git, "resolve_repo", lambda _: (reg_root, dict(key="public", github="example/public")))
    monkeypatch.setattr(git, "worktree_plan", lambda *a: (reg_root, "codex/worker", "a" * 40))
    monkeypatch.setattr(git, "create_worktree", Mock())
    monkeypatch.setattr(authoring, "admit", Mock(return_value=None))
    monkeypatch.setattr(authoring, "recheck", Mock(return_value=None))
    monkeypatch.setattr(checks, "check_resources", Mock())
    monkeypatch.setattr(admission, "spawn_supervisor", Mock(side_effect=OSError("fixture spawn stop")))
    events = []
    monkeypatch.setattr(consumption, "emit_event", lambda t, p, **kw: events.append(
        (t, p, store.record_path("worker").is_file())))
    flags = []
    if boundary == "dry-run":
        flags += ["--dry-run"]
    elif boundary == "resources":
        monkeypatch.setattr(checks, "check_resources", Mock(side_effect=ValueError("fixture resources refusal")))
    elif boundary == "family":
        flags += ["--review-author-model", "gpt-6.1-sol"]
    elif boundary == "target-moved":
        monkeypatch.setattr(authoring, "recheck", Mock(side_effect=ValueError("fixture target moved")))
    elif boundary == "canonical-origin":
        flags += ["--mode", "workspace-write", "--owned-path", "docs/example.md"]
    assert cli.main(["dispatch", "--agent", "sol", "--model", "gpt-6.1-sol", "--task-id", "worker",
                     "--prompt", "Inspect the document", "--research-role", "quality", *flags]) == (
                         0 if boundary == "dry-run" else 2)
    if boundary == "spawn":
        assert events == [(consumption.SURFACED_EVENT,
                           {"task_id": "worker", "research_id": "cefr", "surface": "dispatch"}, True)]
        assert store.read("worker")["status"] == "crashed"
    else:
        assert events == []
        assert not store.record_path("worker").exists()
