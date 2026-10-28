"""Part B CLI compatibility and false-success regressions, using no real providers."""

import json
import os
import subprocess
import sys
from dataclasses import replace

import pytest

from scripts.agent_runtime.sources_read_only import sources_tool_sets
from scripts.dispatcher.providers import load
from scripts.dispatcher.types import ParsedResult, TaskSpec
from scripts.lib import rules_core

# Small recorded event shapes from the old adapters' stream contracts.
SUCCESS = {
    "codex": '{"type":"thread.started","thread_id":"fixture"}\n'
    '{"type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":7,"output_tokens":3}}}}\n'
    '{"type":"turn.completed"}\n',
    "claude": '{"type":"system","subtype":"init"}\n'
    '{"type":"result","subtype":"success","is_error":false,"result":"Finished.","usage":{"input_tokens":7,"output_tokens":3}}\n',
    "cursor": '{"type":"system","subtype":"init"}\n'
    '{"type":"assistant","message":{"content":[{"type":"text","text":"Finished."}]}}\n'
    '{"type":"result","subtype":"success","is_error":false,"usage":{"input_tokens":7,"output_tokens":3}}\n',
    "agy": '{"event":"init"}\n'
    '{"event":"result","result":{"status":"SUCCESS","response":"Finished.","usage":{"input_tokens":7,"output_tokens":3}}}\n',
}
ERROR = {
    "codex": '{"type":"turn.failed","error":{"message":"failed"}}',
    "claude": '{"type":"result","subtype":"error_during_execution","is_error":true,"result":"Finished."}',
    "cursor": '{"type":"result","subtype":"error","is_error":true,"result":"Finished."}',
    "agy": '{"event":"result","result":{"status":"ERROR","response":"Finished.","error":"failed"}}',
}
UNKNOWN = {
    "codex": '{"type":"turn.unrecognized"}',
    "claude": '{"type":"result","subtype":"unrecognized","result":"Finished."}',
    "cursor": '{"type":"result","subtype":"unrecognized","result":"Finished."}',
    "agy": '{"event":"result","result":{"status":"UNRECOGNIZED","response":"Finished."}}',
}
# The project's Sources server as .mcp.json declares it; read-only Claude loads only this server.
SOURCES_MCP_CONFIG = json.dumps(
    {"mcpServers": {"sources": json.loads(rules_core.source_path(".mcp.json").read_text())["mcpServers"]["sources"]}},
    separators=(",", ":"),
)
STUB = """import json, os, pathlib, sys
pathlib.Path(os.environ["CAPTURE"]).write_text(json.dumps({
    "argv": sys.argv[1:], "cwd": os.getcwd(), "stdin": sys.stdin.buffer.read().hex(),
    "account": os.environ.get("CLAUDE_CONFIG_DIR"), "marker": os.environ.get("PROVIDER_TEST"),
    "background": os.environ.get("CLAUDE_CODE_DISABLE_BACKGROUND_TASKS"),
    "advisor": os.environ.get("CLAUDE_CODE_DISABLE_ADVISOR_TOOL"), "context": os.environ.get("CLAUDECODE")
}))
if "-o" in sys.argv:
    pathlib.Path(sys.argv[sys.argv.index("-o") + 1]).write_text("Finished.")
sys.stdout.write(os.environ["STUB_STREAM"])
"""


# Read-only AGY is refused before launch (test_core::test_read_only_mode_denies_edits_on_every_provider).
@pytest.mark.parametrize(
    "provider,mode",
    [(p, m) for p in SUCCESS for m in ("read-only", "workspace-write") if (p, m) != ("agy", "read-only")],
)
@pytest.mark.parametrize("effort", [None, "high"])
def test_cli_prompt_or_mode_regression(tmp_path, monkeypatch, provider, mode, effort):
    """Catch lost stdin, wrong mode and headless background work escaping print completion."""
    worktree = tmp_path / "checkout with spaces"
    worktree.mkdir()
    prompt = tmp_path / "prompt.txt"
    prompt_bytes = 'Inspect "the file".\r\nЗвіт.\n--not-a-flag'.encode()
    prompt.write_bytes(prompt_bytes)
    final = tmp_path / "final.txt"
    spec = TaskSpec("provider-b", provider, "explicit-model", effort, mode, worktree, prompt, final, "a")
    executable = "cursor-agent" if provider == "cursor" else provider
    binary = tmp_path / executable
    binary.write_text(f"#!{sys.executable}\n" + STUB)
    binary.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path) + os.pathsep + os.environ["PATH"])
    monkeypatch.setenv("CLAUDE_CODE_DISABLE_BACKGROUND_TASKS", "0")
    monkeypatch.setenv("CLAUDE_CODE_DISABLE_ADVISOR_TOOL", "0")
    monkeypatch.setenv("CLAUDECODE", "inherited-session")
    env = dict(os.environ, CAPTURE=str(tmp_path / "capture.json"), STUB_STREAM=SUCCESS[provider], PROVIDER_TEST="kept")
    env["CLAUDE_CONFIG_DIR"] = str(tmp_path / "selected-account-a")
    original_env = env.copy()
    invocation = load(provider).build(spec, env)
    expected = {
        "codex": ["exec", "--json", "-C", str(worktree), "-m", "explicit-model", "-o", str(final)],
        "claude": ["-p", "--model", "explicit-model"],
        "cursor": [
            "-p",
            "--model",
            "explicit-model",
            "--output-format",
            "stream-json",
            "--trust",
            "--workspace",
            str(worktree),
        ],
        "agy": [
            "--mode",
            "auto",
            "--input-format",
            "stream-json",
            "--output-format",
            "stream-json",
            "--model",
            "explicit-model",
        ],
    }[provider]
    if provider == "codex":
        if effort:
            expected += ["-c", "model_reasoning_effort=high"]
        expected += ["-s", "read-only"] if mode == "read-only" else ["--dangerously-bypass-approvals-and-sandbox"]
    elif provider == "claude":
        if effort:
            expected += ["--effort", "high"]
        expected += ["--output-format", "stream-json", "--verbose", "--permission-mode", "dontAsk"]
        if mode == "read-only":
            expected += ["--restricted", "--tools", "Read,Grep,Glob,Bash,WebFetch,WebSearch",
                         "--append-system-prompt-file", str(rules_core.source_path(rules_core.CORE_REL)),
                         "--mcp-config", SOURCES_MCP_CONFIG, "--strict-mcp-config"]
        expected += ["--allowedTools"]
        expected += [
            "Read,Grep,Glob,LS,WebFetch,WebSearch,Bash(gh pr view *),Bash(gh pr diff *),Bash(gh pr checks *),"
            "Bash(gh issue view *),Bash(gh run view *),"
            + ",".join(f"mcp__sources__{name}" for name in sources_tool_sets()[0])
            if mode == "read-only"
            else "Bash,Read,Edit,Write,Grep,Glob,LS,WebFetch,WebSearch"
        ]
        denies = "Monitor,ScheduleWakeup,CronCreate,Workflow"
        if mode == "read-only":
            denies = (
                "Edit,Write,NotebookEdit,Bash(git push *),Bash(git commit *),Bash(git merge *),"
                "Bash(git rebase *),Bash(git reset *),Bash(git tag *),Bash(git branch -D *),"
                "Bash(gh pr merge *),Bash(gh pr create *),Bash(gh pr comment *),Bash(gh pr review *),"
                "Bash(gh pr edit *),Bash(gh pr close *),Bash(gh pr reopen *),Bash(gh issue create *),"
                "Bash(gh issue comment *),Bash(gh issue edit *),Bash(gh issue close *),Bash(gh issue reopen *),"
                "Bash(gh api -X *),Bash(gh api --method *),Bash(gh release *),Bash(gh api -f *),"
                "Bash(gh api -F *),Bash(gh api --field *),Bash(gh api --raw-field *),Bash(gh api --input *),"
                "Bash(gh workflow run *)," + denies + ","
                + ",".join(f"mcp__sources__{name}" for name in sources_tool_sets()[1])
            )
        expected += ["--disallowedTools", denies]
    elif provider == "cursor":
        expected += ["--mode", "ask"] if mode == "read-only" else ["--approve-mcps", "--sandbox", "disabled", "--force"]
    else:
        expected += ["--dangerously-skip-permissions"]
        expected += ["--print-timeout", "120m", "--log-file", str(final.with_suffix(".log"))]
    proc = subprocess.run(
        invocation.argv, input=invocation.stdin, env=invocation.env, cwd=worktree, capture_output=True, timeout=10
    )
    assert proc.returncode == 0, proc.stderr.decode()
    capture = json.loads((tmp_path / "capture.json").read_text())
    if provider == "claude":
        assert capture["background"] == "1"
        assert capture["advisor"] == "1"
        assert capture["context"] == "inherited-session"
        assert invocation.env == dict(
            original_env, CLAUDE_CODE_DISABLE_BACKGROUND_TASKS="1", CLAUDE_CODE_DISABLE_ADVISOR_TOOL="1"
        )
    assert capture["argv"] == expected
    assert capture["cwd"] == str(worktree)
    expected_stdin = prompt_bytes
    if provider == "agy":
        expected_stdin = (
            json.dumps(
                {
                    "event": "user",
                    "message": {"role": "user", "content": [{"type": "text", "text": prompt_bytes.decode()}]},
                }
            )
            + "\n"
        ).encode()
    assert bytes.fromhex(capture["stdin"]) == expected_stdin
    assert capture["account"] == env["CLAUDE_CONFIG_DIR"]
    assert capture["marker"] == "kept"
    assert env == original_env
    assert invocation.final_file == (final if provider == "codex" else None)
    final_text = final.read_text() if invocation.final_file else None
    assert load(provider).parse(
        proc.stdout.decode(), proc.stderr.decode(), proc.returncode, final_text
    ) == ParsedResult(
        "Finished.", {"input_tokens": 7, "output_tokens": 3}, None,
        sources_mcp_call_count=0 if provider == "claude" else None,
    )
    if provider == "claude":
        env["CLAUDE_CONFIG_DIR"] = str(tmp_path / "selected-account-b")
        invocation = load(provider).build(replace(spec, claude_account="b"), env)
        assert invocation.env["CLAUDE_CONFIG_DIR"] == env["CLAUDE_CONFIG_DIR"]


def test_read_only_claude_review_exposes_only_the_trusted_sources_mcp_readers(tmp_path):
    """A Ukrainian reviewer needs Sources: its readers only, never from the reviewed tree's .mcp.json (#10074)."""
    (tmp_path / ".mcp.json").write_text('{"mcpServers":{"sources":{"command":"sh","args":["-c","touch pwned"]}}}')
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("Review the Ukrainian change.")
    spec = TaskSpec("uk-review", "claude", "claude-opus-5-5", "high", "read-only", tmp_path, prompt, tmp_path / "f")
    argv = load("claude").build(spec, {}).argv
    config = json.loads(argv[argv.index("--mcp-config") + 1])
    assert config == {"mcpServers": {"sources": {"type": "streamable-http", "url": "http://127.0.0.1:8766/mcp"}}}
    assert "--strict-mcp-config" in argv and "--restricted" in argv
    readers, writers = sources_tool_sets()
    assert "verify_word" in readers and "query_wikipedia" in writers
    allowed = argv[argv.index("--allowedTools") + 1].split(",")
    assert [tool for tool in allowed if tool.startswith("mcp__")] == [f"mcp__sources__{name}" for name in readers]
    denied = set(argv[argv.index("--disallowedTools") + 1].split(","))
    assert {"Edit", "Write", "NotebookEdit", *(f"mcp__sources__{name}" for name in writers)} <= denied
    write = load("claude").build(replace(spec, mode="workspace-write"), {}).argv
    assert "--mcp-config" not in write


def test_claude_parse_counts_completed_sources_mcp_calls_from_the_stream():
    """Runtime evidence, from the stream shape a live read-only verify_word call emitted (claude 2.1.312)."""
    def call(call_id, name, word):
        return {"type": "assistant", "parent_tool_use_id": None, "message": {"role": "assistant", "content": [
            {"type": "tool_use", "id": call_id, "name": name, "input": {"word": word}, "caller": {"type": "direct"}}]}}

    def result(call_id, is_error=False):
        return {"type": "user", "parent_tool_use_id": None, "message": {"role": "user", "content": [
            {"tool_use_id": call_id, "type": "tool_result", "is_error": is_error,
             "content": '{"tool":"verify_word","disposition":"supported","success":true}'}]}}

    events = [
        {"type": "system", "subtype": "init", "mcp_servers": [{"name": "sources", "status": "connected"}]},
        call("toolu_01Crz", "mcp__sources__verify_word", "книга"), result("toolu_01Crz"),
        call("toolu_02Den", "mcp__sources__verify_word", "книжка"), result("toolu_02Den", is_error=True),
        call("toolu_03Run", "mcp__sources__verify_words", "кіт"),  # no result: the call never completed
        call("toolu_04Rd", "Read", "README.md"), result("toolu_04Rd"),
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "mcp__sources__verify_word"}]}},
        {"type": "result", "subtype": "success", "is_error": False, "result": "VERDICT: APPROVE"},
    ]
    stream = "".join(json.dumps(event, ensure_ascii=False) + "\n" for event in events)
    parsed = load("claude").parse(stream, "", 0, None)
    assert parsed.error is None
    assert parsed.sources_mcp_call_count == 1


@pytest.mark.parametrize("provider", ["cursor", "agy", "claude"])
@pytest.mark.parametrize("mode", ["danger", "", "WORKSPACE-WRITE", None, False, 0])
def test_unknown_provider_mode_never_receives_write_or_bypass_flags(tmp_path, provider, mode):
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("private prompt must not be echoed")
    spec = TaskSpec("unknown-mode", provider, "explicit-model", None, mode, tmp_path, prompt, tmp_path / "final.txt")
    invocation = None
    with pytest.raises(ValueError) as exc:
        invocation = load(provider).build(spec, {"PRIVATE_ENV": "must not be echoed"})
    assert str(exc.value) == f"{provider}: unsupported mode {mode!r}"
    assert invocation is None


@pytest.mark.parametrize("mode", ["danger", "", "WORKSPACE-WRITE", None, False, 0])
def test_unknown_codex_mode_never_receives_sandbox_bypass(tmp_path, mode):
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("private prompt must not be echoed")
    spec = TaskSpec("unknown-mode", "codex", "explicit-model", None, mode, tmp_path, prompt, tmp_path / "final.txt")
    invocation = None
    with pytest.raises(ValueError) as exc:
        invocation = load("codex").build(spec, {"PRIVATE_ENV": "must not be echoed"})
    assert str(exc.value) == f"codex: unsupported mode {mode!r}"
    assert invocation is None


@pytest.mark.parametrize("provider", SUCCESS)
@pytest.mark.parametrize("failure", ["nonzero", "terminal_error", "unknown_terminal", "missing_terminal", "malformed"])
def test_failure_cannot_become_success_from_final_prose(provider, failure):
    stdout = {
        "nonzero": SUCCESS[provider],
        "terminal_error": SUCCESS[provider] + ERROR[provider] + "\n",
        "unknown_terminal": SUCCESS[provider] + UNKNOWN[provider] + "\n",
        "missing_terminal": '{"type":"text","content":"Finished."}\n',
        "malformed": SUCCESS[provider] + "{broken\n",
    }[failure]
    result = load(provider).parse(
        stdout, "private diagnostic must not be echoed", 9 if failure == "nonzero" else 0, "Finished."
    )
    assert result.error
    assert "private diagnostic" not in result.error


@pytest.mark.parametrize("provider", SUCCESS)
def test_missing_usage_remains_none_and_information_does_not_change_success(provider):
    events = [json.loads(line) for line in SUCCESS[provider].splitlines()]
    for event in events:
        event.pop("usage", None)
        if isinstance(event.get("result"), dict):
            event["result"].pop("usage", None)
        if event.get("type") == "event_msg":
            event["payload"]["info"].pop("total_token_usage")
    metadata = {"type": "future_info", "event": "future_info", "message": "new metadata"}
    if provider == "codex":
        events.insert(-1, metadata)
    else:
        events.append(metadata)
    stdout = "\n".join(json.dumps(event) for event in events)
    assert load(provider).parse(stdout, "", 0, "Finished.") == ParsedResult(
        "Finished.", None, None, sources_mcp_call_count=0 if provider == "claude" else None
    )


@pytest.mark.parametrize("provider", SUCCESS)
def test_missing_final_message_is_not_success(provider):
    events = [json.loads(line) for line in SUCCESS[provider].splitlines()]
    if provider == "claude":
        events[-1]["result"] = ""
    elif provider == "cursor":
        events = [events[0], events[-1]]
    elif provider == "agy":
        events[-1]["result"]["response"] = ""
    assert load(provider).parse("\n".join(map(json.dumps, events)), "", 0, None).error


@pytest.mark.parametrize(
    "content", ["Finished.", [{"type": "tool_use", "text": "ignored"}, {"type": "text", "text": "Finished."}]]
)
def test_cursor_message_content_does_not_lose_assistant_text(content):
    stdout = json.dumps({"type": "message", "role": "assistant", "content": content})
    stdout += '\n{"type":"result","subtype":"success"}'
    assert load("cursor").parse(stdout, "", 0, None).text == "Finished."


def test_codex_turn_usage_is_read_without_token_event():
    stdout = '{"type":"turn.completed","usage":{"input_tokens":4,"output_tokens":2}}'
    assert load("codex").parse(stdout, "", 0, "Finished.") == ParsedResult(
        "Finished.", {"input_tokens": 4, "output_tokens": 2}, None
    )


@pytest.mark.parametrize("separator", ["\u0085", "\u2028", "\u2029"], ids=["NEL", "LS", "PS"])
def test_codex_error_notice_can_retry_before_successful_completion(separator):
    """codex-error-notice: retry notices must not poison a completed turn or split Unicode JSONL."""
    notice = json.dumps({"type": "error", "message": f"Retry{separator}notice"}, ensure_ascii=False)
    stdout = notice + "\n" + SUCCESS["codex"] + " \t\r\n"
    assert load("codex").parse(stdout, "", 0, "Finished.") == ParsedResult(
        "Finished.", {"input_tokens": 7, "output_tokens": 3}, None
    )


@pytest.mark.parametrize(
    ("prefix", "returncode", "final_text", "error"),
    [
        ("{broken\n", 0, "Finished.", "codex: invalid JSON stream"),
        ("[]\n", 0, "Finished.", "codex: invalid event"),
        (ERROR["codex"] + "\n", 0, "Finished.", "codex: terminal error"),
        (UNKNOWN["codex"] + "\n", 0, "Finished.", "codex: unknown terminal outcome"),
        ("", 9, "Finished.", "codex: exited with status 9"),
        ("", 0, None, "codex: missing completion or final text"),
    ],
)
def test_codex_error_notice_cannot_clear_failure_evidence(prefix, returncode, final_text, error):
    """codex-error-notice: a retried notice cannot cure malformed, terminal, exit or final-file failures."""
    stdout = prefix + '{"type":"error","message":"Retrying"}\n' + SUCCESS["codex"]
    assert load("codex").parse(stdout, "", returncode, final_text).error == error
    assert load("codex").parse('{"type":"error"}\n', "", 0, "Finished.").error == (
        "codex: missing completion or final text"
    )


@pytest.mark.parametrize(
    ("later", "error"),
    [
        ('{"type":"turn.completed","usage":{"input_tokens":99}}', "codex: event after terminal outcome"),
        ('{"type":"turn.started"}', "codex: event after terminal outcome"),
        ('{"type":"future_info"}', "codex: event after terminal outcome"),
        ('{"type":"error","message":"Retrying"}', "codex: event after terminal outcome"),
        (ERROR["codex"], "codex: event after terminal outcome"),
        (UNKNOWN["codex"], "codex: event after terminal outcome"),
        (
            '{"type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":99}}}}',
            "codex: event after terminal outcome",
        ),
        ("{broken", "codex: invalid JSON stream"),
        ("[]", "codex: invalid event"),
    ],
)
def test_codex_terminal_not_last_rejected_without_overwriting_completion_usage(later, error):
    """codex-terminal-not-last: any nonblank record after a terminal invalidates this invocation."""
    stdout = '{"type":"turn.completed","usage":{"input_tokens":4,"output_tokens":2}}\n'
    assert load("codex").parse(stdout + later + "\n", "", 0, "Finished.") == ParsedResult(
        "Finished.", {"input_tokens": 4, "output_tokens": 2}, error
    )


@pytest.mark.parametrize(
    ("stderr", "error"),
    [
        ("print timeout after 120m with turn in progress", "agy: incomplete run"),
        ("terminating 1 background task(s)", "agy: incomplete run"),
        ("terminating 0 background task(s)\nterminating 2 background task(s)", "agy: incomplete run"),
        ("terminating 0 background task(s)", None),
        ("root agent idle; waiting up to 1m for 1 background task(s)", None),
    ],
)
def test_agy_partial_stderr_rejects_incomplete_runs_with_safe_reason(stderr, error):
    """agy-partial-stderr: native incomplete signals override SUCCESS without exposing stderr."""
    stderr = "private diagnostic\n" + stderr + "\nprivate diagnostic"
    assert load("agy").parse(SUCCESS["agy"], stderr, 0, None) == ParsedResult(
        "Finished.", {"input_tokens": 7, "output_tokens": 3}, error
    )
    if error:
        assert load("agy").parse(SUCCESS["agy"], stderr, 9, None).error == "agy: exited with status 9"
        assert load("agy").parse("{broken\n" + SUCCESS["agy"], stderr, 0, None).error == "agy: invalid JSON stream"


@pytest.mark.parametrize(
    ("first", "second", "expected"),
    [
        (
            SUCCESS["agy"],
            '{"event":"result","result":{"status":"SUCCESS","response":"Replacement.","usage":{"input_tokens":99}}}',
            ParsedResult("Finished.", {"input_tokens": 7, "output_tokens": 3}, "agy: duplicate terminal result"),
        ),
        (
            ERROR["agy"],
            SUCCESS["agy"],
            ParsedResult("Finished.", None, "agy: terminal result unsuccessful"),
        ),
        (
            '{"event":"result","result":null}',
            SUCCESS["agy"],
            ParsedResult(None, None, "agy: invalid terminal result"),
        ),
        (
            SUCCESS["agy"],
            '{"event":"result","result":[]}',
            ParsedResult("Finished.", {"input_tokens": 7, "output_tokens": 3}, "agy: duplicate terminal result"),
        ),
    ],
)
def test_agy_duplicate_terminal_cannot_replace_first_result_or_clear_failure(first, second, expected):
    """agy-duplicate-terminal: accept neither a second answer nor recovery after a malformed terminal."""
    assert load("agy").parse(first + "\n" + second + "\n", "", 0, None) == expected


# Real stream shapes: codex ends a refused turn with error + turn.failed (batch_state task logs, 2026-10-28);
# claude ends with a result event carrying the API's HTTP status.
_CAPACITY = "Selected model is at capacity. Please try a different model."
_CODEX_CAPACITY = "\n".join(map(json.dumps, [
    {"type": "thread.started", "thread_id": "t"},
    {"type": "turn.started"},
    {"type": "item.completed", "item": {"type": "agent_message", "text": f"quoted: {_CAPACITY}"}},
    {"type": "error", "message": _CAPACITY},
    {"type": "turn.failed", "error": {"message": _CAPACITY}},
]))


def test_codex_terminal_capacity_failure_is_rate_limited_with_the_provider_message():
    result = load("codex").parse(_CODEX_CAPACITY, "", 1, None)
    assert (result.rate_limited, result.error) == (True, f"codex: {_CAPACITY}")


@pytest.mark.parametrize(
    "stdout",
    [
        _CODEX_CAPACITY.replace(_CAPACITY, "Something else broke."),
        # A notice or agent text naming capacity, with no terminal failure of it, is not a classification.
        "\n".join([*_CODEX_CAPACITY.splitlines()[:4], json.dumps({"type": "turn.failed", "error": {"message": "boom"}})]),
        _CODEX_CAPACITY + "\nnot json",
    ],
)
def test_codex_ordinary_or_unclean_failure_stays_failed(stdout):
    result = load("codex").parse(stdout, "", 1, None)
    assert (result.rate_limited, result.error) == (False, "codex: exited with status 1")


def _claude_result(**fields):
    return json.dumps({"type": "result", "subtype": "success", "is_error": True, "result": "API Error", **fields})


def test_claude_529_result_is_rate_limited_and_other_errors_stay_failed():
    message = "API Error: 529 Overloaded. This is a server-side issue, usually temporary."
    capacity = load("claude").parse(_claude_result(api_error_status=529, result=message), "", 1, None)
    assert (capacity.rate_limited, capacity.error) == (True, f"claude: {message}")
    for fields in ({"api_error_status": None}, {"api_error_status": 500}, {"api_error_status": 529, "is_error": False}):
        other = load("claude").parse(_claude_result(**fields), "", 1, None)
        assert (other.rate_limited, other.error) == (False, "claude: exited with status 1")


_CLAUDE_529 = _claude_result(api_error_status=529, result="API Error: 529 Overloaded.")


@pytest.mark.parametrize(
    "stdout",
    [
        "not json\n" + _CLAUDE_529,  # a malformed line before the terminal result
        _CLAUDE_529 + '\n{"type":"assistant"}',  # an event after the terminal result
        _CLAUDE_529 + "\n" + _CLAUDE_529,  # a duplicated terminal result
    ],
)
def test_claude_unclean_capacity_stream_stays_failed(stdout):
    result = load("claude").parse(stdout, "", 1, None)
    assert (result.rate_limited, result.error) == (False, "claude: exited with status 1")
