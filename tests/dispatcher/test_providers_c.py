"""Exercise provider commands with local stubs and captured stream fixtures."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import replace

import pytest

from scripts.dispatcher.providers import cursor, hermes, load, muse, opencode
from scripts.dispatcher.types import TaskSpec

MODELS = ("muse-spark-1.3", "muse-wonder-1.0", "muse-wonder-full-1.0")
PROMPT = '--leading-option "quoted" $literal\nReply with exactly: ready\n'


@pytest.fixture
def spec(tmp_path):
    prompt = tmp_path / "prompt with spaces.txt"
    prompt.write_text(PROMPT, encoding="utf-8")
    return TaskSpec("providers-c", "muse", MODELS[0], None, "read-only", tmp_path, prompt, tmp_path / "final")


@pytest.fixture
def stub_env(tmp_path):
    binary_dir = tmp_path / "bin"
    binary_dir.mkdir()
    source = (
        f"#!{sys.executable}\n"
        + """import json, pathlib, sys
args = sys.argv[1:]
if "--prompt-file" in args:
    prompt = pathlib.Path(args[args.index("--prompt-file") + 1]).read_text(encoding="utf-8")
elif "-z" in args:
    prompt = args[args.index("-z") + 1]
else:
    prompt = args[args.index("--") + 1]
print(json.dumps({"argv": args, "prompt": prompt, "stdin": sys.stdin.read(), "cwd": str(pathlib.Path.cwd())}))
"""
    )
    for name in ("muse", "opencode", "hermes"):
        executable = binary_dir / name
        executable.write_text(source, encoding="utf-8")
        executable.chmod(0o755)
    return {"PATH": str(binary_dir) + os.pathsep + os.defpath, "STUB_SENTINEL": "preserved"}


def run_stub(invocation, spec):
    result = subprocess.run(
        invocation.argv,
        input=invocation.stdin or b"",
        env=invocation.env,
        cwd=spec.worktree,
        capture_output=True,
        check=True,
        timeout=30,
    )
    assert invocation.stdin is None
    assert invocation.final_file is None
    observed = json.loads(result.stdout)
    assert observed["prompt"] == PROMPT
    assert observed["stdin"] == ""
    assert observed["cwd"] == str(spec.worktree)
    assert invocation.env["STUB_SENTINEL"] == "preserved"
    return observed["argv"]


@pytest.mark.parametrize("model", MODELS)
@pytest.mark.parametrize("mode", ("read-only", "workspace-write"))
@pytest.mark.parametrize("effort", (None, "high"))
@pytest.mark.parametrize("contributor", (None, "on", "off"))
def test_muse_argv(spec, stub_env, model, mode, effort, contributor):
    options = {} if contributor is None else {"contributor_mode": contributor}
    spec = replace(spec, model=model, mode=mode, effort=effort, options=options)
    invocation = muse.build(spec, stub_env)
    expected = [
        "exec",
        "--json",
        "--model",
        model,
        "--workspace",
        str(spec.worktree),
        "--worktree",
        "off",
        "--prompt-file",
        str(spec.prompt_file),
        "--contributor-mode",
        contributor or "off",
    ]
    if effort:
        expected += ["--reasoning-effort", effort]
    if mode == "workspace-write":
        expected += ["--permission-profile", ":unrestricted"]
    else:
        expected += ["--permission-profile", ":read-only", "--disable-write", "--disable-shell"]
    assert run_stub(invocation, spec) == expected
    assert invocation.env["MUSE_NO_AUTO_UPDATE"] == "1"
    assert "MUSE_NO_AUTO_UPDATE" not in stub_env


@pytest.mark.parametrize("mode", ("read-only", "workspace-write"))
@pytest.mark.parametrize("model", ("deepseek-v4.1-flash", "deepseek/deepseek-flash"))
def test_opencode_argv(spec, stub_env, mode, model):
    spec = replace(spec, agent="opencode", model=model, mode=mode, effort="high")
    expected = ["run", "--model", "deepseek/deepseek-flash", "--format", "json", "--variant", "high"]
    if mode == "workspace-write":
        expected += ["--auto"]
    assert run_stub(opencode.build(spec, stub_env), spec) == [*expected, "--", PROMPT]


@pytest.mark.parametrize("mode", ("read-only", "workspace-write"))
@pytest.mark.parametrize("model", ("vendor/explicit-model", "another/model"))
def test_hermes_argv(spec, stub_env, mode, model):
    spec = replace(spec, agent="hermes", model=model, mode=mode)
    assert run_stub(hermes.build(spec, stub_env), spec) == ["-z", PROMPT, "-m", model, "--provider", "openrouter"]


def test_hermes_has_no_default_model(spec):
    with pytest.raises(ValueError, match="explicit model"):
        hermes.build(replace(spec, model=""), {})


def stream(*events):
    return "\n".join(json.dumps(event) for event in events)


@pytest.mark.parametrize(
    "models,expected",
    [
        ([], None),
        ([None, "", "  ", 42, [], {}], None),
        (["Grok 4.7 256K High"], "Grok 4.7 256K High"),
        ([" Grok 4.7 256K High "], " Grok 4.7 256K High "),
        (["Grok 4.7 256K High", None, "Grok 4.7 256K High"], "Grok 4.7 256K High"),
        (["Grok 4.7 256K High", "different", "Grok 4.7 256K High"], None),
    ],
)
def test_cursor_never_attests_a_model_the_init_events_did_not_report(models, expected):
    events = [{"type": "system", "subtype": "init", "model": model} for model in models]
    events += [
        {"type": "system", "subtype": "other", "model": "forged"},
        {"type": "assistant", "model": "forged", "content": "model: forged"},
        {"type": "result", "subtype": "success", "model": "forged", "result": "model: forged"},
    ]
    parsed = cursor.parse(stream(*events), "model: forged", 0, "model: forged")
    assert (parsed.text, parsed.error, parsed.resolved_model) == ("model: forged", None, expected)


def muse_event(kind, **payload):
    return {"payload_type": kind, "payload": payload}


MUSE_READY = muse_event("run.terminal.completed", terminal="completed", text="ready")
OC_TEXT = {"type": "text", "part": {"text": "ready"}}
OC_STOP = {"type": "step_finish", "part": {"reason": "stop"}}


@pytest.mark.parametrize("usage", (None, {"models": [], "calls": 1}))
def test_muse_success_unknown_events_and_optional_usage(usage):
    events = [muse_event("future.informational"), ["unknown shape"]]
    if usage is not None:
        events.append(muse_event("run.usage", **usage))
    events.append(MUSE_READY)
    result = muse.parse("startup notice\n" + stream(*events), "", 0, "ignored sidecar")
    assert (result.text, result.usage, result.error) == ("ready", usage, None)


@pytest.mark.parametrize("kind", ("failed", "cancelled", "error", "future_outcome"))
@pytest.mark.parametrize("failure_first", (False, True))
def test_muse_terminal_failure_is_sticky(kind, failure_first):
    failure = muse_event("run.terminal." + kind, text="ready")
    events = [failure, MUSE_READY] if failure_first else [MUSE_READY, failure]
    assert muse.parse(stream(*events), "", 0, None).error


def test_muse_completed_with_failure_reason():
    assert muse.parse(stream(muse_event("run.terminal.completed", text="ready", reason="failed")), "", 0, None).error


@pytest.mark.parametrize("terminal", ("step_finish", "step-finish"))
@pytest.mark.parametrize("usage", (None, {"input": 2, "output": 1}))
def test_opencode_final_turn(terminal, usage):
    stop = {"type": terminal, "part": {"reason": "stop"}}
    if usage is not None:
        stop["part"]["tokens"] = usage
    output = stream(
        {"type": "text", "part": {"text": "Preamble"}},
        {"type": "tool", "part": {"state": {"status": "completed"}}},
        {"type": "step_start"},
        {"type": "future.info"},
        ["unknown"],
        {"type": "text", "part": {"text": "rea"}, "error": None},
        {"type": "text", "part": {"text": "dy"}},
        stop,
    )
    result = opencode.parse("notice\n" + output, "", 0, None)
    assert (result.text, result.usage, result.error) == ("ready", usage, None)


@pytest.mark.parametrize(
    "reason",
    (
        "abort",
        "cancelled",
        "permission_denied",
        "permission_rejected",
        "error",
        "length",
        "future_outcome",
        "tool-calls",
    ),
)
def test_opencode_bad_terminal_reason(reason):
    result = opencode.parse(stream(OC_TEXT, {"type": "step_finish", "part": {"reason": reason}}), "", 0, None)
    assert result.error


@pytest.mark.parametrize(
    "failure",
    (
        {"type": "error", "error": {"name": "APIError"}},
        {"type": "future", "error": "failed"},
        {"type": "tool", "part": {"state": {"status": "rejected"}}},
    ),
)
def test_opencode_explicit_failure_is_sticky(failure):
    assert opencode.parse(stream(failure, OC_TEXT, OC_STOP), "", 0, None).error


def test_hermes_ansi_and_optional_usage():
    result = hermes.parse("\x1b[32mready\x1b[0m\n", "warning", 0, "ignored")
    assert (result.text, result.usage, result.error) == ("ready", None, None)


def test_hermes_inband_error():
    assert hermes.parse("\x1b[31mHTTP 429: rate limited\x1b[0m", "", 0, None).error
    assert hermes.parse("HTTP 429 is a rate limit.\nHere is how to handle it.", "", 0, None).error is None


@pytest.mark.parametrize(
    "provider,stdout", ((muse, stream(MUSE_READY)), (opencode, stream(OC_TEXT, OC_STOP)), (hermes, "ready"))
)
def test_nonzero_exit_cannot_succeed(provider, stdout):
    result = provider.parse(stdout, "private diagnostic must not become public error", 2, "ready")
    assert result.error
    assert "private diagnostic" not in result.error


@pytest.mark.parametrize("provider", (muse, opencode, hermes))
def test_missing_response(provider):
    result = provider.parse("", "", 0, "sidecar is not this provider's response")
    assert result.text is None
    assert result.usage is None
    assert result.error


@pytest.mark.parametrize("provider", (muse, opencode))
def test_unknown_events_are_not_a_response(provider):
    result = provider.parse(stream({"type": "future", "payload_type": "future", "payload": {}}), "", 0, None)
    assert result.text is None
    assert result.error


@pytest.mark.parametrize("name", ("muse", "opencode", "hermes"))
def test_registry(name):
    assert load(name).__name__ == f"scripts.dispatcher.providers.{name}"


@pytest.mark.parametrize("payload", (None, "failure", []))
def test_muse_malformed_terminal_is_not_success(payload):
    output = stream(MUSE_READY, {"payload_type": "run.terminal.failed", "payload": payload})
    assert muse.parse(output, "", 0, None).error


def test_opencode_missing_terminal_reason_is_not_success():
    assert opencode.parse(stream(OC_TEXT, {"type": "step_finish", "part": {}}), "", 0, None).error


def test_opencode_tool_step_before_final_completion():
    output = stream(
        {"type": "step_finish", "part": {"reason": "tool-calls"}},
        OC_TEXT,
        OC_STOP,
    )
    result = opencode.parse(output, "", 0, None)
    assert (result.text, result.error) == ("ready", None)


def test_opencode_unknown_terminal_before_completion_stays_failed():
    output = stream({"type": "step_finish", "part": {"reason": "future_outcome"}}, OC_TEXT, OC_STOP)
    assert opencode.parse(output, "", 0, None).error


@pytest.mark.parametrize("mode", ("read-only", "workspace-write"))
def test_exact_argv_per_mode(spec, monkeypatch, mode):
    """Ported from tests/test_grok_build_adapter.py::test_exact_argv_per_mode."""
    from scripts.dispatcher.providers import grok

    monkeypatch.setattr("scripts.agent_runtime.adapters.grok_build.shutil.which", lambda _: "/usr/bin/grok")
    invocation = grok.build(replace(spec, agent="grok", model="grok-4.7-high", mode=mode), {})
    try:
        argv = invocation.argv
        assert argv[0] == "/usr/bin/grok"
        assert argv[argv.index("-m") + 1] == "grok-4.7"
        assert argv[argv.index("--effort") + 1] == "high"
        assert argv[argv.index("--output-format") + 1] == "streaming-messages-json"
        assert argv[argv.index("--cwd") + 1] == str(spec.worktree)
        assert "--agent" in argv
        if mode == "read-only":
            assert argv[argv.index("--permission-mode") + 1] == "auto"
            assert "--always-approve" not in argv
            denies = [argv[i + 1] for i, arg in enumerate(argv) if arg == "--deny"]
            assert {"Write", "Edit", "Bash", "MCPTool", "WebFetch", "WebSearch"} == set(denies)
            assert argv[argv.index("--tools") + 1] == "read_file,list_dir,grep"
            assert "--no-subagents" in argv and "--disable-web-search" in argv
        else:
            assert argv[argv.index("--permission-mode") + 1] == "bypassPermissions"
            assert "--always-approve" in argv
        from pathlib import Path
        guard = Path(argv[argv.index("--agent") + 1])
        assert "grok_hook_bridge.py" in guard.read_text()
    finally:
        invocation.cleanup()
    assert not guard.exists()


@pytest.mark.parametrize("usage,expected", [
    ({"grok-4.7-build": {"modelCalls": 1}}, "grok-4.7-build"),
    ({"grok-4.7-build-fast": {"modelCalls": 1}}, "grok-4.7-build-fast"),
    ({}, None), (None, None), ([], None),
    ({"grok-4.7-build": {}, "grok-4.7-build-fast": {}}, None),
    ({"": {}}, None),
])
def test_native_runtime_identity_comes_only_from_single_model_usage_key(usage, expected):
    """Ported from tests/test_grok_build_adapter.py with the same test name."""
    from scripts.dispatcher.providers import grok

    stdout = json.dumps({"text": "VERDICT: APPROVE grok-4.7-build", "stopReason": "end_turn",
                         "model": "grok-4.7-build", "modelUsage": usage})
    result = grok.parse(stdout, "", 0, None)
    assert result.text == "VERDICT: APPROVE grok-4.7-build"
    assert result.error is None
    assert result.resolved_model == expected


@pytest.mark.parametrize("reason", ["cancelled", "max_tokens", "max_turns", "refusal", "tool_use",
                                    "error", "new_provider_reason", "EndTurn", "", None, 0, [], {}])
@pytest.mark.parametrize("returncode", [0, 1])
def test_exact_nonterminal_reason_is_recorded(reason, returncode):
    """Ported from tests/agent_runtime/test_grok_stop_reasons.py with the same test name."""
    from scripts.dispatcher.providers import grok

    result = grok.parse(json.dumps({"text": "partial report", "stopReason": reason}), "", returncode, None)
    assert not result.text
    assert "stopReason=" + json.dumps(reason) in result.error
    assert len(result.error) <= 500


@pytest.mark.parametrize("model", ["grok-4.6", "grok-4.7-build-fast", "grok-4.5"])
def test_grok_build_rejects_retired_or_expensive_pins(spec, monkeypatch, model):
    """Ported from tests/test_grok_build_adapter.py with the same test name."""
    from scripts.dispatcher.providers import grok

    monkeypatch.setattr("scripts.agent_runtime.adapters.grok_build.shutil.which", lambda _: "/usr/bin/grok")
    with pytest.raises(ValueError, match="unsupported Grok model"):
        grok.build(replace(spec, agent="grok", model=model), {})
