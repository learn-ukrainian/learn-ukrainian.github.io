"""Schema loss, unsafe bindings and invalid final output must fail closed."""

import json
import re
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from scripts.dispatcher import agy_sandbox, checks, cli, git, providers, store, worker
from scripts.dispatcher.providers import agy, codex


@pytest.fixture
def dispatch(tmp_path, monkeypatch):
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    monkeypatch.setattr(git, "resolve_repo", lambda _: (tmp_path, dict(key="public", github="example/public")))
    monkeypatch.setattr(git, "worktree_plan", lambda *a: (tmp_path, "codex/schema", "a" * 40))
    monkeypatch.setattr(git, "create_worktree", Mock())
    monkeypatch.setattr(checks, "check_resources", lambda _: None)
    start = Mock(side_effect=lambda spec, record, prompt, timeout: store.create(record, prompt))
    monkeypatch.setattr(worker, "start", start)
    # The checkout is tmp_path itself, so the scratch under the test's scratch root would nest in it.
    monkeypatch.setattr(worker, "create_dispatch_lease", lambda *a: None)
    monkeypatch.setattr(agy_sandbox, "unavailable", lambda: None)
    monkeypatch.setattr(agy_sandbox, "launcher", lambda spec, argv: argv)
    schema = tmp_path / "schema.json"
    schema.write_text('{"type":"object","required":["verdict"]}')

    def invoke(path="schema.json", agent="sol", expected=0, review=False, review_profile="code", task_id="schema"):
        model = {"agy": "gemini-3.8-flash-high", "claude": "claude-opus-5-5"}.get(agent, "gpt-6.1-sol")
        args = ["dispatch", "--agent", agent, "--model", model, "--task-id", task_id, "--prompt", "Review"]
        if agent == "agy" and review_profile is not None:
            args += ["--review-profile", review_profile]
        if path is not None:
            args += ["--output-schema", str(path)]
        if review:
            args += ["--require-review-verdict"]
        assert cli.main(args) == expected
        if expected:
            start.assert_not_called()
            git.create_worktree.assert_not_called()
            assert not (tmp_path / "tasks").exists()
            return None
        return start.call_args.args[0], store.read(task_id)

    return SimpleNamespace(invoke=invoke, schema=schema)


@pytest.mark.parametrize("absolute", [False, True])
@pytest.mark.parametrize("agent", ["sol", "agy"])
def test_schema_loss_record_and_real_codex_argv(dispatch, absolute, agent):
    spec, record = dispatch.invoke(dispatch.schema if absolute else "schema.json", agent=agent)
    assert record["output_schema_path"] == str(dispatch.schema)
    assert record["output_schema_sha256"] == store.digest(dispatch.schema.read_bytes())
    provider = providers.load(spec.agent)
    argv = provider.build(spec, {}).argv
    if agent == "agy":
        assert json.loads(argv[argv.index("--json-schema") + 1]) == {"type": "object", "required": ["verdict"]}
    else:
        assert argv[argv.index("--output-schema") + 1] == str(dispatch.schema)
    dispatch.schema.write_text('{}')
    with pytest.raises(ValueError, match="SHA-256 changed"):
        provider.build(spec, {})


@pytest.mark.parametrize("agent", ["cursor", "muse", "opencode"])
def test_unsupported_schema_refused_before_launch(dispatch, capsys, agent):
    dispatch.invoke(agent=agent, expected=2)
    assert "--output-schema is supported only with the effective codex, agy, or claude agent" in capsys.readouterr().err


@pytest.mark.parametrize("kind", ["missing", "non-json", "non-object", "invalid-schema", "symlink", "relative-escape"])
@pytest.mark.parametrize("agent", ["sol", "agy"])
def test_unsafe_schema_refused_before_launch(dispatch, capsys, kind, agent):
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
    dispatch.invoke(path, agent=agent, expected=2)
    assert "schema" in capsys.readouterr().err


def test_explicit_external_absolute_schema_allowed(dispatch):
    path = dispatch.schema.parent.parent / "external.json"
    path.write_text('{}')
    spec, record = dispatch.invoke(path)
    assert record["output_schema_path"] == str(path)
    assert 'sandbox_mode="read-only"' in codex.build(spec, {}).argv


@pytest.mark.parametrize("agent", ["sol", "agy"])
def test_schema_symlink_substitution_after_binding_refused(dispatch, agent):
    spec, _record = dispatch.invoke(agent=agent)
    target = dispatch.schema.with_name("target.json")
    dispatch.schema.rename(target)
    dispatch.schema.symlink_to(target)
    with pytest.raises(ValueError, match="unsafe"):
        providers.load(spec.agent).build(spec, {})


@pytest.mark.parametrize("output,status", [('{}', "failed"), ('prose', "failed"), ('{"verdict":"APPROVE"}', "done")])
@pytest.mark.parametrize("agent", ["sol", "agy"])
def test_invalid_schema_result_cannot_settle_done(dispatch, monkeypatch, output, status, agent):
    spec, _record = dispatch.invoke(agent=agent)
    path = store.record_path(spec.task_id)
    (path.parent / "logs").mkdir()
    spec.final_file.write_text(output)
    provider = providers.load(spec.agent)
    invocation = provider.build(spec, {})
    monkeypatch.setattr(provider, "build", lambda *a: invocation)
    monkeypatch.setattr(agy_sandbox, "verify", lambda *a: ({}, None, None))
    monkeypatch.setattr(worker.signal, "signal", lambda *a: None)
    monkeypatch.setattr(worker.signal, "pthread_sigmask", lambda *a: None)
    monkeypatch.setattr(git, "snapshot_delivery", lambda *a: {})
    monkeypatch.setattr(worker, "_reap_settled", lambda *a, **k: None)

    def popen(*a, **kw):
        if agent == "agy":
            try:
                payload = json.loads(output)
            except ValueError:
                payload = output
            events = [
                {"event": "init", "init": {"model": spec.model}},
                {"event": "result", "result": {"status": "SUCCESS", "structured_output": payload}},
            ]
            kw["stdout"].write(("\n".join(json.dumps(event) for event in events) + "\n").encode())
        else:
            kw["stdout"].write(b'{"type":"turn.completed"}\n')
        return SimpleNamespace(pid=None, returncode=0, wait=lambda *a, **kw: 0)

    monkeypatch.setattr(worker.subprocess, "Popen", popen)
    worker.supervise(path, spec.options, 10)
    settled = json.loads(path.read_text())
    assert settled["status"] == status
    if status == "failed":
        assert "structured_output_invalid" in settled["error"]


def test_claude_review_binds_findings_schema(dispatch):
    """Case 4: a native Claude code review must bind the findings schema.

    A VERDICT-only reply still cannot become a receipt.
    """
    from scripts.dispatcher.providers import claude
    from scripts.review.review_contract import ContractError, canonical_receipt_payload

    spec, record = dispatch.invoke(path=None, agent="claude", review=True, task_id="claude-schema")
    assert record["require_review_verdict"] is True
    assert record["output_schema_path"].endswith("/schemas/code-review-findings.v1.schema.json")
    argv = claude.build(spec, {}).argv
    schema = json.loads(argv[argv.index("--json-schema") + 1])
    canonical = json.loads(Path(record["output_schema_path"]).read_text(encoding="utf-8"))
    assert "$schema" in canonical and "$schema" not in schema  # Claude Code refuses the meta-schema reference
    assert schema == {key: value for key, value in canonical.items() if key != "$schema"}
    assert schema["properties"]["schema_version"]["const"] == "code-review-findings.v1"
    assert schema["required"] == ["schema_version", "overall", "findings"]
    with pytest.raises(ContractError, match="review_envelope_requires_one_json_block"):
        canonical_receipt_payload("VERDICT: APPROVE\nSCORE: 9/10 No defects.\nNo findings.\n")
    receipt = {
        "schema_version": "code-review-findings.v1",
        "overall": {"correctness": "correct", "explanation": "No defects.", "confidence": 0.9},
        "findings": [],
    }
    bound = json.dumps({
        "type": "result", "subtype": "success", "is_error": False,
        "result": "", "structured_output": receipt,
    })
    parsed = claude.parse(bound, "", 0, None, output_schema=schema)
    assert parsed.error is None
    assert json.loads(parsed.text) == receipt
    preamble = json.dumps({
        "type": "result", "subtype": "success", "is_error": False,
        "result": "VERDICT: APPROVE", "structured_output": receipt,
    })
    parsed = claude.parse(preamble, "", 0, None, output_schema=schema)
    assert json.loads(parsed.text) == receipt
    missing = claude.parse(
        json.dumps({"type": "result", "subtype": "success", "is_error": False, "result": "VERDICT: APPROVE"}),
        "", 0, None, output_schema=schema,
    )
    assert missing.error == "claude: missing structured output"
    failed = claude.parse(bound, "", 1, None, output_schema=schema)
    assert failed.error == "claude: exited with status 1"
    codex_spec, codex_record = dispatch.invoke(path=None, agent="sol", review=True, task_id="codex-schema")
    assert codex_record["output_schema_path"].endswith("/schemas/code-review-findings.v1.schema.json")
    codex_argv = codex.build(codex_spec, {}).argv
    assert codex_argv.count("--output-schema") == 1
    bound_path = Path(codex_argv[codex_argv.index("--output-schema") + 1])
    assert bound_path.parent.name == ".codex-schemas"
    assert bound_path.parent.parent == codex_spec.final_file.parent
    assert codex_spec.options.get("provider_output_schema_sha256") is not None
    bound = json.loads(bound_path.read_text())
    assert "if" not in bound and "oneOf" not in json.dumps(bound) and "not" not in bound
    assert "missing_capabilities" not in bound.get("properties", {})
    assert bound["properties"]["schema_version"]["type"] == "string"
    from scripts.audit.post_build_review import validate_codex_output_schema

    validate_codex_output_schema(bound)
    receipt_schema = json.loads(Path(codex_record["output_schema_path"]).read_text())
    assert "if" in receipt_schema
    refused = {**receipt, "missing_capabilities": ["shell"]}
    from jsonschema import Draft202012Validator
    from jsonschema.exceptions import ValidationError

    with pytest.raises(ValidationError, match="missing_capabilities"):
        Draft202012Validator(receipt_schema).validate(refused)
    Draft202012Validator(receipt_schema).validate(receipt)
    failed_codex = codex.parse("", "HTTP 400 schema.if is not permitted when strict is true", 1, None)
    assert failed_codex.error == (
        "codex: exited with status 1: HTTP 400 schema.if is not permitted when strict is true"
    )

    from scripts.dispatcher.types import TaskSpec

    dry_spec = TaskSpec(
        "codex-dry-schema", "sol", "gpt-6.1-sol", None, "read-only",
        codex_spec.worktree, codex_spec.prompt_file, codex_spec.final_file,
        options={**codex_spec.options, "dry_run": "True"},
    )
    dry_argv = codex.build(dry_spec, {}).argv
    dry_path = Path(dry_argv[dry_argv.index("--output-schema") + 1])
    assert not dry_path.exists()

    name_map_schema = {
        "type": "object",
        "properties": {
            "const": {"type": "string"},
            "if": {"type": "integer"},
            "not": {"type": "boolean"},
        },
        "required": ["const", "if", "not"],
    }
    projected = codex.openai_strict_schema(name_map_schema)
    assert "const" in projected["properties"]
    assert "if" in projected["properties"]
    assert "not" in projected["properties"]
    assert projected["properties"]["const"]["type"] == "string"
    assert codex._needs_openai_strict(name_map_schema) is False


def test_codex_stderr_excerpt_redacts_secret_and_home_path():
    secret = "key_" + "aB09" * 16
    home_path = "/home/fixture/.codex/config.toml"
    failed = codex.parse("", f"open {home_path} failed\nwith {secret}  rejected", 1, None)
    assert failed.error is not None
    assert secret not in failed.error
    assert home_path not in failed.error
    assert "/home/" not in failed.error
    assert failed.error.startswith("codex: exited with status 1: ")
    assert len(failed.error) <= len("codex: exited with status 1: ") + 500


def test_agy_review_binds_findings_schema(dispatch):
    """Defect class: review dispatch silently omits its structured verdict schema."""
    spec, record = dispatch.invoke(path=None, agent="agy", review=True)
    assert record["require_review_verdict"] is True
    assert record["output_schema_path"].endswith("/schemas/code-review-findings.v1.schema.json")
    argv = agy.build(spec, {}).argv
    schema = json.loads(argv[argv.index("--json-schema") + 1])
    assert schema["properties"]["schema_version"]["const"] == "code-review-findings.v1"
    assert schema["required"] == ["schema_version", "overall", "findings"]


def test_agy_ukrainian_review_omits_findings_schema(dispatch):
    """Defect class: Ukrainian review is forced to bind the code-review findings schema."""
    spec, record = dispatch.invoke(path=None, agent="agy", review=True, review_profile="ukrainian")
    assert record["require_review_verdict"] is True
    assert record.get("output_schema_path") is None
    assert record.get("output_schema_sha256") is None
    argv = agy.build(spec, {}).argv
    assert "--json-schema" not in argv


@pytest.mark.parametrize("case", ["valid", "missing-block", "malformed-json", "wrong-schema"])
def test_agy_ukrainian_review_preserves_item_judgments_and_refuses_malformed(case):
    """Defect class: Ukrainian item judgments are dropped by schema enforcement, or invalid blocks are accepted."""
    from scripts.review.review_contract import ContractError, build_item_packet, judge_item_reply

    packet = build_item_packet([{"id": "item-1", "text": "слово"}])
    if case == "valid":
        reply = (
            "VERDICT: APPROVE\n\n"
            "```ukrainian-item-judgments\n"
            '{"schema": "ukrainian-item-judgments.v1", "items": [{"id": "item-1", "verdict": "APPROVE", "finding": "", "sources": "VESUM", "quote": "слово"}]}\n'
            "```\n"
        )
    elif case == "missing-block":
        reply = "VERDICT: APPROVE\n\nNo item judgments block provided."
    elif case == "malformed-json":
        reply = "VERDICT: APPROVE\n\n```ukrainian-item-judgments\n{not valid json\n```\n"
    elif case == "wrong-schema":
        reply = (
            "VERDICT: APPROVE\n\n"
            "```ukrainian-item-judgments\n"
            '{"schema": "code-review-findings.v1", "items": [{"id": "item-1", "verdict": "APPROVE"}]}\n'
            "```\n"
        )

    stream = json.dumps({"event": "result", "result": {"status": "SUCCESS", "response": reply}}) + "\n"
    parsed = agy.parse(stream, "", 0, reply, output_schema=None)
    assert parsed.error is None
    assert parsed.text == reply

    if case == "valid":
        chunk = judge_item_reply(packet, parsed.text, stated="APPROVED", ukrainian=True)
        assert chunk.coverage == ("item-1",)
        assert chunk.void is None
    elif case == "missing-block":
        with pytest.raises(ContractError, match="ITEM_JUDGMENTS_MISSING"):
            judge_item_reply(packet, parsed.text, stated="APPROVED", ukrainian=True)
    else:
        with pytest.raises(ContractError, match="ITEM_JUDGMENTS_MALFORMED"):
            judge_item_reply(packet, parsed.text, stated="APPROVED", ukrainian=True)


def _item_review_record(tmp_path, profile="ukrainian"):
    import hashlib

    from scripts.review.review_contract import build_item_packet, render_item_packet

    brief = tmp_path / "brief.prompt"
    brief.write_text("Review.\n\n" + render_item_packet(build_item_packet([{"id": "item-1", "text": "слово"}])))
    return {"schema_version": 2, "require_review_verdict": True, "review_profile": profile,
            "prompt_file": str(brief), "prompt_sha256": hashlib.sha256(brief.read_bytes()).hexdigest()}


def test_verdict_gate_accepts_ukrainian_item_judgments_block(tmp_path):
    """Defect class (#12417): a contract-only Ukrainian item-judgments reply fails the verdict gate."""
    reply = (
        "```ukrainian-item-judgments\n"
        '{"schema": "ukrainian-item-judgments.v1", "items": [{"id": "item-1", "verdict": "APPROVE", '
        '"finding": "", "sources": "VESUM", "quote": "слово"}]}\n'
        "```\n"
    )
    assert worker._verdict_failure(_item_review_record(tmp_path), reply) is None


def test_verdict_gate_refuses_ukrainian_reply_without_block_or_verdict(tmp_path):
    """Defect class (#12417): a Ukrainian reply with neither a valid block nor a verdict passes the gate."""
    reply = "```ukrainian-item-judgments\n{not valid json\n```\n"
    assert worker._verdict_failure(_item_review_record(tmp_path), reply) == "review_missing_verdict_line"


def test_verdict_gate_code_review_without_verdict_still_fails(tmp_path):
    """Defect class (#12417): the item-judgments path leaks into code-review profiles."""
    reply = (
        "```ukrainian-item-judgments\n"
        '{"schema": "ukrainian-item-judgments.v1", "items": [{"id": "item-1", "verdict": "APPROVE", '
        '"finding": "", "sources": "VESUM", "quote": "слово"}]}\n'
        "```\n"
    )
    assert worker._verdict_failure(_item_review_record(tmp_path, "code"), reply) == "review_missing_verdict_line"


@pytest.mark.parametrize("case", ["valid", "conflicting-response", "missing", "null", "invalid",
                                 "terminal-error", "duplicate-terminal", "exit-failure"])
def test_agy_structured_terminal_not_response(case):
    """Defect class: response prose or an unsuccessful terminal substitutes for structured findings."""
    from scripts.review.review_contract import load_schema
    from scripts.review.verdict_parser import recognized_verdicts

    payload = {"schema_version": "code-review-findings.v1", "findings": [],
               "overall": {"correctness": "correct", "explanation": "No defect found.", "confidence": 0.9}}
    terminal = {"status": "SUCCESS", "structured_output": payload, "response": json.dumps(payload)}
    if case == "conflicting-response":
        terminal["response"] = "VERDICT: REQUEST_CHANGES"
    elif case == "missing":
        terminal.pop("structured_output")
    elif case == "null":
        terminal["structured_output"] = None
    elif case == "invalid":
        terminal["structured_output"] = {"verdict": "APPROVE"}
    elif case == "terminal-error":
        terminal["status"] = "ERROR"
    stream = json.dumps({"event": "result", "result": terminal}) + "\n"
    if case == "duplicate-terminal":
        stream += stream
    parsed = agy.parse(stream, "", int(case == "exit-failure"), json.dumps(payload), output_schema=load_schema())
    if case in {"valid", "conflicting-response"}:
        assert parsed.error is None
        assert json.loads(parsed.text) == payload
        assert recognized_verdicts(parsed.text) == ["APPROVE"]
        assert worker._verdict_failure({"schema_version": 2, "require_review_verdict": True}, parsed.text) is None
    else:
        assert parsed.error is not None


def test_agy_schema_argument_too_large_refused(dispatch, capsys):
    """Defect class: an oversized inline schema reaches process spawn rather than a typed refusal."""
    dispatch.schema.write_text(json.dumps({"type": "object", "description": "x" * (128 * 1024)}))
    dispatch.invoke(agent="agy", expected=2)
    assert "agy_output_schema_unsupported" in capsys.readouterr().err


def test_agy_structured_missing_capability_preserved():
    """Defect class: native schema erases an existing capability-failure declaration."""
    from scripts.review.review_contract import load_schema
    from scripts.review.verdict_parser import recognized_verdicts

    payload = {"schema_version": "code-review-findings.v1", "findings": [],
               "overall": {"correctness": "uncertain", "explanation": "Required capability unavailable.",
                           "confidence": 1}}
    schema = load_schema()
    for capability in ("sources-mcp", "test-execution", "shell", "browser", "checkout-data"):
        payload["missing_capabilities"] = [capability]
        stream = json.dumps({"event": "result", "result": {"status": "SUCCESS", "structured_output": payload}})
        parsed = agy.parse(stream, "", 0, None, output_schema=schema)
        assert parsed.error is None
        assert json.loads(parsed.text)["missing_capabilities"] == [capability]
        assert recognized_verdicts(parsed.text) == ["BLOCKED"]
    for declaration in ([], ["shell", "shell"], ["unknown"], "shell", None, [1]):
        payload["missing_capabilities"] = declaration
        stream = json.dumps({"event": "result", "result": {"status": "SUCCESS", "structured_output": payload}})
        parsed = agy.parse(stream, "", 0, None, output_schema=schema)
        assert parsed.error is not None
        assert "structured_output_invalid" in parsed.error
        assert not parsed.text
    payload["missing_capabilities"] = ["shell"]
    payload["overall"]["correctness"] = "correct"
    stream = json.dumps({"event": "result", "result": {"status": "SUCCESS", "structured_output": payload}})
    parsed = agy.parse(stream, "", 0, None, output_schema=schema)
    assert parsed.error is not None
    assert "additionalProperties" in parsed.error
    assert not parsed.text


def test_review_path_pattern_portable_equivalence():
    """Defect class: a portable-schema rewrite changes which repository paths are accepted."""
    from scripts.review.review_contract import load_schema

    original = re.compile(r"^(?!/)(?![A-Za-z]:)(?!.*(?:^|/)\.\.(?:/|$))"
                          r"[A-Za-z0-9._@+-]+(?:/[A-Za-z0-9._@+-]+)*$")
    portable = re.compile(load_schema()["$defs"]["repo_relative_path"]["pattern"])
    cases = [
        ("a", True), (".", True), ("./a", True), ("a/.", True), ("...", True),
        ("..hidden", True), ("a/..hidden", True), (".agent/file", True),
        ("scripts/dispatcher/agy.py", True), ("+a/@b_1-c.txt", True),
        ("", False), ("..", False), ("../a", False), ("a/..", False),
        ("a/../b", False), ("a//b", False), ("/a", False), ("a/", False),
        ("C:/a", False), ("a\\b", False), ("a:b", False), ("~/.ssh", False),
        ("a b", False), ("a\nb", False), ("./..", False),
    ]
    for path, expected in cases:
        assert (original.search(path) is not None, portable.search(path) is not None) == (expected, expected), path


@pytest.mark.parametrize("phase", ["before-init", "after-init", "success"])
def test_agy_schema_rejection_is_typed_before_model_init(phase):
    """Defect class: a native schema refusal loses its reason or is misclassified after initialization."""
    from scripts.review.review_contract import load_schema

    message = ("invalid --json-schema: standard validation failed\n\n"
               "- at schema: invalid regular expression\n    - unsupported Perl syntax: `(?!`")
    stderr = f"Error: {message}\n\nUsage of agy:\n  --json-schema Optional schema\n"
    payload = {"schema_version": "code-review-findings.v1", "findings": [],
               "overall": {"correctness": "correct", "explanation": "No defect found.", "confidence": 0.9}}
    stdout = "" if phase == "before-init" else json.dumps(
        {"event": "init", "init": {"model": "gemini-3.8-flash-high"}}
    ) + "\n"
    if phase == "success":
        stdout += json.dumps({"event": "result", "result": {"status": "SUCCESS", "structured_output": payload}})
    parsed = agy.parse(stdout, stderr, 0 if phase == "success" else 1, None, output_schema=load_schema())
    if phase == "before-init":
        assert parsed.error == (
            "agy_output_schema_unsupported: AGY rejected the --json-schema argument; "
            "its text is in the task's retained stream"
        )
        assert parsed.text is None and parsed.resolved_model is None
    elif phase == "after-init":
        assert parsed.error == "agy: exited with status 1"
    else:
        assert parsed.error is None and json.loads(parsed.text) == payload
