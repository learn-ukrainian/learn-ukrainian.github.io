"""Schema loss, unsafe bindings and invalid final output must fail closed."""

import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from scripts.dispatcher import checks, cli, git, store, worker
from scripts.dispatcher.providers import codex


@pytest.fixture
def dispatch(tmp_path, monkeypatch):
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    monkeypatch.setattr(git, "resolve_repo", lambda _: (tmp_path, dict(key="public", github="example/public")))
    monkeypatch.setattr(git, "worktree_plan", lambda *a: (tmp_path, "codex/schema", "a" * 40))
    monkeypatch.setattr(git, "create_worktree", Mock())
    monkeypatch.setattr(checks, "check_resources", lambda _: None)
    start = Mock(side_effect=lambda spec, record, prompt, timeout: store.create(record, prompt))
    monkeypatch.setattr(worker, "start", start)
    schema = tmp_path / "schema.json"
    schema.write_text('{"type":"object","required":["verdict"]}')

    def invoke(path="schema.json", agent="sol", expected=0):
        assert cli.main(["dispatch", "--agent", agent, "--model", "gpt-6.1-sol", "--task-id", "schema",
                         "--prompt", "Review", "--output-schema", str(path)]) == expected
        if expected:
            start.assert_not_called()
            git.create_worktree.assert_not_called()
            assert not (tmp_path / "tasks").exists()
            return None
        return start.call_args.args[0], store.read("schema")

    return SimpleNamespace(invoke=invoke, schema=schema)


@pytest.mark.parametrize("absolute", [False, True])
def test_schema_loss_record_and_real_codex_argv(dispatch, absolute):
    spec, record = dispatch.invoke(dispatch.schema if absolute else "schema.json")
    assert record["output_schema_path"] == str(dispatch.schema)
    assert record["output_schema_sha256"] == store.digest(dispatch.schema.read_bytes())
    argv = codex.build(spec, {}).argv
    assert argv[argv.index("--output-schema") + 1] == str(dispatch.schema)
    dispatch.schema.write_text('{}')
    with pytest.raises(ValueError, match="SHA-256 changed"):
        codex.build(spec, {})


@pytest.mark.parametrize("agent", ["claude", "cursor", "agy", "muse", "opencode", "hermes"])
def test_unsupported_schema_refused_before_launch(dispatch, capsys, agent):
    dispatch.invoke(agent=agent, expected=2)
    assert "--output-schema is supported only with the effective codex agent" in capsys.readouterr().err


@pytest.mark.parametrize("kind", ["missing", "non-json", "non-object", "invalid-schema", "symlink", "relative-escape"])
def test_unsafe_schema_refused_before_launch(dispatch, capsys, kind):
    path = dispatch.schema
    if kind == "missing":
        path = path.with_name("missing.json")
    elif kind in {"non-json", "non-object", "invalid-schema"}:
        path.write_text({"non-json": "prose", "non-object": "[]", "invalid-schema": '{"type":42}'}[kind])
    else:
        outside = path.parent.parent / "outside.json"
        outside.write_text('{}')
        if kind == "symlink":
            path = path.with_name("link.json")
            path.symlink_to(outside)
        else:
            path = "../outside.json"
    dispatch.invoke(path, expected=2)
    assert "schema" in capsys.readouterr().err


def test_explicit_external_absolute_schema_allowed(dispatch):
    path = dispatch.schema.parent.parent / "external.json"
    path.write_text('{}')
    spec, record = dispatch.invoke(path)
    assert record["output_schema_path"] == str(path)
    assert codex.build(spec, {}).argv[-2:] == ["-s", "read-only"]


def test_schema_symlink_substitution_after_binding_refused(dispatch):
    spec, _record = dispatch.invoke()
    target = dispatch.schema.with_name("target.json")
    dispatch.schema.rename(target)
    dispatch.schema.symlink_to(target)
    with pytest.raises(ValueError, match="unsafe"):
        codex.build(spec, {})


@pytest.mark.parametrize("output,status", [('{}', "failed"), ('prose', "failed"), ('{"verdict":"APPROVE"}', "done")])
def test_invalid_schema_result_cannot_settle_done(dispatch, monkeypatch, output, status):
    spec, _record = dispatch.invoke()
    path = store.record_path(spec.task_id)
    (path.parent / "logs").mkdir()
    spec.final_file.write_text(output)
    invocation = codex.build(spec, {})
    monkeypatch.setattr(codex, "build", lambda *a: invocation)
    monkeypatch.setattr(worker.signal, "signal", lambda *a: None)
    monkeypatch.setattr(worker.signal, "pthread_sigmask", lambda *a: None)
    monkeypatch.setattr(git, "snapshot_delivery", lambda *a: {})
    monkeypatch.setattr(worker, "_reap_settled", lambda *a: None)

    def popen(*a, **kw):
        kw["stdout"].write(b'{"type":"turn.completed"}\n')
        return SimpleNamespace(returncode=0, wait=lambda *a, **kw: 0)

    monkeypatch.setattr(worker.subprocess, "Popen", popen)
    worker.supervise(path, spec.options, 10)
    settled = json.loads(path.read_text())
    assert settled["status"] == status
    if status == "failed":
        assert "structured_output_invalid" in settled["error"]
