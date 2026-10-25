"""Part B CLI compatibility and false-success regressions, using no real providers."""

import json
import os
import subprocess
import sys
from dataclasses import replace

import pytest

from scripts.dispatcher.providers import load
from scripts.dispatcher.types import ParsedResult, TaskSpec

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
STUB = """import json, os, pathlib, sys
pathlib.Path(os.environ["CAPTURE"]).write_text(json.dumps({
    "argv": sys.argv[1:], "cwd": os.getcwd(), "stdin": sys.stdin.buffer.read().hex(),
    "account": os.environ.get("CLAUDE_CONFIG_DIR"), "marker": os.environ.get("PROVIDER_TEST")
}))
if "-o" in sys.argv:
    pathlib.Path(sys.argv[sys.argv.index("-o") + 1]).write_text("Finished.")
sys.stdout.write(os.environ["STUB_STREAM"])
"""


@pytest.mark.parametrize("provider", SUCCESS)
@pytest.mark.parametrize("mode", ["read-only", "workspace-write"])
@pytest.mark.parametrize("effort", [None, "high"])
def test_cli_prompt_or_mode_regression(tmp_path, monkeypatch, provider, mode, effort):
    """Catch lost stdin, wrong model/effort, wrong cwd and plan-only writers."""
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
        expected += ["-s", mode]
    elif provider == "claude":
        if effort:
            expected += ["--effort", "high"]
        expected += ["--output-format", "stream-json", "--verbose", "--permission-mode", "dontAsk", "--allowedTools"]
        expected += [
            "Read,Grep,Glob,LS,Bash,WebFetch,WebSearch"
            if mode == "read-only"
            else "Bash,Read,Edit,Write,Grep,Glob,LS,WebFetch,WebSearch"
        ]
        if mode == "read-only":
            expected += ["--disallowedTools", invocation.argv[-1]]
            denies = set(invocation.argv[-1].split(","))
            assert {"Edit", "Write", "NotebookEdit", "Bash(git push *)", "Bash(gh api --input *)"} <= denies
    elif provider == "cursor":
        expected += ["--mode", "ask"] if mode == "read-only" else ["--approve-mcps", "--sandbox", "disabled", "--force"]
    else:
        expected += ["--sandbox"] if mode == "read-only" else ["--dangerously-skip-permissions"]
        expected += ["--print-timeout", "120m", "--log-file", str(final.with_suffix(".log"))]
        if mode == "read-only":
            expected += ["--add-dir", str(worktree)]
    proc = subprocess.run(
        invocation.argv, input=invocation.stdin, env=invocation.env, cwd=worktree, capture_output=True, timeout=10
    )
    assert proc.returncode == 0, proc.stderr.decode()
    capture = json.loads((tmp_path / "capture.json").read_text())
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
    ) == ParsedResult("Finished.", {"input_tokens": 7, "output_tokens": 3}, None)
    if provider == "claude":
        env["CLAUDE_CONFIG_DIR"] = str(tmp_path / "selected-account-b")
        invocation = load(provider).build(replace(spec, claude_account="b"), env)
        assert invocation.env["CLAUDE_CONFIG_DIR"] == env["CLAUDE_CONFIG_DIR"]


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
    assert load(provider).parse(stdout, "", 0, "Finished.") == ParsedResult("Finished.", None, None)


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
