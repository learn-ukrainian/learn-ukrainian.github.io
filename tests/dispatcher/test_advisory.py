"""Bounded workers must pass sealed-envelope admission before any paid launch."""

import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from scripts.agent_runtime import bounded_advisory as advisory
from scripts.dispatcher import checks, cli, git, store, worker

_START = worker.start


@pytest.fixture
def launch(tmp_path, monkeypatch):
    (tmp_path / "docs").mkdir()
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    monkeypatch.setattr(git, "resolve_repo", lambda _: (tmp_path, dict(key="public", github="example/public")))
    monkeypatch.setattr(git, "worktree_plan", lambda *a: (tmp_path, "codex/worker", "a" * 40))
    monkeypatch.setattr(git, "create_worktree", Mock())
    monkeypatch.setattr(checks, "check_resources", lambda _: None)
    real_popen = subprocess.Popen

    def detach(argv, *a, **kw):
        if "scripts.dispatcher.worker" in argv:
            return SimpleNamespace(pid=os.getpid(), stdin=SimpleNamespace(write=lambda data: None, close=lambda: None))
        return real_popen(argv, *a, **kw)

    monkeypatch.setattr(worker.subprocess, "Popen", detach)
    monkeypatch.setattr(worker, "start", Mock(side_effect=_START))
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
def test_driver_brief_exception_requires_acceptance_command(launch, complete, capsys, tmp_path, model, monkeypatch):
    """Defect class: concrete or alias models bypass brief validation or reject valid bounded implementation."""
    if model != "gpt-6-luna":
        launch[launch.index("--agent") + 1] = "claude"
    launch[launch.index("--model") + 1] = model
    launch += ["--research-role", "implementation", "--research-task-family", "bounded_implementation",
               "--mode", "workspace-write"]
    (tmp_path / "docs/example.md").write_text("Assigned document")
    for command in (("init",), ("remote", "add", "origin", "git@github.com:example/public.git"),
                    ("-c", "user.name=Stub", "-c", "user.email=stub@example.invalid",
                                "commit", "--allow-empty", "-m", "fixture")):
        subprocess.run(["git", "-C", str(tmp_path), *command], check=True, capture_output=True, timeout=30)
    head = subprocess.run(["git", "-C", str(tmp_path), "rev-parse", "HEAD"], check=True,
                          capture_output=True, text=True, timeout=30).stdout.strip()
    monkeypatch.setattr(git, "worktree_plan", lambda *a: (tmp_path, "codex/worker", head))
    if complete:
        launch += ["--verify-command", "test -f docs/example.md"]
    assert cli.main(launch) == (0 if complete else 2)
    if complete:
        assert store.read("worker")["driver_brief"]["owned_paths"] == ["docs/example.md"]
    else:
        assert "BOUNDED_DRIVER_BRIEF_REFUSED" in capsys.readouterr().err
        worker.start.assert_not_called()


# The tests below are ports of the identically named legacy tests in
# tests/test_delegate_bounded_advisory.py. The legacy suite remains unchanged.
def _write_advisor(launch, capsys, **overrides):
    assert cli.main([*launch, "--print-advisory-binding"]) == 0
    binding = capsys.readouterr().out.strip()
    envelope = dict(task_contract="Inspect assigned paths", owned_paths=["docs/example.md"],
                    max_changed_files=2, max_non_test_loc=10, constraints=["Stay in scope"],
                    risk_boundaries=["No security changes"], acceptance_evidence=["Report findings"],
                    escalation_triggers=["Scope ambiguity"], dispatch_args_sha256=binding)
    envelope.update(overrides)
    response = "```advisory-envelope\n" + json.dumps(envelope) + "\n```\n"
    path = store.record_path("advisor")
    path.parent.mkdir(exist_ok=True)
    path.with_suffix(".result").write_text(response)
    policy = advisory.bounded_execution_policy()
    record = dict(task_id="advisor", status="done", mode="read-only", model=policy.advisor_model_id,
                  advisory_role=policy.advisor_role, advisory_route=advisory.ADVISOR_ROUTE,
                  advisory_binding_sha256=binding, result_file=str(path.with_suffix(".result")), run_nonce="advisor-run",
                  advisory_seal=advisory.seal_advisor_result(response, model=policy.advisor_model_id, run_nonce="advisor-run"))
    path.write_text(json.dumps(record))
    return binding, envelope, response


@pytest.fixture
def runtime(launch, tmp_path, tmp_path_factory, monkeypatch):
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(tmp_path_factory.mktemp("bounded-scratch")))
    def run_git(*args):
        return subprocess.run(["git", "-C", str(tmp_path), *args], check=True,
                              capture_output=True, text=True, timeout=30).stdout.strip()

    (tmp_path / ".gitignore").write_text("tasks/\ngithub-cache/\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "docs/seed.md").write_text("seed\n")
    run_git("init", "-b", "codex/worker")
    run_git("config", "user.name", "Stub")
    run_git("config", "user.email", "stub@example.invalid")
    run_git("add", ".")
    run_git("commit", "-m", "fixture")
    base = run_git("rev-parse", "HEAD")
    remote = tmp_path_factory.mktemp("bounded-remote") / "origin.git"
    run_git("init", "--bare", str(remote))
    run_git("remote", "add", "origin", str(remote))
    run_git("push", "origin", "HEAD:main", "HEAD:codex/worker")
    monkeypatch.setattr(git, "resolve_repo", lambda _: (tmp_path, dict(key="public", github=str(remote), transport="file")))
    monkeypatch.setattr(git, "worktree_plan", lambda *a: (tmp_path, "codex/worker", base))
    monkeypatch.setattr(worker.signal, "signal", lambda *a: None)
    monkeypatch.setattr(worker.signal, "pthread_sigmask", lambda *a: None)
    monkeypatch.setattr(worker, "_reap_settled", lambda *a: None)
    box = SimpleNamespace(response="Committed and pushed the change.", calls=[], submitted=[], run_git=run_git, on_execute=None)

    def build(spec, env):
        from scripts.dispatcher.types import Invocation
        return Invocation(["unit-c-provider"], spec.prompt_file.read_bytes(), env, None)

    from scripts.dispatcher.types import ParsedResult
    box.provider = SimpleNamespace(build=Mock(side_effect=build),
                                   parse=lambda *a: ParsedResult(box.response, None, None))
    monkeypatch.setattr(worker.providers, "load", lambda _: box.provider)
    real_popen = subprocess.Popen

    def popen(argv, *args, **kw):
        if argv != ["unit-c-provider"]:
            return real_popen(argv, *args, **kw)
        box.calls.append(argv)
        def communicate(data, **kw):
            box.submitted.append(data)
            if box.on_execute:
                box.on_execute()

        return SimpleNamespace(returncode=0, communicate=communicate)

    monkeypatch.setattr(worker.subprocess, "Popen", popen)

    def settle(options=None, timeout=None):
        spec, _record, _prompt, hard_timeout = worker.start.call_args.args
        path = store.record_path(spec.task_id)
        (path.parent / "logs").mkdir(exist_ok=True)
        worker.supervise(path, options if options is not None else spec.options,
                         hard_timeout if timeout is None else timeout)
        return store.read(spec.task_id)

    box.settle = settle
    return box


def _admit(launch, capsys, **overrides):
    _write_advisor(launch, capsys, **overrides)
    assert cli.main([*launch, "--advisory-task", "advisor"]) == 0, capsys.readouterr().err
    return store.read("worker")


def _run_bounded_worker(launch, capsys, runtime, tmp_path, files):
    launch += ["--mode", "workspace-write", "--owned-path", "docs/", "--owned-path", "tests/"]
    # Remove the narrower scope inherited from the launch fixture.
    index = launch.index("--owned-path")
    del launch[index:index + 2]
    _admit(launch, capsys, owned_paths=["docs/", "tests/"])
    def execute():
        for name, content in files.items():
            path = tmp_path / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        runtime.run_git("add", ".")
        runtime.run_git("commit", "-m", "worker change")
        runtime.run_git("push", "origin", "HEAD")

    runtime.on_execute = execute
    return runtime.settle()


def test_advisor_dispatch_records_role_binding_and_output_contract(launch, capsys):
    launch[launch.index("--model") + 1] = "gpt-6.1-sol"
    assert cli.main([*launch, "--advisory-role", "bounded_advisory_envelope",
                     "--advisory-binding", "a" * 64]) == 0
    record = store.read("worker")
    assert record["advisory_role"] == "bounded_advisory_envelope"
    assert record["advisory_route"] == "execution_routing.sol_advised_bounded.advisor"
    assert record["advisory_binding_sha256"] == "a" * 64
    assert "advisory_contract" in record["prompt_blocks"]
    prompt = Path(record["prompt_file"]).read_text()
    assert "```advisory-envelope" not in prompt and "`advisory-envelope`" in prompt
    assert "a" * 64 in prompt


@pytest.mark.parametrize("extra,model,code", [
    (["--advisory-role", "bounded_advisory_envelope", "--advisory-binding", "a" * 64], "gpt-6-luna", advisory.ADVISOR_ROUTE_REFUSED),
    (["--advisory-role", "bounded_advisory_envelope"], "gpt-6.1-sol", advisory.FLAG_CONFLICT),
    (["--advisory-binding", "a" * 64], "gpt-6.1-sol", advisory.FLAG_CONFLICT),
    (["--advisory-role", "bounded_advisory_envelope", "--advisory-binding", "XYZ"], "gpt-6.1-sol", advisory.FLAG_CONFLICT),
    (["--advisory-role", "bounded_advisory_envelope", "--advisory-binding", "a" * 64, "--advisory-task", "x"], "gpt-6.1-sol", advisory.FLAG_CONFLICT),
])
def test_advisor_flags_are_refused_when_inconsistent(launch, capsys, extra, model, code):
    launch[launch.index("--model") + 1] = model
    assert cli.main([*launch, *extra]) == 2
    assert code in capsys.readouterr().err
    worker.start.assert_not_called()
    git.create_worktree.assert_not_called()


def test_advisor_must_run_read_only(launch, capsys):
    launch[launch.index("--model") + 1] = "gpt-6.1-sol"
    assert cli.main([*launch, "--mode", "workspace-write", "--advisory-role", "bounded_advisory_envelope",
                     "--advisory-binding", "a" * 64]) == 2
    assert "ADVISORY_ROLE_REFUSED: the advisor runs read-only, not workspace-write" in capsys.readouterr().err
    worker.start.assert_not_called()


def test_b3_the_advisor_worker_seals_its_result_at_finish_and_admission_checks_it(launch, runtime, capsys, tmp_path):
    binding, envelope, response = _write_advisor(launch, capsys)
    runtime.response = response
    advisor_launch = list(launch)
    advisor_launch[advisor_launch.index("--model") + 1] = "gpt-6.1-sol"
    advisor_launch[advisor_launch.index("--task-id") + 1] = "producer"
    assert cli.main([*advisor_launch, "--advisory-role", "bounded_advisory_envelope", "--advisory-binding", binding]) == 0
    record = runtime.settle()
    assert record["status"] == "done"
    assert record["advisory_seal"] == dict(result_sha256=store.digest(response.encode()),
                                          envelope_sha256=advisory.envelope_sha256(envelope),
                                          advisor_model="gpt-6.1-sol", run_nonce=record["run_nonce"])
    loaded = advisory.load_envelope("producer", state_path=store.record_path("producer"),
                                    binding_sha256=binding, repo_root=tmp_path)
    assert loaded.envelope["max_changed_files"] == 2
    assert cli.main([*launch, "--advisory-task", "producer"]) == 0
    worker_record = runtime.settle()
    assert worker_record["status"] == "done"
    assert worker_record["advisory_prompt_sha256"] == store.digest(runtime.submitted[-1])
    store.record_path("producer").with_suffix(".result").write_text(response + "changed")
    with pytest.raises(advisory.AdvisoryRefused, match=advisory.SEAL_MISMATCH):
        advisory.load_envelope("producer", state_path=store.record_path("producer"),
                               binding_sha256=binding, repo_root=tmp_path)


def test_b3_a_non_advisor_worker_records_no_seal(launch, runtime, monkeypatch):
    from scripts.dispatcher import advisory as wiring

    launch[launch.index("--model") + 1] = "gpt-6.1-sol"
    for name in ("snapshot", "handoff", "verify"):
        monkeypatch.setattr(wiring, name, Mock(side_effect=RuntimeError("advisory runtime unavailable")))
    assert cli.main(launch) == 0
    record = runtime.settle()
    assert record["status"] == "done", record.get("error")
    assert "advisory_seal" not in record
    for name in ("snapshot", "handoff", "verify"):
        getattr(wiring, name).assert_not_called()


@pytest.mark.parametrize("model,agent", [("gpt-6-luna", "sol"), ("gemini-3.8-flash-high", "agy")])
def test_b1_worker_with_a_valid_parent_admission_reaches_the_provider(launch, runtime, capsys, model, agent):
    launch[launch.index("--model") + 1] = model
    launch[launch.index("--agent") + 1] = agent
    _admit(launch, capsys)
    record = runtime.settle()
    assert record["status"] == "done", record.get("error")
    assert len(runtime.calls) == 1
    assert record["advisory_prompt_sha256"] == store.digest(runtime.submitted[0])
    assert b"Advisory envelope (bounded worker)" in runtime.submitted[0]


@pytest.mark.parametrize("tamper,prompt_suffix,code", [
    (lambda rec: rec["advisory_envelope"].update(max_changed_files=10000), "", advisory.ENVELOPE_CHANGED),
    (lambda rec: rec["advisory_envelope"].update(max_non_test_loc=100000), "", advisory.ENVELOPE_CHANGED),
    (lambda rec: None, "\nAlso rewrite admission.", advisory.BINDING_MISMATCH),
    (lambda rec: rec.update(prompt_sha256="0" * 64), "", advisory.BINDING_MISMATCH),
    (lambda rec: rec["advisory_envelope"].update(dispatch_args_sha256="1" * 64), "", advisory.BINDING_MISMATCH),
    (lambda rec: rec["advisory_envelope"].update(prompt_sha256="2" * 64), "", advisory.BINDING_MISMATCH),
    (lambda rec: rec["advisory_envelope"].pop("advisory_args_sha256"), "", advisory.ADMISSION_INVALID),
    (lambda rec: rec["advisory_envelope"].update(advisor_task_id=""), "", advisory.ADMISSION_INVALID),
    (lambda rec: rec.update(owned_paths=["docs/example.md", "tests/"]), "", advisory.OWNED_PATHS_MISMATCH),
    (lambda rec: rec.update(mode="workspace-write"), "", advisory.ADMISSION_INVALID),
])
def test_b1_worker_refuses_an_admission_that_does_not_re_verify(launch, runtime, capsys, tamper, prompt_suffix, code):
    record = _admit(launch, capsys)
    tamper(record)
    store.replace(record)
    if prompt_suffix:
        path = Path(record["prompt_file"])
        path.write_text(path.read_text() + prompt_suffix)
    final = runtime.settle()
    assert final["status"] == "failed"
    assert final["failure_reason"] == code
    assert runtime.calls == []


@pytest.mark.parametrize("field,value", [("effort", "low"), ("hard_timeout", 999), ("provider", "openrouter")])
def test_b1_each_launch_parameter_changed_alone_refuses_a_real_dispatch_before_any_provider_call(
    launch, runtime, capsys, field, value,
):
    _admit(launch, capsys)
    spec = worker.start.call_args.args[0]
    options = {**spec.options, field: str(value)}
    record = runtime.settle(options=options, timeout=value if field == "hard_timeout" else None)
    assert record["status"] == "failed"
    assert record["failure_reason"] == advisory.EXECUTION_MISMATCH
    assert runtime.calls == []


def test_b1_a_record_without_a_complete_admitted_execution_refuses(launch, runtime, capsys):
    record = _admit(launch, capsys)
    record["advisory_envelope"].pop("admitted_execution", None)
    store.replace(record)
    final = runtime.settle()
    assert final["status"] == "failed"
    assert final["failure_reason"] == advisory.ADMISSION_INVALID
    assert runtime.calls == []
    record.pop("advisory_envelope")
    record.update(advisory_required=False, status="spawning")
    store.replace(record)
    final = runtime.settle()
    assert final["status"] == "failed"
    assert final["failure_reason"] == advisory.ADMISSION_MISSING
    assert runtime.calls == []


@pytest.mark.parametrize("advisor,code", [
    ({"status": "failed"}, advisory.TASK_NOT_DONE), ({"status": "running"}, advisory.TASK_NOT_DONE),
    ("missing", advisory.TASK_NOT_FOUND), ("malformed", advisory.SEAL_MISMATCH),
    ("result-and-record-digest", advisory.SEAL_MISMATCH),
])
def test_b1_missing_unfinished_or_changed_advisor_evidence_refuses_at_the_worker(launch, runtime, capsys, advisor, code):
    record = _admit(launch, capsys)
    path = store.record_path("advisor")
    if advisor == "missing":
        path.unlink()
    elif isinstance(advisor, dict):
        path.write_text(json.dumps({**json.loads(path.read_text()), **advisor}))
    else:
        result = path.with_suffix(".result")
        result.write_text(result.read_text() + "changed")
        if advisor == "result-and-record-digest":
            record["advisory_envelope"]["result_sha256"] = store.digest(result.read_bytes())
            store.replace(record)
    final = runtime.settle()
    assert final["status"] == "failed"
    assert final["failure_reason"] == code
    assert runtime.calls == []


def test_m12_worker_exceeding_envelope_ceilings_is_a_typed_failure(launch, runtime, capsys, tmp_path):
    state = _run_bounded_worker(launch, capsys, runtime, tmp_path,
                               {"docs/a.py": "x = 1\n" * 8, "docs/b.py": "y = 2\n" * 8,
                                "tests/test_a.py": "assert True\n" * 50})
    assert state["status"] == "failed"
    assert state["failure_reason"] == advisory.CEILING_EXCEEDED
    check = state["advisory_ceiling_check"]
    assert (check["changed_files"], check["non_test_loc"]) == (3, 16)
    assert check["exceeded"] == ["changed_files 3 > max_changed_files 2", "non_test_loc 16 > max_non_test_loc 10"]
    assert state["last_error"].startswith(advisory.CEILING_EXCEEDED)


def test_m13_worker_within_envelope_ceilings_settles_done(launch, runtime, capsys, tmp_path):
    state = _run_bounded_worker(launch, capsys, runtime, tmp_path,
                               {"docs/a.py": "x = 1\n" * 4, "tests/test_a.py": "ok\n" * 90})
    assert state["status"] == "done", state.get("error")
    assert state["advisory_ceiling_check"]["exceeded"] == []
    assert state["advisory_ceiling_check"]["non_test_loc"] == 4


def test_m13_worker_exactly_at_both_ceilings_settles_done(launch, runtime, capsys, tmp_path):
    state = _run_bounded_worker(launch, capsys, runtime, tmp_path,
                               {"docs/a.py": "x = 1\n" * 6, "docs/b.py": "y = 2\n" * 4})
    assert state["status"] == "done", state.get("error")
    check = state["advisory_ceiling_check"]
    assert (check["changed_files"], check["non_test_loc"], check["exceeded"]) == (2, 10, [])


@pytest.mark.parametrize("files,exceeded", [
    ({"docs/a.py": "x = 1\n", "docs/b.py": "y = 2\n", "tests/test_a.py": "ok\n"},
     ["changed_files 3 > max_changed_files 2"]),
    ({"docs/a.py": "x = 1\n" * 11}, ["non_test_loc 11 > max_non_test_loc 10"]),
])
def test_m12_exceeding_either_ceiling_alone_is_a_typed_failure(launch, runtime, capsys, tmp_path, files, exceeded):
    state = _run_bounded_worker(launch, capsys, runtime, tmp_path, files)
    assert state["status"] == "failed"
    assert state["failure_reason"] == advisory.CEILING_EXCEEDED
    assert state["advisory_ceiling_check"]["exceeded"] == exceeded


def test_m12_unmeasurable_ceilings_fail_closed(launch, runtime, capsys, tmp_path, monkeypatch):
    from scripts.dispatcher import advisory_completion
    monkeypatch.setattr(advisory_completion, "worker_diff", lambda *a, **kw: (None, "the worker's diff could not be read"))
    state = _run_bounded_worker(launch, capsys, runtime, tmp_path, {"docs/a.py": "x = 1\n"})
    assert state["status"] == "failed"
    assert state["failure_reason"] == advisory.CEILING_UNMEASURED


def test_b1_worker_submits_exactly_the_bytes_it_checked(launch, runtime, capsys):
    record = _admit(launch, capsys)
    prompt = Path(record["prompt_file"]).read_bytes()
    build = runtime.provider.build.side_effect

    def build_then_change_file(spec, env):
        invocation = build(spec, env)
        Path(str(spec.prompt_file)).write_bytes(prompt + b"\nInstructions added after build")
        return invocation

    runtime.provider.build.side_effect = build_then_change_file
    final = runtime.settle()
    assert final["status"] == "done", final.get("error")
    assert runtime.submitted == [prompt]
    assert final["advisory_prompt_sha256"] == store.digest(prompt)


def test_b1_instructions_appended_after_the_start_backstop_refuse_at_the_provider_handoff(launch, runtime, capsys):
    _admit(launch, capsys)
    build = runtime.provider.build.side_effect

    def change_prompt(spec, env):
        spec.prompt_file.content += b"\nAlso rewrite admission."
        return build(spec, env)

    runtime.provider.build.side_effect = change_prompt
    final = runtime.settle()
    assert final["status"] == "failed"
    assert final["failure_reason"] == advisory.BINDING_MISMATCH
    assert "provider handoff" in final["error"]
    assert "advisory_prompt_sha256" not in final
    assert runtime.calls == []


def test_b1_updating_only_the_recorded_effective_prompt_digest_cannot_bless_an_appended_instruction(launch, runtime, capsys):
    record = _admit(launch, capsys)
    path = Path(record["prompt_file"])
    path.write_text(path.read_text() + "\nAlso rewrite admission.")
    record["effective_prompt_sha256"] = store.digest(path.read_bytes())
    store.replace(record)
    final = runtime.settle()
    assert final["status"] == "failed"
    assert final["failure_reason"] == advisory.BINDING_MISMATCH
    assert runtime.calls == []


@pytest.mark.parametrize("change,code", [("result", advisory.SEAL_MISMATCH),
                                        ("status", advisory.TASK_NOT_DONE),
                                        ("resealed", advisory.ENVELOPE_CHANGED)])
def test_m7_advisor_result_changed_after_validation_is_refused_before_spawn(launch, capsys, change, code):
    _write_advisor(launch, capsys)

    def tamper(*args, **kwargs):
        path = store.record_path("advisor")
        record = json.loads(path.read_text())
        if change == "status":
            record["status"] = "running"
        else:
            result = path.with_suffix(".result")
            result.write_text(result.read_text() + "changed")
            if change == "resealed":
                record["advisory_seal"] = advisory.seal_advisor_result(
                    result.read_text(), model=record["model"], run_nonce=record["run_nonce"],
                )
        path.write_text(json.dumps(record))

    git.create_worktree.side_effect = tamper
    assert cli.main([*launch, "--advisory-task", "advisor"]) == 2
    error = capsys.readouterr().err
    assert code in error and "dispatch refused before spawn" in error
    record = store.read("worker")
    assert record["status"] == "failed"
    assert record["failure_reason"] == code
    assert record["returncode_reason"] == "advisory envelope changed before spawn; worker not started"


@pytest.mark.parametrize("agent,model", [("sol", "gpt-6-luna"), ("claude", "claude-haiku-5-5")])
def test_driver_brief_normal_dispatch_and_replay(launch, runtime, capsys, agent, model):
    launch[launch.index("--agent") + 1] = agent
    launch[launch.index("--model") + 1] = model
    assert cli.main([*launch, "--research-role", "recon", "--research-task-family", "readonly_recon",
                     "--verify-command", "test -d docs", "--initiator", "infra-driver"]) == 0
    record = runtime.settle()
    brief = record["driver_brief"]
    assert record["status"] == "done", record.get("error")
    assert brief["driver"] == {"identity": "infra-driver", "source": "explicit"}
    assert brief["prompt_sha256"] == store.digest(b"Inspect the assigned document")
    assert brief["owned_paths"] == ["docs/example.md"]
    assert "advisory_envelope" not in record
    assert b"Run and report: test -d docs" in runtime.submitted[0]
    assert record["advisory_prompt_sha256"] == store.digest(runtime.submitted[0])
    record.pop("driver_brief")
    record["status"] = "spawning"
    store.replace(record)
    refused = runtime.settle()
    assert refused["status"] == "failed"
    assert refused["failure_reason"] == advisory.ADMISSION_MISSING
    assert len(runtime.calls) == 1


def _exempt_writer_run(launch, runtime, tmp_path, files):
    launch[launch.index("--agent") + 1] = "agy"
    launch[launch.index("--model") + 1] = "gemini-3.8-flash-high"
    launch[launch.index("--owned-path") + 1] = "docs/"
    assert cli.main([*launch, "--mode", "workspace-write", "--research-task-family", "ukrainian-authoring"]) == 0
    def execute():
        for name, content in files.items():
            (tmp_path / name).write_text(content)
        runtime.run_git("add", ".")
        runtime.run_git("commit", "-m", "worker change")
        runtime.run_git("push", "origin", "HEAD")

    runtime.on_execute = execute
    return runtime.settle()


def test_b3_reviewer_probe_a_content_exempt_worker_adding_code_is_a_typed_failure(launch, runtime, tmp_path):
    state = _exempt_writer_run(launch, runtime, tmp_path,
                               {"docs/generate.py": "print('lesson')\n", "docs/lesson-1.md": "# Lesson\n"})
    assert state["status"] == "failed"
    assert state["failure_reason"] == advisory.EXEMPT_CODE_CHANGE
    check = state["advisory_exempt_change_check"]
    assert check["changed_paths"] == ["docs/generate.py", "docs/lesson-1.md"]
    assert check["problems"] == ["'docs/generate.py', which is a code file"]
    assert state["last_error"].startswith(advisory.EXEMPT_CODE_CHANGE)


def test_b3_a_content_only_diff_in_the_same_directory_settles_done(launch, runtime, tmp_path):
    state = _exempt_writer_run(launch, runtime, tmp_path, {"docs/lesson-1.md": "# Lesson\n", "docs/l.yaml": "a: 1\n"})
    assert state["status"] == "done", state.get("error")
    assert state["advisory_exempt_change_check"]["problems"] == []


def test_b3_unreadable_exempt_changes_fail_closed(launch, runtime, tmp_path, monkeypatch):
    from scripts.dispatcher import advisory_completion

    monkeypatch.setattr(advisory_completion, "worker_diff", lambda *a, **kw: (None, "unreadable"))
    state = _exempt_writer_run(launch, runtime, tmp_path, {"docs/lesson-1.md": "# Lesson\n"})
    assert state["status"] == "failed"
    assert state["failure_reason"] == advisory.EXEMPT_CHANGES_UNMEASURED


def test_existing_haiku_routine_mechanical_dispatch_needs_no_new_brief_contract(launch, runtime, capsys):
    launch[launch.index("--agent") + 1] = "claude"
    launch[launch.index("--model") + 1] = "claude-haiku-5-5"
    assert cli.main([*launch, "--research-task-family", "routine_mechanical"]) == 0, capsys.readouterr().err
    record = runtime.settle()
    assert record["status"] == "done", record.get("error")
    assert "driver_brief" not in record and "advisory_envelope" not in record
    assert "advisory_prompt_sha256" not in record
    assert len(runtime.calls) == 1


@pytest.mark.parametrize("model,agent", [("gpt-6-luna", "sol"), ("claude-haiku-5-5", "claude")])
@pytest.mark.parametrize("flag", ["--owned-path", "--research-owned-path"])
def test_explicit_bounded_envelope_retains_security_path_refusal(launch, runtime, capsys, model, agent, flag):
    """Ported from tests/test_delegate_bounded_advisory.py::test_explicit_bounded_envelope_retains_security_path_refusal."""
    launch[launch.index("--agent") + 1] = agent
    launch[launch.index("--model") + 1] = model
    owned = "scripts/agent_runtime/new_gate.py" if flag == "--owned-path" else "docs/example.md"
    launch[launch.index("--owned-path") + 1] = owned
    launch += ["--mode", "workspace-write", "--research-task-family", "bounded_implementation",
               "--research-role", "implementation"]
    if flag == "--research-owned-path":
        launch += [flag, "scripts/agent_runtime/new_gate.py"]
    _write_advisor(launch, capsys, owned_paths=[owned])
    assert cli.main([*launch, "--advisory-task", "advisor"]) == 2
    assert "MECHANICAL_TASK_REFUSED: security-sensitive" in capsys.readouterr().err
    worker.start.assert_not_called()
    git.create_worktree.assert_not_called()
    assert not store.record_path("worker").exists()


@pytest.mark.parametrize("role", ["driver", "security", "review", "security_code", "ukrainian_authoring", "formal-review", "design_approval",
                                  "consult", "consultation", "advice", "adviser"])
def test_luna_free_form_roles_do_not_authorize_excluded_activity_classes(launch, capsys, role):
    """Ported from tests/agent_runtime/test_mechanical_admission.py::test_luna_free_form_roles_do_not_authorize_excluded_activity_classes."""
    launch += ["--research-role", role]
    _write_advisor(launch, capsys)
    assert cli.main([*launch, "--advisory-task", "advisor"]) == 2
    assert "MECHANICAL_TASK_REFUSED: bounded workers cannot take" in capsys.readouterr().err
    worker.start.assert_not_called()
    git.create_worktree.assert_not_called()
    assert not store.record_path("worker").exists()


@pytest.mark.parametrize("extra,reason", [
    ([], "catalog-eligible"),
    (["--research-task-family", "routine_mechanical", "--prompt", "Напиши текст"], "task prompt"),
    (["--research-task-family", "routine_mechanical", "--owned-path", "curriculum/a1/item.md"], "Ukrainian"),
    (["--research-task-family", "routine_mechanical", "--require-review-verdict", "--mode", "read-only"], "review"),
])
def test_excluded_work_refuses_before_routing(launch, runtime, capsys, extra, reason):
    """Ported from tests/agent_runtime/test_mechanical_admission.py::test_excluded_work_refuses_before_routing."""
    launch[launch.index("--agent") + 1] = "claude"
    launch[launch.index("--model") + 1] = "claude-haiku-5-5"
    assert cli.main([*launch, "--mode", "workspace-write", *extra]) == 2
    error = capsys.readouterr().err
    assert "MECHANICAL_TASK_REFUSED" in error and reason in error
    worker.start.assert_not_called()
    git.create_worktree.assert_not_called()
    assert not store.record_path("worker").exists()


@pytest.mark.parametrize("change", ["missing-family", "classification-write", "tampered-family", "tampered-mode"])
def test_worker_refuses_invalid_or_tampered_record_with_typed_terminal_cause(launch, runtime, capsys, change):
    """Ported from tests/test_delegate_mechanical_worker_admission.py::test_worker_refuses_invalid_or_tampered_record_with_typed_terminal_cause."""
    from scripts.agent_runtime.target_admission import mechanical_scope_digest

    launch[launch.index("--agent") + 1] = "claude"
    launch[launch.index("--model") + 1] = "claude-haiku-5-5"
    assert cli.main([*launch, "--research-task-family", "routine_mechanical"]) == 0, capsys.readouterr().err
    record = store.read("worker")
    scope = record["mechanical_task"]
    assert scope["sha256"] == mechanical_scope_digest(scope)
    if change == "missing-family":
        record.pop("mechanical_task")
    elif change == "classification-write":
        record["mode"] = scope["mode"] = "workspace-write"
        scope["family"] = "mechanical_classification"
        scope["sha256"] = mechanical_scope_digest(scope)
    elif change == "tampered-mode":
        record["mode"] = "workspace-write"
    else:
        scope["family"] = "readonly_recon"
    store.replace(record)
    terminal = runtime.settle()
    assert terminal["status"] == "failed"
    assert terminal["failure_reason"] == terminal["last_error"] == "mechanical_admission_refused"
    assert terminal["returncode_reason"] == "mechanical_admission_refused"
    assert terminal["finished_at"] and terminal["stderr_excerpt"].startswith("MECHANICAL_TASK_REFUSED:")
    assert runtime.calls == []
